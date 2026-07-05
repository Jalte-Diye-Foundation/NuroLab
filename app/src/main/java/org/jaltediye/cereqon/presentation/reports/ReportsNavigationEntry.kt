package org.jaltediye.cereqon.presentation.reports

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle

@Composable
fun ReportsNavigationEntry(
    viewModel: ReportsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    ReportsScreen(
        uiState = uiState,
        onRetry = viewModel::refresh,
    )
}
