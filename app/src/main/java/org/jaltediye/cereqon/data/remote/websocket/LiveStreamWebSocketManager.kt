package org.jaltediye.cereqon.data.remote.websocket

import android.util.Log
import org.jaltediye.cereqon.data.remote.BackendDefaults
import org.jaltediye.cereqon.data.remote.dto.LivePayloadDto
import org.jaltediye.cereqon.data.remote.mapper.FeatureNameBuilder
import org.jaltediye.cereqon.data.remote.mapper.LivePayloadMapper
import org.jaltediye.cereqon.domain.model.LiveWindow
import org.jaltediye.cereqon.domain.model.StreamConnectionState
import org.jaltediye.cereqon.data.remote.ServerUrlStore
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import java.net.URI
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.math.min
import kotlin.random.Random

/**
 * OkHttp WebSocket client for GET-upgraded stream at /ws/live.
 *
 * Implements exponential backoff reconnect while [start] is active.
 * Server contract: server-push JSON only; no client messages.
 */
@Singleton
class LiveStreamWebSocketManager @Inject constructor(
    private val okHttpClient: OkHttpClient,
    private val json: Json,
    private val serverUrlStore: ServerUrlStore,
    @org.jaltediye.cereqon.di.ApplicationScope private val applicationScope: CoroutineScope,
) {
    private val mutex = Mutex()
    private val isStarted = AtomicBoolean(false)
    private val reconnectAttempt = AtomicInteger(0)

    private val _reconnectAttemptCount = MutableStateFlow(0)
    val reconnectAttemptCount: StateFlow<Int> = _reconnectAttemptCount.asStateFlow()

    private var webSocket: WebSocket? = null
    private var reconnectJob: Job? = null
    private var warmupJob: Job? = null
    private var hasReceivedFirstPayload = false

    private val _connectionState =
        MutableStateFlow(StreamConnectionState.DISCONNECTED)
    val connectionState: StateFlow<StreamConnectionState> = _connectionState.asStateFlow()

    private val _windows = MutableSharedFlow<LiveWindow>(extraBufferCapacity = 64)
    val windows: SharedFlow<LiveWindow> = _windows.asSharedFlow()

    fun start() {
        if (!isStarted.compareAndSet(false, true)) {
            return
        }
        reconnectAttempt.set(0)
        _reconnectAttemptCount.value = 0
        applicationScope.launch {
            connectInternal()
        }
    }

    fun stop() {
        isStarted.set(false)
        reconnectJob?.cancel()
        reconnectJob = null
        warmupJob?.cancel()
        warmupJob = null
        closeSocket()
        _connectionState.value = StreamConnectionState.DISCONNECTED
        _reconnectAttemptCount.value = 0
    }

    private suspend fun connectInternal() {
        mutex.withLock {
            if (!isStarted.get()) return

            closeSocket()
            hasReceivedFirstPayload = false
            _connectionState.value = StreamConnectionState.CONNECTING

            val wsUrl = buildWebSocketUrl(serverUrlStore.normalized())
            val request = Request.Builder().url(wsUrl).build()

            webSocket = okHttpClient.newWebSocket(
                request,
                object : WebSocketListener() {
                    override fun onOpen(webSocket: WebSocket, response: Response) {
                        applicationScope.launch {
                            onSocketOpen()
                        }
                    }

                    override fun onMessage(webSocket: WebSocket, text: String) {
                        applicationScope.launch {
                            onSocketMessage(text)
                        }
                    }

                    override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                        webSocket.close(code, reason)
                    }

                    override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                        applicationScope.launch {
                            onSocketClosed(reason)
                        }
                    }

                    override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                        applicationScope.launch {
                            onSocketFailure(t)
                        }
                    }
                },
            )
        }
    }

    private suspend fun onSocketOpen() {
        if (!isStarted.get()) return
        _connectionState.value = StreamConnectionState.WARMUP
        scheduleWarmupTimeout()
    }

    private fun scheduleWarmupTimeout() {
        warmupJob?.cancel()
        warmupJob = applicationScope.launch {
            delay(WARMUP_TIMEOUT_MS)
            if (isStarted.get() &&
                !hasReceivedFirstPayload &&
                _connectionState.value == StreamConnectionState.WARMUP
            ) {
                Log.w(TAG, "Warmup timeout elapsed without first payload")
            }
        }
    }

    private suspend fun onSocketMessage(text: String) {
        if (!isStarted.get()) return

        val dto = try {
            json.decodeFromString(LivePayloadDto.serializer(), text)
        } catch (exception: Exception) {
            Log.e(TAG, "Failed to parse WebSocket payload", exception)
            return
        }

        val liveWindow = LivePayloadMapper.toDomain(
            dto = dto,
            channelNames = BackendDefaults.CHANNEL_NAMES,
            expectedFeatureCount = FeatureNameBuilder.expectedFeatureCount(
                BackendDefaults.CHANNEL_COUNT,
            ),
        )

        if (liveWindow == null) {
            Log.w(
                TAG,
                "Dropped frame: feature_vector size ${dto.featureVector.size} " +
                    "!= expected ${BackendDefaults.FEATURE_COUNT}",
            )
            return
        }

        if (!hasReceivedFirstPayload) {
            hasReceivedFirstPayload = true
            warmupJob?.cancel()
            reconnectAttempt.set(0)
            _reconnectAttemptCount.value = 0
        }

        _connectionState.value = StreamConnectionState.STREAMING
        _windows.emit(liveWindow)
    }

    private suspend fun onSocketClosed(reason: String) {
        Log.i(TAG, "WebSocket closed: $reason")
        scheduleReconnect(failure = null)
    }

    private suspend fun onSocketFailure(throwable: Throwable) {
        Log.e(TAG, "WebSocket failure", throwable)
        scheduleReconnect(failure = throwable)
    }

    private suspend fun scheduleReconnect(@Suppress("UNUSED_PARAMETER") failure: Throwable?) {
        warmupJob?.cancel()
        closeSocket()

        if (!isStarted.get()) {
            _connectionState.value = StreamConnectionState.DISCONNECTED
            return
        }

        val attempt = reconnectAttempt.incrementAndGet()
        _reconnectAttemptCount.value = attempt
        if (attempt > MAX_RECONNECT_ATTEMPTS_BEFORE_FAILED) {
            _connectionState.value = StreamConnectionState.FAILED
            return
        }

        _connectionState.value = StreamConnectionState.RECONNECTING
        val delayMs = computeBackoffMs(attempt)

        reconnectJob?.cancel()
        reconnectJob = applicationScope.launch {
            delay(delayMs)
            if (isActive && isStarted.get()) {
                connectInternal()
            }
        }
    }

    private fun closeSocket() {
        webSocket?.close(WEBSOCKET_CLOSE_NORMAL, "Client stopped")
        webSocket = null
    }

    private fun buildWebSocketUrl(httpBaseUrl: String): String {
        val normalized = normalizeBaseUrl(httpBaseUrl)
        val uri = URI(normalized)
        val wsScheme = when (uri.scheme?.lowercase()) {
            "https" -> "wss"
            "http" -> "ws"
            "wss", "ws" -> uri.scheme.lowercase()
            else -> "ws"
        }
        val port = if (uri.port == -1) {
            if (wsScheme == "wss") 443 else 80
        } else {
            uri.port
        }
        val path = (uri.path?.trimEnd('/') ?: "") + WS_PATH
        return "$wsScheme://${uri.host}:$port$path"
    }

    private fun normalizeBaseUrl(url: String): String {
        val trimmed = url.trim()
        return if (trimmed.endsWith("/")) trimmed else "$trimmed/"
    }

    private fun computeBackoffMs(attempt: Int): Long {
        val exponential = INITIAL_RECONNECT_DELAY_MS * (1 shl min(attempt - 1, 5))
        val capped = min(exponential, MAX_RECONNECT_DELAY_MS)
        val jitter = (capped * JITTER_FACTOR * Random.nextDouble(-1.0, 1.0)).toLong()
        return (capped + jitter).coerceAtLeast(INITIAL_RECONNECT_DELAY_MS)
    }

    companion object {
        private const val TAG = "LiveStreamWebSocket"
        private const val WS_PATH = "/ws/live"
        private const val WEBSOCKET_CLOSE_NORMAL = 1000

        private const val INITIAL_RECONNECT_DELAY_MS = 1_000L
        private const val MAX_RECONNECT_DELAY_MS = 30_000L
        private const val JITTER_FACTOR = 0.2
        private const val MAX_RECONNECT_ATTEMPTS_BEFORE_FAILED = Int.MAX_VALUE
        private val WARMUP_TIMEOUT_MS =
            (BackendDefaults.WARMUP_SEC * 1_000).toLong() + 5_000L
    }
}
