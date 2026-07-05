package org.jaltediye.cereqon.presentation.dashboard

import org.jaltediye.cereqon.domain.model.LiveWindow
import org.jaltediye.cereqon.domain.model.StreamConnectionState

data class DashboardUiState(
    val connectionState: StreamConnectionState = StreamConnectionState.DISCONNECTED,
    val latestWindow: LiveWindow? = null,
    val serverBaseUrl: String = "",
    val lastUpdateEpochMs: Long? = null,
    val secondsSinceLastPacket: Long? = null,
    val reconnectAttemptCount: Int = 0,
    val isRefreshing: Boolean = false,
    val errorMessage: String? = null,
    val history: DashboardTimelineHistory = DashboardTimelineHistory(),
) {
    val connectionQuality: DashboardConnectionQuality =
        resolveConnectionQuality(connectionState, secondsSinceLastPacket)

    val isAutoReconnecting: Boolean =
        connectionState == StreamConnectionState.RECONNECTING

    val isLoading: Boolean =
        connectionState == StreamConnectionState.CONNECTING || isRefreshing

    val isWarmup: Boolean =
        connectionState == StreamConnectionState.WARMUP

    val isReconnecting: Boolean =
        connectionState == StreamConnectionState.RECONNECTING

    val isStreaming: Boolean =
        connectionState == StreamConnectionState.STREAMING

    val isFailed: Boolean =
        connectionState == StreamConnectionState.FAILED

    val isDisconnected: Boolean =
        connectionState == StreamConnectionState.DISCONNECTED

    val hasPayload: Boolean = latestWindow != null
}
