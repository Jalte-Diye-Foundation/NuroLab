package org.jaltediye.cereqon.data.repository

import org.jaltediye.cereqon.data.remote.websocket.LiveStreamWebSocketManager
import org.jaltediye.cereqon.domain.model.LiveWindow
import org.jaltediye.cereqon.domain.model.StreamConnectionState
import org.jaltediye.cereqon.domain.repository.LiveStreamRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.StateFlow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class LiveStreamRepositoryImpl @Inject constructor(
    private val webSocketManager: LiveStreamWebSocketManager,
) : LiveStreamRepository {

    override val connectionState: StateFlow<StreamConnectionState> =
        webSocketManager.connectionState

    override val reconnectAttemptCount: StateFlow<Int> =
        webSocketManager.reconnectAttemptCount

    override val windows: Flow<LiveWindow> = webSocketManager.windows

    override fun start() {
        webSocketManager.start()
    }

    override fun stop() {
        webSocketManager.stop()
    }
}
