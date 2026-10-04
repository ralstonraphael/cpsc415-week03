# Spec

## Intent
Implements [intent/classifier.md](intent/classifier.md).

## Components

### Support-message classifier (`classify.py`) and eval runner (`eval.py`)
- **What it does:** `classify.py` takes one support message, asks a model to classify it, and prints one JSON object with `category`, `urgency`, and `reason`. `eval.py` reads five cases from `cases.json`, runs each through the same code, prints PASS or FAIL per case, and ends with a summary line (cases passed, tokens in and out).
- **Language:** Python 3. **Why:** the standard library already has an HTTP client (`urllib.request`) and a JSON parser (`json`), so the whole program is one short file with no install or build step. The alternative was Java 21 as a single-file program: it also runs without a build tool, but Java's standard library has no JSON parser, so it would need either a jar or a hand-written parser that the spec would then have to justify. The trade-off is that Python gives up compile-time type checking, which is why the eval validates every field of the reply at run time.
- **Model:** default `claude-haiku-4-5-20251001`, compared on the same five cases against `claude-sonnet-5`, both reached through the `claude` command-line tool in headless mode (`CHAT_BACKEND=claude-cli`). **Why:** the course template asks for a cheap model against a larger one on a real task, and both of these are available through the Claude subscription already in use, so no extra account or key is needed. The alternative was the class default through OpenRouter, `minimax/minimax-m3` against `xiaomi/mimo-v2.6-flash`, which needs an OpenRouter key the author does not have. The HTTP backend stays in the code as the default route, so the same eval can run against those models later. What differed between the two models is recorded in `CHECKS.md` after the runs, as observations, not as a ranking.
- **Interfaces:**
  - Input: one message as a command-line argument.
  - Environment: `CHAT_BACKEND` (`http`, the default, or `claude-cli`) and `CHAT_MODEL`. The `http` backend also reads `CHAT_BASE_URL` (default `https://openrouter.ai/api/v1`) and `OPENROUTER_API_KEY`. The `claude-cli` backend needs only `CHAT_MODEL` and an existing Claude login.
  - Output: the JSON object on stdout. Token counts go to stderr from `classify.py` and into the summary line from `eval.py`.
  - Files: `cases.json` (the five cases), `CHECKS.md` (results).
- **Dependencies:** none beyond Python 3 and either network access to a chat endpoint (`http`) or the `claude` command-line tool, already logged in (`claude-cli`).

## Behavior
Requirements the eval checks. Every reply must also be a JSON object with exactly `category`, `urgency`, and `reason`, with `category` in {billing, technical, sales, unknown} and `urgency` in {low, medium, high}.

1. A clear billing message returns `billing`.
2. A clear technical message returns `technical`, and a message describing a full outage returns urgency `high`.
3. A clear sales message returns `sales`.
4. An ambiguous message (a plan upgrade that did not take effect) is accepted as either `billing` or `technical`.
5. A message that is not a support request returns `unknown`.

## Failure handling
- **Reply is not JSON, or has text around it:** extract the first `{ ... }` block from the reply and parse that. If nothing parses, the case is FAIL with the reason "not JSON". The eval continues.
- **A field outside the allowed set, or a missing or extra field:** the case is FAIL and the report names the field and the value.
- **Empty reply:** the case is FAIL with the reason "empty reply", and the report shows `finish_reason` and the token counts, because an empty reply with tokens billed usually means the model spent its output budget on hidden reasoning. The fix is to raise `max_tokens`, not to change the case.
- **Missing key (`http` backend):** exit before sending anything, with a message that names `OPENROUTER_API_KEY`. The key is never printed.
- **`claude-cli` backend:** if the `claude` tool is missing, not logged in, times out, or reports an error, the case is FAIL with its message and the eval continues.
- **HTTP error or timeout** (401, 402, 429, 5xx, network): the case is FAIL with the status code and the provider's message, and the eval continues. A 401 or 402 stops the run early with a message about the key or the balance, since every remaining case would fail the same way.

## Cost estimate
A first test call on `claude-haiku-4-5-20251001` used about 550 input and 380 output tokens (mostly extended thinking), so about 1,000 tokens and $0.0024 at list price per classification. One eval is five cases, about $0.012 on Haiku. Sonnet costs roughly three times as much per token, so the two-model comparison is about $0.05 at list price, and re-running it 50 times in a semester is about $2.50 at list price. On the subscription route nothing is billed per call. Observed numbers replace this estimate in `CHECKS.md`.

## Out of scope
Carried over from the intent: replying to customers, any inbox integration or storage, a web interface, languages other than English, retries, rate limiting and caching, depending on built-in structured output, automated tests beyond the five-case eval, a written plan, and pull requests.
