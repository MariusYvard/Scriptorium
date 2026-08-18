#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Coherence terminologique et glossaire automatique pour Scriptorium.

Construit le glossaire des sigles, signale un sigle non defini, un sigle
employe avant sa definition, et des variantes orthographiques d'un meme terme
(trait d'union present ou absent). Rend mecanique la regle "terminologie
stable, terme defini a sa premiere occurrence".

Usage : python3 terminology.py FICHIER [--format text|json]
                                       [--langue-affichage fr|en]
Module importable : analyser(texte) -> dict ;
problemes(d, langue_affichage=None) -> list. Sans langue_affichage, les
constats sont les chaines francaises d'origine a l'octet pres : ce sont
elles que serialise --format json. La mesure, elle, ne connait aucune
langue : les sigles et les variantes de graphie se reperent de la meme
maniere dans les deux.
"""
import argparse
import importlib.util
import json
import os
import re
import sys

_LIB = None


def _lib():
    """Charge libelles.py par son chemin, une seule fois : le module se lit
    par chemin, aucun sys.path n'est garanti."""
    global _LIB
    if _LIB is None:
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "libelles.py")
        spec = importlib.util.spec_from_file_location("scriptorium_libelles",
                                                      chemin)
        _LIB = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_LIB)
    return _LIB


def _langue_du_texte(texte):
    """Langue du document, par delegation a lint-style.py. Elle ne sert qu'a
    choisir la langue d'affichage par defaut : l'analyse elle-meme ne depend
    d'aucune langue. Si le linter n'est pas la, le francais fait office de
    defaut plutot qu'une erreur."""
    try:
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "lint-style.py")
        spec = importlib.util.spec_from_file_location("lint_style", chemin)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.resoudre_langue(texte)
    except Exception:
        return None


ACRO = re.compile(r'\b([A-ZÉÈÀ][A-ZÉÈÀ0-9]{1,6})\b')
# definition : "Expansion (ACRO)" ou "ACRO (expansion)"
DEF_AVANT = re.compile(r'\(([A-ZÉÈÀ][A-ZÉÈÀ0-9]{1,6})\)')
DEF_APRES = re.compile(r'\b([A-ZÉÈÀ][A-ZÉÈÀ0-9]{1,6})\s*\(([^)]{3,})\)')
COURANTS = {"III", "II", "IV", "VI", "VII", "VIII", "IX", "XI", "XII"}


def analyser(texte):
    # positions de definition par sigle
    defs = {}
    for m in DEF_AVANT.finditer(texte):
        defs.setdefault(m.group(1), m.start())
    for m in DEF_APRES.finditer(texte):
        defs.setdefault(m.group(1), min(defs.get(m.group(1), 10 ** 9), m.start()))
    # premiere occurrence de chaque sigle (hors parentheses de definition deja comptees)
    premiere = {}
    compte = {}
    for m in ACRO.finditer(texte):
        a = m.group(1)
        if a in COURANTS or a.isdigit():
            continue
        compte[a] = compte.get(a, 0) + 1
        premiere.setdefault(a, m.start())
    glossaire = {}
    for m in DEF_APRES.finditer(texte):
        glossaire.setdefault(m.group(1), m.group(2).strip())
    non_definis = []
    avant_definition = []
    for a, pos in premiere.items():
        if compte.get(a, 0) < 1:
            continue
        if a not in defs:
            # ignorer les sigles vus une seule fois et tres courts ? non, signaler si >=1
            if compte[a] >= 1 and len(a) >= 2:
                non_definis.append(a)
        elif pos < defs[a]:
            avant_definition.append(a)
    # variantes par trait d'union
    surfaces = {}
    for m in re.finditer(r'\b([A-Za-zÀ-ÿ]{2,}(?:-[A-Za-zÀ-ÿ]{2,})+|[A-Za-zÀ-ÿ]{4,})\b', texte):
        s = m.group(1)
        cle = s.lower().replace('-', '')
        surfaces.setdefault(cle, set()).add(s.lower())
    variantes = []
    for cle, formes in surfaces.items():
        if len(formes) > 1 and any('-' in f for f in formes) and any('-' not in f for f in formes):
            variantes.append(sorted(formes))
    return {
        "glossaire": dict(sorted(glossaire.items())),
        "sigles_non_definis": sorted(set(non_definis)),
        "sigles_avant_definition": sorted(set(avant_definition)),
        "variantes_orthographiques": sorted(variantes),
    }


def problemes(d, langue_affichage=None):
    """Constats lisibles tires de l'analyse.

    Sans langue_affichage, les chaines sont celles d'origine a l'octet pres :
    c'est cette liste que serialise la cle problemes du mode --format json."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    p = []
    if d["sigles_non_definis"]:
        p.append(lib.t("terminology.p.non_definis", la,
                       n=d["sigles_non_definis"]))
    if d["sigles_avant_definition"]:
        p.append(lib.t("terminology.p.avant_definition", la,
                       n=d["sigles_avant_definition"]))
    for v in d["variantes_orthographiques"]:
        p.append(lib.t("terminology.p.variantes", la, formes=v))
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description="Coherence terminologique.")
    ap.add_argument("fichier")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--langue-affichage", choices=["fr", "en"], default=None,
                    help="langue des libelles du rapport texte. Sans "
                         "l'option : la langue du document (pragme "
                         "lint-style:langue), sinon fr. La sortie JSON reste "
                         "francaise quoi qu'il arrive")
    a = ap.parse_args(argv)
    lib = _lib()
    texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    d = analyser(texte)
    if a.format == "json":
        # Le JSON ne se traduit pas : les evals et le jeu d'or le lisent.
        p = problemes(d)
        print(json.dumps({"analyse": d, "problemes": p}, ensure_ascii=False, indent=2))
    else:
        la = lib.resoudre_affichage(a.langue_affichage,
                                    _langue_du_texte(texte))
        p = problemes(d, la)
        print(lib.t("terminology.titre", la))
        if d["glossaire"]:
            print("  " + lib.t("terminology.glossaire", la))
            for k, v in d["glossaire"].items():
                print(f"    {k} = {v}")
        if not p:
            print("  " + lib.t("terminology.aucun_probleme", la))
        for x in p:
            print(f"  - {x}")
    return 1 if (d["sigles_non_definis"] or d["sigles_avant_definition"]) else 0


if __name__ == "__main__":
    sys.exit(main())
