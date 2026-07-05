package org.jaltediye.cereqon.domain.model

/**
 * Personal baseline deviation block from WebSocket payload (optional).
 */
data class DeviationSnapshot(
    val mahalanobis: Double,
    val riskTier: RiskTier,
    val explanations: List<String>,
)
