---
name: award-page-motion
description: >-
  Use when building, redesigning, or critiquing a landing page, hero, or marketing
  site that must feel award-level: scroll-scrubbed scenes, full-bleed video, page
  leave transitions, custom cursors, hover artifacts, or microinteractions tied to
  a product metaphor. Use when motion is generic fade-ups, bounce easing, a pinned
  template, or an "Awwwards clone" and the bar is a reversible, breath-catching,
  reduced-motion-safe choreography.
---

# Award Page Motion

## Overview

The page is a short film. Scroll is the playhead. Every moving thing speaks one product metaphor, and the film plays backward if the visitor scrolls up. Decoration that does not carry that metaphor is cut.

This is the maximum bar extracted from a production scroll film (palindrome video, cipher mosaic, pinned scenes, seam-hover card, cursor-as-control, wave leave). Component-level springs and timing vocabulary live elsewhere. This skill decides what earns a place on the page and how the stage is built.

## When to use

- A landing, launch, or brand page where the first scroll should feel authored.
- Scroll-linked video, pinned scenes, oversized type, or a demo that plays with the scrollbar.
- A leave / route ceremony, a custom cursor, or hover that reveals an artifact.
- A review that asks why a page feels like a template.

**Do not use** for app chrome, settings, tables, or controls people hit all day. Those want short, interruptible feedback (`emilkowalski/skills` — `improve-animations`, `review-animations`). Do not use `gsap-awwwards-website` or any skill whose body is "clone this brand template." Those install someone else's yogurt site. This skill is the craft, applied to the product in front of you.

ScrollTrigger API details: `greensock/gsap-skills` `gsap-scrolltrigger`. One authored moment inside a product UI: `pbakaus/impeccable` animate. Name a motion you can see but cannot call: `animation-vocabulary`.

## Write the thesis before any tween

Five lines, in the code or the PR, before implementation:

1. **Metaphor** — one sentence the motion is proving (conceal, reveal, weight, speed, craft).
2. **Hero material** — the one surface that transforms (film, type, object, diagram).
3. **Playhead** — what scroll progress means in that metaphor.
4. **Ceremony** — the single click or arrival that gets a beat sequence.
5. **Still** — what `prefers-reduced-motion` shows instead (a resolved frame, not a blank).

If you cannot fill line 1, do not animate. Ship layout.

## The bar

A page clears the bar only when all of these are true:

- One metaphor shows up in at least three materials (for example film, type, and the leave), not as a single fade.
- Scrubbed motion is reversible. Scroll up undoes it. No one-shot `whileInView` on a scene the playhead owns.
- The hero is alive at rest (loop, idle, or film) and changes meaning as scroll begins. Rest is not a frozen poster unless reduced motion is on.
- Hover changes emphasis inside a fixed footprint. Position and size of the control do not change.
- The phone cut is a different edit: fewer scenes, one primary action, no hover-only information.
- Reduced motion shows the story's resolved still: readable type, final scale, poster frame. Meaning stays; travel leaves.
- Covered, faded, or offscreen layers stop costing paint and stop taking clicks (`visibility`, `inert`, `pointer-events`).
- Jumping to the top (Home, `scrollTo(0)`) restores chrome in one frame. Back-forward cache restores a leave overlay to hidden.
- Keyboard focus is visible. Anything faded past usefulness is `inert`.
- The scroll loop writes `transform` and `opacity` only.

## Stage model

All visible layers are `position: fixed`. A spacer element is the only in-flow box, and its height is the film's duration. A single ticker reads `scrollY` and writes the stage. Do not pin every section with its own ScrollTrigger. Pins inside a transformed parent, and mobile URL-bar resizes, will fight you.

```
spacer height = hero travel + inner scroll + outro travel
hero layer    fixed, hidden once fully covered
panel layer   fixed, y = viewport − scroll, then 0
inner wrap    translate3d by the leftover scroll
scene pins    100vh stages inside tall sections
outro         fixed, slides up over the last viewport
```

Expose scene progress as a CSS variable `--sp` (0 at pin start, 1 at pin end). CSS may use it (`letter-spacing`, ghost drift). A paused GSAP timeline may set `tl.progress(sp)`. One variable, two consumers, both reversible.

