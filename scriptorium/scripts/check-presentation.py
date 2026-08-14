#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validation deterministe d'un deck de presentation exporte en PDF.

Portions adaptees du projet openscience (Synthetic Sciences, InkVell Inc.), Apache-2.0,
github.com/synthetic-sciences/openscience (logique de validate_presentation.py, backend.cli/
skills/writing/scientific-slides/scripts/). Modifications Marius Yvard, MIT.

Confronte le nombre de pages a la duree annoncee (regle ~1 a 2 diapositives par minute, voir
produire/references/genre-presentation.md pour un minutage plus fin par temps de l'arc), estime
la densite de texte par page (pypdf si present, sinon pdftotext, sinon la verification est
sautee et le rapport le dit explicitement : jamais une densite inventee), et signale les pages
au rendu dense si un backend de rendu est disponible (aucune dependance obligatoire, cascade a
la maniere de images.py : pypdf pour compter et extraire le texte, pdftotext/pdfinfo/pdftoppm de
poppler-utils en repli, sinon degradation propre).

Usage :
    python3 check-presentation.py FICHIER.pdf --duree 15 [--format text|json] [--strict]

Module importable : analyser(chemin, duree) -> dict ; bornes_diapositives(duree) -> (min, max).
"""
import argparse
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile

# Regle de reference : environ 1 a 2 diapositives par minute. Bande volontairement large pour
# valider des styles divers (d'un rythme assertion-evidence sobre a un style tres visuel dense) ;
# NOTE DE COHERENCE : produire/references/genre-presentation.md propose un minutage plus sobre,
# ancre sur la regle 10/20/30 de Kawasaki (environ une diapositive pour deux minutes) pour le
# style soutenance/presentation qu'il documente. Les deux reperes divergent volontairement : ce
# script reste un plancher/plafond de validation generique, pas une reprise du minutage d'un genre.
SEUIL_MOTS_PAR_DIAPO = 60
SEUIL_OCTETS_PAR_PIXEL = 0.35
DPI_RENDU = 50


def bornes_diapositives(duree_min):
    """Repere (minimum, maximum) de diapositives pour une duree donnee, regle ~1-2/minute."""
    lo = max(3, math.floor(duree_min * 1.0))
    hi = max(lo + 1, math.ceil(duree_min * 2.0))
    return lo, hi


def _has(cmd):
    return shutil.which(cmd) is not None


def _dimensions_png(chemin):
    with open(chemin, "rb") as f:
        data = f.read(24)
    if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        w, h = struct.unpack(">II", data[16:24])
        return w, h
    return None, None


def compter_pages_et_taille(chemin):
    """Nombre de pages et dimensions (pts) de la premiere page. pypdf, sinon pdfinfo, sinon
    inconnu (jamais devine)."""
    try:
        from pypdf import PdfReader
        r = PdfReader(chemin)
        n = len(r.pages)
        box = r.pages[0].mediabox
        return n, (float(box.width), float(box.height)), "pypdf"
    except Exception:
        pass
    if _has("pdfinfo"):
        try:
            out = subprocess.run(["pdfinfo", chemin], capture_output=True, text=True, timeout=20).stdout
            n, dims = None, None
            for ligne in out.splitlines():
                if ligne.startswith("Pages:"):
                    n = int(ligne.split(":", 1)[1].strip())
                if ligne.startswith("Page size:"):
                    morceaux = ligne.split(":", 1)[1].strip().split()
                    if len(morceaux) >= 3:
                        dims = (float(morceaux[0]), float(morceaux[2]))
            if n is not None:
                return n, dims, "pdfinfo"
        except Exception:
            pass
    return None, None, None


def extraire_texte_pages(chemin):
    """Texte par page. pypdf, sinon pdftotext (saut de page 0x0c). (None, None) si aucun backend."""
    try:
        from pypdf import PdfReader
        r = PdfReader(chemin)
        return [p.extract_text() or "" for p in r.pages], "pypdf"
    except Exception:
        pass
    if _has("pdftotext"):
        try:
            with tempfile.TemporaryDirectory() as d:
                cible = os.path.join(d, "texte.txt")
                subprocess.run(["pdftotext", "-layout", chemin, cible],
                               check=True, capture_output=True, timeout=30)
                with open(cible, encoding="utf-8", errors="replace") as f:
                    brut = f.read()
                pages = brut.split("\x0c")
                if pages and pages[-1] == "":
                    pages = pages[:-1]
                return pages, "pdftotext"
        except Exception:
            pass
    return None, None


def rendre_pages_basses_res(chemin, dpi=DPI_RENDU):
    """Rendu bas-DPI de chaque page : [(largeur, hauteur, octets_png)]. PyMuPDF si present,
    sinon pdftoppm (poppler-utils), sinon (None, None) : backend optionnel, comme images.py."""
    try:
        import fitz  # PyMuPDF, optionnel
        doc = fitz.open(chemin)
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        out = []
        for page in doc:
            pix = page.get_pixmap(matrix=mat)
            out.append((pix.width, pix.height, len(pix.tobytes("png"))))
        doc.close()
        return out, "pymupdf"
    except ImportError:
        pass
    except Exception:
        pass
    if _has("pdftoppm"):
        try:
            with tempfile.TemporaryDirectory() as d:
                prefixe = os.path.join(d, "p")
                subprocess.run(["pdftoppm", "-png", "-r", str(dpi), chemin, prefixe],
                               check=True, capture_output=True, timeout=60)
                out = []
                for nom in sorted(os.listdir(d)):
                    chemin_img = os.path.join(d, nom)
                    taille = os.path.getsize(chemin_img)
                    largeur, hauteur = _dimensions_png(chemin_img)
                    out.append((largeur, hauteur, taille))
                return out, "pdftoppm"
        except Exception:
            pass
    return None, None


def analyser(chemin, duree=None):
    """Analyse complete d'un fichier de presentation. Retourne un rapport dict :
    fichier, info (liste), avertissements (liste), problemes (liste)."""
    rapport = {"fichier": os.path.basename(chemin), "info": [], "avertissements": [], "problemes": []}
    if not os.path.isfile(chemin):
        rapport["problemes"].append(f"Fichier introuvable : {chemin}")
        return rapport
    if not chemin.lower().endswith(".pdf"):
        rapport["avertissements"].append("Extension non .pdf : concu pour un deck exporte en PDF (voir livrer, action document).")

    n_pages, dims, backend_pages = compter_pages_et_taille(chemin)
    if n_pages is None:
        rapport["problemes"].append("Nombre de pages indetermine : aucun backend disponible (installer pypdf, ou poppler-utils pour pdfinfo).")
    else:
        rapport["info"].append(f"Pages : {n_pages} (source : {backend_pages}).")
        if dims and dims[1]:
            l, h = dims
            rapport["info"].append(f"Dimensions de la premiere page : {l:.0f} x {h:.0f} pts (ratio {l / h:.2f}).")
        if duree:
            lo, hi = bornes_diapositives(duree)
            rapport["info"].append(f"Repere pour {duree:g} min (regle ~1-2 diapositives/minute) : {lo} a {hi} diapositives.")
            if n_pages < lo:
                rapport["avertissements"].append(
                    f"{n_pages} diapositives pour {duree:g} min : en dessous de {lo}, le temps risque d'etre trop court pour le contenu ou le rythme trop lent.")
            elif n_pages > hi:
                rapport["avertissements"].append(
                    f"{n_pages} diapositives pour {duree:g} min : au-dessus de {hi}, risque de depassement du temps annonce.")
            else:
                rapport["info"].append("Nombre de diapositives dans le repere de la duree annoncee.")

    textes, backend_texte = extraire_texte_pages(chemin)
    if textes is None:
        rapport["info"].append("Densite de texte non calculee : aucun backend disponible (pypdf ou pdftotext), verification sautee plutot qu'estimee.")
    else:
        denses = [(i, len(txt.split())) for i, txt in enumerate(textes, 1) if len(txt.split()) > SEUIL_MOTS_PAR_DIAPO]
        rapport["info"].append(f"Densite de texte calculee sur {len(textes)} page(s) (source : {backend_texte}), seuil {SEUIL_MOTS_PAR_DIAPO} mots/diapositive.")
        if denses:
            liste = ", ".join(f"page {i} ({n} mots)" for i, n in denses[:10])
            suffixe = ", ..." if len(denses) > 10 else ""
            rapport["avertissements"].append(
                f"Diapositives au-dessus de {SEUIL_MOTS_PAR_DIAPO} mots : {liste}{suffixe}. "
                f"Une diapositive de fond porte peu de texte (voir produire/references/genre-presentation.md)."
            )

    rendus, backend_rendu = rendre_pages_basses_res(chemin)
    if rendus is None:
        rapport["info"].append("Rendu image non effectue : aucun backend disponible (PyMuPDF ou pdftoppm/poppler-utils), verification des pages denses sautee.")
    else:
        pages_denses = []
        for i, (l, h, taille) in enumerate(rendus, 1):
            if not l or not h:
                continue
            opp = taille / (l * h)
            if opp > SEUIL_OCTETS_PAR_PIXEL:
                pages_denses.append((i, opp))
        rapport["info"].append(f"Rendu bas-DPI ({DPI_RENDU} dpi) de {len(rendus)} page(s) via {backend_rendu}, repere {SEUIL_OCTETS_PAR_PIXEL} octet/pixel.")
        if pages_denses:
            liste = ", ".join(f"page {i} ({opp:.2f} o/px)" for i, opp in pages_denses[:10])
            suffixe = ", ..." if len(pages_denses) > 10 else ""
            rapport["avertissements"].append(
                f"Pages au rendu dense (repere approximatif par octet/pixel, pas une mesure de "
                f"lisibilite reelle) : {liste}{suffixe}. Verifier a l'oeil a la distance de projection."
            )

    return rapport


def _afficher_text(rapport):
    print(f"Validation de presentation : {rapport['fichier']}")
    print("Information :" if rapport["info"] else "Information : aucune")
    for i in rapport["info"]:
        print(f"  - {i}")
    print("Avertissements :" if rapport["avertissements"] else "Avertissements : aucun")
    for w in rapport["avertissements"]:
        print(f"  - {w}")
    print("Problemes :" if rapport["problemes"] else "Problemes : aucun")
    for e in rapport["problemes"]:
        print(f"  - {e}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Validation deterministe d'un deck de presentation (PDF).")
    p.add_argument("fichier")
    p.add_argument("--duree", "-d", type=float, help="duree annoncee en minutes")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--strict", action="store_true", help="code de sortie 1 si un avertissement ou un probleme est releve")
    a = p.parse_args(argv)
    rapport = analyser(a.fichier, a.duree)
    if a.format == "json":
        print(json.dumps(rapport, ensure_ascii=False, indent=2))
    else:
        _afficher_text(rapport)
    if a.strict and (rapport["avertissements"] or rapport["problemes"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
