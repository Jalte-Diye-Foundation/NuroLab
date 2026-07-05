package org.jaltediye.cereqon.presentation.insights

import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale
import java.util.concurrent.TimeUnit
import kotlin.math.max

private val timestampFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")

internal fun formatEpochMs(epochMs: Long?): String {
    if (epochMs == null) return "—"
    return Instant.ofEpochMilli(epochMs)
        .atZone(ZoneId.systemDefault())
        .format(timestampFormatter)
}

internal fun formatSessionDuration(
    startedAtEpochMs: Long,
    endedAtEpochMs: Long?,
    nowEpochMs: Long,
): String {
    val endMs = endedAtEpochMs ?: nowEpochMs
    val durationMs = max(0L, endMs - startedAtEpochMs)
    val hours = TimeUnit.MILLISECONDS.toHours(durationMs)
    val minutes = TimeUnit.MILLISECONDS.toMinutes(durationMs) % 60
    val seconds = TimeUnit.MILLISECONDS.toSeconds(durationMs) % 60
    return if (hours > 0) {
        String.format(Locale.getDefault(), "%dh %02dm %02ds", hours, minutes, seconds)
    } else {
        String.format(Locale.getDefault(), "%dm %02ds", minutes, seconds)
    }
}
