# File: nurolab/app_backend/privacy_logger.py
# Privacy-Safe Context Logger
#
# Safeguards enforced here:
#   - Broad event categories only (no person/session labels)
#   - Coarse time-of-day buckets (no exact timestamps)
#   - Only anonymized high-level metrics; raw EEG never touches this layer

import hashlib
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class ContextType(Enum):
    STUDY    = "Study"
    WORK     = "Work"
    MEETING  = "Meeting"
    COMMUTE  = "Commute"
    REST     = "Rest"
    EXERCISE = "Exercise"
    OTHER    = "Other"


@dataclass
class SessionEvent:
    # No exact timestamp stored — coarse bucket only (privacy safeguard)
    tod_bucket:       str   # 'morning' | 'afternoon' | 'evening' | 'night'
    context_type:     str
    risk_tier:        int   # 0–3 from risk_tier_from_mahalanobis()
    dominant_feature: str
    journal_note:     str = ""
    session_hash:     str = ""  # opaque 12-char token; not linkable to the user


# Minimum events before any trend or heatmap is shown.
# Prevents re-identification through small sample sizes.
MIN_EVENTS_FOR_INSIGHT = 5   # tune upward if k-anonymity analysis warrants it


def time_of_day(dt: datetime) -> str:
    h = dt.hour
    if  5 <= h < 12: return "morning"
    if 12 <= h < 17: return "afternoon"
    if 17 <= h < 21: return "evening"
    return "night"


def log_event(
    risk_tier:     int,
    context_type:  ContextType,
    dominant_feat: str,
    note:          str = "",
) -> dict:
    """
    Create one anonymized event record.

    Args:
        risk_tier:     0–3 deviation severity
        context_type:  ContextType enum value
        dominant_feat: name of top-deviation feature
        note:          optional free-text user journal note

    Returns:
        Dict (safe to store or transmit — contains NO raw EEG, NO exact time)
    """
    now = datetime.utcnow()
    return asdict(SessionEvent(
        tod_bucket=time_of_day(now),
        context_type=context_type.value,
        risk_tier=risk_tier,
        dominant_feature=dominant_feat,
        journal_note=note,
        # Random opaque hash — cannot be linked back to a session
        session_hash=hashlib.sha256(os.urandom(16)).hexdigest()[:12],
    ))
