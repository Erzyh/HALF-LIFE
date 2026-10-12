"""Tier B screening, step 2: rank the fetched papers by prompt-completeness and flag the
ones a human should triage (proposal §3; SPRINT Week 2).

Reads data/tierb_screen.csv (from tierb_fetch.py). A paper is a candidate when its text was
extracted and at least one still-callable (dying) model ID occurs in the body. Ranking is
prompt_score (regex signals) with small bonuses for MCQ/metric evidence. Flags, not
exclusions: web-UI wording, human-outcome wording, terms-of-service risk (jailbreak /
red-teaming titles), and papers already in the P0 pool. Papers with a repository link are
suggested for Tier A review; the rest for Tier B (prompt-only re-execution).

Outputs data/tierb_candidates.csv and data/tierb_candidates.md (top rows by domain group).
Usage: python scripts/tierb_rank.py [--top 300]
"""
import argparse, csv, json, re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCREEN = ROOT / "data" / "tierb_screen.csv"
CENSUS = ROOT / "data" / "census_v2.csv"
TEXTS = ROOT / "external" / "papers_tierb"
# alias-date rule (SPRINT 9/2): "gpt-4-turbo" in a paper is a dead preview snapshot unless the paper
# is dated after the 2024-04-09 GA release or names the dated snapshot itself
DEAD_PREVIEW = re.compile(r"(?i)gpt[\s\-_]*4[\s\-_]*(?:1106|0125)[\s\-_]*preview|gpt[\s\-_]*4[\s\-_]*turbo[\s\-_]*preview"
                          r"|(?:1106|0125)[\s\-_]*preview|gpt[\s\-_]*4[\s\-_]*1106|gpt[\s\-_]*4[\s\-_]*0125")
DATED_TURBO = re.compile(r"(?i)gpt[\s\-_]*4[\s\-_]*turbo[\s\-_]*2024[\s\-_]*04[\s\-_]*09")
GA_DATE = "2024-04-09"
LAG_DATE = "2024-07-01"   # publication within 3 months of GA: experiments may predate it
POOL = ROOT / "data" / "p0_pool.csv"
OUT_CSV = ROOT / "data" / "tierb_candidates.csv"
OUT_MD = ROOT / "data" / "tierb_candidates.md"
TOS = re.compile(r"(?i)jailbreak|red[- ]team|adversarial attack|harmful|toxic|malicious|prompt injection|unsafe")
GROUP = {"Computer Science": "CS", "Medicine": "MED", "Health Professions": "MED", "Dentistry": "MED",
         "Nursing": "MED", "Pharmacology, Toxicology and Pharmaceutics": "MED", "Immunology and Microbiology": "MED",
         "Veterinary": "MED", "Social Sciences": "SOC", "Psychology": "SOC",
         "Business, Management and Accounting": "SOC", "Economics, Econometrics and Finance": "SOC",
         "Arts and Humanities": "SOC", "Biochemistry, Genetics and Molecular Biology": "LIFE",
         "Neuroscience": "LIFE", "Agricultural and Biological Sciences": "LIFE", "": "UNK"}


