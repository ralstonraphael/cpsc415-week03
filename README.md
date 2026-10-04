# Support-message classifier

CPSC 415 Week 3 lab. A command-line program that reads one customer-support message, asks a model for JSON with `category`, `urgency` and `reason`, and a five-case eval that runs the same cases against two models.

Built with a coding agent (Claude Code), as the course requires. Most commits carry a `Co-Authored-By` trailer showing it. The chain is in the history: [intent](intent/classifier.md), then [spec](spec.md), then code.

## How to run it

Python 3, standard library only. Pick a backend with `CHAT_BACKEND`.

**`http` (the default, the class route).** Any OpenAI-compatible chat endpoint:

```
export CHAT_BASE_URL=https://openrouter.ai/api/v1     # the default
export CHAT_MODEL=minimax/minimax-m3
export OPENROUTER_API_KEY=...                         # from the environment, never a file
python3 classify.py "I was charged twice this month"
python3 eval.py
```

**`claude-cli` (used for the results below).** Calls the `claude` command in headless mode on the Claude login already on the machine. No key needed:

```
export CHAT_BACKEND=claude-cli
CHAT_MODEL=claude-haiku-4-5-20251001 python3 eval.py
CHAT_MODEL=claude-sonnet-5 python3 eval.py
```

The results were produced on a Claude subscription, not OpenRouter, so there is no OpenRouter Activity page to verify them against. Token counts and costs are what the `claude` tool reported. The `http` backend has only been exercised against a local mock server.

Comparing models means changing only `CHAT_MODEL`. `eval.py` exits 0 only if every case passes.

## The five cases and what each is for

| Case | What it catches |
|---|---|
| `billing-clear` | Baseline: a plain payment problem with money words in it. |
| `technical-clear` | A clear outage. Also checks that a full lockout is rated high urgency. |
| `sales-clear` | Purchase intent, not a problem report. Guards against sending everything to technical. |
| `ambiguous-billing-or-technical` | Two defensible answers, so it accepts either. Tests whether a failure is a judgment call or a real error. |
| `not-support-unknown` | Not a support request at all. Must come back `unknown`, not forced into a category. |

## Comparison

Full tables and observations are in [CHECKS.md](CHECKS.md).

| Model | Passed (run 1, run 2) | Output tokens, run 2 | Thinking tokens, run 2 | Cost, run 2 | Replies needing the extraction line |
|---|---|---|---|---|---|
| claude-haiku-4-5-20251001 | 5/5, 5/5 | 1,921 | 1,638 | $0.0128 | 5 of 5 |
| claude-sonnet-5 | 5/5, 5/5 | 248 | 0 | $0.0104 | 0 of 5 |

Both models passed every case in both runs. They differed on the ambiguous case (Haiku said technical, Sonnet said billing, and both are accepted), and in how they answered: Haiku put 85% of its output into thinking and wrapped every reply in a code fence, while Sonnet returned bare JSON with no thinking.

## One correction to the spec, and why

The first draft of the spec compared `minimax/minimax-m3` and `xiaomi/mimo-v2.6-flash` through OpenRouter, the class default. I have a Claude subscription and no OpenRouter key, so I told the agent to use Claude instead. The spec now compares `claude-haiku-4-5-20251001` and `claude-sonnet-5` through the `claude` tool, and keeps the `http` backend as the default route so the same eval can run against the OpenRouter models later. It is the commit "Correct intent and spec: use Claude models, no OpenRouter key".

A later spec change is also in the history: once Haiku's output tokens came out about seven times Sonnet's, the summary line was changed to report thinking tokens and cost.

## One line I can explain

```python
match = re.search(r"\{.*\}", text, re.DOTALL)  # first "{" to last "}", across lines
```

This is in `extract_json` in `classify.py`. A model asked for JSON does not always send only JSON. It may add a sentence before it or wrap it in a code fence, and then `json.loads` on the whole reply raises an error. The pattern finds everything from the first `{` to the last `}`, and `re.DOTALL` lets `.` match newlines so a multi-line object is caught. Only that slice is parsed.

It matters here: all 5 of Haiku's replies came wrapped in a code fence, so without this line Haiku would have failed every case on format alone while giving the right answers. The line is greedy on purpose. If a reply held two separate objects, the slice would not be valid JSON and the case would fail as "not JSON". That is a deliberate choice: fail loudly rather than guess which object was meant.

## Why the spec says what it says

- **The ambiguous case accepts two answers** because a plan upgrade that did not take effect really is either a payment problem or an account bug. Marking one of them wrong would test the case writer's opinion, not the model.
- **Only the outage case checks urgency.** Urgency is a judgment call for most messages. A full lockout is the one case where `high` is not arguable.
- **A reply that is not valid JSON is a FAIL, not repaired.** The extraction line handles wrapping around good JSON. Past that, guessing at what the model meant would hide the failures the eval exists to find.
