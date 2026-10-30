# Studs Up for iPhone

The iPhone app lives next to the Android one: same Capacitor 8 project (`android-app/`),
same web game, same plugins. The native Xcode project is `ios/App` (committed), and
GitHub builds it on a Mac in the cloud, so no Mac is needed.

| Plugin | On iPhone | How the game reaches it |
| --- | --- | --- |
| `@capacitor-community/admob` 8.2.1 | Google AdMob ads, consent form, Apple's "Allow tracking?" prompt | `Capacitor.Plugins.AdMob` |
| `cordova-plugin-purchase` 13.18.0 | App Store in-app purchases (StoreKit) | `window.CdvPurchase` (after `deviceready`) |

The game picks the platform with `Capacitor.getPlatform()`: ad unit ids and the store
(`APPLE_APPSTORE` or `GOOGLE_PLAY`) follow from it. Product ids are the same on both stores.

Bundle id: `com.studsup.game` - iPhone only (no iPad), portrait, iOS 15 or later.

## How the build works

`.github/workflows/ios.yml` runs on every push to `main`, on pull requests, and from
**Actions -> iOS build -> Run workflow**:

1. `build-web.py` builds the game, `npm ci` installs Capacitor, and `sync-web.sh ios`
   copies the game into `ios/App/App/public` and runs `pod install`.
2. `xcodebuild archive` builds an unsigned archive. This alone proves the app compiles.
3. If the four secrets below exist (and it isn't a pull request), `xcodebuild -exportArchive`
   signs the app with Xcode cloud signing and uploads it to App Store Connect. No
   certificates or profiles are stored anywhere: Apple keeps the distribution certificate.

The build number is the workflow run number, so each upload is higher than the last.
The version players see is `MARKETING_VERSION` in `ios/App/App.xcodeproj/project.pbxproj`
(keep it equal to `versionName` in the Android `build.gradle`).

## One-time setup (all doable on a phone)

Use Safari or Chrome on the phone. Where a site looks cramped, choose
**Request Desktop Website** (Safari: the "aA" button; Chrome: the menu, **Desktop site**).

1. **Join the Apple Developer Program** (£79 a year): in the **Apple Developer** app
   (iPhone) tap **Account -> Enrol Now**, or go to developer.apple.com/programs/enroll.
   Approval can take a day or two.
2. **Accept the agreements**: appstoreconnect.apple.com -> **Business**. Accept the
   **Paid Apps** agreement and fill in bank and tax details (needed for in-app purchases).
3. **Register the bundle id**: developer.apple.com/account -> **Identifiers -> +** ->
   **App IDs -> App**. Description `Studs Up`, Bundle ID **Explicit**
   `com.studsup.game`. Leave the capabilities as they are -> **Register**.
4. **Create the app record**: appstoreconnect.apple.com -> **Apps -> + -> New App**.
   Platform iOS, name `Studs Up`, language English (UK), bundle id from step 3,
   SKU `studsup`, Full Access.
5. **Make an API key**: appstoreconnect.apple.com -> **Users and Access -> Integrations ->
   App Store Connect API** (the first time, tap **Request Access** and accept). Then
   **Team Keys -> +**, name `GitHub`, access **Admin** -> **Generate**. Note the
   **Issuer ID** (above the list) and the **Key ID**, then tap **Download** (only allowed once).
6. **Find the Team ID**: developer.apple.com/account -> **Membership details -> Team ID**.
7. **Add four secrets on GitHub**: github.com/halfgridgames-ai/Studsup -> **Settings ->
   Secrets and variables -> Actions -> New repository secret**:

   | Secret | Value |
   | --- | --- |
   | `ASC_KEY_ID` | Key ID from step 5 |
   | `ASC_ISSUER_ID` | Issuer ID from step 5 |
   | `ASC_KEY_P8` | the whole text of the downloaded `AuthKey_XXXXXXXXXX.p8`, including the `BEGIN`/`END` lines |
   | `APPLE_TEAM_ID` | Team ID from step 6 |

   To copy the key text on an iPhone: in the **Files** app, long-press the `.p8` file ->
   **Rename**, change the ending to `.txt`, open it, then select all and copy.
8. **Run the build**: GitHub -> **Actions -> iOS build -> Run workflow**. A few minutes after
   it goes green, the build shows in App Store Connect under **TestFlight**.
9. **Test on an iPhone**: in TestFlight in App Store Connect add yourself as an internal tester;
   install Apple's **TestFlight** app on the iPhone and open the invite. Purchases in TestFlight
   are free sandbox purchases.

## Before launch: swap test ids and add products

1. **AdMob app id (iPhone)**: add an **iOS** app in AdMob (it is separate from the Android one).
   Put its app id (contains `~`) in `ios/App/App/Info.plist`, `GADApplicationIdentifier`,
   replacing Google's test id `ca-app-pub-3940256099942544~1458002511`.
2. **Ad unit ids (iPhone)**: in `web-extra/monetize.js`, `IDS.ios` (rewarded and interstitial), from the
   new iOS app in AdMob, then `TEST = false`.
   The settings Rate link uses Apple's review pop-up on iPhone, and Share links to the Pages site
   until the App Store page exists.
3. **In-app purchases**: App Store Connect -> the app -> **Monetization -> In-App Purchases**.
   Same ids as Play (`PRODUCTS` in `web-extra/monetize.js`): coin packs as Consumable, `remove_ads` and `starter_pack` as Non-Consumable. Each needs a display name, description and a review
   screenshot of the shop. Add them to the first app version when you submit it.
4. **App Privacy** (App Store Connect -> App Privacy): the game itself collects nothing, but
   AdMob does. Declare Device ID, Advertising Data, Product Interaction, Coarse Location and
   Crash/Performance Data, used for Third-Party Advertising and Analytics, and **used for
   tracking**. Privacy policy URL: the game's `privacy.html` on its Pages site.
5. **Store page**: 6.9" iPhone screenshots (1320x2868), description, keywords, support URL
   (the Pages site works), age rating questionnaire.

## Notes

- Apple requires a **Restore purchases** button; the shop already has one on native builds.
- The tracking prompt text is `NSUserTrackingUsageDescription` in `Info.plist`. The game asks
  after the UK/EU consent form, once.
- `Info.plist` sets `ITSAppUsesNonExemptEncryption = false`, so TestFlight doesn't ask the
  export-compliance question on every build.
- Icons and splash: `ios/App/App/Assets.xcassets` (1024px icon, 2732px splash): the game icon on
  the game's background colour.
- The game keeps the screen awake (`AppDelegate.swift`) and hides the status bar, like Android.
