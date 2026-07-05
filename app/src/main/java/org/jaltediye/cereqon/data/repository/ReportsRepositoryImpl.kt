package org.jaltediye.cereqon.data.repository

import javax.inject.Inject
import javax.inject.Singleton
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import org.jaltediye.cereqon.data.local.dao.ReportDao
import org.jaltediye.cereqon.data.local.mapper.ReportMapper
import org.jaltediye.cereqon.domain.model.Report
import org.jaltediye.cereqon.domain.repository.ReportsRepository

@Singleton
class ReportsRepositoryImpl @Inject constructor(
    private val reportDao: ReportDao,
) : ReportsRepository {

    override fun observeReports(): Flow<List<Report>> =
        reportDao.observeAll().map { entities ->
            entities.map(ReportMapper::toDomain)
        }

    override suspend fun getReport(reportId: Long): Report? =
        reportDao.getById(reportId)?.let(ReportMapper::toDomain)

    override suspend fun getAllReports(): List<Report> =
        reportDao.getAll().map(ReportMapper::toDomain)

    override suspend fun saveReportMetadata(
        title: String,
        filePath: String,
        format: String,
        createdAtEpochMs: Long,
    ): Long {
        val entity = ReportMapper.newEntity(
            title = title,
            createdAtEpochMs = createdAtEpochMs,
            filePath = filePath,
            format = format,
        )
        return reportDao.insert(entity)
    }

    override suspend fun deleteReport(reportId: Long) {
        reportDao.deleteById(reportId)
    }
}
