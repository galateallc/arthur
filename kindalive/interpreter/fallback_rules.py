"""Fallback impulse for when the LLM is unavailable.

The freeform-paragraph pipeline trusts the LLM. When it fails (network
error, rate limit, parse error), we still want the robot to flinch
slightly rather than go numb — so we nudge cortisol up by a small amount
to register that *something* happened. The 14 source-keyed rules from
the fetcher era have been removed: there is no "weather:storm" or
"sports:goal" event type anymore, only `user:freeform`.
"""

from __future__ import annotations

from kindalive.engine.chemicals import Chemical
from kindalive.engine.impulse import ChemicalImpulse
from kindalive.interpreter.text_input import UserText

_FALLBACK_IMPULSES = [
    ChemicalImpulse(
        Chemical.CORTISOL,
        delta=0.05,
        source_id="fallback:freeform",
        source_label="LLM unavailable — generic stress nudge",
    ),
]


def lookup_fallback(event: UserText) -> list[ChemicalImpulse]:
    """Return the default fallback impulses (a small cortisol nudge)."""
    return list(_FALLBACK_IMPULSES)


def has_fallback(event: UserText) -> bool:
    """A fallback always exists — the default nudge."""
    return True
