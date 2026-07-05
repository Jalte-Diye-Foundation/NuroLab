package org.jaltediye.cereqon.presentation.insights

import org.jaltediye.cereqon.domain.model.InsightSession
import org.jaltediye.cereqon.domain.model.InsightWindowSnapshot

/**
 * UI-held snapshot of Room-backed session data observed through [InsightsViewModel].
 * Preserves ended sessions after [InsightsUiState.sessionState] stops emitting them.
 */
internal data class CachedInsightsSession(
    val session: InsightSession,
    val snapshots: List<InsightWindowSnapshot>,
    val snapshotCount: Int,
) {
    val lastUpdateEpochMs: Long?
        get() {
            val lastSnapshot = snapshots.maxByOrNull { it.capturedAtEpochMs }
            if (lastSnapshot != null) return lastSnapshot.capturedAtEpochMs
            return session.startedAtEpochMs
        }
}
