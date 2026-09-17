# FileDrop — build the APK for free (no PC needed)

I modernized the UI (orange/charcoal theme pulled straight from your logo, the
logo as the app icon + splash screen, rounded cards and buttons, a live status
dot, a "copy address" button) but I can't produce the actual `.apk` binary
myself — Android APK builds need the Android SDK/NDK downloaded from the
internet, and this chat environment has no network access. The good news:
GitHub Actions will build it for you, for free, entirely from your tablet's
browser — no laptop, no Android Studio.

## 1. Create a free GitHub account
Go to github.com and sign up if you don't already have an account.

## 2. Create a new repository
Tap **New repository**, name it `filedrop` (public or private, either is
fine), and create it.

## 3. Upload the plain files
In the repo, tap **Add file → Upload files**, then upload these three:
- `filedrop.py`
- `buildozer.spec`
- `icon.png`

Commit them.

## 4. Add the workflow file (this one needs its own step)
GitHub's uploader can't create the nested `.github/workflows/` folder from a
single file pick on mobile, so add it manually instead:
- Tap **Add file → Create new file**
- In the filename box, type the full path: `.github/workflows/build-apk.yml`
  (GitHub turns the slashes into folders automatically)
- Paste in the contents of `build-apk.yml`
- Commit it

## 5. Let it build
Committing the workflow file automatically triggers the build — go to the
**Actions** tab of your repo and watch it run. The first build takes
**15–20 minutes** (it's downloading the Android SDK/NDK); later builds are
faster.

## 6. Download the APK
When the run finishes with a green check, open it, scroll to **Artifacts**,
and download **FileDrop-apk**. It's a `.zip` — open it and you'll find the
installable `.apk` inside.

## 7. Install it
Transfer/download the `.apk` to your Android device and open it. You'll need
to allow "install unknown apps" for whichever app you opened it with — Android
will prompt you for this the first time.

## If the file picker looks empty on Android 11+
The app requests standard storage permissions, but some newer Android
versions restrict broad folder browsing unless you grant "All files access."
If `SEND FILE` doesn't show your files, go to
**Settings → Apps → FileDrop → Permissions → Files and media** and allow it.

## Every future update
Once this repo exists, any time you change `filedrop.py`, just edit the file
on GitHub (or re-upload it) and commit — the Actions workflow reruns
automatically and a fresh APK shows up in Artifacts a few minutes later.
