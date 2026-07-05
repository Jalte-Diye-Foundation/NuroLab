package org.jaltediye.cereqon.presentation.state

import org.jaltediye.cereqon.domain.model.StreamConnectionState

/**
 * Combined network and WebSocket connection state for live screens.
 */
data class ConnectionUiState(
    val streamState: StreamConnectionState = StreamConnectionState.DISCONNECTED,
    val isNetworkAvailable: Boolean = true,
    val backendReachable: Boolean = false,
    val reconnectAttempt: Int = 0,
) {
    val isLive: Boolean
        get() = streamState == StreamConnectionState.STREAMING

    val isWarmup: Boolean
        get() = streamState == StreamConnectionState.WARMUP

    val isReconnecting: Boolean
        get() = streamState == StreamConnectionState.RECONNECTING
}
