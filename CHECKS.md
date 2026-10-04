# Checks

Two hosted models, five cases, two runs each, on October 4, 2026.

**How these were run.** `CHAT_BACKEND=claude-cli`, which calls the `claude` command in headless mode on a Claude subscription. There is no OpenRouter key, so there is no OpenRouter Activity page to check against: token counts and costs are what the `claude` tool reported, and cost is list price, not billed per call. Command for each run:

```
CHAT_BACKEND=claude-cli CHAT_MODEL=<model> python3 eval.py
```

The `http` backend was exercised only against a local mock server, never a real endpoint.

## Results by case

Each cell is the result, then the model's `category/urgency`. Both models gave the same answer in run 1 and run 2 for every case.

| Case | Accepts | claude-haiku-4-5-20251001 | claude-sonnet-5 |
|---|---|---|---|
| billing-clear | billing | PASS billing/high | PASS billing/medium |
| technical-clear | technical, urgency high | PASS technical/high | PASS technical/high |
| sales-clear | sales | PASS sales/medium | PASS sales/medium |
| ambiguous-billing-or-technical | billing or technical | PASS technical/high | PASS billing/high |
| not-support-unknown | unknown | PASS unknown/low | PASS unknown/low |
| **Passed** | | **5/5, 5/5** | **5/5, 5/5** |

## Run totals

| Run | tokens in | tokens out | of which thinking | cost (list price) | seconds |
|---|---|---|---|---|---|
| Haiku run 1 | 3,162 | 1,827 | not captured | not captured | 30.7 |
| Haiku run 2 | 3,160 | 1,921 | 1,638 | $0.0128 | 29.2 |
| Sonnet run 1 | 3,960 | 269 | not captured | not captured | 17.5 |
| Sonnet run 2 | 3,961 | 248 | 0 | $0.0104 | 24.2 |

Run 1 happened before the code captured thinking tokens and cost. The commit "Report cost and thinking tokens where the backend provides them" explains why that was added.

## Failures

None. No case failed on either model in either run, so there are no failures to classify as judgment calls or real errors.

The failure paths in the spec (not JSON, a field outside the allowed set, an empty reply, HTTP errors, a missing key) were checked against a local mock server before any real model call: 31 checks, all passing. That script is not committed, because automated tests are out of scope this week. No real model triggered any of those paths.

## Observations

These are observations from five cases and two runs, not a ranking.

1. **The models agreed on every clear case and differed on judgment.** On the ambiguous case Haiku said technical and Sonnet said billing; both are accepted, which is what that case is for. On billing-clear Haiku rated urgency high and Sonnet medium. The eval does not check urgency on that case, so that difference is a judgment call, not a failure.
2. **Reply format differed.** In a separate check (one call per case, per model), all 5 of Haiku's replies were wrapped in a ```` ```json ```` code fence, so none parsed directly. All 5 of Sonnet's were bare JSON. Without the extraction fallback in `classify.py`, Haiku would have failed every case despite giving correct answers.
3. **Haiku spent most of its output on thinking.** In run 2, 1,638 of Haiku's 1,921 output tokens (85%) were thinking tokens. Sonnet reported 0. That accounts for Haiku's output being about seven times Sonnet's.
4. **The cost estimate in the spec was half right.** The spec estimated $0.012 for Haiku (observed $0.0128) and about $0.05 for the two-model comparison. Observed: Sonnet $0.0104 and both together $0.0232. The estimate overshot because it assumed Sonnet would cost three times as much per token and use similar token counts. The reported costs fit $1 per million input and $5 per million output tokens for Haiku, and $2 and $10 for Sonnet, so about twice Haiku's price, not three times. I worked those prices out from the reported costs; I did not look them up.
5. **Input tokens were far above the prompt size.** About 630 (Haiku) and 790 (Sonnet) input tokens per call, against roughly 150 tokens of instruction and message. I infer that the `claude` tool adds its own overhead.
6. **Time.** Haiku took about 6 seconds per case and Sonnet about 3.5 to 5. Each call starts a new `claude` process, so this is a rough comparison.
7. **Passing 5/5 on both says the cases are easy for these models, not that the models are equal.**
