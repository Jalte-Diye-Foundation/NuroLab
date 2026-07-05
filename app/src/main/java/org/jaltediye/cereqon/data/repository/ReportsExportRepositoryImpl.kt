package org.jaltediye.cereqon.data.repository

import javax.inject.Inject
import javax.inject.Singleton
import org.jaltediye.cereqon.data.export.ReportExportFileStore
import org.jaltediye.cereqon.data.export.SessionReportCsvExporter
import org.jaltediye.cereqon.data.export.SessionReportPdfExporter
import org.jaltediye.cereqon.data.export.sessionReportTitle
import java.io.File
import org.jaltediye.cereqon.domain.model.InsightSession
import org.jaltediye.cereqon.domain.model.InsightWindowSnapshot
import org.jaltediye.cereqon.domain.model.Outcome
import org.jaltediye.cereqon.domain.model.Report
import org.jaltediye.cereqon.domain.model.ReportFormat
import org.jaltediye.cereqon.domain.repository.InsightsRepository
import org.jaltediye.cereqon.domain.repository.ReportsExportRepository
import org.jaltediye.cereqon.domain.repository.ReportsRepository

@Singleton
class ReportsExportRepositoryImpl @Inject constructor(
    private val insightsRepository: InsightsRepository,
    private val reportsRepository: ReportsRepository,
    private val fileStore: ReportExportFileStore,
    private val csvExporter: SessionReportCsvExporter,
    private val pdfExporter: SessionReportPdfExporter,
) : ReportsExportRepository {

    override suspend fun exportSessionToPdf(sessionId: Long): Outcome<Report> =
        exportSession(sessionId, ReportFormat.PDF) { session, snapshots, outputFile ->
            pdfExporter.write(session, snapshots, outputFile)
        }

    override suspend fun exportSessionToCsv(sessionId: Long): Outcome<Report> =
        exportSession(sessionId, ReportFormat.CSV) { session, snapshots, outputFile ->
            csvExporter.write(session, snapshots, outputFile)
        }

    private suspend fun exportSession(
        sessionId: Long,
        format: String,
        writer: (session: InsightSession, snapshots: List<InsightWindowSnapshot>, outputFile: File) -> Unit,
    ): Outcome<Report> {
        val session = insightsRepository.getSession(sessionId)
            ?: return Outcome.Error("Session $sessionId was not found in Room.")

        val snapshots = insightsRepository.getWindowSnapshots(sessionId)
        if (snapshots.isEmpty()) {
            return Outcome.Error("Session $sessionId has no window snapshots to export.")
        }

        return try {
            val extension = when (format) {
                ReportFormat.PDF -> "pdf"
                ReportFormat.CSV -> "csv"
                else -> format
            }
            val outputFile = fileStore.createExportFile(sessionId, extension)
            writer(session, snapshots, outputFile)

            val createdAtEpochMs = System.currentTimeMillis()
            val reportId = reportsRepository.saveReportMetadata(
                title = sessionReportTitle(session),
                filePath = outputFile.absolutePath,
                format = format,
                createdAtEpochMs = createdAtEpochMs,
            )
            val report = reportsRepository.getReport(reportId)
                ?: return Outcome.Error("Report metadata was saved but could not be read back.")
            Outcome.Success(report)
        } catch (exception: Exception) {
            Outcome.Error(
                message = exception.message ?: "Failed to export session $sessionId as $format.",
                cause = exception,
            )
        }
    }
}
