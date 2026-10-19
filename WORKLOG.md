# Worklog

Running log of changes on SatQuery AI: what was done, why, and a short description. Newest entries first.

Entry format:

```
## YYYY-MM-DD — Short title
**Branch:** <branch> · **Commit:** <sha>
**What:** what changed (files/modules touched).
**Why:** the problem or goal behind it.
**Notes:** behaviour, usage, limitations, follow-ups (optional).
```

---

## 2026-10-19 — Repository hygiene: .gitignore and untracking generated files
**Branch:** `feature/enhancements-and-completion` · **Commit:** `105dbece`
**What:** Added `.gitignore` (Python bytecode, `*.egg-info/`, virtualenvs, test/tool caches, editor/OS files, `.env*`, model weights/checkpoints, `benchmark_results.json`). Removed the tracked `__pycache__/*.pyc` and `satquery.egg-info/` files from the index; they remain on disk.
**Why:** Any run of the code regenerated these files and filled `git status` with ~137 spurious modifications, which hid the real changes.
**Notes:** `test1.tif`, `test2.tif`, and `demo_satellite.tif` are deliberately still tracked because the README and CLI examples use them.

## 2026-10-19 — CLAUDE.md
**Branch:** `feature/enhancements-and-completion` · **Commit:** `105dbece`
**What:** Added `CLAUDE.md` with dev commands (install, tests, CLI, API, benchmark), the agent pipeline architecture (parser → resolver → planner → executor → synthesizer), the tool/model provider extension points, and a list of known placeholders and incomplete modules.
**Why:** Gives future contributors and AI assistants an accurate picture of the code. The README describes several capabilities that are not implemented yet.
**Notes:** The "Known placeholders / incomplete areas" section is the starting backlog for this branch.

## 2026-10-19 — Feature branch created
**Branch:** `feature/enhancements-and-completion` (from `main` @ `1ac4760`)
**What:** Created the working branch for new features, improvements to existing implementations, and completing stubbed modules.
**Why:** Keeps this work isolated from `main` until it is reviewed.
