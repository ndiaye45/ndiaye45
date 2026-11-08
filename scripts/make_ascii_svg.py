"""Convertit source-prepped.png en portrait ASCII monochrome qui « s'écrit » ligne par ligne (SVG, SMIL).

- Rampe de densité : clair (clairsemé) -> sombre (dense). L'espace en tête efface le fond.
- Monochrome : une seule couleur de remplissage. Colorer chaque caractère donne l'effet « neige » de la plupart des portraits.
- Chaque ligne est révélée de gauche à droite par un rectangle de découpe animé, un petit curseur bloc suit le bord ;
  les lignes se décalent de haut en bas. Le portrait s'imprime une fois puis se fige (pas de boucle).
- SMIL tourne dans un SVG inclus via <img> : c'est ce que GitHub exécute.
STATIC=1 produit une image figée (aperçu local).

Usage : python scripts/make_ascii_svg.py [source-prepped.png]   ->  assets/ascii-portrait.svg
"""
from __future__ import annotations

import os
import sys
from html import escape
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "assets" / "ascii-portrait.svg"
STATIC = os.environ.get("STATIC") == "1"

RAMP = " .`:-=+*cs#%@"            # clair (clairsemé) -> sombre (dense)
COLUMNS, ROWS = 100, 53           # grille fixe : le portrait a toujours la même emprise
CHAR_W, LINE_H = 6.0, 12.0        # largeur / hauteur d'une case (rapport 0,5 : un caractère est ~2x plus haut que large)
PAD = 16
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
BG, BORDER, INK = "#0d1117", "#30363d", "#c9d1d9"
GAMMA = 1.0                       # < 1 assombrit les tons moyens (plus de densité), > 1 les éclaircit


def to_grid(path: Path) -> np.ndarray:
    """Image -> tableau ROWS x COLUMNS de tons (0 = noir, 1 = blanc), centrée sur un fond blanc."""
    image = Image.open(path).convert("L")
    # une case est ~2x plus haute que large : à l'écran, la hauteur d'une ligne compte pour deux pixels de largeur
    scale = min(COLUMNS / image.width, ROWS / (image.height * CHAR_W / LINE_H))
    target_w = max(1, round(image.width * scale))
    target_h = max(1, round(image.height * scale * CHAR_W / LINE_H))
    target_w, target_h = min(target_w, COLUMNS), min(target_h, ROWS)
    small = image.resize((target_w, target_h), Image.Resampling.BOX)       # moyenne par case : bien plus fin que du sous-échantillonnage
    canvas = Image.new("L", (COLUMNS, ROWS), 255)
    canvas.paste(small, ((COLUMNS - target_w) // 2, (ROWS - target_h) // 2))
    return (np.asarray(canvas, dtype=float) / 255.0) ** GAMMA


def to_rows(tones: np.ndarray) -> list[str]:
    indices = np.rint((1 - tones) * (len(RAMP) - 1)).astype(int)
    return ["".join(RAMP[i] for i in row) for row in indices]


def render(rows: list[str]) -> str:
    text_w = COLUMNS * CHAR_W
    width = text_w + 2 * PAD
    height = ROWS * LINE_H + 2 * PAD
    clips, texts, cursors = [], [], []
    for i, row in enumerate(rows):
        top = PAD + i * LINE_H
        begin = 0.35 + i * 0.06                                    # lignes décalées de haut en bas
        duration = 0.5
        wipe = ""
        cursor = ""
        if not STATIC:
            wipe = (f'<animate attributeName="width" from="0" to="{text_w}" begin="{begin:.2f}s" dur="{duration}s" fill="freeze"/>')
            cursor = (f'<rect y="{top:.1f}" width="{CHAR_W}" height="{LINE_H}" fill="{INK}" opacity="0" x="{PAD}">'
                      f'<set attributeName="opacity" to="0.85" begin="{begin:.2f}s"/>'
                      f'<animate attributeName="x" from="{PAD}" to="{PAD + text_w - CHAR_W}" begin="{begin:.2f}s" dur="{duration}s" fill="freeze"/>'
                      f'<set attributeName="opacity" to="0" begin="{begin + duration:.2f}s"/></rect>')
        clips.append(f'<clipPath id="c{i}"><rect x="{PAD}" y="{top:.1f}" width="{text_w if STATIC else 0}" height="{LINE_H}">{wipe}</rect></clipPath>')
        if row.strip():
            texts.append(f'<text x="{PAD}" y="{top + LINE_H * 0.78:.1f}" textLength="{text_w}" lengthAdjust="spacing" '
                         f'clip-path="url(#c{i})" xml:space="preserve">{escape(row)}</text>')
        cursors.append(cursor)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width:g}" height="{height:g}" viewBox="0 0 {width:g} {height:g}" role="img" aria-label="ASCII portrait of Papa Youssou Ndiaye">
<style>text{{font:10px {FONT};fill:{INK};white-space:pre}}</style>
<defs>
{chr(10).join(clips)}
</defs>
<rect x=".5" y=".5" width="{width - 1:g}" height="{height - 1:g}" rx="12" fill="{BG}" stroke="{BORDER}"/>
{chr(10).join(texts)}
{chr(10).join(c for c in cursors if c)}
</svg>
'''


def main() -> int:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "source-prepped.png"
    if not source.exists():
        print(f"{source} introuvable : lancez d'abord  python scripts/prep_photo.py <photo>")
        return 1
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(to_rows(to_grid(source))), encoding="utf-8")
    print(f"-> {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size // 1024} Ko)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
