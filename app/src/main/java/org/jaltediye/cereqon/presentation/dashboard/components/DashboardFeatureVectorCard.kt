package org.jaltediye.cereqon.presentation.dashboard.components

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.DataArray
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import org.jaltediye.cereqon.R
import org.jaltediye.cereqon.domain.model.LiveWindow

@Composable
fun DashboardFeatureVectorCard(
    latestWindow: LiveWindow?,
    modifier: Modifier = Modifier,
) {
    DashboardCardShell(
        title = stringResource(R.string.dashboard_card_feature_vector),
        modifier = modifier,
    ) {
        if (latestWindow == null) {
            DashboardEmptyState(
                message = stringResource(R.string.dashboard_feature_unavailable),
                icon = Icons.Outlined.DataArray,
            )
        } else {
            val features = latestWindow.features
            val firstIndex = features.values.indices.firstOrNull()
            val lastIndex = features.values.indices.lastOrNull()

            DashboardLabelValue(
                label = stringResource(R.string.dashboard_feature_window_start),
                value = latestWindow.windowStartTime.toString(),
            )
            DashboardLabelValue(
                label = stringResource(R.string.dashboard_feature_window_end),
                value = latestWindow.windowEndTime.toString(),
            )
            DashboardLabelValue(
                label = stringResource(R.string.dashboard_feature_count),
                value = features.size.toString(),
            )
            if (firstIndex != null) {
                DashboardLabelValue(
                    label = stringResource(R.string.dashboard_feature_first),
                    value = formatFeatureEntry(features.names[firstIndex], features.values[firstIndex]),
                )
            }
            if (lastIndex != null && lastIndex != firstIndex) {
                DashboardLabelValue(
                    label = stringResource(R.string.dashboard_feature_last),
                    value = formatFeatureEntry(features.names[lastIndex], features.values[lastIndex]),
                )
            }
        }
    }
}

private fun formatFeatureEntry(name: String, value: Float): String = "$name: $value"
