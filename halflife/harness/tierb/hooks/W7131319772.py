"""Hook W7131319772 (ContentBench-ResearchTalk v1.0, gpt-5-mini, Table 1 Agreement).

load_items -> concatenation of core.jsonl and hard-sarcasm.jsonl (items.file_url + items.file_url_second, or
              items.file_urls); every row carries its own 'split' field and ids are disjoint (1-500 / 501-1000).
parse      -> the codebook label named earliest in the reply; underscores, spaces or hyphens inside a label are
              accepted (config output.parse_prose); None when no label is named (counted as disagreement).
"""
import json, re, urllib.request

UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}
LABELS = ["sarcastic_critique", "procedural_statement", "genuine_praise", "genuine_critique", "neutral_query"]


def load_items(cfg):
    it = cfg["items"]
    urls = it.get("file_urls") or [u for u in (it.get("file_url"), it.get("file_url_second")) if u]
    rows = []
    for u in urls:
        data = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120).read().decode("utf-8")
        rows += [json.loads(l) for l in data.splitlines() if l.strip()]
    return rows


def parse(text, cfg):
    low = (text or "").lower()
    hits = []
    for lab in LABELS:
        m = re.search(r"(?<![a-z])" + lab.replace("_", r"[\s_\-]+") + r"(?![a-z])", low)
        if m:
            hits.append((m.start(), lab))
    return min(hits)[1] if hits else None


if __name__ == "__main__":
    tests = [("sarcastic_critique", "sarcastic_critique"), ("Genuine Praise.", "genuine_praise"),
             ("Classification: neutral-query", "neutral_query"), ("genuine critique (not praise)", "genuine_critique"),
             ("Label: procedural_statement\n", "procedural_statement"), ("I am not sure.", None)]
    for reply, want in tests:
        assert parse(reply, {}) == want, (reply, parse(reply, {}), want)
    print("W7131319772 hook self-test ok")
