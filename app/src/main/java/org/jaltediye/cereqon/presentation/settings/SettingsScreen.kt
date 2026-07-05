package org.jaltediye.cereqon.presentation.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowBack
import androidx.compose.material.icons.outlined.OpenInNew
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import org.jaltediye.cereqon.R
import org.jaltediye.cereqon.domain.model.ThemeMode
import org.jaltediye.cereqon.presentation.components.CereqonPrimaryButton
import org.jaltediye.cereqon.presentation.dashboard.components.DashboardCardShell
import org.jaltediye.cereqon.presentation.dashboard.components.DashboardLabelValue
import org.jaltediye.cereqon.presentation.state.LoadableUiState

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    uiState: SettingsUiState,
    onServerUrlChanged: (String) -> Unit,
    onSaveServerUrl: () -> Unit,
    onThemeModeSelected: (ThemeMode) -> Unit,
    onRefreshBackendVersion: () -> Unit,
    onPrivacyPolicyClick: () -> Unit,
    onNavigateBack: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Scaffold(
        modifier = modifier.fillMaxSize(),
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = stringResource(R.string.settings_title),
                        style = MaterialTheme.typography.titleLarge,
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Outlined.ArrowBack,
                            contentDescription = stringResource(R.string.settings_back),
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background,
                ),
            )
        },
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 24.dp, vertical = 16.dp),
            verticalArrangement = Arrangement.spacedBy(20.dp),
        ) {
            Text(
                text = stringResource(R.string.settings_subtitle),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            DashboardCardShell(title = stringResource(R.string.settings_server_section)) {
                OutlinedTextField(
                    value = uiState.serverUrl,
                    onValueChange = onServerUrlChanged,
                    modifier = Modifier.fillMaxWidth(),
                    label = { Text(stringResource(R.string.settings_server_url_label)) },
                    placeholder = { Text(stringResource(R.string.welcome_server_url_hint)) },
                    singleLine = true,
                    shape = RoundedCornerShape(12.dp),
                    keyboardOptions = KeyboardOptions(
                        keyboardType = KeyboardType.Uri,
                        imeAction = ImeAction.Done,
                    ),
                    keyboardActions = KeyboardActions(onDone = { onSaveServerUrl() }),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = MaterialTheme.colorScheme.primary,
                        unfocusedBorderColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.5f),
                        focusedContainerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.35f),
                        unfocusedContainerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.25f),
                    ),
                    enabled = !uiState.isSavingServerUrl,
                )

                if (uiState.serverUrlSaved) {
                    Text(
                        text = stringResource(R.string.settings_server_url_saved),
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.padding(top = 8.dp),
                    )
                }

                CereqonPrimaryButton(
                    text = stringResource(R.string.settings_save_server_url),
                    onClick = onSaveServerUrl,
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 12.dp),
                    enabled = !uiState.isSavingServerUrl,
                    loading = uiState.isSavingServerUrl,
                )
            }

            DashboardCardShell(title = stringResource(R.string.settings_theme_section)) {
                Text(
                    text = stringResource(R.string.settings_theme_description),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                SingleChoiceSegmentedButtonRow(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 12.dp),
                ) {
                    ThemeMode.entries.forEachIndexed { index, mode ->
                        SegmentedButton(
                            selected = uiState.themeMode == mode,
                            onClick = { onThemeModeSelected(mode) },
                            shape = SegmentedButtonDefaults.itemShape(
                                index = index,
                                count = ThemeMode.entries.size,
                            ),
                        ) {
                            Text(
                                text = when (mode) {
                                    ThemeMode.SYSTEM -> stringResource(R.string.settings_theme_system)
                                    ThemeMode.LIGHT -> stringResource(R.string.settings_theme_light)
                                    ThemeMode.DARK -> stringResource(R.string.settings_theme_dark)
                                },
                            )
                        }
                    }
                }
            }

            DashboardCardShell(title = stringResource(R.string.settings_about_section)) {
                DashboardLabelValue(
                    label = stringResource(R.string.settings_app_version),
                    value = uiState.appVersion,
                )
                BackendVersionRow(
                    backendVersionState = uiState.backendVersionState,
                    onRefresh = onRefreshBackendVersion,
                )
                Text(
                    text = stringResource(R.string.settings_about_body),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(top = 12.dp),
                )
            }

            DashboardCardShell(title = stringResource(R.string.settings_privacy_section)) {
                Text(
                    text = stringResource(R.string.settings_privacy_description),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                TextButton(
                    onClick = onPrivacyPolicyClick,
                    modifier = Modifier.padding(top = 4.dp),
                ) {
                    Text(text = stringResource(R.string.settings_privacy_policy_link))
                    Icon(
                        imageVector = Icons.Outlined.OpenInNew,
                        contentDescription = null,
                        modifier = Modifier.padding(start = 8.dp),
                    )
                }
            }
        }
    }
}

@Composable
private fun BackendVersionRow(
    backendVersionState: LoadableUiState<String>,
    onRefresh: () -> Unit,
) {
    when (backendVersionState) {
        LoadableUiState.Idle,
        LoadableUiState.Loading,
        -> {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 12.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Text(
                    text = stringResource(R.string.settings_backend_version),
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                CircularProgressIndicator(
                    modifier = Modifier.padding(start = 4.dp),
                    strokeWidth = 2.dp,
                )
            }
        }

        is LoadableUiState.Error -> {
            Column(modifier = Modifier.fillMaxWidth()) {
                DashboardLabelValue(
                    label = stringResource(R.string.settings_backend_version),
                    value = stringResource(R.string.settings_backend_version_unavailable),
                )
                Text(
                    text = backendVersionState.message,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.error,
                )
                TextButton(onClick = onRefresh) {
                    Text(text = stringResource(R.string.settings_retry))
                }
            }
        }

        is LoadableUiState.Success -> {
            DashboardLabelValue(
                label = stringResource(R.string.settings_backend_version),
                value = backendVersionState.data,
            )
        }
    }
}
