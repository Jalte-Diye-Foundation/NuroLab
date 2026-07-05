package org.jaltediye.cereqon.presentation.insights

import org.jaltediye.cereqon.domain.model.InsightSession
import org.jaltediye.cereqon.domain.model.InsightWindowSnapshot
import org.jaltediye.cereqon.domain.model.StreamConnectionState
import org.jaltediye.cereqon.presentation.state.LoadableUiState
import org.jaltediye.cereqon.presentation.state.OfflineUiState

data class InsightsUiState(
    val connectionState: StreamConnectionState = StreamConnectionState.DISCONNECTED,
    val serverBaseUrl: String = "",
    val offlineState: OfflineUiState = OfflineUiState.OfflineNoCache,
    val sessionState: LoadableUiState<InsightSession?> = LoadableUiState.Idle,
    val snapshotsState: LoadableUiState<List<InsightWindowSnapshot>> = LoadableUiState.Idle,
    val snapshotCount: Int = 0,
) {
    val isStreaming: Boolean =
        connectionState == StreamConnectionState.STREAMING

    val hasActiveSession: Boolean =
        sessionState is LoadableUiState.Success && sessionState.data != null

    val hasCachedSnapshots: Boolean =
        snapshotsState is LoadableUiState.Success && snapshotsState.data.isNotEmpty()

    val lastCachedAtEpochMs: Long?
        get() {
            val snapshots = (snapshotsState as? LoadableUiState.Success)?.data.orEmpty()
            val lastSnapshot = snapshots.maxByOrNull { it.capturedAtEpochMs }
            if (lastSnapshot != null) return lastSnapshot.capturedAtEpochMs
            return (sessionState as? LoadableUiState.Success)?.data?.startedAtEpochMs
        }
}
