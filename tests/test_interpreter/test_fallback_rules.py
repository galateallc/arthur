"""Tests for the collapsed fallback rule (single cortisol nudge)."""

from __future__ import annotations

from kindalive.engine.chemicals import Chemical
from kindalive.interpreter.fallback_rules import has_fallback, lookup_fallback
from kindalive.interpreter.text_input import UserText


def test_fallback_returns_cortisol_nudge():
    impulses = lookup_fallback(UserText(summary="anything at all"))
    assert len(impulses) == 1
    assert impulses[0].chemical == Chemical.CORTISOL
    assert impulses[0].delta == 0.05
    assert impulses[0].source_id == "fallback:freeform"


def test_fallback_is_independent_of_summary_content():
    """The single rule does not branch on text — that's the whole point."""
    a = lookup_fallback(UserText(summary="you won the lottery"))
    b = lookup_fallback(UserText(summary="the cat is missing"))
    assert a[0].chemical == b[0].chemical
    assert a[0].delta == b[0].delta


def test_has_fallback_is_always_true():
    assert has_fallback(UserText(summary="anything")) is True
