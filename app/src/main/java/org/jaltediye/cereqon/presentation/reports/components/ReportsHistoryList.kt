package org.jaltediye.cereqon.presentation.reports.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Description
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import org.jaltediye.cereqon.R
import org.jaltediye.cereqon.domain.model.Report
import org.jaltediye.cereqon.presentation.dashboard.components.DashboardCardShell
import org.jaltediye.cereqon.presentation.dashboard.components.DashboardEmptyState
import org.jaltediye.cereqon.presentation.state.LoadableUiState

@Composable
internal fun ReportsHistoryList(
    reportsState: LoadableUiState<List<Report>>,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val title = stringResource(R.string.reports_history_title)
    DashboardCardShell(
        title = title,
        modifier = modifier.semantics { contentDescription = title },
    ) {
        when (reportsState) {
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
                    text = reportsState.message,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.error,
                )
                TextButton(onClick = onRetry) {
                    Text(text = stringResource(R.string.reports_retry))
                }
            }

            is LoadableUiState.Success -> {
                val reports = reportsState.data
                if (reports.isEmpty()) {
                    DashboardEmptyState(
                        message = stringResource(R.string.reports_history_empty),
                        icon = Icons.Outlined.Description,
                    )
                } else {
                    Column(
                        modifier = Modifier.fillMaxWidth(),
                        verticalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        reports.forEach { report ->
                            ReportsHistoryItem(report = report)
                        }
                    }
                }
            }
        }
    }
}
