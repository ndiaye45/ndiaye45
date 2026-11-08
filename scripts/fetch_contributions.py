"""Récupère le calendrier de contributions PUBLIC d'un compte GitHub, sans token ni API GraphQL.

GitHub sert ce calendrier en HTML à https://github.com/users/<login>/contributions (le même fragment que la page de profil).
Sortie : data/contributions.json (jours bruts + statistiques dérivées).

Usage : PROFILE_USER=ndiaye45 python scripts/fetch_contributions.py
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import OrderedDict
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "contributions.json"
USER = os.environ.get("PROFILE_USER", "ndiaye45")


def fetch_html(user: str) -> str:
    response = requests.get(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "profile-readme-heatmap", "Accept": "text/html"},
        timeout=30,
    )
    response.raise_for_status()
    return response.text


def parse_days(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    tooltips = {t.get("for"): t.get_text(" ", strip=True) for t in soup.find_all("tool-tip")}
    days = []
    for cell in soup.select("td.ContributionCalendar-day[data-date]"):
        text = tooltips.get(cell.get("id"), "")
        match = re.match(r"(\d+)\s+contribution", text)       # « No contributions on … » -> 0
        days.append({
            "date": cell["data-date"],
            "level": int(cell.get("data-level", 0)),
            "count": int(match.group(1)) if match else 0,
        })
    days.sort(key=lambda d: d["date"])
    return days


def streaks(days: list[dict]) -> tuple[int, int]:
    """(série en cours, plus longue série). Une série en cours n'est pas coupée si aujourd'hui n'a pas encore de contribution."""
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    current = 0
    index = len(days) - 1
    if index >= 0 and days[index]["count"] == 0:
        index -= 1                                            # la journée en cours n'est peut-être pas terminée
    while index >= 0 and days[index]["count"] > 0:
        current += 1
        index -= 1
    return current, longest


def build(days: list[dict], user: str) -> dict:
    if not days:
        raise RuntimeError("Aucune cellule de calendrier trouvée : le format HTML de GitHub a peut-être changé")
    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])
    monthly: "OrderedDict[str, int]" = OrderedDict()
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]
    return {
        "user": user,
        "from": days[0]["date"],
        "to": days[-1]["date"],
        "total": sum(d["count"] for d in days),
        "active_days": sum(1 for d in days if d["count"] > 0),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly,
        "days": days,
    }


def main() -> int:
    data = build(parse_days(fetch_html(USER)), USER)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{USER}: {data['total']} contributions, {data['active_days']} jours actifs, "
          f"série en cours {data['current_streak']}, record {data['longest_streak']} -> {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
