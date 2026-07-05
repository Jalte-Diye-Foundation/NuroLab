package org.jaltediye.cereqon.presentation.settings

import org.jaltediye.cereqon.domain.model.ThemeMode
import org.jaltediye.cereqon.presentation.state.LoadableUiState

data class SettingsUiState(
    val serverUrl: String = "",
    val themeMode: ThemeMode = ThemeMode.SYSTEM,
    val appVersion: String = "",
    val backendVersionState: LoadableUiState<String> = LoadableUiState.Idle,
    val isSavingServerUrl: Boolean = false,
    val serverUrlSaved: Boolean = false,
)
