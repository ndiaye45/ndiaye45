"""Carte façon `neofetch` (SVG) : les lignes s'impriment une à une à côté du portrait.

Le contenu raconte ce que les chiffres du calendrier ne disent pas : parcours, stack, projets, disponibilité.
STATIC=1 produit une image figée (aperçu local). Modifier CONTENT ci-dessous puis relancer le script.

Usage : python scripts/make_info_card.py   ->  assets/info-card.svg
"""
from __future__ import annotations

import os
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "assets" / "info-card.svg"
STATIC = os.environ.get("STATIC") == "1"

WIDTH, HEIGHT = 490, 391          # HEIGHT égale la hauteur affichée du portrait (370 px de large) : les deux colonnes s'alignent
FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"
BG, BORDER, TEXT, MUTED, GREEN = "#0d1117", "#30363d", "#c9d1d9", "#8b949e", "#39d353"
KEY_X, VALUE_X, LINE = 24, 112, 18

USER, HOST = "ndiaye45", "github"

# (clé, [lignes de valeur]) ; ≈ 45 caractères maximum par ligne de valeur
CONTENT: list[tuple[str, list[str]]] = [
    ("Name", ["Papa Youssou Ndiaye"]),
    ("Role", ["Backend Developer"]),
    ("Now", ["M.Sc. Computer Science (ARIAS)", "Université d'Orléans, France"]),
    ("Prev", ["B.Sc. Computer Science, Limoges"]),
    ("Focus", ["Distributed systems · AI · Security · DevOps"]),
    ("Stack", ["Java · Spring Boot · Spring Security", "PostgreSQL · Docker · GitHub Actions", "Angular · Flutter · JavaFX · Python"]),
    ("Built", ["Service Management: Spring Boot + Angular", "ImageLib: JavaFX, ML tags, k-means colours", "AP Santé: Flutter + Firebase (Univ. Limoges)"]),
    ("Status", ["Open to internship · 4-6 months · Jan 2027"]),
    ("Web", ["yousndiaye.netlify.app"]),
]
SWATCHES = ["#ff5f56", "#ffbd2e", "#39d353", "#58a6ff", "#bc8cff", "#69f0a0", "#c9d1d9", "#30363d"]


def render() -> str:
    lines: list[str] = []          # chaque élément est un <g> animé (une ligne imprimée)
    y = 62

    def add(markup: str) -> None:
        index = len(lines)
        style = "" if STATIC else f' style="animation-delay:{0.25 + index * 0.11:.2f}s"'
        lines.append(f'<g class="l"{style}>{markup}</g>')

    add(f'<text x="{KEY_X}" y="{y}"><tspan class="k">{USER}</tspan><tspan class="d">@</tspan><tspan class="k">{HOST}</tspan></text>')
    y += 8
    add(f'<line x1="{KEY_X}" y1="{y}" x2="{KEY_X + 7.55 * (len(USER) + len(HOST) + 1):.0f}" y2="{y}" stroke="{MUTED}" stroke-width="1"/>')
    y += LINE + 4

    for key, values in CONTENT:
        for i, value in enumerate(values):
            label = f'<text x="{KEY_X}" y="{y}" class="k">{escape(key)}</text>' if i == 0 else ""
            add(f'{label}<text x="{VALUE_X}" y="{y}" class="v">{escape(value)}</text>')
            y += LINE
        y += 3                                                    # petit espace entre deux rubriques

    y += 5
    swatches = "".join(f'<rect x="{KEY_X + i * 22}" y="{y - 11}" width="18" height="12" rx="3" fill="{c}"/>' for i, c in enumerate(SWATCHES))
    add(swatches)

    animation = "" if STATIC else (
        "@keyframes in{from{opacity:0;transform:translateX(-10px)}to{opacity:1;transform:none}}"
        ".l{opacity:0;animation:in .45s ease-out forwards}")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Profile card of Papa Youssou Ndiaye">
<style>
.k{{font:bold 12.5px {FONT};fill:{GREEN}}}
.v{{font:12.5px {FONT};fill:{TEXT}}}
.d{{font:12.5px {FONT};fill:{MUTED}}}
.b{{font:12px {FONT};fill:{MUTED}}}
{animation}
</style>
<rect x=".5" y=".5" width="{WIDTH - 1}" height="{HEIGHT - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>
<circle cx="24" cy="22" r="6" fill="#ff5f56"/><circle cx="44" cy="22" r="6" fill="#ffbd2e"/><circle cx="64" cy="22" r="6" fill="#27c93f"/>
<text x="{WIDTH // 2}" y="26" text-anchor="middle" class="b">{USER}@{HOST}: ~</text>
{chr(10).join(lines)}
</svg>
'''


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(), encoding="utf-8")
    print(f"-> {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
