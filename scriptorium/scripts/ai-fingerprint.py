#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Detecteur d'empreinte IA pour Scriptorium.

Mesure les marqueurs statistiques d'un texte genere : faible variabilite de
longueur de phrase, ouvertures de phrases repetitives, cadence ternaire
systematique, connecteurs suremployes, bigrammes repetes, amplification
contrastive (non seulement ... mais). Tes directives proscrivent ces tics,
ce script les rend mesurables.

Usage : python3 ai-fingerprint.py FICHIER [--format text|json]
Module importable : analyser(texte) -> dict.
"""
import argparse
import json
import math
import re
import sys
from collections import Counter

SENT = re.compile(r'[^.!?…]+[.!?…]+', re.S)
MOT = re.compile(r"\b[\wàâäéèêëîïôöùûüçœ'-]+\b", re.I)
TRIPLE = re.compile(r"\b[\wà-ÿœ]+,\s+[\wà-ÿœ]+\s+(?:et|ou)\s+[\wà-ÿœ]+\b", re.I)
AMPLI = re.compile(r"(?i)non seulement\b.{1,80}?\bmais\b|"
                   r"ne\s+\w+\s+pas seulement\b.{1,80}?\bmais\b|"
                   r"il ne s'agit pas seulement\b.{1,80}?\bmais\b")
CONNECTEURS = ["par ailleurs", "en effet", "de plus", "en outre", "notamment",
               "cependant", "néanmoins", "toutefois", "de surcroît", "en somme",
               "par conséquent", "ainsi", "en définitive"]
STOP = set("le la les un une de des du et ou a à en pour par sur dans que qui se "
           "ne pas plus est sont ce cette son sa ses leur au aux d l il elle on "
           "nous vous ils elles avec sans mais donc or ni car".split())


def _ecart_type(vals):
    if len(vals) < 2:
        return 0.0
    m = sum(vals) / len(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def analyser(texte):
    phrases = [p.strip() for p in SENT.findall(texte) if p.strip()]
    longueurs = [len(MOT.findall(p)) for p in phrases]
    longueurs = [l for l in longueurs if l > 0]
    mots = MOT.findall(texte)
    nmots = len(mots) or 1
    nph = len(longueurs) or 1
    premiers = [MOT.findall(p)[0].lower() for p in phrases if MOT.findall(p)]
    cnt = Counter(premiers)
    top = cnt.most_common(1)[0] if cnt else ("", 0)
    pct_ouverture = round(100 * top[1] / len(premiers), 1) if premiers else 0.0
    bas = texte.lower()
    nconn = sum(bas.count(c) for c in CONNECTEURS)
    dens_conn = round(nconn / nph, 2)
    ntriple = len(TRIPLE.findall(texte))
    dens_triple = round(1000 * ntriple / nmots, 1)
    cw = [m.lower() for m in mots if m.lower() not in STOP and len(m) > 2]
    bg = Counter(zip(cw, cw[1:]))
    bigr = bg.most_common(1)[0] if bg else (("", ""), 0)
    nampli = len(AMPLI.findall(texte))
    et = round(_ecart_type(longueurs), 1)
    signaux = []
    if nph >= 8 and et < 5:
        signaux.append(f"Variabilite de longueur faible (ecart-type {et}), rythme uniforme.")
    if len(premiers) >= 8 and pct_ouverture > 25:
        signaux.append(f"Ouvertures repetitives ({pct_ouverture}% commencent par « {top[0]} »).")
    if dens_conn > 0.5:
        signaux.append(f"Connecteurs suremployes ({dens_conn} par phrase).")
    if dens_triple > 6:
        signaux.append(f"Cadence ternaire dense ({dens_triple} enumerations triples / 1000 mots).")
    if bigr[1] >= 4:
        signaux.append(f"Bigramme repete {bigr[1]} fois : « {bigr[0][0]} {bigr[0][1]} ».")
    if nampli >= 1:
        signaux.append(f"Amplification contrastive (« non seulement ... mais ») x{nampli}.")
    return {
        "phrases": nph, "ecart_type_longueur": et, "ouverture_max_pct": pct_ouverture,
        "densite_connecteurs": dens_conn, "densite_triples": dens_triple,
        "bigramme_max": {"bigramme": " ".join(bigr[0]).strip(), "compte": bigr[1]},
        "amplificateurs": nampli, "signaux": signaux,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Detecteur d'empreinte IA.")
    ap.add_argument("fichier")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    a = ap.parse_args(argv)
    texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    d = analyser(texte)
    if a.format == "json":
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print("Empreinte IA")
        print(f"  ecart-type longueur={d['ecart_type_longueur']} | ouverture max={d['ouverture_max_pct']}%"
              f" | connecteurs/phrase={d['densite_connecteurs']} | triples/1000={d['densite_triples']}")
        if not d["signaux"]:
            print("  Aucun signal marque d'empreinte IA.")
        for s in d["signaux"]:
            print(f"  - {s}")
    return 1 if len(d["signaux"]) >= 2 else 0


if __name__ == "__main__":
    sys.exit(main())
