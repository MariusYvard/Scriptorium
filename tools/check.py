#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Porte d'integration continue editoriale pour Scriptorium.

Passe ou echoue un ou plusieurs documents contre un seuil de scorecard.
A utiliser en CI ou en pre-commit pour verrouiller un document comme du code.

Usage :
    python3 tools/check.py FICHIER... [--seuil 85]
    python3 tools/check.py FICHIER... [--seuil 85] --outrepasser [--justification "texte"]

Code de sortie 0 si tous les documents atteignent le seuil, ou si un
outrepassement valide a ete journalise. 1 sinon (seuil non atteint sans
outrepassement, ou outrepassement refuse faute de justification suffisante).

Echelle de friction des outrepassements (--outrepasser), a 3 crans, calculee
sur le compte d'outrepassements deja journalises pour ce projet (ou ce
fichier local) : cran 1 (premier outrepassement) accepte avec un simple
avertissement ; cran 2 exige --justification "texte" non vide ; cran 3 et
au-dela exige une justification d'au moins 100 caracteres. Chaque
outrepassement est journalise, jamais silencieux : dans scripts/project.py
(entree de type outrepassement, non supprimable) si un projet.json existe
au chemin --projet, sinon dans un fichier local .outrepassements.json
(append-only, meme format d'entree). scripts/project.py expose
compter_outrepassements() pour un futur affichage par audit-doc.py (non
cable dans ce lot).
"""
import argparse
import datetime
import glob
import importlib.util
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.join(ICI, "..", "scripts")
FALLBACK = ".outrepassements.json"


def _mod(f, n):
    spec = importlib.util.spec_from_file_location(n, os.path.join(SCR, f))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


score = _mod("scorecard.py", "scorecard")
projet = _mod("project.py", "project")


def _cran_local(path):
    if not os.path.isfile(path):
        return 1
    try:
        arr = json.load(open(path, encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        arr = []
    return len(arr) + 1


def _journaliser_local(path, libelle, cran, justification):
    arr = []
    if os.path.isfile(path):
        try:
            arr = json.load(open(path, encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            arr = []
    arr.append({
        "horodatage": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "type": "outrepassement",
        "libelle": libelle,
        "cran": cran,
        "justification": justification or "",
    })
    json.dump(arr, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Porte CI editoriale.")
    ap.add_argument("fichiers", nargs="+")
    ap.add_argument("--seuil", type=int, default=85)
    ap.add_argument("--outrepasser", action="store_true",
                     help="Passer outre un echec de seuil (journalise, friction croissante a 3 crans).")
    ap.add_argument("--justification", default="",
                     help="Justification de l'outrepassement (requise a partir du 2e cran).")
    ap.add_argument("--projet", default="projet.json",
                     help="Chemin du projet.json pour journaliser l'outrepassement (defaut projet.json).")
    a = ap.parse_args(argv)
    paths = []
    for f in a.fichiers:
        paths += sorted(glob.glob(f, recursive=True)) or [f]
    echec = False
    echoues = []
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
            echoues.append(p)
    if not vus:
        print("Aucun fichier a verifier.")
    if echec and a.outrepasser:
        projet_existe = os.path.isfile(a.projet)
        cran = projet.prochain_cran(projet.charger(a.projet)) if projet_existe else _cran_local(FALLBACK)
        try:
            projet.valider_justification(cran, a.justification)
        except ValueError as e:
            print(f"Outrepassement refuse : {e}")
            return 1
        libelle = f"seuil {a.seuil} non atteint sur {len(echoues)} fichier(s) : {', '.join(echoues[:3])}"
        if len(echoues) > 3:
            libelle += ", ..."
        if projet_existe:
            projet.journaliser_outrepassement(a.projet, libelle, cran, a.justification or None)
            trace = a.projet
        else:
            _journaliser_local(FALLBACK, libelle, cran, a.justification)
            trace = FALLBACK
        print(f"[OUTREPASSE] cran {cran} journalise dans {trace}.")
        if cran == 1:
            print("Avertissement : 1er outrepassement, aucune justification requise. Le 2e en exigera une.")
        return 0
    return 1 if echec else 0


if __name__ == "__main__":
    sys.exit(main())
