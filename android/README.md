# EGNooz Android prototype

Kotlin + Jetpack Compose client of the published edition JSON.

- **JSON:** `https://egnooz.krystalbbs.net/editions/latest.json`
- **Timezone:** Australia/Melbourne
- **Copy:** Australian English
- Opens publisher pages in a Custom Tab. Does not fetch or store article bodies.

If that URL is 404 (nothing has been published yet), the app shows **Not published yet**. If `latest.json` is still yesterday’s edition, it shows that list with a hold banner. The last successful fetch is cached on the phone for patchy regional data. Pull down to refresh.

No ads, no accounts, no tracking SDK, no push.

## Sideload the debug APK

1. On the phone: Settings → Apps → Special app access → Install unknown apps → allow your file app / Files / Chrome.
2. Copy `app/build/outputs/apk/debug/app-debug.apk` to the phone (Drive, USB, or a local share).
3. Open the APK and install. The debug package id is `net.krystalbbs.egnooz.debug`.

Build it:

```bash
export ANDROID_HOME="$HOME/Android/Sdk"   # or your SDK path
cd android
./gradlew assembleDebug test
# optional Compose screenshots: ./gradlew recordPaparazziDebug
```

The APK lands at `android/app/build/outputs/apk/debug/app-debug.apk`.
