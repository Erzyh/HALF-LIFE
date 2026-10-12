"""Hook for W4403570177 (RMB, Table 3 row GPT-4o-2024-05-13, Helpfulness pairwise accuracy 0.815).

load_items() concatenates the 37 helpfulness pairwise subcategory files of the RMB repository (list
fixed below: 10,067 pairs), renders the dialog history (single user turn as-is; multi-turn as
'User:'/'Assistant:' lines) and assigns chosen/rejected to Assistant A/B with one RNG seeded 20260907
(coin flip per pair, file order); the gold is the letter holding the chosen response. parse() reads the
last [[A]]/[[B]] verdict; accuracy stays with the runner (Eq. 1: share of pairs where the judge picks
the chosen response; no verdict counts as incorrect).
"""
import json, re, urllib.request
from pathlib import Path
import numpy as np

WID = "W4403570177"
SEED = 20260907
BASE = "https://raw.githubusercontent.com/Zhou-Zoey/RMB-Reward-Model-Benchmark/main/RMB_dataset/Pairwise_set/Helpfulness/"
FILES = ["Brainstorming/Idea Development", "Brainstorming/Problem Solving", "Chat/Casual Conversation", "Chat/Discussion",
         "Chat/Supportive Conversation", "Classification/Content Categorization", "Classification/Quality and Compliance Assessment",
         "Closed QA/ContextBased", "Closed QA/OptionBased", "Code/Data Management", "Code/Development and Implementation",
         "Code/Documentation", "Code/Quality and Optimization", "Generation/Creative Writing", "Generation/Professional Content Generation",
         "Open QA/Factual", "Open QA/General Explanation", "Open QA/Hypothetical Scenarios", "Open QA/Interpretative Analysis",
         "Open QA/Personal Opinion and Advice", "Open QA/Technical and Practical Support", "Reasoning/Analytical Reasoning",
         "Reasoning/Critical Thinking", "Reasoning/Human Decision Making", "Reasoning/Logical Deduction", "Reasoning/Pattern Recognition",
         "Rewrite/Paraphrasing", "Rewrite/PostQuality Assessment Rewriting", "Rewrite/Textual ExpansionReduction", "Rewrite/Tone Adjustment",
         "Role Playing/General Character", "Role Playing/Specific Character", "Summarization/Specialized Summaries",
         "Summarization/Standard Summaries", "Translation/GeneralExcerpt Language Translation", "Translation/Literary and Cultural Translation",
         "Translation/Technical and Scientific Translation"]
CACHE = Path(__file__).resolve().parents[3] / "external" / "data" / "tierb_items" / WID
UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}


def _dialog(turns):
    if len(turns) == 1:
        return str(turns[0].get("content", ""))
    return "\n\n".join(f"{'User' if t.get('role') == 'user' else 'Assistant'}: {t.get('content', '')}" for t in turns)


def load_items(cfg):
    CACHE.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    rows = []
    for rel in FILES:
        p = CACHE / (rel.replace("/", "__") + ".json")
        if not p.exists():
            url = BASE + urllib.request.quote(rel) + ".json"
            p.write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300).read())
        for rec in json.loads(p.read_text(encoding="utf-8")):
            rej = rec.get("rejected") if isinstance(rec.get("rejected"), dict) else rec.get("reject")   # key varies by file
            chosen, rejected = rec["chosen"]["answer"], rej["answer"]
            chosen_is_a = bool(rng.integers(0, 2))
            rows.append({"id": f"{rel.split('/')[-1]}:{rec['pair_uid']}", "subcategory": rel, "question": _dialog(rec["conversation_input"]),
                         "answer_a": chosen if chosen_is_a else rejected, "answer_b": rejected if chosen_is_a else chosen,
                         "gold": "A" if chosen_is_a else "B", "chosen_model": rec["chosen"].get("llm_name")})
    return rows


def parse(text, cfg):
    if not text:
        return None
    ms = re.findall(r"\[\[([AB])\]\]", text)
    return ms[-1] if ms else None


if __name__ == "__main__":
    assert parse("Explanation... [[A]]", {}) == "A" and parse("[[A]] ... final: [[B]]", {}) == "B" and parse("A is better", {}) is None
    assert _dialog([{"role": "user", "content": "hi"}]) == "hi"
    assert _dialog([{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}]) == "User: hi\n\nAssistant: hello"
    assert len(FILES) == 37 and np.random.default_rng(SEED).integers(0, 2) in (0, 1)
    print("ok")
