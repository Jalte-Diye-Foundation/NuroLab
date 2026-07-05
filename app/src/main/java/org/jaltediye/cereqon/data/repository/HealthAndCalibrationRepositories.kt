package org.jaltediye.cereqon.data.repository

import org.jaltediye.cereqon.data.remote.api.BackendApiService
import org.jaltediye.cereqon.data.remote.dto.BuildBaselineRequestDto
import org.jaltediye.cereqon.data.remote.mapper.BaselineResultMapper
import org.jaltediye.cereqon.data.remote.mapper.CalibrationStatusMapper
import org.jaltediye.cereqon.data.remote.mapper.HealthMapper
import org.jaltediye.cereqon.domain.model.BaselineResult
import org.jaltediye.cereqon.domain.model.CalibrationStatus
import org.jaltediye.cereqon.domain.model.HealthStatus
import org.jaltediye.cereqon.domain.model.Outcome
import org.jaltediye.cereqon.domain.repository.CalibrationRepository
import org.jaltediye.cereqon.domain.repository.HealthRepository
import org.jaltediye.cereqon.domain.repository.SettingsRepository
import javax.inject.Inject
import retrofit2.HttpException
import java.io.IOException
import javax.inject.Singleton

@Singleton
class HealthRepositoryImpl @Inject constructor(
    private val apiService: BackendApiService,
) : HealthRepository {

    @Volatile
    private var cachedHealth: HealthStatus? = null

    override suspend fun checkHealth(): Outcome<HealthStatus> {
        return try {
            val health = HealthMapper.toDomain(apiService.getHealth())
            cachedHealth = health
            Outcome.Success(health)
        } catch (exception: IOException) {
            Outcome.Error(
                message = "Unable to reach the Cereqon server. Check the URL and network.",
                cause = exception,
            )
        } catch (exception: HttpException) {
            Outcome.Error(
                message = "Server returned HTTP ${exception.code()}",
                cause = exception,
            )
        } catch (exception: Exception) {
            Outcome.Error(
                message = "Health check failed: ${exception.message ?: "Unknown error"}",
                cause = exception,
            )
        }
    }

    override suspend fun getCachedHealth(): HealthStatus? = cachedHealth
}

@Singleton
class CalibrationRepositoryImpl @Inject constructor(
    private val apiService: BackendApiService,
    private val settingsRepository: SettingsRepository,
) : CalibrationRepository {

    override suspend fun getStatus(): Outcome<CalibrationStatus> {
        return try {
            val status = CalibrationStatusMapper.toDomain(apiService.getCalibrationStatus())
            settingsRepository.setLastKnownCalibrated(status.calibrated)
            Outcome.Success(status)
        } catch (exception: IOException) {
            Outcome.Error(
                message = "Unable to reach the Cereqon server.",
                cause = exception,
            )
        } catch (exception: HttpException) {
            Outcome.Error(
                message = "Calibration status failed with HTTP ${exception.code()}",
                cause = exception,
            )
        } catch (exception: Exception) {
            Outcome.Error(
                message = exception.message ?: "Calibration status failed",
                cause = exception,
            )
        }
    }

    override suspend fun submitBaseline(
        relaxedWindows: List<List<Float>>,
    ): Outcome<BaselineResult> {
        if (relaxedWindows.isEmpty()) {
            return Outcome.Error("At least one relaxed window is required for calibration.")
        }

        return try {
            val request = BuildBaselineRequestDto.from(relaxedWindows)
            val response = apiService.buildBaseline(request)
            val result = BaselineResultMapper.toDomain(response)
            settingsRepository.setLastKnownCalibrated(true)
            Outcome.Success(result)
        } catch (exception: IOException) {
            Outcome.Error(
                message = "Baseline upload failed due to a network error.",
                cause = exception,
            )
        } catch (exception: HttpException) {
            Outcome.Error(
                message = "Baseline upload failed with HTTP ${exception.code()}",
                cause = exception,
            )
        } catch (exception: Exception) {
            Outcome.Error(
                message = exception.message ?: "Baseline upload failed",
                cause = exception,
            )
        }
    }
}
