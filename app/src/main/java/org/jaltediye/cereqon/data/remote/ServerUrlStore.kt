package org.jaltediye.cereqon.data.remote

import org.jaltediye.cereqon.BuildConfig
import okhttp3.HttpUrl.Companion.toHttpUrlOrNull
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Thread-safe holder for the active REST/WebSocket base URL.
 * Updated by [org.jaltediye.cereqon.data.local.preferences.SettingsRepositoryImpl].
 */
@Singleton
class ServerUrlStore @Inject constructor() {

    @Volatile
    var baseUrl: String = BuildConfig.DEFAULT_SERVER_BASE_URL
        private set

    fun update(baseUrl: String) {
        this.baseUrl = normalize(baseUrl)
    }

    fun normalized(): String = normalize(baseUrl)

    private fun normalize(url: String): String {
        val trimmed = url.trim()
        return if (trimmed.endsWith("/")) trimmed else "$trimmed/"
    }

    fun asHttpUrl() = normalized().toHttpUrlOrNull()
        ?: throw IllegalArgumentException("Invalid server base URL: $baseUrl")
}
