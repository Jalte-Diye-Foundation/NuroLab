package org.jaltediye.cereqon.domain.model

/**
 * User-selected appearance persisted in DataStore.
 */
enum class ThemeMode {
    SYSTEM,
    LIGHT,
    DARK,
    ;

    fun isDark(isSystemInDarkTheme: Boolean): Boolean =
        when (this) {
            SYSTEM -> isSystemInDarkTheme
            LIGHT -> false
            DARK -> true
        }

    companion object {
        fun fromStored(value: String?): ThemeMode =
            when (value?.lowercase()) {
                LIGHT.name.lowercase() -> LIGHT
                DARK.name.lowercase() -> DARK
                else -> SYSTEM
            }

        fun storageValue(mode: ThemeMode): String = mode.name.lowercase()
    }
}
