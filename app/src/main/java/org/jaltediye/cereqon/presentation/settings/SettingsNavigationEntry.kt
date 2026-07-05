package org.jaltediye.cereqon.presentation.settings

import android.content.Intent
import android.net.Uri
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.platform.LocalContext
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import org.jaltediye.cereqon.R

@Composable
fun SettingsNavigationEntry(
    onNavigateBack: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val context = LocalContext.current

    SettingsScreen(
        uiState = uiState,
        onServerUrlChanged = viewModel::onServerUrlChanged,
        onSaveServerUrl = viewModel::saveServerUrl,
        onThemeModeSelected = viewModel::onThemeModeSelected,
        onRefreshBackendVersion = viewModel::refreshBackendVersion,
        onPrivacyPolicyClick = {
            val url = context.getString(R.string.settings_privacy_policy_url)
            context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
        },
        onNavigateBack = onNavigateBack,
    )
}
