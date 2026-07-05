package org.jaltediye.cereqon.domain.model

/**
 * Client-computed brain metrics derived from feature vectors.
 * Mirrors backend analytics.py formulas; not provided over WebSocket.
 */
data class BrainMetrics(
    val alphaDe: Double,
    val betaDe: Double,
    val thetaDe: Double,
    val deltaDe: Double,
    val gammaDe: Double,
    val alphaBetaRatio: Double,
    val engagementIndex: Double,
    val relaxationIndex: Double,
    val cognitiveLoad: Double,
)
