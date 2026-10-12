"""Hook for W4414494504 (PGxRAG, gpt-4-turbo LLM-only, 225 SME-verified MCQs).

load_items: sheet 'Supplementary table 1' of the released xlsx; each Question_with_Ground_Truth cell is a JSON
            string {Question, Options{A..D}, 'Correct option': 'A. <text>', Explanation} -> fields question,
            option_a..option_d, answer_letter (leading letter of 'Correct option'), id = 1-based row number.
render:     the Table 1 query object: json.dumps({"Question", "Options": {A..D}}, indent=0) reproduces the
            config's user_template layout with properly escaped values.
parse:      the option letter the model selected (uppercase A-D only; the surrounding words are matched
            case-insensitively), in this order:
            1. JSON reply -> value of a key containing 'correct' / 'answer' -> leading letter;
            2. the LAST explicit answer statement: 'the correct|best|most appropriate|recommended answer|option|choice
               [from the provided choices] [is|would be]: [**]["][Option ]X' or 'Option X ["..."] is|seems the
               correct|best|most appropriate ...';
            3. the first quoted or bold letter followed by a colon: '"C": "..."', '**"B": ...', '**A**: ...';
            4. 'Option X' / 'Option "X"' when exactly one distinct letter is named that way (an enumeration of
               all options gives several letters and is left to the rules above);
            5. a letter starting a line ('B) ...', 'C. ...') when exactly one distinct letter starts a line;
            else None -> counted incorrect (a free-text answer that names no option letter is not mapped to the
            option texts; the paper's SMEs did that by hand).
            [triage 2026-09-09: the archived replies answer as 'The correct answer is "C": "..."' / '"B": "..."'
            (566 of 675); the earlier regexes missed the quoted-letter form and, with re.I on the letter class,
            read the article 'a' as option A -> 581 unparsed, 8.1%; see result_before_triage.json]
Metric: runner accuracy against answer_letter.
"""
import io, json, re, urllib.request

URL = "https://huggingface.co/datasets/Wellytics/PGxRAG/resolve/main/PGxRAG%20Supplementary%20tables_revised.xlsx"
UA = {"User-Agent": "Mozilla/5.0 (compatible; halflife-tierb/0.1; academic research)"}


def load_items(cfg):
    import pandas as pd
    with urllib.request.urlopen(urllib.request.Request(URL, headers=UA), timeout=120) as r:
        data = r.read()
    df = pd.read_excel(io.BytesIO(data), sheet_name="Supplementary table 1", header=1)   # row 1 = title, row 2 = header
    rows = []
    for i, cell in enumerate(df["Question_with_Ground_Truth"].tolist()):
        if not isinstance(cell, str) or not cell.strip():
            continue
        obj = json.loads(cell)
        opts = obj["Options"]
        m = re.match(r"\s*([A-D])", str(obj.get("Correct option", "")))
        if not m:
            raise RuntimeError(f"row {i + 1}: no letter in 'Correct option' {obj.get('Correct option')!r}")
        rows.append({"id": str(i + 1), "question": obj["Question"], "option_a": opts["A"], "option_b": opts["B"],
                     "option_c": opts["C"], "option_d": opts["D"], "answer_letter": m.group(1),
                     "references": str(df["References"].iloc[i]) if "References" in df else ""})
    if len(rows) != 225:
        raise RuntimeError(f"expected 225 questions, got {len(rows)}")
    return rows


def render(cfg, row):
    q = {"Question": row["question"], "Options": {k: row[f"option_{k.lower()}"] for k in "ABCD"}}
    msgs = []
    if cfg["prompt"].get("system"):
        msgs.append({"role": "system", "content": cfg["prompt"]["system"]})
    msgs.append({"role": "user", "content": json.dumps(q, indent=0, ensure_ascii=False)})
    return msgs


_L = r'([A-D])(?![A-Za-z])'
_QUOTED_TXT = r'(?:[\s\-\u2013:]*\(?["\u201c][^"\u201d]{0,250}["\u201d]\)?)?'      # an optional quoted option text
_STMT = [
    # 'The correct answer is: **"B": ...' | 'the best option from the provided choices is:\n**B**' | 'correct answer is "D: ...'
    re.compile(r'(?i:(?:correct|best|most\s+appropriate|most\s+accurate|most\s+suitable|recommended|safest|right)\s+'
               r'(?:answer|option|choice|response)'
               r'(?:\s+(?:from|among)\s+(?:the|those)\s+(?:provided|given|listed|available)?\s*(?:choices|options))?'
               r'(?:\s+(?:is|would\s+be|will\s+be|should\s+be))?)\s*[:\-]?\s*\**\s*(?:(?i:option)\s+)?["\u201c]?\(?' + _L),
    # 'Option B ("...") is the recommended approach' | 'Option "B" - "..." seems the most appropriate'
    re.compile(r'(?i:option)\s+["\u201c]?' + _L + r'["\u201d]?\)?' + _QUOTED_TXT + r'\**\s*'
               r'(?i:is|would\s+be|seems|appears|remains)\s+(?i:the\s+|to\s+be\s+(?:the\s+)?)?'
               r'(?i:most\s+\w+|correct|best|recommended|appropriate|right|advisable|safest)'),
]
_QUOTED = re.compile(r'["\u201c]' + _L + r'["\u201d]\s*[:\uff1a]|\*\*' + _L + r'\*\*\s*[:\uff1a]|\*\*["\u201c]' + _L + r'["\u201d]')
_OPTION = re.compile(r'(?i:option)\s+["\u201c]?' + _L)
_LINESTART = re.compile(r'(?m)^\W*' + _L + r'[\.\):]')


