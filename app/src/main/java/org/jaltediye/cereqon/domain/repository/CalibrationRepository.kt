package org.jaltediye.cereqon.domain.repository

import org.jaltediye.cereqon.domain.model.BaselineResult
import org.jaltediye.cereqon.domain.model.CalibrationStatus
import org.jaltediye.cereqon.domain.model.Outcome

/**
 * Calibration REST operations and status polling.
 */
interface CalibrationRepository {
    suspend fun getStatus(): Outcome<CalibrationStatus>
    suspend fun submitBaseline(relaxedWindows: List<List<Float>>): Outcome<BaselineResult>
}
