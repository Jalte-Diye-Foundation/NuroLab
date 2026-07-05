package org.jaltediye.cereqon.domain.model

/**
 * Represents the outcome of a domain or repository operation.
 */
sealed class Outcome<out T> {
    data class Success<T>(val value: T) : Outcome<T>()
    data class Error(val message: String, val cause: Throwable? = null) : Outcome<Nothing>()
    data object Loading : Outcome<Nothing>()
}
