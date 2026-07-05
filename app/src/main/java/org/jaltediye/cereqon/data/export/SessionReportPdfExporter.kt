package org.jaltediye.cereqon.data.export

import android.graphics.Paint
import android.graphics.Typeface
import android.graphics.pdf.PdfDocument
import java.io.File
import java.io.FileOutputStream
import javax.inject.Inject
import javax.inject.Singleton
import org.jaltediye.cereqon.domain.model.InsightSession
import org.jaltediye.cereqon.domain.model.InsightWindowSnapshot

@Singleton
class SessionReportPdfExporter @Inject constructor() {

    fun write(
        session: InsightSession,
        snapshots: List<InsightWindowSnapshot>,
        outputFile: File,
    ) {
        outputFile.parentFile?.mkdirs()

        val document = PdfDocument()
        val titlePaint = Paint().apply {
            textSize = 18f
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
            isAntiAlias = true
        }
        val headerPaint = Paint().apply {
            textSize = 12f
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
            isAntiAlias = true
        }
        val bodyPaint = Paint().apply {
            textSize = 11f
            isAntiAlias = true
        }

        val lines = buildReportLines(session, snapshots)
        var pageNumber = 1
        var lineIndex = 0

        while (lineIndex < lines.size) {
            val pageInfo = PdfDocument.PageInfo.Builder(PAGE_WIDTH, PAGE_HEIGHT, pageNumber).create()
            val page = document.startPage(pageInfo)
            val canvas = page.canvas
            var y = PAGE_MARGIN_TOP

            if (pageNumber == 1) {
                canvas.drawText("Cereqon Session Report", PAGE_MARGIN_LEFT, y, titlePaint)
                y += LINE_HEIGHT * 2
            }

            while (lineIndex < lines.size && y <= PAGE_HEIGHT - PAGE_MARGIN_BOTTOM) {
                val paint = if (lines[lineIndex].startsWith("Window snapshots")) {
                    headerPaint
                } else {
                    bodyPaint
                }
                canvas.drawText(lines[lineIndex], PAGE_MARGIN_LEFT, y, paint)
                y += LINE_HEIGHT
                lineIndex++
            }

            document.finishPage(page)
            pageNumber++
        }

        FileOutputStream(outputFile).use { outputStream ->
            document.writeTo(outputStream)
        }
        document.close()
    }

    private fun buildReportLines(
        session: InsightSession,
        snapshots: List<InsightWindowSnapshot>,
    ): List<String> {
        val lines = mutableListOf(
            "Session ID: ${session.id}",
            "Started: ${formatExportEpochMs(session.startedAtEpochMs)}",
            "Ended: ${formatExportEpochMs(session.endedAtEpochMs).ifBlank { "—" }}",
            "Server: ${session.serverBaseUrl}",
            "Calibrated at start: ${session.calibratedAtStart}",
            "Window snapshots: ${snapshots.size}",
            "",
            "Window snapshots",
        )

        snapshots.forEachIndexed { index, snapshot ->
            lines += listOf(
                "${index + 1}. start=${snapshot.windowStartTime}, end=${snapshot.windowEndTime}",
                "   captured=${formatExportEpochMs(snapshot.capturedAtEpochMs)}",
                "   risk_tier=${snapshot.riskTier ?: "—"}, mahalanobis=${snapshot.mahalanobis ?: "—"}",
            )
        }

        return lines
    }

    companion object {
        private const val PAGE_WIDTH = 595
        private const val PAGE_HEIGHT = 842
        private const val PAGE_MARGIN_LEFT = 40f
        private const val PAGE_MARGIN_TOP = 48f
        private const val PAGE_MARGIN_BOTTOM = 48f
        private const val LINE_HEIGHT = 16f
    }
}
