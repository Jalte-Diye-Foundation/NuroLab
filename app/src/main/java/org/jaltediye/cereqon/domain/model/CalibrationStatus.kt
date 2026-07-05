package org.jaltediye.cereqon.domain.model

/**
 * Backend calibration status from GET /calibration/status.
 */
data class CalibrationStatus(
    val calibrated: Boolean,
    val nFeatures: Int,
    val dataSource: String,
    val modelsLoaded: List<String>,
)
