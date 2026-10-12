"""Render the first slide of a .pptx to a PNG through PowerPoint (Windows, needs PowerPoint and pywin32).

python scripts/pptx_export.py figures/flow_diagram.pptx figures/flow_diagram.png [dpi]

PowerPoint's Export writes the slide at the pixel size asked for; the width in pixels is the slide width in inches times
the dpi (default 300), so the result matches the other 300-dpi figures. Nothing is saved back into the .pptx.
"""
import sys
from pathlib import Path

from pptx import Presentation


def main():
    src = Path(sys.argv[1]).resolve()
    dst = Path(sys.argv[2]).resolve()
    dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 300
    prs = Presentation(src)
    w_in, h_in = prs.slide_width / 914400, prs.slide_height / 914400
    import win32com.client  # noqa: E402  (pywin32)
    app = win32com.client.Dispatch("PowerPoint.Application")
    deck = app.Presentations.Open(str(src), ReadOnly=True, Untitled=False, WithWindow=False)
    try:
        deck.Slides(1).Export(str(dst), "PNG", int(round(w_in * dpi)), int(round(h_in * dpi)))
    finally:
        deck.Close()
    from PIL import Image
    im = Image.open(dst)
    im.save(dst, dpi=(dpi, dpi))                  # record the resolution in the file
    print(f"-> {dst} {im.size} at {dpi} dpi")


if __name__ == "__main__":
    main()
