# Intent: classifier

## Goal
A command-line program that, given one customer support message, asks a model to classify it and prints a single JSON object with three fields — `category`, `urgency`, and a one-sentence `reason` — so a support lead can route the message to the right person and prioritize urgent ones.

## Who it is for
A support lead who triages incoming customer messages by hand. Today they read each message and decide who should handle it and how fast; the classifier is meant to do that first pass for them, not to reply to customers or replace their judgment.

The JSON is also read by an eval runner during the lab, and may later be read by a routing script.

## Constraints
- **Language:** Python 3, standard library only (per `CLAUDE.md`).
- **Model:** `minimax/minimax-m3` via OpenRouter, the default for this course.
- **Invocation:** command line. One message per run.
- **Output contract:** a single JSON object on stdout, parseable by `json.loads`, with exactly three top-level fields. Anything else is a failure for the consumer.
  - `category` ∈ `{"billing", "technical", "sales", "unknown"}`
  - `urgency` ∈ `{"low", "medium", "high"}`
  - `reason` is a single sentence (string).
- **Boundary on "unknown":** return `"unknown"` only when the message is clearly not a support request (greeting, spam, unrelated question). A real but ambiguous support message still gets a best-guess category — the lead wants every real support message routed somewhere.

## Not in scope
- Reading from inboxes, ticketing systems, or batch files. One message per run.
- Generating a response back to the customer. The classifier classifies; it does not reply.
- Storing, logging, or persisting messages or results.
- A user interface beyond the command line.
- Translation of the message.
- The eval runner itself (it is a separate program that reads the JSON this program emits).
- Any retry, fallback, or caching layer around the model call beyond what the spec calls for.

## Success looks like
1. A support lead can run the program, hand it a message, and see a parseable JSON object on stdout whose three fields are all present and valid.
2. Off-topic messages come back as `category: "unknown"`; real but ambiguous support messages come back as a best-guess category, never `"unknown"`.
3. The eval runner can read every output without special-casing, and a future routing script can do the same by parsing the same three fields.

## Open questions
- The exact command-line input mechanism (stdin vs. argv vs. file) is left to the spec, since it does not change what the program does for the lead.
- How the program surfaces a hard failure (model error, bad key, timeout) is left to the spec; the contract is that success means a single valid JSON object on stdout, and anything else is a failure for the consumer.

**Approved by:** <your name>, <date>
