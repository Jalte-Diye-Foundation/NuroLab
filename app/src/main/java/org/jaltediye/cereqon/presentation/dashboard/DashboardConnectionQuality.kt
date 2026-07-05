package org.jaltediye.cereqon.presentation.dashboard

import org.jaltediye.cereqon.domain.model.StreamConnectionState

/**
 * UI-only connection quality derived from stream state and packet recency.
 * Not a computed analytics metric — reflects transport health only.
 */
enum class DashboardConnectionQuality {
    UNKNOWN,
    EXCELLENT,
    GOOD,
    DEGRADED,
    POOR,
    OFFLINE,
}

fun resolveConnectionQuality(
    connectionState: StreamConnectionState,
    secondsSinceLastPacket: Long?,
): DashboardConnectionQuality {
    return when (connectionState) {
        StreamConnectionState.DISCONNECTED,
        StreamConnectionState.FAILED,
        -> DashboardConnectionQuality.OFFLINE

        StreamConnectionState.CONNECTING,
        StreamConnectionState.WARMUP,
        -> DashboardConnectionQuality.UNKNOWN

        StreamConnectionState.RECONNECTING ->
            DashboardConnectionQuality.POOR

        StreamConnectionState.STREAMING -> {
            when (secondsSinceLastPacket) {
                null -> DashboardConnectionQuality.UNKNOWN
                in 0..4 -> DashboardConnectionQuality.EXCELLENT
                in 5..8 -> DashboardConnectionQuality.GOOD
                in 9..15 -> DashboardConnectionQuality.DEGRADED
                else -> DashboardConnectionQuality.POOR
            }
        }
    }
}
