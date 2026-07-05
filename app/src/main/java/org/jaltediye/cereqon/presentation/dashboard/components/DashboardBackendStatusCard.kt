package org.jaltediye.cereqon.presentation.dashboard.components

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import org.jaltediye.cereqon.R
import org.jaltediye.cereqon.domain.model.StreamConnectionState
import org.jaltediye.cereqon.presentation.dashboard.DashboardUiState
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

@Composable
fun DashboardBackendStatusCard(
    uiState: DashboardUiState,
    modifier: Modifier = Modifier,
) {
    val cardDescription = stringResource(R.string.dashboard_card_backend_status)

    DashboardCardShell(
        title = cardDescription,
        modifier = modifier.semantics { contentDescription = cardDescription },
    ) {
        DashboardLabelValue(
            label = stringResource(R.string.dashboard_backend_server_url),
            value = uiState.serverBaseUrl.ifBlank {
                stringResource(R.string.dashboard_backend_url_unknown)
            },
        )
        DashboardLabelValue(
            label = stringResource(R.string.dashboard_backend_connection),
            value = backendConnectionLabel(uiState.connectionState),
        )
        DashboardLabelValue(
            label = stringResource(R.string.dashboard_backend_last_update),
            value = formatLastUpdate(uiState.lastUpdateEpochMs),
        )
    }
}

@Composable
private fun backendConnectionLabel(state: StreamConnectionState): String {
    return when (state) {
        StreamConnectionState.DISCONNECTED ->
            stringResource(R.string.dashboard_status_disconnected)

        StreamConnectionState.CONNECTING ->
            stringResource(R.string.dashboard_status_connecting)

        StreamConnectionState.WARMUP ->
            stringResource(R.string.dashboard_status_connected)

        StreamConnectionState.STREAMING ->
            stringResource(R.string.dashboard_status_connected)

        StreamConnectionState.RECONNECTING ->
            stringResource(R.string.dashboard_status_reconnecting)

        StreamConnectionState.FAILED ->
            stringResource(R.string.dashboard_status_failed)
    }
}

@Composable
private fun formatLastUpdate(epochMs: Long?): String {
    if (epochMs == null) {
        return stringResource(R.string.dashboard_backend_last_update_none)
    }
    val formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")
    return Instant.ofEpochMilli(epochMs)
        .atZone(ZoneId.systemDefault())
        .format(formatter)
}
