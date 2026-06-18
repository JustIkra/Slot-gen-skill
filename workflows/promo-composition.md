# Promo / Lobby-Thumbnail Composition — Best Practices

Reusable spec for slot **key art** and **1:1 lobby thumbnails**. Reverse-engineered
from released competitor tiles by measuring them, then **stress-tested by building a
procedural promo and having an art director tear it apart**. That second pass matters:
the first version of this doc over-trusted global pixel histograms and produced
artifacts (a fake white "light beam", flat over-lit pages). The corrected rules below
separate the numbers that genuinely predict a premium tile from the naive proxies that
mislead.

Use this whenever the task is a **store/lobby icon, promo banner, or marketing key
art**, not an in-game symbol.

> **Golden rule:** measure **hierarchy, depth and separation** — not global brightness.
> Numbers are sanity checks; they never substitute for the squint test (§A).

---

## THE RULES THAT ACTUALLY MATTER (check these first)

### A. Squint test — exactly two focal points
Blur the tile by ~6% of its width. You must see **exactly two** distinct blobs: the
**hero** and the **logo**. If it blurs into one glowing mush, or the logo merges into a
bright background (e.g. gold coins under gold text), the hierarchy is broken. This is the
single most predictive check.

### B. Depth separation — hero must out-value its background
The hero must clearly sit *in front of* the background. Measurable: **mean luma of the
hero bounding box ≥ ~2× mean luma of the background directly behind/around it.** A strong
dark vignette behind a glowing centered hero is *correct*, not a defect (see §E).

### C. Atmospheric perspective — push the background back
Background elements must have **lower local contrast, lower saturation, and softer focus**
than the hero. Hard-edged, sharp, saturated background architecture competes with the
hero and flattens depth. Wash the BG with darkness/haze/blur.

### D. Distinct silhouette (cutout test)
The hero's silhouette must stay readable — **not sliced or buried by opaque VFX** (light
beams, thick ribbons, swirls crossing in front). If you cut the hero out, it should be a
clean recognizable shape.

### E. Directional light & volume
The hero needs a **light side and a shadow side** (a luma gradient across it), so it reads
3-D. Lighting a hero uniformly "from everywhere" makes it flat. Exception: a symbol asset
that is intentionally front-lit and symmetric — then don't fight it, but still seat it in
directional ambient.

### F. Trust an already-lit hero asset — don't double-expose it
If the hero PNG **already contains its own burst / rays / glow / sparks** (common for slot
symbol art), do **not** stack procedural god-rays + bloom + a light-beam + speculars on
top. That double exposure is exactly what produces the flat, noisy, washed look. Augment
minimally: seat it into the BG, maybe one soft backglow, and stop.

---

## NUMERIC SANITY CHECKS (ranges, not hard gates)

These are useful guard-rails. Treat them as ranges that flag a problem, not targets to
force — forcing them produces artifacts.

### 1. Area budget (rough)
Hero **35–60%**, Logo **18–30%**, Background+FX the rest (**can exceed 40%** — several
winners run a big atmospheric background). The old rigid "60/20/20" and even "40/30/30"
quotas are too strict; let the composition breathe. Over-scaling the hero past ~65% chokes
the logo.

### 2. Title : subtitle ratio = 2 : 1 to 3 : 1  ✅ reliable
Equal-size lines read as amateur. Shrink the smaller line (e.g. "BOOK OF") to ~40–50% of
the main word's cap height.

### 3. Logo separation = dark, not glow  ✅ reliable, hard rule
Separate the title from a bright/glowing BG with a **dark backing plate, a heavy
drop-shadow (opacity > 80%), or a thick dark stroke**. A **colored outer glow does NOT
separate** — it bleeds into the light and kills legibility at small size. A thin colored
brand rim is fine **only if** a dark shadow sits under it.

### 4. Dynamic range, not "pure white"
Want "sparkle / pop"? That's **contrast + localization**, not volume of white pixels.
- Deep blacks present: **P2 ≤ ~10**.
- A warm-gold palette legitimately peaks around RGB [255,200,100] — its luma tops out
  ~190. **Do NOT force a global P98 ≥ 250 / "2% pure white".** Forcing it makes you paint
  opaque white shapes (the "beam" crutch).
- Instead, **specular localization**: the brightest ~1% of pixels should live **inside the
  top ~20% of the hero's bounding box** (the light originates from the hero), as small
  pinpoint glints/sparks — not a big graphic shape, not smeared across the frame.

### 5. Vignette — strong is fine for a centered hero
Do **not** target a fixed corner/center ratio. A centered glowing hero on a dark set
naturally gives a very strong vignette (corners ≪ center) and that is *good*. What matters
is §B (depth separation) and that the **corners are genuinely dark** (anchors the eye).
Only worry if the whole frame is uniformly mid-bright (milky) — that's the real failure.

### 6. Saturation floor ≈ > 0.55, ≤ 2 dominant hues
Keep colour rich but disciplined. Don't add gratuitous secondary-colour FX (e.g. random
teal ribbons) just to hit a colour-contrast number.

### 7. Warm / cool separation
Separate hero from ambient by temperature (warm hero ↔ cooler ambient, or vice-versa). A
delta is good; don't manufacture it with noise.

---

## Failure modes (learned the hard way)

- **Double-exposing an already-lit hero** (§F) → flat, noisy wash. The #1 mistake.
- **Forcing pure-white to satisfy a histogram** → opaque "light beam" / fake-sun crutches
  that don't interact with the scene. Light must be soft/volumetric + tiny speculars.
