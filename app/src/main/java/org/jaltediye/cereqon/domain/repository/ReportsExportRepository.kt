package org.jaltediye.cereqon.domain.repository

import org.jaltediye.cereqon.domain.model.Outcome
import org.jaltediye.cereqon.domain.model.Report

/**
 * Generates local PDF/CSV reports from Room session data and persists metadata via [ReportsRepository].
 * No backend calls, cloud sync, or sharing.
 */
interface ReportsExportRepository {

    suspend fun exportSessionToPdf(sessionId: Long): Outcome<Report>

    suspend fun exportSessionToCsv(sessionId: Long): Outcome<Report>
}
