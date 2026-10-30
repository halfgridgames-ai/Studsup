# Studs Up for Android

This folder turns the web game at the repo root into the Google Play app
(`com.studsup.game`, **Studs Up: Red Card Football**). It uses
[Capacitor](https://capacitorjs.com) 8 with these plugins:

| Plugin | What it does | How the game reaches it |
| --- | --- | --- |
| `@capacitor-community/admob` | AdMob ads (real Studs Up ids on Android) | `monetize.js` |
| `cordova-plugin-purchase` | Google Play Billing | `monetize.js` |
| `@capacitor/share` + `@capacitor/filesystem` | share sheet for goal clips, room codes, the Play link | `native-share.js` |
| `@capacitor/haptics` | vibration | the game's `vib()` |
| `@capacitor-community/in-app-review` | Google Play's rating pop-up | `IAR()` in `index.html` |
| `@capacitor-firebase/analytics` | Firebase Analytics (match, tutorial and ad events) | `analytics.js` -> `track()` in `index.html` |

## How the build works

GitHub Actions (`.github/workflows/android.yml`) builds on every push to `main`
(and `tester-feedback` while v29 is in review):

1. `npm ci` installs the pinned Capacitor packages.
2. `sync-web.sh` copies the game into `www/`, swapping the CDN copies of three.js and the
   Google fonts for the local ones in `web-extra/` (the app must work offline), adds
   `monetize.js` and `native-share.js`, then runs `npx cap sync android`.
3. Gradle builds a debug APK, and a release AAB. Without signing secrets the unsigned AAB
   is pushed to the `build-output` branch, to be signed with the upload key.

Signing: the upload key lives outside the repo (never commit `*.jks`). Sign the unsigned
AAB with `jarsigner -sigalg SHA256withRSA -digestalg SHA-256 -keystore studs-up-upload.jks
app-release-unsigned.aab upload`, or set the secrets `SU_KEYSTORE_BASE64`,
`SU_KEYSTORE_PASSWORD`, `SU_KEY_ALIAS`, `SU_KEY_PASSWORD` to sign in CI.

Bump `versionCode` (and `versionName`) in `android/app/build.gradle` for every Play upload.
0.5.2 was versionCode 29.

Icons: `python3 tools/make-icons.py` rebuilds the launcher icons and splash from
`../icon-512.png`, `tools/icon-logo.png` and `tools/icon-background.png`.

## Analytics (Firebase)

`web-extra/analytics.js` sends play events (`match_start`, `match_end`, `tutorial_begin`,
`tutorial_complete`, `rewarded_ad_watched`) through `@capacitor-firebase/analytics`.
It only switches on when `android/app/google-services.json` is committed: download it from
the "Half Grid Games" Firebase project (Android app `com.studsup.game`). The file is not secret.

## Ads

Android uses the real Studs Up AdMob ids: the app id in `android/app/src/main/AndroidManifest.xml`
and the unit ids (`IDS.android`) in `web-extra/monetize.js`, with `TEST = false`. iOS still uses
Google's test units until the iPhone app is registered in AdMob. To test ads on a phone, add it as a
test device in AdMob (Settings -> Test devices); never tap real ads on your own phone.

Settings shows "Ad privacy choices" when Google's consent rules require it (UK/EU, some US states).