Measure on resize with a coalesced `requestAnimationFrame`. On `(pointer: coarse)`, ignore height-only resizes so the URL bar does not rebuild the scrub. Call `ScrollTrigger.config({ ignoreMobileResize: true })` if ScrollTrigger is loaded. Re-measure when fonts finish loading and when a `ResizeObserver` sees the inner wrap change.

**Ease law.** Scrub is `ease: "none"` — the scrollbar is the curve. Gestures use `cubic-bezier(0.22, 1, 0.36, 1)` (GSAP `power3.out`) for 0.4–0.55s. Travel that is already on screen uses `power2.inOut`. Never bounce, elastic, or overshoot on a marketing page. Ambient loops (marquees, rail stripes) are linear and paused under reduced motion.

## What earns a scene

| Job | Treatment | Reject |
|---|---|---|
| Hero | Full-bleed material + one composed type block + one control | Stock gradient, three equal CTAs, fade-up headline |
| Proof | A scrubbed object that enacts the metaphor | Autoplay video with no scroll link, or a feature grid of icons |
| Gallery | Scale tied to viewport overlap, captions in the empty cell beside the image | Masonry that fades in once |
| Statement | One line, pinned, huge | A paragraph pinned for a viewport |
| Steps | One viewport each on desktop; one stacked screen on phones | Three identical fade-ups |
| Outro | A slide that covers the film; wordmark at display size | A document footer after `margin-top` |

Between proof scenes, give the eye air. Empty cells are part of the layout. Captions sit in that air and fade with the image, not on top of it.

## Microinteractions

Each one is a state change with a reading, not a decoration.

- **Decrypt / censor type.** Unresolved characters are a fixed glyph set (`█▓▒░•`). Resolve left to right over 8–14 frames at ~34–42ms. Same driver for reveal and hide. Skip the interval under reduced motion and set the final string. Use tabular figures wherever digits change.
- **Seam hover.** Two regions share one fixed card. Hover moves a `clip-path` seam so the hovered side claims area. The other side's label fades. Click floods the clip to cover the card, then the leave ceremony runs. Rounded corners live on the wrapper; clip-paths cannot round them.
- **Tilt.** `rotateX` / `rotateY` via `quickTo` (~0.5s, `power3.out`) around a resting pose. A specular `--shine` slides opposite the tilt. The element's box on the page never changes.
- **Cursor.** Desktop fine pointer only, at `min-width: 1024px`. Default: small mark, `mix-blend-mode: exclusion`. Over a link: slight scale. Over the hero control: the cursor *becomes* the label (pill, pulse once). On commit: that label censors. If a hover image is the feedback, suppress the cursor. If the changing text is the feedback, make the cursor quiet so it does not cover the type.
- **Hover still.** The image that follows the pointer must live in a fixed layer that is **not** inside a transformed ancestor (`transform` on a parent makes `position: fixed` local). On enter, jump to the pointer, then `quickTo` (~0.4s). Fade in ~120ms linear. Gate on `(pointer: fine)` and no reduced motion.
- **Origin.** A card scaling in uses `transform-origin` toward the empty side, so it grows into the air rather than out of the caption.

Hover-only content needs a non-hover path: touch toggles, or the information is also in the page.

## Video

- One film, two files if needed: forward, then the same film reversed. Swap on `ended`. No jump cut, no crossfade dip to black.
- `muted playsInline`. Reveal the stage on `loadeddata`, on `error`, or after ~2.5s so Data Saver still shows the poster.
- Reduced motion: do not call `play()`. Poster frame only.
- Scroll treats the frame as a material. Sample the current video into a small buffer, draw it back with `imageSmoothingEnabled = false`, and increase cell size with eased progress. Mix in a few palette cells so the image becomes unreadable as the next scene covers it. Stop the loop when progress is ~0 and when the hero is fully covered.
- Cap device pixel ratio (about 1.25 on fine pointers, 1 on coarse).
- When the hero is covered, set the stage `visibility: hidden`.

## Leave ceremony

Order is the craft. Do not navigate on the same frame as the click.

1. Immediate: the control commits (clip flood, label censors). Modifier-clicks (`meta`, `ctrl`, `shift`, `alt`, middle button) skip the ceremony and use the real link.
2. ~0–0.6s: a small burst from the click point (a dozen particles, `power2.out`, removed on complete).
3. ~0.35s after the event: the overlay wave starts, so the burst is readable.
4. Wave completes, then `location` changes.

