package org.jaltediye.cereqon

import android.app.Application
import org.jaltediye.cereqon.domain.repository.SettingsRepository
import dagger.hilt.android.HiltAndroidApp
import javax.inject.Inject
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch
import org.jaltediye.cereqon.di.ApplicationScope
import org.jaltediye.cereqon.di.IoDispatcher
import kotlinx.coroutines.CoroutineDispatcher

/**
 * Application entry point. Initializes Hilt and synchronizes persisted settings
 * before any network components are used.
 */
@HiltAndroidApp
class CereqonApp : Application() {

    @Inject lateinit var settingsRepository: SettingsRepository

    @Inject @ApplicationScope lateinit var applicationScope: CoroutineScope

    @Inject @IoDispatcher lateinit var ioDispatcher: CoroutineDispatcher

    override fun onCreate() {
        super.onCreate()
        applicationScope.launch(ioDispatcher) {
            settingsRepository.getServerBaseUrl()
        }
    }
}
