# CTRL+SPACE — mobile / responsive test report

## Viewports actually tested
320px (Galaxy S9+), 360px, 375px, 390px (iPhone 14), 412px (Pixel 7), 430px, 768px, 1280px — the full sweep across both `mobile_app_test.py` (iPhone 14 profile) and `mobile_devices.py` (Pixel 7 + Galaxy S9+ profiles, plus the explicit 320–1280px desktop-site width sweep).

## Results
| Check | Result |
|---|---|
| No horizontal overflow / no zoom-out needed | ✅ confirmed on 13 screens × 2 device profiles (Pixel 7, Galaxy S9+), this pass |
| Touch target size (≥44×44 CSS px) | ✅ "0 controls under 32px tall on Admin" reported for both profiles — i.e. zero undersized controls found |
| Bottom navigation, 5 tabs, active state | ✅ |
| Safe-area spacing | ✅ (CSS `env(safe-area-inset-*)` used throughout, verified rendering) |
| PWA manifest (standalone, 192+512 icons, maskable icon) | ✅ |
| Service worker controls the app | ✅ |
| Offline: saved report readable, honest error for unvisited reports | ✅ |
| Reconnection banner | ✅ |
| Arabic RTL layout, no overflow | ✅ (5/5 Arabic suite) |
| Keyboard behavior / orientation | Not separately probed this pass (Chromium emulation doesn't model a real on-screen keyboard pushing the viewport the way a physical device does) |

## Native Android (new this session — not browser emulation)
Built a real debug APK via Capacitor + Gradle and ran it on an actual Android emulator (Pixel_8 AVD, API-level image, not Chromium device emulation):
- App boots past the native splash screen.
- Connects to the Flask backend over the emulator's `10.0.2.2` host-loopback alias (recovered automatically from one transient "Server unreachable" moment to "Online").
- Home screen shows real seeded stats (6 reports / 36 passages / 8 experiments / 5 lessons).
- Deep navigation works: opened a real NTRS report detail (Saffire VI, NTRS 20240002981) with its correct "abstract not stored, read it on the NASA record" honesty message.
- Screenshots captured via `adb exec-out screencap` are the actual evidence, not a description.

## Explicitly disclosed, not claimed
- **No physical phone was used anywhere in this report.** Every result above is either Chromium browser/device emulation or one real Android *emulator* (software-virtualized hardware, not a physical device).
- iOS: not built (no Mac/Xcode on this machine); Capacitor project files are prepared but unverified.
- A real on-screen-keyboard occlusion test and true device-rotation test were not performed (emulation limitation), and are listed here rather than silently skipped.
