package org.jaltediye.cereqon.presentation.insights

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@Composable
fun InsightsNavigationEntry(
    viewModel: InsightsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    InsightsScreen(
        uiState = uiState,
        onRetry = viewModel::refresh,
    )
}
