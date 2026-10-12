"""Aggregate harness/cards/*.json into harness/cards/INDEX.md + data/cards_summary.json.

Columns: card | title | domain | live arm | status | est_cost | blockers | claim_type | orig value.
Totals: status counts, cost by cost-tier, blocker frequency, domain distribution.
Tolerant to partially filled/drafted cards (missing fields -> "?").
"""
import glob, json
from collections import Counter
from pathlib import Path

HALF = Path(__file__).resolve().parents[1]
CARDS = HALF / "harness" / "cards"


def g(d, *path, default="?"):
    for p in path:
        if not isinstance(d, dict) or p not in d or d[p] in (None, ""):
            return default
        d = d[p]
    return d


def cost(card):
    b = card.get("budget", {}) or {}
    for k in ("est_cost_usd", "est_cost_usd_subset", "estimate_usd"):
        v = b.get(k)
        if isinstance(v, (int, float)):
            return float(v)
        if isinstance(v, dict):
            for kk in ("subset", "full"):
                if isinstance(v.get(kk), (int, float)):
                    return float(v[kk])
        if isinstance(v, str):
            import re
            m = re.search(r"(\d+(?:\.\d+)?)", v)
            if m:
                return float(m.group(1))
    return None


def pool_fields():
    """openalex W-id -> field, from data/p0_pool.csv (cards do not carry the domain)."""
    import csv
    out = {}
    pool = HALF / "data" / "p0_pool.csv"
    if pool.exists():
        for r in csv.DictReader(open(pool, encoding="utf-8-sig")):
            out[r["openalex_id"].rsplit("/", 1)[-1]] = r["field"] or "?"
    out["T1"] = out.get("W4394986684", "?")
    return out


def main():
    rows = []
    fields = pool_fields()
    for f in sorted(glob.glob(str(CARDS / "*.json"))):
        c = json.loads(open(f, encoding="utf-8").read())
        live = g(c, "protocol", "model")
        if live == "?":
            live = g(c, "arms")
            if isinstance(live, list):
                live = ", ".join(a.get("model", "?") for a in live if isinstance(a, dict) and a.get("arm", "").startswith("baseline"))
            elif isinstance(live, dict):
                live = g(live, "baseline_alive", "model")
        ov = g(c, "claim", "original_values")
        if isinstance(ov, dict):
            ov = "; ".join(f"{k}={v}" for k, v in list(ov.items())[:2])
        rows.append({
            "card": c.get("card_id", Path(f).stem), "title": str(c.get("title", "?"))[:60],
            "domain": str(fields.get(Path(f).stem, fields.get(c.get("card_id", ""), g(c, "field", default="?"))))[:18],
            "live_arm": str(live)[:32], "status": c.get("status", "?"),
            "cost": cost(c), "blockers": "; ".join(c.get("blockers", []) or [])[:80],
            "claim_type": g(c, "claim", "claim_type"), "orig": str(ov)[:40],
            "user_checks": len(c.get("user_checks", []) or []),
        })

    st = Counter(r["status"] for r in rows)
    ct = Counter(r["claim_type"] for r in rows)
    known = [r["cost"] for r in rows if r["cost"] is not None]
    blk = Counter(b.strip()[:50] for r in rows for b in r["blockers"].split(";") if b.strip())

    lines = ["# 카드 색인 (자동 생성)", "",
             f"카드 {len(rows)}장 · 상태 {dict(st)} · 비용 추정 합계 ${sum(known):.0f} ({len(known)}장 기준, 3시드·비배치 보수치) · 사용자 확인 질문 {sum(r['user_checks'] for r in rows)}건", "",
             "| 카드 | 논문 | 도메인 | 살아있는 팔 | 상태 | 비용$ | 주장 유형 | 원 보고값 | 차단 요인 |", "|---|---|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["status"], r["cost"] if r["cost"] is not None else 1e9)):
        cst = f"{r['cost']:.0f}" if r["cost"] is not None else "?"
        lines.append(f"| {r['card']} | {r['title']} | {r['domain']} | {r['live_arm']} | {r['status']} | {cst} | {r['claim_type']} | {r['orig']} | {r['blockers']} |")
    lines += ["", "## 주장 유형 분포", "", ", ".join(f"{k}: {v}" for k, v in ct.most_common()), "",
              "## 차단 요인 빈도 (상위)", ""] + [f"- {k} — {v}" for k, v in blk.most_common(12)]
    (CARDS / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")
    (HALF / "data" / "cards_summary.json").write_text(json.dumps({"n": len(rows), "status": st, "claim_type": ct,
        "cost_total_known": sum(known), "n_cost_known": len(known), "blockers_top": blk.most_common(12)}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"cards: {len(rows)} | status: {dict(st)} | cost known: {len(known)} sum ${sum(known):.0f}")
    print("claim types:", dict(ct))


if __name__ == "__main__":
    main()