def parse(text, cfg):
    if not text:
        return None
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=re.S)
    try:
        obj = json.loads(t)
    except Exception:
        m = re.search(r"\{.*\}", t, re.S)
        obj = None
        if m:
            try:
                obj = json.loads(m.group(0))
            except Exception:
                obj = None
    if isinstance(obj, dict):                                             # 1. JSON reply
        for k, v in obj.items():
            if "correct" in k.lower() or "answer" in k.lower():
                m = re.match(r"\s*\(?([A-D])(?![A-Za-z])", str(v))
                if m:
                    return m.group(1)
    stmts = [(m.start(), m.group(1)) for pat in _STMT for m in pat.finditer(t)]
    if stmts:                                                              # 2. last explicit answer statement
        return max(stmts)[1]
    m = _QUOTED.search(t)                                                  # 3. first '"C":' / '**A**:' / '**"B"'
    if m:
        return next(g for g in m.groups() if g)
    for pat in (_OPTION, _LINESTART):                                      # 4./5. a single named option letter
        letters = {m.group(1) for m in pat.finditer(t)}
        if len(letters) == 1:
            return letters.pop()
    return None


if __name__ == "__main__":
    tests = [('{"Correct option": "A. Phenytoin", "Explanation": "..."}', "A"),
             ("```json\n{\n\"Correct option\": \"C. Levetiracetam\"\n}\n```", "C"),
             ('{\n"Answer": "B"\n}', "B"),
             ("The correct answer is B. Valproate and Lamotrigine because ...", "B"),
             ("D) Gabapentin, Pregabalin", "D"), ("I cannot answer this.", None),
             ('The correct answer is "A": "Phenytoin, Fosphenytoin, Carbamazepine, Oxcarbazepine".\n\nThe presence of the HLA-B*15:02 allele ...', "A"),
             ('The correct answer is: \n**"B": "It can reduce the sensitivity to acenocoumarol."**\n\n**Explanation:**\nAcenocoumarol is a ...', "B"),
             ('"B": "It assesses the enzyme Dihydropyrimidine dehydrogenase (DPD) activity."', "B"),
             ('The side effect ... is "A": Lip smacking or puckering. This symptom can be indicative of tardive dyskinesia.', "A"),
             ('The correct answer is:\n**A**: "Increase the dose to 150% of the standard dose."\n\nPatients with a CYP2D6 variation ...', "A"),
             ('The correct answer is "D: Rasburicase."', "D"),
             ('Therefore, the best option from the provided choices is:\n\n**B**: "Assess for other risk factors of thrombosis."', "B"),
             ('**Option B**: "Avoid azathioprine and use an alternative drug if possible."', "B"),
             ('- **Option B ("Choose an alternative, such as febuxostat")** is the recommended approach.\n- **Option C ("Increase the dose")** is inappropriate.', "B"),
             ('Option "B" - "12 years and older: 5 mg/day; younger than 12 years: 0.025 mg/kg per day" seems the most appropriate.', "B"),
             ('- **Option A**: "Increase the dose." This option is not advisable.\n- **Option B**: "Reduce the dose." This is safer.\n- **Option C**: ...\n- **Option D**: ...', None),
             ('- the correct dosage would be "50 mg every 12 hours" (Option "C").\n- otherwise "75 mg every 12 hours" (Option "B").', None),
             ('The correct answer is a matter of guideline interpretation; see option details.', None),
             ('Patients with hepatitis B. Vitamin D. No option applies.', None)]
    for reply, want in tests:
        got = parse(reply, {})
        assert got == want, (reply[:80], got, want)
    print("W4414494504 hook self-test ok")
    row = {"question": 'Q "x"?', "option_a": "a", "option_b": "b", "option_c": "c", "option_d": "d"}
    print(render({"prompt": {"system": None}}, row)[0]["content"])