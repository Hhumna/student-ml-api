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

[PASTE THE "why not publish from every PR" paragraph I'll give you]

## Rollback

Rollbacks in this architecture do not require reverting source code or rebuilding artifacts. We simply deploy the previously known-good container image directly from the registry.

[PASTE THE rollback paragraph]

## Traceability

[PASTE the traceability block]

## Branch Protection

The `main` branch is strictly protected to ensure stability. Direct pushes are disabled. All changes must go through a Pull Request and require passing status checks from the CI workflow before they can be merged.
