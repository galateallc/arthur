# Kindalive — Testing Strategy

## Philosophy

The neurochemical model is the kind of system where bugs manifest as "the robot feels wrong" — subtle, hard to pinpoint, easy to introduce. The testing strategy is designed around two principles:

1. **Test the math, not the feelings.** Every test asserts on chemical concentrations and numeric emotion values, never on subjective interpretations.
2. **Time is injectable.** The core engine never calls `time.time()` or `asyncio.sleep()` directly. A `ManualClock` lets tests advance time explicitly and deterministically.

---

## Test Layers

### 1. Unit Tests — Chemical Mechanics

Test the math of individual chemicals in isolation.

```python
# test_chemicals.py

def test_decay_toward_baseline():
    """A chemical above baseline should decay back down."""
    engine = NeurochemicalEngine(clock=ManualClock())
    engine.state.set(Chemical.DOPAMINE, 0.9)
    engine.advance(dt=60.0)  # advance 60 seconds (internally sub-steps)
    assert engine.state.get(Chemical.DOPAMINE) < 0.9
    assert engine.state.get(Chemical.DOPAMINE) > engine.state.baseline(Chemical.DOPAMINE)

def test_decay_recovery_from_below_baseline():
    """A chemical below baseline should recover back up."""
    engine = NeurochemicalEngine(clock=ManualClock())
    engine.state.set(Chemical.SEROTONIN, 0.1)  # baseline is 0.5
    engine.advance(dt=3600.0)
    assert engine.state.get(Chemical.SEROTONIN) > 0.1

def test_level_clamped_to_range():
    """Levels must stay within [0.0, 1.0]."""
    engine = NeurochemicalEngine(clock=ManualClock())
    engine.apply_impulse(ChemicalImpulse(Chemical.DOPAMINE, delta=5.0))
    assert engine.state.get(Chemical.DOPAMINE) <= 1.0
    engine.apply_impulse(ChemicalImpulse(Chemical.DOPAMINE, delta=-5.0))
    assert engine.state.get(Chemical.DOPAMINE) >= 0.0

def test_half_life_accuracy():
    """After one half-life, the gap to baseline should close by exactly 50%."""
    engine = NeurochemicalEngine(clock=ManualClock())
    engine.state.set(Chemical.ADRENALINE, 1.0)  # baseline 0.1, half-life ~3 min
    engine.advance(dt=180.0)  # 3 minutes = one half-life
    # Using true half-life formula: 2^(-dt/half_life) = 2^(-1) = 0.5
    expected = 0.1 + (1.0 - 0.1) * 0.5  # halfway back to baseline = 0.55
    assert abs(engine.state.get(Chemical.ADRENALINE) - expected) < 0.05
```

**What this catches:** Math errors in decay formulas, clamping failures, baseline misconfiguration.

---

### 2. Unit Tests — Cross-Chemical Interactions

Test that chemicals affect each other correctly.

```python
# test_interactions.py — tests for ALL 7 interaction rules

def test_cortisol_suppresses_serotonin():
    """High cortisol should drag serotonin down over time."""
    engine = NeurochemicalEngine(clock=ManualClock())
    engine.state.set(Chemical.CORTISOL, 0.9)
    initial_serotonin = engine.state.get(Chemical.SEROTONIN)
    engine.advance(dt=60.0)
    assert engine.state.get(Chemical.SEROTONIN) < initial_serotonin

def test_gaba_dampens_adrenaline():
    """High GABA should reduce adrenaline faster than decay alone."""
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
    """High adrenaline should suppress GABA."""
    engine = NeurochemicalEngine(clock=ManualClock())
    engine.state.set(Chemical.ADRENALINE, 0.9)
    initial_gaba = engine.state.get(Chemical.GABA)
    engine.advance(dt=30.0)
    assert engine.state.get(Chemical.GABA) < initial_gaba

def test_testosterone_amplifies_adrenaline():
    """High testosterone should keep adrenaline above what decay alone would produce."""
    with_test = NeurochemicalEngine(clock=ManualClock())
    with_test.state.set(Chemical.ADRENALINE, 0.5)
    with_test.state.set(Chemical.TESTOSTERONE, 0.9)
    without_test = NeurochemicalEngine(clock=ManualClock())
    without_test.state.set(Chemical.ADRENALINE, 0.5)
    without_test.state.set(Chemical.TESTOSTERONE, 0.0)
    with_test.advance(dt=30.0)
    without_test.advance(dt=30.0)
    assert with_test.state.get(Chemical.ADRENALINE) > without_test.state.get(Chemical.ADRENALINE)

def test_oxytocin_suppresses_cortisol():
    """High oxytocin should reduce cortisol faster than decay alone."""
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
    """Cortisol above 0.7 for a sustained period should shift its baseline up."""
    engine = NeurochemicalEngine(clock=ManualClock())
    initial_baseline = engine.state.baseline(Chemical.CORTISOL)
    # Keep cortisol high by repeatedly spiking it
    for _ in range(100):
        engine.state.set(Chemical.CORTISOL, 0.9)
        engine.advance(dt=10.0)
    assert engine.state.baseline(Chemical.CORTISOL) > initial_baseline

def test_low_cortisol_recovers_baseline():
    """Cortisol below 0.3 should slowly recover an elevated baseline."""
    engine = NeurochemicalEngine(clock=ManualClock())
    engine.state.set_baseline(Chemical.CORTISOL, 0.4)  # elevated from default 0.2
    engine.state.set(Chemical.CORTISOL, 0.1)  # keep cortisol low
    engine.advance(dt=3600.0)  # 1 hour of low cortisol
    assert engine.state.baseline(Chemical.CORTISOL) < 0.4

def test_interactions_dont_cause_instability():
    """Run interactions for a long simulated time — nothing should explode."""
    engine = NeurochemicalEngine(clock=ManualClock())
    for chem in Chemical:
        engine.state.set(chem, 1.0)
    engine.advance(dt=10000.0)  # ~2.7 hours of extreme values
    for chem in Chemical:
        assert 0.0 <= engine.state.get(chem) <= 1.0
```

