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

## Compositing layers so elements DETACH from the bg (physical-light recipe)

The #1 reason an AI-asset promo reads as a flat "sticker behind a film" is the
COMPOSITING, not the assets. A pile of `screen` glow layers + 2D drop-shadows +
360° rim looks like a Photoshop applique. Real depth comes from simulating light.
Battle-tested recipe (PIL/numpy), layer order bottom→top:

1. **Bake the vignette INTO the background**, never over the whole flatten at the
   end (a final vignette darkens the logo corners → instantly cheap). Drop the
   "+lift blacks" trick — lifting bg blacks puts a light hero on a light bg = flat.
   `bgvig = clip(1 - 0.46*clip(r-0.34)/0.66)`; `bg[...,:3] *= bgvig`.
2. **Cast shadows = MULTIPLY, doubled** (not normal-blend grey). Contact: `dy≈0.6%`,
   `blur≈0.6%`, opacity ~150. Ambient: `dy≈2-3%`, `blur≈2.5%`, opacity ~90.
   A shadow that lands on a receiver (book→pedestal) must be **masked by the
   receiver's alpha** (`shadow_alpha *= recv_alpha/255`) or it floats in the air.
3. **Light wrap** instead of a dark separation halo (never put dark mud over a
   backlit center): take the object's inner edge band (`alpha - MinFilter(alpha)`),
   blur it, multiply by the **blurred background**, `screen` over the object. The
   bright bg now bleeds onto the rim → the ring stops being a sticker.
4. **Directional rim**, not 360° stroke. Shift the alpha and subtract:
   `rim = clip(alpha - roll(alpha, dy), 0,255)` → lights only the top edges (light
   from above/center). MaxFilter-dilate rim = inside-stroke = sticker look.
5. **Local glow on stone = color DODGE, not screen.** Screen glow milks the black
   point (stacking 4+ screens = grey haze under the title). A `multiply` dark pool
   under the logo + a `dodge` colored radial paints the stone cyan/warm without
   washing it. (`dodge`: `base / (1 - clamp(blend*a, 0, .996))`.)
6. Final grade = contrast + saturation + slight gamma ONLY (vignette already in bg).

flatten() needs `multiply` (`base * ((rgb/255)*a + (1-a))`) and `dodge` blends.
For PSD export map `dodge → linear_dodge` (fallback screen).

This single refactor moved a "behind a film" 1:1 master from murky to genuine depth
in one pass. Diagnosed by asking a vision model to read the assembler SCRIPT + the
layers (see below).

## Using a vision model as art director (and its trap)

Send the rendered promo + the cut layers (+ optionally the assembler script text)
to `gemini-pro` via `openrouter_image.query_image(prompt, images)` for a critique.
Two hard-won caveats:

- **The score is frame-of-reference dependent and noisy.** The SAME file scored
  9.5/10 ("ship it") when judged inside a real lobby grid of mass-market slots, and
  4–5/10 when judged against hand-painted tier-1 refs — in the same session. Pin the
  comparison set deliberately and tell it which bar to use.
- **Compare against YOUR OWN studio's released promo**, not just Pragmatic top-3.
  That makes the critique concrete (custom lettering on a drawn plate, hand-painted
  rendering, multi-plane depth) and separates "needs better ASSETS / overpaint" from
  "needs better compositing". Compositing has a ceiling; past it the gap is the
  AI-generation vs digital-painting quality, which the assembler can't close.

## Baking light onto a bg AT the element positions (two-reference gen)

To regenerate a background that already carries the glow/shadows the foreground
elements would cast, pass **two** reference images in one generation call: the
current bg AND the final composited promo. `generate_image` only takes one ref, so
POST the chat/completions payload yourself with two `image_url` parts before the
text (same shape as `query_image`). Prompt: "image 1 is the bg, image 2 shows where
the ring/book/title sit — emit ONLY the environment with light radiating from where
the book is, bake the halo/spill at those positions, no book/ring/title drawn."
Removing wall torches + a clean white center burst this way beat any procedural glow.

