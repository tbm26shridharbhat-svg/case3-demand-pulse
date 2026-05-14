# Deployment — Hugging Face Spaces (Streamlit, free tier)

The brief recommends HF Spaces for data demos. End-to-end takes ~10 minutes.

## 1. Create the Space

1. Sign in at <https://huggingface.co> (free).
2. Profile menu → **New Space**.
3. Settings:
   - **Owner:** you
   - **Space name:** `case3-demand-pulse` (or your preferred slug)
   - **License:** MIT
   - **SDK:** **Streamlit**
   - **Hardware:** CPU basic — Free
4. Click **Create Space**. HF gives you a git remote like
   `https://huggingface.co/spaces/<you>/case3-demand-pulse`.

## 2. Push the project to that remote

```bash
# from the project root
git remote add hf https://huggingface.co/spaces/<you>/case3-demand-pulse
git push hf main
```

## 3. Tell HF where the app lives

HF Spaces expects either `app.py` or `streamlit_app.py` at the **root** of the Space repo,
or the entrypoint declared in the Space's README YAML frontmatter.

Easiest fix: prepend the following YAML to the **top** of `README.md` before pushing to HF
(do this on a deploy branch so the GitHub README stays clean):

```yaml
---
title: Demand Pulse
emoji: 📈
colorFrom: blue
colorTo: red
sdk: streamlit
sdk_version: 1.40.0
app_file: app/streamlit_app.py
pinned: false
---
```

Push that branch to HF only; keep GitHub on `main` without the frontmatter.

## 4. Wait ~3 minutes for first build

HF will install `requirements.txt`, then start the Streamlit app. You'll get a URL like
`https://<you>-case3-demand-pulse.hf.space`. Paste it into the top of `README.md`.

## 5. Verify

- Open the URL in an incognito window.
- Click through all 5 sidebar pages — they should render without errors.
- Try the `surge_cost` sidebar input — numbers should recompute in <1s.
- Open it on your phone — table rendering may need horizontal scroll, that's expected.

## Troubleshooting

- **"App didn't start" / build error** → check the Space's "Logs" tab; usually a missing
  package in `requirements.txt`. Add and push.
- **First page load > 30 seconds** → HF cold start; warms up after first hit.
- **`outputs/forecast.csv` not found** → Notebook 04 wasn't run before push. Re-run it
  locally and commit the CSV before pushing.
