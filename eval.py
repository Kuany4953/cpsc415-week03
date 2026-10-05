"""Run the classifier against the cases in cases.json and report results.

For each case, eval.py invokes classifier.py via stdin and parses the JSON it
emits on stdout. It compares the resulting category against the case's
expected_category (or the allowed_categories list for ambiguous cases) and
prints PASS or FAIL per case. At the end it prints a summary with totals,
including the sum of prompt_tokens and completion_tokens read from the
optional usage side file (n/a if missing or unset).

Standard library only.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load_cases(path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"could not read {path}: {e}", file=sys.stderr)
        sys.exit(1)
    try:
        cases = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"cases.json is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(cases, list):
        print("cases.json must be a JSON array", file=sys.stderr)
        sys.exit(1)
    return cases


def _run_classifier(message: str, env: dict) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(HERE / "classifier.py")],
        input=message,
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _evaluate_case(case: dict, env: dict) -> dict:
    message = case["message"]
    rc, stdout, stderr = _run_classifier(message, env)
    result = {
        "id": case["id"],
        "kind": case["kind"],
        "rc": rc,
        "stderr": stderr.strip(),
        "stdout": stdout,
        "category": None,
        "expected": None,
        "passed": False,
        "reason": "",
    }
    expected = case.get("expected_category")
    allowed = case.get("allowed_categories")
    if expected is not None:
        result["expected"] = expected
    elif allowed is not None:
        result["expected"] = "one of " + ", ".join(allowed)
    else:
        result["expected"] = "<unspecified>"

    if rc != 0:
        result["reason"] = f"classifier exited {rc}: {stderr.strip() or '<no stderr>'}"
        return result
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        result["reason"] = f"classifier stdout is not JSON: {stdout!r}"
        return result
    if not isinstance(parsed, dict):
        result["reason"] = f"classifier stdout is not a JSON object: {stdout!r}"
        return result
    category = parsed.get("category")
    urgency = parsed.get("urgency")
    reason = parsed.get("reason")
    if not isinstance(category, str) or not isinstance(urgency, str) or not isinstance(reason, str):
        result["reason"] = f"classifier output missing fields: {parsed!r}"
        return result
    result["category"] = category
    if expected is not None:
        result["passed"] = category == expected
    elif allowed is not None:
        result["passed"] = category in allowed
    if not result["passed"]:
        result["reason"] = f"got category={category!r}, expected {result['expected']!r}"
    else:
        result["reason"] = f"category={category!r} urgency={urgency!r}"
    return result


def _load_usage_totals(path: Path) -> tuple[int | None, int | None]:
    if not path:
        return None, None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None, None
    prompt_total = 0
    completion_total = 0
    saw_any = False
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, dict):
            continue
        p = entry.get("prompt_tokens")
        c = entry.get("completion_tokens")
        if isinstance(p, int):
            prompt_total += p
            saw_any = True
        if isinstance(c, int):
            completion_total += c
            saw_any = True
    if not saw_any:
        return None, None
    return prompt_total, completion_total


def main() -> int:
    cases_path = HERE / "cases.json"
    cases = _load_cases(cases_path)

    usage_path = os.environ.get("CHAT_USAGE_OUT", "").strip()
    env = os.environ.copy()
    if usage_path:
        # Truncate so each eval run starts fresh.
        try:
            Path(usage_path).write_text("", encoding="utf-8")
        except OSError:
            pass

    results: list[dict] = []
    for case in cases:
        result = _evaluate_case(case, env)
        results.append(result)
        label = "PASS" if result["passed"] else "FAIL"
        print(f"{label} {result['id']} ({result['kind']}): {result['reason']}")

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print()
    print(f"summary: {passed}/{total} passed")

    if usage_path:
        prompt_total, completion_total = _load_usage_totals(Path(usage_path))
        if prompt_total is None and completion_total is None:
            print("tokens: in=n/a out=n/a (no usage data recorded)")
        else:
            print(
                f"tokens: in={prompt_total if prompt_total is not None else 'n/a'} "
                f"out={completion_total if completion_total is not None else 'n/a'}"
            )
    else:
        print("tokens: in=n/a out=n/a (CHAT_USAGE_OUT not set)")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())