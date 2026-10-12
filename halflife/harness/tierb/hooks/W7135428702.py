"""Hook for W7135428702 (SommBench WTQA): the prompt block is chosen by the item's language code.

render() picks prompt.user_template_by_language[row.language] (the eight Appendix A blocks, Figures 4-11)
and fills {question}, {a}, {b}, {c}, {d}. Items, label_map (a-d -> A-D), the 'letter' parse and accuracy
stay with the runner. With items.filter removed all 1,024 rows (128 x 8 languages) are rendered, matching
Table 1 (0.73 = mean of the eight equal-sized per-language accuracies).
"""
SLOTS = ("question", "a", "b", "c", "d")


def render(cfg, row):
    p = cfg["prompt"]
    lang = str(row.get("language", "")).strip().lower()
    template = (p.get("user_template_by_language") or {}).get(lang)
    if template is None:
        raise KeyError(f"no prompt block for language {lang!r}")
    for s in SLOTS:
        template = template.replace("{" + s + "}", str(row[s]))
    msgs = [{"role": "user", "content": template}]
    if p.get("system"):
        msgs.insert(0, {"role": "system", "content": p["system"]})
    return msgs


if __name__ == "__main__":
    cfg = {"prompt": {"system": None, "user_template_by_language": {"en": "Q: {question}\n(A) {a}\n(B) {b}\n(C) {c}\n(D) {d}",
                                                                    "de": "Frage: {question}\n(A) {a}\n(B) {b}\n(C) {c}\n(D) {d}"}}}
    row = {"language": "de", "question": "Was ist {Riesling}?", "a": "x", "b": "y", "c": "z", "d": "w"}
    out = render(cfg, row)[0]["content"]
    assert out.startswith("Frage: Was ist {Riesling}?") and out.endswith("(D) w")
    try:
        render(cfg, dict(row, language="xx")); raise AssertionError
    except KeyError:
        pass
    print("ok")