**What this catches:** Interaction feedback loops, numeric instability, runaway values, baseline drift direction and bounds.

---

### 3. Unit Tests — Emotion Projection

Test that chemical states map to expected emotions.

```python
# test_emotion_projection.py

def test_high_dopamine_serotonin_means_happiness():
    state = ChemicalState()
    state.set(Chemical.DOPAMINE, 0.9)
    state.set(Chemical.SEROTONIN, 0.9)
    state.set(Chemical.CORTISOL, 0.0)
    emotions = EmotionProjection.compute(state)
    assert emotions.happiness > 0.6

def test_high_cortisol_low_gaba_means_anxiety():
    state = ChemicalState()
    state.set(Chemical.CORTISOL, 0.9)
    state.set(Chemical.ADRENALINE, 0.7)
    state.set(Chemical.GABA, 0.0)
    state.set(Chemical.SEROTONIN, 0.1)
    emotions = EmotionProjection.compute(state)
    assert emotions.anxiety > emotions.calm
    assert emotions.anxiety > emotions.happiness

def test_default_state_is_neutral():
    """At baseline chemicals, positive emotions are moderate, negative emotions are low."""
    state = ChemicalState()  # all at baseline
    emotions = EmotionProjection.compute(state)
    # Positive/ambient emotions should be moderate at rest
    assert 0.15 < emotions.happiness < 0.5
    assert 0.15 < emotions.calm < 0.5
    assert 0.15 < emotions.bonding < 0.5
    # Negative/arousal emotions should be low at rest
    assert emotions.anxiety < 0.15
    assert emotions.anger < 0.15
    assert emotions.excitement < 0.3
    # No emotion should be extreme
    for value in emotions.as_dict().values():
        assert value < 0.5
```

**What this catches:** Weight misconfiguration, projection formulas that produce nonsensical emotional states.

---

### 4. Unit Tests — Saturation

```python
# test_saturation.py

def test_repeated_impulses_diminish():
    """The same event firing repeatedly should have less effect each time."""
    engine = NeurochemicalEngine(clock=ManualClock())
    deltas = []
    for i in range(5):
        before = engine.state.get(Chemical.DOPAMINE)
        engine.apply_impulse(ChemicalImpulse(
            Chemical.DOPAMINE, delta=0.2, duration_seconds=0,
            source_id="goal_scored", source_label="Goal"
        ))
        after = engine.state.get(Chemical.DOPAMINE)
        deltas.append(after - before)
    # Each successive delta should be smaller
    for i in range(1, len(deltas)):
        assert deltas[i] < deltas[i - 1]
```

---

### 5. LLM Interpreter Tests

The interpreter is the most critical layer to test well, since it sits between raw events and the chemical engine. Tests are split into three tiers: no LLM needed, mocked LLM, and live LLM.

#### a) Validator tests (no LLM, no network)

Test that the validation layer catches bad LLM output.

```python
# test_interpreter/test_validator.py

def test_rejects_invalid_chemical_name():
    raw = [{"chemical": "unobtanium", "delta": 0.2, "duration_seconds": 0,
            "source_id": "x", "source_label": "x"}]
    result = ImpulseValidator.validate(raw)
    assert result == []  # silently dropped

def test_clamps_excessive_delta():
    raw = [{"chemical": "dopamine", "delta": 5.0, "duration_seconds": 0,
            "source_id": "x", "source_label": "x"}]
    result = ImpulseValidator.validate(raw)
    assert result[0].delta == 0.5  # clamped to max

def test_clamps_negative_delta():
    raw = [{"chemical": "cortisol", "delta": -3.0, "duration_seconds": 0,
            "source_id": "x", "source_label": "x"}]
    result = ImpulseValidator.validate(raw)
    assert result[0].delta == -0.5

def test_rejects_too_many_impulses():
    raw = [{"chemical": "dopamine", "delta": 0.1, "duration_seconds": 0,
            "source_id": "x", "source_label": "x"}] * 20
    result = ImpulseValidator.validate(raw)
    assert len(result) <= 8

def test_rejects_malformed_json():
    result = ImpulseValidator.validate_raw("this is not json")
    assert result == []
```

#### b) Cache tests (no LLM, no network)

```python
# test_interpreter/test_impulse_cache.py

def test_cache_hit_returns_cached_impulses():
    cache = ImpulseCache(max_size=100, ttl_seconds=3600)
    impulses = [ChemicalImpulse(Chemical.DOPAMINE, 0.2, 0, "x", "x")]
    cache.put("sports:goal:home_team_scored", impulses)
    assert cache.get("sports:goal:home_team_scored") == impulses

def test_cache_miss_returns_none():
    cache = ImpulseCache(max_size=100, ttl_seconds=3600)
    assert cache.get("never_seen_event") is None

def test_cache_expires_after_ttl(manual_clock):
    cache = ImpulseCache(max_size=100, ttl_seconds=60, clock=manual_clock)
    cache.put("key", [some_impulse])
    manual_clock.advance(seconds=61)
    assert cache.get("key") is None

def test_cache_evicts_lru_when_full():
    cache = ImpulseCache(max_size=2, ttl_seconds=3600)
    cache.put("a", [impulse_a])
    cache.put("b", [impulse_b])
    cache.put("c", [impulse_c])  # evicts "a"
    assert cache.get("a") is None
    assert cache.get("b") is not None
```

