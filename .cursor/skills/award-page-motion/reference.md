# Award page motion — recipes

Implement from the thesis in SKILL.md. These are the patterns, not a brand kit. Keep the product's type, color, and copy. Reuse the timing and structure.

House curve: `cubic-bezier(0.22, 1, 0.36, 1)`.

## Scroll engine

```tsx
// Spacer is the only in-flow height. Layers are fixed.
// height = 1vh hero cover + inner max scroll + 1vh outro (+ a little slack).
const update = () => {
  const y = window.scrollY;
  const vh = window.innerHeight;
  const panelY = Math.max(0, vh - y);
  panel.style.transform = `translate3d(0, ${panelY}px, 0)`;
  wrap.style.transform = `translate3d(0, ${-Math.max(0, y - vh)}px, 0)`;
  stage.style.visibility = y >= vh ? "hidden" : "visible";

  for (const s of scenes) {
    const topVp = panelY + (-Math.max(0, y - vh)) + s.top;
    const pinRange = Math.max(0, s.h - vh);
    const pinOffset = Math.min(Math.max(-topVp, 0), pinRange);
    s.pin.style.transform = `translate3d(0, ${pinOffset}px, 0)`;
    const sp = pinRange ? pinOffset / pinRange : 1;
    s.el.style.setProperty("--sp", sp.toFixed(4));
    const fadeIn = Math.min(1, Math.max(0, (vh * 0.9 - topVp) / (vh * 0.45)));
    const exitP = Math.min(1, Math.max(0, (-topVp - pinRange) / (vh * 0.4)));
    s.pin.style.opacity = String(Math.min(fadeIn, 1 - exitP));
  }
};
gsap.ticker.add(update);
```

Scene CSS consumes the same variable:

```css
.ghost {
  transform: translate(-50%, calc(-50% + (0.5 - var(--sp, 0.5)) * 12vh));
}
.verb {
  letter-spacing: calc(0.06em - clamp(0, var(--sp, 1) * 2.2, 1) * 0.09em);
}
```

A demo timeline scrubs from `--sp` and never plays on its own:

```tsx
const sp = parseFloat(scene.style.getPropertyValue("--sp") || "0");
tl.progress(Math.min(1, Math.max(0, (sp - 0.04) / 0.9)), false);
```

Card scale from overlap, not from a mount tween. `s = 0` fully offscreen; ramp in over ~0.6vh and out over ~0.4vh. Reduced motion forces `1`.

Coalesce measure:

```tsx
let raf = 0;
const schedule = () => {
  cancelAnimationFrame(raf);
  raf = requestAnimationFrame(measure);
};
const onResize = () => {
  if (coarse && window.innerWidth === lastW) return;
  lastW = window.innerWidth;
  schedule();
};
```

Chrome fade starts after ~0.12vh and finishes ~0.45vh into the panel. When `scrollY` returns to 0 after being positive, clear inline opacity and `inert` once.

## Video as material

Palindrome: two muted videos. On forward `ended`, hide it, show reverse, `currentTime = 0`, `play()`. Swap back the same way.

Cipher pass, only while `0 < scrollY < 1vh`:

```tsx
const p = Math.min(1, scrollY / (vh * 0.85));
if (p <= 0.02) { ctx.clearRect(0, 0, w, h); canvas.style.opacity = "0"; return; }
const eased = p * p;
const cols = Math.max(14, Math.round(150 - eased * 136));
const rows = Math.max(8, Math.round((cols * canvas.height) / canvas.width));
// cover-crop the live video into a cols×rows buffer, then:
ctx.imageSmoothingEnabled = false;
ctx.drawImage(buffer, 0, 0, cols, rows, 0, 0, canvas.width, canvas.height);
canvas.style.opacity = String(Math.min(1, (p - 0.02) / 0.18));
```

Leading edge of the next panel: a second canvas drawn at cell resolution (`image-rendering: pixelated`), alpha rising with row², a few accent cells from a stable hash. Redraw on a coarse step (~130ms) while the edge is on screen so the dither lives. Anchor the canvas to the panel's top.

Stable hash (same cells every frame for a given seed):

```tsx
const hash = (a: number, b: number) => {
  const s = Math.sin(a * 127.1 + b * 311.7) * 43758.5453;
  return s - Math.floor(s);
};
```

## Scramble

```tsx
const GLYPHS = "█▓▒░•§#%¤";
function scrambleTo(el: HTMLElement, target: string, reduced: boolean) {
  if (reduced) { el.textContent = target; return; }
  let frame = 0;
  const total = 11;
  const id = window.setInterval(() => {
    frame++;
    const n = Math.floor((frame / total) * target.length);
    let out = "";
    for (let i = 0; i < target.length; i++) {
      out += i < n ? target[i] : GLYPHS[(Math.random() * GLYPHS.length) | 0];
    }
    el.textContent = out;
    if (frame >= total) { clearInterval(id); el.textContent = target; }
  }, 38);
}
```

Ignore a new target when it equals the last one, unless the string is a live counter (then write through only while no interval is running). Censor direction is the opposite walk: resolved prefix becomes glyphs.

## Seam card

Footprint is fixed (`aspect-ratio` of a real card, perspective on the outer box). The rotating face is an inner element.

```css
.card { position: absolute; inset: 0; border-radius: 16px; overflow: hidden;
  transform: rotateX(9deg) rotateY(-8deg); }
.face { position: absolute; inset: 0; transition: clip-path 0.5s cubic-bezier(0.22, 1, 0.36, 1); }
.face-a { clip-path: polygon(0 0, calc(100% - 3px) 0, 0 calc(100% - 3px)); }
.face-b { clip-path: polygon(100% 3px, 100% 100%, 3px 100%); }
.doors:has(.face-a:hover) .face-a { clip-path: polygon(0 0, 138% 0, 0 138%); z-index: 2; }
.face.filling { z-index: 3; transition: clip-path 0.55s cubic-bezier(0.7, 0, 0.2, 1); }
.face-a.filling { clip-path: polygon(0 0, 300% 0, 0 300%); }
```

