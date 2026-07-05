package org.jaltediye.cereqon.presentation.dashboard

/**
 * Rolling window of raw backend samples for dashboard line charts (max 60 updates).
 */
data class DashboardTimelineHistory(
    val mahalanobis: List<Double> = emptyList(),
    val riskTier: List<Int> = emptyList(),
    val firstFeature: List<Float> = emptyList(),
) {
    fun appendFromWindow(
        mahalanobis: Double?,
        riskTier: Int?,
        firstFeature: Float?,
    ): DashboardTimelineHistory {
        return copy(
            mahalanobis = if (mahalanobis != null) {
                this.mahalanobis.appendCapped(mahalanobis)
            } else {
                this.mahalanobis
            },
            riskTier = if (riskTier != null) {
                this.riskTier.appendCapped(riskTier)
            } else {
                this.riskTier
            },
            firstFeature = if (firstFeature != null) {
                this.firstFeature.appendCapped(firstFeature)
            } else {
                this.firstFeature
            },
        )
    }

    private fun List<Double>.appendCapped(value: Double): List<Double> =
        (this + value).takeLast(MAX_POINTS)

    private fun List<Int>.appendCapped(value: Int): List<Int> =
        (this + value).takeLast(MAX_POINTS)

    private fun List<Float>.appendCapped(value: Float): List<Float> =
        (this + value).takeLast(MAX_POINTS)

    companion object {
        const val MAX_POINTS = 60
    }
}
