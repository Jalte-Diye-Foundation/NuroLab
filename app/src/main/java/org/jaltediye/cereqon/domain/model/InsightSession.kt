package org.jaltediye.cereqon.domain.model

/**
 * A persisted monitoring session for Insights.
 * Mirrors [org.jaltediye.cereqon.data.local.entity.SessionEntity] without analytics.
 */
data class InsightSession(
    val id: Long,
    val startedAtEpochMs: Long,
    val endedAtEpochMs: Long?,
    val serverBaseUrl: String,
    val calibratedAtStart: Boolean,
)
