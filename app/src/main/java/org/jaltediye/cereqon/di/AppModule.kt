package org.jaltediye.cereqon.di

import android.content.Context
import androidx.room.Room
import org.jaltediye.cereqon.BuildConfig
import org.jaltediye.cereqon.data.local.dao.CalibrationAttemptDao
import org.jaltediye.cereqon.data.local.dao.ReportDao
import org.jaltediye.cereqon.data.local.dao.SessionDao
import org.jaltediye.cereqon.data.local.dao.WindowSnapshotDao
import org.jaltediye.cereqon.data.local.database.CereqonDatabase
import org.jaltediye.cereqon.data.local.preferences.SettingsRepositoryImpl
import org.jaltediye.cereqon.data.remote.DynamicBaseUrlInterceptor
import org.jaltediye.cereqon.data.remote.ServerUrlStore
import org.jaltediye.cereqon.data.remote.api.BackendApiService
import org.jaltediye.cereqon.data.repository.CalibrationRepositoryImpl
import org.jaltediye.cereqon.data.repository.HealthRepositoryImpl
import org.jaltediye.cereqon.data.repository.InsightsRepositoryImpl
import org.jaltediye.cereqon.data.repository.LiveStreamRepositoryImpl
import org.jaltediye.cereqon.data.repository.ReportsExportRepositoryImpl
import org.jaltediye.cereqon.data.repository.ReportsRepositoryImpl
import org.jaltediye.cereqon.domain.repository.CalibrationRepository
import org.jaltediye.cereqon.domain.repository.HealthRepository
import org.jaltediye.cereqon.domain.repository.InsightsRepository
import org.jaltediye.cereqon.domain.repository.LiveStreamRepository
import org.jaltediye.cereqon.domain.repository.ReportsExportRepository
import org.jaltediye.cereqon.domain.repository.ReportsRepository
import org.jaltediye.cereqon.domain.repository.SettingsRepository
import dagger.Binds
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import com.jakewharton.retrofit2.converter.kotlinx.serialization.asConverterFactory
import okhttp3.MediaType.Companion.toMediaType
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {

    private val jsonMediaType = "application/json".toMediaType()

    @Provides
    @Singleton
    fun provideJson(): Json = Json {
        ignoreUnknownKeys = true
        isLenient = true
        encodeDefaults = true
        explicitNulls = false
    }

    @Provides
    @Singleton
    fun provideLoggingInterceptor(): HttpLoggingInterceptor =
        HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) {
                HttpLoggingInterceptor.Level.BODY
            } else {
                HttpLoggingInterceptor.Level.NONE
            }
        }

    @Provides
    @Singleton
    fun provideOkHttpClient(
        dynamicBaseUrlInterceptor: DynamicBaseUrlInterceptor,
        loggingInterceptor: HttpLoggingInterceptor,
    ): OkHttpClient =
        OkHttpClient.Builder()
            .addInterceptor(dynamicBaseUrlInterceptor)
            .addInterceptor(loggingInterceptor)
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .pingInterval(30, TimeUnit.SECONDS)
            .build()

    @Provides
    @Singleton
    fun provideRetrofit(
        okHttpClient: OkHttpClient,
        json: Json,
        serverUrlStore: ServerUrlStore,
    ): Retrofit =
        Retrofit.Builder()
            .baseUrl(serverUrlStore.normalized())
            .client(okHttpClient)
            .addConverterFactory(json.asConverterFactory(jsonMediaType))
            .build()

    @Provides
    @Singleton
    fun provideBackendApiService(retrofit: Retrofit): BackendApiService =
        retrofit.create(BackendApiService::class.java)
}

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideCereqonDatabase(
        @ApplicationContext context: Context,
    ): CereqonDatabase =
        Room.databaseBuilder(
            context,
            CereqonDatabase::class.java,
            CereqonDatabase.DATABASE_NAME,
        ).fallbackToDestructiveMigration()
            .build()

    @Provides
    fun provideSessionDao(database: CereqonDatabase): SessionDao = database.sessionDao()

    @Provides
    fun provideWindowSnapshotDao(database: CereqonDatabase): WindowSnapshotDao =
        database.windowSnapshotDao()

    @Provides
    fun provideCalibrationAttemptDao(database: CereqonDatabase): CalibrationAttemptDao =
        database.calibrationAttemptDao()

    @Provides
    fun provideReportDao(database: CereqonDatabase): ReportDao = database.reportDao()
}

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    @Singleton
    abstract fun bindHealthRepository(impl: HealthRepositoryImpl): HealthRepository

    @Binds
    @Singleton
    abstract fun bindCalibrationRepository(impl: CalibrationRepositoryImpl): CalibrationRepository

    @Binds
    @Singleton
    abstract fun bindLiveStreamRepository(impl: LiveStreamRepositoryImpl): LiveStreamRepository

    @Binds
    @Singleton
    abstract fun bindSettingsRepository(impl: SettingsRepositoryImpl): SettingsRepository

    @Binds
    @Singleton
    abstract fun bindInsightsRepository(impl: InsightsRepositoryImpl): InsightsRepository

    @Binds
    @Singleton
    abstract fun bindReportsRepository(impl: ReportsRepositoryImpl): ReportsRepository

    @Binds
    @Singleton
    abstract fun bindReportsExportRepository(
        impl: ReportsExportRepositoryImpl,
    ): ReportsExportRepository
}
