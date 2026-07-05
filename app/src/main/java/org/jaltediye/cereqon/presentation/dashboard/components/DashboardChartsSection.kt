package org.jaltediye.cereqon.presentation.dashboard.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.runtime.Composable
import androidx.compose.runtime.key
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import org.jaltediye.cereqon.R
import org.jaltediye.cereqon.presentation.dashboard.DashboardTimelineHistory

@Composable
fun DashboardChartsSection(
    history: DashboardTimelineHistory,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier.fillMaxWidth(),
        verticalArrangement = Arrangement.spacedBy(16.dp),
    ) {
        key("risk-tier", history.riskTier.size) {
            DashboardLineChart(
                title = stringResource(R.string.dashboard_chart_risk_tier),
                values = history.riskTier.toChartFloats(),
            )
        }
        key("mahalanobis", history.mahalanobis.size) {
            DashboardLineChart(
                title = stringResource(R.string.dashboard_chart_mahalanobis),
                values = history.mahalanobis.toChartFloats(),
            )
        }
        key("first-feature", history.firstFeature.size) {
            DashboardLineChart(
                title = stringResource(R.string.dashboard_chart_feature),
                values = history.firstFeature,
            )
        }
    }
}
