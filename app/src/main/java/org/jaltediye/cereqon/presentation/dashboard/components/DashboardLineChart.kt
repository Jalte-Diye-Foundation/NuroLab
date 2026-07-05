package org.jaltediye.cereqon.presentation.dashboard.components

import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.animate
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.ShowChart
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.unit.dp
import org.jaltediye.cereqon.R
import org.jaltediye.cereqon.presentation.dashboard.DashboardTimelineHistory

private data class ChartSeries(
    val normalizedYs: FloatArray,
    val pointCount: Int,
)

@Composable
fun DashboardLineChart(
    title: String,
    values: List<Float>,
    modifier: Modifier = Modifier,
) {
    val chartDescription = if (values.isEmpty()) {
        stringResource(R.string.dashboard_chart_no_data)
    } else {
        stringResource(
            R.string.dashboard_chart_content_description,
            title,
            values.size,
        )
    }

    DashboardCardShell(
        title = title,
        modifier = modifier.semantics { contentDescription = chartDescription },
    ) {
        if (values.isEmpty()) {
            DashboardEmptyState(
                message = stringResource(R.string.dashboard_chart_no_data),
                icon = Icons.Outlined.ShowChart,
            )
        } else {
            val series = remember(values) { values.toChartSeries() }
            var drawProgress by remember { mutableFloatStateOf(1f) }
            var lastAnimatedSize by remember { mutableIntStateOf(values.size) }

            LaunchedEffect(values.size) {
                if (values.size != lastAnimatedSize) {
                    lastAnimatedSize = values.size
                    drawProgress = 0f
                    animate(
                        initialValue = 0f,
                        targetValue = 1f,
                        animationSpec = tween(durationMillis = 600, easing = FastOutSlowInEasing),
                    ) { value, _ ->
                        drawProgress = value
                    }
                }
            }

            val lineColor = MaterialTheme.colorScheme.primary
            val gridColor = MaterialTheme.colorScheme.outline.copy(alpha = 0.25f)

            Canvas(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(160.dp)
                    .padding(top = 12.dp),
            ) {
                if (series.pointCount < 2) {
                    val y = size.height / 2f
                    drawLine(
                        color = lineColor,
                        start = Offset(0f, y),
                        end = Offset(size.width * drawProgress, y),
                        strokeWidth = 3f,
                        cap = StrokeCap.Round,
                    )
                    return@Canvas
                }

                val stepX = size.width / (series.pointCount - 1)
                val visibleCount = ((series.pointCount - 1) * drawProgress).toInt()
                    .coerceAtLeast(1)

                drawLine(
                    color = gridColor,
                    start = Offset(0f, size.height),
                    end = Offset(size.width, size.height),
                    strokeWidth = 1f,
                )

                val clipPath = Path()
                for (index in 0..visibleCount) {
                    val x = stepX * index
                    val y = size.height - (series.normalizedYs[index] * size.height)
                    if (index == 0) {
                        clipPath.moveTo(x, y)
                    } else {
                        clipPath.lineTo(x, y)
                    }
                }

                drawPath(
                    path = clipPath,
                    color = lineColor,
                    style = Stroke(width = 3f, cap = StrokeCap.Round),
                )
            }

            Text(
                text = stringResource(
                    R.string.dashboard_chart_points,
                    values.size,
                    DashboardTimelineHistory.MAX_POINTS,
                ),
                modifier = Modifier.padding(top = 8.dp),
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

private fun List<Float>.toChartSeries(): ChartSeries {
    val min = min()
    val max = max()
    val range = (max - min).coerceAtLeast(0.0001f)
    return ChartSeries(
        normalizedYs = FloatArray(size) { index -> (this[index] - min) / range },
        pointCount = size,
    )
}

@JvmName("doubleListToChartFloats")
fun List<Double>.toChartFloats(): List<Float> = map { it.toFloat() }

@JvmName("intListToChartFloats")
fun List<Int>.toChartFloats(): List<Float> = map { it.toFloat() }