Wave shape: an SVG of a few paths in a `0 0 100 100` viewBox, `preserveAspectRatio="none"`. Each path's top edge is N control points tweened from 100 to 0 with small random delays; rebuild the cubic `d` on every tick. A pale path leads; a deeper path covers. Two paths are enough.

On `pageshow` with `event.persisted`, reset the overlay to hidden and clear "leaving" latches. Otherwise Back shows a stuck cover.

Dispatch one window event for "leave" so the cursor, the doors, and the wave share a clock.

## Phone cut

At a narrow breakpoint, do not scale the desktop film down.

- Collapse multi-step scenes into one screen.
- Replace a multi-region hover control with one real button.
- Turn a horizontal scrubbed demo into sequential full-screen acts. Hand off with a short fade **in series**. Never crossfade two acts: a parked scrub would show two ghosts.
- Hover panels, custom cursors, and pointer-following stills do not exist here.
- Give a long scrub more scroll distance, not faster motion.

## Accessibility and performance

- `prefers-reduced-motion: reduce`: poster instead of film, scene opacity 1, card scale 1, no scramble intervals, no particle burst, no cursor, no marquee. Keep color and state changes that carry meaning.
- Faded chrome: `opacity` plus `inert` (and `pointer-events: none` on overlays) once it is no longer the target. Restore attributes when scroll returns to the top.
- One `h1`, visually hidden if the display type is duplicated for art.
- Focus-visible outlines on controls. The seam hover's `:focus-visible` matches `:hover`.
- `will-change` only on layers that move every frame (`transform`, `opacity`). Remove it under reduced motion.
- Do not animate `width`, `height`, `top`, `left`, `margin`, or `box-shadow` on the ticker.
- Pause videos and cancel the ticker on cleanup.

## Build order

1. Thesis (five lines).
2. Tokens: one paper, one ink that is not `#000`, one accent. OKLCH. Display type is heavy, tight tracking, few sizes.
3. Spacer + ticker skeleton with a fake panel slide. Prove reverse scroll and top-restore before art.
4. Hero material and its scroll degradation.
5. Scenes fed by `--sp`.
6. The one ceremony.
7. Pointer and phone gates.
8. Reduced-motion pass as a separate edit, not a media query sprinkled at the end.

## Rationalizations

| Excuse | Reality |
|---|---|
| A fade-up on scroll is the modern look | Every template ships it. It does not prove the metaphor. |
| I'll ScrollTrigger-pin each section | One ticker, one spacer, `--sp`. Separate pins fight transformed parents and the mobile URL bar. |
| Bounce feels premium | It dates the page. House curve is `cubic-bezier(0.22, 1, 0.36, 1)`. Scrub stays linear. |
| The card should grow on hover | The footprint never moves. Emphasis is clip, opacity, tilt, tracking. |
| A custom cursor on the whole site | The cursor becomes the control, or it steps aside. A blob that hides the pointer is costume. |
| Mobile is the desktop shrunk | Phones get another cut. Hover-only story does not exist. |
| Reduced motion means delete the scene | Show the resolved still. The story stays readable. |
| Crossfade the mobile acts | A parked scrub shows two half-opacity layouts. Hand off in series. |
| `will-change` on the page | Only the moving layer. Hide the hero once it is covered. |
| Clone an Awwwards recreation | That copies another brand's chapters. Write this product's thesis. |
| Navigate immediately on click | The ceremony needs beats. Wait for the wave's `onComplete`. |
| `whileInView` once is fine for the demo | The demo is on the playhead. It must scrub backward. |

## Before you call it done

- Scroll down and back up: every scrubbed value returns.
- Home key at the bottom: chrome opacity and `inert` reset once.
- Emulate `prefers-reduced-motion`: film paused on poster, type final, no intervals.
- Emulate a coarse pointer at 390px: no cursor, no hover-only copy, one primary action.
- Trigger Back after a leave: overlay is gone.
- Throttle CPU and scroll: no layout properties in the ticker; covered video is `visibility: hidden`.

Recipes (cipher sample, `--sp` pin, seam card, wave, scramble, hover still) are in [reference.md](reference.md). Read only the section you are implementing.