#### c) Prompt builder tests (no LLM, no network)

```python
# test_interpreter/test_prompt_builder.py

def test_prompt_includes_event_summary():
    event = UserText(source="sports", event_type="goal",
                          summary="BOS scored, leads 3-2", ...)
    context = RobotContext(personality_name="cheerful", affinity=1.5, ...)
    prompt = PromptBuilder.build_user_prompt(event, context)
    assert "BOS scored, leads 3-2" in prompt

def test_prompt_includes_personality():
    context = RobotContext(personality_name="stoic", ...)
    prompt = PromptBuilder.build_user_prompt(some_event, context)
    assert "stoic" in prompt

def test_system_prompt_lists_all_chemicals():
    system = PromptBuilder.build_system_prompt()
    for chem in Chemical:
        assert chem.value.lower() in system.lower()
```

#### d) Full interpreter with mocked LLM (no network)

```python
# test_interpreter/test_llm_interpreter.py

def test_interpreter_returns_impulses_for_goal():
    """Mock the LLM to return a known response, verify the full pipeline."""
    mock_llm = MockLLMClient(response=[
        {"chemical": "dopamine", "delta": 0.25, "duration_seconds": 0,
         "source_id": "goal", "source_label": "Goal scored"},
        {"chemical": "adrenaline", "delta": 0.3, "duration_seconds": 10,
         "source_id": "goal", "source_label": "Goal scored"},
    ])
    interpreter = LLMInterpreter(llm_client=mock_llm, cache=ImpulseCache(...))
    event = UserText(source="sports", event_type="goal",
                          summary="Home team scored", ...)
    impulses = await interpreter.interpret(event, robot_context)
    assert len(impulses) == 2
    assert impulses[0].chemical == Chemical.DOPAMINE

def test_interpreter_uses_cache_on_second_call():
    mock_llm = MockLLMClient(response=[...])
    interpreter = LLMInterpreter(llm_client=mock_llm, cache=ImpulseCache(...))
    event = UserText(...)
    await interpreter.interpret(event, robot_context)
    await interpreter.interpret(event, robot_context)  # same event
    assert mock_llm.call_count == 1  # only called LLM once

def test_interpreter_falls_back_on_llm_failure():
    mock_llm = MockLLMClient(raises=ConnectionError("API down"))
    interpreter = LLMInterpreter(llm_client=mock_llm, cache=ImpulseCache(...),
                                  fallback=FallbackRules())
    event = UserText(source="sports", event_type="goal", ...)
    impulses = await interpreter.interpret(event, robot_context)
    assert len(impulses) > 0  # got fallback impulses, not empty
```

#### e) Fallback rule tests (no LLM, no network)

```python
# test_interpreter/test_fallback_rules.py

def test_fallback_handles_known_event_types():
    rules = FallbackRules()
    impulses = rules.lookup("sports", "goal")
    assert any(i.chemical == Chemical.DOPAMINE for i in impulses)

def test_fallback_returns_empty_for_unknown_events():
    rules = FallbackRules()
    impulses = rules.lookup("unknown_source", "unknown_type")
    assert impulses == []
```

#### f) Live LLM integration tests (requires API key, slow)

These run against the real Claude API to verify prompt quality and output format.

```python
# test_llm_integration.py

@pytest.mark.llm
@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="No API key")
async def test_llm_interprets_hockey_goal():
    interpreter = LLMInterpreter(llm_client=RealLLMClient(), ...)
    event = UserText(
        source="sports", event_type="goal",
        summary="Boston Bruins score in overtime to win 3-2 against Montreal",
        raw_data={}, urgency="realtime"
    )
    impulses = await interpreter.interpret(event, cheerful_robot_context)
    chemicals = {i.chemical for i in impulses}
    # The LLM should reasonably produce at least dopamine and adrenaline
    assert Chemical.DOPAMINE in chemicals
    # All deltas should be within valid range
    for imp in impulses:
        assert -0.5 <= imp.delta <= 0.5

@pytest.mark.llm
async def test_llm_handles_ambiguous_event():
    """Verify the LLM doesn't crash on weird/edge-case events."""
    interpreter = LLMInterpreter(llm_client=RealLLMClient(), ...)
    event = UserText(
        source="news", event_type="headline",
        summary="Scientists discover new species of deep-sea fish",
        raw_data={}, urgency="background"
    )
    impulses = await interpreter.interpret(event, default_robot_context)
    # Should return valid impulses (possibly mild curiosity/dopamine)
    for imp in impulses:
        assert imp.chemical in Chemical
        assert -0.5 <= imp.delta <= 0.5
```

**What this catches:** Prompt regressions (LLM starts returning unexpected formats), API changes, validation gaps, cache logic errors, fallback coverage holes.

---

### 6. LLM Backend Tests

The two real backends (`AnthropicBackend`, `OpenAICompatBackend`) are thin protocol adapters. The OpenAI-compatible one is tested offline by monkeypatching `httpx.AsyncClient.post`:

```python
# test_interpreter/test_openai_backend.py

async def test_call_posts_chat_completion(monkeypatch):
    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    backend = OpenAICompatBackend(base_url="http://localhost:11434/v1",
                                  model="llama3.1")
    result = await backend.call("system text", "user text")
    assert captured["url"].endswith("/chat/completions")
    assert captured["payload"]["messages"][0]["role"] == "system"
```

