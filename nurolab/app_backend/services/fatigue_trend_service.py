# Cognitive fatigue trend detection. Does NOT introduce a new metric —
# it watches the existing cognitive_load value (theta/alpha ratio,
# already computed every ~2s in analytics.py) over the course of a
# session, and detects a genuine upward trend using linear regression
# slope, rather than reacting to normal window-to-window noise.
#
# No clinical claims, no new model — just trend detection on an
# existing, already-validated metric.

from __future__ import annotations

import numpy as np


class FatigueTrendTracker:
    """Tracks cognitive_load values across a session and detects a
    genuine rising trend. One instance per live session — same pattern
    as DeviationEngine's session-level lifecycle (see deviation_engine.py).
    """

    def __init__(self, window_size: int = 30, slope_threshold: float = 0.01):
        """
        Args:
            window_size: how many recent readings to consider (at ~2s
                per reading, 30 = last ~1 minute of session data)
            slope_threshold: minimum upward slope (per reading) to call
                it a genuine trend rather than noise. Tune this once
                real session data is available — 0.01 is a starting
                estimate, not a validated clinical threshold.
        """
        self.window_size = window_size
        self.slope_threshold = slope_threshold
        self._history: list[float] = []

    def add_reading(self, cognitive_load: float) -> dict:
        """Call this once per live window with the current cognitive_load
        value. Returns the current trend status.
        """
        self._history.append(cognitive_load)
        if len(self._history) > self.window_size:
            self._history.pop(0)

        return self._evaluate()

    def _evaluate(self) -> dict:
        n = len(self._history)
        if n < 5:
            # Not enough data yet to say anything meaningful.
            return {
                "fatigue_trend": "insufficient_data",
                "slope": None,
                "readings_collected": n,
            }

        x = np.arange(n)
        y = np.array(self._history)
        # Simple linear regression slope — least squares fit.
        slope = float(np.polyfit(x, y, 1)[0])

        if slope > self.slope_threshold:
            trend = "rising"
        elif slope < -self.slope_threshold:
            trend = "falling"
        else:
            trend = "stable"

        return {
            "fatigue_trend": trend,
            "slope": round(slope, 5),
            "readings_collected": n,
        }