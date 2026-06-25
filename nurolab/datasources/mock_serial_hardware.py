# File: nurolab/datasources/mock_serial_hardware.py
# Simulates a serial port sending CSV EEG lines, so you can test
# LiveHardwareSource's parsing logic before real hardware exists.
# Integration day = zero surprises.

import threading
import time
import numpy as np


class MockSerialPort:
    """
    Drop-in replacement for serial.Serial for local testing.

    Spawns a background thread that generates synthetic CSV EEG
    lines at the correct sample rate, just like real firmware would.

    Usage:
        src = LiveHardwareSource.__new__(LiveHardwareSource)
        src._ser = MockSerialPort(n_channels=8, fs=256.0)
        src._fs = 256.0
        src._names = [f'CH{i+1}' for i in range(8)]
        chunk = src.read_chunk(256)  # works exactly like real hardware
    """

    def __init__(self, n_channels: int = 8, fs: float = 256.0):
        self.n_channels = n_channels
        self.fs = fs
        self._buf = []
        self._lock = threading.Lock()
        self._running = True
        self._rng = np.random.default_rng(seed=0)
        threading.Thread(target=self._generate, daemon=True).start()

    def _generate(self):
        t = 0.0
        interval = 1.0 / self.fs
        while self._running:
            start = time.time()
            # Synthetic EEG: pink noise + 10 Hz alpha
            vals = self._rng.standard_normal(self.n_channels) * 30.0
            vals[0] += 15 * np.sin(2 * np.pi * 10 * t)  # alpha on ch0
            ts_ms = int(time.time() * 1000)
            csv = f"{ts_ms}," + ",".join(f"{v:.4f}" for v in vals) + "\n"
            with self._lock:
                self._buf.append(csv.encode("ascii"))
            t += interval
            # Pace to correct sample rate
            elapsed = time.time() - start
            if elapsed < interval:
                time.sleep(interval - elapsed)

    def readline(self) -> bytes:
        """Blocks until one line is available (matches serial.Serial.readline)."""
        while True:
            with self._lock:
                if self._buf:
                    return self._buf.pop(0)
            time.sleep(0.001)

    @property
    def is_open(self) -> bool:
        return self._running

    def close(self):
        self._running = False