**What this catches:** protocol drift (wrong endpoint, missing system message, auth header slips), env-var configuration regressions.

---

### 7. Scenario Tests (Full Pipeline Integration)

Full pipeline tests using `ImpulseFactory` (for engine-level) and `MockLLMClient` (for full-pipeline) to simulate real-world sequences.

**Key distinction:**
- `ImpulseFactory` — a test helper in `conftest.py` that returns `ChemicalImpulse` lists for common scenarios. Used for engine-level tests that bypass the interpreter.
- `MockLLMBackend` — a queueable fake LLM used in full-pipeline tests (`UserText` → interpreter → engine).

```python
# conftest.py — shared test helpers

class ImpulseFactory:
    """Convenience factory for common impulse patterns in engine-level tests."""
    @staticmethod
    def presence_nearby():
        return [ChemicalImpulse(Chemical.OXYTOCIN, delta=0.3, duration_seconds=300)]
    @staticmethod
    def weather_sunny():
        return [ChemicalImpulse(Chemical.SEROTONIN, delta=0.15)]
    @staticmethod
    def market_up(percent=1.0):
        return [ChemicalImpulse(Chemical.DOPAMINE, delta=0.1 + percent * 0.05)]
    @staticmethod
    def sports_goal(team="home"):
        return [ChemicalImpulse(Chemical.DOPAMINE, delta=0.25),
                ChemicalImpulse(Chemical.ADRENALINE, delta=0.35)]
    @staticmethod
    def market_crash(percent=5.0):
        return [ChemicalImpulse(Chemical.CORTISOL, delta=min(0.1 + percent * 0.05, 0.5)),
                ChemicalImpulse(Chemical.ADRENALINE, delta=0.25),
                ChemicalImpulse(Chemical.DOPAMINE, delta=-0.2)]
    @staticmethod
    def weather_storm():
        return [ChemicalImpulse(Chemical.CORTISOL, delta=0.15),
                ChemicalImpulse(Chemical.ADRENALINE, delta=0.1)]
```

The factory names (`weather_sunny`, `sports_goal`, `market_crash`, …)
are just descriptive labels for impulse recipes — there are no weather
or sports *event types* in the system anymore. The only real input is
a freeform paragraph (`UserText`).

```python
# test_integration.py

def test_couch_scenario_engine_level():
    """
    Robot is sitting with owner, watching hockey, nice weather, market up.
    Should end up in a very positive emotional state.
    Uses direct impulse injection (no LLM in the loop).
    """
    clock = ManualClock()
    robot = Robot(engine=NeurochemicalEngine(clock=clock))

    # Owner sits down — sustained oxytocin
    robot.receive_impulses(ImpulseFactory.presence_nearby())
    clock.advance(minutes=5)

    # Nice weather in background
    robot.receive_impulses(ImpulseFactory.weather_sunny())
    clock.advance(minutes=10)

    # Market is up
    robot.receive_impulses(ImpulseFactory.market_up(percent=1.2))
    clock.advance(minutes=2)

    # Goal scored!
    robot.receive_impulses(ImpulseFactory.sports_goal(team="home"))

    emotions = robot.current_emotions()
    assert emotions.happiness > emotions.anxiety
    assert emotions.bonding > 0.3
    assert emotions.anxiety < 0.2

async def test_couch_scenario_full_pipeline():
    """
    The same idea through the full pipeline:
    UserText (freeform paragraph) → MockLLMBackend → Engine → EmotionProjection.
    Verifies the layers integrate correctly.
    """
    backend = MockLLMBackend()
    backend.enqueue_impulses([
        {"chemical": "oxytocin", "delta": 0.3, "duration_seconds": 300},
        {"chemical": "dopamine", "delta": 0.25},
        {"chemical": "adrenaline", "delta": 0.35},
    ])

    clock = ManualClock()
    robot = Robot(engine=NeurochemicalEngine(clock=clock), llm_backend=backend)

    await robot.process_event(UserText(
        summary="My owner sat down next to me, the home team just "
                "scored, and it's a beautiful afternoon."
    ))

    emotions = robot.current_emotions()
    assert emotions.happiness > emotions.anxiety

def test_bad_day_scenario():
    """Market crash, bad weather, alone. Should feel stressed."""
    clock = ManualClock()
    robot = Robot(engine=NeurochemicalEngine(clock=clock))

    robot.receive_impulses(ImpulseFactory.market_crash(percent=5.0))
    robot.receive_impulses(ImpulseFactory.weather_storm())
    clock.advance(hours=2)

    emotions = robot.current_emotions()
    assert emotions.anxiety > emotions.happiness
    assert emotions.calm < 0.3

def test_mood_recovery():
    """After a stressful event, the robot should gradually return to neutral."""
    clock = ManualClock()
    robot = Robot(engine=NeurochemicalEngine(clock=clock))

    robot.receive_impulses(ImpulseFactory.market_crash(percent=5.0))
    stressed_cortisol = robot.current_chemicals().get(Chemical.CORTISOL)

    # Let time pass with no new events
    clock.advance(hours=4)

    recovered_cortisol = robot.current_chemicals().get(Chemical.CORTISOL)
    assert recovered_cortisol < stressed_cortisol
    assert robot.current_emotions().anxiety < 0.3

def test_personality_affects_reaction():
    """A 'stoic' robot and an 'anxious' robot react differently to the same event."""
    clock = ManualClock()
    stoic_seed = SeedChemistry.from_dict(PERSONALITY_PRESETS["stoic"])
    anxious_seed = SeedChemistry.from_dict(PERSONALITY_PRESETS["anxious"])

    stoic = Robot(engine=NeurochemicalEngine(clock=clock, seed=stoic_seed), personality="stoic")
    anxious = Robot(engine=NeurochemicalEngine(clock=clock, seed=anxious_seed), personality="anxious")

    impulses = ImpulseFactory.market_crash(percent=3.0)
    stoic.receive_impulses(impulses)
    anxious.receive_impulses(impulses)

    assert anxious.current_emotions().anxiety > stoic.current_emotions().anxiety
```

