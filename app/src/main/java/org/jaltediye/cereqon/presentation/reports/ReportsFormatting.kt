package org.jaltediye.cereqon.presentation.reports

import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import org.jaltediye.cereqon.domain.model.Report

private val timestampFormatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")
private val sessionReferencePattern = Regex("""session\s+#?(\d+)""", RegexOption.IGNORE_CASE)

internal fun formatReportEpochMs(epochMs: Long): String =
    Instant.ofEpochMilli(epochMs)
        .atZone(ZoneId.systemDefault())
        .format(timestampFormatter)

internal fun Report.parsedSessionId(): Long? =
    sessionReferencePattern.find(title)?.groupValues?.getOrNull(1)?.toLongOrNull()

internal enum class ReportExportStatus {
    Exported,
    Pending,
}

internal fun Report.exportStatus(): ReportExportStatus =
    if (filePath.isNotBlank()) ReportExportStatus.Exported else ReportExportStatus.Pending
