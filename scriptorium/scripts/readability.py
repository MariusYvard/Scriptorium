#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Métriques de lisibilité déterministes pour Scriptorium (français).

Transforme la règle floue « varier le rythme » en mesure : longueur de
phrase moyenne et écart-type, part de phrases longues et courtes, longueur
de paragraphe, densité lexicale, approximation du taux de passif, indice
LIX (agnostique à la langue, lisible pour le français).

Usage :
    python3 readability.py FICHIER [--format text|json]
    cat doc.md | python3 readability.py -

Le module est importable : mesurer(texte) -> dict.
"""
import argparse
import json
import math
import re
import sys

MOT_RE = re.compile(r"\b[\wàâäéèêëîïôöùûüç'-]+\b", re.I)
PHRASE_RE = re.compile(r"[^.!?…]+[.!?…]+", re.S)
PASSIF_RE = re.compile(
    r"\b(est|sont|été|était|étaient|fut|furent|sera|seront|"
    r"a été|ont été|avait été)\s+\w*(é|és|ée|ées)\b", re.I)


def nettoyer(texte):
    # retire les blocs de code et la syntaxe markdown lourde
    texte = re.sub(r"```.*?```", " ", texte, flags=re.S)
    texte = re.sub(r"`[^`]*`", " ", texte)
    texte = re.sub(r"^\s{0,3}[#>|].*$", " ", texte, flags=re.M)
    texte = re.sub(r"[*_#>]+", " ", texte)
    return texte


def ecart_type(valeurs):
    if len(valeurs) < 2:
        return 0.0
    moy = sum(valeurs) / len(valeurs)
    var = sum((v - moy) ** 2 for v in valeurs) / (len(valeurs) - 1)
    return math.sqrt(var)


def mesurer(texte):
    propre = nettoyer(texte)
    phrases = [p.strip() for p in PHRASE_RE.findall(propre) if p.strip()]
    if not phrases:
        phrases = [propre.strip()] if propre.strip() else []
    longueurs = [len(MOT_RE.findall(p)) for p in phrases]
    longueurs = [l for l in longueurs if l > 0]
    mots = MOT_RE.findall(propre)
    n_mots = len(mots)
    n_phr = len(longueurs) or 1
    paras = [b for b in re.split(r"\n\s*\n", texte) if b.strip()]
    phr_par_para = []
    for b in paras:
        bp = nettoyer(b)
        phr_par_para.append(max(1, len(PHRASE_RE.findall(bp))))
    mots_longs = sum(1 for m in mots if len(m) > 6)
    types = {m.lower() for m in mots}
    n_passif = len(PASSIF_RE.findall(propre))
    moy_phr = (sum(longueurs) / n_phr) if longueurs else 0.0
    lix = (moy_phr + 100.0 * mots_longs / n_mots) if n_mots else 0.0
    return {
        "mots": n_mots,
        "phrases": len(longueurs),
        "paragraphes": len(paras),
        "longueur_phrase_moyenne": round(moy_phr, 1),
        "longueur_phrase_ecart_type": round(ecart_type(longueurs), 1),
        "phrases_longues_sup30_pct": round(100 * sum(1 for l in longueurs if l > 30) / n_phr, 1),
        "phrases_courtes_inf8_pct": round(100 * sum(1 for l in longueurs if l < 8) / n_phr, 1),
        "phrases_par_paragraphe_moyenne": round(sum(phr_par_para) / len(phr_par_para), 1) if phr_par_para else 0.0,
        "densite_lexicale": round(len(types) / n_mots, 3) if n_mots else 0.0,
        "taux_passif_approx_pct": round(100 * n_passif / n_phr, 1),
        "indice_lix": round(lix, 1),
    }


def interpreter(m):
    notes = []
    if m["longueur_phrase_ecart_type"] < 5 and m["phrases"] >= 5:
        notes.append("Écart-type faible : rythme monotone, varier la longueur des phrases.")
    if m["longueur_phrase_moyenne"] > 28:
        notes.append("Phrases longues en moyenne : fatigue l'attention, intercaler des phrases courtes.")
    if m["phrases_courtes_inf8_pct"] < 8 and m["phrases"] >= 6:
        notes.append("Peu de phrases courtes : réserver des phrases brèves aux messages clés.")
    if m["indice_lix"] > 56:
        notes.append("LIX élevé (texte difficile), acceptable pour un lectorat expert, lourd sinon.")
    if m["indice_lix"] < 34 and m["mots"] > 120:
        notes.append("LIX bas (texte très simple), vérifier que la précision n'est pas sacrifiée.")
    if m["densite_lexicale"] < 0.35 and m["mots"] > 200:
        notes.append("Densité lexicale faible : répétitions probables, varier le vocabulaire.")
    if m["taux_passif_approx_pct"] > 25:
        notes.append("Taux de passif élevé : préférer des verbes d'action quand c'est possible.")
    if not notes:
        notes.append("Rythme et lisibilité dans les bornes attendues.")
    return notes


def rapport_texte(m):
    out = ["Métriques de lisibilité"]
    cle_lib = {
        "mots": "Mots", "phrases": "Phrases", "paragraphes": "Paragraphes",
        "longueur_phrase_moyenne": "Longueur phrase (moy.)",
        "longueur_phrase_ecart_type": "Longueur phrase (écart-type)",
        "phrases_longues_sup30_pct": "Phrases > 30 mots (%)",
        "phrases_courtes_inf8_pct": "Phrases < 8 mots (%)",
        "phrases_par_paragraphe_moyenne": "Phrases / paragraphe (moy.)",
        "densite_lexicale": "Densité lexicale (TTR)",
        "taux_passif_approx_pct": "Passif approx. (%)",
        "indice_lix": "Indice LIX",
    }
    for k, lib in cle_lib.items():
        out.append(f"  {lib:32} {m[k]}")
    out.append("\nLecture :")
    out += [f"  - {n}" for n in interpreter(m)]
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description="Métriques de lisibilité Scriptorium.")
    p.add_argument("fichier", help="chemin du fichier, ou - pour stdin")
    p.add_argument("--format", choices=["text", "json"], default="text")
    a = p.parse_args(argv)
    try:
        texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    except OSError as e:
        print(f"Erreur de lecture : {e}", file=sys.stderr)
        return 2
    m = mesurer(texte)
    if a.format == "json":
        print(json.dumps({"metriques": m, "lecture": interpreter(m)},
                         ensure_ascii=False, indent=2))
    else:
        print(rapport_texte(m))
    return 0


if __name__ == "__main__":
    sys.exit(main())
