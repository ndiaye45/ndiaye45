"""Prépare une photo pour la conversion ASCII (à lancer une fois par photo).

Un visage éclairé à plat devient un bloc sombre illisible en ASCII. Trois traitements corrigent cela :
  1. suppression du fond (rembg, facultatif) pour isoler le sujet ;
  2. CLAHE (égalisation adaptative du contraste, OpenCV) : donne de vrais reliefs, lumières et ombres ;
  3. composition sur blanc pur : le fond tombe sur le bout « vide » de la rampe ASCII (blanc = espaces).
Le résultat est recadré autour du sujet. Sortie : source-prepped.png (niveaux de gris).

Installation : pip install -r scripts/requirements-portrait.txt
Usage : python scripts/prep_photo.py source-photo.jpg [source-prepped.png]
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MARGIN = 0.06           # marge autour du sujet, en proportion de sa taille


def remove_background(image: Image.Image) -> Image.Image:
    try:
        from rembg import remove          # lourd (onnxruntime + modèle) : seulement si installé
    except ImportError:
        print("rembg absent : le fond n'est pas supprimé (pip install rembg). Un fond uni donnera quand même un bon résultat.")
        return image
    return remove(image)


def prep(source: Path, target: Path) -> None:
    image = Image.open(source).convert("RGBA")
    image = remove_background(image)
    alpha = np.array(image.getchannel("A"))
    has_mask = alpha.min() < 255

    white = Image.new("RGBA", image.size, (255, 255, 255, 255))
    white.alpha_composite(image)
    gray = np.array(white.convert("L"))

    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    boosted = clahe.apply(gray)
    # Le CLAHE grise légèrement le fond : on le remet à blanc pur (masque rembg, sinon seuil sur les tons presque blancs).
    background = alpha < 16 if has_mask else gray > 245
    boosted[background] = 255

    ys, xs = np.where(~background)
    if len(xs):                                   # recadrage serré autour du sujet, avec une marge
        pad_x = int((xs.max() - xs.min()) * MARGIN)
        pad_y = int((ys.max() - ys.min()) * MARGIN)
        left, right = max(0, xs.min() - pad_x), min(boosted.shape[1], xs.max() + pad_x + 1)
        top, bottom = max(0, ys.min() - pad_y), min(boosted.shape[0], ys.max() + pad_y + 1)
        boosted = boosted[top:bottom, left:right]

    Image.fromarray(boosted).save(target)
    print(f"{source.name} -> {target} ({boosted.shape[1]}x{boosted.shape[0]})")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    prep(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "source-prepped.png")
    return 0


if __name__ == "__main__":
    sys.exit(main())
