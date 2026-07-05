package org.jaltediye.cereqon.presentation.state

/**
 * Generic loadable UI wrapper for one-shot or refreshable content.
 */
sealed interface LoadableUiState<out T> {
    data object Idle : LoadableUiState<Nothing>
    data object Loading : LoadableUiState<Nothing>
    data class Success<T>(val data: T) : LoadableUiState<T>
    data class Error(val message: String, val retry: (() -> Unit)? = null) : LoadableUiState<Nothing>
}
