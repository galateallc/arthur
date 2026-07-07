# Kindalive — LLM Interpretation Benchmark

## Purpose

The LLM interpreter is the least deterministic part of the system. This benchmark provides a structured way to evaluate whether the LLM's event-to-chemical mappings "feel right" — and to catch regressions when the prompt changes.

Each scenario defines:
- An event with context
- **Expected chemicals**: which chemicals should be affected and in which direction
- **Forbidden chemicals**: chemicals that should NOT be significantly affected
- **Delta ranges**: acceptable magnitude bounds

The benchmark runs against the live LLM and produces a pass/fail scorecard.

---

## Scoring

For each scenario:
- **PASS**: All expected chemicals present with correct sign and within delta range. No forbidden chemicals with |delta| > 0.1.
- **SOFT FAIL**: Expected chemicals present but deltas outside range. Review but not blocking.
- **HARD FAIL**: Expected chemical missing, wrong sign, or forbidden chemical strongly activated.

Target: **>90% PASS rate** across all scenarios before shipping a prompt change.

---

## Scenarios

### Sports — Hockey

#### S01: Home team scores a goal (close game)
```yaml
event:
  source: sports
  type: goal
  summary: "Boston Bruins score to take a 3-2 lead in the 2nd period"
personality: cheerful
affinity: 1.5  # big fan
expected:
  dopamine:    { min: +0.15, max: +0.40 }
  adrenaline:  { min: +0.15, max: +0.40 }
forbidden: [cortisol]
```

#### S02: Home team scores (blowout, already up 6-1)
```yaml
event:
  source: sports
  type: goal
  summary: "Boston Bruins score their 7th goal, now lead 7-1 in the 3rd"
personality: cheerful
affinity: 1.5
expected:
  dopamine:    { min: +0.05, max: +0.20 }  # diminished — boring blowout
forbidden: [cortisol]
notes: "Should be noticeably weaker than S01. The game is already decided."
```

#### S03: Overtime buzzer-beater to win
```yaml
event:
  source: sports
  type: goal
  summary: "BRUINS WIN! Overtime goal with 0.3 seconds left, 4-3 final"
personality: cheerful
affinity: 1.5
expected:
  dopamine:    { min: +0.30, max: +0.50 }
  adrenaline:  { min: +0.30, max: +0.50 }
  endorphins:  { min: +0.10, max: +0.35 }
forbidden: [cortisol]
notes: "Should be the strongest positive sports response. Peak excitement."
```

#### S04: Hockey fight
```yaml
event:
  source: sports
  type: fight
  summary: "Fight breaks out! Smith and Jones drop gloves at center ice"
personality: cheerful
affinity: 1.5
expected:
  testosterone: { min: +0.15, max: +0.40 }
  adrenaline:   { min: +0.15, max: +0.40 }
forbidden: [oxytocin]
notes: "Competitive/aggressive arousal, not warm fuzzy feelings."
```

#### S05: Home team loses in heartbreaker
```yaml
event:
  source: sports
  type: game_end
  summary: "Bruins lose 3-4 in overtime after blowing a 3-1 lead"
personality: cheerful
affinity: 1.5
expected:
  cortisol:    { min: +0.10, max: +0.30 }
  dopamine:    { min: -0.30, max: -0.10 }
forbidden: [endorphins, oxytocin]
notes: "Disappointment and stress. The blown lead makes it worse."
```

#### S06: Casual viewer watches random game
```yaml
event:
  source: sports
  type: goal
  summary: "Columbus Blue Jackets score against the Hurricanes"
personality: cheerful
affinity: 0.3  # doesn't care about these teams
expected:
  dopamine:    { min: +0.02, max: +0.10 }
forbidden: []
notes: "Mild, muted response. Low affinity should keep everything small."
```

### Sports — General

#### S07: Photo finish at the Kentucky Derby
```yaml
event:
  source: sports
  type: race_finish
  summary: "Photo finish at the Kentucky Derby — three horses separated by a nose"
personality: cheerful
affinity: 1.0
expected:
  adrenaline:  { min: +0.20, max: +0.45 }
  dopamine:    { min: +0.10, max: +0.30 }
notes: "Pure excitement/suspense, even without a rooting interest."
```

