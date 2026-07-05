package org.jaltediye.cereqon.presentation.calibration

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Job
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.jaltediye.cereqon.di.IoDispatcher
import org.jaltediye.cereqon.domain.model.LiveWindow
import org.jaltediye.cereqon.domain.model.Outcome
import org.jaltediye.cereqon.domain.model.StreamConnectionState
import org.jaltediye.cereqon.domain.repository.CalibrationRepository
import org.jaltediye.cereqon.domain.repository.InsightsRepository
import org.jaltediye.cereqon.domain.repository.LiveStreamRepository
import org.jaltediye.cereqon.domain.repository.SettingsRepository
import org.jaltediye.cereqon.presentation.state.LoadableUiState

sealed interface CalibrationEvent {
    data object NavigateToDashboard : CalibrationEvent
}

@HiltViewModel
class CalibrationViewModel @Inject constructor(
    private val liveStreamRepository: LiveStreamRepository,
    private val calibrationRepository: CalibrationRepository,
    private val insightsRepository: InsightsRepository,
    private val settingsRepository: SettingsRepository,
    @IoDispatcher private val ioDispatcher: CoroutineDispatcher,
) : ViewModel() {

    private val _uiState = MutableStateFlow(CalibrationUiState())
    val uiState: StateFlow<CalibrationUiState> = _uiState.asStateFlow()

    private val _events = Channel<CalibrationEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    private val collectedVectors = mutableListOf<List<Float>>()
    private var countdownJob: Job? = null
    private var collectionStarted = false
    private var finishingCollection = false
    private var calibrationSessionId: Long? = null

    init {
        viewModelScope.launch {
            liveStreamRepository.connectionState.collect { connectionState ->
                _uiState.update { it.copy(streamConnectionState = connectionState) }
                handleConnectionState(connectionState)
            }
        }
        viewModelScope.launch {
            liveStreamRepository.windows.collect { window ->
                handleWindow(window)
            }
        }
    }

    fun startCalibration() {
        val phase = _uiState.value.phase
        if (phase != CalibrationPhase.INTRO && phase != CalibrationPhase.ERROR) return

        resetCollectionState()
        _uiState.update {
            it.copy(
                phase = CalibrationPhase.CONNECTING,
                errorMessage = null,
                submitState = LoadableUiState.Idle,
            )
        }
        viewModelScope.launch {
            beginCalibrationSession()
            liveStreamRepository.start()
        }
    }

    fun retry() {
        viewModelScope.launch {
            endCalibrationSession()
            liveStreamRepository.stop()
            collectionStarted = false
            finishingCollection = false
            countdownJob?.cancel()
            countdownJob = null
            collectedVectors.clear()
            _uiState.value = CalibrationUiState()
            startCalibration()
        }
    }

    private fun resetCollectionState() {
        collectionStarted = false
        finishingCollection = false
        countdownJob?.cancel()
        countdownJob = null
        collectedVectors.clear()
        _uiState.update {
            it.copy(
                remainingSeconds = CalibrationUiState.CALIBRATION_DURATION_SECONDS,
                collectedWindows = 0,
                progressFraction = 0f,
            )
        }
    }

    private fun handleConnectionState(connectionState: StreamConnectionState) {
        val phase = _uiState.value.phase
        if (phase != CalibrationPhase.CONNECTING &&
            phase != CalibrationPhase.WARMUP &&
            phase != CalibrationPhase.COLLECTING
        ) {
            return
        }

        when (connectionState) {
            StreamConnectionState.CONNECTING -> {
                _uiState.update { it.copy(phase = CalibrationPhase.CONNECTING) }
            }

            StreamConnectionState.WARMUP -> {
                _uiState.update { it.copy(phase = CalibrationPhase.WARMUP) }
            }

            StreamConnectionState.STREAMING -> {
                beginCollection()
            }

            StreamConnectionState.FAILED -> {
                failCalibration(
                    message = "Live stream connection failed. Check the server and try again.",
                )
            }

            StreamConnectionState.RECONNECTING -> Unit

            StreamConnectionState.DISCONNECTED -> {
                if (phase == CalibrationPhase.COLLECTING && !finishingCollection) {
                    failCalibration(
                        message = "Live stream disconnected during calibration.",
                    )
                }
            }
        }
    }

    private fun beginCollection() {
        if (collectionStarted) return
        collectionStarted = true
        _uiState.update { it.copy(phase = CalibrationPhase.COLLECTING) }
        startCountdown()
    }

    private fun startCountdown() {
        countdownJob?.cancel()
        countdownJob = viewModelScope.launch {
            var remaining = CalibrationUiState.CALIBRATION_DURATION_SECONDS
            while (remaining > 0 && isActive) {
                delay(1_000)
                remaining -= 1
                _uiState.update {
                    it.copy(
                        remainingSeconds = remaining,
                        progressFraction = 1f - (
                            remaining.toFloat() /
                                CalibrationUiState.CALIBRATION_DURATION_SECONDS
                            ),
                    )
                }
            }
            if (isActive) {
                finishCollection()
            }
        }
    }

    private fun handleWindow(window: LiveWindow) {
        if (_uiState.value.phase != CalibrationPhase.COLLECTING) return

        val vector = window.features.values
        if (vector.isEmpty()) return

        collectedVectors.add(vector)
        _uiState.update { it.copy(collectedWindows = collectedVectors.size) }
        persistWindowSnapshot(window)
    }

    private fun finishCollection() {
        finishingCollection = true
        countdownJob?.cancel()
        countdownJob = null
        liveStreamRepository.stop()

        if (collectedVectors.isEmpty()) {
            viewModelScope.launch {
                endCalibrationSession()
            }
            failCalibration(
                message = "No feature windows were collected. Ensure the backend stream is active and retry.",
            )
            return
        }

        _uiState.update {
            it.copy(
                phase = CalibrationPhase.SUBMITTING,
                submitState = LoadableUiState.Loading,
            )
        }

        viewModelScope.launch {
            endCalibrationSession()
            when (val outcome = calibrationRepository.submitBaseline(collectedVectors.toList())) {
                is Outcome.Success -> {
                    _uiState.update {
                        it.copy(
                            phase = CalibrationPhase.SUCCESS,
                            submitState = LoadableUiState.Success(outcome.value),
                            progressFraction = 1f,
                            remainingSeconds = 0,
                        )
                    }
                    _events.send(CalibrationEvent.NavigateToDashboard)
                }

                is Outcome.Error -> {
                    _uiState.update {
                        it.copy(
                            phase = CalibrationPhase.ERROR,
                            submitState = LoadableUiState.Error(
                                message = outcome.message,
                                retry = { retry() },
                            ),
                            errorMessage = outcome.message,
                        )
                    }
                }

                Outcome.Loading -> Unit
            }
        }
    }

    private fun failCalibration(message: String) {
        countdownJob?.cancel()
        countdownJob = null
        collectionStarted = false
        liveStreamRepository.stop()
        viewModelScope.launch {
            endCalibrationSession()
        }
        _uiState.update {
            it.copy(
                phase = CalibrationPhase.ERROR,
                errorMessage = message,
                submitState = LoadableUiState.Error(
                    message = message,
                    retry = { retry() },
                ),
            )
        }
    }

    override fun onCleared() {
        countdownJob?.cancel()
        liveStreamRepository.stop()
        val sessionId = calibrationSessionId
        calibrationSessionId = null
        if (sessionId != null) {
            runBlocking {
                withContext(ioDispatcher) {
                    insightsRepository.endSession(sessionId, System.currentTimeMillis())
                }
            }
        }
        super.onCleared()
    }

    private suspend fun beginCalibrationSession() {
        endCalibrationSession()
        val serverUrl = settingsRepository.getServerBaseUrl()
        calibrationSessionId = insightsRepository.startSession(
            serverBaseUrl = serverUrl,
            calibratedAtStart = false,
        )
    }

    private suspend fun endCalibrationSession() {
        val sessionId = calibrationSessionId ?: return
        insightsRepository.endSession(sessionId, System.currentTimeMillis())
        calibrationSessionId = null
    }

    private fun persistWindowSnapshot(window: LiveWindow) {
        val sessionId = calibrationSessionId ?: return
        viewModelScope.launch {
            insightsRepository.recordWindowSnapshot(sessionId, window)
        }
    }
}
