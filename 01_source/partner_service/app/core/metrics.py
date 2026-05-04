from __future__ import annotations

from prometheus_client import Counter

shadow_comparisons_total = Counter(
    "partner_shadow_comparisons_total",
    "Shadow mode comparison runs",
)
shadow_divergences_total = Counter(
    "partner_shadow_divergences_total",
    "Shadow mode schema divergences",
    ["partner_id"],
)
