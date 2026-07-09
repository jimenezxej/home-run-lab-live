# Free iPhone Setup

You cannot open `localhost` from your iPhone because `localhost` means the device you are holding. To use the app on iPhone, host the `app/` folder on GitHub Pages.

## Simple GitHub Pages upload

1. Create a public GitHub repo named `homerun-lab`.
2. Run this on Chromebook:

```bash
cd ~/homerun-lab
bash scripts/build-github-upload.sh
```

3. Upload the files inside `github-upload/` to the root of the GitHub repo.
4. In GitHub, go to Settings -> Pages.
5. Choose Deploy from branch -> `main` -> `/root`.
6. Open the Pages link on iPhone Safari.
7. Tap Share -> Add to Home Screen.

## Updating data

Every time you want fresh data online:

```bash
cd ~/homerun-lab
bash scripts/update-live-data.sh
bash scripts/build-github-upload.sh
```

Then upload the fresh `slate.json`, `hr-history.json`, and `live-events.json` to GitHub.

Automatic cloud updates can be added later with GitHub Actions, but the local workflow above is the simplest free version.
