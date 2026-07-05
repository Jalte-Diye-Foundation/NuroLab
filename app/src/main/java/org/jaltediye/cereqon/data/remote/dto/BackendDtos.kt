package org.jaltediye.cereqon.data.remote.dto

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class HealthResponseDto(
    val status: String,
    val version: String,
)

@Serializable
data class CalibrationStatusResponseDto(
    val calibrated: Boolean,
    @SerialName("n_features") val nFeatures: Int,
    @SerialName("data_source") val dataSource: String,
    @SerialName("models_loaded") val modelsLoaded: List<String>,
)

@Serializable
data class BuildBaselineResponseDto(
    val status: String,
    @SerialName("n_windows") val nWindows: Int,
)

/**
 * POST /calibration/build_baseline request body.
 * FastAPI expects an object with a required [relaxed_windows] field.
 */
@Serializable
data class BuildBaselineRequestDto(
    @SerialName("relaxed_windows") val relaxedWindows: List<List<Float>>,
) {
    companion object {
        fun from(relaxedWindows: List<List<Float>>): BuildBaselineRequestDto =
            BuildBaselineRequestDto(relaxedWindows = relaxedWindows)
    }
}
@Serializable
data class LivePayloadDto(
    @SerialName("window_start_time") val windowStartTime: Double,
    @SerialName("window_end_time") val windowEndTime: Double,
    @SerialName("feature_vector") val featureVector: List<Double>,
    val predictions: Map<String, PredictionEntryDto> = emptyMap(),
    val deviation: DeviationDto? = null,
)

@Serializable
data class PredictionEntryDto(
    val label: String? = null,
    val confidence: Double? = null,
    val error: String? = null,
)

@Serializable
data class DeviationDto(
    val mahalanobis: Double,
    @SerialName("risk_tier") val riskTier: Int,
    val explanations: List<String>,
)
