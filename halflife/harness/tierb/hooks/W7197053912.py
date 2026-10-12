"""Hook W7197053912 (ANCHOR-RE baseline prompt on SemRepGS, gpt-5-mini, Table 2 micro-F1).

load_items -> reads the headerless test.out TSV with the code release's column names (utils/io.py
              load_tsv_data) and builds the 'candidate_relations' slot: the candidate labels of column 10 in the
              release's schema order (SEMREP_LABEL_SCHEMA_ORDER in main.py) plus 'none', followed by one
              '- label: definition' line per candidate with the definitions of SemRep_LABEL2DEF in utils/text.py
              (the file the release feeds to the model; parsed with ast). Copies of test.out and the definitions
              are cached under external/data/tierb_items/W7197053912/.
parse      -> the JSON field 'label' (lower-cased; '', none, norel -> 'none').
score      -> micro-F1 over the positive relation types: a pair counts as TP when gold and prediction agree on a
              positive label, FP when a positive label is predicted wrongly, FN when a positive gold label is
              missed; 'none' is excluded as in Sec. 3.8. No per-item list.
"""
import ast, json, re, urllib.request
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}
RAW = "https://raw.githubusercontent.com/COMBINI-Hub/Multi_Agent_Relation_Extraction/main/"
CACHE = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / "W7197053912"
COLS = ["idx", "label", "sentence", "subject_text", "object_text", "subject_type", "object_type",
        "subject_group", "object_group", "label_choices"]
ORDER = ["administered_to", "augments", "causes", "diagnoses", "disrupts", "inhibits", "precedes", "predisposes",
         "prevents", "stimulates", "treats", "uses", "compared_with", "isa", "location_of", "part_of",
         "process_of", "produces", "affects", "coexists_with", "associated_with", "interacts_with"]


def _cached(name, url):
    p = CACHE / name
    if not p.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        p.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read())
    return p.read_bytes()


def definitions():
    src = _cached("utils_text.py", RAW + "utils/text.py").decode("utf-8-sig")
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "SemRep_LABEL2DEF" for t in node.targets):
            return ast.literal_eval(node.value)
    raise RuntimeError("SemRep_LABEL2DEF not found in utils/text.py")


def candidate_block(label_choices, defs):
    labs = [l.strip().lower() for l in label_choices.split(";") if l.strip()]
    labs = sorted(labs, key=lambda l: ORDER.index(l) if l in ORDER else len(ORDER))
    return ", ".join(labs + ["none"]) + "\n" + "\n".join(f"- {l}: {defs.get(l, 'Definition unavailable.')}" for l in labs)


def load_items(cfg):
    defs = definitions()
    rows = []
    for line in _cached("test.out", cfg["items"]["file_url"]).decode("utf-8").splitlines():
        if not line.strip():
            continue
        r = dict(zip(COLS, line.split("\t")[:10]))
        r["candidate_relations"] = candidate_block(r["label_choices"], defs)
        r["subject"], r["object"] = r["subject_text"], r["object_text"]
        rows.append(r)
    return rows


def parse(text, cfg):
    t = (text or "").strip()
    obj = None
    try:
        obj = json.loads(t)
    except Exception:
        m = re.search(r"\{.*\}", t, re.S)
        if m:
            try:
                obj = json.loads(m.group(0))
            except Exception:
                obj = None
    if not isinstance(obj, dict) or "label" not in obj:
        return None
    lab = str(obj.get("label") or "").strip().strip("'\"`’‘").strip().lower()
    return "none" if lab in ("", "none", "norel", "null", "no relation") else lab.replace(" ", "_")


def score(preds, golds, cfg):
    tp = fp = fn = 0
    for p, g in zip(preds, golds):
        g = str(g).strip().lower()
        g = "none" if g in ("", "none", "norel") else g
        p = "none" if p is None else p
        if g != "none" and p == g:
            tp += 1
        else:
            if p != "none":
                fp += 1
            if g != "none":
                fn += 1
    return 2 * tp / max(1, 2 * tp + fp + fn), None


if __name__ == "__main__":
    tests = [('{"subject": "a", "label": "TREATS"}', "treats"), ('```json\n{"label": "’none’"}\n```', "none"),
             ('text {"label": "part of"} more', "part_of"), ('{"label": null}', "none"), ("no json", None)]
    for reply, want in tests:
        assert parse(reply, {}) == want, (reply, parse(reply, {}), want)
    v, _ = score(["treats", "none", "causes", None, "isa"], ["TREATS", "None", "None", "CAUSES", "PART_OF"], {})
    assert abs(v - 2 * 1 / (2 * 1 + 2 + 2)) < 1e-12, v      # tp 1, fp 2 (causes, isa), fn 2 (causes missed, part_of)
    blk = candidate_block("predisposes; coexists_with; isa", {"isa": "D1", "predisposes": "D2", "coexists_with": "D3"})
    assert blk.startswith("predisposes, isa, coexists_with, none\n- predisposes: D2\n- isa: D1\n- coexists_with: D3"), blk
    print("W7197053912 hook self-test ok")
