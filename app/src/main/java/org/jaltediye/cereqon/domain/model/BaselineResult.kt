package org.jaltediye.cereqon.domain.model

/**
 * Result of POST /calibration/build_baseline.
 */
data class BaselineResult(
    val status: String,
    val nWindows: Int,
)
