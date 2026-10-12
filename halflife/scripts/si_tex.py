"""Build the Supplementary Information source: Supplementary Notes (paper/si_notes.tex, written by hand) followed by
the supplementary tables typeset from SUPPLEMENTARY_TABLES.md (the file scripts/supp_tables.py regenerates), with
Table S9 (one row per successor result) taken from data/p3_summary.csv.

python scripts/si_tex.py            -> paper/si.tex (then: cd paper && pdflatex si.tex twice)

Every "## Table Sn." section of the Markdown file becomes a captioned longtable; paragraphs under a heading become
table notes and "### " sub-headings become sub-tables. Korean class labels are translated, LaTeX specials escaped,
long tokens made breakable, and wide tables are set smaller and, beyond ten columns, in landscape.
"""
import csv
import re
from pathlib import Path

HALF = Path(__file__).resolve().parents[1]
PAPER = HALF / "paper"
MD = HALF / "SUPPLEMENTARY_TABLES.md"
TEXT_WIDTH_MM = 170.0
LANDSCAPE_WIDTH_MM = 247.0
KO = {"핵심 주장 성립": "claim holds", "부분 성립": "holds in part", "불성립": "claim fails", "판단 불가": "cannot judge", "불일치": "unresolved",
      "확인 필요": "could not be judged", "해당없음": "not transferable", "부분 생존": "partial", "판정 불능": "could not be judged", "판정불능": "could not be judged",
      "인용·언급": "cited or mentioned", "못찾음": "not found", "판단불가": "cannot judge", "날짜 스냅숏": "dated snapshot",
      "별칭·계열명": "alias or family name", "제품명": "product name", "클라우드배포": "cloud deployment", "서드파티": "third-party gateway",
      "접근경로": "access path", "버전표기": "designation precision", "실행시점": "run date", "확신도": "confidence",
      "재현": "reproduced", "근접": "close", "편차": "deviated", "생존": "survived", "사망": "died", "실행": "executed", "동률": "tie",
      "아니오": "no", "없음": "none", "있음": "present", "불명": "unknown", "혼합": "mixed", "웹UI": "web UI", "연월": "month and year",
      "연도만": "year only", "열람": "full text accessible", "로컬": "local", "예": "yes"}


def ko(s):
    s = str(s)
    for k in sorted(KO, key=len, reverse=True):
        s = s.replace(k, KO[k])
    return s


def esc(s):
    s = ko(s)
    s = s.replace("\\", r"\textbackslash{}")
    for a, b in (("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}"),
                 ("~", r"\textasciitilde{}"), ("^", r"\textasciicircum{}")):
        s = s.replace(a, b)
    for a, b in (("≥", r"$\geq$"), ("≤", r"$\leq$"), ("→", r"$\rightarrow$"), ("←", r"$\leftarrow$"), ("–", "--"), ("—", "---"),
                 ("×", r"$\times$"), ("α", r"$\alpha$"), ("κ", r"$\kappa$"), ("χ", r"$\chi$"), ("Δ", r"$\Delta$"), ("±", r"$\pm$"),
                 ("·", r"$\cdot$"), ("’", "'"), ("‘", "`"), ("“", "``"), ("”", "''"), ("…", "..."), ("²", r"$^2$")):
        s = s.replace(a, b)
    # let long identifiers, paths, slashes and underscores break
    s = s.replace("/", "/\\allowbreak{}").replace(r"\_", r"\_\allowbreak{}").replace("-", "-\\allowbreak{}")
    s = re.sub(r"([A-Za-z0-9]{14})(?=[A-Za-z0-9]{6})", r"\1\\allowbreak{}", s)
    return s


def breakable(s, every=8):
    """Insert break opportunities inside long alphanumeric runs (used only when a table cannot fit otherwise)."""
    return re.sub(r"[A-Za-z0-9]{12,}", lambda m: "\\allowbreak{}".join(m.group(0)[i:i + every] for i in range(0, len(m.group(0)), every)), s)


def md_inline(s):
    """Markdown emphasis inside a paragraph or cell."""
    s = esc(s)
    s = re.sub(r"\\textasciitilde\{\}", "~", s)  # not used in the md
    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
    s = re.sub(r"`(.+?)`", r"\\texttt{\1}", s)
    return s


SIZES = [(r"\small", 1.75), (r"\footnotesize", 1.55), (r"\scriptsize", 1.32), (r"\tiny", 1.08)]   # approximate mm per character


