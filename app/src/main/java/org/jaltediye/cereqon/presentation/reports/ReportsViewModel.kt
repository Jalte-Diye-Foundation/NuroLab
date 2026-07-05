package org.jaltediye.cereqon.presentation.reports

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.CoroutineDispatcher
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
import kotlinx.coroutines.withContext
import org.jaltediye.cereqon.di.IoDispatcher
import org.jaltediye.cereqon.domain.model.InsightSession
import org.jaltediye.cereqon.domain.model.Outcome
import org.jaltediye.cereqon.domain.model.Report
import org.jaltediye.cereqon.domain.model.StreamConnectionState
import org.jaltediye.cereqon.domain.repository.InsightsRepository
import org.jaltediye.cereqon.domain.repository.LiveStreamRepository
import org.jaltediye.cereqon.domain.repository.ReportsExportRepository
import org.jaltediye.cereqon.domain.repository.ReportsRepository
import org.jaltediye.cereqon.domain.repository.SettingsRepository
import org.jaltediye.cereqon.presentation.state.LoadableUiState
import org.jaltediye.cereqon.presentation.state.OfflineUiState

/**
 * Reports presentation layer — **read-only** with respect to the live WebSocket.
 *
 * Stream ownership lives in [org.jaltediye.cereqon.presentation.dashboard.DashboardViewModel]
 * (and [org.jaltediye.cereqon.presentation.calibration.CalibrationViewModel] during calibration).
 * This ViewModel observes [LiveStreamRepository.connectionState] for offline semantics only;
 * it never calls [LiveStreamRepository.start] or [LiveStreamRepository.stop].
 */
@HiltViewModel
class ReportsViewModel @Inject constructor(
    private val reportsRepository: ReportsRepository,
    private val reportsExportRepository: ReportsExportRepository,
    private val insightsRepository: InsightsRepository,
    private val liveStreamRepository: LiveStreamRepository,
    private val settingsRepository: SettingsRepository,
    @IoDispatcher private val ioDispatcher: CoroutineDispatcher,
) : ViewModel() {

    private val _uiState = MutableStateFlow(ReportsUiState())
    val uiState: StateFlow<ReportsUiState> = _uiState.asStateFlow()

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
        observeCachedReports()
    }

    fun refresh() {
        observeCachedReports()
    }

    fun exportSessionToPdf(sessionId: Long) {
        runExport(sessionId) { reportsExportRepository.exportSessionToPdf(sessionId) }
    }

    fun exportSessionToCsv(sessionId: Long) {
        runExport(sessionId) { reportsExportRepository.exportSessionToCsv(sessionId) }
    }

    fun exportActiveSessionToPdf() {
        val sessionId = resolveExportSessionId() ?: return
        exportSessionToPdf(sessionId)
    }

    fun exportActiveSessionToCsv() {
        val sessionId = resolveExportSessionId() ?: return
        exportSessionToCsv(sessionId)
    }

    private fun resolveExportSessionId(): Long? {
        val sessionId = (uiState.value.sessionState as? LoadableUiState.Success)?.data?.id
        if (sessionId == null) {
            _uiState.update {
                it.copy(
                    exportState = LoadableUiState.Error(
                        message = "No active session available to export.",
                    ),
                )
            }
        }
        return sessionId
    }

    private fun runExport(
        sessionId: Long,
        export: suspend () -> Outcome<Report>,
    ) {
        viewModelScope.launch {
            _uiState.update { it.copy(exportState = LoadableUiState.Loading) }
            val outcome = withContext(ioDispatcher) { export() }
            _uiState.update { current ->
                current.copy(
                    exportState = when (outcome) {
                        is Outcome.Success -> LoadableUiState.Success(outcome.value)
                        is Outcome.Error -> LoadableUiState.Error(
                            message = outcome.message,
                            retry = if (outcome.message.contains("active session", ignoreCase = true)) {
                                null
                            } else {
                                { runExport(sessionId, export) }
                            },
                        )
                        Outcome.Loading -> LoadableUiState.Loading
                    },
                )
            }
        }
    }

    private fun observeCachedReports() {
        cacheObservationJob?.cancel()
        cacheObservationJob = viewModelScope.launch {
            combine(
                reportsRepository.observeReports(),
                insightsRepository.observeActiveSession().flatMapLatest { session ->
                    if (session == null) {
                        flowOf(ReportsSessionSnapshot(null, 0))
                    } else {
                        insightsRepository.observeWindowSnapshotCount(session.id).flatMapLatest { count ->
                            flowOf(ReportsSessionSnapshot(session, count))
                        }
                    }
                },
            ) { reports, sessionSnapshot ->
                ReportsCacheSnapshot(reports, sessionSnapshot.session, sessionSnapshot.snapshotCount)
            }
                .onStart {
                    _uiState.update {
                        it.copy(
                            reportsState = LoadableUiState.Loading,
                            sessionState = LoadableUiState.Loading,
                        )
                    }
                }
                .catch { exception ->
                    val message = exception.message ?: "Failed to load cached reports."
                    _uiState.update {
                        it.copy(
                            reportsState = LoadableUiState.Error(
                                message = message,
                                retry = { refresh() },
                            ),
                            sessionState = LoadableUiState.Error(
                                message = message,
                                retry = { refresh() },
                            ),
                        )
                    }
                }
                .collect { cache ->
                    _uiState.update { current ->
                        val updated = current.copy(
                            reportsState = LoadableUiState.Success(cache.reports),
                            sessionState = LoadableUiState.Success(cache.session),
                            snapshotCount = cache.snapshotCount,
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
        state: ReportsUiState,
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

    private data class ReportsSessionSnapshot(
        val session: InsightSession?,
        val snapshotCount: Int,
    )

    private data class ReportsCacheSnapshot(
        val reports: List<Report>,
        val session: InsightSession?,
        val snapshotCount: Int,
    )
}
