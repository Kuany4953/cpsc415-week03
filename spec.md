# Spec

<!-- The agent writes this from the approved intent. You validate it against the intent.
     If the spec and the intent disagree, the intent wins until you change the intent. -->

## Intent
This spec implements `intent/classifier.md`.

## Components

### classifier
- **What it does:** reads one support message from stdin, sends it to a model via the OpenRouter API, validates the response, and prints a single JSON object on stdout with three fields — `category`, `urgency`, `reason` — so a downstream consumer (the eval runner today, a routing script later) can read it without special-casing.
- **Language:** Python 3. **Why:** the standard library ships `json`, `urllib.request`, and `sys`, so the program stays a single self-contained file with no third-party dependencies — appropriate for an introductory lab and easy for the eval runner to invoke. **Alternative considered:** Java. Java would require either a JSON library jar (the one exception allowed in `CLAUDE.md`) plus more boilerplate for a CLI entrypoint and an HTTP client, with no functional gain at this scope; the cost outweighs the value of practicing Java for a single-file CLI that just shells out to one HTTP call.
- **Model:** `minimax/minimax-m3` via OpenRouter. **Why:** this is the default named in `CLAUDE.md`. The eval will also run `xiaomi/mimo-v2.6-flash` on the same cases so the two can be compared directly. The spec commits to `minimax/minimax-m3` as the chosen model; `xiaomi/mimo-v2.6-flash` is named as the comparison. Differences to be measured empirically at eval time — expected axes are category accuracy, the off-topic→`"unknown"` boundary, urgency calibration, reason quality, and per-call cost.
- **Interfaces:**
  - **Input:** one support message read from stdin, UTF-8 text, one or more lines, terminated by EOF. Stdin is chosen over argv so the program works for both interactive use (paste or type) and scripted use (pipe from a file or `echo`); argv would break for multi-line messages without quoting.
  - **Output:** exactly one JSON object on stdout, parseable by `json.loads`, with three top-level string fields: `category`, `urgency`, `reason`. Nothing else is written to stdout on a successful run.
  - **Errors:** one-line human-readable messages on stderr and a non-zero exit code. No JSON, no partial output on stdout.
  - **API:** OpenRouter-compatible chat completions endpoint. The program reads three environment variables: `CHAT_BASE_URL` (the endpoint base URL), `CHAT_MODEL` (the model identifier — e.g. `minimax/minimax-m3`, or `xiaomi/mimo-v2.6-flash` for the comparison run), and `OPENROUTER_API_KEY` (the bearer token). The lab sets all three so the same program can be evaluated against multiple models.
  - **Files:** none read or written. The program is stateless and emits no logs.
- **Dependencies:** Python 3 standard library only (`json`, `sys`, `urllib.request`, `os`); network access to an OpenRouter-compatible endpoint; three environment variables — `CHAT_BASE_URL`, `CHAT_MODEL`, `OPENROUTER_API_KEY`. No third-party Python packages.

## Behavior
Requirements the eval will check. Numbered.

1. Output is a single valid JSON object with exactly three fields: `category`, `urgency`, and `reason` (where `reason` is one sentence).
2. `category` is one of `"billing"`, `"technical"`, `"sales"`, `"unknown"`; `urgency` is one of `"low"`, `"medium"`, `"high"`.
3. A clear support message gets the correct category.
4. An ambiguous support message gets one of its two plausible categories, never `"unknown"`.
5. A message that is not a support request returns `"unknown"`.

## Failure handling
- **Empty stdin:** exit non-zero; one-line error on stderr (`empty input`); nothing on stdout.
- **Non-UTF-8 stdin:** exit non-zero; one-line error on stderr; nothing on stdout.
- **Missing or empty `OPENROUTER_API_KEY`, `CHAT_BASE_URL`, or `CHAT_MODEL`:** exit non-zero; one-line error on stderr naming the missing variable; nothing on stdout.
- **Network error or timeout calling OpenRouter:** exit non-zero; one-line error on stderr; no retry, no partial output on stdout.
- **OpenRouter returns a non-2xx response:** exit non-zero; one-line error on stderr with the status; nothing on stdout.
- **OpenRouter returns a 2xx but with an empty reply from the model** (no assistant message, or an empty content string): exit non-zero; one-line error on stderr; nothing on stdout.
- **Model response is not parseable as JSON, or is missing any of `category` / `urgency` / `reason`:** exit non-zero; one-line error on stderr; no partial classification on stdout.
- **Model response has `category` or `urgency` values outside the allowed sets:** exit non-zero; one-line error on stderr; nothing on stdout. The eval treats any of these as a failure so the contract stays strict.

## Cost estimate
- **Per call:** a short system prompt (a few sentences) plus the user message (a typical support message is on the order of 50–300 tokens) plus a short JSON response (three fields, roughly 30–60 tokens). Total well under 500 tokens per call.
- **Per call at typical OpenRouter rates for a small model:** a small fraction of a US cent.
- **Semester of use:** the eval plus ad-hoc testing — on the order of 500–1000 calls — is well under USD $1.
- **Caveat:** exact per-token rates for `minimax/minimax-m3` and `xiaomi/mimo-v2.6-flash` should be confirmed against OpenRouter's published pricing at eval time. The eval will report observed cost on the chosen cases for both models.

## Out of scope
Carried over from the intent, plus anything the design ruled out:
- Reading from inboxes, ticketing systems, or batch files — one message per run.
- Generating a response back to the customer — the classifier classifies; it does not reply.
- Storing, logging, or persisting messages or results.
- A user interface beyond the command line.
- Translation of the message.
- The eval runner itself — a separate program that reads the JSON this program emits.
- Any retry, fallback, or caching layer around the model call.
- Multi-language support — the spec assumes English-language support messages and does not require translation or other-language classification.
