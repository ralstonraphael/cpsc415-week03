#!/usr/bin/env python3
"""Run every case in cases.json through classify.py and print PASS or FAIL for each.

Usage:  python3 eval.py [cases.json]

Uses the same CHAT_BACKEND, CHAT_MODEL (and key) variables as classify.py, so comparing
two models means changing only CHAT_MODEL. A failing case never stops the run, except a
fatal error such as a bad key, which would make every remaining case fail the same way.
"""
import json
import sys

import classify


def judge(case, result):
    """Return why this result fails the case, or None if it passes."""
    if result["category"] not in case["accept"]:
        return 'category "%s" is not one of %s' % (result["category"], case["accept"])
    wanted = case.get("expect_urgency")
    if wanted and result["urgency"] not in wanted:
        return 'urgency "%s" is not one of %s' % (result["urgency"], wanted)
    return None


def main(argv):
    path = argv[1] if len(argv) > 1 else "cases.json"
    with open(path, encoding="utf-8") as handle:
        cases = json.load(handle)
    passed = tokens_in = tokens_out = thinking = 0
    seconds = 0.0
    cost = None  # stays None unless the backend reports a cost
    for case in cases:
        out = classify.classify(case["message"])
        reply = out["reply"]
        timing = ""
        if reply:
            tokens_in += reply.tokens_in
            tokens_out += reply.tokens_out
            thinking += reply.thinking
            seconds += reply.seconds
            if reply.cost is not None:
                cost = (cost or 0.0) + reply.cost
            timing = "  (%.1fs, %d in / %d out, %d thinking)" % (
                reply.seconds, reply.tokens_in, reply.tokens_out, reply.thinking)
        if out["ok"]:
            problem = judge(case, out["result"])
            got = "%s/%s" % (out["result"]["category"], out["result"]["urgency"])
        else:
            problem = out["error"]
            got = "-"
        if problem is None:
            passed += 1
            print("PASS %-32s %s%s" % (case["id"], got, timing))
        else:
            print("FAIL %-32s %s  <- %s%s" % (case["id"], got, problem, timing))
        if out["fatal"]:
            print("stopping early: %s" % out["error"])
            break
    print("SUMMARY backend=%s model=%s passed=%d/%d tokens_in=%d tokens_out=%d thinking=%d cost=%s seconds=%.1f" % (
        classify.backend(), classify.os.environ.get("CHAT_MODEL", "?"), passed, len(cases),
        tokens_in, tokens_out, thinking, "n/a" if cost is None else "$%.4f" % cost, seconds))
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
