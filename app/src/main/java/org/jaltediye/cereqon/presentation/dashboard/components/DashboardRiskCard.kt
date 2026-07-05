package org.jaltediye.cereqon.presentation.dashboard.components

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Shield
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import org.jaltediye.cereqon.R
import org.jaltediye.cereqon.domain.model.DeviationSnapshot
import org.jaltediye.cereqon.domain.model.LiveWindow

@Composable
fun DashboardRiskCard(
    latestWindow: LiveWindow?,
    modifier: Modifier = Modifier,
) {
    DashboardCardShell(
        title = stringResource(R.string.dashboard_card_risk),
        modifier = modifier,
    ) {
        val deviation = latestWindow?.deviation
        if (deviation == null) {
            DashboardEmptyState(
                message = stringResource(R.string.dashboard_risk_unavailable),
                icon = Icons.Outlined.Shield,
            )
        } else {
            DashboardLabelValue(
                label = stringResource(R.string.dashboard_risk_mahalanobis),
                value = deviation.mahalanobis.toString(),
            )
            DashboardLabelValue(
                label = stringResource(R.string.dashboard_risk_tier),
                value = deviation.riskTier.value.toString(),
            )
            DashboardLabelValue(
                label = stringResource(R.string.dashboard_risk_explanations),
                value = formatExplanations(deviation),
            )
        }
    }
}

private fun formatExplanations(deviation: DeviationSnapshot): String =
    if (deviation.explanations.isEmpty()) {
        "[]"
    } else {
        deviation.explanations.joinToString(separator = "\n")
    }
