# CTRL+SPACE wordmark & splash branding

Written 2026-11-14. Implements the two reference images supplied in chat (a dark wordmark lockup with red/blue corner-bracket accents, and a NASA-style poster of a burning hand against Earth's curve) into the mobile app's splash screen.

## What was actually inspected

The two reference images were pasted directly into the conversation, not provided as files — there is no mechanism available to this session to export a pasted chat image to disk, so the literal source files could not be copied into the repo. Two things followed from that:

1. **The wordmark** (thin geometric "ctrl + space", red plus sign, red top-left bracket fading to white, blue bottom-right bracket with a small floating blue plus) is simple enough to **recreate faithfully in CSS** — same structure, same two-tone bracket treatment, same colors — without needing the original pixels. This is what was built.
2. **The poster artwork** (realistic flame-hand, Earth curvature, starfield, meteor trails) is a detailed illustration that cannot be honestly hand-recreated from a description. Before asking the user to export it, the project's own existing assets were checked — `frontend/assets/hero.jpg` (added 2026-11-12, already in the repo and already precached by the service worker) turned out to be the **same artwork family**: an 880×880 painted poster of a burning hand reaching up in front of Earth's curve and a starfield, with a small "ctrl + space" wordmark baked into its own corner. It was already used, but only as a 132×132 cropped icon. This file was used as the real, full splash-screen background — no placeholder, no substitute image, no fabrication.

## Files changed

| File | Change |
|---|---|
| `frontend/app/index.html` | Splash markup: removed the small `.splash-logo` cropped-icon div, added a full-bleed `.splash-art` background layer; rebuilt the `.wm` wordmark markup with two corner-bracket elements (`.wmcorner.tl`, `.wmcorner.br`) and a floating accent plus (`.wmplus`), replacing the old single `.br` span. |
| `frontend/app/app.css` | New `.splash-art` rule (full-bleed `hero.jpg`, `background-size:cover`, a bottom-weighted dark gradient so text stays legible, a slow 12s zoom-in), `#splash` changed from center-aligned to bottom-weighted layout so the artwork reads clearly above the wordmark. Rebuilt `.wm`/`.wmcorner`/`.wmplus` rules: red (`#E8392B`) top-left bracket with a red→white horizontal fade, blue (`#287BFF`) bottom-right bracket, small floating blue plus — matching the reference wordmark's two-tone construction. Added `direction:ltr` to `.wm` (see bug found below). Removed the now-unused `.splash-logo` rule. |
| `frontend/sw.js` | `VERSION` bumped `v5.6.0` → `v5.7.0` so the changed shell files aren't served stale from cache. |

No backend, routing, or auth changes. No other screens touched — `.wm` was confirmed (via grep) to be used only on the splash screen, so this was a contained change.

## Onboarding → skip → browse without login

The prompt also asked to "add onboarding then skip to see the app without login or sign up." This was checked against the real app **before** assuming it needed building, and it already works end-to-end:
- First real visit → `boot()` in `main.js` redirects to `/app/welcome` (onboarding), confirmed live.
- Onboarding's Skip button → `finishOnboarding()` → `go(R.home, true)`, with no login redirect anywhere in that path.
- `vHome()` already renders a full guest experience when `S.user` is `null` (greeting, search, discover/ask/experiments/compare/saved chips, real stats, a "Sign in" / "Demo mode" card instead of saved items) — nothing gates the route itself.

Verified live with Playwright: fresh load → `/app/welcome` → click Skip → lands on `/app` with a guest home screen, no forced sign-in. No code change was needed for this part.

## Bug found and fixed while testing

Testing in Arabic (`dir="rtl"`) showed the wordmark itself flipping to read "space + ctrl" — the `.wm` flex row had no explicit text direction, so it inherited the page's RTL flow along with everything else. A brand lockup should never mirror reading order, so `.wm { direction: ltr }` was added. Re-verified: in RTL, every other string on the splash/onboarding screen is Arabic and right-to-left as expected, and the wordmark itself still reads "ctrl + space" left-to-right.

## Verified, not assumed

- Live Playwright screenshots at 375×667 (iPhone SE), 390×844 (default test viewport), 412×846 (Galaxy-class), and 1280×800 (wide/desktop browser window) — artwork fills the frame at every size with `background-size:cover`, wordmark stays legible, no clipping of either corner bracket.
- A first version left a faint ghost of the artwork's own baked-in "ctrl + space" bleeding through near the bottom edge, under the real wordmark — found by screenshot inspection, fixed by tightening the gradient overlay to reach full opacity earlier (78% down instead of 95%), re-verified it's gone.
- `getComputedStyle` confirms `.splash-art`'s `background-image` actually resolves to `/assets/hero.jpg` (not a broken reference), and 0 console/page errors on load.
- Full regression after the change: backend unaffected (no backend files touched); desktop E2E **19/19**; mobile app E2E **21/21** (including the dedicated "01 Splash: logo, tagline, backend check, then onboarding" case); Arabic RTL **5/5**; PWA installability **9/9** — all clean, 0 page errors.

## Not done

- The literal source pixels of the two pasted reference images were never available as files in this session, so nothing claims to be a pixel-identical export of them — the wordmark is a faithful CSS recreation, and the splash artwork reuses the project's own existing, matching `hero.jpg` asset rather than a new file. If an exact source file for either exists, saving it into `frontend/assets/` and naming the path would let it replace either piece directly.
- The desktop site (`frontend/`, non-`/app`) header was not touched — this pass was scoped to what the user pointed at (the mobile app's logo and splash screen), not a repeat of the earlier, separate "header wordmark placement" prompt that was asked about before any images had been supplied.
