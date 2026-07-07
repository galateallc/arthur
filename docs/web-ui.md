# Web UI — the Kindalive Dashboard

A NiceGUI page built around one thing: a **retro LED dot-matrix robot
face** (Cozmo / flip-dot style) that contorts in real time as the
neurochemistry shifts. Type a paragraph, the LLM translates it to
chemical impulses, the chemistry moves, and the face shows the
emotional mix. Chemical levels and the emotion mix are always visible
beside the face.

## Running It

```bash
# Offline (face + chemistry work; text input disabled)
python3 -m kindalive.expression.web_ui

# Cloud LLM — Claude. Any of these three work:
#   (a) put ANTHROPIC_API_KEY in .env at the repo root (auto-loaded)
#   (b) export ANTHROPIC_API_KEY in your shell
#   (c) pass it on the command line
ANTHROPIC_API_KEY=sk-ant-... python3 -m kindalive.expression.web_ui
python3 -m kindalive.expression.web_ui --anthropic-key sk-ant-...

# Local LLM — any OpenAI-compatible server (Ollama, LM Studio, vLLM…)
KINDALIVE_LLM_BASE_URL=http://localhost:11434/v1 \
KINDALIVE_LLM_MODEL=llama3.1 \
python3 -m kindalive.expression.web_ui

# Cloud via OpenRouter (also OpenAI-compatible)
KINDALIVE_LLM_BASE_URL=https://openrouter.ai/api/v1 \
KINDALIVE_LLM_MODEL=qwen/qwen3-235b-a22b \
KINDALIVE_LLM_KEY=sk-or-... \
python3 -m kindalive.expression.web_ui --llm openai

# Or all on the command line:
python3 -m kindalive.expression.web_ui --llm openai \
    --llm-base-url https://openrouter.ai/api/v1 \
    --llm-model qwen/qwen3-235b-a22b --llm-key sk-or-...

# Personality preset / custom bind
python3 -m kindalive.expression.web_ui --personality cheerful --port 9090
```

Open http://localhost:8080. The Robot lives as a module-level singleton
(single-client assumption).

### LLM resolution (`--llm auto`, the default)

1. `ANTHROPIC_API_KEY` present → Claude (Haiku).
2. Otherwise `KINDALIVE_LLM_BASE_URL` set → OpenAI-compatible server.
3. Otherwise → offline; the text input is disabled.

`--llm anthropic|openai|off` forces a choice. `--llm-model` overrides
the model for either backend. The header shows which backend is live.

### OpenAI-compatible / OpenRouter backend

Any server that speaks the OpenAI `/chat/completions` API works —
Ollama, LM Studio, vLLM, llama.cpp, OpenAI, and **OpenRouter**. Config
comes from these (CLI flags override env vars):

| Setting | Env var | CLI flag |
|---|---|---|
| Base URL | `KINDALIVE_LLM_BASE_URL` | `--llm-base-url` |
| Model ID | `KINDALIVE_LLM_MODEL` | `--llm-model` |
| API key | `KINDALIVE_LLM_KEY` (or `OPENAI_API_KEY`) | `--llm-key` |
| Attribution (OpenRouter, optional) | `KINDALIVE_LLM_REFERER`, `KINDALIVE_LLM_TITLE` | — |

For **OpenRouter**: set the base URL to `https://openrouter.ai/api/v1`,
the key to your OpenRouter key, and the model to the **exact slug from
[openrouter.ai/models](https://openrouter.ai/models)** (e.g.
`qwen/qwen3-235b-a22b` — there is no "qwen 3.6"; use the real ID).
`X-Title` defaults to `Kindalive` for attribution; set
`KINDALIVE_LLM_REFERER` if you want OpenRouter's app-ranking referer too.

Note: the interpreter needs the model to return a JSON object
(`{"reply", "impulses"}`); the prompt demands JSON-only. Prefer an
**instruct** model. A "thinking"/reasoning variant that emits
chain-of-thought before the JSON can break the parse and fall back — if
you see `FALLBACK — JSONDecodeError`, that's the cause (the raw response
is logged to stderr as `[kindalive.llm]`).

## Use it from your phone

The dashboard is fully responsive: on a phone the three columns collapse
to a single column with the LED face on top, the text box + **Send**
button under it, and the chemical/emotion bars below. The LED face is a
lightweight 2D canvas (the device pixel ratio is capped and the panel
reflows on resize/rotation), so it stays smooth on modest hardware.
It's also installable — open it, then **Share → Add to Home
Screen**, and it launches fullscreen like a native app.

