#!/usr/bin/env python3
"""Classify one customer-support message and print JSON: category, urgency, reason.

Usage:  python3 classify.py "message text"

Backends, chosen with CHAT_BACKEND:
  http        An OpenAI-compatible chat endpoint (the default). Reads CHAT_BASE_URL
              (default https://openrouter.ai/api/v1), CHAT_MODEL and OPENROUTER_API_KEY.
  claude-cli  The `claude` command in headless mode, using the existing Claude login.
              Reads only CHAT_MODEL.

Standard library only. The API key is read from the environment and never printed.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

CATEGORIES = ("billing", "technical", "sales", "unknown")
URGENCIES = ("low", "medium", "high")
FIELDS = {"category", "urgency", "reason"}

SYSTEM = (
    "You classify one customer-support message. "
    "Reply with only a JSON object with exactly these fields: "
    '"category" (one of billing, technical, sales, unknown), '
    '"urgency" (one of low, medium, high), '
    'and "reason" (one sentence). '
    "Use unknown when the message is not a request for support or sales help. "
    "Do not add any other text."
)


class ModelError(Exception):
    """The model could not be reached or returned an error. fatal means stop the eval."""

    def __init__(self, message, fatal=False):
        super().__init__(message)
        self.fatal = fatal


class Reply:
    def __init__(self, text, tokens_in, tokens_out, finish_reason, seconds, cost=None, thinking=0):
        self.cost = cost          # dollars at list price, when the backend reports it
        self.thinking = thinking  # part of tokens_out spent on hidden reasoning
        self.text = text
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.finish_reason = finish_reason
        self.seconds = seconds


def backend():
    return os.environ.get("CHAT_BACKEND", "http")


def model():
    name = os.environ.get("CHAT_MODEL")
    if not name:
        raise ModelError("CHAT_MODEL is not set", fatal=True)
    return name


def call_http(message, model_name):
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise ModelError("OPENROUTER_API_KEY is not set", fatal=True)
    base = os.environ.get("CHAT_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
    body = json.dumps({
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": message},
        ],
        "temperature": 0,
        "max_tokens": int(os.environ.get("CHAT_MAX_TOKENS", "600")),
    }).encode("utf-8")
    request = urllib.request.Request(
        base + "/chat/completions",
        data=body,
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key},
    )
    start = time.time()
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            data = json.load(response)
    except urllib.error.HTTPError as err:
        detail = err.read().decode("utf-8", "replace")[:200]
        raise ModelError("HTTP %d: %s" % (err.code, detail), fatal=err.code in (401, 402))
    except (urllib.error.URLError, TimeoutError) as err:
        raise ModelError("network error: %s" % err)
    try:
        choice = data["choices"][0]
        text = choice["message"].get("content") or ""
    except (KeyError, IndexError, TypeError):
        raise ModelError("unexpected response shape: %s" % json.dumps(data)[:200])
    usage = data.get("usage") or {}
    details = usage.get("completion_tokens_details") or {}
    return Reply(text, usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0),
                 choice.get("finish_reason"), time.time() - start,
                 cost=usage.get("cost"), thinking=details.get("reasoning_tokens") or 0)


def call_cli(message, model_name):
    command = [
        "claude", "-p", "--model", model_name, "--output-format", "json",
        "--system-prompt", SYSTEM, "--tools", "", "--no-session-persistence",
        "--disable-slash-commands", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
        "--setting-sources", "local",
    ]
    start = time.time()
    try:
        # The message goes in on stdin so a message starting with "-" is never read as a flag.
        done = subprocess.run(command, input=message, capture_output=True, text=True,
                              timeout=120, cwd=tempfile.gettempdir())
    except FileNotFoundError:
        raise ModelError("the `claude` command was not found", fatal=True)
    except subprocess.TimeoutExpired:
        raise ModelError("claude timed out after 120 seconds")
    if done.returncode != 0:
        raise ModelError("claude exited %d: %s" % (done.returncode, (done.stderr or done.stdout)[:200]))
    try:
        data = json.loads(done.stdout)
    except ValueError:
        raise ModelError("claude did not return JSON: %s" % done.stdout[:200])
    if data.get("is_error"):
        raise ModelError("claude reported an error: %s" % str(data.get("result"))[:200])
    usage = data.get("usage") or {}
    tokens_in = (usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0)
                 + usage.get("cache_read_input_tokens", 0))
    details = usage.get("output_tokens_details") or {}
    return Reply(data.get("result") or "", tokens_in, usage.get("output_tokens", 0),
                 data.get("stop_reason"), time.time() - start,
                 cost=data.get("total_cost_usd"), thinking=details.get("thinking_tokens") or 0)


def extract_json(text):
    """Return the JSON value inside a model reply, or raise ValueError."""
    try:
        return json.loads(text)
    except ValueError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)  # first "{" to last "}", across lines
    if not match:
        raise ValueError("not JSON")
    try:
        return json.loads(match.group(0))
    except ValueError:
        raise ValueError("not JSON")


def check_fields(value):
    """Return a description of what is wrong with the parsed reply, or None if it is fine."""
    if not isinstance(value, dict):
        return "reply is JSON but not an object"
    missing = FIELDS - value.keys()
    if missing:
        return "missing field: " + ", ".join(sorted(missing))
    extra = value.keys() - FIELDS
    if extra:
        return "extra field: " + ", ".join(sorted(extra))
    if value["category"] not in CATEGORIES:
        return 'category "%s" is not one of %s' % (value["category"], ", ".join(CATEGORIES))
    if value["urgency"] not in URGENCIES:
        return 'urgency "%s" is not one of %s' % (value["urgency"], ", ".join(URGENCIES))
    if not isinstance(value["reason"], str) or not value["reason"].strip():
        return "reason is empty"
    return None


def classify(message):
    """Classify one message. Returns a dict: ok, result, error, reply, fatal."""
    out = {"ok": False, "result": None, "error": None, "reply": None, "fatal": False}
    try:
        model_name = model()
        if backend() == "claude-cli":
            reply = call_cli(message, model_name)
        elif backend() == "http":
            reply = call_http(message, model_name)
        else:
            raise ModelError("CHAT_BACKEND must be http or claude-cli", fatal=True)
    except ModelError as err:
        out["error"] = str(err)
        out["fatal"] = err.fatal
        return out
    out["reply"] = reply
    if not reply.text.strip():
        out["error"] = "empty reply (finish_reason=%s, tokens_out=%d); try a larger CHAT_MAX_TOKENS" % (
            reply.finish_reason, reply.tokens_out)
        return out
    try:
        value = extract_json(reply.text)
    except ValueError as err:
        out["error"] = "%s: %s" % (err, reply.text.strip()[:120].replace("\n", " "))
        return out
    problem = check_fields(value)
    if problem:
        out["error"] = problem
        return out
    out["ok"] = True
    out["result"] = value
    return out


def main(argv):
    if len(argv) != 2:
        print('usage: python3 classify.py "message text"', file=sys.stderr)
        return 2
    out = classify(argv[1])
    reply = out["reply"]
    if reply:
        extra = "" if reply.cost is None else "  $%.4f" % reply.cost
        print("tokens in=%d out=%d (thinking %d)  %.1fs%s" % (
            reply.tokens_in, reply.tokens_out, reply.thinking, reply.seconds, extra), file=sys.stderr)
    if not out["ok"]:
        print("error: " + out["error"], file=sys.stderr)
        return 1
    print(json.dumps(out["result"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
