package org.jaltediye.cereqon.data.local.mapper

import org.jaltediye.cereqon.data.local.entity.ReportEntity
import org.jaltediye.cereqon.domain.model.Report

object ReportMapper {

    fun toDomain(entity: ReportEntity): Report =
        Report(
            id = entity.id,
            title = entity.title,
            createdAtEpochMs = entity.createdAtEpochMs,
            filePath = entity.filePath,
            format = entity.format,
        )

    fun toEntity(report: Report): ReportEntity =
        ReportEntity(
            id = report.id,
            title = report.title,
            createdAtEpochMs = report.createdAtEpochMs,
            filePath = report.filePath,
            format = report.format,
        )

    fun newEntity(
        title: String,
        createdAtEpochMs: Long,
        filePath: String,
        format: String,
    ): ReportEntity =
        ReportEntity(
            title = title,
            createdAtEpochMs = createdAtEpochMs,
            filePath = filePath,
            format = format,
        )
}
