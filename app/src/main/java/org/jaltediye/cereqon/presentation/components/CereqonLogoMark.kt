package org.jaltediye.cereqon.presentation.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import androidx.compose.ui.graphics.Color
import org.jaltediye.cereqon.presentation.theme.CereqonSignalLive

@Composable
fun CereqonLogoMark(
    modifier: Modifier = Modifier,
    waveColor: Color = Color.White,
) {
    Canvas(modifier = modifier.size(72.dp)) {
        val cx = size.width / 2f
        val cy = size.height / 2f
        val r = size.minDimension * 0.28f

        val hex = Path().apply {
            for (i in 0..5) {
                val angle = Math.toRadians((60.0 * i) - 90.0)
                val x = cx + r * kotlin.math.cos(angle).toFloat()
                val y = cy + r * kotlin.math.sin(angle).toFloat()
                if (i == 0) moveTo(x, y) else lineTo(x, y)
            }
            close()
        }
        drawPath(
            path = hex,
            color = CereqonSignalLive,
            style = Stroke(width = 3f),
        )

        val wave = Path().apply {
            moveTo(size.width * 0.12f, cy)
            lineTo(size.width * 0.28f, cy)
            lineTo(size.width * 0.34f, cy - r * 0.55f)
            lineTo(size.width * 0.42f, cy + r * 0.65f)
            lineTo(size.width * 0.50f, cy - r * 0.25f)
            lineTo(size.width * 0.58f, cy + r * 0.45f)
            lineTo(size.width * 0.66f, cy)
            lineTo(size.width * 0.88f, cy)
        }
        drawPath(
            path = wave,
            color = waveColor,
            style = Stroke(
                width = 4f,
                cap = StrokeCap.Round,
                join = StrokeJoin.Round,
            ),
        )

        drawCircle(
            color = CereqonSignalLive,
            radius = 4f,
            center = Offset(cx + r * 0.78f, cy - r * 0.72f),
        )
    }
}
