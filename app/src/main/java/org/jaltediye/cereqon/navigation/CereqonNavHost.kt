package org.jaltediye.cereqon.navigation

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import org.jaltediye.cereqon.presentation.calibration.CalibrationScreen
import org.jaltediye.cereqon.presentation.dashboard.DashboardScreen
import org.jaltediye.cereqon.presentation.insights.InsightsNavigationEntry
import org.jaltediye.cereqon.presentation.reports.ReportsNavigationEntry
import org.jaltediye.cereqon.presentation.settings.SettingsNavigationEntry
import org.jaltediye.cereqon.presentation.welcome.WelcomeScreen

@Composable
fun CereqonNavHost(
    modifier: Modifier = Modifier,
) {
    val navController = rememberNavController()

    NavHost(
        navController = navController,
        startDestination = Routes.WELCOME,
        modifier = modifier,
    ) {
        composable(Routes.WELCOME) {
            WelcomeScreen(
                onNavigateToCalibration = {
                    navController.navigate(Routes.CALIBRATION) {
                        popUpTo(Routes.WELCOME) { inclusive = true }
                    }
                },
            )
        }
        composable(Routes.CALIBRATION) {
            CalibrationScreen(
                onNavigateToDashboard = {
                    navController.navigate(Routes.DASHBOARD) {
                        popUpTo(Routes.CALIBRATION) { inclusive = true }
                    }
                },
            )
        }
        composable(Routes.DASHBOARD) {
            DashboardScreen(
                onNavigateToInsights = {
                    navController.navigate(Routes.INSIGHTS)
                },
                onNavigateToSettings = {
                    navController.navigate(Routes.SETTINGS)
                },
            )
        }
        composable(Routes.INSIGHTS) {
            InsightsNavigationEntry()
        }
        composable(Routes.REPORTS) {
            ReportsNavigationEntry()
        }
        composable(Routes.SETTINGS) {
            SettingsNavigationEntry(
                onNavigateBack = { navController.popBackStack() },
            )
        }
    }
}
