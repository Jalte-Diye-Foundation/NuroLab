# File: nurolab/app_backend/eeg/headset_ingest.py
# Receives live sample packets pushed over WebSocket from real NuroLab
# headset firmware, buffers them per-channel, and serves fixed-length
# windows to the rest of the pipeline — the real (non-simulated)
# counterpart to SimulatedEEGSource.
#
# This is the piece that was previously a NotImplementedError stub. It
# implements the client side of the protocol documented in
# HARDWARE_BACKEND_INTERCONNECTION.md: firmware connects to
# ws://<host>/ws/ingest/headset and sends one JSON text frame per packet:
#
#   {
#     "seq": 1042,
#     "timestamp_ms": 1720000000123,
#     "fs": 250,
#     "gain": 24,
#     "unit": "uV",
#     "channels": {
#       "Fp1": [<250 floats, 1 second of samples>],
#       "Fp2": [...],
#       ...
#     }
#   }

from __future__ import annotations

import collections
import logging
import time
from typing import Optional

import numpy as np

logger = logging.getLogger("nurolab.eeg.ingest")


class HeadsetIngestBuffer:
    """Thread-/task-safe ring buffer of the most recent samples per channel,
    fed by the /ws/ingest/headset endpoint and read by /ws/live and the
    clinical-prediction helper endpoints.
    """

    # If no packet has arrived within this many seconds, the headset is
    # considered disconnected and callers should fall back to simulation.
    STALE_AFTER_SEC = 5.0

    def __init__(self, expected_channels: list[str], window_sec: float = 2.0, max_buffer_sec: float = 10.0):
        self.expected_channels = list(expected_channels)
        self.window_sec = window_sec
        self.max_buffer_sec = max_buffer_sec

        self._buffers: dict[str, collections.deque] = {
            ch: collections.deque() for ch in self.expected_channels
        }
        self._reported_fs: Optional[float] = None
        self._reported_gain: Optional[float] = None
        self._reported_unit: Optional[str] = None
        self._last_seq: Optional[int] = None
        self._last_seen: float = 0.0
        self._packets_received: int = 0
        self._dropped_packets: int = 0

    def push_packet(self, packet: dict) -> None:
        """Ingest one packet from firmware. Raises ValueError on malformed input
        (caller should log + drop, not crash the ingest connection)."""
        if "channels" not in packet or "fs" not in packet:
            raise ValueError("Packet missing required 'channels' or 'fs' field")

        fs = float(packet["fs"])
        channels = packet["channels"]
        if not isinstance(channels, dict) or not channels:
            raise ValueError("Packet 'channels' must be a non-empty object")

        self._reported_fs = fs
        self._reported_gain = packet.get("gain", self._reported_gain)
        self._reported_unit = packet.get("unit", self._reported_unit)
        self._last_seq = packet.get("seq", self._last_seq)
        self._last_seen = time.time()
        self._packets_received += 1

        max_len = int(self.max_buffer_sec * fs)
        for ch, samples in channels.items():
            if ch not in self._buffers:
                # Unexpected channel name — buffer it anyway so /hardware/status
                # can surface the mismatch, but don't let it silently vanish.
                self._buffers[ch] = collections.deque(maxlen=max_len)
                logger.warning(
                    "Received unexpected channel '%s' not in expected_channels=%s",
                    ch, self.expected_channels,
                )
            else:
                # (Re)apply maxlen now that we know the real fs.
                if self._buffers[ch].maxlen != max_len:
                    self._buffers[ch] = collections.deque(self._buffers[ch], maxlen=max_len)
            self._buffers[ch].extend(float(s) for s in samples)

    def is_connected(self) -> bool:
        return (time.time() - self._last_seen) < self.STALE_AFTER_SEC if self._last_seen else False

    def get_latest_window(self) -> Optional[tuple[dict[str, np.ndarray], float]]:
        """Returns (channel_data, fs) for the most recent `window_sec` seconds,
        or None if not enough data has arrived yet / headset is disconnected."""
        if not self.is_connected() or self._reported_fs is None:
            return None

        n_needed = int(self.window_sec * self._reported_fs)
        window: dict[str, np.ndarray] = {}
        for ch in self.expected_channels:
            buf = self._buffers.get(ch)
            if buf is None or len(buf) < n_needed:
                return None  # not enough data yet on this channel
            window[ch] = np.array(list(buf)[-n_needed:], dtype=float)

        return window, self._reported_fs

    def status(self) -> dict:
        return {
            "connected": self.is_connected(),
            "last_seen_seconds_ago": round(time.time() - self._last_seen, 2) if self._last_seen else None,
            "reported_fs": self._reported_fs,
            "reported_gain": self._reported_gain,
            "reported_unit": self._reported_unit,
            "last_seq": self._last_seq,
            "packets_received": self._packets_received,
            "channels_seen": sorted(self._buffers.keys()),
            "expected_channels": self.expected_channels,
            "unexpected_channels": sorted(set(self._buffers.keys()) - set(self.expected_channels)),
        }