There are two ways to reach it from your phone.

### A. Same Wi-Fi (computer must be on)

Bind to all interfaces and open your computer's LAN IP from the phone:

```bash
ANTHROPIC_API_KEY=sk-ant-... \
python3 -m kindalive.expression.web_ui --host 0.0.0.0
# then on the phone: http://<your-computer-LAN-IP>:8080
```

Quick and zero-cost, but the computer has to be awake and on the same
network.

### B. Always-on host (no computer needed)

To use it any time without your computer, run it somewhere always-on —
a small cloud VM, a container platform (Fly.io / Render / Railway), or a
Raspberry Pi at home. A `Dockerfile` is included:

```bash
docker build -t kindalive .
docker run -p 8080:8080 -e ANTHROPIC_API_KEY=sk-ant-... kindalive
```

`main()` reads `KINDALIVE_HOST` (the image sets it to `0.0.0.0`) and
`$PORT` / `KINDALIVE_PORT`, so most platforms that inject a `$PORT` work
with no extra flags. Point your phone at the host's URL and add it to
your home screen.

Notes:
- Use the **cloud LLM** (`ANTHROPIC_API_KEY`) for a remote host — a
  local OpenAI-compatible server on your home machine isn't reachable
  from the cloud unless you also expose it.
- Put the host behind HTTPS (most platforms do this automatically).
  Some mobile browser features are happier over `https://`.
- The app assumes a single client (one shared Robot). That's fine for
  personal use; it is not multi-tenant.

### API keys via `.env`

On startup, `main()` walks upward from the current directory looking
for a `.env` file and loads `KEY=VALUE` pairs into `os.environ`
(zero-dependency loader in `kindalive/env_loader.py`). Shell-exported
variables win. Pass `--no-dotenv` to skip.

## Layout

```
┌──────────────────────────────────────────────────────────────┐
│ KINDALIVE  [default]        time [1× 10× 60×]   LLM: model   │  header
├──────────────┬───────────────────────────────┬───────────────┤
│ NEUROCHEM    │                               │  EMOTION MIX  │
│ dopamine  ▓▓ │        ┌───────────────┐      │  happiness ▓▓ │
│ serotonin ▓▓▓│        │               │      │  excitement ▓ │
│ oxytocin  ▓  │        │   LED FACE    │      │  anger     ░  │
│ testost.  ▓▓ │        │ (LED matrix)  │      │  calm      ▓▓▓│
│ cortisol  ▓  │        │               │      │  bonding   ▓▓ │
│ adrenaline░  │        └───────────────┘      │  anxiety   ░  │
│ endorphins▓  │         CALM 0.34             │  sadness   ░  │
│ gaba      ▓▓ │   calm 0.34 · happiness 0.31  │  euphoria  ░  │
│              │ ┌───────────────────────────┐ │               │
│              │ │ Tell the robot something… │ │               │
│              │ └───────────────────────────┘ │               │
└──────────────┴───────────────────────────────┴───────────────┘
```

## Features

### 1. The LED dot-matrix face (center)

A retro LED panel drawn on a plain 2D canvas in `web_assets/face3d.js`
— eyes, brow bars and a mouth rendered as a grid of glowing dots that
light up in the dominant emotion's accent color, over a faint unlit
grid, with a CSS scanline + vignette overlay for the broadcast look.

All 12 `FaceState` muscles (FACS Action Units) drive it: eyes become
happy arcs when smiling or alert blocks otherwise (widened by
`eyelid_upper_raise`, narrowed by `eyelid_lower_tighten`), brow bars
angle from `brow_lower`/`brow_inner_raise`, and the mouth curves with
the smile factor, narrows with `lip_pucker`, and opens with `jaw_open`.
The web UI pushes muscle targets at 10 Hz; the JS lerps toward them and
layers autonomous life on top — blinks, eye saccades, and a breathing
glow. No WebGL, no model files, no dependency — just the browser.

The dominant emotion and its strength render under the face, with the
top-3 emotion mix below; the same accent color lights the dots.

### 2. Freeform text input (under the face)

The only input. **Enter** to send (**Shift+Enter** for newline,
**Ctrl+Enter** also works). The paragraph becomes a
`UserText(summary=text)` and routes through the LLM interpreter. The
status line under the box shows the interpreter path and the applied
impulses:

- **`"…" — LLM OK → dopamine +0.30, adrenaline +0.25`**
- **`"…" — cache hit`** — exact repeat served from cache.
- **`"…" — FALLBACK — <error>`** — LLM call failed; a small cortisol
  nudge was applied. Check stderr for the `[kindalive.llm]` log with
  the raw response snippet.

