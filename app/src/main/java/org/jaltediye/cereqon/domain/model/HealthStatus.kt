package org.jaltediye.cereqon.domain.model

/**
 * Backend health response from GET /health.
 */
data class HealthStatus(
    val status: String,
    val version: String,
)
