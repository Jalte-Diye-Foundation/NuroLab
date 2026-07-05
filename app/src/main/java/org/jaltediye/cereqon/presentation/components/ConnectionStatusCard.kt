package org.jaltediye.cereqon.presentation.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.material.icons.outlined.CloudOff
import androidx.compose.material.icons.outlined.ErrorOutline
import androidx.compose.material.icons.outlined.Wifi
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import org.jaltediye.cereqon.R
import org.jaltediye.cereqon.domain.model.HealthStatus
import org.jaltediye.cereqon.presentation.state.LoadableUiState
import org.jaltediye.cereqon.presentation.theme.CereqonSignalError
import org.jaltediye.cereqon.presentation.theme.CereqonSignalLive
import org.jaltediye.cereqon.presentation.theme.CereqonSignalSuccess
import org.jaltediye.cereqon.presentation.theme.CereqonSignalWarning

@Composable
fun ConnectionStatusCard(
    connectionState: LoadableUiState<HealthStatus>,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val shape = RoundedCornerShape(16.dp)
    val borderColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.35f)

    Column(
        modifier = modifier
            .fillMaxWidth()
            .background(MaterialTheme.colorScheme.surface, shape)
            .border(width = 1.dp, color = borderColor, shape = shape)
            .padding(20.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        when (connectionState) {
            LoadableUiState.Idle -> StatusRow(
                dotColor = MaterialTheme.colorScheme.outline,
                pulse = false,
                icon = Icons.Outlined.CloudOff,
                message = stringResource(R.string.welcome_connection_idle),
            )

            LoadableUiState.Loading -> StatusRow(
                dotColor = CereqonSignalWarning,
                pulse = true,
                icon = Icons.Outlined.Wifi,
                message = stringResource(R.string.welcome_connection_checking),
            )

            is LoadableUiState.Success -> StatusRow(
                dotColor = CereqonSignalSuccess,
                pulse = false,
                icon = Icons.Outlined.Wifi,
                message = stringResource(
                    R.string.welcome_connection_success,
                    connectionState.data.version,
                ),
            )

            is LoadableUiState.Error -> {
                StatusRow(
                    dotColor = CereqonSignalError,
                    pulse = false,
                    icon = Icons.Outlined.ErrorOutline,
                    message = connectionState.message,
                )
                TextButton(onClick = onRetry) {
                    Text(text = stringResource(R.string.welcome_test_connection))
                }
            }
        }
    }
}

@Composable
private fun StatusRow(
    dotColor: Color,
    pulse: Boolean,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    message: String,
) {
    val infiniteTransition = rememberInfiniteTransition(label = "pulse")
    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 0.85f,
        targetValue = 1.15f,
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = 900),
            repeatMode = RepeatMode.Reverse,
        ),
        label = "pulseScale",
    )
    val animatedDotColor by animateColorAsState(
        targetValue = dotColor,
        animationSpec = tween(300),
        label = "dotColor",
    )

    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Box(
            modifier = Modifier
                .size(10.dp)
                .scale(if (pulse) pulseScale else 1f)
                .alpha(if (pulse) 0.9f else 1f)
                .background(animatedDotColor, CircleShape),
        )
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = CereqonSignalLive,
            modifier = Modifier.size(22.dp),
        )
        Text(
            text = message,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurface,
        )
    }
}
