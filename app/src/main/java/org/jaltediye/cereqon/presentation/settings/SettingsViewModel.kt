package org.jaltediye.cereqon.presentation.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import org.jaltediye.cereqon.BuildConfig
import org.jaltediye.cereqon.domain.model.Outcome
import org.jaltediye.cereqon.domain.model.ThemeMode
import org.jaltediye.cereqon.domain.repository.HealthRepository
import org.jaltediye.cereqon.domain.repository.SettingsRepository
import org.jaltediye.cereqon.presentation.state.LoadableUiState

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val settingsRepository: SettingsRepository,
    private val healthRepository: HealthRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(
        SettingsUiState(appVersion = BuildConfig.VERSION_NAME),
    )
    val uiState: StateFlow<SettingsUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            settingsRepository.serverBaseUrl.collect { url ->
                _uiState.update { it.copy(serverUrl = url, serverUrlSaved = false) }
            }
        }
        viewModelScope.launch {
            settingsRepository.themeMode.collect { themeMode ->
                _uiState.update { it.copy(themeMode = themeMode) }
            }
        }
        refreshBackendVersion()
    }

    fun onServerUrlChanged(url: String) {
        _uiState.update { it.copy(serverUrl = url, serverUrlSaved = false) }
    }

    fun saveServerUrl() {
        val url = _uiState.value.serverUrl.trim()
        if (url.isEmpty()) {
            _uiState.update {
                it.copy(
                    backendVersionState = LoadableUiState.Error(
                        message = "Enter a server URL to save.",
                    ),
                )
            }
            return
        }

        viewModelScope.launch {
            _uiState.update { it.copy(isSavingServerUrl = true, serverUrlSaved = false) }
            settingsRepository.setServerBaseUrl(url)
            _uiState.update {
                it.copy(
                    serverUrl = url,
                    isSavingServerUrl = false,
                    serverUrlSaved = true,
                )
            }
            refreshBackendVersion()
        }
    }

    fun onThemeModeSelected(themeMode: ThemeMode) {
        if (_uiState.value.themeMode == themeMode) return
        viewModelScope.launch {
            settingsRepository.setThemeMode(themeMode)
        }
    }

    fun refreshBackendVersion() {
        viewModelScope.launch {
            _uiState.update { it.copy(backendVersionState = LoadableUiState.Loading) }
            healthRepository.getCachedHealth()?.let { cached ->
                _uiState.update {
                    it.copy(backendVersionState = LoadableUiState.Success(cached.version))
                }
            }
            when (val outcome = healthRepository.checkHealth()) {
                is Outcome.Success -> {
                    _uiState.update {
                        it.copy(backendVersionState = LoadableUiState.Success(outcome.value.version))
                    }
                }
                is Outcome.Error -> {
                    _uiState.update {
                        it.copy(
                            backendVersionState = LoadableUiState.Error(
                                message = outcome.message,
                                retry = { refreshBackendVersion() },
                            ),
                        )
                    }
                }
                Outcome.Loading -> Unit
            }
        }
    }
}
