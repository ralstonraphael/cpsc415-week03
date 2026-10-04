# Project conventions

<!-- The agent reads this at the start of every session. Keep it short and current.
     Graded: does it reflect how the team actually works? -->

## What this repository is
CPSC 415 Week 3 lab: a command-line support-message classifier that asks a hosted model for JSON (`category`, `urgency`, `reason`), plus a five-case eval that runs the same cases against two models. Current spec: [spec.md](spec.md). Intent: [intent/classifier.md](intent/classifier.md).

## Commands
```
# build:  none (Python 3 standard library only)
# run:    python3 classify.py "message text"
# eval:   python3 eval.py            # reads cases.json
# env:    CHAT_BASE_URL  CHAT_MODEL  OPENROUTER_API_KEY
```

## Conventions
- Python 3, standard library only. No third-party packages.
- Default model `minimax/minimax-m3`; second model for the comparison `xiaomi/mimo-v2.6-flash`. Change only `CHAT_MODEL` between runs.
- File names are lowercase with underscores. Cases live in `cases.json`; eval results live in `CHECKS.md`.
- The API key is read from `OPENROUTER_API_KEY` in the environment. It never appears in a file, a commit, or program output.

## Working rules

For an introductory lab, follow its explicitly assigned stages; the full chain below applies to major projects. Week 1 uses its own minimal repository.

- Write or update `intent/` and `spec.md` before code. Get `plan.md` approved before implementing.
- One feature per branch and pull request. Never push to `main` directly.
- Never commit `.env` or `.claude/settings.local.json`.
- This is the Week 3 introductory lab. Stages assigned: intent and spec.
  No plan.md, no branches or pull requests. Commit to main.
- Standard library only, except that Java may add one JSON library jar.

## Common mistakes
Things the agent got wrong before and must not repeat. Add to this list as they happen.
- None yet.