def longtable(header, rows, caption_tex, label=None):
    ncol = len(header)
    if ncol > 14:                            # too many columns for one landscape page: split into parts that share the first column
        parts, per = [], 11
        others = list(range(1, ncol))
        chunks = [others[i:i + per] for i in range(0, len(others), per)]
        out = []
        for k, chunk in enumerate(chunks, 1):
            idx = [0] + chunk
            h = [header[i] for i in idx]
            rr = [[r[i] if i < len(r) else "" for i in idx] for r in rows]
            cap = caption_tex + (f" (part {k} of {len(chunks)})" if len(chunks) > 1 else "")
            out.append(longtable(h, rr, cap, label if k == 1 else None))
        return "".join(out)
    allrows = [header] + rows
    cells = [[ko(r[i]) if i < len(r) else "" for r in allrows] for i in range(ncol)]   # measured after translation
    maxlen = [min(max(len(c) for c in col), 48) for col in cells]
    # longest unbreakable token per column: body tokens split at spaces and slashes (identifiers kept whole),
    # header tokens also at underscores and hyphens because esc() makes those breakable
    tok = []
    for i, col in enumerate(cells):
        body_tok = max((len(t) for c in col[1:] for t in re.split(r"[\s/]+", c)), default=0)
        head_tok = max((len(t) for t in re.split(r"[\s/_-]+", col[0])), default=0)
        tok.append(max(body_tok, head_tok, 1))
    start = 0 if (ncol <= 5 and len(rows) <= 40) else 1 if (ncol <= 8 and len(rows) <= 60) else 2 if ncol <= 12 else 3
    chosen = None
    for landscape in (False, True):
        width = LANDSCAPE_WIDTH_MM if landscape else TEXT_WIDTH_MM
        usable = width - 3.0 * ncol - 4.0
        for size, cw in SIZES[start:]:
            floors = [min(t, 24) * cw + 1.0 for t in tok]
            if sum(floors) <= usable:
                chosen = (landscape, size, cw, floors, usable)
                break
        if chosen:
            break
    squeeze = chosen is None
    if squeeze:                             # even landscape + tiny cannot hold the longest tokens: shrink floors and let tokens break
        landscape, size, cw = True, r"\tiny", SIZES[-1][1]
        usable = LANDSCAPE_WIDTH_MM - 3.0 * ncol - 4.0
        floors = [min(t, 9) * cw + 1.0 for t in tok]
        chosen = (landscape, size, cw, floors, usable)
    landscape, size, cw, floors, usable = chosen
    want = [max(m, 4) * cw for m in maxlen]
    spare = usable - sum(floors)
    extra = [max(w - f, 0.0) for w, f in zip(want, floors)]
    k = min(1.0, spare / sum(extra)) if sum(extra) > 0 else 0.0
    widths = [f + e * k for f, e in zip(floors, extra)]
    if sum(widths) > usable:
        widths = [w * usable / sum(widths) for w in widths]
    colspec = "".join(f">{{\\raggedright\\arraybackslash}}p{{{w:.1f}mm}}" for w in widths)
    out = []
    if landscape:
        out.append(r"\begin{landscape}")
    out.append(size)
    out.append(r"\begin{longtable}{" + colspec + "}")
    out.append(r"\caption*{" + caption_tex + "}" + (r"\label{" + label + "}" if label else "") + r"\\")
    head = " & ".join(r"\textbf{" + esc(h) + "}" for h in header) + r" \\"
    out += [r"\toprule", head, r"\midrule", r"\endfirsthead", r"\toprule", head, r"\midrule", r"\endhead", r"\bottomrule", r"\endfoot"]
    for r in rows:
        cells_tex = [md_inline(r[i]) if i < len(r) else "" for i in range(ncol)]
        if squeeze:
            cells_tex = [breakable(c) for c in cells_tex]
        out.append(" & ".join(cells_tex) + r" \\")
    out.append(r"\end{longtable}")
    out.append(r"\normalsize")
    if landscape:
        out.append(r"\end{landscape}")
    return "\n".join(out) + "\n\n"


