package org.jaltediye.cereqon.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow
import org.jaltediye.cereqon.data.local.entity.CalibrationAttemptEntity
import androidx.room.Update
import org.jaltediye.cereqon.data.local.entity.ReportEntity
import org.jaltediye.cereqon.data.local.entity.SessionEntity
import org.jaltediye.cereqon.data.local.entity.WindowSnapshotEntity

@Dao
interface SessionDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(session: SessionEntity): Long

    @Update
    suspend fun update(session: SessionEntity)

    @Query("SELECT * FROM sessions WHERE ended_at_epoch_ms IS NULL ORDER BY started_at_epoch_ms DESC LIMIT 1")
    suspend fun getActiveSession(): SessionEntity?

    @Query("SELECT * FROM sessions WHERE ended_at_epoch_ms IS NULL ORDER BY started_at_epoch_ms DESC LIMIT 1")
    fun observeActiveSession(): Flow<SessionEntity?>

    @Query("SELECT * FROM sessions WHERE id = :sessionId")
    suspend fun getById(sessionId: Long): SessionEntity?
}

@Dao
interface WindowSnapshotDao {
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insert(snapshot: WindowSnapshotEntity): Long

    @Query(
        """
        SELECT * FROM window_snapshots
        WHERE session_id = :sessionId
        ORDER BY window_end_time ASC
        """,
    )
    suspend fun getBySession(sessionId: Long): List<WindowSnapshotEntity>

    @Query(
        """
        SELECT * FROM window_snapshots
        WHERE session_id = :sessionId
        ORDER BY window_end_time ASC
        """,
    )
    fun observeBySession(sessionId: Long): Flow<List<WindowSnapshotEntity>>

    @Query("SELECT COUNT(*) FROM window_snapshots WHERE session_id = :sessionId")
    suspend fun countBySession(sessionId: Long): Int

    @Query("SELECT COUNT(*) FROM window_snapshots WHERE session_id = :sessionId")
    fun observeCountBySession(sessionId: Long): Flow<Int>
}

@Dao
interface CalibrationAttemptDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(attempt: CalibrationAttemptEntity): Long

    @Update
    suspend fun update(attempt: CalibrationAttemptEntity)

    @Query("SELECT * FROM calibration_attempts ORDER BY started_at_epoch_ms DESC")
    suspend fun getAll(): List<CalibrationAttemptEntity>
}

@Dao
interface ReportDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(report: ReportEntity): Long

    @Query("SELECT * FROM reports ORDER BY created_at_epoch_ms DESC")
    suspend fun getAll(): List<ReportEntity>

    @Query("SELECT * FROM reports ORDER BY created_at_epoch_ms DESC")
    fun observeAll(): Flow<List<ReportEntity>>

    @Query("SELECT * FROM reports WHERE id = :reportId")
    suspend fun getById(reportId: Long): ReportEntity?

    @Query("DELETE FROM reports WHERE id = :reportId")
    suspend fun deleteById(reportId: Long)
}
