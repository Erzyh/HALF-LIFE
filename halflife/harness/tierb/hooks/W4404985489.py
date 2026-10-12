"""Hook for W4404985489 (Variable Extraction for Model Recovery, Table 1 row pureGPT4T, Overall F1 0.491).

load_items() reads the SciVar chunk set (589 chunks carrying the paper's 2,083 annotations; annotation =
[start, end, text, type] with type 'var desc' or 'var val'). parse() reads the 'name | description | value'
lines of a reply into prediction entries: a 'var desc' entry (name | description) and, when the value is
not None, a 'var val' entry (name | value). judge_requests() forms, per chunk and per type, the Cartesian
product of prediction and gold entries and asks the paper's GPT-4 Turbo similarity evaluator (Figure 6,
one output token, 'y'/'n'). score_with_judge() computes recall (gold entries with >= 1 match), precision
(prediction entries with >= 1 match) and F1, pooled over chunks; the per-chunk averages are printed.
"""
import json, re, urllib.request
from pathlib import Path

WID = "W4404985489"
CACHE = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / WID
UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}
JUDGE_PROMPT = ("You are a human evaluator. The following pair of text describes a variable and its description/value.\n"
                "{a}\n{b}\nPlease check if they mean the same. Answer y or n.")


def load_items(cfg):
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / "askem_variable_dataset.json"
    if not p.exists():
        p.write_bytes(urllib.request.urlopen(urllib.request.Request(cfg["items"]["file_url"], headers=UA), timeout=300).read())
    data = json.loads(p.read_text(encoding="utf-8"))
    return [{"id": str(i), "all_text": c["all_text"], "file": c.get("file"), "page": c.get("page"),
             "gold": [{"type": a[3], "text": a[2]} for a in c["annotations"]]} for i, c in enumerate(data)]


def parse(text, cfg):
    if text is None:
        return None
    out = []
    for line in text.splitlines():
        parts = [x.strip().strip("`*") for x in line.strip().strip("-* ").split("|")]
        if len(parts) < 3 or not parts[0]:
            continue
        name, desc, value = parts[0], parts[1], " | ".join(parts[2:]).strip()
        if name.lower() == "name" and desc.lower() == "description":
            continue                                             # echoed header line
        out.append({"name": name, "desc": desc, "value": value})
    return out


def _entries(preds):
    ents = []
    for e in preds or []:
        if e["desc"] and e["desc"].lower() not in ("none", "n/a", "null", "-"):
            ents.append(("var desc", f"{e['name']} | {e['desc']}"))
        if e["value"] and e["value"].lower() not in ("none", "n/a", "null", "-"):
            ents.append(("var val", f"{e['name']} | {e['value']}"))
    return ents


def _pairs(item, text):
    pe = _entries(parse(text, None))
    ge = [(g["type"], g["text"]) for g in item["gold"]]
    return pe, ge, [(pi, gi) for pi, (pt, _) in enumerate(pe) for gi, (gt, _) in enumerate(ge) if pt == gt]


def _judge_model(cfg):
    m = re.match(r"llm:([\w.\-]+)", str(cfg["metric"].get("judge", "")))
    return m.group(1) if m else cfg["model"]["id"]


def judge_requests(cfg, items, responses):
    model, reqs = _judge_model(cfg), []
    for it in items:
        for (iid, s), rec in responses.items():
            if iid != it["id"]:
                continue
            pe, ge, pairs = _pairs(it, rec["response"]["choices"][0]["message"].get("content") or "")
            for pi, gi in pairs:
                msg = JUDGE_PROMPT.replace("{a}", pe[pi][1]).replace("{b}", ge[gi][1])
                reqs.append({"id": f"{iid}|{pi}|{gi}", "seed_idx": s, "meta": {"item": iid, "pi": pi, "gi": gi, "type": pe[pi][0]},
                             "body": {"model": model, "messages": [{"role": "user", "content": msg}], "temperature": 0.0, "max_tokens": 1}})
    print(f"[{WID}] {len(reqs)} judge pairs for {len(items)} chunks")
    return reqs


def score_with_judge(cfg, items, responses, judge_responses):
    tg = tp = mg = mp = 0
    per_chunk, missing = [], 0
    for it, rec in zip(items, responses):
        s = rec.get("seed_idx", 0)
        pe, ge, pairs = _pairs(it, rec["response"]["choices"][0]["message"].get("content") or "")
        hit_p, hit_g = set(), set()
        for pi, gi in pairs:
            jr = judge_responses.get((f"{it['id']}|{pi}|{gi}", s))
            if jr is None:
                missing += 1
                continue
            if (jr["response"]["choices"][0]["message"].get("content") or "").strip().lower().startswith("y"):
                hit_p.add(pi); hit_g.add(gi)
        tg += len(ge); tp += len(pe); mg += len(hit_g); mp += len(hit_p)
        r = len(hit_g) / len(ge) if ge else None
        p = len(hit_p) / len(pe) if pe else 0.0
        per_chunk.append((r, p))
    recall, precision = mg / max(1, tg), mp / max(1, tp)
    f1 = 0.0 if recall + precision == 0 else 2 * recall * precision / (recall + precision)
    rs = [r for r, _ in per_chunk if r is not None]; ps = [p for _, p in per_chunk]
    ar, ap = sum(rs) / max(1, len(rs)), sum(ps) / max(1, len(ps))
    af = 0.0 if ar + ap == 0 else 2 * ar * ap / (ar + ap)
    print(f"[{WID}] pooled: recall {recall:.3f} precision {precision:.3f} F1 {f1:.3f} (gold {tg}, predicted {tp}); "
          f"per-chunk averages: recall {ar:.3f} precision {ap:.3f} F1 {af:.3f}; judge verdicts missing {missing}")
    return f1, None


def score(preds, golds, cfg):
    raise RuntimeError("W4404985489 needs the GPT-4 Turbo similarity judge: run --judge before --analyze")


if __name__ == "__main__":
    t = "Here are the variables:\nname | description | numerical value\nS | susceptibles | None\nR0 | basic reproduction number | 2.5\n- beta | transmission rate | 0.3 | extra"
    p = parse(t, {})
    assert [e["name"] for e in p] == ["S", "R0", "beta"] and p[2]["value"] == "0.3 | extra"
    assert [e[0] for e in _entries(p)] == ["var desc", "var desc", "var val", "var desc", "var val"]
    item = {"id": "7", "gold": [{"type": "var desc", "text": "susceptibles (S)"}, {"type": "var val", "text": "R0 = 2.5"}]}
    pe, ge, pairs = _pairs(item, t)
    assert len(pairs) == 3 * 1 + 2 * 1
    rec = {"seed_idx": 0, "response": {"choices": [{"message": {"content": t}}]}}
    reqs = judge_requests({"metric": {"judge": "llm:gpt-4-turbo-2024-04-09, x"}, "model": {"id": "m"}}, [item], {("7", 0): rec})
    assert len(reqs) == 5 and reqs[0]["body"]["max_tokens"] == 1 and "susceptibles (S)" in reqs[0]["body"]["messages"][0]["content"]
    jr = {(r["id"], 0): {"response": {"choices": [{"message": {"content": "y" if r["meta"]["pi"] == 0 or r["meta"]["pi"] == 2 else "n"}}]}} for r in reqs}
    f1, _ = score_with_judge({}, [item], [rec], jr)
    assert abs(f1 - 2 * 1.0 * 0.4 / 1.4) < 1e-9, f1
    print("ok")
