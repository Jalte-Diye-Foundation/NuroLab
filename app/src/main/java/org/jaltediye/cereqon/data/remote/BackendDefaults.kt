package org.jaltediye.cereqon.data.remote

/**
 * Backend-aligned defaults from nurolab/app_backend/server.py SyntheticEEGSource configuration.
 */
object BackendDefaults {
    const val SAMPLE_RATE_HZ = 256.0
    const val WINDOW_SEC = 20.0
    const val STRIDE_SEC = 2.0
    const val CHANNEL_COUNT = 8

    val CHANNEL_NAMES: List<String> = listOf(
        "Fp1", "Fp2", "F3", "F4", "T7", "T8", "O1", "O2",
    )

    const val FEATURE_COUNT = CHANNEL_COUNT * 8 // 5 DE bands + 3 Hjorth per channel

    /** Backend buffer fill time before first WebSocket payload (seconds). */
    const val WARMUP_SEC = WINDOW_SEC
}
