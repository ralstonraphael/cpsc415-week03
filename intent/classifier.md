# Intent: Support-message classifier

## Goal
A small command-line program that reads one customer-support message, asks a language model to sort it, and prints a single JSON object with three fields: `category` (one of billing, technical, sales, or unknown), `urgency` (low, medium, or high), and `reason` (one sentence). A short eval runs five known messages through it so two different models can be compared on exactly the same cases.

## Who it is for
Someone triaging a shared support inbox that gets a mix of billing questions, bug reports, and sales inquiries. Today they read every message and route it by hand. For this course, it is also the practice case for getting structured data out of a model and checking it against known answers.

## Constraints
- Python standard library only (see the spec for the language decision).
- Calls a hosted model. The default route is an OpenAI-compatible chat endpoint, with the endpoint, model, and key taken from environment variables. The author has a Claude subscription and no OpenRouter key, so the program can also reach Claude models through the `claude` command-line tool. Either way, changing models means changing one variable.
- No API key in the repository, in a commit, or in any output.
- Cost ceiling: a full eval (five cases, two models) should cost a few cents at most, at list price.
- Due Monday, October 5, 2026, 1:30 PM.

## Not in scope
- Replying to the customer, connecting to a real inbox, storing messages, a web interface, or authentication.
- Languages other than English, and messages longer than a short paragraph.
- Production concerns: retries, rate limiting, caching, batching.
- Relying on a model's built-in structured-output feature. It may be tried as an extra, but the eval must not depend on it.
- Automated tests beyond the five-case eval, a written plan, and pull requests. Those come in later weeks.

## Success looks like
1. Running the program on a clear billing message prints one JSON object with exactly the three fields and `category` set to `billing`.
2. A message that is not a support request at all (for example, a note about lunch plans) comes back as `unknown`.
3. The eval prints PASS or FAIL for each of the five cases and a summary line with the number passed and the tokens used. Running it again with only `CHAT_MODEL` changed compares a second model on the same cases.
4. If a model's reply is not valid JSON, has a value outside the allowed set, or is empty, that case is reported as FAIL and the eval carries on to the next case instead of crashing.

## Open questions
- Urgency scale: low, medium, high. Is a three-level scale enough, or should it have more levels?
- The ambiguous case: which two categories should it accept?

**Approved by:** _pending_
