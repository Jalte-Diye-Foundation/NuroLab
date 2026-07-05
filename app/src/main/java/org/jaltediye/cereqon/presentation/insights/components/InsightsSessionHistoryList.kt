package org.jaltediye.cereqon.presentation.insights.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.History
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import org.jaltediye.cereqon.R
import org.jaltediye.cereqon.domain.model.InsightSession
import org.jaltediye.cereqon.presentation.dashboard.components.DashboardCardShell
import org.jaltediye.cereqon.presentation.dashboard.components.DashboardEmptyState
import org.jaltediye.cereqon.presentation.insights.CachedInsightsSession
import org.jaltediye.cereqon.presentation.insights.formatEpochMs

@Composable
internal fun InsightsSessionHistoryList(
    sessions: List<CachedInsightsSession>,
    activeSessionId: Long?,
    selectedSessionId: Long?,
    onSelectLive: () -> Unit,
    onSelectSession: (Long) -> Unit,
    modifier: Modifier = Modifier,
) {
    val title = stringResource(R.string.insights_history_title)
    DashboardCardShell(
        title = title,
        modifier = modifier.semantics { contentDescription = title },
    ) {
        if (sessions.isEmpty()) {
            DashboardEmptyState(
                message = stringResource(R.string.insights_history_empty),
                icon = Icons.Outlined.History,
            )
            return@DashboardCardShell
        }

        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            if (activeSessionId != null) {
                InsightsSessionHistoryItem(
                    label = stringResource(R.string.insights_history_live_item),
                    detail = sessions.firstOrNull { it.session.id == activeSessionId }
                        ?.let { formatSessionDetail(it.session) }
                        ?: stringResource(R.string.insights_history_live_detail),
                    selected = selectedSessionId == null || selectedSessionId == activeSessionId,
                    onClick = onSelectLive,
                )
            }

            sessions
                .filter { it.session.id != activeSessionId }
                .forEach { cached ->
                    InsightsSessionHistoryItem(
                        label = stringResource(
                            R.string.insights_history_session_item,
                            cached.session.id,
                        ),
                        detail = formatSessionDetail(cached.session),
                        selected = selectedSessionId == cached.session.id,
                        onClick = { onSelectSession(cached.session.id) },
                    )
                }
        }
    }
}

@Composable
private fun formatSessionDetail(session: InsightSession): String {
    val started = formatEpochMs(session.startedAtEpochMs)
    val ended = session.endedAtEpochMs?.let { formatEpochMs(it) }
    return if (ended != null) {
        stringResource(R.string.insights_history_session_range, started, ended)
    } else {
        stringResource(R.string.insights_history_session_started, started)
    }
}

@Composable
private fun InsightsSessionHistoryItem(
    label: String,
    detail: String,
    selected: Boolean,
    onClick: () -> Unit,
) {
    val containerColor = if (selected) {
        MaterialTheme.colorScheme.primaryContainer
    } else {
        MaterialTheme.colorScheme.surfaceContainerHighest
    }
    val contentColor = if (selected) {
        MaterialTheme.colorScheme.onPrimaryContainer
    } else {
        MaterialTheme.colorScheme.onSurface
    }

    androidx.compose.material3.Surface(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.medium,
        color = containerColor,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Text(
                text = label,
                style = MaterialTheme.typography.titleSmall,
                color = contentColor,
            )
            Text(
                text = detail,
                style = MaterialTheme.typography.bodySmall,
                color = contentColor.copy(alpha = 0.85f),
            )
        }
    }
}
