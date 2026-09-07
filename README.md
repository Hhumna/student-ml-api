# student-ml-api

A Flask Machine Learning inference API integrated with a full CI/CD pipeline using GitHub Actions and GitHub Container Registry (GHCR).

## API Endpoints

### `GET /health`
Returns the health status and metadata of the application.

**Response:**
```json
{
  "status": "healthy",
  "application": "student-ml-api",
  "application_version": "1.1.0",
  "model_version": "model-1"
}
```

### `POST /predict`
Returns a prediction based on the provided input value.

**Request:**
```json
{
  "value": 10
}
```

**Response:**
```json
{
  "input": 10,
  "prediction": 20
}
```

## Development Workflow

Our development lifecycle follows a structured pipeline:
Feature Branches -> Pull Requests (PRs) -> CI Validation -> Code Review -> Merge to `main` -> Version Tagging -> Automated Release to GHCR.

## Running Locally

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run tests:
   ```bash
   pytest
   ```
3. Start the application:
   ```bash
   python app.py
   ```

## Running with Docker

**Building and running locally:**
```bash
docker build -t student-ml-api:latest .
docker run -d --name student-ml-api -p 5000:5000 student-ml-api:latest
```

**Pulling from GHCR:**
```bash
docker pull ghcr.io/hhumna/student-ml-api:latest
docker run -d --name student-ml-api -p 5000:5000 ghcr.io/hhumna/student-ml-api:latest
```

## CI/CD Pipeline

The pipeline is split into two independent workflows:
* **ci.yml**: Triggered on Pull Requests to `main`. It runs tests and validates that the Docker image can be built successfully, but it does NOT publish anything.
* **release.yml**: Triggered only when a new version tag (e.g., `v1.0.0`) is pushed. It runs tests and formally builds and publishes the release artifact to GHCR.

Publishing an image on every Pull Request would mean every proposed, unreviewed, and possibly broken change ends up in the registry — wasting storage and bandwidth, and risking that someone accidentally pulls an unvetted image as if it were production-ready. Separating CI (validate on PR) from release (publish on tag) ensures only code that has passed review and been intentionally merged and versioned ever reaches the registry, keeping it a trustworthy history of shippable artifacts rather than a dumping ground of in-progress work.

## Rollback

Rollbacks in this architecture do not require reverting source code or rebuilding artifacts. We simply deploy the previously known-good container image directly from the registry.

Rolling back via the registry means running a pre-built, already-tested artifact — the exact same binary validated by CI and deployed originally, with all dependencies baked in. It takes seconds and carries zero risk of environment drift (different OS, missing system libraries, a different Python patch version). In contrast, a source-based rollback (`git clone` → `pip install` → `python app.py`) rebuilds everything from scratch on the target machine, depending on network access, the right interpreter version, and no dependency-resolution surprises — any of which can turn a quick rollback into a debugging session during a live incident.

Example performed in this project: after publishing v1.1.0, we simulated a rollback by running `docker run ghcr.io/hhumna/student-ml-api:1.0.0` directly — no code changes, no rebuild — and confirmed via `/health` that the old response schema was restored.

## Traceability

| Version | PR | Merge Commit | Git Tag | Docker Image | Image Digest |
|---------|-----|--------------|---------|---------------|---------------|
| 1.0.0 | #1 | `b3dfd4e0e3ac4a01edc9e9530c6a2d3203ebf9d4` | `v1.0.0` | `ghcr.io/hhumna/student-ml-api:1.0.0` | `sha256:b8f739c620e4270cb29bf5d35d4ab012251c9330a875b7b99649d0936c680627` |
| 1.1.0 | #2 | `b73b3b6c38231fdb855d82648022f43cfa9f1f7f` | `v1.1.0` | `ghcr.io/hhumna/student-ml-api:1.1.0` | `sha256:<sha256:c42f212ab8eb48bd0f2880e5dfff5ba8b0e717f6ade983dc3fd444d90f7ab72c>` |

## Docker Build Cache Analysis

To validate Docker's layer caching behavior, three builds were compared: a baseline build, a build after modifying only `app.py`, and a build after modifying only `requirements.txt`.

| Step | Baseline | app.py changed | requirements.txt changed |
|------|----------|-----------------|----------------------------|
| FROM python:3.11-slim | Ran | Cached | Cached |
| ARG / LABEL instructions | Ran | Cached | Cached |
| WORKDIR /app | Ran | Cached | Cached |
| COPY requirements.txt . | Ran | Cached | **Re-ran** (file changed) |
| RUN pip install -r requirements.txt | Ran | Cached | **Re-ran** (invalidated by prior step) |
| COPY . . | Ran | **Re-ran** (source changed) | Re-ran |
| EXPOSE / CMD | Ran | Re-ran | Re-ran |

**Key finding:** Changing only `app.py` left every layer up to and including `pip install` cached — the expensive dependency install step was skipped entirely, and only the final copy/expose/cmd layers re-ran. Changing `requirements.txt` invalidated the cache starting from the `COPY requirements.txt .` step, forcing a full dependency reinstall.

**Why `COPY requirements.txt . → RUN pip install → COPY . .` beats `COPY . . → RUN pip install`:** Docker caches each instruction as a layer and invalidates a layer (and everything after it) only when its own input changes. If the whole source tree is copied in a single `COPY . .` before installing dependencies, then *any* code change — even editing a single line in `app.py` — invalidates the cache at that copy step, which then forces `pip install` to re-run on every single build, even though the actual dependency list never changed. By copying only `requirements.txt` first and installing dependencies before copying the rest of the source code, dependency installation is only re-triggered when dependencies themselves actually change — dramatically speeding up iterative development and CI build times, since source code changes far more often than dependencies do.

## Failure Analysis

### Failure 1: Failed pytest in CI
**Symptom:** GitHub Actions CI run failed with a red X on the `feature/prediction-api` branch (commit `fa0d380`).
**Root Cause:** A test assertion was deliberately changed to expect `data["status"] == "wrong"` instead of the correct value `"healthy"`, to validate that CI correctly catches test failures before merge.
**Evidence:** CI run "test-and-build" failed after 9s with `AssertionError: assert 'healthy' == 'wrong'`. See GitHub Actions run history.
**Correction:** Reverted the assertion to `data["status"] == "healthy"` in commit `8281357` ("fix: correct health endpoint test assertion"). The next CI run passed with 6/6 tests green.

### Failure 2: Wrong container port mapping
**Symptom:** `curl http://localhost:5000/health` returns `curl: (7) Failed to connect to localhost port 5000 after 0 ms: Connection refused`.
**Root Cause:** The container was started with `docker run -p 6000:5000 ...`, mapping host port 6000 to the container's internal port 5000. The app is correctly running and listening inside the container — the port mismatch is purely on the host-side mapping, not an application bug.
**Evidence:** `curl -v http://localhost:5000/health` fails with "Connection refused", while `curl -v http://localhost:6000/health` succeeds with a 200 OK and the correct `/health` JSON response, proving the container itself is healthy.
**Correction:** Corrected the `docker run` command to map the intended host port to container port 5000, e.g. `docker run -p 5000:5000 ...`, matching the port the Flask app actually binds to (as declared in `EXPOSE 5000` in the Dockerfile).

## Branch Protection

The `main` branch is strictly protected to ensure stability. Direct pushes are disabled. All changes must go through a Pull Request and require passing status checks from the CI workflow before they can be merged.
