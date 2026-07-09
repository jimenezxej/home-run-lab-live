# Home Run Lab 3.1

A Chromebook-friendly MLB home run research dashboard with:

- live slate generation from `pipeline.py`
- live home run tracker from MLB game feeds
- iPhone PWA files in `app/`
- GitHub Pages upload/deploy helpers in `scripts/`
- optional GitHub Actions updater in `.github/workflows/update-data.yml`

## Local Chromebook run

```bash
cd ~/homerun-lab
bash run-chromebook.sh
```

Open:

```text
http://localhost:8000?v=3.1
```

## Build a GitHub Pages upload folder

```bash
cd ~/homerun-lab
python3 scripts/build_github_upload.py
```

Upload the contents of `github-upload/` to your GitHub Pages repository.

## One-command deploy later

Clone your GitHub Pages repo locally, copy `scripts/deploy_config.example.json` to
`scripts/deploy_config.json`, edit `repo_path`, then run:

```bash
python3 scripts/deploy_github.py
```

## Notes

- The site does not need the terminal after it is uploaded to GitHub, but it only shows the most recently uploaded JSON files.
- Live cloud updates need either GitHub Actions or another always-on host.
- True iPhone push notifications require HTTPS plus a notification backend; this package includes the PWA foundation and alert center, not a paid push service.
