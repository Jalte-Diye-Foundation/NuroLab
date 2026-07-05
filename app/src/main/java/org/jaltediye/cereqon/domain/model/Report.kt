package org.jaltediye.cereqon.domain.model

/**
 * A persisted report metadata record.
 * Mirrors [org.jaltediye.cereqon.data.local.entity.ReportEntity] without export logic.
 */
data class Report(
    val id: Long,
    val title: String,
    val createdAtEpochMs: Long,
    val filePath: String,
    val format: String,
)
