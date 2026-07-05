package org.jaltediye.cereqon.domain.repository

import kotlinx.coroutines.flow.Flow
import org.jaltediye.cereqon.domain.model.Report

/**
 * Persistence and retrieval for report metadata via Room.
 *
 * **Read path:** reactive [Flow] observers emit on every Room table change.
 * **Write path:** [saveReportMetadata] stores export file references after local generation.
 */
interface ReportsRepository {

    /** Reactive report list ordered by creation time (newest first). */
    fun observeReports(): Flow<List<Report>>

    suspend fun getReport(reportId: Long): Report?

    suspend fun getAllReports(): List<Report>

    suspend fun saveReportMetadata(
        title: String,
        filePath: String,
        format: String,
        createdAtEpochMs: Long = System.currentTimeMillis(),
    ): Long

    suspend fun deleteReport(reportId: Long)
}
