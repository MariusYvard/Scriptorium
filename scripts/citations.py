#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Moteur de citations pour Scriptorium : BibTeX, formatage, deduplication.

Lit du BibTeX, formate chaque reference en APA 7 ou Vancouver, deduplique par
DOI puis par titre. La recuperation des metadonnees a partir d'un DOI (Crossref)
est optionnelle et reseau (--doi). Tout le reste est hors ligne.

Usage :
    python3 citations.py FICHIER.bib --to apa|vancouver [--dedupe]
    python3 citations.py --doi 10.xxxx/yyyy   (reseau, recupere une entree)
Module importable : parser_bibtex(texte) ; format_apa(e) ; format_vancouver(e) ; dedupe(entrees).
"""
import argparse
import json
import re
import sys

ENTREE = re.compile(r'@(\w+)\s*\{\s*([^,]+)\s*,(.*?)\n\s*\}', re.S)
CHAMP = re.compile(r'(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|"[^"]*"|[^,\n]+)', re.S)


def parser_bibtex(texte):
    entrees = []
    for m in ENTREE.finditer(texte):
        typ, cle, corps = m.group(1).lower(), m.group(2).strip(), m.group(3)
        champs = {}
        for c in CHAMP.finditer(corps):
            k = c.group(1).lower()
            v = c.group(2).strip().strip(',').strip()
            if v and v[0] in '{"' and v[-1] in '}"':
                v = v[1:-1]
            champs[k] = ' '.join(v.split())
        champs["_type"] = typ
        champs["_cle"] = cle
        entrees.append(champs)
    return entrees


def _auteurs(brut):
    if not brut:
        return []
    out = []
    for a in re.split(r'\s+and\s+', brut):
        a = a.strip()
        if ',' in a:
            nom, prenoms = [p.strip() for p in a.split(',', 1)]
        else:
            bouts = a.split()
            nom = bouts[-1] if bouts else a
            prenoms = ' '.join(bouts[:-1])
        initiales = ''.join(p[0].upper() + '.' for p in prenoms.split() if p)
        out.append((nom, initiales))
    return out


def format_apa(e):
    aut = _auteurs(e.get("author", ""))
    if aut:
        noms = [f"{n}, {i}" for n, i in aut]
        if len(noms) == 1:
            sa = noms[0]
        elif len(noms) <= 7:
            sa = ", ".join(noms[:-1]) + " et " + noms[-1]
        else:
            sa = ", ".join(noms[:6]) + " ... " + noms[-1]
    else:
        sa = "Anonyme"
    an = e.get("year", "s.d.")
    titre = e.get("title", "Sans titre")
    s = f"{sa} ({an}). {titre}."
    if e.get("journal"):
        s += f" {e['journal']}"
        if e.get("volume"):
            s += f", {e['volume']}"
            if e.get("number"):
                s += f"({e['number']})"
        if e.get("pages"):
            s += f", {e['pages'].replace('--', '-')}"
        s += "."
    elif e.get("publisher"):
        s += f" {e['publisher']}."
    if e.get("doi"):
        s += f" https://doi.org/{e['doi']}"
    return s


def format_vancouver(e):
    aut = _auteurs(e.get("author", ""))
    noms = [f"{n} {i.replace('.', '')}" for n, i in aut]
    if len(noms) > 6:
        sa = ", ".join(noms[:6]) + ", et al"
    else:
        sa = ", ".join(noms) if noms else "Anonyme"
    titre = e.get("title", "Sans titre")
    s = f"{sa}. {titre}."
    if e.get("journal"):
        s += f" {e['journal']}."
        s += f" {e.get('year', 's.d.')}"
        if e.get("volume"):
            s += f";{e['volume']}"
            if e.get("number"):
                s += f"({e['number']})"
        if e.get("pages"):
            s += f":{e['pages'].replace('--', '-')}"
        s += "."
    else:
        s += f" {e.get('publisher', '')} {e.get('year', '')}.".replace("  ", " ")
    if e.get("doi"):
        s += f" doi:{e['doi']}"
    return s


def dedupe(entrees):
    vus = {}
    uniques = []
    doublons = []
    for e in entrees:
        cle = (e.get("doi", "").lower().strip()
               or re.sub(r'[^a-z0-9]', '', e.get("title", "").lower()))
        if cle and cle in vus:
            doublons.append(e.get("_cle"))
        else:
            if cle:
                vus[cle] = True
            uniques.append(e)
    return uniques, doublons


def fetch_doi(doi):  # reseau, appele seulement avec --doi
    import urllib.request
    url = "https://api.crossref.org/works/" + doi.strip()
    with urllib.request.urlopen(url, timeout=15) as r:
        msg = json.loads(r.read().decode("utf-8"))["message"]
    auteurs = " and ".join(
        f"{a.get('family', '')}, {a.get('given', '')}" for a in msg.get("author", []))
    return {
        "_type": msg.get("type", "article"), "_cle": doi.replace("/", "_"),
        "author": auteurs, "title": " ".join(msg.get("title", ["Sans titre"])),
        "year": str(msg.get("issued", {}).get("date-parts", [[None]])[0][0] or ""),
        "journal": " ".join(msg.get("container-title", [""])),
        "volume": msg.get("volume", ""), "number": msg.get("issue", ""),
        "pages": msg.get("page", ""), "doi": msg.get("DOI", doi),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Moteur de citations BibTeX.")
    ap.add_argument("fichier", nargs="?", help="fichier .bib, ou - pour stdin")
    ap.add_argument("--to", choices=["apa", "vancouver"], default="apa")
    ap.add_argument("--dedupe", action="store_true")
    ap.add_argument("--doi", help="recupere une entree depuis Crossref (reseau)")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    a = ap.parse_args(argv)
    if a.doi:
        e = fetch_doi(a.doi)
        print(format_apa(e) if a.to == "apa" else format_vancouver(e))
        return 0
    texte = sys.stdin.read() if a.fichier in (None, "-") else open(a.fichier, encoding="utf-8").read()
    entrees = parser_bibtex(texte)
    doublons = []
    if a.dedupe:
        entrees, doublons = dedupe(entrees)
    fmt = format_apa if a.to == "apa" else format_vancouver
    refs = [fmt(e) for e in entrees]
    if a.format == "json":
        print(json.dumps({"references": refs, "doublons": doublons}, ensure_ascii=False, indent=2))
    else:
        for i, r in enumerate(refs, 1):
            print(f"{i}. {r}" if a.to == "vancouver" else r)
        if doublons:
            print(f"\nDoublons ecartes : {doublons}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
