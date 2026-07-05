package org.jaltediye.cereqon.domain.model

/**
 * ML prediction for a single condition (depression, epilepsy, etc.).
 */
sealed class Prediction {
    abstract val condition: String

    data class Success(
        override val condition: String,
        val label: String,
        val confidence: Double,
    ) : Prediction()

    data class Failed(
        override val condition: String,
        val error: String,
    ) : Prediction()
}
