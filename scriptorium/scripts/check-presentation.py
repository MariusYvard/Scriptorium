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
                                              [--langue-affichage fr|en]

Module importable : analyser(chemin, duree, langue_affichage=None) -> dict ;
bornes_diapositives(duree) -> (min, max). Sans langue_affichage, les constats sont les
chaines francaises d'origine a l'octet pres : ce sont elles que serialise --format json.
Le fichier analyse est un PDF, il ne porte pas de pragme de langue : la langue
d'affichage par defaut est donc le francais, et seule l'option la change.
"""
import argparse
import importlib.util
import json
import math
import os
import shutil
import struct
import subprocess
import sys
import tempfile

_LIB = None


def _lib():
    """Charge libelles.py par son chemin, une seule fois : le module se lit par chemin,
    aucun sys.path n'est garanti quand le script est lance depuis un dossier quelconque."""
    global _LIB
    if _LIB is None:
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "libelles.py")
        spec = importlib.util.spec_from_file_location("scriptorium_libelles", chemin)
        _LIB = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_LIB)
    return _LIB


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


def analyser(chemin, duree=None, langue_affichage=None):
    """Analyse complete d'un fichier de presentation. Retourne un rapport dict :
    fichier, info (liste), avertissements (liste), problemes (liste).

    Sans langue_affichage, les trois listes portent les chaines francaises d'origine a
    l'octet pres : ce sont elles que serialise le mode --format json."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    rapport = {"fichier": os.path.basename(chemin), "info": [], "avertissements": [], "problemes": []}
    if not os.path.isfile(chemin):
        rapport["problemes"].append(lib.t("presentation.m.fichier_introuvable", la, chemin=chemin))
        return rapport
    if not chemin.lower().endswith(".pdf"):
        rapport["avertissements"].append(lib.t("presentation.m.extension", la))

    n_pages, dims, backend_pages = compter_pages_et_taille(chemin)
    if n_pages is None:
        rapport["problemes"].append(lib.t("presentation.m.pages_indeterminees", la))
    else:
        rapport["info"].append(lib.t("presentation.m.pages", la, n=n_pages, backend=backend_pages))
        if dims and dims[1]:
            l, h = dims
            rapport["info"].append(lib.t(
                "presentation.m.dimensions", la, largeur="%.0f" % l, hauteur="%.0f" % h,
                ratio="%.2f" % (l / h)))
        if duree:
            lo, hi = bornes_diapositives(duree)
            rapport["info"].append(lib.t("presentation.m.repere", la, duree="%g" % duree,
                                         lo=lo, hi=hi))
            if n_pages < lo:
                rapport["avertissements"].append(lib.t(
                    "presentation.m.trop_peu", la, n=n_pages, duree="%g" % duree, lo=lo))
            elif n_pages > hi:
                rapport["avertissements"].append(lib.t(
                    "presentation.m.trop", la, n=n_pages, duree="%g" % duree, hi=hi))
            else:
                rapport["info"].append(lib.t("presentation.m.dans_le_repere", la))

    textes, backend_texte = extraire_texte_pages(chemin)
    if textes is None:
        rapport["info"].append(lib.t("presentation.m.densite_sautee", la))
    else:
        denses = [(i, len(txt.split())) for i, txt in enumerate(textes, 1) if len(txt.split()) > SEUIL_MOTS_PAR_DIAPO]
        rapport["info"].append(lib.t("presentation.m.densite_calculee", la, n=len(textes),
                                     backend=backend_texte, seuil=SEUIL_MOTS_PAR_DIAPO))
        if denses:
            liste = ", ".join(lib.t("presentation.item.mots", la, page=i, n=n)
                              for i, n in denses[:10])
            suite = lib.t("presentation.suite", la) if len(denses) > 10 else ""
            rapport["avertissements"].append(lib.t(
                "presentation.m.pages_denses_texte", la, seuil=SEUIL_MOTS_PAR_DIAPO,
                liste=liste, suite=suite))

    rendus, backend_rendu = rendre_pages_basses_res(chemin)
    if rendus is None:
        rapport["info"].append(lib.t("presentation.m.rendu_saute", la))
    else:
        pages_denses = []
        for i, (l, h, taille) in enumerate(rendus, 1):
            if not l or not h:
                continue
            opp = taille / (l * h)
            if opp > SEUIL_OCTETS_PAR_PIXEL:
                pages_denses.append((i, opp))
        rapport["info"].append(lib.t("presentation.m.rendu", la, dpi=DPI_RENDU,
                                     n=len(rendus), backend=backend_rendu,
                                     seuil=SEUIL_OCTETS_PAR_PIXEL))
        if pages_denses:
            liste = ", ".join(lib.t("presentation.item.octets", la, page=i,
                                    valeur="%.2f" % opp) for i, opp in pages_denses[:10])
            suite = lib.t("presentation.suite", la) if len(pages_denses) > 10 else ""
            rapport["avertissements"].append(lib.t(
                "presentation.m.pages_denses_rendu", la, liste=liste, suite=suite))

    return rapport


def rapport_texte(rapport, langue_affichage=None):
    """Rendu texte lisible. Les constats portes par rapport ont ete composes dans la
    langue d'affichage par analyser() : ils sont repris tels quels."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    out = [lib.t("presentation.titre", la, fichier=rapport["fichier"])]
    for cle, cle_vide, entrees in (
            ("presentation.info", "presentation.info_aucune", rapport["info"]),
            ("presentation.avertissements", "presentation.avertissements_aucun",
             rapport["avertissements"]),
            ("presentation.problemes", "presentation.problemes_aucun",
             rapport["problemes"])):
        out.append(lib.t(cle if entrees else cle_vide, la))
        out += ["  - %s" % x for x in entrees]
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description="Validation deterministe d'un deck de presentation (PDF).")
    p.add_argument("fichier")
    p.add_argument("--duree", "-d", type=float, help="duree annoncee en minutes")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--strict", action="store_true", help="code de sortie 1 si un avertissement ou un probleme est releve")
    p.add_argument("--langue-affichage", choices=["fr", "en"], default=None,
                   help="langue des libelles du rapport texte (defaut fr : un PDF ne "
                        "porte pas de pragme de langue). La sortie JSON reste francaise "
                        "quoi qu'il arrive")
    a = p.parse_args(argv)
    if a.format == "json":
        # Le JSON ne se traduit pas : les evals et le jeu d'or le lisent.
        rapport = analyser(a.fichier, a.duree)
        print(json.dumps(rapport, ensure_ascii=False, indent=2))
    else:
        la = _lib().resoudre_affichage(a.langue_affichage)
        rapport = analyser(a.fichier, a.duree, la)
        print(rapport_texte(rapport, la))
    if a.strict and (rapport["avertissements"] or rapport["problemes"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
