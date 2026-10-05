# Project conventions

<!-- The agent reads this at the start of every session. Keep it short and current.
     Graded: does it reflect how the team actually works? -->

## What this repository is
One paragraph. Link to the current `spec.md`.

## Commands
```
# run a single classification (message on stdin)
export CHAT_BASE_URL="https://openrouter.ai/api/v1"
export CHAT_MODEL="minimax/minimax-m3"
# OPENROUTER_API_KEY must already be set in your shell profile. Never commit it.
export CHAT_USAGE_OUT="/tmp/usage.json"   # optional
echo "I was charged twice for the same invoice." | python3 classifier.py

# run all cases
export CHAT_USAGE_OUT="/tmp/usage.json"   # optional but recommended
python3 eval.py

# lint / format
python3 -m py_compile classifier.py eval.py
```

## Conventions
- Language and style rules the agent must follow.
- Where tests live and how they are named.
- Branch and PR naming.

## Working rules

For an introductory lab, follow its explicitly assigned stages; the full chain below applies to major projects. Week 1 uses its own minimal repository.

- Write or update `intent/` and `spec.md` before code. Get `plan.md` approved before implementing.
- One feature per branch and pull request. Never push to `main` directly.
- Never commit `.env` or `.claude/settings.local.json`.

## Common mistakes
Things the agent got wrong before and must not repeat. Add to this list as they happen.
## Working rules
- This is the Week 3 introductory lab. Stages assigned: intent and spec.
  No plan.md, no branches or pull requests. Commit to main.
- Standard library only, except that Java may add one JSON library jar.

## Team conventions
- Language: Python 3, standard library only
- Default model: minimax/minimax-m3 via OpenRouter
- File naming: lowercase with underscores (e.g. classifier.py, eval.py, cases.json)
