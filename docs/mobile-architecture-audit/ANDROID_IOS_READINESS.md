# Android and iOS readiness

Read-only audit, 2026-11-14. No destructive commands run. One non-destructive diagnostic (`npx cap doctor`) was executed this pass; it only reads project state and prints a report — it does not modify files.

## Android

### Project structure — EXISTS, verified real

A generated native Android project exists at `mobile/capacitor/android/`, created by `npx cap add android` (per `mobile/capacitor/package.json`'s `"android"` script). Confirmed present: `app/build.gradle`, `build.gradle`, `settings.gradle`, `variables.gradle`, `capacitor.settings.gradle`, `gradlew`/`gradlew.bat`, `gradle/wrapper/`, `app/src/main/AndroidManifest.xml`, `app/src/main/java/com/ctrlspace/app/MainActivity.java`.

### Application ID / package configuration

- `applicationId "com.ctrlspace.app"` and `namespace "com.ctrlspace.app"` (`mobile/capacitor/android/app/build.gradle`), matching `capacitor.config.json`'s `appId`.
- `android:label="@string/app_name"`, launcher activity `.MainActivity`, `android:exported="true"`, `android:launchMode="singleTask"` (`AndroidManifest.xml`).

### SDK versions

From `mobile/capacitor/android/variables.gradle`:
| Setting | Value |
|---|---|
| `minSdkVersion` | 22 (Android 5.1) |
| `compileSdkVersion` | 34 |
| `targetSdkVersion` | 34 |

### Permissions

**Exactly one** permission declared in `AndroidManifest.xml`: `android.permission.INTERNET`. No camera, location, storage, notifications, or other permissions — consistent with the finding in `WEB_VS_MOBILE_ANALYSIS.md` that no native device-capability plugins are wired into the app.

### Network security configuration

No `network_security_config.xml` file exists in `app/src/main/res/`. Cleartext HTTP to the emulator-loopback address (`10.0.2.2`) is instead controlled by Capacitor's own `cleartext: true` config flag in `capacitor.config.json`, which Capacitor's build tooling applies at the native layer. This audit did not independently trace Capacitor's internal manifest-merge mechanism for that flag beyond confirming the flag is present in both the root config and the config baked into the built APK (`app/src/main/assets/capacitor.config.json`) — flagging this as a thing to re-verify if cleartext behavior is ever in question, rather than asserting a mechanism not directly inspected.

### Build variants / signing

Only a `release` build type block is declared (`minifyEnabled false`, default ProGuard files referenced) — no custom signing config in `app/build.gradle` (debug builds use Android's default auto-generated debug keystore, which is normal for a non-release build). **No release signing configuration exists yet** — required before a real Play Store submission, not required for development/testing.

### Gradle dependencies

Standard Capacitor 6 Android dependency set: `androidx.appcompat`, `androidx.coordinatorlayout`, `androidx.core:core-splashscreen`, the generated `capacitor-android` and `capacitor-cordova-android-plugins` modules, plus JUnit/Espresso test dependencies (unused — see below). No custom native dependencies have been added.

### Native integrations

**None beyond Capacitor's own WebView bridge.** A direct search of every mobile-client JS file for `Capacitor.*` bridge calls or `@capacitor/<plugin>` imports (camera, geolocation, push notifications, filesystem, share, etc.) found **zero matches**. The only Android-side custom code is the stock, unmodified `MainActivity.java` Capacitor generates for every project. Two placeholder test files (`ExampleInstrumentedTest.java`, `ExampleUnitTest.java`) are Capacitor's default templates and were never adapted into real tests for this app.

### Can a real Android build happen? — YES, independently verified, not just claimed

Two independent pieces of evidence, not one:
1. **A debug APK already exists on disk**: `mobile/capacitor/android/app/build/outputs/apk/debug/app-debug.apk`, 3,747,776 bytes, built 2026-11-13 16:30. Verified with the `file` command: `Android package (APK), with gradle app-metadata.properties, with APK Signing Block` — a real, validly-structured, debug-signed APK, not an empty or corrupt file.
2. **`npx cap doctor` run this pass** (read-only diagnostic, no files changed): reported `[success] Android looking great! 👌`. Installed toolchain: `@capacitor/cli` 6.2.3, `@capacitor/core` 6.2.3, `@capacitor/android` 6.2.3 (latest available is 8.6.2 — two major versions behind; see issues doc).

This audit did **not** re-run the ~26-minute `./gradlew assembleDebug` build, since a successful build from this exact project state is already on disk and dated within the last 24 hours, and re-running it would not be a meaningfully different verification — it would just reproduce the same artifact. If the project's dependencies or Gradle files change, a fresh build should be re-run and re-verified rather than trusting this one indefinitely.

**Caveat, stated precisely per the audit's own rule ("do not claim APK readiness without an actual build"):** the APK that was actually built is configured to load `http://10.0.2.2:8000/app` — the Android emulator's alias for the host machine's `localhost`. This APK **will not work on a physical device or in production** without changing `capacitor.config.json`'s `server.url` to a real, reachable HTTPS address and rebuilding. The build succeeds; the resulting app's usefulness outside an emulator talking to a locally-running dev server is currently zero. Full detail in `WEB_VS_MOBILE_ANALYSIS.md` and `ARCHITECTURE_ISSUES_AND_RECOMMENDATIONS.md`.

### Android verdict: **READY for emulator/local development. NOT READY for physical-device or production use** until `server.url` points at a real deployed server.

---

## iOS

### Project structure — DOES NOT EXIST

No `ios/` directory exists anywhere in the repository. `find mobile/capacitor -maxdepth 1 -iname ios` returns nothing. `npx cap add ios` has never been run in this environment.

### What *does* exist

- `@capacitor/ios` is a declared dependency in `mobile/capacitor/package.json` (`^6.1.0`) and is genuinely installed in `node_modules` (confirmed present).
- An `"ios"` npm script exists (`npx cap add ios && npm run icons && npx cap sync ios`) — the tooling to scaffold an iOS project is present and would very likely work, but has not been exercised.
- `.github/workflows/ios-build.yml` — a complete CI workflow that, on a `macos-14` GitHub Actions runner, would run `npm run ios` (scaffolding the project fresh in CI) and then `xcodebuild ... -sdk iphonesimulator ... CODE_SIGNING_ALLOWED=NO` to produce an **unsigned iOS Simulator build**. This workflow has never been run successfully (or at all) — this repository has no `.git` directory (see `ARCHITECTURE_ISSUES_AND_RECOMMENDATIONS.md`), so no GitHub Actions run is even possible yet without first pushing the code to a GitHub remote.

### Bundle identifier / deployment target / Info.plist / signing

**UNVERIFIABLE** — none of these exist yet, since no `ios/` project has been generated. They would be created by `npx cap add ios` (which reads `capacitor.config.json`'s `appId`/`appName`/`ios.backgroundColor`/`ios.contentInset` to seed the new Xcode project), but nothing can be reported about them until that command is actually run somewhere with Xcode available.

### Can a real iOS build happen? — BLOCKED in this environment, UNVERIFIED overall

This machine is Windows (confirmed: `win32` platform, PowerShell/Git Bash shell). Building and running an iOS app fundamentally requires macOS and Xcode — Apple does not support building iOS apps on Windows or Linux, with or without Capacitor. This is not a project configuration problem; it is a platform requirement that cannot be worked around locally.

A real iOS build is possible via the existing `ios-build.yml` **once the repository is pushed to a GitHub remote** (GitHub Actions' `macos-14` runners provide Xcode), and would produce a **simulator-only** build without additional Apple Developer signing credentials — explicitly, per the audit's own rule, not something this audit can claim succeeded since it has not been run.

### iOS verdict: **BLOCKED.** Not a code defect — a genuine environment limitation (no macOS/Xcode available here). The path to unblock it (push to GitHub, run the existing `ios-build.yml` workflow) is already built and committed; it has simply never been exercised.
