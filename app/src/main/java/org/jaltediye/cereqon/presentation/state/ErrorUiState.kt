package org.jaltediye.cereqon.presentation.state

/**
 * Structured error presentation for feature screens.
 */
sealed interface ErrorUiState {
    data object None : ErrorUiState

    data class Transient(val message: String) : ErrorUiState

    data class Blocking(
        val message: String,
        val actionLabel: String,
        val onAction: () -> Unit,
    ) : ErrorUiState

    data class PredictionPartial(
        val errors: Map<String, String>,
    ) : ErrorUiState
}
