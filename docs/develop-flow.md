# Development & Release Flow

This document details the branch management, commit verification, and release pipeline. We follow an automated release candidate (RC) structure integrated with GitHub Actions.

---

## 1. Local Development Cycle

All development work, including fixes and new features, occurs within release candidate branches (e.g. `v1.0.8-rc`).

### Verification & Commit
Before pushing code, always verify the source code format:

```bash
# Run code check and linting (ignoring frontend folder)
flake8 . --exclude=web --count --exit-zero --max-complexity=20 --max-line-length=256 --statistics

# Commit changes and push to current release candidate branch
git add .
git commit -m "fix: jwt validation logic"
git push
```

---

## 2. Release & Production Deploy

When development for the version is complete, the branch is merged into `main` to trigger the release automation.

### Merging & Automatic Pipeline
1. Open a **Pull Request** on GitHub:
   * **Source Branch:** `v1.0.X-rc` (e.g. `v1.0.8-rc`)
   * **Target Branch:** `main`
2. Once approved, **Merge** the Pull Request.
3. The merge automatically triggers the **Release Tag** workflow, which performs:
   * **Tag Creation:** Strips the `-rc` suffix from the branch name and creates the official tag (e.g., `v1.0.8`).
   * **Release Notes:** Automatically builds a GitHub Release with a changelog generated from the merged commits.
   * **Branch Cleanup:** Deletes the remote `v1.0.X-rc` branch.
   * **Docker Build:** Builds and pushes the Docker image to Docker Hub tagged with the release version.

---

## 3. Transitioning to the Next Release

Once the release is deployed, synchronize your local environment and prepare the workspace for the next cycle.

### 1. Synchronize local `main`
```bash
git checkout main
git pull
```

### 2. Create the next candidate branch (e.g., `v1.0.9-rc`)
```bash
# Ensure local references are clean
git fetch --prune

# Create new RC branch
git checkout -b v1.0.9-rc
```

### 3. Bump version and publish branch setup
Update the `"version"` field in `web/package.json` to match the new version:

```json
{
  "name": "ipxa",
  "version": "v1.0.9",
  ...
}
```

Commit the change and push to establish tracking:

```bash
git add web/package.json
git commit -m "docs: bump version to 1.0.9-rc"
git push -u origin v1.0.9-rc
```