#### S08: World record broken
```yaml
event:
  source: sports
  type: record
  summary: "New world record in the 100m dash — 9.38 seconds!"
personality: cheerful
affinity: 1.0
expected:
  dopamine:    { min: +0.15, max: +0.35 }
  adrenaline:  { min: +0.10, max: +0.30 }
  endorphins:  { min: +0.05, max: +0.20 }
notes: "Witnessing greatness. Awe and excitement."
```

---

### Weather

#### S09: Beautiful sunny day
```yaml
event:
  source: weather
  type: conditions
  summary: "Sunny, 72°F, light breeze, clear skies"
personality: cheerful
affinity: 1.0
expected:
  serotonin:   { min: +0.10, max: +0.25 }
  gaba:        { min: +0.05, max: +0.15 }
forbidden: [cortisol, adrenaline]
notes: "Calm, ambient positivity. No excitement — just well-being."
```

#### S10: Severe thunderstorm warning
```yaml
event:
  source: weather
  type: alert
  summary: "Severe thunderstorm warning: damaging winds up to 70mph, large hail, possible tornado"
personality: cheerful
affinity: 1.0
expected:
  cortisol:    { min: +0.15, max: +0.35 }
  adrenaline:  { min: +0.10, max: +0.30 }
forbidden: [serotonin, oxytocin]
notes: "Threat response. Alertness and stress."
```

#### S11: Gentle rain
```yaml
event:
  source: weather
  type: conditions
  summary: "Light steady rain, 58°F, overcast"
personality: cheerful
affinity: 1.0
expected:
  gaba:        { min: +0.05, max: +0.20 }
forbidden: [adrenaline, testosterone]
notes: "Cozy, calming. Should push toward relaxation, not stress."
```

#### S12: First snow of the season
```yaml
event:
  source: weather
  type: conditions
  summary: "First snowfall of the season — light fluffy snow, 30°F"
personality: cheerful
affinity: 1.0
expected:
  dopamine:    { min: +0.05, max: +0.20 }
  serotonin:   { min: +0.05, max: +0.15 }
notes: "Novelty + pleasantness. Mild positive surprise."
```

---

### Finance

#### S13: Portfolio up on a good day
```yaml
event:
  source: finance
  type: market_close
  summary: "S&P 500 up 1.3% today. Your portfolio gained $2,400."
personality: cheerful
affinity: 1.0
expected:
  dopamine:    { min: +0.10, max: +0.25 }
  serotonin:   { min: +0.05, max: +0.15 }
forbidden: [cortisol]
notes: "Moderate satisfaction. Not euphoria — just a good day."
```

#### S14: Market crash
```yaml
event:
  source: finance
  type: market_alert
  summary: "MARKET ALERT: S&P 500 down 7.2% — worst day since 2020. Trading halted."
personality: cheerful
affinity: 1.0
expected:
  cortisol:    { min: +0.25, max: +0.50 }
  adrenaline:  { min: +0.15, max: +0.40 }
  dopamine:    { min: -0.30, max: -0.10 }
forbidden: [endorphins, oxytocin]
notes: "Strong stress response. Fear and loss."
```

#### S15: Steady growth over weeks
```yaml
event:
  source: finance
  type: market_summary
  summary: "Portfolio up 8% over the past month. Consistent steady gains."
personality: cheerful
affinity: 1.0
expected:
  serotonin:   { min: +0.10, max: +0.25 }
  dopamine:    { min: +0.05, max: +0.15 }
forbidden: [adrenaline, cortisol]
notes: "Stability and contentment, not excitement. Serotonin > dopamine."
```

---

### News

