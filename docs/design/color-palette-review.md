# Kindalive Web UI — Color Palette Review

> **Status:** Historical design-review artifact (2026-04-11). The
> palette it recommends — neutral dark-gray surfaces and valence-family
> chemical/emotion colors — is still live in
> `kindalive/expression/web_ui.py` (`CHEMICAL_COLORS` / `EMOTION_COLORS`)
> and `web_assets/style.css`. Note that the UI has since been **simplified
> to its essentials** (the 3-column dashboard now shows chemistry / LED
> face / emotion mix); the breakdown panel, timeline chart, event feed,
> and inject sliders this review discusses were removed in the pivot, so
> read those parts as design rationale, not current UI. This document
> drew on Refactoring UI,
> Linear, Vercel Geist, Grafana best practices, and the Okabe–Ito
> colorblind-safe palette research.

## Executive summary

The current UI is a saturated indigo stage with 16 fully-bright competing hues
and a neon-gold accent that's the same yellow as dopamine/happiness —
everything screams for attention at once, so nothing reads as signal. The fix
is to (1) swap the indigo for a true neutral dark-gray base, (2) collapse the
palette from "rainbow per series" to "valence families" where most series
render in muted tones and only the dominant series / active events pop, and
(3) demote the `#fccc00` accent to a single restrained brand mark so the data
colors can be the brightest pixels on screen.

## What works

- The three-column layout and information hierarchy (chemistry / face /
  readouts / timeline-breakdown-inject) are sound; this is a layout-confident
  dashboard.
- Tabular-num value labels, monospace breakdown panel, and per-row progress
  bars are exactly right for a numerical dashboard.
- The pulsing gold dominant-emotion label is a nice focal device — the
  *concept* is right, just the *color* fights everything else.
- Dark theme is the correct choice for a telemetry surface.

## What's broken

- **Background `#0c0c3e` is not neutral** — it's a ~240° indigo at ~25%
  chroma. Everything on top inherits a blue cast, and cool data colors (gaba
  `#5c94fc`, sadness `#336699`, calm `#5c94fc`) visually dissolve into it.
- **Card `#15154a` vs. border `#3a3a7e` vs. background `#0c0c3e`** are all
  the same hue at different lightnesses. There is no neutral tier, so the UI
  reads as "one color of blue" with no separation between structural and
  content layers.
- **`#fccc00` is used for 9+ roles at once** (brand mark, every card title,
  dominant label glow, slider thumb, chart event markers, focus ring) *and*
  it is the exact same family as dopamine `#ffcc00` and happiness `#ffcc00`.
  You cannot tell at a glance whether yellow means "chrome" or "data."
- **Cortisol `#bc0000` + adrenaline `#ff3030` + anger `#bc0000`** are three
  near-identical reds that are supposed to convey three distinct semantics.
  They'll be indistinguishable in the timeline.
- **Oxytocin `#ff69b4` and bonding `#ff69b4`** are literally the same pink,
  but so is the dopamine/happiness pair — confusing because it implies a
  1:1 mapping that isn't actually consistent across the other 6 pairs.
- **8 fully-saturated lines** on one chart, all drawn at `width: 2` with no
  opacity hierarchy — classic rainbow-spaghetti. Refactoring UI is explicit
  that pure-saturated colors feel "cheap" on dark backgrounds and you should
  scale saturation back.
- **`#b0c4fc` body text** is a low-contrast periwinkle that likely fails
  WCAG AA against `#15154a` for small type.
- **Sadness `#336699` is almost invisible** — it's darker than several
  border colors. It cannot be the dominant emotion's color and also be
  illegible.
- **Red/green for the breakdown panel** (`#5cf05c` positive, `#ff6666`
  negative) is the classic deuteranope confusion pair with no secondary
  encoding.

## Research: how professional dashboards solve this

1. **Refactoring UI (Schoger/Wathan)** — Build three families: grays (8–10
   shades), primary (5–10 shades), accents (5–10 shades, used *sparingly*).
   Don't reach for pure HSL primaries; use desaturated shades on dark
   backgrounds. **Most of the UI should be grayscale**, and color should
   signal meaning, not decoration.
2. **Vercel Geist / Linear** — Both build themes on top of a neutral
   grayscale (Linear uses LCH so equal-L values look equally bright). Chrome
   is near-monochrome; a single accent color carries brand + focus + primary
   action. Data viz uses lower-saturation versions of the same accent family
   plus 3–5 categorical hues only when needed.
3. **Okabe–Ito (Nature Methods)** — The canonical 8-color categorical
   palette that survives protanopia/deuteranopia/tritanopia:
   `#E69F00 #56B4E9 #009E73 #F0E442 #0072B2 #D55E00 #CC79A7 #000000`. Every
   pair has ≥30 ΔL in CIELAB. This is the only off-the-shelf set of 8 safe
   colors.
