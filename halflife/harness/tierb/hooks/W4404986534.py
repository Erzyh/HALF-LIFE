r"""Hook for W4404986534 (LLM-as-a-Judge survey meta-evaluation, GPT-4-turbo on LLMEval2, Percentage Agreement).

load_items: LLMEval2_benchmark.json.zip (Google Drive id 1sRbYZ0SWqmbIlzC_eB2zjyQF5TBynSXo, 1.4 MB; JSON lines with
            dataset, query, response1, response2, human in {model1, model2, TIE}) -> 2 rows per sample: order '12'
            (Response 1 = response1) and order '21' (swapped); gold = the human label mapped to the presented order.
render:     adapted Gao et al. pairwise template (config user_template) with question / response_1 / response_2.
parse:      first case-insensitive mention of 'response 1' / 'response 2' / 'tie'; none -> invalid (excluded).
score:      Percentage Agreement over valid judgements; per-item list over valid judgements.
"""
import io, json, re, urllib.request, zipfile

URL = "https://drive.google.com/uc?export=download&id=1sRbYZ0SWqmbIlzC_eB2zjyQF5TBynSXo&confirm=t"
UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}
LABELS = ["Response 1", "Response 2", "TIE"]


def load_items(cfg):
    with urllib.request.urlopen(urllib.request.Request(URL, headers=UA), timeout=180) as r:
        data = r.read()
    if data[:2] != b"PK":
        raise RuntimeError("Google Drive did not return the zip archive (interstitial page); download it manually")
    z = zipfile.ZipFile(io.BytesIO(data))
    name = next(n for n in z.namelist() if n.endswith(".json") and not n.startswith("__MACOSX"))
    recs = [json.loads(l) for l in z.read(name).decode("utf-8").splitlines() if l.strip()]
    if len(recs) != 2553:
        raise RuntimeError(f"expected 2,553 LLMEval2 samples, got {len(recs)}")
    rows = []
    for i, r in enumerate(recs):
        h = r["human"]
        for order, (r1, r2) in (("12", (r["response1"], r["response2"])), ("21", (r["response2"], r["response1"]))):
            if h == "TIE":
                gold = "TIE"
            else:
                first_is_model1 = order == "12"
                gold = "Response 1" if (h == "model1") == first_is_model1 else "Response 2"
            rows.append({"id": f"{i}_{order}", "question": r["query"], "response_1": r1, "response_2": r2,
                         "dataset": r.get("dataset"), "gold": gold})
    return rows


def render(cfg, row):
    t = cfg["prompt"]["user_template"]
    for k in ("question", "response_1", "response_2"):
        t = t.replace("{" + k + "}", str(row[k]))
    msgs = [{"role": "system", "content": cfg["prompt"]["system"]}] if cfg["prompt"].get("system") else []
    msgs.append({"role": "user", "content": t})
    return msgs


def parse(text, cfg):
    if not text:
        return None
    hits = [(m.start(), lab) for lab, pat in (("Response 1", r"(?i)response\s*1"), ("Response 2", r"(?i)response\s*2"), ("TIE", r"(?i)\btie\b"))
            for m in [re.search(pat, text)] if m]
    return min(hits)[1] if hits else None


def score(preds, golds, cfg):
    per = [1.0 if p == g else 0.0 for p, g in zip(preds, golds) if p is not None]
    print(f"[W4404986534] valid {len(per)} of {len(preds)} judgements")
    return (sum(per) / len(per) if per else float("nan")), per


if __name__ == "__main__":
    ts = ["Response 1", "response 2 is better", "TIE", "Both are equal, so it is a tie.", "I prefer the second one"]
    print([parse(t, {}) for t in ts])
    assert [parse(t, {}) for t in ts] == ["Response 1", "Response 2", "TIE", "TIE", None]
    v, per = score(["Response 1", "TIE", None, "Response 2"], ["Response 1", "Response 2", "TIE", "Response 2"], {})
    assert abs(v - 2 / 3) < 1e-9 and len(per) == 3
    print("ok", v)
