#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Controle d'integrite numerique pour Scriptorium.

Signale les pourcentages impossibles (superieurs a 100), les partitions de
pourcentages qui ne somment pas a cent, et un separateur decimal mixte
(virgule et point employes pour les decimales). Un rapport se juge d'abord
sur la justesse de ses nombres.

Usage : python3 numbers.py FICHIER [--format text|json]
Module importable : analyser(texte) -> dict.
"""
import argparse
import json
import re
import sys

PCT = re.compile(r'(\d{1,3}(?:[.,]\d+)?)\s*%')
LISTE_PCT = re.compile(r'((?:\d{1,3}(?:[.,]\d+)?\s*%[\s,;]*(?:et|ou|and)?\s*){3,})')


def _val(s):
    return float(s.replace(',', '.'))


def analyser(texte):
    impossibles = []
    for m in PCT.finditer(texte):
        v = _val(m.group(1))
        if v > 100:
            impossibles.append(m.group(0))
    partitions = []
    for ligne in texte.splitlines():
        for m in LISTE_PCT.finditer(ligne):
            vals = [_val(x) for x in re.findall(r'(\d{1,3}(?:[.,]\d+)?)\s*%', m.group(1))]
            if len(vals) >= 3:
                s = sum(vals)
                if not (99.0 <= s <= 101.0):
                    partitions.append({"valeurs": vals, "somme": round(s, 2)})
    a_virgule = bool(re.search(r'\d,\d', texte))
    a_point = bool(re.search(r'\d\.\d', texte))
    return {
        "pourcentages_impossibles": impossibles,
        "partitions_incoherentes": partitions,
        "separateur_decimal_mixte": a_virgule and a_point,
    }


def problemes(d):
    p = []
    if d["pourcentages_impossibles"]:
        p.append(f"Pourcentages superieurs a 100 : {d['pourcentages_impossibles']}")
    for part in d["partitions_incoherentes"]:
        p.append(f"Partition de pourcentages qui ne somme pas a 100 : {part['valeurs']} (somme {part['somme']})")
    if d["separateur_decimal_mixte"]:
        p.append("Separateur decimal mixte (virgule et point). Choisir une seule convention.")
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description="Integrite numerique.")
    ap.add_argument("fichier")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    a = ap.parse_args(argv)
    texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    d = analyser(texte)
    p = problemes(d)
    if a.format == "json":
        print(json.dumps({"analyse": d, "problemes": p}, ensure_ascii=False, indent=2))
    else:
        print("Integrite numerique")
        if not p:
            print("  Aucun probleme numerique detecte.")
        for x in p:
            print(f"  - {x}")
    return 1 if d["pourcentages_impossibles"] else 0


if __name__ == "__main__":
    sys.exit(main())
