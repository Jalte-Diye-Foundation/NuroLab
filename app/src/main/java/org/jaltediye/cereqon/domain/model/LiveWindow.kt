package org.jaltediye.cereqon.domain.model

/**
 * One live analysis window from the WebSocket /ws/live stream.
 */
data class LiveWindow(
    val windowStartTime: Double,
    val windowEndTime: Double,
    val features: FeatureVector,
    val predictions: List<Prediction>,
    val deviation: DeviationSnapshot?,
    val receivedAtEpochMs: Long = System.currentTimeMillis(),
)
