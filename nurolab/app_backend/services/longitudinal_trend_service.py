# File: nurolab/app_backend/services/longitudinal_trend_service.py
#
# Longitudinal trend detection across SAVED SESSIONS over time (days/
# weeks) — different from fatigue_trend_service.py, which watches
# cognitive_load WITHIN one live connection (minutes-scale). This
# watches session-level aggregates ACROSS separate sessions
# (calendar-time scale), using the same honest linear-regression-slope
# approach, applied to a different axis.
#
# Directly implements the "longitudinal studies — what does someone's
# brain look like over weeks and months" future-research item.

from __future__ import annotations

import numpy as np

MIN_SESSIONS_FOR_TREND = 5  # same reasoning as fatigue_trend_service —
                             # don't claim a trend on too little data


def analyze_trends(sessions: list) -> dict:
    """Takes a list of SessionRecord-like objects (must have .timestamp,
    .deviation_score, .stress_prediction, .attention_prediction,
    .fatigue_prediction — matches session_service.get_history()'s
    return type), ordered oldest-to-newest, and returns trend direction
    + slope for each metric.

    Returns a dict like:
        {
            "sessions_analyzed": int,
            "date_range_days": float,
            "deviation_score": {"trend": "rising", "slope": 0.42},
            "stress": {"trend": "stable", "slope": 0.001},
            ...
        }
    """
    n = len(sessions)
    if n < MIN_SESSIONS_FOR_TREND:
        return {
            "status": "insufficient_data",
            "sessions_analyzed": n,
            "sessions_needed": MIN_SESSIONS_FOR_TREND,
        }

    # Sessions must be oldest-first for slope direction to make sense —
    # session_service.get_history() can return either order depending on
    # the `sort` param, so we defensively re-sort here rather than
    # assume the caller got it right.
    ordered = sorted(sessions, key=lambda s: s.timestamp)

    t0 = ordered[0].timestamp
    days_elapsed = np.array([(s.timestamp - t0).total_seconds() / 86400.0 for s in ordered])
    date_range_days = float(days_elapsed[-1])

    def _trend_for(values: list[float | None], threshold: float) -> dict:
        # Filter out None values (e.g. stress_prediction wasn't always saved)
        valid = [(d, v) for d, v in zip(days_elapsed, values) if v is not None]
        if len(valid) < MIN_SESSIONS_FOR_TREND:
            return {"trend": "insufficient_data", "slope": None, "n_valid": len(valid)}

        x = np.array([d for d, _ in valid])
        y = np.array([v for _, v in valid])
        slope = float(np.polyfit(x, y, 1)[0])  # per-day slope

        if slope > threshold:
            trend = "rising"
        elif slope < -threshold:
            trend = "falling"
        else:
            trend = "stable"
        return {"trend": trend, "slope": round(slope, 5), "n_valid": len(valid)}

    return {
        "status": "ok",
        "sessions_analyzed": n,
        "date_range_days": round(date_range_days, 1),
        "deviation_score": _trend_for([s.deviation_score for s in ordered], threshold=1.0),
        "stress": _trend_for([s.stress_prediction for s in ordered], threshold=0.01),
        "attention": _trend_for([s.attention_prediction for s in ordered], threshold=0.01),
        "fatigue": _trend_for([s.fatigue_prediction for s in ordered], threshold=0.01),
    }
