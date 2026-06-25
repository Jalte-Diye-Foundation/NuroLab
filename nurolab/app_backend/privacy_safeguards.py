# File: nurolab/app_backend/privacy_safeguards.py
# Privacy Safeguards Engine
#
# Enforces ALL five privacy safeguards at the data layer so they
# cannot be bypassed by any upstream caller.
#
# Safeguards:
#   1. Broad event categories only (no person/session labels)
#   2. Coarse time-of-day buckets (no exact timestamps)
#   3. Aggregated insights only (never single-session)
#   4. MIN_EVENTS_FOR_INSIGHT gate before any trend/heatmap
#   5. Only anonymized metrics stored; raw EEG never persisted here

from collections import defaultdict
from .privacy_logger import log_event, MIN_EVENTS_FOR_INSIGHT, ContextType


class PrivacySafeguardsEngine:
    """
    Wraps all insight generation with privacy enforcement.

    Usage:
        engine = PrivacySafeguardsEngine()

        # After each window:
        engine.record(
            risk_tier=2,
            context_type=ContextType.STUDY,
            dominant_feat="Fp1_alpha_DE",
        )

        # When the app requests a chart/heatmap:
        insight = engine.get_insight(ContextType.STUDY)
        if insight is None:
            # Not enough data yet — do NOT render the heatmap
            pass
    """

    def __init__(self):
        # In-memory store: {context_type_value: [anonymized event dicts]}
        # Raw EEG arrays are NEVER placed here.
        self._store = defaultdict(list)

    def record(
        self,
        risk_tier:     int,
        context_type:  ContextType,
        dominant_feat: str,
        note:          str = "",
    ) -> dict:
        """
        Record one anonymized event.
        Raw EEG must NOT be passed here — only high-level metrics.

        Returns:
            The anonymized event dict (for logging/debugging).
        """
        event = log_event(risk_tier, context_type, dominant_feat, note)
        self._store[context_type.value].append(event)
        return event

    def get_insight(self, context_type: ContextType) -> dict | None:
        """
        Returns aggregated insight dict ONLY if MIN_EVENTS_FOR_INSIGHT
        events have been recorded for this context.

        Returns None if below the threshold — the UI MUST NOT render
        a heatmap or trend chart in that case.

        The returned dict contains ONLY aggregate statistics.
        No individual session data is ever exposed.
        """
        events = self._store[context_type.value]

        if len(events) < MIN_EVENTS_FOR_INSIGHT:
            return None  # gate: not enough data to show insight

        avg_risk = sum(e["risk_tier"] for e in events) / len(events)

        tod_counts = defaultdict(int)
        for e in events:
            tod_counts[e["tod_bucket"]] += 1

        # Dominant feature histogram (top 5)
        feat_counts = defaultdict(int)
        for e in events:
            feat_counts[e["dominant_feature"]] += 1
        top_features = sorted(feat_counts.items(), key=lambda x: -x[1])[:5]

        return {
            "context":          context_type.value,
            "n_events":         len(events),
            "avg_risk_tier":    round(avg_risk, 2),
            "tod_distribution": dict(tod_counts),
            "top_features":     dict(top_features),
            # All values are aggregates — no individual session data exposed
        }

    def event_count(self, context_type: ContextType) -> int:
        """How many events have been recorded for this context."""
        return len(self._store[context_type.value])

    def events_until_insight(self, context_type: ContextType) -> int:
        """How many more events needed before insight is available."""
        return max(0, MIN_EVENTS_FOR_INSIGHT - self.event_count(context_type))
