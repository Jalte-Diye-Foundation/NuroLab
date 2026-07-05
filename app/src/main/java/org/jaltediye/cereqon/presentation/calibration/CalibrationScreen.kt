package org.jaltediye.cereqon.presentation.calibration

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ErrorOutline
import androidx.compose.material.icons.outlined.Psychology
import androidx.compose.material.icons.outlined.Timer
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import org.jaltediye.cereqon.R
import org.jaltediye.cereqon.domain.model.StreamConnectionState
import org.jaltediye.cereqon.presentation.components.CereqonPrimaryButton
import org.jaltediye.cereqon.presentation.state.LoadableUiState
import org.jaltediye.cereqon.presentation.theme.CereqonTheme

@Composable
fun CalibrationScreen(
    onNavigateToDashboard: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: CalibrationViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    LaunchedEffect(viewModel) {
        viewModel.events.collect { event ->
            when (event) {
                CalibrationEvent.NavigateToDashboard -> onNavigateToDashboard()
            }
        }
    }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        containerColor = MaterialTheme.colorScheme.background,
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 24.dp, vertical = 32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Icon(
                imageVector = Icons.Outlined.Psychology,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
                modifier = Modifier.size(48.dp),
            )

            Text(
                text = stringResource(R.string.calibration_title),
                style = MaterialTheme.typography.headlineMedium,
                color = MaterialTheme.colorScheme.onBackground,
                textAlign = TextAlign.Center,
            )

            Text(
                text = stringResource(R.string.calibration_subtitle),
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center,
            )

            when (uiState.phase) {
                CalibrationPhase.INTRO -> IntroContent(onStart = viewModel::startCalibration)

                CalibrationPhase.CONNECTING,
                CalibrationPhase.WARMUP,
                CalibrationPhase.COLLECTING,
                -> ActiveCalibrationContent(uiState = uiState)

                CalibrationPhase.SUBMITTING -> SubmittingContent(uiState = uiState)

                CalibrationPhase.SUCCESS -> SuccessContent(uiState = uiState)

                CalibrationPhase.ERROR -> ErrorContent(
                    message = uiState.errorMessage.orEmpty(),
                    onRetry = viewModel::retry,
                )
            }
        }
    }
}

@Composable
private fun IntroContent(onStart: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface,
        ),
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(
                text = stringResource(R.string.calibration_intro_heading),
                style = MaterialTheme.typography.titleMedium,
            )
            Text(
                text = stringResource(R.string.calibration_intro_body),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }

    CereqonPrimaryButton(
        text = stringResource(R.string.calibration_start),
        onClick = onStart,
        modifier = Modifier.fillMaxWidth(),
    )
}

@Composable
private fun ActiveCalibrationContent(uiState: CalibrationUiState) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface,
        ),
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            Text(
                text = streamStatusLabel(uiState),
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.primary,
            )

            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                RowMetric(
                    icon = Icons.Outlined.Timer,
                    label = stringResource(R.string.calibration_time_remaining),
                    value = uiState.formattedRemainingTime,
                )
                Text(
                    text = stringResource(
                        R.string.calibration_windows_collected,
                        uiState.collectedWindows,
                    ),
                    style = MaterialTheme.typography.bodyMedium,
                )
            }

            LinearProgressIndicator(
                progress = { uiState.progressFraction.coerceIn(0f, 1f) },
                modifier = Modifier.fillMaxWidth(),
                color = MaterialTheme.colorScheme.primary,
                trackColor = MaterialTheme.colorScheme.surfaceVariant,
            )

            Text(
                text = stringResource(R.string.calibration_relax_hint),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun RowMetric(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    value: String,
) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(
            text = label,
            style = MaterialTheme.typography.labelMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.primary,
            )
            Text(
                text = value,
                style = MaterialTheme.typography.displaySmall,
                color = MaterialTheme.colorScheme.onSurface,
            )
        }
    }
}

@Composable
private fun SubmittingContent(uiState: CalibrationUiState) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface,
        ),
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Text(
                text = stringResource(R.string.calibration_submitting),
                style = MaterialTheme.typography.titleMedium,
            )
            Text(
                text = stringResource(
                    R.string.calibration_submitting_detail,
                    uiState.collectedWindows,
                ),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                textAlign = TextAlign.Center,
            )
        }
    }

    CereqonPrimaryButton(
        text = stringResource(R.string.calibration_submitting),
        onClick = {},
        modifier = Modifier.fillMaxWidth(),
        enabled = false,
        loading = true,
    )
}

@Composable
private fun SuccessContent(uiState: CalibrationUiState) {
    val result = (uiState.submitState as? LoadableUiState.Success)?.data

    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer,
        ),
    ) {
        Column(
            modifier = Modifier.padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(
                text = stringResource(R.string.calibration_success_title),
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onPrimaryContainer,
            )
            Text(
                text = stringResource(
                    R.string.calibration_success_detail,
                    result?.nWindows ?: uiState.collectedWindows,
                ),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onPrimaryContainer,
            )
        }
    }
}

@Composable
private fun ErrorContent(
    message: String,
    onRetry: () -> Unit,
) {
    AnimatedVisibility(
        visible = true,
        enter = fadeIn(),
        exit = fadeOut(),
    ) {
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(16.dp),
            colors = CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.errorContainer,
            ),
        ) {
            Column(
                modifier = Modifier.padding(20.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                androidx.compose.foundation.layout.Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Icon(
                        imageVector = Icons.Outlined.ErrorOutline,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.onErrorContainer,
                    )
                    Text(
                        text = stringResource(R.string.calibration_error_title),
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.onErrorContainer,
                    )
                }
                Text(
                    text = message.ifBlank { stringResource(R.string.calibration_error_generic) },
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onErrorContainer,
                )
                TextButton(onClick = onRetry) {
                    Text(text = stringResource(R.string.calibration_retry))
                }
            }
        }
    }

    Spacer(modifier = Modifier.height(8.dp))

    CereqonPrimaryButton(
        text = stringResource(R.string.calibration_retry),
        onClick = onRetry,
        modifier = Modifier.fillMaxWidth(),
    )
}

@Composable
private fun streamStatusLabel(uiState: CalibrationUiState): String {
    return when (uiState.phase) {
        CalibrationPhase.CONNECTING -> stringResource(R.string.calibration_status_connecting)
        CalibrationPhase.WARMUP -> stringResource(R.string.calibration_status_warmup)
        CalibrationPhase.COLLECTING -> stringResource(R.string.calibration_status_collecting)
        else -> when (uiState.streamConnectionState) {
            StreamConnectionState.RECONNECTING ->
                stringResource(R.string.calibration_status_reconnecting)
            else -> stringResource(R.string.calibration_status_collecting)
        }
    }
}

@Preview(showBackground = true)
@Composable
private fun CalibrationIntroPreview() {
    CereqonTheme {
        IntroContent(onStart = {})
    }
}

@Preview(showBackground = true)
@Composable
private fun CalibrationActivePreview() {
    CereqonTheme {
        ActiveCalibrationContent(
            uiState = CalibrationUiState(
                phase = CalibrationPhase.COLLECTING,
                streamConnectionState = StreamConnectionState.STREAMING,
                remainingSeconds = 245,
                collectedWindows = 12,
                progressFraction = 0.18f,
            ),
        )
    }
}
