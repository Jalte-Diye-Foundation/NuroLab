package org.jaltediye.cereqon.data.export

import java.io.File
import javax.inject.Inject
import javax.inject.Singleton
import org.jaltediye.cereqon.domain.model.InsightSession
import org.jaltediye.cereqon.domain.model.InsightWindowSnapshot

@Singleton
class SessionReportCsvExporter @Inject constructor() {

    fun write(
        session: InsightSession,
        snapshots: List<InsightWindowSnapshot>,
        outputFile: File,
    ) {
        outputFile.parentFile?.mkdirs()
        outputFile.bufferedWriter().use { writer ->
            writer.appendLine("# Cereqon Session Report")
            writer.appendLine("# session_id,${session.id}")
            writer.appendLine("# started_at,${formatExportEpochMs(session.startedAtEpochMs)}")
            writer.appendLine("# ended_at,${formatExportEpochMs(session.endedAtEpochMs)}")
            writer.appendLine("# server_base_url,${escapeCsvField(session.serverBaseUrl)}")
            writer.appendLine("# calibrated_at_start,${session.calibratedAtStart}")
            writer.appendLine(
                "window_start_time,window_end_time,captured_at_epoch_ms,risk_tier,mahalanobis,predictions_json",
            )
            snapshots.forEach { snapshot ->
                writer.appendLine(
                    listOf(
                        snapshot.windowStartTime.toString(),
                        snapshot.windowEndTime.toString(),
                        snapshot.capturedAtEpochMs.toString(),
                        snapshot.riskTier?.toString().orEmpty(),
                        snapshot.mahalanobis?.toString().orEmpty(),
                        escapeCsvField(snapshot.predictionsJson.orEmpty()),
                    ).joinToString(","),
                )
            }
        }
    }

    private fun escapeCsvField(value: String): String {
        val needsQuotes = value.any { character ->
            character == ',' || character == '"' || character == '\n' || character == '\r'
        }
        if (!needsQuotes) {
            return value
        }
        return "\"${value.replace("\"", "\"\"")}\""
    }
}
