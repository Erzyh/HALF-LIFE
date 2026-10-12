"""Extended Data Fig. 5: the sensitivity panels (a and b, figures/sensitivity.png from scripts/sensitivity.py) above the
still-served-identifier curves (c, figures/census_survival_unconditional.png from scripts/census_extension.py). Both
scripts draw their own panel letters outside the axes, so nothing is written on the images here. No API calls.
Output: figures/ed_sensitivity_extension.png. Usage: python scripts/ed_fig5_compose.py
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
F = ROOT / "figures"


def main():
    a = Image.open(F / "sensitivity.png").convert("RGB")
    c = Image.open(F / "census_survival_unconditional.png").convert("RGB")
    dpi = int(round(a.info.get("dpi", (300, 300))[0]))
    gap = round(0.15 * dpi)
    im = Image.new("RGB", (max(a.width, c.width), a.height + gap + c.height), "white")
    im.paste(a, (0, 0))
    im.paste(c, (0, a.height + gap))
    im.save(F / "ed_sensitivity_extension.png", dpi=(dpi, dpi))
    print("figures/ed_sensitivity_extension.png", im.size, f"{dpi} dpi")


if __name__ == "__main__":
    main()
