package org.jaltediye.cereqon.domain.repository

import kotlinx.coroutines.flow.Flow
import org.jaltediye.cereqon.domain.model.ThemeMode

/**
 * User preferences and server configuration persisted via DataStore.
 */
interface SettingsRepository {
    val serverBaseUrl: Flow<String>
    val onboardingCompleted: Flow<Boolean>
    val lastKnownCalibrated: Flow<Boolean>
    val themeMode: Flow<ThemeMode>

    suspend fun setServerBaseUrl(url: String)
    suspend fun setOnboardingCompleted(completed: Boolean)
    suspend fun setLastKnownCalibrated(calibrated: Boolean)
    suspend fun setThemeMode(mode: ThemeMode)
    suspend fun getServerBaseUrl(): String
    suspend fun getThemeMode(): ThemeMode
}