- **Washing the hero uniformly bright** to lift P50/P98 → kills internal contrast (e.g.
  glowing pages with no falloff, no ambient occlusion in the spine crease). Keep the
  material dark where it should be dark.
- **Colored glow behind text** for separation → use a dark shadow instead.
- **Sharp, saturated background** competing with the hero → blur + desaturate + darken it.
- **Over-vignetting into a black tunnel** is possible, but rarer than the milky-bg failure.

---

## Corrected pass/fail checklist

Qualitative-first, then numeric guard-rails:

- [ ] **Squint (6% blur) → exactly two focal points** (hero + logo), logo not merging into BG
- [ ] Hero bounding-box mean luma ≥ ~2× the BG behind it (depth separation)
- [ ] BG is lower-contrast, lower-saturation, softer-focus than the hero (atmosphere)
- [ ] Hero silhouette readable, not sliced by opaque VFX
- [ ] Hero has a light side & shadow side (not flat-lit) — unless intentionally symmetric
- [ ] Hero ≈ 35–60% of tile; logo ≈ 18–30%
- [ ] Title cap-height is 2×–3× the subtitle
- [ ] Logo separated by dark plate / drop-shadow / thick stroke (NOT colored glow)
- [ ] Corners genuinely dark; frame not uniformly milky
- [ ] P2 ≤ ~10 (true blacks present); brightest ~1% localized to top of hero bbox
- [ ] mean_sat > ~0.55; ≤ 2 dominant hues
- [ ] If the hero art is already self-lit, procedural light layers are minimal (no double-exposure)

---

## How to measure (the metrics that are worth computing)

PIL + numpy on any candidate. The trustworthy ones:

- **luma** = `rgb @ [0.299, 0.587, 0.114]`.
- **Depth separation** — `mean(luma[hero_bbox]) / mean(luma[bg_ring_around_hero])`; want ≥ ~2.
- **Specular localization** — take the brightest 1% of pixels (`luma ≥ percentile 99`);
  what fraction fall inside the top 20% of the hero bbox? Want most of them; want NONE of
  them forming a large contiguous opaque blob (check the largest connected component is
  small).
- **Squint** — downscale to ~1/16, threshold at e.g. 60% of max luma, count connected
  components; want ≈ 2 dominant ones.
- **Atmosphere** — local-contrast (std of luma in a sliding window) and saturation, measured
  in a BG patch vs a hero patch; BG should be lower on both.
- **P2 / mean_sat** — quick histogram guard-rails.

Note what NOT to over-weight: global **P98**, a fixed **corner/center vignette ratio**, and
rigid **area quotas**. They measure pixels, not hierarchy, and forcing them produced the
worst artifacts. Always end on the squint test, not a number.

---

## Rebuilding a flat promo as an editable layered PSD
When the deliverable is an editable master (per-layer PSD) but you only have a flat render,
decompose it first (see `art-generation.md` → "Decomposing a finished flat key-art"), then
composite keyed layers — opaque parts (gold/stone/logo) via magenta + `chroma_key`,
light/glow/smoke via black + luma-key on **screen**. Group as
`01_bg / 02_frame / 03_hero / 04_logo / 06_grade` and write the PSD with pytoshop (set the
merged `image_data` to the graded flatten so the PSD thumbnail matches the JPG).

The polish levers that actually moved an art-director score from 5 → 9.5 (priority order):
- **Ground the hero** — a hard, dark contact-AO ellipse where it meets the altar/base. A
  floating hero with no contact shadow reads as a 2-D sticker.
- **Restrain the hero's own glow + add a warm rim-light** — a flooded glow flattens volume;
  pull it back to an accent and rim-light the edges to separate hero from frame.
- **Separate the logo with a DARK backing** (plate / heavy multiply shadow), never a coloured
  glow — coloured outer glow bleeds into a bright BG and kills legibility at thumbnail size.
- **Gold = specular, not flat** — key the already-bright gold pixels and screen them back as
  hot white/pale-yellow edge highlights, and deepen the core contrast. Matte gold reads as clay.
- **Tie the magic light into the metal** — cyan rim-lights on the ring's inner lip and the
  altar top edge make separately-rendered assets share one 3-D space.
- **Lift background blacks but KEEP the vignette** — crushed-black architecture reads as a
  cutout; raise the shadows so pillars/statues read, keep the corners dark for focus.

## Art-director-in-the-loop (Gemini vision)
Use a vision model (`gemini-3.1-pro-preview`) as a brutal AD pass — but **context decides
signal quality**. Judging the tile alone, or against one image, is NOISY: scores swung
6.5 → 5.5 → 4.5 → 5 → 3 across genuinely *improving* builds, with theatrical wording. Stabilise it:
- Send the tile + the **real lobby grid** it will sit in + 2-3 **premium competitor tiles** +
  the **studio's own released promo** (house quality bar) in ONE request.
- State the **client constraints** up front (keep composition, keep crest size, no sparks,
  brand logo can't be redesigned) so it stops re-flagging locked decisions.
- Ask for "fair, concrete, consistent, no theatrics", ranked must-fixes only, a /10 and a ship
  call. With that framing it became consistent and reached SHIP at 9.5/10.
- **Trust your own eyes over a single noisy score** — verify each AD claim against the actual
  composite before acting (it once called a clearly-bolder logo "thin/condensed", and dropped
  the score 3 points on a logo swap while the rest was "locked & approved").