Specular band on the card, driven by the tilt handler:

```css
.card::after {
  content: "";
  background: linear-gradient(115deg, transparent 42%, oklch(1 0 0 / 0.14) 49%, transparent 63%);
  transform: translateX(calc(var(--shine, 0) * 1%));
}
```

Tilt (fine pointer, not reduced motion):

```tsx
const rx = gsap.quickTo(card, "rotationX", { duration: 0.5, ease: "power3.out" });
const ry = gsap.quickTo(card, "rotationY", { duration: 0.5, ease: "power3.out" });
const sh = gsap.quickTo(card, "--shine", { duration: 0.5, ease: "power3.out" });
// nx, ny in [-0.5, 0.5] from the card box
rx(REST_X + ny * 14);
ry(REST_Y - nx * 16);
sh(-(nx + ny * 0.4) * 34);
```

Feature copy beside the card: rows start at `yPercent: 130` inside `overflow: hidden` and stagger to 0 (0.55s, `power3.out`, 0.06 apart). The title uses the scramble. The panel slot is reserved; do not mount/unmount it or the column jumps.

## Hover still outside the transformed wrap

```tsx
gsap.set(image, { xPercent: -50, yPercent: -50 });
const setX = gsap.quickTo(image, "x", { duration: 0.4, ease: "power3" });
const setY = gsap.quickTo(image, "y", { duration: 0.4, ease: "power3" });
// first enter: setX(clientX, clientX) snaps; later moves ease
```

The image element is `position: fixed` on a layer that has no transformed ancestor.

## Pixel object on a scrubbed timeline

Ambient spin uses wall-clock time. Materialize and glitch are values **inside** the paused timeline so they reverse:

```tsx
const fx = { mat: 0, glitch: 0 };
tl.to(fx, { mat: 1, duration: 0.4, ease: "power1.inOut" })
  .addLabel("flightStart")
  .to(fx, { glitch: 1, duration: 0.35 }, "flightStart")
  .to(fx, { glitch: 0, duration: 0.3 }, ">-0.3")
  .to(fx, { mat: 0, duration: 0.35, ease: "power1.in" });
```

Draw the hero object to an offscreen canvas, then copy cells whose hash is below `fx.mat`. At `mat >= 0.998`, blit the whole buffer. Glitch is a horizontal band tear plus a tinted echo, gated so it is not every frame.

Phone film mode: map timeline labels to three views. Each view's opacity is `min(enter, 1 - exit)` with a ~0.15s handoff. Do not overlap two views at partial opacity for long.

## Wave leave

```tsx
const NUM = 10;
const render = () => {
  paths.forEach((path, i) => {
    const pts = allPoints[i];
    let d = `M 0 ${pts[0]} C`;
    for (let j = 0; j < NUM - 1; j++) {
      const p = ((j + 1) / (NUM - 1)) * 100;
      const cp = p - (100 / (NUM - 1)) / 2;
      d += ` ${cp} ${pts[j]} ${cp} ${pts[j + 1]} ${p} ${pts[j + 1]}`;
    }
    path.setAttribute("d", d + " V 100 H 0");
  });
};
// timeline delay 0.35s, each point 0→0 with random delay ≤ 0.25s,
// second path offset by ~0.15s, duration 0.75, power2.inOut, onUpdate: render
// onComplete: navigate. pageshow persisted: fill points to 100, hide svg.
```

Particles: ~14 spans at the click point, random angle, distance 34–100px, gravity bias downward, scale and fade, 0.55–0.9s, remove on complete.

## Cursor gates

```tsx
if (!matchMedia("(pointer: fine)").matches || innerWidth < 1024) return;
```

```css
@media (pointer: fine) and (min-width: 1024px) {
  .cursor { display: block; }
  html, a { cursor: none; }
}
.cursor { mix-blend-mode: exclusion; transform: translate(-50%, -50%); }
.cursor.tag { mix-blend-mode: normal; } /* the pill must keep its fill */
.cursor.quiet, .cursor.suppress { opacity: 0 !important; }
```

A single pulse on the pill (`box-shadow` to 16px, ~1.5s) reads as "this is the button." No pulse under reduced motion.

## Type and color floor

- Paper and ink from OKLCH. Ink is a deep neutral, never pure black. One accent hue.
- Display: heavy weight, `letter-spacing` around `-0.03em`, line-height near 1.
- Eyebrows: 11–12px, tracking ~0.16–0.22em, uppercase.
- Chrome that must sit on both a light film and a dark panel: `mix-blend-mode: exclusion` with white, so one color reads on both. Do not blend type that must stay a true brand color (a partner mark, a video cutout).
- Oversized wordmark on the outro, `clamp` from a phone size to something that fills the row. Legal line stays small and quiet.

## Scattered grid

For `cols` columns, row `r` places an image at column `(r * 2 + r % 2) % cols`. Every third row places a second image two columns over. Remaining cells are empty. Captions for the left half sit to the right of the card; the right half, to the left, and those left-side captions align to the top so two captions never share a line. Under 640px, captions drop below the image.

## Outro

Footer is fixed, `translateY(100vh)` until the inner wrap has finished, then progress over the last viewport minus a small slack. `pointer-events` and `inert` flip only after progress passes ~0.55, so a barely visible footer does not steal clicks.

A quiet ambient band (dot gradients on a wide repeating layer, linear 18s) sits at the top of the outro. Pause that animation under reduced motion.