## Keying a logo/text off a solid bg at full res (flood-fill, keep largest CC)

remove.bg caps free output (~600px). For a logo generated on solid white OR black,
key full-res yourself: flood-fill the bg from the border on a "flatness" mask
(`min>230 & sat<22` for white, `max<45` for black), then **keep only the largest
connected foreground component** (`scipy.ndimage.label`) — this drops detached
sparks/embers the model sprinkles in. `MinFilter` erode the alpha a few px to thin
a too-thick outline. Auto-detect bg color from the corners' mean. Sparks baked
ON TOP of the letters can't be removed this way — regenerate without them.

## nano-banana-pro foggy-washout failure

Beyond the "no image data" miss, `nano-banana-pro` sometimes returns a real image
that is a **washed-out foggy smear** (subject barely visible, ghosted, low
contrast). Same fix: retry (it is stochastic — the identical prompt succeeds on the
next call). Cheap detector before using the output:
`black_frac = (rgb.min(2) < 25).mean()` and `mean = rgb.mean()` — a proper
black-bg render has `black_frac ≳ 0.5`; a foggy fail is `mean ≳ 150`, `black_frac ≈ 0`.

## One parametric assembler for ALL promo resolutions (don't hand-tune each)

A full promo set is 30+ sizes (icons, square, portrait, landscape, ultra-wide
banners). Do NOT write a hard-coded canvas per size. Write ONE canvas-agnostic
`build()` that reuses the physical-light pipeline above, and pick geometry from a
`layout(ar)` function that buckets by **aspect ratio**:

- `ar ≥ 2.3` → **beside**: monument left (cx≈0.26), logo right (cx≈0.66). The
  tier-1 standard for wide banners — two masses split the bar 50/50, no dead zones.
- `1.9 ≤ ar < 2.3` (≈2:1) → **centered**: monument centered + grounded, title band
  below. Works only here; on wider it leaves side voids.
- `ar < 0.85` portrait / `0.85–1.25` square / `1.25–2.3` landscape → **stack**:
  monument centered, logo under it.

Each bucket returns a dict of fractional params: `MX, LX` (monument/logo x), `FCY,
FH, FMAXW` (frame center-y, height-frac, max-width cap), `ring_dy/book_dy`,
`logo_cy/logo_w`, `book_h, glow_h`, `smile` (logo arc depth), `backlight`, `zoom`.
All glow radii in **pixels derived from the placed monument height** (`rpx =
0.42*fhpx`) so circles stay circular at any AR. `place_fit` anchors the monument by
height with a width cap. Render time ~1 min for 33 sizes. Validate a few extremes
(tiny beside, vertical portrait, 2:1) before the full sweep.

**Ask the vision model for the LAYOUT verdict, not just the look.** It correctly
called: ultra-wide → beside beats centered; a single-LINE title is unreadable on a
1600–1920px-wide band (becomes a subtitle ribbon); keep the title 2 lines for CTA
mass on every format. "Centered + grounded" altar is good everywhere; "title in one
line" is the part to reject.

## The vignette must NOT touch the foreground (isolate it)

The baked bg vignette is centered on the canvas. In **beside/centered** layouts the
monument sits OFF-center → it falls in the vignette's dark periphery and reads dim,
even though its own pixels are unchanged. Proof: measure the frame layer pre-composite
— it's byte-identical between layouts (e.g. mean 125.1 vs 125.2); the dimming is NOT
the metal. Two real causes & fixes:

1. **`light_wrap` samples the vignetted bg.** Off-center → it samples the dark edge →
   no bright edge bleed → the monument looks flat. **Fix: feed `light_wrap` a SEPARATE
   non-vignetted (bright) copy of the bg** (`bg_for_wrap` snapshotted BEFORE `bg *=
   bgvig`). Never widen/move the vignette to "brighten" the monument — that's treating
   the symptom; isolate the foreground from the vignette instead.
