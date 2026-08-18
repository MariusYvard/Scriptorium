#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Controle d'integrite numerique pour Scriptorium.

Signale les pourcentages impossibles (superieurs a 100), les partitions de
pourcentages qui ne somment pas a cent, un separateur decimal mixte et un
espacement du signe pourcent contraire a la convention de la langue. Un
rapport se juge d'abord sur la justesse de ses nombres.

Les deux derniers controles dependent de la LANGUE, et c'est le melange au
sein d'une meme convention qui est fautif, jamais la coexistence des deux
caracteres :

  - francais : virgule decimale, espace comme separateur de milliers
    ("1 234 567,89"). Un point entre deux chiffres y est un separateur
    decimal etranger.
  - anglais : point decimal, virgule comme separateur de milliers
    ("1,234,567.89"). Cette forme est correcte et ne doit rien declencher.
    Les groupes de milliers bien formes sont retires avant l'examen, sans
    quoi tout grand nombre anglais passerait pour un melange.

Usage : python3 numbers.py FICHIER [--format text|json] [--langue fr|en|auto]
Module importable : analyser(texte, langue=None) -> dict.
"""
import argparse
import json
import os
import re
import sys

PCT = re.compile(r'(\d{1,3}(?:[.,]\d+)?)\s*%')
LISTE_PCT = re.compile(r'((?:\d{1,3}(?:[.,]\d+)?\s*%[\s,;]*(?:et|ou|and)?\s*){3,})')

LANGUES = ("fr", "en")

# Virgule de milliers anglaise bien formee : precedee d'un chiffre, suivie
# d'exactement trois chiffres. Elle est retiree du texte avant de chercher un
# separateur decimal etranger, sinon "1,234,567.89" ferait un faux positif.
MILLIERS_EN = re.compile(r'(?<=\d),(?=\d{3}(?!\d))')

# Espacement du signe pourcent. Le francais insere une espace avant le signe
# (Imprimerie nationale, BIPM), l'anglais le colle au nombre (APA 7, Chicago).
# Seuls les cas non ambigus sont releves. La nature exacte de l'espace
# francaise, insecable en typographie soignee, n'est PAS exigee ici : dans une
# source Markdown l'espace ordinaire est l'usage courant, et l'exiger leverait
# un constat a chaque pourcentage, ce qui est precisement le defaut a eviter.
PCT_COLLE = re.compile(r'\d%')
PCT_ESPACE = re.compile(r'\d[ \t   ]+%')

_LINT = None


def _lint():
    """Charge lint-style.py a la demande, une seule fois. Le nom du fichier
    porte un tiret, il n'est pas importable tel quel. La resolution de langue
    y est definie et documentee : elle est lue ici, jamais recopiee."""
    global _LINT
    if _LINT is None:
        import importlib.util
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "lint-style.py")
        spec = importlib.util.spec_from_file_location("lint_style", chemin)
        _LINT = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_LINT)
    return _LINT


def resoudre_langue(texte, langue=None):
    """Tranche la langue d'analyse, par delegation a lint-style.py : option
    explicite, puis auto, puis pragme du document, puis francais. Un code
    hors fr, en et auto n'est pas honore, la resolution ordinaire s'applique
    et la langue retenue est rendue dans la cle "langue" du resultat."""
    if langue is not None and langue not in LANGUES and langue != "auto":
        langue = None
    return _lint().resoudre_langue(texte, langue)


def _val(s):
    return float(s.replace(',', '.'))


def separateur_mixte(texte, langue):
    """Vrai quand deux conventions decimales cohabitent dans le meme texte.

    En anglais, les virgules de milliers bien formees sont retirees d'abord :
    seule une virgule decimale residuelle, employee a cote d'un point
    decimal, constitue un melange.
    """
    examine = MILLIERS_EN.sub('', texte) if langue == "en" else texte
    return bool(re.search(r'\d,\d', examine)) and bool(re.search(r'\d\.\d', examine))


def espacement_pourcent(texte, langue):
    """Occurrences dont l'espacement du signe pourcent contredit la
    convention de la langue. Liste vide quand tout est conforme."""
    if langue == "en":
        return [m.group(0) for m in PCT_ESPACE.finditer(texte)]
    return [m.group(0) for m in PCT_COLLE.finditer(texte)]


def analyser(texte, langue=None):
    langue = resoudre_langue(texte, langue)
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
    return {
        "langue": langue,
        "pourcentages_impossibles": impossibles,
        "partitions_incoherentes": partitions,
        "separateur_decimal_mixte": separateur_mixte(texte, langue),
        "espacement_pourcent": espacement_pourcent(texte, langue),
    }


def problemes(d):
    p = []
    if d["pourcentages_impossibles"]:
        p.append(f"Pourcentages superieurs a 100 : {d['pourcentages_impossibles']}")
    for part in d["partitions_incoherentes"]:
        p.append(f"Partition de pourcentages qui ne somme pas a 100 : {part['valeurs']} (somme {part['somme']})")
    if d["separateur_decimal_mixte"]:
        p.append("Separateur decimal mixte (virgule et point). Choisir une seule convention.")
    if d["espacement_pourcent"]:
        attendu = ("le signe pourcent se colle au nombre en anglais"
                   if d.get("langue") == "en"
                   else "une espace precede le signe pourcent en francais")
        p.append(f"Espacement du signe pourcent contraire a la convention "
                 f"({attendu}) : {d['espacement_pourcent']}")
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description="Integrite numerique.")
    ap.add_argument("fichier")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--langue", choices=["fr", "en", "auto"], default=None,
                     help="convention numerique appliquee. Sans l'option : le "
                          "pragme lint-style:langue du document, sinon fr")
    a = ap.parse_args(argv)
    texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    d = analyser(texte, a.langue)
    p = problemes(d)
    if a.format == "json":
        print(json.dumps({"analyse": d, "problemes": p}, ensure_ascii=False, indent=2))
    else:
        print("Integrite numerique")
        print(f"  langue analysee : {d['langue']}")
        if not p:
            print("  Aucun probleme numerique detecte.")
        for x in p:
            print(f"  - {x}")
    return 1 if d["pourcentages_impossibles"] else 0


if __name__ == "__main__":
    sys.exit(main())
