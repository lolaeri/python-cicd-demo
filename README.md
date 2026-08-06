# Python CI/CD Pipeline (Personal Project)

A small Flask app I built to actually learn CI/CD hands-on with **GitHub Actions**, rather
than just reading about it. It's intentionally simple — the point was the pipeline, not the app.

```
python-cicd-demo/
├── app.py                        # my Flask app
├── tests/test_app.py             # unit tests (unittest)
├── requirements.txt              # runtime dependencies
├── requirements-dev.txt          # + lint/coverage tooling
├── Dockerfile                    # container image definition
└── .github/workflows/ci-cd.yml   # the pipeline itself
```

## 1. How I designed the pipeline

I went with a single workflow, `ci-cd.yml`, split into five jobs that run in sequence
(each one depends on the last via `needs:`):

| Stage | Job | What it does | Runs on |
|---|---|---|---|
| CI | `lint` | Runs `flake8` for static analysis | every push/PR |
| CI | `test` | Runs the unit tests with coverage, across Python 3.11 and 3.12 (matrix build) | every push/PR |
| CI | `build` | Builds the Docker image and smoke-tests it (`curl /health`) | every push/PR |
| CD | `push-image` | Tags and pushes the image to Docker Hub (`:sha` and `:latest`) | push to `main` only |
| CD | `deploy` | Deploys the pushed image, via a GitHub **Environment** | push to `main` only |

**Why I set it up this way:**
- I wanted pull requests to only ever run the CI jobs (`lint` → `test` → `build`) —
  nothing gets pushed or deployed until code is actually merged to `main`, so `main` always
  reflects what's really running.
- I build the Docker image **once** (`build`) and reuse it (as an artifact) in `push-image`
  instead of rebuilding it — that way the image I tested is byte-for-byte the image that ships.
- I added `concurrency` to cancel superseded runs on the same branch, so if I push twice in
  quick succession I'm not burning minutes on a run that's already obsolete.

## 2. How I set it up

1. Created a new repo on GitHub and pushed this folder to it:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Flask app + CI/CD pipeline"
   git branch -M main
   git remote add origin https://github.com/<your-username>/python-cicd-demo.git
   git push -u origin main
   ```
2. **Added my secrets** (Settings → Secrets and variables → Actions → New repository secret):
   - `DOCKERHUB_USERNAME` — my Docker Hub username
   - `DOCKERHUB_TOKEN` — a Docker Hub access token (Account Settings → Security → New Access Token)
3. **Created a `production` environment** (Settings → Environments → New environment,
   named it `production`). I added a required reviewer here too — this is what lets me
   actually "manage" deployments (approve/reject) instead of having them fire automatically.
4. Pushed a commit — the `lint`/`test`/`build` jobs kicked off immediately. Opened a PR into
   `main` to watch them gate the merge; once merged, `push-image`/`deploy` ran.

## 3. How I manage it day to day

This is what I actually do to keep the pipeline running smoothly:

- **Monitoring runs:** I check the *Actions* tab for every run's status and full logs —
  this is where I diagnose a failed `flake8` or test run.
- **Re-running failures:** if something flakes, I re-run it as-is, or with debug logging on,
  straight from the run's page (`Re-run jobs` → `Re-run failed jobs`) — no new commit needed.
- **Branch protection:** I require the `lint`, `test`, and `build` checks to pass before a PR
  can be merged (Settings → Branches → Branch protection rule for `main`), so CI is an
  enforced gate, not just an FYI.
- **Approving deployments:** with a required reviewer on the `production` environment, the
  `deploy` job pauses and shows up under the repo's **Environments** tab waiting on me —
  that's my manual control point for CD.
- **Rolling back:** since every image is tagged with the commit SHA (`IMAGE:<sha>`), rolling
  back just means re-running the `deploy` step of an earlier successful run (or manually
  deploying an older `:sha` tag) rather than reverting code first.
- **Rotating secrets:** if I ever need to revoke a Docker Hub token, I generate a new one and
  update the Actions secret — no workflow changes needed.

## 4. Running it locally

```bash
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v   # same tests CI runs
python app.py                             # starts the app on localhost:5000
```

## 5. What I'd add next

- Upload coverage to `codecov` so I can track trends over time instead of just a one-off number.
- Add a `staging` environment (auto-deploy) ahead of `production` (manual approval).
- Swap the placeholder `deploy` step for a real target — probably a `curl` to a
  Render/Railway deploy hook, or `ssh` + `docker compose pull && up -d`.
- Add Dependabot (`.github/dependabot.yml`) so `requirements.txt` and the base image stay
  patched without me having to remember to check.
