# Building the Android APK and the iOS app

**Status:** no APK or iOS app was built in the original build environment (no internet, no Android SDK or Gradle, no macOS/Xcode). Everything below is prepared so the builds take a few clicks elsewhere. The project and workflows are untested until their first run.

The native apps are **Capacitor shells** (`mobile/capacitor/`): a real Android/iOS app with the CTRL+SPACE icon and splash screen that opens the mobile app at `https://<your-server>/app`. The research server (Python) must be running and reachable over **HTTPS**, because the data, accounts and AI live there.

## Step 0 — Give the server an HTTPS address

- **For a demo from your laptop:** `python run.py serve`, then `cloudflared tunnel --url http://localhost:8000` (or `ngrok http 8000`). Copy the `https://…` address it prints. It changes each time you restart the tunnel, so rebuild the app or use a fixed hosted address for the competition.
- **Hosted:** deploy as in `docs/DEPLOYMENT.md` and use your domain.

## Option A — Build in the cloud with GitHub Actions (no installs)

1. Create a GitHub repository and upload the contents of `CTRL_SPACE_FINAL_PROJECT.zip` (the `ctrl-space` folder must be the repository root, so `.github/workflows/` is at the top).
2. **Android APK:** Actions → **Build Android APK** → *Run workflow* → paste your `https://` server address → wait about 5–10 minutes → open the run → download **CTRL-SPACE-android-apk** → unzip → `app-debug.apk`.
   Install: copy it to an Android phone and open it (allow "install unknown apps" for your file manager or browser).
3. **iOS:** Actions → **Build iOS app** → *Run workflow* → same address → download **CTRL-SPACE-ios-simulator**.
   This runs in Xcode’s iOS Simulator on a Mac (drag `App.app` onto a running simulator). It **cannot** be installed on a real iPhone: see “Real iPhones” below.

## Option B — PWABuilder (no code, Android and iOS packages)

Go to pwabuilder.com, enter `https://<your-server>/app`, then:
- **Android → Generate package:** a signed `.apk` for testing plus an `.aab` for Google Play.
- **iOS → Generate package:** an Xcode project; building and signing it still requires a Mac.

## Option C — Build on your own computer

Requirements: Node.js 18+; Android Studio (Android); a Mac with Xcode 15+ and CocoaPods (iOS).

```bash
cd mobile/capacitor
# put your https address + "/app" in capacitor.config.json → server.url
npm install
npm run android        # creates android/, generates icons and splash
npm run apk            # → android/app/build/outputs/apk/debug/app-debug.apk
npm run ios            # Mac only: creates ios/
npx cap open ios       # opens Xcode → choose your iPhone → Run
```

## Real iPhones

Apple only allows signed apps on real devices:
- **Free, your own phone:** Xcode with a personal Apple ID (Signing & Capabilities → Team). The app expires after 7 days.
- **Team testing (TestFlight) or App Store:** Apple Developer Program (US$99/year), then Product → Archive in Xcode.
- **No Mac at all:** install the web app from Safari (Share → Add to Home Screen); it opens full-screen like an app.

## Release builds (Play Store)

The workflow produces a **debug** APK, fine for demos and judging. For Google Play, create a release keystore and run `./gradlew bundleRelease` with signing configured, or use PWABuilder’s `.aab`.

## What the native shell does and does not add

It adds an installable app icon, splash screen and app-store packaging. All features, offline reading, Arabic and the AI assistant come from the same `/app` code, so they behave as tested in the browser. Not verified: behaviour inside the Android WebView and iOS WKWebView on physical devices.
