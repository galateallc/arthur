"""Tests for all 7 cross-chemical interaction rules + stability."""

from kindalive.engine.chemicals import Chemical
from kindalive.engine.clock import ManualClock
from kindalive.engine.neurochemical_engine import NeurochemicalEngine


def test_cortisol_suppresses_serotonin():
    engine = NeurochemicalEngine(clock=ManualClock())
    engine.state.set(Chemical.CORTISOL, 0.9)
    initial = engine.state.get(Chemical.SEROTONIN)
    engine.advance(dt=60.0)
    assert engine.state.get(Chemical.SEROTONIN) < initial


def test_gaba_dampens_adrenaline():
    with_gaba = NeurochemicalEngine(clock=ManualClock())
    with_gaba.state.set(Chemical.ADRENALINE, 0.8)
    with_gaba.state.set(Chemical.GABA, 0.9)
    without_gaba = NeurochemicalEngine(clock=ManualClock())
    without_gaba.state.set(Chemical.ADRENALINE, 0.8)
    without_gaba.state.set(Chemical.GABA, 0.0)
    with_gaba.advance(dt=30.0)
    without_gaba.advance(dt=30.0)
    assert with_gaba.state.get(Chemical.ADRENALINE) < without_gaba.state.get(Chemical.ADRENALINE)


def test_adrenaline_inhibits_gaba():
    engine = NeurochemicalEngine(clock=ManualClock())
    engine.state.set(Chemical.ADRENALINE, 0.9)
    initial = engine.state.get(Chemical.GABA)
    engine.advance(dt=30.0)
    assert engine.state.get(Chemical.GABA) < initial


def test_testosterone_amplifies_adrenaline():
    with_t = NeurochemicalEngine(clock=ManualClock())
    with_t.state.set(Chemical.ADRENALINE, 0.5)
    with_t.state.set(Chemical.TESTOSTERONE, 0.9)
    without_t = NeurochemicalEngine(clock=ManualClock())
    without_t.state.set(Chemical.ADRENALINE, 0.5)
    without_t.state.set(Chemical.TESTOSTERONE, 0.0)
    with_t.advance(dt=30.0)
    without_t.advance(dt=30.0)
    assert with_t.state.get(Chemical.ADRENALINE) > without_t.state.get(Chemical.ADRENALINE)


def test_oxytocin_suppresses_cortisol():
    with_oxy = NeurochemicalEngine(clock=ManualClock())
    with_oxy.state.set(Chemical.CORTISOL, 0.8)
    with_oxy.state.set(Chemical.OXYTOCIN, 0.9)
    without_oxy = NeurochemicalEngine(clock=ManualClock())
    without_oxy.state.set(Chemical.CORTISOL, 0.8)
    without_oxy.state.set(Chemical.OXYTOCIN, 0.0)
    with_oxy.advance(dt=60.0)
    without_oxy.advance(dt=60.0)
    assert with_oxy.state.get(Chemical.CORTISOL) < without_oxy.state.get(Chemical.CORTISOL)


def test_sustained_cortisol_raises_baseline():
    engine = NeurochemicalEngine(clock=ManualClock())
    initial_bl = engine.state.baseline(Chemical.CORTISOL)
    for _ in range(100):
        engine.state.set(Chemical.CORTISOL, 0.9)
        engine.advance(dt=10.0)
    assert engine.state.baseline(Chemical.CORTISOL) > initial_bl


def test_low_cortisol_recovers_baseline():
    engine = NeurochemicalEngine(clock=ManualClock())
    engine.state.set_baseline(Chemical.CORTISOL, 0.4)
    engine.state.set(Chemical.CORTISOL, 0.1)
    engine.advance(dt=3600.0)
    assert engine.state.baseline(Chemical.CORTISOL) < 0.4


def test_interactions_dont_cause_instability():
    engine = NeurochemicalEngine(clock=ManualClock())
    for chem in Chemical:
        engine.state.set(chem, 1.0)
    engine.advance(dt=10000.0)
    for chem in Chemical:
        level = engine.state.get(chem)
        assert 0.0 <= level <= 1.0, f"{chem}: {level}"


def test_baseline_state_is_a_fixed_point():
    """At rest (all chemicals at baseline) nothing should drift — the
    interactions must vanish at equilibrium."""
    engine = NeurochemicalEngine(clock=ManualClock())
    baselines = {chem: engine.state.get(chem) for chem in Chemical}
    engine.advance(dt=1800.0)  # 30 simulated minutes
    for chem in Chemical:
        assert abs(engine.state.get(chem) - baselines[chem]) < 1e-3, (
            f"{chem.value} drifted from baseline at rest"
        )


def test_adrenaline_spike_does_not_max_out():
    """A strong adrenaline + testosterone spike must decay, not run away
    to the ceiling (regression: GABA collapse used to remove adrenaline's
    damping and let testosterone ratchet it to 1.0)."""
    engine = NeurochemicalEngine(clock=ManualClock())
    engine.state.set(Chemical.ADRENALINE, 0.55)
    engine.state.set(Chemical.TESTOSTERONE, 0.6)
    peak = engine.state.get(Chemical.ADRENALINE)
    engine.advance(dt=300.0)  # 5 minutes
    later = engine.state.get(Chemical.ADRENALINE)
    assert later < peak, "adrenaline rose instead of decaying"
    assert later < 0.5, f"adrenaline stayed too high: {later}"


def test_resting_cortisol_does_not_minimize_out():
    """Cortisol must hold near its baseline at rest, not collapse to 0
    (regression: oxytocin suppression + baseline drift used to pin it)."""
    engine = NeurochemicalEngine(clock=ManualClock())
    baseline = engine.state.baseline(Chemical.CORTISOL)
    engine.advance(dt=1800.0)  # 30 simulated minutes at rest
    cortisol = engine.state.get(Chemical.CORTISOL)
    assert abs(cortisol - baseline) < 0.05, (
        f"cortisol drifted to {cortisol} from baseline {baseline}"
    )
    assert engine.state.baseline(Chemical.CORTISOL) == baseline, (
        "cortisol baseline ratcheted at normal rest"
    )


def test_oxytocin_cannot_drive_cortisol_below_baseline():
    """Bonding eases elevated stress but doesn't push cortisol below rest."""
    engine = NeurochemicalEngine(clock=ManualClock())
    engine.state.set(Chemical.OXYTOCIN, 0.9)  # strong bonding, cortisol at rest
    baseline = engine.state.baseline(Chemical.CORTISOL)
    engine.advance(dt=300.0)
    assert engine.state.get(Chemical.CORTISOL) >= baseline - 1e-6
