"""ImpulseValidator — sanitize and validate LLM-produced impulses.

Validation steps:
1. Schema check — correct field names and types
2. Chemical names — must be one of the 8 known chemicals
3. Delta clamping — values outside [-0.5, +0.5] get clamped
4. Duration clamping — [0, 300] seconds
5. Array size — reject responses with more than 8 impulses
"""

from __future__ import annotations

from typing import Any

from kindalive.engine.chemicals import Chemical
from kindalive.engine.impulse import ChemicalImpulse

# Validation bounds
MAX_DELTA = 0.5
MIN_DELTA = -0.5
MAX_DURATION = 300.0
MAX_IMPULSES = 8


class ValidationError(Exception):
    """Raised when impulse data is structurally invalid."""


def validate_raw_impulses(raw: list[dict[str, Any]]) -> list[ChemicalImpulse]:
    """Validate and convert raw dicts (from LLM JSON) to ChemicalImpulse list.

    Returns validated impulses. Raises ValidationError for structural problems.
    Individual impulses with bad chemical names are skipped (not fatal).
    """
    if not isinstance(raw, list):
        raise ValidationError(f"Expected list, got {type(raw).__name__}")

    if len(raw) > MAX_IMPULSES:
        raise ValidationError(
            f"Too many impulses: {len(raw)} (max {MAX_IMPULSES})"
        )

    impulses: list[ChemicalImpulse] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValidationError(f"Impulse [{i}] is not a dict")

        # Chemical name (required)
        chem_name = item.get("chemical")
        if not isinstance(chem_name, str):
            raise ValidationError(f"Impulse [{i}] missing or invalid 'chemical'")

        try:
            chemical = Chemical.from_string(chem_name)
        except ValueError:
            # Skip unknown chemicals rather than failing the whole batch
            continue

        # Delta (required)
        delta = item.get("delta")
        if delta is None:
            raise ValidationError(f"Impulse [{i}] missing 'delta'")
        try:
            delta = float(delta)
        except (TypeError, ValueError):
            raise ValidationError(f"Impulse [{i}] 'delta' is not a number")

        # Clamp delta
        delta = max(MIN_DELTA, min(MAX_DELTA, delta))

        # Duration (optional, default 0)
        duration = item.get("duration_seconds", 0)
        try:
            duration = float(duration)
        except (TypeError, ValueError):
            duration = 0.0
        duration = max(0.0, min(MAX_DURATION, duration))

        # Source fields (optional)
        source_id = str(item.get("source_id", ""))
        source_label = str(item.get("source_label", ""))

        impulses.append(
            ChemicalImpulse(
                chemical=chemical,
                delta=delta,
                duration_seconds=duration,
                source_id=source_id,
                source_label=source_label,
            )
        )

    return impulses
