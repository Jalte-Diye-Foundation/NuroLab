package org.jaltediye.cereqon.presentation.welcome

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import org.jaltediye.cereqon.domain.model.Outcome
import org.jaltediye.cereqon.domain.repository.HealthRepository
import org.jaltediye.cereqon.domain.repository.SettingsRepository
import org.jaltediye.cereqon.presentation.state.LoadableUiState

@HiltViewModel
class WelcomeViewModel @Inject constructor(
    private val healthRepository: HealthRepository,
    private val settingsRepository: SettingsRepository,
) : ViewModel() {

    private val _uiState = MutableStateFlow(WelcomeUiState())
    val uiState: StateFlow<WelcomeUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            val storedUrl = settingsRepository.getServerBaseUrl()
            _uiState.update { it.copy(serverUrl = storedUrl) }
        }
    }

    fun onServerUrlChanged(url: String) {
        _uiState.update {
            it.copy(
                serverUrl = url,
                connectionState = LoadableUiState.Idle,
                setupComplete = false,
            )
        }
    }

    fun testConnection() {
        val url = _uiState.value.serverUrl.trim()
        if (url.isEmpty()) {
            _uiState.update {
                it.copy(
                    connectionState = LoadableUiState.Error(
                        message = "Enter a server URL to continue.",
                        retry = { testConnection() },
                    ),
                )
            }
            return
        }

        viewModelScope.launch {
            _uiState.update { it.copy(connectionState = LoadableUiState.Loading) }
            settingsRepository.setServerBaseUrl(url)
            when (val outcome = healthRepository.checkHealth()) {
                is Outcome.Success -> {
                    _uiState.update {
                        it.copy(
                            serverUrl = url,
                            connectionState = LoadableUiState.Success(outcome.value),
                        )
                    }
                }
                is Outcome.Error -> {
                    _uiState.update {
                        it.copy(
                            connectionState = LoadableUiState.Error(
                                message = outcome.message,
                                retry = { testConnection() },
                            ),
                        )
                    }
                }
                Outcome.Loading -> Unit
            }
        }
    }

    fun onContinue() {
        if (!_uiState.value.canContinue) return

        viewModelScope.launch {
            _uiState.update { it.copy(isSaving = true) }
            settingsRepository.setServerBaseUrl(_uiState.value.serverUrl)
            settingsRepository.setOnboardingCompleted(true)
            _uiState.update {
                it.copy(
                    isSaving = false,
                    setupComplete = true,
                )
            }
        }
    }
}