---

### 8. Seed Chemistry Tests

Test that baseline configuration correctly shapes resting state and dynamic behavior.

```python
# test_seed_chemistry.py

def test_species_defaults_produce_expected_baselines():
    """SeedChemistry.from_species_defaults() matches the documented table."""
    seed = SeedChemistry.from_species_defaults()
    assert seed.baselines[Chemical.DOPAMINE] == 0.3
    assert seed.baselines[Chemical.SEROTONIN] == 0.5
    assert seed.baselines[Chemical.GABA] == 0.4
    assert len(seed.baselines) == 8

def test_partial_override_keeps_other_defaults():
    """Overriding 2 chemicals should leave the other 6 at species defaults."""
    seed = SeedChemistry.from_dict({"baselines": {"dopamine": 0.5, "cortisol": 0.1}})
    assert seed.baselines[Chemical.DOPAMINE] == 0.5
    assert seed.baselines[Chemical.CORTISOL] == 0.1
    assert seed.baselines[Chemical.SEROTONIN] == 0.5  # untouched default

def test_seed_determines_resting_emotions():
    """Two seeds with different baselines should produce different resting emotions."""
    clock = ManualClock()
    cheerful_seed = SeedChemistry.from_dict({
        "baselines": {"serotonin": 0.6, "dopamine": 0.4}
    })
    default_seed = SeedChemistry.from_species_defaults()

    cheerful = Robot(engine=NeurochemicalEngine(clock=clock, seed=cheerful_seed))
    default = Robot(engine=NeurochemicalEngine(clock=clock, seed=default_seed))

    assert cheerful.current_emotions().happiness > default.current_emotions().happiness

def test_half_life_multiplier_changes_decay_speed():
    """A robot with faster adrenaline decay should lose excitement quicker."""
    clock = ManualClock()
    fast_decay = SeedChemistry.from_dict({
        "half_life_multipliers": {"adrenaline": 0.5}  # half the half-life
    })
    normal = SeedChemistry.from_species_defaults()

    fast_bot = Robot(engine=NeurochemicalEngine(clock=clock, seed=fast_decay))
    norm_bot = Robot(engine=NeurochemicalEngine(clock=clock, seed=normal))

    impulse = [ChemicalImpulse(Chemical.ADRENALINE, delta=0.5)]
    fast_bot.receive_impulses(impulse)
    norm_bot.receive_impulses(impulse)

    clock.advance(seconds=180)  # one normal half-life

    # Fast-decay robot should have lost more adrenaline
    assert fast_bot.current_chemicals().get(Chemical.ADRENALINE) < \
           norm_bot.current_chemicals().get(Chemical.ADRENALINE)

def test_interaction_scale_amplifies_cross_chemical_effects():
    """Higher interaction_scale should amplify cross-chemical interactions."""
    clock = ManualClock()
    amplified = SeedChemistry.from_dict({"interaction_scale": 1.5})
    normal = SeedChemistry.from_species_defaults()

    amp_bot = Robot(engine=NeurochemicalEngine(clock=clock, seed=amplified))
    norm_bot = Robot(engine=NeurochemicalEngine(clock=clock, seed=normal))

    # Spike cortisol — should suppress serotonin via interaction
    impulse = [ChemicalImpulse(Chemical.CORTISOL, delta=0.5)]
    amp_bot.receive_impulses(impulse)
    norm_bot.receive_impulses(impulse)

    clock.advance(seconds=60)

    # Amplified robot's serotonin should be more suppressed
    assert amp_bot.current_chemicals().get(Chemical.SEROTONIN) < \
           norm_bot.current_chemicals().get(Chemical.SEROTONIN)

def test_random_seed_stays_in_valid_range():
    """Randomly generated seed chemistry should always produce valid baselines."""
    import random
    for _ in range(100):
        seed = SeedChemistry.from_dict({
            "baselines": {
                chem.value: round(random.uniform(0.1, 0.7), 2)
                for chem in Chemical
            },
            "interaction_scale": round(random.uniform(0.7, 1.3), 2),
        })
        for chem in Chemical:
            assert 0.0 <= seed.baselines[chem] <= 1.0
        engine = NeurochemicalEngine(clock=ManualClock(), seed=seed)
        engine.advance(dt=3600.0)  # 1 hour — nothing should explode
        for chem in Chemical:
            assert 0.0 <= engine.state.get(chem) <= 1.0

def test_seed_persists_through_serialization():
    """Seed chemistry should survive a round-trip save/load."""
    seed = SeedChemistry.from_dict({
        "baselines": {"dopamine": 0.5, "cortisol": 0.1},
        "half_life_multipliers": {"adrenaline": 0.7},
        "interaction_scale": 1.2,
    })
    json_data = seed.to_dict()
    restored = SeedChemistry.from_dict(json_data)
    assert restored.baselines[Chemical.DOPAMINE] == 0.5
    assert restored.half_life_multipliers[Chemical.ADRENALINE] == 0.7
    assert restored.interaction_scale == 1.2
```

