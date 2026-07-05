package org.jaltediye.cereqon.presentation.state

/**
 * Offline/cache availability state for Insights and Reports.
 */
sealed interface OfflineUiState {
    data object Online : OfflineUiState

    data object OfflineNoCache : OfflineUiState

    data class OfflineWithCache(val lastSyncAtEpochMs: Long) : OfflineUiState
}
