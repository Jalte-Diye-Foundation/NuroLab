package org.jaltediye.cereqon.domain.repository

import org.jaltediye.cereqon.domain.model.LiveWindow
import org.jaltediye.cereqon.domain.model.StreamConnectionState
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.StateFlow

/**
 * Live WebSocket stream from /ws/live.
 *
 * ## Stream ownership
 *
 * | Feature | Role | Lifecycle |
 * |---------|------|-----------|
 * | **Dashboard** | Owner | Calls [start] on enter, [stop] on leave (`onCleared`) |
 * | **Calibration** | Owner (transient) | Calls [start] during collection, [stop] on completion |
 * | **Insights** | Read-only observer | Observes [connectionState] only; never calls [start] or [stop] |
 *
 * Only one owner may drive the singleton [LiveStreamWebSocketManager] at a time.
 * Navigation pop semantics ensure Dashboard and Calibration do not overlap.
 */
interface LiveStreamRepository {
    val connectionState: StateFlow<StreamConnectionState>
    val reconnectAttemptCount: StateFlow<Int>
    val windows: Flow<LiveWindow>

    fun start()
    fun stop()
}
