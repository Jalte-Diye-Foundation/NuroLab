package org.jaltediye.cereqon.presentation.welcome

import org.jaltediye.cereqon.domain.model.HealthStatus
import org.jaltediye.cereqon.presentation.state.LoadableUiState

data class WelcomeUiState(
    val serverUrl: String = "",
    val connectionState: LoadableUiState<HealthStatus> = LoadableUiState.Idle,
    val isSaving: Boolean = false,
    val setupComplete: Boolean = false,
) {
    val canContinue: Boolean =
        connectionState is LoadableUiState.Success && !isSaving && !setupComplete

    val isTestingConnection: Boolean =
        connectionState is LoadableUiState.Loading || isSaving
}
