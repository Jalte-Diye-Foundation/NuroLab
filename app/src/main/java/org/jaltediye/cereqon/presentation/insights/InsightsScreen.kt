package org.jaltediye.cereqon.presentation.insights

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.History
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableLongStateOf
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.delay
import org.jaltediye.cereqon.R
import org.jaltediye.cereqon.presentation.dashboard.components.DashboardCardShell
import org.jaltediye.cereqon.presentation.dashboard.components.DashboardEmptyState
import org.jaltediye.cereqon.presentation.insights.components.InsightsLiveSessionOverviewCard
import org.jaltediye.cereqon.presentation.insights.components.InsightsSessionHistoryList
import org.jaltediye.cereqon.presentation.insights.components.InsightsStoredSessionOverviewCard
import org.jaltediye.cereqon.presentation.state.LoadableUiState

@Composable
fun InsightsScreen(
    uiState: InsightsUiState,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier,
) {
    val sessionCache = remember { mutableStateMapOf<Long, CachedInsightsSession>() }
    var selectedSessionId by remember { mutableStateOf<Long?>(null) }
    var nowEpochMs by remember { mutableLongStateOf(System.currentTimeMillis()) }
    var previousActiveSessionId by remember { mutableStateOf<Long?>(null) }

    val activeSession = (uiState.sessionState as? LoadableUiState.Success)?.data
    val activeSessionId = activeSession?.id
    val isViewingLive = selectedSessionId == null ||
        (activeSessionId != null && selectedSessionId == activeSessionId)

    LaunchedEffect(uiState.sessionState, uiState.snapshotsState, uiState.snapshotCount) {
        val session = (uiState.sessionState as? LoadableUiState.Success)?.data ?: return@LaunchedEffect
        val snapshots = (uiState.snapshotsState as? LoadableUiState.Success)?.data.orEmpty()
        sessionCache[session.id] = CachedInsightsSession(
            session = session,
            snapshots = snapshots,
            snapshotCount = uiState.snapshotCount,
        )
    }

    LaunchedEffect(activeSessionId) {
        val endedId = previousActiveSessionId
        if (activeSessionId == null && endedId != null) {
            val cached = sessionCache[endedId]
            if (cached != null && cached.session.endedAtEpochMs == null) {
                val endedAtEpochMs = cached.lastUpdateEpochMs ?: System.currentTimeMillis()
                sessionCache[endedId] = cached.copy(
                    session = cached.session.copy(endedAtEpochMs = endedAtEpochMs),
                )
            }
        }
        previousActiveSessionId = activeSessionId
    }

    LaunchedEffect(isViewingLive, activeSession?.endedAtEpochMs) {
        val shouldTick = isViewingLive && activeSession != null && activeSession.endedAtEpochMs == null
        if (!shouldTick) return@LaunchedEffect
        while (true) {
            delay(1_000)
            nowEpochMs = System.currentTimeMillis()
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
            verticalArrangement = Arrangement.spacedBy(20.dp),
        ) {
            Text(
                text = stringResource(R.string.insights_title),
                style = MaterialTheme.typography.headlineMedium,
                color = MaterialTheme.colorScheme.onBackground,
            )
            Text(
                text = stringResource(R.string.insights_subtitle),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            InsightsSessionHistoryList(
                sessions = sessionCache.values.sortedByDescending { it.session.startedAtEpochMs },
                activeSessionId = activeSessionId,
                selectedSessionId = selectedSessionId,
                onSelectLive = { selectedSessionId = null },
                onSelectSession = { sessionId -> selectedSessionId = sessionId },
            )

            if (isViewingLive) {
                InsightsLiveSessionOverviewCard(
                    sessionState = uiState.sessionState,
                    windowCount = uiState.snapshotCount,
                    connectionState = uiState.connectionState,
                    offlineState = uiState.offlineState,
                    lastUpdateEpochMs = uiState.lastCachedAtEpochMs,
                    nowEpochMs = nowEpochMs,
                    onRetry = onRetry,
                )
            } else {
                val cached = selectedSessionId?.let { sessionCache[it] }
                if (cached != null) {
                    InsightsStoredSessionOverviewCard(
                        session = cached.session,
                        windowCount = cached.snapshotCount,
                        lastUpdateEpochMs = cached.lastUpdateEpochMs,
                        nowEpochMs = nowEpochMs,
                    )
                } else {
                    DashboardCardShell(title = stringResource(R.string.insights_stored_session_title)) {
                        DashboardEmptyState(
                            message = stringResource(R.string.insights_session_unavailable),
                            icon = Icons.Outlined.History,
                        )
                    }
                }
            }
        }
    }
}