**What this catches:** Seed override logic errors, half-life multiplier miscalculation, interaction scaling bugs, serialization round-trip failures, invalid random generation.

---

### 9. Property-Based Tests (Hypothesis)

For invariants that must always hold, regardless of inputs.

```python
# test_properties.py
from hypothesis import given, strategies as st

@given(
    levels=st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=8, max_size=8),
    dt=st.floats(min_value=0.01, max_value=3600.0)
)
def test_chemicals_always_stay_in_range(levels, dt):
    """No matter the starting state or time step, levels stay in [0, 1]."""
    engine = NeurochemicalEngine(clock=ManualClock())
    for chem, level in zip(Chemical, levels):
        engine.state.set(chem, level)
    engine.advance(dt=dt)  # uses sub-stepping internally
    for chem in Chemical:
        assert 0.0 <= engine.state.get(chem) <= 1.0

@given(
    levels=st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=8, max_size=8)
)
def test_emotions_always_in_range(levels):
    """Emotion projections never go outside [0, 1]."""
    state = ChemicalState()
    for chem, level in zip(Chemical, levels):
        state.set(chem, level)
    emotions = EmotionProjection.compute(state)
    for value in emotions.as_dict().values():
        assert 0.0 <= value <= 1.0
```

**What this catches:** Edge cases you'd never think to write by hand — extreme combinations, tiny/huge time steps, boundary values.

---

### 10. Event Routing Tests

There is no batching or urgency distinction anymore — `RealtimeRouter` composes cache + LLM + apply into a single call. Tests verify that composition.

```python
# test_event_router.py

async def test_router_applies_interpreted_impulses():
    """The router interprets the paragraph and applies the impulses."""
    applied: list[ChemicalImpulse] = []
    router = RealtimeRouter(
        interpreter=interpreter_with_mock_llm,
        context_fn=lambda: context,
        apply_fn=applied.extend,
    )
    await router.route(UserText(summary="you won the lottery"))
    assert len(applied) > 0

async def test_router_skips_apply_when_no_impulses():
    """Empty interpretation → apply_fn is never called."""
    await router.route(UserText(summary="nothing happened"))
    assert applied == []
```

**What this catches:** Composition errors between cache, interpreter, and engine apply.

---

### 11. Expression Layer Tests

Test that `TextExpressionOutput` produces readable text from emotion vectors and chemical state. The `express()` method receives both `EmotionVector` and `ChemicalState` (chemicals drive posture/engagement rules per the architecture).

```python
# test_expression.py

@pytest.fixture
def expression():
    return TextExpressionOutput()

def make_chemicals(**overrides):
    """Helper: create ChemicalState with overrides from baseline."""
    state = ChemicalState()
    for name, val in overrides.items():
        state.set(Chemical[name.upper()], val)
    return state

async def test_happy_expression(expression):
    """High happiness + excitement should produce positive text."""
    emotions = EmotionVector(happiness=0.8, excitement=0.6, calm=0.3,
                             bonding=0.4, sadness=0.0, anxiety=0.0,
                             anger=0.0, euphoria=0.5)
    chemicals = make_chemicals(dopamine=0.9, serotonin=0.8, adrenaline=0.6)
    text = await expression.express(emotions, chemicals)
    assert "happy" in text.lower() or "excited" in text.lower()
    assert "leaning forward" in text.lower()  # adrenaline > 0.5 and dopamine > 0.4

async def test_anxious_expression(expression):
    """High anxiety + low calm should produce stressed text."""
    emotions = EmotionVector(happiness=0.1, excitement=0.2, calm=0.05,
                             bonding=0.1, sadness=0.2, anxiety=0.8,
                             anger=0.3, euphoria=0.0)
    chemicals = make_chemicals(cortisol=0.8, adrenaline=0.5, gaba=0.1)
    text = await expression.express(emotions, chemicals)
    assert "anxious" in text.lower() or "stressed" in text.lower()
    assert "tense" in text.lower()  # cortisol > 0.5 and gaba < 0.3

async def test_neutral_expression(expression):
    """At baseline, expression should be calm/neutral."""
    emotions = EmotionVector(happiness=0.3, excitement=0.1, calm=0.4,
                             bonding=0.3, sadness=0.05, anxiety=0.05,
                             anger=0.05, euphoria=0.1)
    chemicals = make_chemicals()  # all at baseline
    text = await expression.express(emotions, chemicals)
    assert "calm" in text.lower() or "relaxed" in text.lower() or "content" in text.lower()

async def test_dominant_emotion_comes_first(expression):
    """The strongest emotion should appear first in the description."""
    emotions = EmotionVector(happiness=0.1, excitement=0.1, calm=0.1,
                             bonding=0.9, sadness=0.0, anxiety=0.0,
                             anger=0.0, euphoria=0.0)
    chemicals = make_chemicals(oxytocin=0.9)
    text = await expression.express(emotions, chemicals)
    assert "bond" in text.lower() or "connect" in text.lower() or "affection" in text.lower()

async def test_mixed_emotions_both_present(expression):
    """When two strong conflicting emotions exist, both should be mentioned."""
    emotions = EmotionVector(happiness=0.7, excitement=0.5, calm=0.1,
                             bonding=0.2, sadness=0.1, anxiety=0.6,
                             anger=0.1, euphoria=0.3)
    chemicals = make_chemicals(dopamine=0.7, cortisol=0.6, adrenaline=0.5)
    text = await expression.express(emotions, chemicals)
    has_positive = any(w in text.lower() for w in ["happy", "excited", "joy"])
    has_negative = any(w in text.lower() for w in ["anxious", "nervous", "tense"])
    assert has_positive and has_negative
```