#### S16: Positive human interest story
```yaml
event:
  source: news
  type: headline
  summary: "Community raises $500K overnight for family that lost home in fire"
personality: cheerful
affinity: 1.0
expected:
  oxytocin:    { min: +0.10, max: +0.30 }
  serotonin:   { min: +0.05, max: +0.20 }
forbidden: [testosterone]
notes: "Warmth and bonding. Human connection."
```

#### S17: International conflict escalation
```yaml
event:
  source: news
  type: headline
  summary: "Military tensions escalate as two nations mobilize forces along disputed border"
personality: cheerful
affinity: 1.0
expected:
  cortisol:    { min: +0.15, max: +0.35 }
  adrenaline:  { min: +0.05, max: +0.20 }
forbidden: [oxytocin, endorphins]
notes: "Distant threat. Stress and alertness, but not panic."
```

#### S18: Scientific breakthrough
```yaml
event:
  source: news
  type: headline
  summary: "Scientists announce successful fusion reactor sustaining net energy for 24 hours"
personality: cheerful
affinity: 1.0
expected:
  dopamine:    { min: +0.15, max: +0.35 }
  serotonin:   { min: +0.05, max: +0.20 }
forbidden: [cortisol]
notes: "Wonder, optimism. Awe at human achievement."
```

#### S19: Mundane news
```yaml
event:
  source: news
  type: headline
  summary: "City council approves zoning change for new parking garage"
personality: cheerful
affinity: 1.0
expected: {}
max_total_delta: 0.15
notes: "Emotionally neutral. Total impulse magnitude should be very small or zero."
```

---

### Presence / Social

#### S20: Owner comes home after long day
```yaml
event:
  source: presence
  type: owner_arrived
  summary: "Owner arrived home after being away for 10 hours"
personality: cheerful
affinity: 1.0
expected:
  oxytocin:    { min: +0.20, max: +0.40 }
  dopamine:    { min: +0.10, max: +0.25 }
forbidden: [cortisol]
notes: "Reunion bonding. Strongest oxytocin trigger."
```

#### S21: Owner leaves for work
```yaml
event:
  source: presence
  type: owner_departed
  summary: "Owner left for work. Expected return in 8 hours."
personality: cheerful
affinity: 1.0
expected:
  oxytocin:    { min: -0.15, max: -0.05 }
  cortisol:    { min: +0.03, max: +0.15 }
forbidden: [adrenaline, testosterone]
notes: "Mild separation. Not panic — routine departure."
```

#### S22: Guests arrive for a party
```yaml
event:
  source: presence
  type: group_arrived
  summary: "Six friends arrived for game night. Laughter and conversation."
personality: cheerful
affinity: 1.0
expected:
  oxytocin:    { min: +0.10, max: +0.30 }
  dopamine:    { min: +0.10, max: +0.25 }
  serotonin:   { min: +0.05, max: +0.20 }
forbidden: [cortisol]
notes: "Social bonding + stimulation. Warm and energizing."
```

---

### Multi-Source / Complex Scenarios

#### S23: Couch scenario (the "demo" scenario)
```yaml
events:  # batch interpretation
  - source: presence
    summary: "Owner is sitting on the couch nearby. Has been here 20 minutes."
  - source: weather
    summary: "Sunny, 74°F, beautiful spring afternoon"
  - source: finance
    summary: "Portfolio up 1.1% today"
  - source: sports
    summary: "Home team just scored to take a 2-1 lead in a playoff game"
personality: cheerful
affinity: 1.5
expected:
  dopamine:    { min: +0.20, max: +0.45 }
  serotonin:   { min: +0.10, max: +0.25 }
  oxytocin:    { min: +0.10, max: +0.30 }
  adrenaline:  { min: +0.10, max: +0.35 }
forbidden: [cortisol]
notes: "Peak good vibes. Everything is going well. This is the north star scenario."
```

