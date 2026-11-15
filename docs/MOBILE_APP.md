# CTRL+SPACE as a mobile app

**APK / iOS:** build steps in [`NATIVE_BUILDS.md`](NATIVE_BUILDS.md) (cloud build via GitHub Actions, PWABuilder, or locally). The older `mobile/android/` scaffold was replaced by `mobile/capacitor/` (Android + iOS).


**v5:** the installed app now opens a dedicated mobile client at `/app` (28 screens, floating tab bar, onboarding, full-screen AI assistant). Architecture, feature status and the React Native decision: [`MOBILE_ARCHITECTURE.md`](MOBILE_ARCHITECTURE.md). Screen gallery: `docs/gallery/`.


CTRL+SPACE is an **installable mobile app (PWA)**: it installs onto the home screen, opens full-screen with its own icon and launch screen, uses a bottom tab bar, and keeps reports and experiments you have opened available **offline**. The research server (Python) still has to run somewhere the phone can reach.

## What was tested (Chromium, Pixel 7 device profile)

`python e2e/pwa_test.py BASE_URL` — Chromium's own installability check returns **no errors**; the manifest parses cleanly; the service worker controls the app; the tab bar navigates; offline, the app opens straight to a previously opened report with an offline banner; a never-opened report shows an honest error; back online, everything reloads. Personal, account and admin data are never cached, and cached research data is cleared on sign-out.

**Not tested here:** installing on a physical phone or an Android emulator, and building an APK (no Android SDK or internet in the build environment).

## Option 1 — Install from the browser (fastest, no build)

Chrome only installs apps from **HTTPS** addresses (or localhost). So the phone needs an HTTPS address for the server:

- **Hosted:** deploy as in `docs/DEPLOYMENT.md` and open `https://your-domain`.
- **For a demo from your laptop:** run `python run.py serve`, then expose it with an HTTPS tunnel, e.g. `cloudflared tunnel --url http://localhost:8000` or `ngrok http 8000`, and open the `https://…` address it prints on the phone.

Then: **Android (Chrome):** menu ⋮ → **Install app**. On Android, Chrome turns this into a real installed app (it appears in the app drawer and app settings). **iPhone (Safari):** Share → **Add to Home Screen**.

## Option 2 — Android APK from the PWA, no code (PWABuilder)

With the HTTPS address from option 1, go to pwabuilder.com, enter the address, choose **Android → Generate package**. You get a signed `.apk` to install for testing and an `.aab` for Google Play. This wraps the same app as a Trusted Web Activity.

## Option 3 — Native Android shell (Capacitor), in `mobile/android/`

Requires Node.js 18+ and Android Studio. **Untested scaffold.**

1. Put your server’s HTTPS address in `mobile/android/capacitor.config.json` → `server.url`.
   (For a laptop on the same Wi-Fi you can use `http://192.168.x.x:8000` and set `"cleartext": true`; never ship that.)
2. `cd mobile/android && npm install && npm run add-android && npm run sync && npm run open`
3. In Android Studio: **Build → Build App Bundle(s) / APK(s) → Build APK(s)**, or press Run with the emulator selected.

## iPhone

Option 1 (Add to Home Screen) works on iPhone. A native iOS build would need a Mac with Xcode (`npx cap add ios`); not prepared here.
