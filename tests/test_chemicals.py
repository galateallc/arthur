"""Tests for ChemicalState + decay math."""

from kindalive.engine.chemicals import Chemical, ChemicalState
from kindalive.engine.clock import ManualClock
from kindalive.engine.neurochemical_engine import NeurochemicalEngine


def test_decay_toward_baseline():
    engine = NeurochemicalEngine(clock=ManualClock())
    engine.state.set(Chemical.DOPAMINE, 0.9)
    engine.advance(dt=60.0)
    assert engine.state.get(Chemical.DOPAMINE) < 0.9
    assert engine.state.get(Chemical.DOPAMINE) > engine.state.baseline(Chemical.DOPAMINE)


def test_decay_recovery_from_below_baseline():
    engine = NeurochemicalEngine(clock=ManualClock())
    # Use dopamine (baseline 0.3) — less affected by interactions at default state
    engine.state.set(Chemical.DOPAMINE, 0.05)
    engine.advance(dt=60.0)  # short enough that decay dominates
    assert engine.state.get(Chemical.DOPAMINE) > 0.05


def test_level_clamped_to_range():
    engine = NeurochemicalEngine(clock=ManualClock())
    from kindalive.engine.impulse import ChemicalImpulse

    engine.apply_impulse(ChemicalImpulse(Chemical.DOPAMINE, delta=5.0))
    assert engine.state.get(Chemical.DOPAMINE) <= 1.0
    engine.apply_impulse(ChemicalImpulse(Chemical.DOPAMINE, delta=-5.0))
    assert engine.state.get(Chemical.DOPAMINE) >= 0.0


def test_half_life_accuracy():
    # Test decay on dopamine: baseline 0.3, half-life 1200s.
    # Dopamine has minimal interaction interference at default state.
    engine = NeurochemicalEngine(clock=ManualClock())
    engine.state.set(Chemical.DOPAMINE, 0.9)  # baseline 0.3, half-life 1200s
    engine.advance(dt=1200.0)
    # True half-life: gap closes by 50%
    # Gap = 0.9 - 0.3 = 0.6, after 1 half-life: 0.3 + 0.6 * 0.5 = 0.6
    expected = 0.6
    # Allow wider tolerance because interactions also run
    assert abs(engine.state.get(Chemical.DOPAMINE) - expected) < 0.1


def test_chemical_from_string_case_insensitive():
    assert Chemical.from_string("dopamine") == Chemical.DOPAMINE
    assert Chemical.from_string("DOPAMINE") == Chemical.DOPAMINE
    assert Chemical.from_string("Gaba") == Chemical.GABA
    assert Chemical.from_string("GABA") == Chemical.GABA


def test_chemical_from_string_unknown_raises():
    import pytest

    with pytest.raises(ValueError, match="Unknown chemical"):
        Chemical.from_string("unobtanium")


def test_chemical_state_as_dict():
    state = ChemicalState()
    d = state.as_dict()
    assert "dopamine" in d
    assert "gaba" in d
    assert len(d) == 8


def test_advance_dt_zero_is_noop():
    engine = NeurochemicalEngine(clock=ManualClock())
    engine.state.set(Chemical.DOPAMINE, 0.8)
    engine.advance(dt=0.0)
    assert engine.state.get(Chemical.DOPAMINE) == 0.8


def test_advance_negative_dt_raises():
    import pytest
    engine = NeurochemicalEngine(clock=ManualClock())
    with pytest.raises(ValueError, match="dt must be >= 0"):
        engine.advance(dt=-1.0)


def test_robot_advance_moves_clock():
    """Robot.advance() should move the ManualClock forward."""
    from kindalive.robot import Robot
    clock = ManualClock()
    robot = Robot(engine=NeurochemicalEngine(clock=clock))
    robot.advance(dt=60.0)
    assert clock.now() == 60.0


def test_chemical_state_copy_is_independent():
    state = ChemicalState()
    state.set(Chemical.DOPAMINE, 0.9)
    copy = state.copy()
    state.set(Chemical.DOPAMINE, 0.1)
    assert copy.get(Chemical.DOPAMINE) == 0.9
