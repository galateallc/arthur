# Feature Ideas for Kindalive

A short, current list of where Kindalive could go next. Feasibility:
**Easy** (an evening), **Medium** (a few days), **Hard** (significant
effort), **Research** (needs experimentation). Every idea must respect
the core rule: emotions are *computed* from chemistry, never stored.

> The project deliberately stripped its old data fetchers (sports /
> weather / news / finance) and terminal UIs. The only input now is the
> owner's freeform text → LLM → chemical impulses, shown on the LED
> dot-matrix face. Ideas below build on that, not the fetcher era.

---

## Shipped

- **LLM interpreter as the robot's voice** — one call returns
  `{reply, impulses}`; the spoken reply is read aloud (Web Speech API,
  mood-mapped prosody) and lip-synced on the face.
- **Session conversation memory** — multi-turn context so the robot
  remembers the discussion (`Robot.conversation`).
- **Local *or* cloud LLM** — `OpenAICompatBackend` (Ollama / LM Studio /
  vLLM / OpenAI) alongside the Anthropic backend.
- **LED dot-matrix face** — 12-muscle `FaceState` drawn as a glowing dot
  grid with blinks, saccades, mood color, and talking lip-sync.
- **Mobile + hostable** — responsive, installable PWA; `Dockerfile` +
  `KINDALIVE_HOST`/`$PORT` for always-on hosting.
- **Reset with a random starting mood** — you don't always meet a calm
  robot.
- **Open-source packaging** — MIT license, zero-dependency core with
  `[web]`/`[anthropic]`/`[openai]` extras, CI (tests + >=80% coverage
  gate + `mypy --strict`), CONTRIBUTING.md, README demo GIF.
- **Hardware adapter examples** — `examples/` drives a MAX7219 LED
  matrix and PCA9685 servos from `FaceState` (first slice of
  "physical-robot output"; terminal fallback without hardware).

---

## Input & interaction

- **Push-to-talk speech input** (Medium) — Web Speech *recognition* to
  dictate into the text box, so you can talk *to* the robot, not just type.
- **Personality picker in the header** (Easy) — the presets (`cheerful`,
  `stoic`, `anxious`) already exist; surface a selector that rebuilds the
  robot with that seed (Reset already rebuilds, so this is mostly UI).
- **Voice picker** (Easy) — choose among the browser's
  `speechSynthesis.getVoices()` instead of the OS default.

## The face

- **Selectable face skins** (Medium) — the renderer is decoupled behind
  `window.kindaliveFace`; the flat-2D and abstract-3D prototypes from the
  bake-off could ship as alternate skins toggled in the UI.
- **Richer idle life** (Easy) — occasional look-arounds, micro-expressions,
  a sleepy droop when nothing happens for a while.
- **Physical-robot output** (Research) — `examples/` already maps
  `FaceState` to a MAX7219 matrix and PCA9685 servos; the research part
  is a full animatronic head (linkages, calibration, safety limits).

## Memory & mood

- **Persist mood across restarts** (Medium) — `persistence/state_store.py`
  can already serialize the engine; wire it so a robot that was stressed
  before a reboot is still a bit stressed after.
- **Conversation summarization** (Research) — for very long sessions,
  summarize older turns instead of dropping them at the 40-message cap.
- **Mood sparkline** (Easy) — a tiny history strip of the dominant emotion
  over the session (a row of colored dots, no heavy charting).

## Behavior

- **Autonomous drift / ambient mood** (Medium) — let the robot
  occasionally shift on its own (a slow circadian sway, a random sigh),
  so it feels alive between messages.
- **Multiple robots** (Hard) — the engine is per-instance; a
  `RobotManager` + a switcher would let you keep several with distinct
  personalities and histories.

## Quality

- ~~**`mypy --strict` in CI**~~ — shipped; CI fails on any strict-mode error.
- ~~**Coverage gate**~~ — shipped; `pytest --cov` fails under 80%.
- **PyPI release** (Easy) — packaging metadata is ready; publish
  `kindalive` so `pip install kindalive` works without the repo.
