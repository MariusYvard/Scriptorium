#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Coherence terminologique et glossaire automatique pour Scriptorium.

Construit le glossaire des sigles, signale un sigle non defini, un sigle
employe avant sa definition, et des variantes orthographiques d'un meme terme
(trait d'union present ou absent). Rend mecanique la regle "terminologie
stable, terme defini a sa premiere occurrence".

Usage : python3 terminology.py FICHIER [--format text|json]
Module importable : analyser(texte) -> dict.
"""
import argparse
import json
import re
import sys

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


def problemes(d):
    p = []
    if d["sigles_non_definis"]:
        p.append(f"Sigles employes sans definition : {d['sigles_non_definis']}")
    if d["sigles_avant_definition"]:
        p.append(f"Sigles employes avant leur definition : {d['sigles_avant_definition']}")
    for v in d["variantes_orthographiques"]:
        p.append(f"Variantes d'un meme terme (trait d'union) : {v}")
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description="Coherence terminologique.")
    ap.add_argument("fichier")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    a = ap.parse_args(argv)
    texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    d = analyser(texte)
    p = problemes(d)
    if a.format == "json":
        print(json.dumps({"analyse": d, "problemes": p}, ensure_ascii=False, indent=2))
    else:
        print("Terminologie")
        if d["glossaire"]:
            print("  Glossaire :")
            for k, v in d["glossaire"].items():
                print(f"    {k} = {v}")
        if not p:
            print("  Aucun probleme terminologique.")
        for x in p:
            print(f"  - {x}")
    return 1 if (d["sigles_non_definis"] or d["sigles_avant_definition"]) else 0


if __name__ == "__main__":
    sys.exit(main())
