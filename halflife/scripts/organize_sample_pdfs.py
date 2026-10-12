"""Sort the collected main-sample PDFs into one folder per coder.

python scripts/organize_sample_pdfs.py [--zip]

Reads the assignment (data/coding/assignment_main_k4.csv: each paper has coder1 and coder2) and the collector's
manifest (coding/pdfs_main/manifest.csv), then builds coding/pdfs_main/coders/coder<A-D>/ with that coder's 250
papers as hard links to the collected files (no second copy on disk; a plain copy is made where a link is refused).
Each coder folder gets a README.txt with the count and the list of papers whose PDF could not be collected, with DOI
and landing page, so the coder knows which ones to open through the library. With --zip, one zip archive per coder is
written to coding/pdfs_main/zips/ for distribution. Nothing here is committed or deposited.
"""
import argparse
import csv
import os
import shutil
import time
import zipfile
from pathlib import Path

import pandas as pd

HALF = Path(__file__).resolve().parents[1]
SRC = HALF / "coding" / "pdfs_main"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", action="store_true")
    a = ap.parse_args()
    assign = pd.read_csv(HALF / "data" / "coding" / "assignment_main_k4.csv", encoding="utf-8-sig")
    assign["wid"] = assign.openalex_id.str.rsplit("/", n=1).str[-1]
    man = {r["wid"]: r for r in csv.DictReader(open(SRC / "manifest.csv", encoding="utf-8-sig"))}
    coders = sorted(set(assign.coder1) | set(assign.coder2))
    root = SRC / "coders"
    summary = []
    for c in coders:
        mine = assign[(assign.coder1 == c) | (assign.coder2 == c)].sort_values("num")
        d = root / f"coder{c}"
        d.mkdir(parents=True, exist_ok=True)
        got, missing = [], []
        for r in mine.itertuples():
            m = man.get(r.wid)
            src = SRC / f"{int(r.num):03d}_{r.wid}.pdf"
            if m and m["status"] == "ok" and src.exists():
                dst = d / src.name
                if not dst.exists():
                    try:
                        os.link(src, dst)
                    except OSError:
                        shutil.copy2(src, dst)
                got.append(r)
            else:
                missing.append((int(r.num), r.wid, (m or {}).get("title", ""), (m or {}).get("doi", ""), (m or {}).get("landing", ""), (m or {}).get("status", "not collected")))
        lines = [f"HALF-LIFE 본표본 PDF, 코더 {c} ({time.strftime('%Y-%m-%d')})", "",
                 f"배정 {len(mine)}편 가운데 PDF {len(got)}편이 이 폴더에 있습니다. 파일명은 워크북의 번호_OpenAlexID.pdf입니다.",
                 "PDF는 코딩 작업에만 쓰고 다른 곳에 올리지 마세요.", ""]
        if missing:
            lines += [f"받지 못한 {len(missing)}편은 아래 DOI 또는 링크로 열어 주세요(도서관 구독 필요할 수 있음).", ""]
            for num, wid, title, doi, landing, status in missing:
                lines.append(f"{num:03d}  {wid}  {title[:90]}  {doi or landing}  [{status}]")
        (d / "README.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        with open(d / "missing.csv", "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["num", "wid", "title", "doi", "landing_page", "status"])
            w.writerows(missing)
        size = sum((d / f"{int(r.num):03d}_{r.wid}.pdf").stat().st_size for r in got)
        summary.append((c, len(mine), len(got), len(missing), size / 1e6))
        if a.zip:
            z = SRC / "zips"
            z.mkdir(exist_ok=True)
            zp = z / f"halflife_pdfs_coder{c}.zip"
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
                for p in sorted(d.iterdir()):
                    zf.write(p, arcname=f"coder{c}/{p.name}")
            summary[-1] = summary[-1] + (zp.stat().st_size / 1e6,)
    print("coder  assigned  pdfs  missing  MB" + ("  zip MB" if a.zip else ""))
    for s in summary:
        print("  ".join([f"{s[0]:>5}", f"{s[1]:>8}", f"{s[2]:>4}", f"{s[3]:>7}", f"{s[4]:>6.0f}"] + ([f"{s[5]:>6.0f}"] if a.zip else [])))


if __name__ == "__main__":
    main()
