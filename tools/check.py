#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Porte d'integration continue editoriale pour Scriptorium.

Passe ou echoue un ou plusieurs documents contre un seuil de scorecard.
A utiliser en CI ou en pre-commit pour verrouiller un document comme du code.

Usage : python3 tools/check.py FICHIER... [--seuil 85]
Code de sortie 0 si tous les documents atteignent le seuil, 1 sinon.
"""
import argparse
import glob
import importlib.util
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.join(ICI, "..", "scripts")


def _mod(f, n):
    spec = importlib.util.spec_from_file_location(n, os.path.join(SCR, f))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


score = _mod("scorecard.py", "scorecard")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Porte CI editoriale.")
    ap.add_argument("fichiers", nargs="+")
    ap.add_argument("--seuil", type=int, default=85)
    a = ap.parse_args(argv)
    paths = []
    for f in a.fichiers:
        paths += sorted(glob.glob(f, recursive=True)) or [f]
    echec = False
    vus = 0
    for p in paths:
        if not os.path.isfile(p):
            continue
        vus += 1
        r = score.evaluer(open(p, encoding="utf-8").read())
        ok = r["total"] >= a.seuil
        print(f"  [{'OK' if ok else 'ECHEC'}] {r['total']:>3}/100 (seuil {a.seuil})  {p}")
        if not ok:
            echec = True
    if not vus:
        print("Aucun fichier a verifier.")
    return 1 if echec else 0


if __name__ == "__main__":
    sys.exit(main())
