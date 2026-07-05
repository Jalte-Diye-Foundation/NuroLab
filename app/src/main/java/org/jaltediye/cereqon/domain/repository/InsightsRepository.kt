package org.jaltediye.cereqon.domain.repository

import kotlinx.coroutines.flow.Flow
import org.jaltediye.cereqon.domain.model.InsightSession
import org.jaltediye.cereqon.domain.model.InsightWindowSnapshot
import org.jaltediye.cereqon.domain.model.LiveWindow

/**
 * Persistence and retrieval for Insights session history via Room.
 * No analytics or derived metrics — storage and read-through only.
 *
 * **Read path:** reactive [Flow] observers emit on every Room table change.
 * **Write path:** suspend functions used by stream owners (Dashboard, Calibration).
 */
interface InsightsRepository {

    /** Reactive active-session observer; emits `null` when no session is open. */
    fun observeActiveSession(): Flow<InsightSession?>

    /** Reactive window snapshots for [sessionId], ordered by window end time. */
    fun observeWindowSnapshots(sessionId: Long): Flow<List<InsightWindowSnapshot>>

    /** Reactive snapshot count for [sessionId]. */
    fun observeWindowSnapshotCount(sessionId: Long): Flow<Int>

    suspend fun getActiveSession(): InsightSession?

    suspend fun getSession(sessionId: Long): InsightSession?

    suspend fun getWindowSnapshots(sessionId: Long): List<InsightWindowSnapshot>

    suspend fun countWindowSnapshots(sessionId: Long): Int

    suspend fun startSession(serverBaseUrl: String, calibratedAtStart: Boolean): Long

    suspend fun endSession(sessionId: Long, endedAtEpochMs: Long)

    suspend fun recordWindowSnapshot(sessionId: Long, window: LiveWindow): Long
}
