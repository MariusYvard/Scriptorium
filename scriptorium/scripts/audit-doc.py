#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit consolide d'un document pour Scriptorium.

Lance le scorecard, le detecteur d'empreinte IA, le controle de coherence et
l'audit de tableaux sur un fichier texte, et produit un rapport unifie.
Pour un PDF ou un Word, la competence auditer-existant extrait d'abord le
texte, puis appelle ce script.

Usage : python3 audit-doc.py FICHIER.md [--format text|json]
"""
import argparse
import importlib.util
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))


def _mod(f, n):
    spec = importlib.util.spec_from_file_location(n, os.path.join(ICI, f))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


score = _mod("scorecard.py", "scorecard")
aifp = _mod("ai-fingerprint.py", "ai_fingerprint")
coh = _mod("coherence.py", "coherence")
tab = _mod("tables.py", "tables")


def auditer(texte):
    return {
        "scorecard": score.evaluer(texte),
        "empreinte_ia": aifp.analyser(texte)["signaux"],
        "coherence": coh.problemes(coh.analyser(texte)),
        "tableaux": tab.auditer(texte)["problemes"],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Audit consolide.")
    ap.add_argument("fichier")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    a = ap.parse_args(argv)
    texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    d = auditer(texte)
    if a.format == "json":
        print(json.dumps(d, ensure_ascii=False, indent=2))
        return 0
    sc = d["scorecard"]
    print(f"AUDIT CONSOLIDE — scorecard {sc['total']}/100 ({sc['verdict']})\n")
    for nom, ax in sc["axes"].items():
        print(f"  {nom:26} {ax['score']:>2}/20")
    print("\nEmpreinte IA :")
    print("  " + ("aucun signal" if not d["empreinte_ia"] else "; ".join(d["empreinte_ia"])))
    print("Coherence :")
    print("  " + ("aucune redite" if not d["coherence"] else "; ".join(d["coherence"])))
    print("Tableaux :")
    print("  " + ("aucun probleme" if not d["tableaux"] else "; ".join(d["tableaux"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
