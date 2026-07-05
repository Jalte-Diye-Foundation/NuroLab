package org.jaltediye.cereqon

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import org.jaltediye.cereqon.domain.model.ThemeMode
import org.jaltediye.cereqon.domain.repository.SettingsRepository
import org.jaltediye.cereqon.navigation.CereqonNavHost
import org.jaltediye.cereqon.presentation.theme.CereqonTheme
import dagger.hilt.android.AndroidEntryPoint
import javax.inject.Inject

@AndroidEntryPoint
class MainActivity : ComponentActivity() {

    @Inject lateinit var settingsRepository: SettingsRepository

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            val themeMode by settingsRepository.themeMode.collectAsStateWithLifecycle(
                initialValue = ThemeMode.SYSTEM,
            )
            val isSystemInDarkTheme = isSystemInDarkTheme()
            CereqonTheme(
                darkTheme = themeMode.isDark(isSystemInDarkTheme),
            ) {
                Surface(modifier = Modifier.fillMaxSize()) {
                    CereqonNavHost(modifier = Modifier.fillMaxSize())
                }
            }
        }
    }
}
