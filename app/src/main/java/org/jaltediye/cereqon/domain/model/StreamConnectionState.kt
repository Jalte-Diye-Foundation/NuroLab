package org.jaltediye.cereqon.domain.model

/**
 * WebSocket connection lifecycle states exposed by [org.jaltediye.cereqon.domain.repository.LiveStreamRepository].
 */
enum class StreamConnectionState {
    /** No active connection attempt. */
    DISCONNECTED,

    /** Opening WebSocket to /ws/live. */
    CONNECTING,

    /** WebSocket open; waiting for first payload (~20 s backend buffer fill). */
    WARMUP,

    /** Receiving live window payloads. */
    STREAMING,

    /** Connection lost; retry scheduled. */
    RECONNECTING,

    /** Unrecoverable failure until user action or network change. */
    FAILED,
}
