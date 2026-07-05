package org.jaltediye.cereqon.data.remote.mapper

import org.jaltediye.cereqon.data.remote.dto.BuildBaselineResponseDto
import org.jaltediye.cereqon.data.remote.dto.CalibrationStatusResponseDto
import org.jaltediye.cereqon.data.remote.dto.DeviationDto
import org.jaltediye.cereqon.data.remote.dto.HealthResponseDto
import org.jaltediye.cereqon.data.remote.dto.LivePayloadDto
import org.jaltediye.cereqon.data.remote.dto.PredictionEntryDto
import org.jaltediye.cereqon.domain.model.BaselineResult
import org.jaltediye.cereqon.domain.model.BrainMetrics
import org.jaltediye.cereqon.domain.model.CalibrationStatus
import org.jaltediye.cereqon.domain.model.DeviationSnapshot
import org.jaltediye.cereqon.domain.model.FeatureVector
import org.jaltediye.cereqon.domain.model.HealthStatus
import org.jaltediye.cereqon.domain.model.LiveWindow
import org.jaltediye.cereqon.domain.model.Prediction
import org.jaltediye.cereqon.domain.model.RiskTier

object HealthMapper {
    fun toDomain(dto: HealthResponseDto): HealthStatus =
        HealthStatus(status = dto.status, version = dto.version)
}

object CalibrationStatusMapper {
    fun toDomain(dto: CalibrationStatusResponseDto): CalibrationStatus =
        CalibrationStatus(
            calibrated = dto.calibrated,
            nFeatures = dto.nFeatures,
            dataSource = dto.dataSource,
            modelsLoaded = dto.modelsLoaded,
        )
}

object BaselineResultMapper {
    fun toDomain(dto: BuildBaselineResponseDto): BaselineResult =
        BaselineResult(status = dto.status, nWindows = dto.nWindows)
}

object DeviationMapper {
    fun toDomain(dto: DeviationDto): DeviationSnapshot =
        DeviationSnapshot(
            mahalanobis = dto.mahalanobis,
            riskTier = RiskTier.fromInt(dto.riskTier),
            explanations = dto.explanations,
        )
}

object PredictionMapper {
    fun toDomain(condition: String, dto: PredictionEntryDto): Prediction {
        dto.error?.let { error ->
            return Prediction.Failed(condition = condition, error = error)
        }
        val label = dto.label
        val confidence = dto.confidence
        return if (label != null && confidence != null) {
            Prediction.Success(
                condition = condition,
                label = label,
                confidence = confidence,
            )
        } else {
            Prediction.Failed(
                condition = condition,
                error = "Missing label or confidence in prediction payload",
            )
        }
    }

    fun toDomainMap(predictions: Map<String, PredictionEntryDto>): List<Prediction> =
        predictions.map { (condition, entry) -> toDomain(condition, entry) }
}

object FeatureVectorMapper {
    /**
     * Maps wire values to [FeatureVector], validating length against [expectedFeatureCount].
     *
     * @return domain vector or null when size mismatch (frame dropped by caller).
     */
    fun toDomain(
        values: List<Double>,
        channelNames: List<String>,
        expectedFeatureCount: Int,
    ): FeatureVector? {
        if (values.size != expectedFeatureCount) {
            return null
        }
        val names = FeatureNameBuilder.build(channelNames)
        if (names.size != values.size) {
            return null
        }
        return FeatureVector(
            values = values.map { it.toFloat() },
            names = names,
        )
    }
}

object LivePayloadMapper {
    fun toDomain(
        dto: LivePayloadDto,
        channelNames: List<String>,
        expectedFeatureCount: Int,
    ): LiveWindow? {
        val features = FeatureVectorMapper.toDomain(
            values = dto.featureVector,
            channelNames = channelNames,
            expectedFeatureCount = expectedFeatureCount,
        ) ?: return null

        return LiveWindow(
            windowStartTime = dto.windowStartTime,
            windowEndTime = dto.windowEndTime,
            features = features,
            predictions = PredictionMapper.toDomainMap(dto.predictions),
            deviation = dto.deviation?.let(DeviationMapper::toDomain),
        )
    }
}

/**
 * Mirrors backend nurolab/processing/features.py build_feature_names() ordering.
 */
object FeatureNameBuilder {
    private val bandNames = listOf("delta", "theta", "alpha", "beta", "gamma")
    private val hjorthNames = listOf("activity", "mobility", "complexity")

    fun build(channelNames: List<String>): List<String> {
        val names = mutableListOf<String>()
        for (channel in channelNames) {
            for (band in bandNames) {
                names += "${channel}_${band}_DE"
            }
            for (hjorth in hjorthNames) {
                names += "${channel}_hjorth_$hjorth"
            }
        }
        return names
    }

    fun expectedFeatureCount(channelCount: Int): Int =
        channelCount * (bandNames.size + hjorthNames.size)
}

object BrainMetricsMapper {
    private const val EPSILON = 1e-10

    fun compute(features: FeatureVector): BrainMetrics {
        fun avgBand(band: String): Double {
            val values = features.names.zip(features.values)
                .filter { (name, _) -> name.contains("_${band}_DE") }
                .map { (_, value) -> value.toDouble() }
            return if (values.isEmpty()) 0.0 else values.average()
        }

        val alpha = avgBand("alpha")
        val beta = avgBand("beta")
        val theta = avgBand("theta")
        val delta = avgBand("delta")
        val gamma = avgBand("gamma")

        return BrainMetrics(
            alphaDe = alpha,
            betaDe = beta,
            thetaDe = theta,
            deltaDe = delta,
            gammaDe = gamma,
            alphaBetaRatio = alpha / (beta + EPSILON),
            engagementIndex = beta / (alpha + theta + EPSILON),
            relaxationIndex = alpha / (beta + EPSILON),
            cognitiveLoad = theta / (alpha + EPSILON),
        )
    }
}
