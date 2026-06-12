# Agent notes

Conventions for AI coding agents working in this repository.

## Code style

- Do not add inline/line comments explaining what code does. Code should be self-explanatory through naming.
  Only add a comment when it captures non-obvious *why* (a workaround, a hidden constraint, a subtle invariant)
  that isn't derivable from reading the code.

## Commits and releases

- Releases are managed by [release-please](https://github.com/googleapis/release-please) (config:
  `release-please-config.json`, `.release-please-manifest.json`, workflow:
  `.github/workflows/release-please.yml`). Commit messages on `main` MUST follow
  [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `chore:`, `ci:`, `docs:`, etc.) —
  release-please uses them to compute version bumps and changelog entries. Use `feat!:`/`BREAKING CHANGE:` only for
  real breaking changes.
- Versions in `backend/pyproject.toml`, `frontend/package.json` and `frontend/package-lock.json` are managed by
  release-please via its release PR. Don't bump them by hand.
- `main` is a protected branch; all changes go through PRs.
- `ci:`/`chore:`/`docs:` commits don't bump the version or appear in the changelog (release-please's default
  conventional-commit sections hide them). If a change fixes the release/release-please/docker-publish pipeline
  itself, use `fix:` instead of `ci:` — that way the merge produces a real release PR and the fix gets exercised
  by an actual release.

## CI/CD

- `.github/workflows/ci.yml` runs lint + tests + build for backend and frontend on every PR and push to `main`.
  It never builds or pushes the Docker image.
- `.github/workflows/docker-publish.yml` builds and pushes the production image to GHCR only when a `vX.Y.Z` tag
  is pushed — i.e. when a release-please release PR is merged. Don't add Docker build/push steps to `ci.yml`.