2. **Missing backlight.** A centered hero gets a bright back-glow from the bg's center
   light; an off-center one doesn't. **Add an isolated warm backlight bloom BEHIND the
   ring** (screen, samples nothing from the bg): `rg(MX, fcy-0.05, fhpx*0.55, gamma=2.2,
   op≈150)`. Keep it TIGHT (high gamma, ~0.55 radius) — a soft wide one (gamma 1.45,
   0.82 radius) is "cotton fog", an art-director red flag.

## Gold/metal specular: SCREEN warm, never DODGE white (the "lava" blowout)

A DODGE specular with a low threshold and white colour blows gold rings to molten
white ("золото пересвечено лавой"). DODGE is `base/(1-blend)` → explodes past 255 and
erases the metal's tone. Correct premium-metal specular:
`spec_a = clip((Lf-170)/50)` (only the brightest rim peaks), colour **`(255,215,120)`
warm gold not white**, `* 0.45`, blend **`screen` not dodge**. Brightness is held by
luma + backlight, NOT by a blown highlight — you can kill the blowout and keep the glow.
Likewise keep metal `contrast ≤ ~1.08` (1.18 pushes mids to clip) with `gamma 0.95`
to deepen shadows.

## The final gamma-lift in flatten() is the "milky / behind-a-film" culprit

If the whole composite looks greyish/foggy with no deep blacks, the usual cause is a
**final `255*power(base/255, 1/1.06)` in `flatten()`** — it raises the black point
across the assembled image. **Delete it.** Carry contrast with `(base-128)*1.10+128`
instead. Two siblings: (a) don't `*1.08` the bg base — it flattens corridor shadow
depth; (b) an atmosphere/haze `screen` layer must be WEAK (multipliers ~0.15/0.12/0.10,
not ~0.32) or it veils the whole scene grey.

## Magical SFX / glow goes BEHIND the ring, not screened on top

A portal vortex / energy swirl `screen`-ed ON TOP of the gold ring kills the ring's
inner-edge contrast and geometry. Place the keyed-on-black SFX (and its core radial)
**before** the frame layer so the opaque ring sits in front of it (the portal opening
is transparent → the glow shows through the hole, the gold occludes the rest). Same for
"ground/contact": an element that looks pasted onto a darker bg needs a MULTIPLY
contact-shadow AO under its base, its lower edge darkened, and a **cyan reflection from
the portal onto the ring's inner rim + the floor** to tie the colour temperature
together — otherwise warm hero on cool bg reads as two different scenes.

## Re-skinning a chroma-key asset via gen: forbid baked radial light

When regenerating a magenta-bg key asset (e.g. strip glyphs off a gold ring, keep the
texture), the model loves to bake a glow/halo/rim onto the magenta around the subject —
which **contaminates the chroma key** (the glow blends into magenta → ragged cut).
Prompt explicitly: "DO NOT create ANY radial light sources, glow, halo, bloom, rim-light
or haze — ONLY the <material> texture (self-shading ON the surface) and FLAT uniform
solid magenta #FF00FF right up to the edges." Validate with `magenta_frac = ((r>200)&
(b>200)&(g<120)).mean()` (want ≳ 0.5+). **Send the final master render (raw, un-keyed,
no preprocessing) as a SECOND reference** so the model matches the scene's light
direction/highlights and the re-skin drops back in seamlessly. Always regen to a
`_candidate.png`, eyeball it, back up the old asset, then swap.

## Reviewing MANY renders at once → ONE contact sheet, not N images

Sending ~33 separate images to `query_image` overflowed the vision model: it burned the
whole budget on reasoning tokens and returned **empty text** (`Vision model returned
empty text`). Fix: compose the set into ONE labelled **contact sheet** (e.g. 6×6 tiles,
each captioned `#n WxH`) and send that single image. The model then critiques the set
**as a set** (consistency, which formats are weakest) — which is what you actually want.
