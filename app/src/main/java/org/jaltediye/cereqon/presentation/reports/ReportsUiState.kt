package org.jaltediye.cereqon.presentation.reports

import org.jaltediye.cereqon.domain.model.InsightSession
import org.jaltediye.cereqon.domain.model.Report
import org.jaltediye.cereqon.domain.model.StreamConnectionState
import org.jaltediye.cereqon.presentation.state.LoadableUiState
import org.jaltediye.cereqon.presentation.state.OfflineUiState

data class ReportsUiState(
    val connectionState: StreamConnectionState = StreamConnectionState.DISCONNECTED,
    val serverBaseUrl: String = "",
    val offlineState: OfflineUiState = OfflineUiState.OfflineNoCache,
    val reportsState: LoadableUiState<List<Report>> = LoadableUiState.Idle,
    val sessionState: LoadableUiState<InsightSession?> = LoadableUiState.Idle,
    val snapshotCount: Int = 0,
    val exportState: LoadableUiState<Report> = LoadableUiState.Idle,
) {
    val isStreaming: Boolean =
        connectionState == StreamConnectionState.STREAMING

    val hasReports: Boolean =
        reportsState is LoadableUiState.Success && reportsState.data.isNotEmpty()

    val hasActiveSession: Boolean =
        sessionState is LoadableUiState.Success && sessionState.data != null

    val lastCachedAtEpochMs: Long?
        get() {
            val reports = (reportsState as? LoadableUiState.Success)?.data.orEmpty()
            val newestReport = reports.maxByOrNull { it.createdAtEpochMs }
            if (newestReport != null) return newestReport.createdAtEpochMs
            return (sessionState as? LoadableUiState.Success)?.data?.startedAtEpochMs
        }
}
