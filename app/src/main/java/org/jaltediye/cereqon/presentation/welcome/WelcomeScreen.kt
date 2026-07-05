package org.jaltediye.cereqon.presentation.welcome

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.slideInVertically
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import org.jaltediye.cereqon.R
import org.jaltediye.cereqon.presentation.components.CereqonLogoMark
import org.jaltediye.cereqon.presentation.components.CereqonPrimaryButton
import org.jaltediye.cereqon.presentation.components.ConnectionStatusCard

@Composable
fun WelcomeScreen(
    onNavigateToCalibration: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: WelcomeViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    var visible by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        visible = true
    }

    LaunchedEffect(uiState.setupComplete) {
        if (uiState.setupComplete) {
            onNavigateToCalibration()
        }
    }

    Scaffold(
        modifier = modifier.fillMaxSize(),
        containerColor = MaterialTheme.colorScheme.background,
    ) { innerPadding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(innerPadding)
                .imePadding()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 24.dp, vertical = 32.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            AnimatedVisibility(
                visible = visible,
                enter = fadeIn(tween(600)) + slideInVertically(
                    initialOffsetY = { it / 4 },
                    animationSpec = tween(600),
                ),
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    CereqonLogoMark(
                        waveColor = MaterialTheme.colorScheme.onBackground,
                    )
                    Text(
                        text = stringResource(R.string.app_name),
                        style = MaterialTheme.typography.displayLarge,
                        color = MaterialTheme.colorScheme.onBackground,
                    )
                    Text(
                        text = stringResource(R.string.welcome_tagline),
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                    Text(
                        text = stringResource(R.string.welcome_foundation),
                        style = MaterialTheme.typography.labelMedium,
                        color = MaterialTheme.colorScheme.primary,
                    )
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            OutlinedTextField(
                value = uiState.serverUrl,
                onValueChange = viewModel::onServerUrlChanged,
                modifier = Modifier.fillMaxWidth(),
                label = { Text(stringResource(R.string.welcome_server_url_label)) },
                placeholder = { Text(stringResource(R.string.welcome_server_url_hint)) },
                singleLine = true,
                shape = RoundedCornerShape(12.dp),
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Uri,
                    imeAction = ImeAction.Done,
                ),
                keyboardActions = KeyboardActions(
                    onDone = { viewModel.testConnection() },
                ),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = MaterialTheme.colorScheme.primary,
                    unfocusedBorderColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.5f),
                    focusedContainerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.35f),
                    unfocusedContainerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.25f),
                ),
                enabled = !uiState.isTestingConnection && !uiState.setupComplete,
            )

            TextButton(
                onClick = viewModel::testConnection,
                enabled = !uiState.isTestingConnection && !uiState.setupComplete,
                modifier = Modifier.align(Alignment.End),
            ) {
                Text(text = stringResource(R.string.welcome_test_connection))
            }

            ConnectionStatusCard(
                connectionState = uiState.connectionState,
                onRetry = viewModel::testConnection,
            )

            Spacer(modifier = Modifier.height(16.dp))

            val continueLabel = if (uiState.setupComplete) {
                stringResource(R.string.welcome_setup_complete)
            } else {
                stringResource(R.string.welcome_continue)
            }

            CereqonPrimaryButton(
                text = continueLabel,
                onClick = viewModel::onContinue,
                modifier = Modifier.fillMaxWidth(),
                enabled = uiState.canContinue,
                loading = uiState.isSaving,
            )
        }
    }
}
