package org.jaltediye.cereqon.presentation.calibration

import org.jaltediye.cereqon.domain.model.BaselineResult
import org.jaltediye.cereqon.domain.model.StreamConnectionState
import org.jaltediye.cereqon.presentation.state.LoadableUiState

enum class CalibrationPhase {
    INTRO,
    CONNECTING,
    WARMUP,
    COLLECTING,
    SUBMITTING,
    SUCCESS,
    ERROR,
}

data class CalibrationUiState(
    val phase: CalibrationPhase = CalibrationPhase.INTRO,
    val streamConnectionState: StreamConnectionState = StreamConnectionState.DISCONNECTED,
    val remainingSeconds: Int = CalibrationUiState.CALIBRATION_DURATION_SECONDS,
    val collectedWindows: Int = 0,
    val progressFraction: Float = 0f,
    val submitState: LoadableUiState<BaselineResult> = LoadableUiState.Idle,
    val errorMessage: String? = null,
) {
    val isActive: Boolean =
        phase == CalibrationPhase.CONNECTING ||
            phase == CalibrationPhase.WARMUP ||
            phase == CalibrationPhase.COLLECTING ||
            phase == CalibrationPhase.SUBMITTING

    val formattedRemainingTime: String
        get() {
            val minutes = remainingSeconds / 60
            val seconds = remainingSeconds % 60
            return "%d:%02d".format(minutes, seconds)
        }

    companion object {
        const val CALIBRATION_DURATION_SECONDS = 300
    }
}
