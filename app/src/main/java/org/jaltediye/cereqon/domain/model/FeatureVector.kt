package org.jaltediye.cereqon.domain.model

/**
 * Ordered feature vector aligned with backend build_feature_names() ordering.
 */
data class FeatureVector(
    val values: List<Float>,
    val names: List<String>,
) {
    val size: Int get() = values.size

    fun valueAt(index: Int): Float = values[index]

    fun valueByName(name: String): Float? {
        val index = names.indexOf(name)
        return if (index >= 0) values[index] else null
    }

    fun indexed(): Map<String, Float> = names.zip(values).toMap()
}
