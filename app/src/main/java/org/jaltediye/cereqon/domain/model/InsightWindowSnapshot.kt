package org.jaltediye.cereqon.domain.model

/**
 * A persisted window snapshot for Insights historical review.
 * Mirrors [org.jaltediye.cereqon.data.local.entity.WindowSnapshotEntity] without analytics.
 */
data class InsightWindowSnapshot(
    val id: Long,
    val sessionId: Long,
    val windowStartTime: Double,
    val windowEndTime: Double,
    val capturedAtEpochMs: Long,
    val riskTier: Int?,
    val mahalanobis: Double?,
    val predictionsJson: String?,
)