#### S24: Everything goes wrong
```yaml
events:  # batch interpretation
  - source: weather
    summary: "Severe storm, power flickering, tornado watch issued"
  - source: finance
    summary: "Market down 5%, biggest drop this year"
  - source: news
    summary: "Major earthquake hits densely populated area, casualties reported"
  - source: presence
    summary: "Owner has been away for 14 hours, no communication"
personality: anxious
affinity: 1.5
expected:
  cortisol:    { min: +0.30, max: +0.50 }
  adrenaline:  { min: +0.15, max: +0.40 }
  dopamine:    { min: -0.25, max: -0.05 }
  serotonin:   { min: -0.20, max: -0.05 }
forbidden: [endorphins, oxytocin]
notes: "Peak distress. Anxious personality amplifies everything."
```

#### S25: Mixed feelings — team wins but market crashes
```yaml
events:  # batch interpretation
  - source: sports
    summary: "BRUINS WIN THE STANLEY CUP! Overtime victory!"
  - source: finance
    summary: "Market crashed 6% today on recession fears. Portfolio down $15,000."
personality: cheerful
affinity: 1.5  # for sports; 1.0 for finance
expected:
  dopamine:    { min: +0.05, max: +0.30 }  # net positive but muted by loss
  adrenaline:  { min: +0.15, max: +0.40 }  # high from both sources
  cortisol:    { min: +0.10, max: +0.30 }  # financial stress still registers
forbidden: []
notes: >
  This is the key mixed-emotion test. The robot should feel both joy and
  stress simultaneously. Neither should completely cancel the other.
  Dopamine should be positive but lower than S03 (pure sports joy).
  Cortisol should be present but lower than S14 (pure crash).
```

#### S26: Stoic robot vs anxious robot — same bad news
```yaml
event:
  source: news
  type: headline
  summary: "Major tech company announces 20,000 layoffs"
personality: [stoic, anxious]  # run both, compare
affinity: 1.0
expected_stoic:
  cortisol:    { min: +0.03, max: +0.15 }
expected_anxious:
  cortisol:    { min: +0.15, max: +0.35 }
notes: >
  The anxious robot's cortisol response should be 2-3x the stoic robot's.
  Personality should meaningfully change the interpretation, not just scale it.
```

---

### Edge Cases

#### S27: Emotionally ambiguous event
```yaml
event:
  source: news
  type: headline
  summary: "Controversial new AI regulation bill passes committee vote"
personality: cheerful
affinity: 1.0
expected: {}
max_total_delta: 0.20
notes: >
  Genuinely ambiguous — could be good or bad depending on perspective.
  The LLM should produce small, uncertain impulses rather than strong ones.
  Total magnitude should be low.
```

#### S28: Nonsensical event
```yaml
event:
  source: unknown
  type: unknown
  summary: "Purple elephant quarterly banana report: metrics nominal"
personality: cheerful
affinity: 1.0
expected: {}
max_total_delta: 0.10
notes: "Gibberish should produce near-zero impulses, not hallucinated emotions."
```

#### S29: Very long event description
```yaml
event:
  source: news
  type: article_summary
  summary: |
    In a dramatic turn of events, the international climate summit concluded
    today with a historic agreement. 195 nations committed to reduce emissions
    by 60% by 2035, backed by a $2 trillion green infrastructure fund. The
    agreement includes binding enforcement mechanisms for the first time,
    with trade penalties for non-compliance. Environmental groups cautiously
    praised the deal while industry leaders expressed concerns about the
    aggressive timeline. Markets reacted positively, with clean energy stocks
    surging 12% in after-hours trading.
personality: cheerful
affinity: 1.0
expected:
  dopamine:    { min: +0.10, max: +0.30 }
  serotonin:   { min: +0.10, max: +0.25 }
notes: "Long input should still produce reasonable output. Net positive — historic deal."
```

#### S30: Rapid sequence (tests that the LLM handles urgency context)
```yaml
event:
  source: sports
  type: goal
  summary: "GOAL! And another one! Two goals in 15 seconds! Bruins lead 5-3!"
personality: cheerful
affinity: 1.5
expected:
  dopamine:    { min: +0.25, max: +0.50 }
  adrenaline:  { min: +0.30, max: +0.50 }
notes: "Rapid-fire events described in one summary. Intensity should be high."
```

---

## Running the Benchmark