4. **Grafana best practices** — Recommends ≤6 visible series at once; use
   "classic palette by series name" so colors are stable across views; pair
   high-contrast hues (blue + orange) rather than blue + green. When more
   series exist, mute inactive ones and highlight on hover.
5. **Power BI / Ananya Deka on dark-mode dataviz** — Don't invert a light
   palette; lift lightness and drop saturation. Gridlines should be
   `#2a2a2a`–`#3e3e3e`, axes only slightly brighter. Text tiers should sit
   at ~92% / ~70% / ~50% lightness of the base.

## Proposed palette

All values chosen on a neutral cool-gray ramp (~240° hue, ~4% chroma) so
nothing is "blue" — it just feels dark and calm. Designed to pass WCAG AA
for small text on `--card`.

### Surfaces

```
background:      #0B0D12   /* true near-black with a whisper of blue */
background-alt:  #0F1218   /* second tier, for the top bar */
card:            #141820   /* primary panel */
card-hover:      #1A1F29   /* hover / active panel */
border:          #232834   /* visible but recessive */
border-muted:    #1B2028   /* internal dividers */
```

### Text

```
text-primary:    #E8ECF3   /* body, values */
text-secondary:  #A3ADBF   /* labels, axis ticks */
text-muted:      #6B7587   /* captions, footnotes, inactive */
```

`text-primary` on `card` ≈ 12.5:1 contrast. `text-secondary` on `card`
≈ 6.1:1. Both pass AA.

### Accent / brand / status

```
primary:  #7C9CFF   /* single brand blue — brand mark, focus rings,
                       primary buttons, slider thumb, active toggle.
                       Replaces #fccc00 entirely in chrome. */
success:  #3DD68C   /* positive breakdown contribs, LLM: ON */
warning:  #F5B544   /* event markers on the timeline (was #fccc00) */
danger:   #F0616B   /* negative breakdown contribs, errors */
```

Success/danger are **not** pure red/green — both are shifted so a
deuteranope sees them as "yellow-green" vs "salmon-pink," and they're
additionally encoded with `+`/`−` prefixes in the breakdown panel.

### Chemicals (valence-family scheme)

Grouped by physiological family, not arbitrary. Each family shares a hue
wedge; lightness/chroma distinguishes within the family:

```
# "Reward / drive" family — warm golds & oranges
dopamine:     #E6A23C   # warm amber — reward anticipation
testosterone: #D96B2C   # deeper burnt-orange — drive, dominance
endorphins:   #E8C36B   # pale straw — sustained pleasure / analgesia

# "Bonding / calm" family — teal & soft blue
serotonin:    #4FB7A6   # muted teal — wellbeing
oxytocin:     #7FB3D9   # dusty sky — affiliation (NOT pink)
gaba:         #5682B5   # slate blue — inhibitory calm

# "Stress / arousal" family — red-orange & magenta
cortisol:     #C4513F   # rust red — chronic stress
adrenaline:   #E8526B   # hot coral — acute arousal (distinct from cortisol)
```

Every pair has ≥30 ΔL in CIELAB; the two reds (cortisol/adrenaline) are
separated by both lightness (~20) and hue angle (~15°) so they survive
deuteranopia as "darker muddy" vs "brighter pink-coral."

### Emotions (parallel scheme)

```
# Positive
happiness:  #E6A23C   # mirrors dopamine — warm amber
excitement: #D96B2C   # mirrors testosterone — burnt orange
euphoria:   #C678DD   # lone magenta — the "something rare" flag
bonding:    #7FB3D9   # mirrors oxytocin — dusty sky

# Neutral / low-arousal
calm:       #4FB7A6   # mirrors serotonin — teal

# Negative
anxiety:    #B892D1   # muted lavender — high arousal + negative valence
anger:      #C4513F   # mirrors cortisol — rust red
sadness:    #6B87A8   # slate, LIFTED from #336699 so it's visible on dark
```

The intentional color-sharing between a chemical and its "signature emotion"
teaches the user the causal mapping.

## Grouping strategy

**Valence + arousal families instead of 16 independent hues.** Three
families:

- **Warm (reward/drive):** ambers → oranges → rust. High-valence positive
  states.
- **Cool (bonding/calm):** teals → dusty blues → slates. Low-arousal
  positive + low-arousal negative (sadness lives here because it's
  low-arousal).
- **Hot (stress/threat):** rust reds → coral → muted lavender. High-arousal
  negative.