**What this catches:** Expression regressions, missing emotions in output, incorrect dominance ordering, posture/engagement rule failures.

---

### 12. Sustained-Duration Impulse Tests

Test that impulses with `duration_seconds > 0` apply their effect gradually over time.

```python
# test_sustained_impulses.py

def test_sustained_impulse_applies_over_time():
    """A 300-second oxytocin impulse should apply gradually, not all at once."""
    clock = ManualClock()
    engine = NeurochemicalEngine(clock=clock)
    initial = engine.state.get(Chemical.OXYTOCIN)

    engine.apply_impulse(ChemicalImpulse(
        Chemical.OXYTOCIN, delta=0.3, duration_seconds=300))

    # Immediately after: should NOT have the full delta applied
    just_after = engine.state.get(Chemical.OXYTOCIN)
    assert just_after < initial + 0.3

    # After full duration: cumulative effect should approach the full delta
    engine.advance(dt=300.0)
    after_full = engine.state.get(Chemical.OXYTOCIN)
    assert after_full > initial + 0.1  # significant effect occurred

def test_sustained_impulse_interrupted_by_decay():
    """Decay still operates during a sustained impulse — net effect may be less than delta."""
    clock = ManualClock()
    engine = NeurochemicalEngine(clock=clock)
    engine.apply_impulse(ChemicalImpulse(
        Chemical.DOPAMINE, delta=0.3, duration_seconds=600))
    engine.advance(dt=600.0)
    # Decay fights the sustained impulse, so net effect < full delta
    assert engine.state.get(Chemical.DOPAMINE) < engine.state.baseline(Chemical.DOPAMINE) + 0.3

def test_zero_duration_impulse_is_instant():
    """An impulse with duration_seconds=0 should apply all at once."""
    clock = ManualClock()
    engine = NeurochemicalEngine(clock=clock)
    before = engine.state.get(Chemical.ADRENALINE)
    engine.apply_impulse(ChemicalImpulse(Chemical.ADRENALINE, delta=0.3, duration_seconds=0))
    after = engine.state.get(Chemical.ADRENALINE)
    assert abs((after - before) - 0.3) < 0.01
```

**What this catches:** Sustained impulse timing errors, instant vs gradual application bugs, decay interaction with ongoing impulses.

---

### 13. Persistence Tests

```python
# test_persistence.py

def test_save_and_restore():
    """Chemical state survives a round-trip through serialization."""
    state = ChemicalState()
    state.set(Chemical.DOPAMINE, 0.75)
    state.set(Chemical.CORTISOL, 0.6)

    json_data = StateStore.serialize(state)
    restored = StateStore.deserialize(json_data)

    for chem in Chemical:
        assert abs(state.get(chem) - restored.get(chem)) < 1e-6

def test_baseline_drift_persists():
    """If cortisol baseline has drifted, that drift should survive save/load."""
    state = ChemicalState()
    state.set_baseline(Chemical.CORTISOL, 0.35)  # drifted from default 0.2

    json_data = StateStore.serialize(state)
    restored = StateStore.deserialize(json_data)

    assert abs(restored.baseline(Chemical.CORTISOL) - 0.35) < 1e-6
```

---

### 14. Facial Muscle Projection Tests

`FaceProjection` is a second projection from `ChemicalState`, parallel to
`EmotionProjection`. It must satisfy the same shape of invariants:
output values are in `[0, 1]`, baseline state is neutral, targeted
chemical activations produce the expected muscles.

```python
# test_face.py

@settings(max_examples=200, deadline=None)
@given(...)  # 8 chemicals, each in [0, 1]
def test_face_values_in_unit_interval(...):
    face = project_face(state)
    for name, value in face.as_dict().items():
        assert 0.0 <= value <= 1.0

def test_baseline_state_is_neutral():
    face = project_face(ChemicalState())
    assert all(v < 0.40 for v in face.as_dict().values())
    assert face.cheek_raise < 0.30
    assert face.brow_lower < 0.30

def test_intense_joy_activates_smile_muscles():
    state = _state_with(dopamine=1.0, endorphins=1.0, oxytocin=0.7)
    face = project_face(state)
    assert face.cheek_raise > 0.7
    assert face.lip_corner_pull > 0.7
    assert face.lip_corner_depress < 0.10

def test_acute_stress_activates_anger_muscles():
    state = _state_with(cortisol=1.0, adrenaline=0.9, gaba=0.05)
    face = project_face(state)
    assert face.brow_lower > 0.6
    assert face.eyelid_upper_raise > 0.7
    assert face.lip_press > 0.4
```

`test_full_pipeline.py::test_text_to_face_payload_chain` locks the whole
chain together — text → MockLLM → impulses → `ChemicalState` →
`FaceState` → renderer payload — asserting that joyful text moves the
smile muscles and that the payload carries exactly the 12 muscles the
JS consumes.

The companion `test_face_3d.py` checks the Python side of the LED face:

- `face_payload(face)` emits all 12 muscles, clamped to `[0, 1]`, and
  a mood accent (color + intensity).
- `payload_js(...)` embeds valid JSON in the `setTargets(...)` call.
- `face3d.js` exists, exposes `window.kindaliveFace.setTargets`, and
  references every one of the 12 muscle names — guards against a
  muscle being silently ignored by the renderer.
- the renderer is pure 2D canvas (no WebGL / Three.js dependency).

