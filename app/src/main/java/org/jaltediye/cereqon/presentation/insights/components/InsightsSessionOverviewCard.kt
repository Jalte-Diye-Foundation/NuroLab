package org.jaltediye.cereqon.presentation.insights.components

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import org.jaltediye.cereqon.R
import org.jaltediye.cereqon.domain.model.InsightSession
import org.jaltediye.cereqon.domain.model.StreamConnectionState
import org.jaltediye.cereqon.presentation.dashboard.components.DashboardCardShell
import org.jaltediye.cereqon.presentation.dashboard.components.DashboardEmptyState
import org.jaltediye.cereqon.presentation.dashboard.components.DashboardLabelValue
import org.jaltediye.cereqon.presentation.insights.formatEpochMs
import org.jaltediye.cereqon.presentation.insights.formatSessionDuration
import org.jaltediye.cereqon.presentation.state.LoadableUiState
import org.jaltediye.cereqon.presentation.state.OfflineUiState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.History

@Composable
internal fun InsightsLiveSessionOverviewCard(
    sessionState: LoadableUiState<InsightSession?>,
    windowCount: Int,
    connectionState: StreamConnectionState,
    offlineState: OfflineUiState,
    lastUpdateEpochMs: Long?,
    nowEpochMs: Long,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
) {
    DashboardCardShell(
        title = stringResource(R.string.insights_live_session_title),
        modifier = modifier,
    ) {
        when (sessionState) {
            LoadableUiState.Idle,
            LoadableUiState.Loading,
            -> {
                CircularProgressIndicator(
                    modifier = Modifier.fillMaxWidth(),
                    color = MaterialTheme.colorScheme.primary,
                )
            }

            is LoadableUiState.Error -> {
                Text(
                    text = sessionState.message,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.error,
                )
                TextButton(onClick = onRetry) {
                    Text(text = stringResource(R.string.insights_retry))
                }
            }

            is LoadableUiState.Success -> {
                val session = sessionState.data
                if (session == null) {
                    DashboardEmptyState(
                        message = stringResource(R.string.insights_no_session),
                        icon = Icons.Outlined.History,
                    )
                } else {
                    InsightsSessionFields(
                        session = session,
                        windowCount = windowCount,
                        showConnectionStatus = true,
                        connectionState = connectionState,
                        offlineState = offlineState,
                        lastUpdateEpochMs = lastUpdateEpochMs,
                        nowEpochMs = nowEpochMs,
                    )
                }
            }
        }
    }
}

@Composable
internal fun InsightsStoredSessionOverviewCard(
    session: InsightSession,
    windowCount: Int,
    lastUpdateEpochMs: Long?,
    nowEpochMs: Long,
    modifier: Modifier = Modifier,
) {
    DashboardCardShell(
        title = stringResource(R.string.insights_stored_session_title),
        modifier = modifier,
    ) {
        InsightsSessionFields(
            session = session,
            windowCount = windowCount,
            showConnectionStatus = false,
            connectionState = StreamConnectionState.DISCONNECTED,
            offlineState = OfflineUiState.Online,
            lastUpdateEpochMs = lastUpdateEpochMs,
            nowEpochMs = nowEpochMs,
        )
    }
}

@Composable
private fun InsightsSessionFields(
    session: InsightSession,
    windowCount: Int,
    showConnectionStatus: Boolean,
    connectionState: StreamConnectionState,
    offlineState: OfflineUiState,
    lastUpdateEpochMs: Long?,
    nowEpochMs: Long,
) {
    DashboardLabelValue(
        label = stringResource(R.string.insights_active_session),
        value = stringResource(
            R.string.insights_session_summary,
            session.id,
            formatEpochMs(session.startedAtEpochMs),
        ),
    )
    DashboardLabelValue(
        label = stringResource(R.string.insights_session_duration),
        value = formatSessionDuration(
            startedAtEpochMs = session.startedAtEpochMs,
            endedAtEpochMs = session.endedAtEpochMs,
            nowEpochMs = nowEpochMs,
        ),
    )
    DashboardLabelValue(
        label = stringResource(R.string.insights_window_count),
        value = windowCount.toString(),
    )
    if (showConnectionStatus) {
        DashboardLabelValue(
            label = stringResource(R.string.insights_connection_status),
            value = connectionStatusLabel(connectionState, offlineState),
        )
    }
    DashboardLabelValue(
        label = stringResource(R.string.insights_calibration_status),
        value = if (session.calibratedAtStart) {
            stringResource(R.string.insights_calibration_yes)
        } else {
            stringResource(R.string.insights_calibration_no)
        },
    )
    DashboardLabelValue(
        label = stringResource(R.string.insights_last_update),
        value = formatEpochMs(lastUpdateEpochMs),
    )
}

@Composable
private fun connectionStatusLabel(
    connectionState: StreamConnectionState,
    offlineState: OfflineUiState,
): String {
    val streamLabel = when (connectionState) {
        StreamConnectionState.DISCONNECTED ->
            stringResource(R.string.dashboard_status_disconnected)

        StreamConnectionState.CONNECTING ->
            stringResource(R.string.dashboard_status_connecting)

        StreamConnectionState.WARMUP ->
            stringResource(R.string.dashboard_status_warmup)

        StreamConnectionState.STREAMING ->
            stringResource(R.string.dashboard_status_streaming)

        StreamConnectionState.RECONNECTING ->
            stringResource(R.string.dashboard_status_reconnecting)

        StreamConnectionState.FAILED ->
            stringResource(R.string.dashboard_status_failed)
    }

    return when (offlineState) {
        OfflineUiState.Online -> streamLabel
        OfflineUiState.OfflineNoCache -> stringResource(
            R.string.insights_connection_offline_no_cache,
            streamLabel,
        )

        is OfflineUiState.OfflineWithCache -> stringResource(
            R.string.insights_connection_offline_with_cache,
            streamLabel,
            formatEpochMs(offlineState.lastSyncAtEpochMs),
        )
    }
}
