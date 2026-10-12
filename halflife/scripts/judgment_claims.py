"""Claim-sentence table for the prompt-level judgement (coding/judgment_claims_v1.csv and .xlsx).

One line per prompt-level paper in the judgement sheet (86): what the re-executed number measures (from the run
configuration), where the paper reports it (from the triage record), and the sentence of the paper's abstract that
carries the number or the metric (fetched from OpenAlex and cached). The judges read this line instead of the paper
when they fill the conclusion level. The first author reviews and completes the '주장 문장' column before the table
is sent; rows left empty make their judgement rows 'cannot judge'. OpenAlex is free (api key from halflife/.openalex_key).
Usage: python scripts/judgment_claims.py [--no-fetch]
"""
import argparse, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from census_harvest import api_key  # noqa: E402

CACHE = ROOT / "coding" / "judgment_claims_abstracts.json"
OUT = ROOT / "coding" / "judgment_claims_v1"


def abstract_of(wid, key):
    url = f"https://api.openalex.org/works/{wid}?select=id,title,abstract_inverted_index" + (f"&api_key={key}" if key else "")
    req = urllib.request.Request(url, headers={"User-Agent": "halflife-claims/0.1 (academic research)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read().decode("utf-8"))
    inv = d.get("abstract_inverted_index") or {}
    words = sorted(((pos, w) for w, poss in inv.items() for pos in poss), key=lambda x: x[0])
    return " ".join(w for _, w in words)


def sentences(text):
    text = re.sub(r"\s+", " ", text or "").strip()
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text) if len(s.split()) >= 4]


def value_forms(v):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return []
    forms = {f"{x:g}", f"{x:.1f}", f"{x:.2f}"}
    if 0 < x <= 1:
        forms |= {f"{100 * x:g}", f"{100 * x:.1f}", f"{100 * x:.0f}"}
    if x > 1:
        forms |= {f"{x / 100:.3f}".rstrip("0"), f"{x:.0f}"}
    return sorted(forms, key=len, reverse=True)


def pick(abstract, value, keywords):
    sents = sentences(abstract)
    scored = []
    for s in sents:
        score = 0
        if any(re.search(rf"(?<![\d.]){re.escape(f)}(?![\d])", s) for f in value_forms(value)):
            score += 3
        score += sum(1 for k in keywords if k and re.search(re.escape(k), s, re.I))
        if score:
            scored.append((score, s))
    scored.sort(key=lambda x: -x[0])
    return " ".join(s for _, s in scored[:2])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-fetch", action="store_true", help="use the cached abstracts only")
    a = ap.parse_args()
    sheet = pd.read_excel(ROOT / "coding" / "judgment_sheet_v1.xlsx", sheet_name="PromptLevel_blind")
    papers = sheet.drop_duplicates("논문 ID")[["논문 ID", "논문", "지표", "원 논문 값"]]
    cache = json.load(open(CACHE, encoding="utf-8")) if CACHE.exists() else {}
    key = api_key()
    rows = []
    for r in papers.itertuples(index=False):
        wid = r[0]
        tri = json.load(open(ROOT / "harness" / "tierb" / f"{wid}.json", encoding="utf-8")) if (ROOT / "harness" / "tierb" / f"{wid}.json").exists() else {}
        cfg_p = ROOT / "harness" / "tierb" / "configs" / f"{wid}.json"
        cfg = json.load(open(cfg_p, encoding="utf-8")) if cfg_p.exists() else {}
        claim, metric, task = tri.get("claim") or {}, cfg.get("metric") or {}, cfg.get("task") or {}
        if wid not in cache and not a.no_fetch:
            try:
                cache[wid] = abstract_of(wid, key)
            except Exception as e:  # keep going; the row stays without an abstract sentence
                cache[wid] = ""
                print("abstract failed", wid, str(e)[:80])
            time.sleep(0.2)
        abstract = cache.get(wid, "")
        name = metric.get("name_paper") or claim.get("metric") or r[2]
        keywords = [w for w in re.split(r"[^A-Za-z0-9-]+", str(name)) if len(w) > 3][:4] + ["GPT-4", "GPT-4o", "o1", "o3", "Gemini", "Claude"]
        abs_sent = pick(abstract, r[3], keywords)
        measured = f"{name}: {metric.get('definition', '')}".strip(": ")
        where = claim.get("location") or metric.get("original_location") or ""
        model = (cfg.get("model") or {}).get("id", "") if isinstance(cfg.get("model"), dict) else ""
        # draft claim: the cell the pre-specified number comes from, stated as a level ("model X scores Y on Z"); the
        # abstract sentence, when one was found, is appended so the reviewer can see how the paper frames it
        level = f"{model or 'the model'}: {name} = {r[3]} ({task.get('type', claim.get('task_type', ''))}; {where})".strip()
        draft = level + (f" | 초록: {abs_sent}" if abs_sent else "")
        blob = f"{abs_sent} {name} {measured}".lower()
        if re.search(r"fail|cannot|can't|unable|limitation|bias|refus|error rate|hallucinat|unsafe|vulnerab|over-refusal|not good enough|struggle", blob):
            kind = "한계?"
        elif re.search(r"outperform|better than|compared (with|to)|versus|improve|gain|surpass|superior", blob):
            kind = "비교?"
        else:
            kind = "수준?"
        rows.append({"논문 ID": wid, "논문": r[1], "지표(시트)": r[2], "원 논문 값": r[3], "측정한 것(설정)": measured[:300],
                     "표 위치(트리아지)": where, "초록 문장(자동 선택)": abs_sent, "주장 문장(검토 후 확정)": draft,
                     "유형(수준/한계/비교)": kind, "비고": "" if abstract else "초록 없음(OpenAlex)"})
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    df = pd.DataFrame(rows)
    df.to_csv(OUT.with_suffix(".csv"), index=False, encoding="utf-8-sig")
    df.to_excel(OUT.with_suffix(".xlsx"), index=False)
    # judges' copy: four columns, optional reference for the conclusion level (is the metric a limitation or a comparison?)
    judges = df[["논문 ID", "논문", "표 위치(트리아지)", "초록 문장(자동 선택)"]].rename(
        columns={"표 위치(트리아지)": "재실행한 숫자가 논문의 어디에 있는 값인가", "초록 문장(자동 선택)": "그 숫자나 지표가 나오는 초록 문장 (없으면 빈칸)"})
    jp = ROOT / "coding" / "judgment_claims_v1_judges.xlsx"
    with pd.ExcelWriter(jp, engine="openpyxl") as xw:
        judges.to_excel(xw, index=False, sheet_name="논문별 참고")
        ws = xw.sheets["논문별 참고"]
        for col, width in zip("ABCD", (14, 60, 60, 110)):
            ws.column_dimensions[col].width = width
        from openpyxl.styles import Alignment
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.alignment = Alignment(wrap_text=True, vertical="top")
    print(f"{len(df)} papers; abstract sentence found for {int((df['초록 문장(자동 선택)'] != '').sum())}; -> {OUT.with_suffix('.xlsx').relative_to(ROOT)} and {jp.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
