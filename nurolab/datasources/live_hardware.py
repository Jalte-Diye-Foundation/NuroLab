# File: nurolab/datasources/live_hardware.py
# TEMPLATE — fill in the marked sections once hardware team delivers
# their circuit diagram + firmware data format.
#
# Before writing: get 3 answers from the hardware team:
#   1. Transport: USB-Serial, BLE, WiFi/WebSocket, UDP?
#   2. Frame format: binary struct layout, or CSV/JSON?
#   3. Confirmed sample rate, channel count, channel names/order?

import serial           # pip install pyserial
import numpy as np
from .base import EEGDataSource


class LiveHardwareSource(EEGDataSource):
    """
    Adapter for the real Nurolab device. This is the ONLY class in
    the entire codebase that needs to know about the physical hardware's
    data format.

    Fill in the marked sections once the firmware spec is confirmed.
    """

    def __init__(
        self,
        port: str,
        baud: int = 115200,
        fs: float = 256.0,          # <-- CONFIRM with HW team
        channel_names: list = None,  # <-- CONFIRM with HW team
    ):
        self._fs = fs
        self._names = channel_names or [f"CH{i+1}" for i in range(8)]
        self._ser = serial.Serial(port, baud, timeout=1)

    @property
    def sample_rate(self) -> float:
        return self._fs

    @property
    def channel_names(self) -> list:
        return self._names

    @property
    def n_channels(self) -> int:
        return len(self._names)

    def is_live(self) -> bool:
        return True

    def read_chunk(self, n_samples: int) -> np.ndarray:
        """
        ==== FILL IN ONCE FIRMWARE FORMAT IS CONFIRMED ====

        Example below assumes CSV lines like:
            '<timestamp_ms>,<ch1>,<ch2>,...,<chN>\\n'

        Replace the parsing logic to match your actual firmware output.
        """
        rows = []
        while len(rows) < n_samples:
            line = self._ser.readline().decode("ascii", errors="ignore").strip()
            if not line or line.startswith("["):
                continue
            parts = line.split(",")
            if len(parts) != self.n_channels + 1:
                continue  # malformed frame, skip
            try:
                values = [float(p) for p in parts[1:]]
                rows.append(values)
            except ValueError:
                continue
        return np.array(rows, dtype=float)

    def close(self):
        if hasattr(self, "_ser") and self._ser.is_open:
            self._ser.close()


# ── Alternative: WebSocket transport ─────────────────────────────────────────
# If hardware streams over WiFi, replace LiveHardwareSource above with this:
#
# import asyncio, websockets, struct, queue, threading
#
# class LiveHardwareSourceWS(EEGDataSource):
#     def __init__(self, ws_url, fs=256.0, channel_names=None):
#         self._fs = fs
#         self._names = channel_names or [f'CH{i+1}' for i in range(8)]
#         self._q = queue.Queue()
#         threading.Thread(target=self._run, args=(ws_url,), daemon=True).start()
#
#     def _run(self, url):
#         async def _listen():
#             async with websockets.connect(url) as ws:
#                 async for msg in ws:
#                     # FILL IN: unpack binary struct per firmware spec
#                     # e.g. struct.unpack(f'>{self.n_channels}f', msg)
#                     values = struct.unpack(f'>{self.n_channels}f', msg)
#                     self._q.put(values)
#         asyncio.run(_listen())
#
#     def read_chunk(self, n_samples):
#         rows = [self._q.get() for _ in range(n_samples)]
#         return np.array(rows, dtype=float)
