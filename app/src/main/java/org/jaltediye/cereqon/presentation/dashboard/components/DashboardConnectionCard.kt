package org.jaltediye.cereqon.presentation.dashboard.components

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CloudOff
import androidx.compose.material.icons.outlined.ErrorOutline
import androidx.compose.material.icons.outlined.Sensors
import androidx.compose.material.icons.outlined.Wifi
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import org.jaltediye.cereqon.R
import org.jaltediye.cereqon.domain.model.StreamConnectionState
import org.jaltediye.cereqon.presentation.components.CereqonPrimaryButton
import org.jaltediye.cereqon.presentation.dashboard.DashboardUiState
import org.jaltediye.cereqon.presentation.theme.CereqonSignalError
import org.jaltediye.cereqon.presentation.theme.CereqonSignalLive
import org.jaltediye.cereqon.presentation.theme.CereqonSignalSuccess
import org.jaltediye.cereqon.presentation.theme.CereqonSignalWarning

@Composable
fun DashboardConnectionCard(
    uiState: DashboardUiState,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val (dotColor, pulse, icon, label) = connectionVisuals(uiState.connectionState)
    val statusDescription = stringResource(
        R.string.dashboard_connection_content_description,
        label,
    )

    DashboardCardShell(
        title = stringResource(R.string.dashboard_card_connection),
        modifier = modifier.semantics { contentDescription = statusDescription },
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                ConnectionPulseDot(color = dotColor, pulse = pulse)
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = CereqonSignalLive,
                    modifier = Modifier.size(24.dp),
                )
                Text(
                    text = label,
                    style = MaterialTheme.typography.titleSmall,
                    color = MaterialTheme.colorScheme.onSurface,
                )
            }

            DashboardStatusStrip(uiState = uiState)

            AnimatedVisibility(
                visible = uiState.isFailed,
                enter = fadeIn(),
                exit = fadeOut(),
            ) {
                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Text(
                        text = uiState.errorMessage
                            ?: stringResource(R.string.dashboard_stream_error_generic),
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.error,
                    )
                    CereqonPrimaryButton(
                        text = stringResource(R.string.dashboard_retry_connection),
                        onClick = onRetry,
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
            }
        }
    }
}

@Composable
private fun ConnectionPulseDot(
    color: Color,
    pulse: Boolean,
) {
    val infiniteTransition = rememberInfiniteTransition(label = "connectionPulse")
    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 0.85f,
        targetValue = 1.15f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 900),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "pulseScale",
    )

    Box(
        modifier = Modifier
            .size(10.dp)
            .scale(if (pulse) pulseScale else 1f)
            .alpha(if (pulse) 0.9f else 1f)
            .background(color, CircleShape),
    )
}

@Composable
private fun connectionVisuals(
    state: StreamConnectionState,
): ConnectionVisuals {
    return when (state) {
        StreamConnectionState.DISCONNECTED -> ConnectionVisuals(
            dotColor = MaterialTheme.colorScheme.outline,
            pulse = false,
            icon = Icons.Outlined.CloudOff,
            label = stringResource(R.string.dashboard_status_disconnected),
        )

        StreamConnectionState.CONNECTING -> ConnectionVisuals(
            dotColor = CereqonSignalWarning,
            pulse = true,
            icon = Icons.Outlined.Wifi,
            label = stringResource(R.string.dashboard_status_connecting),
        )

        StreamConnectionState.WARMUP -> ConnectionVisuals(
            dotColor = CereqonSignalWarning,
            pulse = true,
            icon = Icons.Outlined.Sensors,
            label = stringResource(R.string.dashboard_status_warmup),
        )

        StreamConnectionState.STREAMING -> ConnectionVisuals(
            dotColor = CereqonSignalSuccess,
            pulse = false,
            icon = Icons.Outlined.Sensors,
            label = stringResource(R.string.dashboard_status_streaming),
        )

        StreamConnectionState.RECONNECTING -> ConnectionVisuals(
            dotColor = CereqonSignalWarning,
            pulse = true,
            icon = Icons.Outlined.Wifi,
            label = stringResource(R.string.dashboard_status_reconnecting),
        )

        StreamConnectionState.FAILED -> ConnectionVisuals(
            dotColor = CereqonSignalError,
            pulse = false,
            icon = Icons.Outlined.ErrorOutline,
            label = stringResource(R.string.dashboard_status_failed),
        )
    }
}

private data class ConnectionVisuals(
    val dotColor: Color,
    val pulse: Boolean,
    val icon: ImageVector,
    val label: String,
)
