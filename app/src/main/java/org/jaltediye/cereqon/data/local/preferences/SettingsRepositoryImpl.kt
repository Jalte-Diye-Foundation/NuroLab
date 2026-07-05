package org.jaltediye.cereqon.data.local.preferences

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import org.jaltediye.cereqon.BuildConfig
import org.jaltediye.cereqon.data.remote.ServerUrlStore
import org.jaltediye.cereqon.domain.model.ThemeMode
import org.jaltediye.cereqon.domain.repository.SettingsRepository
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

private val Context.settingsDataStore: DataStore<Preferences> by preferencesDataStore(
    name = "cereqon_settings",
)

@Singleton
class SettingsRepositoryImpl @Inject constructor(
    @ApplicationContext private val context: Context,
    private val serverUrlStore: ServerUrlStore,
) : SettingsRepository {

    override val serverBaseUrl: Flow<String> =
        context.settingsDataStore.data.map { preferences ->
            preferences[Keys.SERVER_BASE_URL] ?: BuildConfig.DEFAULT_SERVER_BASE_URL
        }

    override val onboardingCompleted: Flow<Boolean> =
        context.settingsDataStore.data.map { preferences ->
            preferences[Keys.ONBOARDING_COMPLETED] ?: false
        }

    override val lastKnownCalibrated: Flow<Boolean> =
        context.settingsDataStore.data.map { preferences ->
            preferences[Keys.LAST_KNOWN_CALIBRATED] ?: false
        }

    override val themeMode: Flow<ThemeMode> =
        context.settingsDataStore.data.map { preferences ->
            ThemeMode.fromStored(preferences[Keys.THEME_MODE])
        }

    override suspend fun setServerBaseUrl(url: String) {
        val normalized = normalizeBaseUrl(url)
        context.settingsDataStore.edit { preferences ->
            preferences[Keys.SERVER_BASE_URL] = normalized
        }
        serverUrlStore.update(normalized)
    }

    override suspend fun setOnboardingCompleted(completed: Boolean) {
        context.settingsDataStore.edit { preferences ->
            preferences[Keys.ONBOARDING_COMPLETED] = completed
        }
    }

    override suspend fun setLastKnownCalibrated(calibrated: Boolean) {
        context.settingsDataStore.edit { preferences ->
            preferences[Keys.LAST_KNOWN_CALIBRATED] = calibrated
        }
    }

    override suspend fun setThemeMode(mode: ThemeMode) {
        context.settingsDataStore.edit { preferences ->
            preferences[Keys.THEME_MODE] = ThemeMode.storageValue(mode)
        }
    }

    override suspend fun getServerBaseUrl(): String {
        val stored = serverBaseUrl.first()
        serverUrlStore.update(stored)
        return stored
    }

    override suspend fun getThemeMode(): ThemeMode = themeMode.first()

    private fun normalizeBaseUrl(url: String): String {
        val trimmed = url.trim()
        return if (trimmed.endsWith("/")) trimmed else "$trimmed/"
    }

    private object Keys {
        val SERVER_BASE_URL = stringPreferencesKey("server_base_url")
        val ONBOARDING_COMPLETED = booleanPreferencesKey("onboarding_completed")
        val LAST_KNOWN_CALIBRATED = booleanPreferencesKey("last_known_calibrated")
        val THEME_MODE = stringPreferencesKey("theme_mode")
    }
}