def split_cells(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def parse_md(text):
    """Yield sections: (number, caption, blocks) where blocks are ('p', text) | ('h3', text) | ('table', header, rows)."""
    lines = text.splitlines()
    sections, cur = [], None
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = re.match(r"## Table S(\d+)\.\s*(.*)", ln)
        if m:
            cur = {"num": int(m.group(1)), "caption": m.group(2).strip(), "blocks": []}
            sections.append(cur)
            i += 1
            continue
        if cur is None:
            i += 1
            continue
        if ln.startswith("### "):
            cur["blocks"].append(("h3", ln[4:].strip()))
            i += 1
            continue
        if ln.startswith("|"):
            block = []
            while i < len(lines) and lines[i].startswith("|"):
                block.append(lines[i])
                i += 1
            rows = [split_cells(l) for l in block]
            rows = [r for r in rows if not all(re.fullmatch(r":?-{2,}:?", c or "---") for c in r)]
            if rows:
                cur["blocks"].append(("table", rows[0], rows[1:]))
            continue
        if ln.strip():
            para = []
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(("|", "## ", "### ")):
                para.append(lines[i].strip())
                i += 1
            if not para:               # a '## ' line that is not a table heading: skip it rather than loop on it
                i += 1
                continue
            cur["blocks"].append(("p", " ".join(para)))
            continue
        i += 1
    return sections


def s9_from_csv():
    p = HALF / "data" / "p3_summary.csv"
    rows = list(csv.reader(open(p, encoding="utf-8-sig")))
    header, body = rows[0], rows[1:]
    keep = [c for c in header if c not in ("note", "subset_note", "config_model", "fingerprints", "served")]
    idx = [header.index(c) for c in keep]
    body2 = [[r[j] if j < len(r) else "" for j in idx] for r in body]
    cap = (r"\textbf{Table S9.} Successor conditions, one row per result: condition, paper, metric, reported value, pre-retirement baseline, "
           r"successor value with its 95\% interval, difference from the reported value and from the baseline in points, class against each, "
           r"the baseline's own class, number of items, unparsed replies and cost (from data/p3\_summary.csv)")
    return longtable(keep, body2, cap)


def main():
    text = MD.read_text(encoding="utf-8")
    sections = parse_md(text)
    notes = (PAPER / "si_notes.tex").read_text(encoding="utf-8") if (PAPER / "si_notes.tex").exists() else "% si_notes.tex missing\n"
    preamble = ""
    m = re.search(r"^# .*?\n\n(.*?)\n\n## ", text, re.S)
    if m:
        preamble = md_inline(m.group(1))
    head = r"""\documentclass[10pt,a4paper]{article}
\usepackage[margin=18mm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage{helvet}
\renewcommand{\familydefault}{\sfdefault}
\usepackage{longtable,booktabs,array,pdflscape,amsmath,amssymb,microtype}
\usepackage[font=small,labelfont=bf,justification=raggedright,singlelinecheck=false]{caption}
\usepackage[hidelinks]{hyperref}
\setlength{\LTcapwidth}{\textwidth}
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.08}
\setcounter{secnumdepth}{0}
\sloppy
\emergencystretch=2em
\title{Supplementary Information\\[4pt]\large The half-life of science that depends on commercial language models}
\author{Hyeonwoo Gil, Sangsu Ahn, Janghyuck Hwang, Junggi Kim, Junmyeong Kim and Shinjin Kang}
\date{Version of \today. Tables regenerate from the deposited data with \texttt{scripts/supp\_tables.py}; this document with \texttt{scripts/si\_tex.py}.}
\begin{document}
\maketitle
\tableofcontents
\clearpage
"""
    body = [head, notes, r"\clearpage" + "\n", r"\section{Supplementary Tables}" + "\n\n"]
    if preamble:
        body.append(preamble + "\n\n")
    done9 = False
    for sec in sorted(sections, key=lambda x: x["num"]):
        if sec["num"] > 9 and not done9:
            body.append(s9_from_csv())
            done9 = True
        cap = r"\textbf{Table S" + str(sec["num"]) + ".} " + md_inline(sec["caption"])
        first_table = True
        sub = None
        for b in sec["blocks"]:
            if b[0] == "h3":
                sub = b[1]
            elif b[0] == "p":
                body.append(md_inline(b[1]) + "\n\n")
            elif b[0] == "table":
                c = cap if first_table else (r"\textbf{Table S" + str(sec["num"]) + " (continued).} " + (md_inline(sub) if sub else ""))
                if first_table and sub:
                    c = cap + " " + md_inline(sub)
                body.append(longtable(b[1], b[2], c))
                first_table = False
                sub = None
    if not done9:
        body.append(s9_from_csv())
    body.append(r"\end{document}" + "\n")
    (PAPER / "si.tex").write_text("".join(body), encoding="utf-8")
    print(f"si.tex: {len(sections)} markdown sections + S9 from csv; wrote {PAPER / 'si.tex'}")


if __name__ == "__main__":
    main()
