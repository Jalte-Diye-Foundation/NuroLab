package org.jaltediye.cereqon.domain.repository

import org.jaltediye.cereqon.domain.model.BaselineResult
import org.jaltediye.cereqon.domain.model.CalibrationStatus
import org.jaltediye.cereqon.domain.model.HealthStatus
import org.jaltediye.cereqon.domain.model.LiveWindow
import org.jaltediye.cereqon.domain.model.Outcome
import org.jaltediye.cereqon.domain.model.StreamConnectionState
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.StateFlow

/**
 * REST health checks against GET /health.
 */
interface HealthRepository {
    suspend fun checkHealth(): Outcome<HealthStatus>
    suspend fun getCachedHealth(): HealthStatus?
}
