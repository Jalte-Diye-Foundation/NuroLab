# File: nurolab/app_backend/services/burnout_risk_service.py
#
# Combines the 4 longitudinal trends (deviation_score, stress, attention,
# fatigue — see longitudinal_trend_service.py) into a single composite
# signal. This is a SYNTHESIS layer, not a new data source or new model
# — it just counts how many trends point in a "concerning" direction at
# once, which is more meaningful than any single metric trending alone
# (a single rising metric could be noise; several rising together over
# real time is a more honest pattern to flag).
#
# IMPORTANT — language discipline: this is explicitly NOT a diagnosis.
# It flags a pattern worth noticing, nothing more. No clinical claims.

from __future__ import annotations

RISK_TIER_DESCRIPTIONS = {
    "low": "No concerning pattern detected across your recent sessions.",
    "moderate": "Some indicators have been trending in a less favorable "
                 "direction across your recent sessions. Worth keeping an eye on.",
    "elevated": "Multiple indicators have been trending in a less favorable "
                 "direction together across your recent sessions. This is a "
                 "pattern worth paying attention to — not a diagnosis, but a "
                 "signal that rest or a lighter workload might help.",
}


def compute_burnout_signal(trends: dict) -> dict:
    """Takes the output of longitudinal_trend_service.analyze_trends()
    and derives a single composite signal.

    Returns:
        {
            "status": "ok" | "insufficient_data",
            "concerning_count": int,       # how many of 4 trends are concerning
            "concerning_signals": [str],   # which ones, by name
            "risk_tier": "low" | "moderate" | "elevated",
            "message": str,                # plain-language, non-diagnostic
        }
    """
    if trends.get("status") != "ok":
        # Not enough session history yet — pass the same insufficient_data
        # signal through rather than pretending we can say anything.
        return {
            "status": "insufficient_data",
            "sessions_analyzed": trends.get("sessions_analyzed", 0),
            "sessions_needed": trends.get("sessions_needed"),
        }

    concerning_signals = []

    if trends["deviation_score"]["trend"] == "rising":
        concerning_signals.append("deviation_score")
    if trends["stress"]["trend"] == "rising":
        concerning_signals.append("stress")
    if trends["fatigue"]["trend"] == "rising":
        concerning_signals.append("fatigue")
    if trends["attention"]["trend"] == "falling":
        concerning_signals.append("attention")

    count = len(concerning_signals)

    if count >= 3:
        tier = "elevated"
    elif count == 2:
        tier = "moderate"
    else:
        tier = "low"

    return {
        "status": "ok",
        "concerning_count": count,
        "concerning_signals": concerning_signals,
        "risk_tier": tier,
        "message": RISK_TIER_DESCRIPTIONS[tier],
    }