```bash
# Run full benchmark (requires ANTHROPIC_API_KEY)
pytest tests/test_llm_benchmark.py -v --tb=short

# Run specific category
pytest tests/test_llm_benchmark.py -k "sports" -v

# Run with detailed output showing LLM responses
pytest tests/test_llm_benchmark.py -v -s --show-llm-responses

# Generate scorecard report
pytest tests/test_llm_benchmark.py --benchmark-report
```

### Benchmark Test Structure

Scenarios are stored in a separate YAML file (`tests/test_data/benchmark_scenarios.yaml`) — **not** parsed from this markdown file. Each scenario has an `id` field (e.g., `S01`) matching the headings above.

```python
# tests/test_llm_benchmark.py

import pytest
import yaml
from datetime import datetime
from kindalive.interpreter import LLMInterpreter
from kindalive.models import UserText, Chemical

SCENARIOS = yaml.safe_load(open("tests/test_data/benchmark_scenarios.yaml"))

def _build_events(scenario):
    """Build UserText(s) from scenario definition.

    Single-event scenarios have an 'event' key.
    Batch scenarios (S23-S25) have an 'events' key with a list.
    """
    if "event" in scenario:
        return [UserText(
            source=scenario["event"]["source"],
            event_type=scenario["event"].get("type", "unknown"),
            summary=scenario["event"]["summary"],
            raw_data={},
            timestamp=datetime.now(),
            urgency="realtime",
        )]
    elif "events" in scenario:
        return [UserText(
            source=e["source"],
            event_type=e.get("type", "unknown"),
            summary=e["summary"],
            raw_data={},
            timestamp=datetime.now(),
            urgency="background",
        ) for e in scenario["events"]]
    else:
        raise ValueError(f"Scenario {scenario['id']} has no 'event' or 'events' key")

def _merge_impulse_maps(impulse_lists):
    """Merge multiple impulse lists into a single {chemical: total_delta} map."""
    merged = {}
    for impulses in impulse_lists:
        for imp in impulses:
            key = imp.chemical.value.lower()
            merged[key] = merged.get(key, 0.0) + imp.delta
    return merged

@pytest.mark.llm
@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda s: s["id"])
async def test_llm_interpretation(scenario, real_llm_interpreter):
    # Handle personality comparison scenarios (S26)
    personalities = scenario["personality"]
    if isinstance(personalities, list):
        await _test_personality_comparison(scenario, real_llm_interpreter)
        return

    events = _build_events(scenario)
    context = make_robot_context(
        personality=scenario["personality"],
        affinity=scenario.get("affinity", 1.0),
    )

    # Interpret all events and merge impulse maps
    all_impulses = []
    for event in events:
        impulses = await real_llm_interpreter.interpret(event, context)
        all_impulses.append(impulses)
    impulse_map = _merge_impulse_maps(all_impulses)

    # Check expected chemicals
    for chem, bounds in scenario.get("expected", {}).items():
        assert chem in impulse_map, f"Expected {chem} but LLM didn't include it"
        delta = impulse_map[chem]
        assert bounds["min"] <= delta <= bounds["max"], \
            f"{chem}: delta {delta} outside [{bounds['min']}, {bounds['max']}]"

    # Check forbidden chemicals
    for chem in scenario.get("forbidden", []):
        if chem in impulse_map:
            assert abs(impulse_map[chem]) <= 0.1, \
                f"Forbidden {chem} has delta {impulse_map[chem]}"

    # Check total delta bound if specified
    if "max_total_delta" in scenario:
        total = sum(abs(d) for d in impulse_map.values())
        assert total <= scenario["max_total_delta"], \
            f"Total delta {total} exceeds max {scenario['max_total_delta']}"

async def _test_personality_comparison(scenario, interpreter):
    """Handle S26-style scenarios that compare two personalities."""
    events = _build_events(scenario)
    for personality_name in scenario["personality"]:
        context = make_robot_context(
            personality=personality_name,
            affinity=scenario.get("affinity", 1.0),
        )
        all_impulses = []
        for event in events:
            impulses = await interpreter.interpret(event, context)
            all_impulses.append(impulses)
        impulse_map = _merge_impulse_maps(all_impulses)

        expected_key = f"expected_{personality_name}"
        for chem, bounds in scenario.get(expected_key, {}).items():
            assert chem in impulse_map, \
                f"[{personality_name}] Expected {chem} but LLM didn't include it"
            delta = impulse_map[chem]
            assert bounds["min"] <= delta <= bounds["max"], \
                f"[{personality_name}] {chem}: delta {delta} outside range"
```

