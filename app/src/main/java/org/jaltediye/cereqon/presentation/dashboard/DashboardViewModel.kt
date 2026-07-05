package org.jaltediye.cereqon.presentation.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import org.jaltediye.cereqon.di.IoDispatcher
import org.jaltediye.cereqon.domain.model.LiveWindow
import org.jaltediye.cereqon.domain.model.StreamConnectionState
import org.jaltediye.cereqon.domain.repository.InsightsRepository
import org.jaltediye.cereqon.domain.repository.LiveStreamRepository
import org.jaltediye.cereqon.domain.repository.SettingsRepository

@HiltViewModel
class DashboardViewModel @Inject constructor(
    private val liveStreamRepository: LiveStreamRepository,
    private val settingsRepository: SettingsRepository,
    private val insightsRepository: InsightsRepository,
    @IoDispatcher private val ioDispatcher: CoroutineDispatcher,
) : ViewModel() {

    private val _uiState = MutableStateFlow(DashboardUiState())
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    private var monitoringSessionId: Long? = null

    init {
        viewModelScope.launch {
            val serverUrl = settingsRepository.getServerBaseUrl()
            _uiState.update { it.copy(serverBaseUrl = serverUrl) }
        }
        viewModelScope.launch {
            liveStreamRepository.connectionState.collect { connectionState ->
                _uiState.update { current ->
                    current.copy(
                        connectionState = connectionState,
                        errorMessage = if (connectionState == StreamConnectionState.FAILED) {
                            current.errorMessage
                                ?: STREAM_CONNECTION_FAILED_MESSAGE
                        } else {
                            null
                        },
                    )
                }
            }
        }
        viewModelScope.launch {
            liveStreamRepository.reconnectAttemptCount.collect { attempt ->
                _uiState.update { it.copy(reconnectAttemptCount = attempt) }
            }
        }
        viewModelScope.launch {
            liveStreamRepository.windows.collect { window ->
                _uiState.update { current ->
                    val deviation = window.deviation
                    val firstFeature = window.features.values.firstOrNull()
                    current.copy(
                        latestWindow = window,
                        lastUpdateEpochMs = window.receivedAtEpochMs,
                        secondsSinceLastPacket = 0L,
                        history = current.history.appendFromWindow(
                            mahalanobis = deviation?.mahalanobis,
                            riskTier = deviation?.riskTier?.value,
                            firstFeature = firstFeature,
                        ),
                    )
                }
                persistWindowSnapshot(window)
            }
        }
        viewModelScope.launch {
            while (isActive) {
                delay(PACKET_TIMER_TICK_MS)
                _uiState.update { current ->
                    val last = current.lastUpdateEpochMs ?: return@update current
                    val elapsed = ((System.currentTimeMillis() - last) / 1000L)
                        .coerceAtLeast(0L)
                    current.copy(secondsSinceLastPacket = elapsed)
                }
            }
        }
        connectStream()
    }

    fun refresh() {
        if (_uiState.value.isRefreshing) return

        viewModelScope.launch {
            _uiState.update { it.copy(isRefreshing = true, errorMessage = null) }
            liveStreamRepository.stop()
            val serverUrl = settingsRepository.getServerBaseUrl()
            _uiState.update { it.copy(serverBaseUrl = serverUrl) }
            ensureMonitoringSession()
            liveStreamRepository.start()
            withTimeoutOrNull(REFRESH_SETTLE_TIMEOUT_MS) {
                liveStreamRepository.connectionState.first { state ->
                    state == StreamConnectionState.STREAMING ||
                        state == StreamConnectionState.FAILED
                }
            }
            _uiState.update { it.copy(isRefreshing = false) }
        }
    }

    fun connectStream() {
        _uiState.update {
            it.copy(
                errorMessage = null,
                latestWindow = null,
                lastUpdateEpochMs = null,
                secondsSinceLastPacket = null,
                history = DashboardTimelineHistory(),
            )
        }
        viewModelScope.launch {
            ensureMonitoringSession()
            liveStreamRepository.start()
        }
    }

    fun retryConnection() {
        liveStreamRepository.stop()
        connectStream()
    }

    override fun onCleared() {
        liveStreamRepository.stop()
        val sessionId = monitoringSessionId
        monitoringSessionId = null
        if (sessionId != null) {
            runBlocking {
                withContext(ioDispatcher) {
                    insightsRepository.endSession(sessionId, System.currentTimeMillis())
                }
            }
        }
        super.onCleared()
    }

    private suspend fun ensureMonitoringSession() {
        val serverUrl = settingsRepository.getServerBaseUrl()
        val calibratedAtStart = settingsRepository.lastKnownCalibrated.first()
        monitoringSessionId = insightsRepository.startSession(
            serverBaseUrl = serverUrl,
            calibratedAtStart = calibratedAtStart,
        )
    }

    private fun persistWindowSnapshot(window: LiveWindow) {
        val sessionId = monitoringSessionId ?: return
        viewModelScope.launch {
            insightsRepository.recordWindowSnapshot(sessionId, window)
        }
    }

    companion object {
        private const val STREAM_CONNECTION_FAILED_MESSAGE =
            "Live stream connection failed. Check the server and try again."
        private const val PACKET_TIMER_TICK_MS = 1_000L
        private const val REFRESH_SETTLE_TIMEOUT_MS = 10_000L
    }
}
