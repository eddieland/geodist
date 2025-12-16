# Publishing pipeline (dry-run first)

- Workflow: `.github/workflows/release.yml` triggers on tags matching `vMAJOR.MINOR.PATCH` and defaults to dry-run.
- Gates: runs Python lint/tests (`make lint`, `make test`) and Rust fmt/clippy/tests before any packaging starts.
- Outputs in dry-run: cargo publish dry-run builds `loxodrome-rs` and uploads the crate tarball; `maturin build` builds manylinux x86_64 wheels for Python 3.10-3.13 plus an sdist from Linux (macOS/Windows runners are temporarily disabled for faster iterations).

## Cutting a dry-run release

1. Ensure versions match: bump `loxodrome-rs/Cargo.toml` and `loxodrome/pyproject.toml` to the same value.
2. Tag the release: `git tag -s v0.1.0 && git push origin v0.1.0` (re-sign if you prefer lightweight tags).
3. Inspect artifacts in the run named `Release Publishing (dry-run default)`:
   - `loxodrome-rs-crate`: cargo-produced `.crate` tarball (from `cargo publish --dry-run`).
   - `python-wheels-*`: platform wheels and the Linux-built sdist.
4. Optionally exercise a wheel locally by downloading the artifact and installing with `pip install dist/<wheel>` to sanity-check metadata and importability.

## Flipping to live publish (gated)

- Default stays dry-run. Live uploads require the repository to be public and either the repository variable `PUBLISH_LIVE=true` **or** the manual `workflow_dispatch` input `publish_live=true`.
- `CRATES_IO_TOKEN` is still required when live publishing the Rust crate. PyPI now uses Trusted Publishing (OIDC) via the `pypi` environment, so no API token is needed once the project is linked on pypi.org.
- To push on demand: open the “Release Publishing” workflow in Actions, choose the branch/tag to run against, set `publish_live=true`, and confirm manifests are already bumped to the version you want to ship.
- Live path: artifacts still upload, and gated steps run `cargo publish --locked` plus `pypa/gh-action-pypi-publish` over the gathered wheels/sdist.

## Quick verification / rollback notes

- Verify versions with the preflight log (tag vs manifests) and check the dry-run `cargo publish` and `maturin build` outputs for warnings (warnings fail the jobs).
- If a live publish is started with missing secrets or a private repo, the workflow halts before pushing to registries with an explicit error.
- Roll back a mistaken live push by yanking/replacing the release on the registries; clear `PUBLISH_LIVE` or remove the tokens to restore the dry-run-only behavior.

## Automating the bump + tag

- Use the manual workflow `.github/workflows/prepare-release.yml` (Actions → “Prepare Release (bump + tag)”) with input `version = MAJOR.MINOR.PATCH`.
- The workflow updates both manifest versions, commits `Release vX.Y.Z`, creates tag `vX.Y.Z`, and pushes the commit + tag with `GITHUB_TOKEN`.
- It fails fast if the tag already exists, the working tree is dirty, or the version pattern is invalid. The tag then triggers the release publishing workflow automatically.