def num(x):
    try:
        return int(float(x))
    except (TypeError, ValueError):
        return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=300)
    a = ap.parse_args()
    pool = {r["openalex_id"] for r in csv.DictReader(open(POOL, encoding="utf-8-sig"))} if POOL.exists() else set()
    rows = list(csv.DictReader(open(SCREEN, encoding="utf-8-sig")))
    dates = {r["openalex_id"]: r["date"] for r in csv.DictReader(open(CENSUS, encoding="utf-8-sig"))}
    tm_path = ROOT / "data" / "tierb_title_match.json"
    title_match = json.load(open(tm_path, encoding="utf-8")) if tm_path.exists() else {}
    cands = []
    for r in rows:
        if not r["fetch"] in ("pdf", "html") or not r["live_ids_in_body"]:
            continue
        wid_ = r["openalex_id"].rsplit("/", 1)[-1]
        if title_match.get(wid_) is not None and title_match[wid_] < 0.5:
            continue   # fetched document is not this paper (landing page / wrong OA link)
        s = {k: num(r[k]) for k in ("prompt_label", "you_are", "prompt_words", "long_quote", "metric", "params",
                                     "api", "webui", "mcq", "human_outcome", "prompt_score")}
        score = s["prompt_score"] + (2 if s["mcq"] else 0) + (1 if s["metric"] else 0) + (1 if s["api"] else 0)
        flags = []
        live = set(r["live_ids_in_body"].split("|"))
        alias_note = ""
        if "gpt-4-turbo" in live and "gpt-4-turbo-2024-04-09" not in live:
            wid = r["openalex_id"].rsplit("/", 1)[-1]
            try:
                text = (TEXTS / f"{wid}.txt").read_text(encoding="utf-8")
            except OSError:
                text = ""
            date = dates.get(r["openalex_id"], "")
            if DATED_TURBO.search(text):
                alias_note = "dated 04-09 in text"
            elif DEAD_PREVIEW.search(text):
                flags.append("alias_dead")
                alias_note = "dead preview in text"
            elif date and date < GA_DATE:
                flags.append("alias_dead")
                alias_note = f"paper dated {date}"
            elif date and date < LAG_DATE:
                flags.append("alias_unresolved")
                alias_note = f"paper dated {date}, within 3 months of GA"
            else:
                alias_note = f"post-GA alias ({date})"
        if live == {"chatgpt-4o-latest"}:
            flags.append("rolling_alias")
        if s["webui"] >= 2 and s["webui"] >= s["api"]:
            flags.append("webui")
        if s["human_outcome"] >= 5:
            flags.append("human")
        if TOS.search(r["title"]):
            flags.append("tos")
        if r["openalex_id"] in pool:
            flags.append("in_pool")
        cands.append({"openalex_id": r["openalex_id"], "title": r["title"], "year": r["year"], "field": r["field"],
                      "group": GROUP.get(r["field"], "ENG" if r["field"] else "UNK"), "citations": num(r["citations"]),
                      "live_ids": r["live_ids_in_body"], "n_links": num(r["n_links"]), "score": score,
                      "signals": f"label{s['prompt_label']} youare{s['you_are']} words{s['prompt_words']} quote{s['long_quote']} "
                                 f"metric{s['metric']} params{s['params']} mcq{s['mcq']} api{s['api']} webui{s['webui']} human{s['human_outcome']}",
                      "flags": "|".join(flags), "alias_note": alias_note,
                      "tier": "A?" if num(r["n_links"]) > 0 else "B?", "doi": r["doi"]})
    cands.sort(key=lambda c: (-c["score"], -c["citations"]))
    for i, c in enumerate(cands, 1):
        c["rank"] = i
    fields = ["rank", "openalex_id", "title", "year", "field", "group", "citations", "live_ids", "n_links", "score",
              "tier", "flags", "alias_note", "signals", "doi"]
    with open(OUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(cands)

    fetched = sum(1 for r in rows if r["fetch"] in ("pdf", "html"))
    print(f"scanned {len(rows)}, fetched {fetched}, candidates {len(cands)}, unflagged {sum(1 for c in cands if not c['flags'])}")
    print("score>=10:", sum(1 for c in cands if c["score"] >= 10), "| score>=10 & links:", sum(1 for c in cands if c["score"] >= 10 and c["n_links"]))
    print("by group (unflagged):", Counter(c["group"] for c in cands if not c["flags"]))
    turbo = [c for c in cands if "gpt-4-turbo" in c["live_ids"].split("|")]
    split = Counter(("dated" if c["alias_note"].startswith("dated") or "gpt-4-turbo-2024-04-09" in c["live_ids"]
                     else "dead" if "alias_dead" in c["flags"] else "unresolved" if "alias_unresolved" in c["flags"]
                     else "post-GA alias") for c in turbo)
    print(f"gpt-4-turbo mentions {len(turbo)}: {dict(split)}")

    def pick(pool_, quotas):
        """Fill per-domain-group quotas in score order, then top up any shortfall by score."""
        out, used = [], Counter()
        for c in pool_:
            if used[c["group"]] < quotas.get(c["group"], 0):
                used[c["group"]] += 1
                out.append(c)
        n = sum(quotas.values())
        for c in pool_:
            if len(out) >= n:
                break
            if c not in out:
                out.append(c)
        return out
    ok = [c for c in cands if not c["flags"]]
    # Tier B = prompt-only papers (no repository); papers with a repository go to the Tier A review list
    batch_b = pick([c for c in ok if c["score"] >= 12 and c["n_links"] == 0],
                   {"SOC": 12, "ENG": 8, "MED": 8, "CS": 6, "LIFE": 4, "UNK": 2})
    pass_a = pick([c for c in ok if c["n_links"] > 0 and c["score"] >= 10],
                  {"SOC": 8, "ENG": 6, "MED": 6, "CS": 5, "LIFE": 4, "UNK": 1})
    batch_b.sort(key=lambda c: c["rank"])
    pass_a.sort(key=lambda c: c["rank"])
    for name, sel in (("tierb_batch1", batch_b), ("tierA_pass2_candidates", pass_a)):
        with open(ROOT / "data" / f"{name}.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(sel)
    lines = [f"# Tier B 후보 순위 (자동 선별, {len(rows)}편 스캔 / {fetched}편 전문 확보 / {len(cands)}편 후보)", "",
             "후보 = 전문 확보 + 본문에 사망 예고 모델 ID 등장. 점수 = 프롬프트 표시, 'You are', 인용 블록, 지표, 호출 설정 신호의 합에 MCQ·지표·API 가점.",
             "플래그는 제외가 아니라 검토 표시: alias_dead(별칭이 죽은 preview를 가리킴), alias_unresolved(GA 3개월 내 출판), webui, human, tos, rolling_alias, in_pool.", "",
             f"gpt-4-turbo 언급 {len(turbo)}편의 별칭 해소: {dict(split)}",
             f"플래그 없는 후보 {len(ok)}편, 그중 저장소 링크 보유 {sum(1 for c in ok if c['n_links'])}편", "",
             f"## 제안 1: Tier B 1차 배치 ({len(batch_b)}편, 점수 12 이상, 분야군 할당 SOC 12 / ENG 8 / MED 8 / CS 6 / LIFE 4 / UNK 2)", "",
             "| 순위 | 군 | 점수 | 인용 | 살아있는 팔 | 별칭 메모 | 제목 |", "|---|---|---|---|---|---|---|"]
    for c in batch_b:
        lines.append(f"| {c['rank']} | {c['group']} | {c['score']} | {c['citations']} | {c['live_ids']} | {c['alias_note']} | {c['title'][:80]} |")
    lines += ["", f"## 제안 2: Tier A 2차 카드 작성 후보 ({len(pass_a)}편, 링크 보유, 점수 10 이상, 분야군 할당 SOC 8 / ENG 6 / MED 6 / CS 5 / LIFE 4 / UNK 1)", "",
              "| 순위 | 군 | 점수 | 인용 | 살아있는 팔 | 링크 | 제목 |", "|---|---|---|---|---|---|---|"]
    for c in pass_a:
        lines.append(f"| {c['rank']} | {c['group']} | {c['score']} | {c['citations']} | {c['live_ids']} | {c['n_links']} | {c['title'][:80]} |")
    lines += ["", "## 분야군별 상위 후보 (플래그 없음)", ""]
    for g in ("CS", "MED", "SOC", "ENG", "LIFE", "UNK"):
        sub = [c for c in ok if c["group"] == g][:25]
        if not sub:
            continue
        lines += [f"### {g} ({sum(1 for c in ok if c['group'] == g)}편 중 상위 {len(sub)})", "",
                  "| 순위 | 점수 | 인용 | 살아있는 팔 | 링크 | 제목 |", "|---|---|---|---|---|---|"]
        for c in sub:
            lines.append(f"| {c['rank']} | {c['score']} | {c['citations']} | {c['live_ids']} | {c['n_links']} | {c['title'][:90]} |")
        lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"batch B: {len(batch_b)} {Counter(c['group'] for c in batch_b)} | pass A: {len(pass_a)} {Counter(c['group'] for c in pass_a)}")


if __name__ == "__main__":
    main()
