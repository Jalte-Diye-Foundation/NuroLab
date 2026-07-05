package org.jaltediye.cereqon.data.local.mapper

import org.jaltediye.cereqon.data.local.entity.SessionEntity
import org.jaltediye.cereqon.data.local.entity.WindowSnapshotEntity
import org.jaltediye.cereqon.domain.model.InsightSession
import org.jaltediye.cereqon.domain.model.InsightWindowSnapshot
import org.jaltediye.cereqon.domain.model.LiveWindow

object InsightSessionMapper {

    fun toDomain(entity: SessionEntity): InsightSession =
        InsightSession(
            id = entity.id,
            startedAtEpochMs = entity.startedAtEpochMs,
            endedAtEpochMs = entity.endedAtEpochMs,
            serverBaseUrl = entity.serverBaseUrl,
            calibratedAtStart = entity.calibratedAtStart,
        )

    fun toEntity(
        session: InsightSession,
    ): SessionEntity =
        SessionEntity(
            id = session.id,
            startedAtEpochMs = session.startedAtEpochMs,
            endedAtEpochMs = session.endedAtEpochMs,
            serverBaseUrl = session.serverBaseUrl,
            calibratedAtStart = session.calibratedAtStart,
        )

    fun newEntity(
        serverBaseUrl: String,
        calibratedAtStart: Boolean,
        startedAtEpochMs: Long,
    ): SessionEntity =
        SessionEntity(
            startedAtEpochMs = startedAtEpochMs,
            serverBaseUrl = serverBaseUrl,
            calibratedAtStart = calibratedAtStart,
        )
}

object InsightWindowSnapshotMapper {

    fun toDomain(entity: WindowSnapshotEntity): InsightWindowSnapshot =
        InsightWindowSnapshot(
            id = entity.id,
            sessionId = entity.sessionId,
            windowStartTime = entity.windowStartTime,
            windowEndTime = entity.windowEndTime,
            capturedAtEpochMs = entity.capturedAtEpochMs,
            riskTier = entity.riskTier,
            mahalanobis = entity.mahalanobis,
            predictionsJson = entity.predictionsJson,
        )

    fun fromLiveWindow(sessionId: Long, window: LiveWindow): WindowSnapshotEntity =
        WindowSnapshotEntity(
            sessionId = sessionId,
            windowStartTime = window.windowStartTime,
            windowEndTime = window.windowEndTime,
            capturedAtEpochMs = window.receivedAtEpochMs,
            riskTier = window.deviation?.riskTier?.value,
            mahalanobis = window.deviation?.mahalanobis,
            predictionsJson = null,
        )
}
