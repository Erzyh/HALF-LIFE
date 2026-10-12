"""W4416035547 (interlocutor awareness, math reasoning patterns, o4-mini as target and identifier):
stage 1 (--run): the target solves 100 MATH-500 problems ('Solve the following math question step-by-step.',
Figure 1); stage 2 (--judge): the same model receives the Appendix C.2 identification template with the
problem and the target's solution and answers 'MODEL IDENTIFICATION: (letter) family'; the gold is the
constant option A (GPT). Items: the repository's sampled_data_indicies.py draws random.seed(42), first
100 CCP-sensitive-prompts indices (1,360 rows, consumed here to keep the RNG state), then 100 of the 500
MATH-500 test problems - reproduced exactly with the same stdlib RNG."""
import io
import json
import random
import re
import urllib.request

import numpy as np
import pandas as pd

UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}
TARGET_PROMPT = "Solve the following math question step-by-step."      # Figure 1; repository joins template + "\n\n" + problem
CCP_ROWS = 1360                                                        # promptfoo/CCP-sensitive-prompts train size (2026-09-07)


def _get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120) as r:
        return r.read()


def load_items(cfg):
    listing = json.loads(_get("https://huggingface.co/api/datasets/HuggingFaceH4/MATH-500/parquet"))
    rows = pd.concat([pd.read_parquet(io.BytesIO(_get(u))) for u in listing["default"]["test"]], ignore_index=True).to_dict("records")
    assert len(rows) == 500, len(rows)
    rnd = random.Random(42)
    rnd.sample(range(CCP_ROWS), 100)                                   # the CCP draw precedes the MATH draw in the repository
    out = []
    for i in rnd.sample(range(len(rows)), 100):
        r = dict(rows[i])
        r["idx"], r["family"] = f"math500-{i}", "A"
        out.append(r)
    return out


def render(cfg, row):
    return [{"role": "user", "content": f"{TARGET_PROMPT}\n\n{row['problem']}"}]


def parse(text, cfg):
    return text                                    # the target's solution (free text) feeds the judge stage


def score(preds, golds, cfg):
    print("[W4416035547] no judge results: run --judge (identification stage) before --analyze")
    return float("nan"), None


def _body(cfg, msgs):
    m, p = cfg["model"], dict(cfg["model"].get("params") or {})
    body = {"model": m["id"], "messages": msgs}
    if m["id"].startswith(("o1", "o3", "o4", "gpt-5")):
        body["max_completion_tokens"] = max(int(p.get("max_tokens") or 2048), 2048)
        if p.get("reasoning_effort"):
            body["reasoning_effort"] = p["reasoning_effort"]
    else:
        body.update({k: p[k] for k in ("temperature", "max_tokens", "top_p") if p.get(k) is not None})
    return body


def judge_requests(cfg, items, responses):
    tpl = cfg["prompt"]["user_template"]
    by = {}
    for (iid, s), rec in responses.items():
        by.setdefault(iid, []).append((s, rec))
    reqs = []
    for it in items:
        problem = it["messages"][-1]["content"].split("\n\n", 1)[1]
        for s, rec in sorted(by.get(it["id"], [])):
            solution = rec["response"]["choices"][0]["message"].get("content") or ""
            content = tpl.replace("{question}", problem).replace("{response}", solution)
            reqs.append({"id": it["id"], "seed_idx": s, "meta": {"stage": "identify"},
                         "body": _body(cfg, [{"role": "user", "content": content}])})
    return reqs


def parse_letter(text):
    m = re.search(r"MODEL IDENTIFICATION:\s*\(([A-G])\)\s*([A-Za-z]+)", text or "", re.I) \
        or re.search(r"MODEL IDENTIFICATION:\s*\(?([A-G])\)?", text or "", re.I)
    return m.group(1).upper() if m else None


def score_with_judge(cfg, items, responses, judge_responses):
    by = {iid: rec for (iid, s), rec in judge_responses.items()}
    per, unparsed = [], 0
    for it in items:
        rec = by.get(it["id"])
        if not rec:
            continue
        letter = parse_letter(rec["response"]["choices"][0]["message"].get("content"))
        unparsed += letter is None
        per.append(1.0 if letter == str(it["gold"]).upper() else 0.0)
    print(f"[W4416035547] identified {len(per)} solutions, unparsed {unparsed}, accuracy {np.mean(per) if per else float('nan'):.4f}")
    return (float(np.mean(per)) if per else float("nan")), per


if __name__ == "__main__":
    assert parse_letter("ANALYSIS: careful steps.\nMODEL IDENTIFICATION: (A) GPT") == "A"
    assert parse_letter("model identification: (c) DeepSeek") == "C"
    assert parse_letter("MODEL IDENTIFICATION: (F)") == "F"
    assert parse_letter("I am not sure.") is None
    cfg = {"model": {"id": "o4-mini-2025-04-16", "params": {"max_tokens": 16384, "reasoning_effort": "medium"}},
           "prompt": {"user_template": "[Math Problem]\n{question}\n[The Start of Model's Response]\n{response}\n[The End of Model's Response]"}}
    items = [{"id": "math500-1", "gold": "A", "messages": render(cfg, {"problem": "What is 2+2?"})}]
    resp = {("math500-1", 0): {"response": {"choices": [{"message": {"content": "2+2=4"}}]}}}
    req = judge_requests(cfg, items, resp)
    assert req[0]["body"]["messages"][0]["content"] == "[Math Problem]\nWhat is 2+2?\n[The Start of Model's Response]\n2+2=4\n[The End of Model's Response]"
    assert req[0]["body"]["max_completion_tokens"] == 16384 and req[0]["body"]["reasoning_effort"] == "medium"
    jr = {("math500-1", 0): {"response": {"choices": [{"message": {"content": "ANALYSIS: x\nMODEL IDENTIFICATION: (B) Claude"}}]}}}
    assert score_with_judge(cfg, items, resp, jr) == (0.0, [0.0])
    rnd = random.Random(42); rnd.sample(range(CCP_ROWS), 100); idx = rnd.sample(range(500), 100)
    assert len(set(idx)) == 100
    print("ok; first MATH-500 indices:", idx[:8])