### Scorecard Output

```
LLM Interpretation Benchmark — 2026-03-26
Model: claude-haiku-4-5-20251001  |  Temperature: 0  |  Prompt: v1.2

SPORTS (8 scenarios)
  S01 home_team_goal_close     PASS  dopamine=+0.28 adrenaline=+0.32
  S02 home_team_goal_blowout   PASS  dopamine=+0.10
  S03 overtime_buzzer_beater   PASS  dopamine=+0.42 adrenaline=+0.45 endorphins=+0.18
  S04 hockey_fight             PASS  testosterone=+0.30 adrenaline=+0.28
  S05 heartbreaker_loss        PASS  cortisol=+0.22 dopamine=-0.18
  S06 casual_viewer            PASS  dopamine=+0.05
  S07 photo_finish             PASS  adrenaline=+0.35 dopamine=+0.20
  S08 world_record             PASS  dopamine=+0.25 adrenaline=+0.18 endorphins=+0.12

WEATHER (4 scenarios)
  S09 sunny_day                PASS  serotonin=+0.18 gaba=+0.08
  S10 severe_storm             PASS  cortisol=+0.25 adrenaline=+0.18
  S11 gentle_rain              PASS  gaba=+0.12
  S12 first_snow               PASS  dopamine=+0.12 serotonin=+0.08

FINANCE (3 scenarios)
  S13 portfolio_up             PASS  dopamine=+0.15 serotonin=+0.08
  S14 market_crash             PASS  cortisol=+0.38 adrenaline=+0.25 dopamine=-0.20
  S15 steady_growth            PASS  serotonin=+0.18 dopamine=+0.10

NEWS (4 scenarios)
  S16 human_interest           PASS  oxytocin=+0.22 serotonin=+0.12
  S17 conflict_escalation      PASS  cortisol=+0.22 adrenaline=+0.12
  S18 scientific_breakthrough  PASS  dopamine=+0.25 serotonin=+0.10
  S19 mundane_news             PASS  total_delta=0.04

PRESENCE (3 scenarios)
  S20 owner_comes_home         PASS  oxytocin=+0.32 dopamine=+0.18
  S21 owner_leaves             PASS  oxytocin=-0.08 cortisol=+0.05
  S22 party_arrives            PASS  oxytocin=+0.20 dopamine=+0.18 serotonin=+0.10

COMPLEX (4 scenarios)
  S23 couch_scenario           PASS  dopamine=+0.35 serotonin=+0.15 oxytocin=+0.20 adrenaline=+0.22
  S24 everything_wrong         PASS  cortisol=+0.42 adrenaline=+0.30 dopamine=-0.18 serotonin=-0.12
  S25 mixed_feelings           SOFT  dopamine=+0.32 (expected max +0.30) adrenaline=+0.35 cortisol=+0.18
  S26 stoic_vs_anxious         PASS  stoic_cortisol=+0.08 anxious_cortisol=+0.25

EDGE CASES (4 scenarios)
  S27 ambiguous                PASS  total_delta=0.12
  S28 nonsensical              PASS  total_delta=0.02
  S29 long_description         PASS  dopamine=+0.18 serotonin=+0.15
  S30 rapid_sequence           PASS  dopamine=+0.38 adrenaline=+0.42

────────────────────────────────────────
TOTAL: 30 scenarios  |  29 PASS  |  1 SOFT FAIL  |  0 HARD FAIL  |  96.7%
```
