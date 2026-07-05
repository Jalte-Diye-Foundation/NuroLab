package org.jaltediye.cereqon.data.local.entity

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(tableName = "sessions")
data class SessionEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    @ColumnInfo(name = "started_at_epoch_ms")
    val startedAtEpochMs: Long,
    @ColumnInfo(name = "ended_at_epoch_ms")
    val endedAtEpochMs: Long? = null,
    @ColumnInfo(name = "server_base_url")
    val serverBaseUrl: String,
    @ColumnInfo(name = "calibrated_at_start")
    val calibratedAtStart: Boolean,
)

@Entity(
    tableName = "window_snapshots",
    indices = [
        Index(value = ["session_id", "window_end_time"], unique = true),
        Index(value = ["captured_at_epoch_ms"]),
    ],
)
data class WindowSnapshotEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    @ColumnInfo(name = "session_id")
    val sessionId: Long,
    @ColumnInfo(name = "window_start_time")
    val windowStartTime: Double,
    @ColumnInfo(name = "window_end_time")
    val windowEndTime: Double,
    @ColumnInfo(name = "captured_at_epoch_ms")
    val capturedAtEpochMs: Long,
    @ColumnInfo(name = "risk_tier")
    val riskTier: Int? = null,
    @ColumnInfo(name = "mahalanobis")
    val mahalanobis: Double? = null,
    @ColumnInfo(name = "predictions_json")
    val predictionsJson: String? = null,
)

@Entity(tableName = "calibration_attempts")
data class CalibrationAttemptEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    @ColumnInfo(name = "started_at_epoch_ms")
    val startedAtEpochMs: Long,
    @ColumnInfo(name = "completed_at_epoch_ms")
    val completedAtEpochMs: Long? = null,
    @ColumnInfo(name = "windows_collected")
    val windowsCollected: Int,
    @ColumnInfo(name = "windows_submitted")
    val windowsSubmitted: Int,
    @ColumnInfo(name = "outcome_status")
    val outcomeStatus: String? = null,
    @ColumnInfo(name = "error_message")
    val errorMessage: String? = null,
)

@Entity(tableName = "reports")
data class ReportEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    @ColumnInfo(name = "title")
    val title: String,
    @ColumnInfo(name = "created_at_epoch_ms")
    val createdAtEpochMs: Long,
    @ColumnInfo(name = "file_path")
    val filePath: String,
    @ColumnInfo(name = "format")
    val format: String,
)
