package org.jaltediye.cereqon.presentation.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val LightColorScheme = lightColorScheme(
    primary = CereqonPrimary,
    onPrimary = CereqonOnPrimary,
    primaryContainer = CereqonPrimaryContainer,
    onPrimaryContainer = CereqonOnPrimaryContainer,
    secondary = CereqonSecondary,
    onSecondary = CereqonOnSecondary,
    tertiary = CereqonTertiary,
    onTertiary = CereqonOnTertiary,
    background = CereqonBackground,
    onBackground = CereqonOnBackground,
    surface = CereqonSurface,
    onSurface = CereqonOnSurface,
    surfaceVariant = CereqonSurfaceVariant,
    onSurfaceVariant = CereqonOnSurfaceVariant,
    outline = CereqonOutline,
    error = CereqonError,
    onError = CereqonOnError,
    surfaceContainerLow = CereqonSurfaceContainerLow,
    surfaceContainerHighest = CereqonSurfaceContainerHighest,
)

private val DarkColorScheme = darkColorScheme(
    primary = CereqonDarkPrimary,
    onPrimary = CereqonDarkOnPrimary,
    primaryContainer = CereqonDarkPrimaryContainer,
    onPrimaryContainer = CereqonDarkOnPrimaryContainer,
    secondary = CereqonDarkSecondary,
    onSecondary = CereqonDarkOnSecondary,
    tertiary = CereqonTertiary,
    onTertiary = CereqonOnTertiary,
    background = CereqonDarkBackground,
    onBackground = CereqonDarkOnBackground,
    surface = CereqonDarkSurface,
    onSurface = CereqonDarkOnSurface,
    surfaceVariant = CereqonDarkSurfaceVariant,
    onSurfaceVariant = CereqonDarkOnSurfaceVariant,
    outline = CereqonDarkOutline,
    error = CereqonDarkError,
    onError = CereqonDarkOnError,
    surfaceContainerLow = CereqonDarkSurfaceContainerLow,
    surfaceContainerHighest = CereqonDarkSurfaceContainerHighest,
)

@Composable
fun CereqonTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme,
        typography = CereqonTypography,
        content = content,
    )
}
