"""Classify a single customer support message.

Reads one UTF-8 message from stdin, sends it to an OpenRouter-compatible chat
completions endpoint, validates the model's reply, and prints exactly one JSON
object on stdout with three string fields: category, urgency, reason. Any other
outcome is a failure: a one-line human-readable message on stderr and a non-zero
exit code, with nothing on stdout.

Standard library only.
"""

import json
import os
import sys
import urllib.error
import urllib.request

ALLOWED_CATEGORIES = {"billing", "technical", "sales", "unknown"}
ALLOWED_URGENCIES = {"low", "medium", "high"}

SYSTEM_PROMPT = (
    "You are a triage assistant for a small software company. "
    "Classify the user's message into exactly one category and one urgency level, "
    "and give one short sentence of reasoning.\n"
    "Return your answer as a JSON object with three string fields:\n"
    '  "category": one of "billing", "technical", "sales", "unknown"\n'
    '  "urgency":  one of "low", "medium", "high"\n'
    '  "reason":   one sentence explaining the choice\n'
    'Use "unknown" only when the message is clearly not a support request '
    "(greeting, spam, or unrelated question). A real but ambiguous support "
    "message must still get a best-guess category, never \"unknown\".\n"
    "Respond with JSON only. No prose before or after the JSON object."
)


def _err(msg: str) -> None:
    """Write a one-line error to stderr and exit non-zero."""
    print(msg, file=sys.stderr)
    sys.exit(1)


def _read_stdin() -> str:
    raw = sys.stdin.buffer.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        _err("stdin is not valid UTF-8")
    if not text.strip():
        _err("empty input")
    return text


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        _err(f"missing or empty env var: {name}")
    return value


def _call_model(base_url: str, model: str, api_key: str, message: str) -> dict:
    url = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        "temperature": 0,
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            status = resp.status
            payload = resp.read()
    except urllib.error.HTTPError as e:
        # HTTPError also has a body — surface it on stderr for debugging,
        # but keep the message short and human-readable.
        _err(f"openrouter returned HTTP {e.code}")
    except urllib.error.URLError as e:
        _err(f"network error: {e.reason}")
    except TimeoutError:
        _err("network timeout calling openrouter")
    except OSError as e:
        _err(f"network error: {e}")
    if not 200 <= status < 300:
        _err(f"openrouter returned HTTP {status}")
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        _err("openrouter returned a non-JSON body")
    return data


def _extract_reply_and_usage(data: dict) -> tuple[dict, dict | None]:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        _err("openrouter returned no choices")
    first = choices[0]
    if not isinstance(first, dict):
        _err("openrouter returned a malformed choice")
    message = first.get("message")
    if not isinstance(message, dict):
        _err("openrouter returned no assistant message")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        _err("openrouter returned an empty assistant message")
    usage = data.get("usage")
    return {"content": content}, (usage if isinstance(usage, dict) else None)


def _parse_reply(content: str) -> dict:
    # The model is asked to reply with JSON only, but be tolerant of leading
    # or trailing prose by locating the first '{' and the matching '}'.
    text = content.strip()
    try:
        reply = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            _err("model response is not parseable as JSON")
        try:
            reply = json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            _err("model response is not parseable as JSON")
    if not isinstance(reply, dict):
        _err("model response is not a JSON object")
    category = reply.get("category")
    urgency = reply.get("urgency")
    reason = reply.get("reason")
    if not isinstance(category, str) or not isinstance(urgency, str) or not isinstance(reason, str):
        _err("model response is missing category, urgency, or reason")
    if category not in ALLOWED_CATEGORIES:
        _err(f"category {category!r} is not in the allowed set")
    if urgency not in ALLOWED_URGENCIES:
        _err(f"urgency {urgency!r} is not in the allowed set")
    if not reason.strip():
        _err("reason is empty")
    return {"category": category, "urgency": urgency, "reason": reason.strip()}


def _write_usage(usage: dict | None) -> None:
    path = os.environ.get("CHAT_USAGE_OUT", "").strip()
    if not path:
        return
    if usage is None:
        line = json.dumps({"prompt_tokens": None, "completion_tokens": None, "total_tokens": None})
    else:
        def _int(field: str):
            v = usage.get(field)
            return v if isinstance(v, int) else None
        line = json.dumps({
            "prompt_tokens": _int("prompt_tokens"),
            "completion_tokens": _int("completion_tokens"),
            "total_tokens": _int("total_tokens"),
        })
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError as e:
        _err(f"could not write usage file {path!r}: {e}")


def main() -> None:
    base_url = _require_env("CHAT_BASE_URL")
    model = _require_env("CHAT_MODEL")
    api_key = _require_env("OPENROUTER_API_KEY")
    message = _read_stdin()
    data = _call_model(base_url, model, api_key, message)
    reply, usage = _extract_reply_and_usage(data)
    parsed = _parse_reply(reply["content"])
    _write_usage(usage)
    print(json.dumps(parsed))


if __name__ == "__main__":
    main()