**What this catches:** projection regressions when chemical weights are
retuned; Python↔JS contract drift; the "creepy permanent grin at rest"
failure mode.

---

## Test Execution

### Running tests

```bash
# All unit tests (fast, no API keys needed, no LLM calls)
pytest tests/ -m "not integration and not llm"

# Specific layer
pytest tests/test_chemicals.py
pytest tests/test_emotion_projection.py
pytest tests/test_interpreter/

# Full pipeline scenarios (uses MockLLM, still fast)
pytest tests/test_integration.py

# Live LLM integration tests (requires ANTHROPIC_API_KEY)
ANTHROPIC_API_KEY=xxx pytest tests/ -m llm

# Property-based tests (slower, more thorough)
pytest tests/test_properties.py --hypothesis-seed=random

# Everything with coverage
pytest tests/ --cov=kindalive --cov-report=term-missing
```

### CI pipeline

```
1. Lint (ruff)
2. Type check (mypy)
3. Unit tests (pytest -m "not integration and not llm")
4. Property tests (pytest tests/test_properties.py)
5. Coverage gate (>= 80%)
```

Live LLM integration tests (and the LLM benchmark) run on a separate schedule since they hit the API and cost money.

---

## Visual Debugging

During development, the web dashboard (`python3 -m
kindalive.expression.web_ui`, see [web-ui.md](web-ui.md)) is the live
debugger: it shows every chemical level as a bar, the full emotion mix,
the dominant emotion under the face, and the interpreter status label
(`LLM` / `CACHE` / `FALLBACK`). Conceptually it renders:

```
╔══════════════════════════════════════════════╗
║  KINDALIVE — Chemical State                  ║
╠══════════════════════════════════════════════╣
║  Dopamine    ████████░░░░  0.67              ║
║  Serotonin   ██████░░░░░░  0.52              ║
║  Oxytocin    █████████░░░  0.74              ║
║  Testosterone ███░░░░░░░░░  0.28             ║
║  Cortisol    ██░░░░░░░░░░  0.15              ║
║  Adrenaline  ████████████  0.95  ← SPIKE     ║
║  Endorphins  █████░░░░░░░  0.41              ║
║  GABA        ████░░░░░░░░  0.33              ║
╠══════════════════════════════════════════════╣
║  Dominant: EXCITEMENT (0.82)                 ║
║  Mood: Happy + Excited + Bonding             ║
╚══════════════════════════════════════════════╝
```

For headless debugging there is also the one-shot CLI
(`python3 -m kindalive.main --text "..."`), which prints the impulses
the LLM returned and the resulting emotion snapshot.

---

## Build Order (Test-First)

The implementation order is designed so that every step can be tested before moving to the next.

**Status: all steps complete, including the strip-and-pivot (freeform text only) and the LED-face pivot. 181 unit tests passing.**

| Step | Build | Test with | Status |
|------|-------|-----------|--------|
| 1 | `ChemicalState` + decay | Unit tests: decay math, clamping, half-life accuracy | Done |
| 2 | `SeedChemistry` + baseline config | Seed tests: species defaults, partial overrides, half-life multipliers | Done |
| 3 | `ChemicalImpulse` + apply (incl. sustained) | Unit tests: impulse application, saturation, duration | Done |
| 4 | Cross-chemical interactions (with `interaction_scale`) | Unit tests: interaction effects, stability, baseline drift, scaling | Done |
| 5 | `NeurochemicalEngine` (tick loop + seed) | Unit tests with `ManualClock`, property tests | Done |
| 6 | `EmotionProjection` | Unit tests: known chemical states → expected emotions | Done |
| 7 | `Robot` class + `ImpulseFactory` | Engine-level scenario tests: couch, bad day, recovery | Done |
| 8 | Personality presets + custom seeds | Seed chemistry tests: personality comparison, random seeding | Done |
| 9 | `TextExpressionOutput` (expression layer) | Expression tests: dominant emotion, mixed emotions, neutral | Done |
| 10 | `RealtimeRouter` | Routing tests: cache + LLM + apply composition | Done |
| 11 | `ImpulseValidator` | Validator unit tests: clamping, rejection, edge cases | Done |
| 12 | `ImpulseCache` | Cache unit tests: hit/miss, TTL, eviction | Done |
| 13 | `FallbackRules` | Fallback unit tests: known event types, unknowns | Done |
| 14 | `PromptBuilder` | Prompt unit tests: all fields present, all chemicals listed | Done |
| 15 | `LLMInterpreter` (with MockLLM) | Full interpreter tests: pipeline, cache usage, fallback | Done |
| 16 | Full pipeline scenario tests | UserText → MockLLM → Router → Engine → Expression | Done |
| 17 | Persistence (incl. seed chemistry) | Round-trip serialization tests for state + seed | Done |
| 18 | Live LLM integration tests | Real Claude API calls with known paragraphs | Done |
| 19 | LLM benchmark (30 scenarios) | Scorecard: >90% PASS rate required | Done |
| 20 | LLM backends | `AnthropicBackend` (live-gated) + `OpenAICompatBackend` (`test_openai_backend.py`, offline) | Done |
| 21 | Web dashboard (the only UI) | NiceGUI app at `kindalive/expression/web_ui.py`; `.env` auto-loader; `tests/test_web_ui.py` + `tests/test_env_loader.py` | Done |
| 22 | Face projection + LED face | 12-muscle `FaceProjection` (`test_face.py`); LED dot-matrix payload/wiring + lip-sync (`test_face_3d.py`); visual check in the browser | Done |
