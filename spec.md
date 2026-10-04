# Spec

## Intent
Implements [intent/classifier.md](intent/classifier.md).

## Components

### Support-message classifier (`classify.py`) and eval runner (`eval.py`)
- **What it does:** `classify.py` takes one support message, asks a model to classify it, and prints one JSON object with `category`, `urgency`, and `reason`. `eval.py` reads five cases from `cases.json`, runs each through the same code, prints PASS or FAIL per case, and ends with a summary line (cases passed, tokens in and out).
- **Language:** Python 3. **Why:** the standard library already has an HTTP client (`urllib.request`) and a JSON parser (`json`), so the whole program is one short file with no install or build step. The alternative was Java 21 as a single-file program: it also runs without a build tool, but Java's standard library has no JSON parser, so it would need either a jar or a hand-written parser that the spec would then have to justify. The trade-off is that Python gives up compile-time type checking, which is why the eval validates every field of the reply at run time.
- **Model:** default `minimax/minimax-m3`, compared on the same five cases against `xiaomi/mimo-v2.6-flash`, both through OpenRouter. **Why:** the class model is the baseline, and the second is a cheaper, faster model, so the comparison answers whether a cheaper model is good enough for a task this small. What differed is recorded in `CHECKS.md` after the runs, as observations, not as a ranking.
- **Interfaces:**
  - Input: one message as a command-line argument.
  - Environment: `CHAT_BASE_URL` (default `https://openrouter.ai/api/v1`), `CHAT_MODEL`, `OPENROUTER_API_KEY`.
  - Output: the JSON object on stdout. Token counts go to stderr from `classify.py` and into the summary line from `eval.py`.
  - Files: `cases.json` (the five cases), `CHECKS.md` (results).
- **Dependencies:** none beyond Python 3 and network access to the chat endpoint.

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
- **Missing key:** exit before sending anything, with a message that names `OPENROUTER_API_KEY`. The key is never printed.
- **HTTP error or timeout** (401, 402, 429, 5xx, network): the case is FAIL with the status code and the provider's message, and the eval continues. A 401 or 402 stops the run early with a message about the key or the balance, since every remaining case would fail the same way.

## Cost estimate
About 250 tokens per classification (a short instruction, a message of 30 to 60 tokens, a reply of about 60). One eval run is five cases on one model, so about 1,250 tokens, and the full comparison is about 2,500 tokens. At a rough upper bound of $1 per million tokens that is a quarter of a cent per full comparison, and a semester of re-running it 50 times is still well under a dollar. A model that spends output on hidden reasoning could use ten times as many tokens, which is still pennies. Observed numbers replace this estimate in `CHECKS.md`.

## Out of scope
Carried over from the intent: replying to customers, any inbox integration or storage, a web interface, languages other than English, retries, rate limiting and caching, depending on built-in structured output, automated tests beyond the five-case eval, a written plan, and pull requests.
