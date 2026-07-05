package org.jaltediye.cereqon.presentation.dashboard.components

import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Autorenew
import androidx.compose.material.icons.outlined.NetworkCheck
import androidx.compose.material.icons.outlined.Schedule
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import org.jaltediye.cereqon.R
import org.jaltediye.cereqon.presentation.dashboard.DashboardConnectionQuality
import org.jaltediye.cereqon.presentation.dashboard.DashboardUiState
import org.jaltediye.cereqon.presentation.theme.CereqonSignalError
import org.jaltediye.cereqon.presentation.theme.CereqonSignalSuccess
import org.jaltediye.cereqon.presentation.theme.CereqonSignalWarning

@Composable
fun DashboardStatusStrip(
    uiState: DashboardUiState,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        StatusChip(
            icon = Icons.Outlined.NetworkCheck,
            label = stringResource(R.string.dashboard_quality_label),
            value = qualityLabel(uiState.connectionQuality),
            indicatorColor = qualityColor(uiState.connectionQuality),
            contentDescription = stringResource(
                R.string.dashboard_quality_content_description,
                qualityLabel(uiState.connectionQuality),
            ),
        )

        AnimatedContent(
            targetState = uiState.secondsSinceLastPacket,
            transitionSpec = { fadeIn() togetherWith fadeOut() },
            label = "packetTimer",
        ) { seconds ->
            StatusChip(
                icon = Icons.Outlined.Schedule,
                label = stringResource(R.string.dashboard_packet_timer_label),
                value = packetTimerLabel(seconds, uiState.lastUpdateEpochMs != null),
                indicatorColor = MaterialTheme.colorScheme.primary,
                contentDescription = stringResource(
                    R.string.dashboard_packet_timer_content_description,
                    packetTimerLabel(seconds, uiState.lastUpdateEpochMs != null),
                ),
            )
        }

        if (uiState.isAutoReconnecting) {
            StatusChip(
                icon = Icons.Outlined.Autorenew,
                label = stringResource(R.string.dashboard_auto_reconnect_label),
                value = stringResource(
                    R.string.dashboard_auto_reconnect_attempt,
                    uiState.reconnectAttemptCount.coerceAtLeast(1),
                ),
                indicatorColor = CereqonSignalWarning,
                contentDescription = stringResource(
                    R.string.dashboard_auto_reconnect_content_description,
                    uiState.reconnectAttemptCount.coerceAtLeast(1),
                ),
            )
        }
    }
}

@Composable
private fun StatusChip(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    value: String,
    indicatorColor: androidx.compose.ui.graphics.Color,
    contentDescription: String,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(MaterialTheme.colorScheme.surfaceContainerHighest)
            .padding(horizontal = 12.dp, vertical = 10.dp)
            .semantics { this.contentDescription = contentDescription },
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        Box(
            modifier = Modifier
                .size(8.dp)
                .clip(CircleShape)
                .background(indicatorColor),
        )
        Icon(
            imageVector = icon,
            contentDescription = null,
            modifier = Modifier.size(18.dp),
            tint = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = label,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text(
                text = value,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurface,
            )
        }
    }
}

@Composable
private fun qualityLabel(quality: DashboardConnectionQuality): String {
    return when (quality) {
        DashboardConnectionQuality.UNKNOWN ->
            stringResource(R.string.dashboard_quality_unknown)
        DashboardConnectionQuality.EXCELLENT ->
            stringResource(R.string.dashboard_quality_excellent)
        DashboardConnectionQuality.GOOD ->
            stringResource(R.string.dashboard_quality_good)
        DashboardConnectionQuality.DEGRADED ->
            stringResource(R.string.dashboard_quality_degraded)
        DashboardConnectionQuality.POOR ->
            stringResource(R.string.dashboard_quality_poor)
        DashboardConnectionQuality.OFFLINE ->
            stringResource(R.string.dashboard_quality_offline)
    }
}

@Composable
private fun qualityColor(quality: DashboardConnectionQuality): androidx.compose.ui.graphics.Color {
    return when (quality) {
        DashboardConnectionQuality.EXCELLENT,
        DashboardConnectionQuality.GOOD,
        -> CereqonSignalSuccess

        DashboardConnectionQuality.DEGRADED -> CereqonSignalWarning
        DashboardConnectionQuality.POOR,
        DashboardConnectionQuality.OFFLINE,
        -> CereqonSignalError

        DashboardConnectionQuality.UNKNOWN ->
            MaterialTheme.colorScheme.outline
    }
}

@Composable
private fun packetTimerLabel(seconds: Long?, hasPacket: Boolean): String {
    return when {
        !hasPacket -> stringResource(R.string.dashboard_packet_timer_none)
        seconds == null -> stringResource(R.string.dashboard_packet_timer_none)
        seconds == 0L -> stringResource(R.string.dashboard_packet_timer_just_now)
        else -> stringResource(R.string.dashboard_packet_timer_ago, seconds)
    }
}
