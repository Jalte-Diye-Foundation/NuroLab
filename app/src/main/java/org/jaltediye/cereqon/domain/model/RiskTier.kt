package org.jaltediye.cereqon.domain.model

/**
 * Mahalanobis risk tier mapped from backend deviation.risk_tier (0–3).
 */
enum class RiskTier(val value: Int) {
    BASELINE(0),
    MILD(1),
    MODERATE(2),
    SIGNIFICANT(3),
    ;

    companion object {
        fun fromInt(value: Int): RiskTier =
            entries.firstOrNull { it.value == value } ?: BASELINE
    }
}
