"""Aggregate the Tier B triage records (harness/tierb/<Wid>.json) into an index and a summary.

Outputs harness/tierb/INDEX.md and data/tierb_triage_summary.json. Duplicates (arXiv and venue
versions of one paper) are collapsed by normalised title, keeping the record with the better
verdict. Non-schema blocker tokens used by the triage agents (prompt_none, no_prompt) are mapped
to 'no_prompt'.
"""
import csv, glob, json, re
from collections import Counter
from pathlib import Path

HALF = Path(__file__).resolve().parents[1]
TB = HALF / "harness" / "tierb"
CAND = HALF / "data" / "tierb_candidates.csv"
ORDER = {"eligible": 0, "maybe": 1, "ineligible": 2}
COST = {"low": 3, "mid": 15, "high": 40}   # rough USD per paper at 3 seeds (high = capped subset)


def norm(t):
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())[:60]


def main():
    meta = {r["openalex_id"].rsplit("/", 1)[-1]: r for r in csv.DictReader(open(CAND, encoding="utf-8-sig"))}
    recs = []
    for f in sorted(glob.glob(str(TB / "W*.json"))):
        try:
            c = json.load(open(f, encoding="utf-8"))
        except json.JSONDecodeError as e:
            print("bad json:", f, e)
            continue
        wid = Path(f).stem
        c["wid"] = wid
        c["group"] = meta.get(wid, {}).get("group", "?")
        c["blockers"] = ["no_prompt" if b in ("prompt_none", "no_prompt") else b for b in (c.get("blockers") or [])]
        if c.get("verdict") == "ineligible" and not c["blockers"] and (c.get("prompt") or {}).get("verbatim") == "none":
            c["blockers"] = ["no_prompt"]
        recs.append(c)
    # collapse duplicates (arXiv vs venue versions): title-token Jaccard >= 0.7, keep the better verdict
    def toks(c):
        return set(re.sub(r"[^a-z0-9 ]", " ", (c.get("title") or "").lower()).split())
    recs.sort(key=lambda c: ORDER.get(c.get("verdict"), 3))
    kept = []
    for c in recs:
        t = toks(c)
        dup = next((k for k in kept if len(t & toks(k)) / max(1, len(t | toks(k))) >= 0.7), None)
        if dup:
            c["duplicate_of"] = dup["wid"]
        else:
            kept.append(c)
    uniq = kept

    def lm(c):
        return (c.get("live_model") or {}).get("resolved", "?")

    def claim(c):
        cl = c.get("claim") or {}
        v = cl.get("value")
        n = cl.get("n_items")
        return f"{cl.get('metric', '?')}={v} (n={n})"

    summary = {
        "records": len(recs), "unique_papers": len(uniq),
        "verdict": Counter(c.get("verdict") for c in uniq),
        "verdict_by_group": {g: dict(Counter(c.get("verdict") for c in uniq if c["group"] == g))
                             for g in sorted({c["group"] for c in uniq})},
        "eligible_task_type": Counter((c.get("claim") or {}).get("task_type") for c in uniq if c.get("verdict") == "eligible"),
        "eligible_cost_tier": Counter((c.get("cost") or {}).get("tier") for c in uniq if c.get("verdict") == "eligible"),
        "eligible_live_model": Counter(lm(c) for c in uniq if c.get("verdict") == "eligible"),
        "maybe_cost_tier": Counter((c.get("cost") or {}).get("tier") for c in uniq if c.get("verdict") == "maybe"),
        "blockers_ineligible": Counter(b for c in uniq if c.get("verdict") == "ineligible" for b in c["blockers"]),
        "role_all": Counter((c.get("live_model") or {}).get("role") for c in uniq),
        "prompt_verbatim_all": Counter((c.get("prompt") or {}).get("verbatim") for c in uniq),
        "alias_resolution_all": Counter(lm(c) for c in uniq),
    }
    elig = sorted([c for c in uniq if c.get("verdict") == "eligible"],
                  key=lambda c: ({"low": 0, "mid": 1, "high": 2}.get((c.get("cost") or {}).get("tier"), 3), c["group"]))
    maybe = sorted([c for c in uniq if c.get("verdict") == "maybe"], key=lambda c: c["group"])
    est = sum(COST.get((c.get("cost") or {}).get("tier"), 20) for c in elig)
    est_lowmid = sum(COST.get((c.get("cost") or {}).get("tier"), 20) for c in elig if (c.get("cost") or {}).get("tier") in ("low", "mid"))
    summary["est_cost_usd_eligible_all"] = est
    summary["est_cost_usd_eligible_low_mid"] = est_lowmid
    (HALF / "data" / "tierb_triage_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=dict), encoding="utf-8")

    L = [f"# Tier B 트리아지 색인 ({len(recs)} 레코드, 중복 제거 후 {len(uniq)}편)", "",
         f"판정: {dict(summary['verdict'])}", "",
         "분야군별: " + "; ".join(f"{g} {v}" for g, v in summary["verdict_by_group"].items()), "",
         f"적격 편수 과제 유형: {dict(summary['eligible_task_type'])}",
         f"적격 편수 비용 등급: {dict(summary['eligible_cost_tier'])} (저·중 등급만 돌리면 약 ${est_lowmid}, 전부 약 ${est})",
         f"적격 편수 살아있는 팔: {dict(summary['eligible_live_model'])}",
         f"부적격 사유(중복 집계): {dict(summary['blockers_ineligible'].most_common())}",
         f"300편 전체 역할 분포: {dict(summary['role_all'])} / 프롬프트 원문: {dict(summary['prompt_verbatim_all'])}", "",
         "## 적격 (eligible)", "",
         "| wid | 군 | 살아있는 팔 | 역할 | 프롬프트 | 과제 | 주장 | 비용 | 데이터 | 제목 |", "|---|---|---|---|---|---|---|---|---|---|"]
    for c in elig:
        L.append(f"| {c['wid']} | {c['group']} | {lm(c)} | {(c.get('live_model') or {}).get('role')} | {(c.get('prompt') or {}).get('verbatim')} | "
                 f"{(c.get('claim') or {}).get('task_type')} | {claim(c)} | {(c.get('cost') or {}).get('tier')} | {(c.get('data') or {}).get('public')} | {(c.get('title') or '')[:70]} |")
    L += ["", "## 조건부 (maybe)", "", "| wid | 군 | 살아있는 팔 | 과제 | 주장 | 비용 | 걸림돌 / 메모 | 제목 |", "|---|---|---|---|---|---|---|---|"]
    for c in maybe:
        note = (c.get("notes") or (c.get("prompt") or {}).get("note") or "")[:110]
        L.append(f"| {c['wid']} | {c['group']} | {lm(c)} | {(c.get('claim') or {}).get('task_type')} | {claim(c)} | {(c.get('cost') or {}).get('tier')} | {'|'.join(c['blockers'])} {note} | {(c.get('title') or '')[:60]} |")
    L += ["", "## 부적격 사유별 편수", ""]
    for b, n in summary["blockers_ineligible"].most_common():
        L.append(f"- {b}: {n}")
    dups = [c for c in recs if c.get("duplicate_of")]
    if dups:
        L += ["", "## 중복 레코드 (같은 논문의 다른 판)", ""] + [f"- {c['wid']} = {c['duplicate_of']} ({(c.get('title') or '')[:60]})" for c in dups]
    (TB / "INDEX.md").write_text("\n".join(L), encoding="utf-8")
    print(json.dumps({k: (dict(v) if isinstance(v, Counter) else v) for k, v in summary.items() if k != "verdict_by_group"}, ensure_ascii=False, indent=1, default=dict))
    print("by group:", summary["verdict_by_group"])
    print("->", TB / "INDEX.md")


if __name__ == "__main__":
    main()