The status line shows the **full** phrase you sent (no truncation) — the
whole text always reaches the LLM.

The robot **remembers the conversation**: every message carries the prior
exchanges to the LLM as multi-turn context, so follow-ups land in context
instead of the robot having amnesia. The thread persists for the session
(across page reloads — one shared Robot) and resets when you switch
personality. History is bounded to the last ~20 exchanges.

### 3. Spoken reply + voice (TTS)

The LLM is both the interpreter and the robot's **voice**: alongside the
chemical impulses it returns a short spoken-style `reply`
(`Robot.last_reply`), coloured by the robot's current mood. The reply
appears as a 🗣 line under the input and is read aloud through the
browser's built-in speech synthesizer (Web Speech API — client-side, no
dependency, works on phones). Speaking rate and pitch are mapped from the
post-event mood: more arousal → faster, more positive valence → higher.

The **🔊 toggle** in the header mutes/unmutes speech. Because iOS/Safari
only allow programmatic speech after a real user gesture, the page primes
the speech engine on your first tap; on iOS, interact with the page once
(the first Send tap counts) and replies will speak from then on.

### 4. Neurochemistry panel (left)

Eight chemical bars with live numeric levels, refreshed at 10 Hz,
colored by the valence-family palette (dopamine amber, serotonin teal,
cortisol rust, GABA slate, …).

### 5. Emotion mix panel (right)

Eight emotion bars — the computed projection, never stored. The
dominant emotion is also named under the face.

### 6. Time (header)

Simulation time always runs in real time. The 1×/10×/60× toggle speeds
it up so you can watch adrenaline decay in seconds or cortisol over
"hours".

### 7. Reset (header)

**Reset** rebuilds the robot — clearing the conversation thread and
giving it a fresh chemical state — and clears the input/reply/status and
stops any speech. The fresh state is **slightly randomized** (each
chemical nudged up to ±0.22 off its baseline), so you don't always meet a
perfectly calm robot: it might open cheerful, restless, wistful, or a
little on edge. The same jitter applies to the robot the server starts
with, so the very first page load is varied too. Speed and voice settings
are kept.

## Architecture

- **Single-client, local-first** — one Robot, one page, no auth.
- **Async-native** — the submit handler `await`s
  `robot.interpret_text(...)` directly; NiceGUI runs on FastAPI.
- **10 Hz refresh** — one `ui.timer` advances the robot by wall-clock
  delta × speed, repaints the bars, and pushes a face payload via
  `ui.run_javascript`.
- **The face animates client-side at 60 fps** — Python only sends
  targets; smoothing, blinking, and glitches live in the browser.

## Files

| File | Role |
|------|------|
| `kindalive/expression/web_ui.py` | NiceGUI app — layout, handlers, refresh loop |
| `kindalive/expression/face.py` | 12-muscle `FaceState` + `FaceProjection.compute` |
| `kindalive/expression/face_3d.py` | Payload mapping + boot wiring |
| `kindalive/expression/web_assets/face3d.js` | The LED dot-matrix face (2D-canvas renderer) |
| `kindalive/expression/web_assets/style.css` | Dashboard styling + scanline overlay |
| `kindalive/interpreter/anthropic_backend.py` | Claude backend |
| `kindalive/interpreter/openai_backend.py` | Local/cloud OpenAI-compatible backend |
| `kindalive/env_loader.py` | Dependency-free `.env` loader |
| `tests/test_web_ui.py` | Smoke tests + `Robot.last_impulses` behavior |
| `tests/test_face_3d.py` | Payload mapping + asset wiring tests |

## Verification

```bash
# Smoke test — module imports and app is constructable
python3 -c "from kindalive.expression.web_ui import create_app; print('ok')"

# Unit tests
pytest tests/test_web_ui.py tests/test_face_3d.py -v

# Launch
python3 -m kindalive.expression.web_ui
```

Then in the browser:

1. The head should be glossy, swaying gently, blinking, glancing
   around, and occasionally stuttering — over a drifting neon-band
   backdrop with scanlines.
2. With an LLM configured, type "you won the lottery" → wide eyes,
   raised brows, open grin; dopamine/adrenaline bars spike; the
   accent color shifts to the dominant emotion.
3. Set time to 60× and watch the face relax back to baseline as the
   chemistry decays.
4. Type "the cat is missing and a storm is rolling in" → inner brows
   rise, lip corners depress, lids tighten; cortisol climbs.