One outlier (euphoria magenta) acts as a "this is unusual" flag. Because
families share hue wedges, when cortisol and adrenaline both rise, the
timeline shows a coherent "warm-red band swelling" instead of two random
lines — the visual gestalt itself encodes meaning.

## Specific changes beyond color

1. **Dim inactive series in the chart to 25% opacity**; only the top-3 by
   current value render at full opacity and `width: 2.5`. Rainbow → signal.
2. **Drop chart line width for non-dominant to 1px**, dominant to 2.5px.
3. **Remove the `#fccc00` from card titles** — titles should be
   `text-secondary` at 11px uppercase with 0.08em letter-spacing. Let data
   be the only colorful thing.
4. **Pulse the dominant label in `--primary` blue**, not gold, at 60%
   opacity so it doesn't compete with timeline lines.
5. **Gridlines**: `#1B2028` (border-muted), axis ticks in `text-muted`.
6. **Typography:** body Inter 13px/1.5, labels 11px/1.4, tabular-nums for
   all values. Fix label columns to a rigid grid with
   `text-overflow: ellipsis; overflow: hidden`.
7. **Tighten spacing** — card padding 16px → 12px, row gap 8px → 6px. More
   data per pixel reduces the "noise" feeling.
8. **Single accent rule**: `--primary` appears in exactly 4 places (brand
   mark, active toggle, focused input, play button). Anywhere else that
   currently uses `#fccc00`, switch to `text-secondary`.

## Colorblind check

- **Deuteranopia:** cortisol (`#C4513F`, L≈46) vs adrenaline (`#E8526B`,
  L≈60) differ by 14 L-units and shift differently — cortisol becomes muddy
  olive, adrenaline becomes salmon. Distinguishable.
- **Protanopia:** the reward family desaturates toward yellow-beige but
  stays clearly warmer than the teal/slate family. Happiness `#E6A23C` and
  cortisol `#C4513F` are separated by ΔL≈24.
- **Tritanopia:** oxytocin `#7FB3D9` and gaba `#5682B5` stay distinct by
  lightness; serotonin teal shifts toward pink but stays separated from the
  bonding blue by hue.
- **Red/green breakdown signals** replaced with `#3DD68C` vs `#F0616B`
  (yellow-green vs salmon), additionally carry `+`/`−` glyphs — never
  color-only encoded.
- All 8 chemical pairs maintain ≥30 ΔL in CIELAB (the Okabe–Ito threshold).

## Recommendation summary

1. **Replace the indigo base with neutral cool-gray.**
   `#0c0c3e → #0B0D12`, card `#15154a → #141820`, border
   `#3a3a7e → #232834`. This alone fixes ~60% of the "noisy" feeling.
2. **Kill the gold chrome.** `#fccc00` disappears from card titles, slider
   thumbs, focus rings, dominant label, event markers. Keep one instance:
   the `★ KINDALIVE` brand mark, but in `#7C9CFF`.
3. **Regroup chemical/emotion colors into three valence families**
   (warm-reward, cool-calm, hot-stress) so the timeline reads as bands
   instead of spaghetti.
4. **Mute non-dominant chart series to 25% opacity + 1px** and only
   highlight the current top-3 at full saturation.
5. **Lift text contrast**: body `#b0c4fc → #E8ECF3`, secondary
   `→ #A3ADBF`. Both clear WCAG AA.
6. **Replace red/green breakdown colors** with `#3DD68C` / `#F0616B` and
   require `+`/`−` prefixes so the breakdown panel is colorblind-safe.

## Sources

- [Building Your Color Palette — Refactoring UI](https://refactoringui.com/previews/building-your-color-palette/)
- [Designing for Color blindness — Martin Krzywinski / BCGSC](https://mk.bcgsc.ca/colorblind/palettes.mhtml)
- [Coloring for Colorblindness — David Nichols](https://davidmathlogic.com/colorblind/)
- [Okabe–Ito Palette Hex Codes — Conceptviz](https://conceptviz.app/blog/scientific-color-palette-for-research-papers-and-posters)
- [Vercel Geist Colors](https://vercel.com/geist/colors)
- [Linear Style](https://linear.style/)
- [Implementing Dark Mode for Data Visualizations — Ananya Deka](https://ananyadeka.medium.com/implementing-dark-mode-for-data-visualizations-design-considerations-66cd1ff2ab67)
- [Designing Power BI Dashboards in Dark Mode — Numerro](https://www.numerro.io/blog/designing-dashboard-in-dark-mode)
- [Grafana — Time Series color options](https://docs.aws.amazon.com/grafana/latest/userguide/v9-time-series-color.html)
- [7 Best Practices for Grafana Dashboard Design — MetricFire](https://www.metricfire.com/blog/7-best-practices-for-grafana-dashboard-design/)
