package org.jaltediye.cereqon.presentation.reports.components

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import org.jaltediye.cereqon.R
import org.jaltediye.cereqon.domain.model.Report
import org.jaltediye.cereqon.presentation.dashboard.components.DashboardLabelValue
import org.jaltediye.cereqon.presentation.reports.ReportExportStatus
import org.jaltediye.cereqon.presentation.reports.exportStatus
import org.jaltediye.cereqon.presentation.reports.formatReportEpochMs
import org.jaltediye.cereqon.presentation.reports.parsedSessionId

@Composable
internal fun ReportsHistoryItem(
    report: Report,
    modifier: Modifier = Modifier,
) {
    val sessionReference = report.parsedSessionId()?.let { sessionId ->
        stringResource(R.string.reports_session_reference_value, sessionId)
    } ?: report.title.takeIf { it.isNotBlank() }
        ?: stringResource(R.string.reports_session_reference_unknown)

    val exportStatusLabel = when (report.exportStatus()) {
        ReportExportStatus.Exported ->
            stringResource(R.string.reports_export_status_exported)
        ReportExportStatus.Pending ->
            stringResource(R.string.reports_export_status_pending)
    }

    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.medium,
        color = MaterialTheme.colorScheme.surfaceContainerHighest,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Text(
                text = report.title.ifBlank {
                    stringResource(R.string.reports_report_item_title, report.id)
                },
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.onSurface,
            )

            DashboardLabelValue(
                label = stringResource(R.string.reports_report_date),
                value = formatReportEpochMs(report.createdAtEpochMs),
            )
            DashboardLabelValue(
                label = stringResource(R.string.reports_session_reference),
                value = sessionReference,
            )
            DashboardLabelValue(
                label = stringResource(R.string.reports_export_status),
                value = exportStatusLabel,
            )
            if (report.format.isNotBlank()) {
                DashboardLabelValue(
                    label = stringResource(R.string.reports_format_label),
                    value = report.format,
                )
            }
        }
    }
}
