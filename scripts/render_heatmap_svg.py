"""Dessine data/contributions.json en calendrier 53 semaines x 7 jours (SVG animé, une seule fois).

Chaque case glisse vers le bas en diagonale au chargement (keyframes CSS), puis l'image se fige : pas de boucle.
GitHub ne lit pas le JavaScript des README mais joue les animations CSS/SMIL d'un SVG inclus via <img>.
STATIC=1 produit une image figée (aperçu local, Quick Look).

Usage : python scripts/render_heatmap_svg.py   ->  assets/contrib-heatmap.svg
"""
from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUTPUT = ROOT / "assets" / "contrib-heatmap.svg"
STATIC = os.environ.get("STATIC") == "1"

# rampe verte façon GitHub ; le niveau 5 est un vert néon réservé aux jours records
PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG, BORDER, MUTED, TEXT = "#0d1117", "#30363d", "#8b949e", "#c9d1d9"

WIDTH = 860          # même largeur que portrait (370) + carte (490) : les bords s'alignent dans le README
BOX, PITCH = 12, 15
LEFT, TOP = 46, 56
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def level_of(day: dict, maximum: int) -> int:
    level = day["level"]
    if level >= 4 and maximum > 0 and day["count"] >= 0.8 * maximum:
        return 5
    return level


def render(data: dict) -> str:
    days = data["days"]
    first = date.fromisoformat(days[0]["date"])
    week_start = first - timedelta(days=(first.weekday() + 1) % 7)       # le calendrier commence le dimanche
    maximum = max(d["count"] for d in days)

    cells, month_labels = [], []
    last_label_column = -10
    previous_month = None
    columns = 0
    for day in days:
        current = date.fromisoformat(day["date"])
        offset = (current - week_start).days
        column, row = offset // 7, offset % 7
        columns = max(columns, column + 1)
        x, y = LEFT + column * PITCH, TOP + row * PITCH
        delay = 0.15 + column * 0.018 + row * 0.045                          # vague diagonale
        style = "" if STATIC else f' style="animation-delay:{delay:.3f}s"'
        cells.append(f'<rect class="c" x="{x}" y="{y}" width="{BOX}" height="{BOX}" rx="3" '
                     f'fill="{PALETTE[level_of(day, maximum)]}"{style}/>')
        if row == 0 and current.month != previous_month:
            if previous_month is not None and column - last_label_column >= 3:
                month_labels.append(f'<text x="{x}" y="{TOP - 10}" class="m">{MONTHS[current.month - 1]}</text>')
                last_label_column = column
            previous_month = current.month

    grid_bottom = TOP + 7 * PITCH
    height = grid_bottom + 56
    day_labels = "".join(
        f'<text x="{LEFT - 10}" y="{TOP + row * PITCH + 10}" class="m" text-anchor="end">{name}</text>'
        for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")))

    # légende « Less ▢▢▢▢▢▢ More », alignée à droite
    legend_width = 28 + 6 * PITCH + 30
    legend_x = WIDTH - 24 - legend_width
    legend_y = grid_bottom + 24
    legend = [f'<text x="{legend_x}" y="{legend_y + 10}" class="m">Less</text>']
    for i, color in enumerate(PALETTE):
        legend.append(f'<rect x="{legend_x + 32 + i * PITCH}" y="{legend_y}" width="{BOX}" height="{BOX}" rx="3" fill="{color}"/>')
    legend.append(f'<text x="{legend_x + 32 + 6 * PITCH + 4}" y="{legend_y + 10}" class="m">More</text>')

    best = data["best_day"]
    best_label = date.fromisoformat(best["date"]).strftime("%b %d, %Y").replace(" 0", " ")
    parts = [f'{data["total"]:,} contributions in the last year'.replace(",", " "),
             f'longest streak {data["longest_streak"]} day{"s" if data["longest_streak"] != 1 else ""}']
    if best["count"] > 0:
        parts.append(f'best day {best["count"]} ({best_label})')
    footer = f'<text x="24" y="{legend_y + 10}" class="t">{"  ·  ".join(parts)}</text>'

    animation = "" if STATIC else (
        "@keyframes drop{from{opacity:0;transform:translateY(-9px)}to{opacity:1;transform:none}}"
        ".c{opacity:0;transform-box:fill-box;animation:drop .5s cubic-bezier(.2,.8,.2,1) forwards}")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" aria-label="Contribution graph of {data["user"]}: {data["total"]} contributions in the last year">
<style>
.m{{font:11px {FONT};fill:{MUTED}}}
.t{{font:12px {FONT};fill:{TEXT}}}
.h{{font:12px {FONT};fill:{MUTED}}}
{animation}
</style>
<rect x=".5" y=".5" width="{WIDTH - 1}" height="{height - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>
<text x="24" y="28" class="h">{data["user"]} / contribution graph</text>
{"".join(month_labels)}
{day_labels}
{chr(10).join(cells)}
{chr(10).join(legend)}
{footer}
</svg>
'''


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(data), encoding="utf-8")
    print(f"-> {OUTPUT.relative_to(ROOT)} ({OUTPUT.stat().st_size // 1024} Ko)")


if __name__ == "__main__":
    main()
