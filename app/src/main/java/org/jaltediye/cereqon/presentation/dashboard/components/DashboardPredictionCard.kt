package org.jaltediye.cereqon.presentation.dashboard.components

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Psychology
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import org.jaltediye.cereqon.R
import org.jaltediye.cereqon.domain.model.LiveWindow
import org.jaltediye.cereqon.domain.model.Prediction

@Composable
fun DashboardPredictionCard(
    latestWindow: LiveWindow?,
    modifier: Modifier = Modifier,
) {
    DashboardCardShell(
        title = stringResource(R.string.dashboard_card_predictions),
        modifier = modifier,
    ) {
        val predictions = latestWindow?.predictions.orEmpty()
        if (predictions.isEmpty()) {
            DashboardEmptyState(
                message = stringResource(R.string.dashboard_predictions_empty),
                icon = Icons.Outlined.Psychology,
                accessibilityLabel = stringResource(R.string.dashboard_predictions_empty_description),
            )
        } else {
            predictions.forEach { prediction ->
                PredictionRow(prediction = prediction)
            }
        }
    }
}

@Composable
private fun PredictionRow(prediction: Prediction) {
    when (prediction) {
        is Prediction.Success -> {
            DashboardLabelValue(
                label = prediction.condition.replaceFirstChar { it.uppercase() },
                value = stringResource(
                    R.string.dashboard_prediction_confidence,
                    prediction.label,
                    prediction.confidence,
                ),
            )
        }

        is Prediction.Failed -> {
            DashboardLabelValue(
                label = prediction.condition.replaceFirstChar { it.uppercase() },
                value = stringResource(
                    R.string.dashboard_prediction_error,
                    prediction.error,
                ),
            )
        }
    }
}
