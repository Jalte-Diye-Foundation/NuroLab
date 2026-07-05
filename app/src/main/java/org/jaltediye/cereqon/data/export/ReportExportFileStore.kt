package org.jaltediye.cereqon.data.export

import android.content.Context
import dagger.hilt.android.qualifiers.ApplicationContext
import java.io.File
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import javax.inject.Inject
import javax.inject.Singleton
import org.jaltediye.cereqon.domain.model.InsightSession

@Singleton
class ReportExportFileStore @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    private val timestampFormatter = DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss")

    fun reportsDirectory(): File =
        File(context.filesDir, REPORTS_DIR_NAME).apply { mkdirs() }

    fun createExportFile(sessionId: Long, formatExtension: String): File {
        val timestamp = Instant.now()
            .atZone(ZoneId.systemDefault())
            .format(timestampFormatter)
        val fileName = "session_${sessionId}_${timestamp}.$formatExtension"
        return File(reportsDirectory(), fileName)
    }

    companion object {
        const val REPORTS_DIR_NAME = "reports"
    }
}

internal fun formatExportEpochMs(epochMs: Long?): String {
    if (epochMs == null) return ""
    return Instant.ofEpochMilli(epochMs)
        .atZone(ZoneId.systemDefault())
        .format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
}

internal fun sessionReportTitle(session: InsightSession): String =
    "Session ${session.id} Report"
