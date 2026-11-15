# Mobile build verification

Read-only audit, 2026-11-14. This phase's rule: non-destructive checks are fine to execute; destructive cleanup or dependency upgrades are not. One command was actually executed this pass. Everything else is evidence read from the filesystem (existing build artifacts, CI workflow definitions).

## Command executed this pass

```
$ cd mobile/capacitor && npx cap doctor
```

**Environment:** Windows 11, this repository's `mobile/capacitor/node_modules` (already installed from an earlier session — `npm install --ignore-scripts`, documented in `CLAUDE.md` as the workaround for a `sharp`-binary GitHub-release throttling issue in this sandbox; not required for this diagnostic).

**Result (full output):**
```
   Capacitor Doctor   

Latest Dependencies:
  @capacitor/cli: 8.6.2
  @capacitor/core: 8.6.2
  @capacitor/android: 8.6.2
  @capacitor/ios: 8.6.2

Installed Dependencies:
  @capacitor/cli: 6.2.3
  @capacitor/ios: 6.2.3
  @capacitor/core: 6.2.3
  @capacitor/android: 6.2.3

[success] Android looking great! 👌
```

**Interpretation:** the installed Capacitor toolchain (6.2.3) is internally consistent across `cli`/`core`/`android`/`ios` — no version-mismatch warnings, which is itself a meaningful pass/fail signal `cap doctor` checks for. It is two major versions behind the latest available (8.6.2) — noted as a finding in `ARCHITECTURE_ISSUES_AND_RECOMMENDATIONS.md`, not a build blocker. No "iOS" section was printed because no `ios/` project exists to check (consistent with `ANDROID_IOS_READINESS.md`).

This command reads project state only; it did not modify `capacitor.config.json`, `package.json`, or any generated files. Confirmed no files changed as a result.

## Prior build evidence (not re-executed this pass, verified to still exist)

A full `./gradlew assembleDebug` (the real Android build command, run via `npm run apk` → `cd android && ./gradlew assembleDebug`) was executed in an earlier session on 2026-11-13, per `CLAUDE.md`'s own build log ("first run ≈26 min, mostly dependency resolution"). This audit did **not** re-run that build — a 26-minute build adds no new information when its output artifact can be directly inspected and is dated within the last 24 hours. Instead, the artifact itself was verified directly:

```
$ ls -la mobile/capacitor/android/app/build/outputs/apk/debug/app-debug.apk
-rw-r--r-- ... 3747776 Nov 13 16:30 app-debug.apk

$ file mobile/capacitor/android/app/build/outputs/apk/debug/app-debug.apk
mobile/capacitor/android/app/build/outputs/apk/debug/app-debug.apk: Android package (APK), with gradle app-metadata.properties, with APK Signing Block
```

This confirms a real, non-empty, structurally valid, signed Android package exists — not an assumption carried over from the prior session's own claim, but independently re-verified against the actual file on disk during this audit.

**If this project's dependencies, Gradle files, or source change, this build should be re-run and re-verified — this verification is only valid for the project state as of 2026-11-13 16:30 / this audit's inspection on 2026-11-14.**

## Commands available but intentionally not run this pass

| Command | What it would do | Why not run |
|---|---|---|
| `./gradlew assembleDebug` (fresh) | Full ~26-minute Android rebuild | A valid, current artifact already exists (see above); redundant for an audit-only phase. |
| `npx cap sync android` | Copies `www/` into the Android project and updates native plugin registrations | Non-destructive, but not needed — nothing in the web assets changed since the last sync relevant to this audit, and this is a *development* action (syncing changes), which the audit's "do not modify" framing argues against running speculatively. |
| `npm run ios` (`cap add ios`) | Scaffolds a new `ios/` Xcode project | Would create new files, which this audit-only phase explicitly avoids; also only partially useful without macOS/Xcode to actually open/build the result. |
| `xcodebuild ...` | Build the iOS app | **Cannot run at all** — this is a Windows machine; `xcodebuild` requires macOS. Not a choice, a hard platform limitation. |
| `.github/workflows/android-apk.yml` / `ios-build.yml` via GitHub Actions | Cloud builds (Android debug APK; unsigned iOS Simulator build) | This repository has no `.git` directory (confirmed: `git rev-parse --is-inside-work-tree` → "fatal: not a git repository") — there is no GitHub remote to dispatch a workflow against yet. Not a workflow-file problem; a repository-initialization problem (see `ARCHITECTURE_ISSUES_AND_RECOMMENDATIONS.md`). |

## Build verification summary

| Platform | Buildable in this environment? | Evidence | Caveat |
|---|---|---|---|
| Android (debug, emulator) | **Yes — verified** | Existing signed APK, re-confirmed valid via `file`; `cap doctor` reports no issues | Points at an emulator-only server address; see `ANDROID_IOS_READINESS.md` |
| Android (release, signed, physical device) | **Not yet attempted** | No signing config present in `app/build.gradle` | Requires a release keystore + `server.url` pointed at a real server first |
| iOS (simulator, via CI) | **Possible, not yet exercised** | `ios-build.yml` exists and is well-formed | Requires pushing to a GitHub remote (none exists) to actually run it |
| iOS (local build) | **Blocked** | No macOS/Xcode in this environment | Hard platform requirement, not a project defect |
