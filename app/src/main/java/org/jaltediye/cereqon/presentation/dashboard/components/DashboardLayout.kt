package org.jaltediye.cereqon.presentation.dashboard.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.BoxWithConstraints
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.heading
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import org.jaltediye.cereqon.R
import org.jaltediye.cereqon.domain.model.LiveWindow
import org.jaltediye.cereqon.presentation.dashboard.DashboardTimelineHistory
import org.jaltediye.cereqon.presentation.dashboard.DashboardUiState

private val WideLayoutBreakpoint = 720.dp

@Composable
fun DashboardScrollContent(
    uiState: DashboardUiState,
    onRetry: () -> Unit,
    onNavigateToSettings: () -> Unit = {},
    modifier: Modifier = Modifier,
) {
    BoxWithConstraints(modifier = modifier) {
        val useWideLayout = maxWidth >= WideLayoutBreakpoint
        val horizontalPadding = if (useWideLayout) 32.dp else 20.dp
        val cardSpacing = if (useWideLayout) 20.dp else 16.dp

        Column(
            modifier = Modifier
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = horizontalPadding, vertical = 20.dp),
            verticalArrangement = Arrangement.spacedBy(cardSpacing),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column(
                    modifier = Modifier.weight(1f),
                    verticalArrangement = Arrangement.spacedBy(6.dp),
                ) {
                    Text(
                        text = stringResource(R.string.dashboard_title),
                        style = MaterialTheme.typography.headlineLarge,
                        color = MaterialTheme.colorScheme.onBackground,
                        modifier = Modifier.semantics { heading() },
                    )
                    Text(
                        text = stringResource(R.string.dashboard_subtitle),
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                TextButton(onClick = onNavigateToSettings) {
                    Text(text = stringResource(R.string.settings_title))
                }
            }

            if (useWideLayout) {
                WideDashboardGrid(
                    uiState = uiState,
                    latestWindow = uiState.latestWindow,
                    history = uiState.history,
                    onRetry = onRetry,
                    cardSpacing = cardSpacing,
                )
            } else {
                NarrowDashboardStack(
                    uiState = uiState,
                    latestWindow = uiState.latestWindow,
                    history = uiState.history,
                    onRetry = onRetry,
                )
            }
        }
    }
}

@Composable
private fun NarrowDashboardStack(
    uiState: DashboardUiState,
    latestWindow: LiveWindow?,
    history: DashboardTimelineHistory,
    onRetry: () -> Unit,
) {
    DashboardConnectionCard(uiState = uiState, onRetry = onRetry)
    DashboardBackendStatusCard(uiState = uiState)
    DashboardRiskCard(latestWindow = latestWindow)
    DashboardPredictionCard(latestWindow = latestWindow)
    DashboardFeatureVectorCard(latestWindow = latestWindow)
    DashboardChartsSection(history = history)
}

@Composable
private fun WideDashboardGrid(
    uiState: DashboardUiState,
    latestWindow: LiveWindow?,
    history: DashboardTimelineHistory,
    onRetry: () -> Unit,
    cardSpacing: androidx.compose.ui.unit.Dp,
) {
    Column(verticalArrangement = Arrangement.spacedBy(cardSpacing)) {
        DashboardConnectionCard(uiState = uiState, onRetry = onRetry)
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(cardSpacing),
        ) {
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(cardSpacing),
            ) {
                DashboardBackendStatusCard(uiState = uiState)
                DashboardRiskCard(latestWindow = latestWindow)
                DashboardPredictionCard(latestWindow = latestWindow)
            }
            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(cardSpacing),
            ) {
                DashboardFeatureVectorCard(latestWindow = latestWindow)
                DashboardChartsSection(history = history)
            }
        }
    }
}
