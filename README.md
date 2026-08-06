# Python CI/CD Demo — GitHub Actions

A minimal Flask app used to build and manage a real CI/CD pipeline with **GitHub Actions**.

```
python-cicd-demo/
├── app.py                        # Flask application
├── tests/test_app.py             # Unit tests (unittest)
├── requirements.txt              # Runtime dependencies
├── requirements-dev.txt          # + lint/coverage tooling
├── Dockerfile                    # Container image definition
└── .github/workflows/ci-cd.yml   # The pipeline itself
```

## 1. Pipeline design

The pipeline is a single workflow, `ci-cd.yml`, split into five jobs that run in sequence
(each depends on the one before it via `needs:`):

| Stage | Job | What it does | Runs on |
|---|---|---|---|
| CI | `lint` | Runs `flake8` for static analysis | every push/PR |
| CI | `test` | Runs the unit tests with coverage, across Python 3.11 and 3.12 (matrix build) | every push/PR |
| CI | `build` | Builds the Docker image and smoke-tests it (`curl /health`) | every push/PR |
| CD | `push-image` | Tags and pushes the image to Docker Hub (`:sha` and `:latest`) | push to `main` only |
| CD | `deploy` | Deploys the pushed image, via a GitHub **Environment** | push to `main` only |

**Why this shape:**
- Pull requests only ever run the CI jobs (`lint` → `test` → `build`) — nothing is pushed or
  deployed until code is merged to `main`, so `main` always reflects what's actually running.
- The Docker image is built **once** (`build`) and reused (as an artifact) by `push-image`,
  instead of rebuilding it — this keeps the image that was tested identical to the image that
  ships.
- `concurrency` cancels superseded runs on the same branch, so pushing twice in quick
  succession doesn't waste minutes on a run that's already obsolete.

## 2. Setting it up on your own GitHub account

1. Create a new repository on GitHub and push this folder to it:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Flask app + CI/CD pipeline"
   git branch -M main
   git remote add origin https://github.com/<your-username>/python-cicd-demo.git
   git push -u origin main
   ```
2. **Add secrets** (Settings → Secrets and variables → Actions → New repository secret):
   - `DOCKERHUB_USERNAME` — your Docker Hub username
   - `DOCKERHUB_TOKEN` — a Docker Hub access token (Account Settings → Security → New Access Token)
3. **Create the `production` environment** (Settings → Environments → New environment,
   name it `production`). Optionally add a required reviewer here — this is what lets you
   "manage" deployments (approve/reject) rather than have them fire automatically.
4. Push a commit — the `lint`/`test`/`build` jobs run immediately. Open a PR into `main` to
   see them gate the merge; merge it and the `push-image`/`deploy` jobs run.

## 3. Managing the pipeline

This is what "managing" the pipeline looks like day to day, once it's live in GitHub:

- **Monitoring runs:** the *Actions* tab lists every run, per-job status, and full logs for
  each step — this is where a failed `flake8` or test run is diagnosed.
- **Re-running failures:** a run can be re-run as-is, or with debug logging on, from the
  run's page (`Re-run jobs` → `Re-run failed jobs`), without needing a new commit.
- **Branch protection:** requiring the `lint`, `test`, and `build` checks to pass before a PR
  can be merged (Settings → Branches → Branch protection rule for `main`) turns the CI stage
  into an enforced gate, not just an FYI.
- **Approving deployments:** with a required reviewer on the `production` environment, the
  `deploy` job pauses and shows up under the repo's **Environments** tab awaiting approval —
  this is the manual control point for CD.
- **Rollback:** because every image is tagged with the commit SHA (`IMAGE:<sha>`), rolling
  back means re-running the `deploy` step of a previous successful workflow run (or manually
  deploying an older `:sha` tag) rather than reverting code first.
- **Secret rotation:** Docker Hub tokens can be revoked and replaced in Docker Hub, then
  updated in the repo's Actions secrets, with no workflow changes needed.

## 4. Running locally (outside the pipeline)

```bash
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v   # run the same tests CI runs
python app.py                             # start the app on localhost:5000
```

## 5. Extending this pipeline

- Add `codecov`/`coverage` upload as a step to track coverage trends over time.
- Add a `staging` environment (auto-deploy) ahead of the `production` one (manual approval).
- Replace the placeholder `deploy` step with a real target — a `curl` to a Render/Railway
  deploy hook, an `ssh` + `docker compose pull && up -d`, or a `kubectl set image` for k8s.
- Add Dependabot (`.github/dependabot.yml`) to keep `requirements.txt` and the base image
  patched automatically.
