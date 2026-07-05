package org.jaltediye.cereqon.data.repository

import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import org.jaltediye.cereqon.data.local.dao.SessionDao
import org.jaltediye.cereqon.data.local.dao.WindowSnapshotDao
import org.jaltediye.cereqon.data.local.mapper.InsightSessionMapper
import org.jaltediye.cereqon.data.local.mapper.InsightWindowSnapshotMapper
import org.jaltediye.cereqon.domain.model.InsightSession
import org.jaltediye.cereqon.domain.model.InsightWindowSnapshot
import org.jaltediye.cereqon.domain.model.LiveWindow
import org.jaltediye.cereqon.domain.repository.InsightsRepository

@Singleton
class InsightsRepositoryImpl @Inject constructor(
    private val sessionDao: SessionDao,
    private val windowSnapshotDao: WindowSnapshotDao,
) : InsightsRepository {

    private val sessionMutex = Mutex()

    override fun observeActiveSession(): Flow<InsightSession?> =
        sessionDao.observeActiveSession().map { entity ->
            entity?.let(InsightSessionMapper::toDomain)
        }

    override fun observeWindowSnapshots(sessionId: Long): Flow<List<InsightWindowSnapshot>> =
        windowSnapshotDao.observeBySession(sessionId).map { entities ->
            entities.map(InsightWindowSnapshotMapper::toDomain)
        }

    override fun observeWindowSnapshotCount(sessionId: Long): Flow<Int> =
        windowSnapshotDao.observeCountBySession(sessionId)

    override suspend fun getActiveSession(): InsightSession? =
        sessionDao.getActiveSession()?.let(InsightSessionMapper::toDomain)

    override suspend fun getSession(sessionId: Long): InsightSession? =
        sessionDao.getById(sessionId)?.let(InsightSessionMapper::toDomain)

    override suspend fun getWindowSnapshots(sessionId: Long): List<InsightWindowSnapshot> =
        windowSnapshotDao.getBySession(sessionId).map(InsightWindowSnapshotMapper::toDomain)

    override suspend fun countWindowSnapshots(sessionId: Long): Int =
        windowSnapshotDao.countBySession(sessionId)

    override suspend fun startSession(
        serverBaseUrl: String,
        calibratedAtStart: Boolean,
    ): Long = sessionMutex.withLock {
        val active = sessionDao.getActiveSession()
        if (active != null) {
            return@withLock active.id
        }
        val entity = InsightSessionMapper.newEntity(
            serverBaseUrl = serverBaseUrl,
            calibratedAtStart = calibratedAtStart,
            startedAtEpochMs = System.currentTimeMillis(),
        )
        sessionDao.insert(entity)
    }

    override suspend fun endSession(sessionId: Long, endedAtEpochMs: Long) {
        sessionMutex.withLock {
            val existing = sessionDao.getById(sessionId) ?: return
            if (existing.endedAtEpochMs != null) {
                return
            }
            sessionDao.update(
                existing.copy(endedAtEpochMs = endedAtEpochMs),
            )
        }
    }

    override suspend fun recordWindowSnapshot(sessionId: Long, window: LiveWindow): Long {
        val session = sessionDao.getById(sessionId) ?: return RoomInsertIgnored.ROW_ID
        if (session.endedAtEpochMs != null) {
            return RoomInsertIgnored.ROW_ID
        }
        val entity = InsightWindowSnapshotMapper.fromLiveWindow(sessionId, window)
        return windowSnapshotDao.insert(entity)
    }

    private object RoomInsertIgnored {
        const val ROW_ID: Long = -1L
    }
}
