# Checks

Run on 2026-10-05 with the cases in `cases.json`. Each row is one full pass
of `eval.py` against one model. `CHAT_USAGE_OUT=/tmp/usage.json` was set so
token counts could be summed from the side file.

## Comparison

| Model                  | Cases passed | Failed and how | Tokens in | Tokens out |
|------------------------|--------------|----------------|-----------|------------|
| minimax/minimax-m3     | 5/5          | none           | 1733      | 573        |
| xiaomi/mimo-v2.6-flash | 5/5          | none           | 965       | 376        |

## Observations

- Categories matched on every case for both models, including the ambiguous
  case (`technical` for both) and the off-topic case (`unknown` for both).
- Urgency differed on the sales case and the ambiguous case both between
  models and between two runs of `minimax/minimax-m3` (sales was `low` in
  one run and `medium` in another; the ambiguous case was `medium` in one
  run and `high` in another). The eval does not check urgency against an
  expected value — it only checks urgency is in the allowed set — so these
  differences are judgment calls by the model, not failures.

## Known issues

- `eval.py` does not set `CHAT_USAGE_OUT` itself. You must `export
  CHAT_USAGE_OUT=/tmp/usage.json` before running for the summary line to
  show token counts; otherwise it prints `tokens: in=n/a out=n/a
  (CHAT_USAGE_OUT not set)`.