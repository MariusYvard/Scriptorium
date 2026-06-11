#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Memoire de projet pour Scriptorium : un fichier projet.json conserve le
brief, la charte, le glossaire, la bibliotheque de sources, le profil de
discipline et le plan. Recharge au debut de chaque session, il evite de
repartir de zero.

Usage :
    python3 project.py init [--out projet.json]
    python3 project.py show [--file projet.json]
    python3 project.py get CLE [--file projet.json]
    python3 project.py set CLE VALEUR [--file projet.json]
Module importable : charger(path) ; sauver(path, d).
"""
import argparse
import json
import os
import sys

SQUELETTE = {
    "titre": "",
    "genre": "",
    "problematique": "",
    "brief": "",
    "charte": "charte-graphique.json",
    "profil": "profil.json",
    "plan": "plan.json",
    "glossaire": {},
    "sources": [],
    "notes": "",
}


def charger(path):
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    return dict(SQUELETTE)


def sauver(path, d):
    json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Memoire de projet.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init")
    i.add_argument("--out", default="projet.json")
    sh = sub.add_parser("show")
    sh.add_argument("--file", default="projet.json")
    g = sub.add_parser("get")
    g.add_argument("cle")
    g.add_argument("--file", default="projet.json")
    s = sub.add_parser("set")
    s.add_argument("cle")
    s.add_argument("valeur")
    s.add_argument("--file", default="projet.json")
    a = ap.parse_args(argv)
    if a.cmd == "init":
        if os.path.exists(a.out):
            print(f"{a.out} existe deja, inchange.")
            return 0
        sauver(a.out, dict(SQUELETTE))
        print(f"Memoire de projet creee : {a.out}")
        return 0
    if a.cmd == "show":
        print(json.dumps(charger(a.file), ensure_ascii=False, indent=2))
        return 0
    if a.cmd == "get":
        print(json.dumps(charger(a.file).get(a.cle, None), ensure_ascii=False))
        return 0
    if a.cmd == "set":
        d = charger(a.file)
        try:
            val = json.loads(a.valeur)
        except json.JSONDecodeError:
            val = a.valeur
        d[a.cle] = val
        sauver(a.file, d)
        print(f"{a.cle} mis a jour dans {a.file}.")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
