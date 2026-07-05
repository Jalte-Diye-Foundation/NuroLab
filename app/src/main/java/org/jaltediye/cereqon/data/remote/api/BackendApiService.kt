package org.jaltediye.cereqon.data.remote.api

import org.jaltediye.cereqon.data.remote.dto.BuildBaselineRequestDto
import org.jaltediye.cereqon.data.remote.dto.BuildBaselineResponseDto
import org.jaltediye.cereqon.data.remote.dto.CalibrationStatusResponseDto
import org.jaltediye.cereqon.data.remote.dto.HealthResponseDto
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST

/**
 * Retrofit service for backend REST endpoints defined in nurolab/app_backend/server.py.
 */
interface BackendApiService {

    @GET("health")
    suspend fun getHealth(): HealthResponseDto

    @GET("calibration/status")
    suspend fun getCalibrationStatus(): CalibrationStatusResponseDto

    @POST("calibration/build_baseline")
    suspend fun buildBaseline(
        @Body request: BuildBaselineRequestDto,
    ): BuildBaselineResponseDto
}
