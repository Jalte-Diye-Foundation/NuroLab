package org.jaltediye.cereqon.presentation.insights

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.flow.onStart
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import org.jaltediye.cereqon.domain.model.InsightSession
import org.jaltediye.cereqon.domain.model.InsightWindowSnapshot
import org.jaltediye.cereqon.domain.model.StreamConnectionState
import org.jaltediye.cereqon.domain.repository.InsightsRepository
import org.jaltediye.cereqon.domain.repository.LiveStreamRepository
import org.jaltediye.cereqon.domain.repository.SettingsRepository
import org.jaltediye.cereqon.presentation.state.LoadableUiState
import org.jaltediye.cereqon.presentation.state.OfflineUiState

/**
 * Insights presentation layer — **read-only** with respect to the live WebSocket.
 *
 * Stream ownership lives in [org.jaltediye.cereqon.presentation.dashboard.DashboardViewModel]
 * (and [org.jaltediye.cereqon.presentation.calibration.CalibrationViewModel] during calibration).
 * This ViewModel observes [LiveStreamRepository.connectionState] for offline semantics only;
 * it never calls [LiveStreamRepository.start] or [LiveStreamRepository.stop].
 */
@HiltViewModel
class InsightsViewModel @Inject constructor(
    private val insightsRepository: InsightsRepository,
    private val liveStreamRepository: LiveStreamRepository,
    private val settingsRepository: SettingsRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(InsightsUiState())
    val uiState: StateFlow<InsightsUiState> = _uiState.asStateFlow()

    private var cacheObservationJob: Job? = null

    init {
        viewModelScope.launch {
            val serverUrl = settingsRepository.getServerBaseUrl()
            _uiState.update { it.copy(serverBaseUrl = serverUrl) }
        }
        viewModelScope.launch {
            liveStreamRepository.connectionState.collect { connectionState ->
                _uiState.update { current ->
                    current.copy(
                        connectionState = connectionState,
                        offlineState = resolveOfflineState(connectionState, current),
                    )
                }
            }
        }
        observeCachedInsights()
    }

    fun refresh() {
        observeCachedInsights()
    }

    private fun observeCachedInsights() {
        cacheObservationJob?.cancel()
        cacheObservationJob = viewModelScope.launch {
            insightsRepository.observeActiveSession()
                .flatMapLatest { session ->
                    if (session == null) {
                        flowOf(InsightsCacheSnapshot(null, emptyList(), 0))
                    } else {
                        combine(
                            insightsRepository.observeWindowSnapshots(session.id),
                            insightsRepository.observeWindowSnapshotCount(session.id),
                        ) { snapshots, count ->
                            InsightsCacheSnapshot(session, snapshots, count)
                        }
                    }
                }
                .onStart {
                    _uiState.update {
                        it.copy(
                            sessionState = LoadableUiState.Loading,
                            snapshotsState = LoadableUiState.Loading,
                        )
                    }
                }
                .catch { exception ->
                    val message = exception.message ?: "Failed to load cached insights."
                    _uiState.update {
                        it.copy(
                            sessionState = LoadableUiState.Error(
                                message = message,
                                retry = { refresh() },
                            ),
                            snapshotsState = LoadableUiState.Error(
                                message = message,
                                retry = { refresh() },
                            ),
                        )
                    }
                }
                .collect { cache ->
                    _uiState.update { current ->
                        val updated = current.copy(
                            sessionState = LoadableUiState.Success(cache.session),
                            snapshotsState = LoadableUiState.Success(cache.snapshots),
                            snapshotCount = cache.count,
                        )
                        updated.copy(
                            offlineState = resolveOfflineState(
                                updated.connectionState,
                                updated,
                            ),
                        )
                    }
                }
        }
    }

    private fun resolveOfflineState(
        connectionState: StreamConnectionState,
        state: InsightsUiState,
    ): OfflineUiState {
        return when (connectionState) {
            StreamConnectionState.STREAMING,
            StreamConnectionState.WARMUP,
            StreamConnectionState.CONNECTING,
            StreamConnectionState.RECONNECTING,
            -> OfflineUiState.Online

            StreamConnectionState.DISCONNECTED,
            StreamConnectionState.FAILED,
            -> {
                val lastCached = state.lastCachedAtEpochMs
                if (lastCached != null) {
                    OfflineUiState.OfflineWithCache(lastCached)
                } else {
                    OfflineUiState.OfflineNoCache
                }
            }
        }
    }

    private data class InsightsCacheSnapshot(
        val session: InsightSession?,
        val snapshots: List<InsightWindowSnapshot>,
        val count: Int,
    )
}
