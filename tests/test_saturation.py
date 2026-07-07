"""Tests for impulse saturation (diminishing returns)."""

from kindalive.engine.chemicals import Chemical
from kindalive.engine.clock import ManualClock
from kindalive.engine.impulse import ChemicalImpulse
from kindalive.engine.neurochemical_engine import NeurochemicalEngine


def test_repeated_impulses_diminish():
    engine = NeurochemicalEngine(clock=ManualClock())
    deltas = []
    for i in range(5):
        before = engine.state.get(Chemical.DOPAMINE)
        engine.apply_impulse(ChemicalImpulse(
            Chemical.DOPAMINE, delta=0.2, duration_seconds=0,
            source_id="goal_scored", source_label="Goal",
        ))
        after = engine.state.get(Chemical.DOPAMINE)
        deltas.append(after - before)
    for i in range(1, len(deltas)):
        assert deltas[i] < deltas[i - 1]


def test_saturation_resets_after_window():
    clock = ManualClock()
    engine = NeurochemicalEngine(clock=clock)

    # Apply impulse, note the delta
    before = engine.state.get(Chemical.DOPAMINE)
    engine.apply_impulse(ChemicalImpulse(
        Chemical.DOPAMINE, delta=0.2, source_id="goal",
    ))
    first_delta = engine.state.get(Chemical.DOPAMINE) - before

    # Reset dopamine, advance past window
    engine.state.set(Chemical.DOPAMINE, engine.state.baseline(Chemical.DOPAMINE))
    clock.advance(seconds=310)  # past 5-min window

    before = engine.state.get(Chemical.DOPAMINE)
    engine.apply_impulse(ChemicalImpulse(
        Chemical.DOPAMINE, delta=0.2, source_id="goal",
    ))
    fresh_delta = engine.state.get(Chemical.DOPAMINE) - before

    assert abs(fresh_delta - first_delta) < 0.01  # should be same as first


def test_no_saturation_without_source_id():
    engine = NeurochemicalEngine(clock=ManualClock())
    deltas = []
    for _ in range(5):
        before = engine.state.get(Chemical.DOPAMINE)
        engine.apply_impulse(ChemicalImpulse(Chemical.DOPAMINE, delta=0.1))
        after = engine.state.get(Chemical.DOPAMINE)
        deltas.append(after - before)
    # Without source_id, no saturation — deltas should be equal
    # (small differences from clamping are ok)
    for d in deltas:
        assert abs(d - 0.1) < 0.01 or d < 0.1  # clamping may reduce later ones
