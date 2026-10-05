# Support message classifier

A small command-line program that asks a model to classify one customer
support message and prints a single JSON object on stdout with `category`,
`urgency`, and `reason`. Driven by `spec.md` and `intent/classifier.md`.

## How to run

`classifier.py` reads the message from stdin and three required environment
variables plus one optional one:

```sh
export CHAT_BASE_URL="https://openrouter.ai/api/v1"
export CHAT_MODEL="minimax/minimax-m3"
export OPENROUTER_API_KEY="sk-or-..."
export CHAT_USAGE_OUT="/tmp/usage.json"   # optional; omit to skip token side file
echo "I was charged twice for the same invoice." | python3 classifier.py
# {"category": "billing", "urgency": "high", "reason": "..."}
```

To run the full eval against the cases in `cases.json`:

```sh
export CHAT_USAGE_OUT="/tmp/usage.json"   # optional but recommended
python3 eval.py
```

The eval prints `PASS` or `FAIL` per case and a summary line with total
tokens in and out. Without `CHAT_USAGE_OUT` set, the summary reports
`tokens: in=n/a out=n/a`.

## Cases

`cases.json` holds five cases, each designed to catch a specific behavior:

- `clear_billing` — duplicate charge and refund ask. Catches whether the
  classifier routes money/account questions to billing rather than the
  more general `unknown`.
- `clear_technical` — mobile app crash with a concrete OS (Android 14) and
  device. Catches whether the classifier picks up on a real bug report.
- `clear_sales` — prospective customer comparing Team and Business plans
  and asking about a trial. Catches whether the classifier routes
  pre-purchase questions to sales rather than billing or technical.
- `ambiguous_login_billing` — login trouble plus a recent billing-cycle
  email. Catches whether the classifier commits to a category (any of
  `technical` or `billing`) instead of falling back to `unknown` on a
  real but ambiguous support message.
- `off_topic_weather` — weather question about Hartford. Catches whether
  the classifier returns `unknown` for a message that is plainly not a
  support request.

## Model comparison

Run on 2026-10-05 with `CHAT_USAGE_OUT=/tmp/usage.json` set:

| Model                  | Cases passed | Tokens in | Tokens out |
|------------------------|--------------|-----------|------------|
| minimax/minimax-m3     | 5/5          | 1733      | 573        |
| xiaomi/mimo-v2.6-flash | 5/5          | 965       | 376        |

Both models got every case right on category, including the ambiguous case
(both picked `technical`) and the off-topic case (both picked `unknown`).
Urgency varied between runs and between models on the sales and ambiguous
cases — those are judgment calls, since the eval only checks that urgency
is in the allowed set.

See `CHECKS.md` for the full observation notes.

## Spec corrections applied

The agent's first draft of `spec.md` listed nine numbered behaviors in the
Behavior section. I consolidated them down to the five the lab requires
(parsing, allowed sets, clear messages, ambiguous messages, off-topic
messages) and added an explicit empty-reply failure case in Failure
handling. I also rewrote the sales case in `cases.json` to remove any
mention of billing, so it is unambiguously sales.

## One line of code

This is the line in `classifier.py` that extracts the JSON from the
model's reply when the model wraps it in prose:

```python
reply = json.loads(text[start : end + 1])
```

`text` is the model's raw reply. `start` is the index of the first `{` and
`end` is the index of the last `}` in that string (computed just above).
So `text[start : end + 1]` is the slice from the opening brace to the
closing brace, inclusive — and we hand that slice to `json.loads`.

Two details worth knowing:

- We only reach this line if the first attempt — `json.loads(text)` —
  failed, meaning the model said something around the JSON, like
  `Sure! {"category": "billing", ...} hope that helps.`
- The `+ 1` matters because Python's slice syntax excludes the end index.
  Without it, the closing `}` would be sliced off and the JSON would not
  parse again.