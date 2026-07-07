# Contributing to Kindalive

Thanks for your interest! First, expectations: **Kindalive is a hobby
project, maintained at hobby pace.** Issues and PRs are welcome and
read with genuine interest, but responses may take days or weeks, and
"no" is a likely answer for features that grow the maintenance surface.
Forks are warmly encouraged.

## Ground Rules (the architecture ones)

`docs/architecture.md` is the source of truth. The rules that will get
a PR bounced if broken:

1. **Emotions are computed, never stored.** They are pure functions of
   `ChemicalState`. No `mood` variables, ever.
2. **Decay uses true half-life**: `2^(-dt / half_life)`, not
   `e^(-dt/half_life)`.
3. **All chemicals and emotions are clamped to [0, 1]**, after all
   interaction rules run in a sub-step (the engine sub-steps any
   `dt > 0.5s`).
4. **Impulses are discrete events** — never scale their deltas by `dt`.
5. **Use `ManualClock` in tests** — never `time.time()` or
   `asyncio.sleep()` in the core engine.

## Dev Setup

```bash
git clone https://github.com/smithandrewjohn/Kindalive
cd Kindalive
pip install -e ".[all,dev]"
```

The core library has zero dependencies; `[all,dev]` adds the web UI
(NiceGUI), both LLM backends, and the test/type tooling.

## Before You Push

```bash
# Fast unit tests (no API keys, no LLM calls) + coverage gate (>=80%)
pytest tests/ -m "not integration and not llm" --cov

# Strict type check (must be clean)
mypy
```

CI runs exactly these on Python 3.10–3.13, plus a core-only run on 3.9
(the zero-dependency engine supports 3.9; the NiceGUI dashboard needs
3.10+).

If you change emotion weights, interaction coefficients, or chemical
parameters, also:

1. Update `docs/architecture.md` first
2. Update the corresponding TOML in `kindalive/config/`
3. Run the LLM benchmark if you have an API key
   (`pytest tests/ -m llm`, >90% PASS expected)

## Code Conventions

- Python 3.9+ syntax, `from __future__ import annotations`, full type
  hints (`mypy --strict` must pass)
- Enum values are lowercase strings; parse chemical names with
  `Chemical.from_string()` (case-insensitive)
- External code goes through the `Robot` class, not
  `NeurochemicalEngine`
- Test files mirror source structure
  (`kindalive/engine/chemicals.py` → `tests/test_chemicals.py`)

## Good First Contributions

The fun list lives in `FEATURE_IDEAS.md` — items marked **Easy** are
sized for an evening. Hardware adapters for new displays/actuators
(see `examples/`) are especially welcome: they're self-contained and
don't touch the engine.
