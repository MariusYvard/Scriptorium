#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generation et audit de tableaux pour Scriptorium.

Genere un tableau Markdown autonome a partir d'un CSV ou d'un JSON (en-tetes,
unites, source) et audite les tableaux Markdown d'un document : cellules vides,
colonne numerique sans unite dans l'en-tete, ligne Total incoherente. Les
tableaux sont l'autre moitie du principe « une figure est du contenu ».

Le tableau produit par gen est du contenu de document : il reste dans la
langue de l'ecrit et ne passe pas par la couche de libelles. Ce qui en passe,
ce sont les constats d'audit et les messages de la commande.

Usage :
    python3 tables.py gen DATA.csv|.json [--caption "..."] [--source "..."]
    python3 tables.py audit DOCUMENT.md [--format text|json]
                                        [--langue-affichage fr|en]
Module importable : generer(...) ; auditer(texte, langue_affichage=None)
-> dict.
"""
import argparse
import csv
import importlib.util
import json
import os
import re
import sys

ICI = os.path.dirname(os.path.abspath(__file__))

_MODULES = {}


def _charger(fichier, nom):
    """Charge un module voisin par son chemin, une seule fois. Les noms de
    fichiers portent un tiret, ils ne sont pas importables tels quels."""
    if nom not in _MODULES:
        spec = importlib.util.spec_from_file_location(
            nom, os.path.join(ICI, fichier))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _MODULES[nom] = mod
    return _MODULES[nom]


def _lib():
    return _charger("libelles.py", "scriptorium_libelles")


def _lint():
    return _charger("lint-style.py", "lint_style")


TBL = re.compile(r'^\s*\|.*\|\s*$')
NUM = re.compile(r'^-?\d+(?:[.,]\d+)?$')
UNITE = re.compile(r'[(\[].*[)\]]|[%€$]|\b(kg|g|m|cm|mm|km|s|h|MPa|GPa|°C|K|W|kW|MW|€|\$|pts?|an|ans)\b', re.I)


def _md(headers, rows, caption=None, source=None):
    out = ["| " + " | ".join(str(h) for h in headers) + " |",
           "| " + " | ".join("---" for _ in headers) + " |"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    s = "\n".join(out)
    if caption:
        s = f"Tableau : {caption}\n\n" + s
    if source:
        s += f"\n\nSource : {source}"
    return s


def generer(path, caption=None, source=None):
    if path.endswith(".json"):
        data = json.load(open(path, encoding="utf-8"))
        if isinstance(data, dict) and "columns" in data:
            headers, rows = data["columns"], data["rows"]
        else:
            headers = list(data[0].keys())
            rows = [[d.get(h, "") for h in headers] for d in data]
    else:
        r = list(csv.reader(open(path, encoding="utf-8")))
        headers, rows = r[0], r[1:]
    return _md(headers, rows, caption, source)


def _parse(tb):
    rows = []
    for l in tb:
        cells = [c.strip() for c in l.strip().strip('|').split('|')]
        rows.append(cells)
    body = [r for r in rows if not all(re.fullmatch(r':?-{3,}:?', c or '') for c in r)]
    return body


def auditer(texte, langue_affichage=None):
    """Audit des tableaux Markdown du texte.

    Sans langue_affichage, les constats sont les chaines francaises d'origine
    a l'octet pres : c'est cette liste que serialise la cle problemes du mode
    --format json, et que lit audit-doc.py."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    lignes = texte.splitlines()
    tables, cur = [], []
    for l in lignes:
        if TBL.match(l):
            cur.append(l)
        elif cur:
            tables.append(cur)
            cur = []
    if cur:
        tables.append(cur)
    problemes = []
    for ti, tb in enumerate(tables, 1):
        body = _parse(tb)
        if len(body) < 2:
            continue
        headers = body[0]
        data = body[1:]
        for ri, r in enumerate(data, 1):
            for ci, c in enumerate(r):
                if c == "":
                    h = headers[ci] if ci < len(headers) else ci + 1
                    problemes.append(lib.t("tables.p.cellule_vide", la,
                                           n=ti, ligne=ri, colonne=h))
        for ci, h in enumerate(headers):
            col = [r[ci] for r in data if ci < len(r)]
            num = [v for v in col if NUM.fullmatch(v.replace(' ', ''))]
            if num and len(num) >= max(1, len(col) // 2) and not UNITE.search(h):
                problemes.append(lib.t("tables.p.colonne_sans_unite", la,
                                       n=ti, colonne=h))
        for ci in range(len(headers)):
            for r in data:
                if r and re.match(r'\s*total\b', r[0].lower()) and ci < len(r) and NUM.fullmatch(r[ci].replace(' ', '')):
                    comps = [float(x[ci].replace(',', '.').replace(' ', '')) for x in data
                             if x is not r and ci < len(x) and NUM.fullmatch(x[ci].replace(' ', ''))]
                    tot = float(r[ci].replace(',', '.').replace(' ', ''))
                    if comps and abs(sum(comps) - tot) > 0.01:
                        h = headers[ci] if ci < len(headers) else ci + 1
                        problemes.append(lib.t(
                            "tables.p.total_incoherent", la, n=ti, colonne=h,
                            total=tot, somme=round(sum(comps), 2)))
    return {"tables": len(tables), "problemes": problemes}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generation et audit de tableaux.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen")
    g.add_argument("data")
    g.add_argument("--caption")
    g.add_argument("--source")
    g.add_argument("--out")
    g.add_argument("--langue-affichage", choices=["fr", "en"], default=None,
                   help="langue des messages de la commande. Le tableau "
                        "produit, lui, est du contenu de document et ne "
                        "change pas de langue")
    au = sub.add_parser("audit")
    au.add_argument("fichier")
    au.add_argument("--format", choices=["text", "json"], default="text")
    au.add_argument("--langue-affichage", choices=["fr", "en"], default=None,
                    help="langue des libelles du rapport texte. Sans "
                         "l'option : la langue du document (pragme "
                         "lint-style:langue), sinon fr. La sortie JSON reste "
                         "francaise quoi qu'il arrive")
    a = ap.parse_args(argv)
    lib = _lib()
    if a.cmd == "gen":
        md = generer(a.data, a.caption, a.source)
        if a.out:
            open(a.out, "w", encoding="utf-8").write(md)
            print(lib.t("tables.ecrit",
                        lib.resoudre_affichage(a.langue_affichage),
                        chemin=a.out))
        else:
            print(md)
        return 0
    texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    if a.format == "json":
        # Le JSON ne se traduit pas : les evals et le jeu d'or le lisent.
        d = auditer(texte)
        print(json.dumps(d, ensure_ascii=False, indent=2))
        return 1 if d["problemes"] else 0
    la = lib.resoudre_affichage(a.langue_affichage,
                                _lint().resoudre_langue(texte))
    d = auditer(texte, la)
    print(lib.t("tables.titre", la, tables=d["tables"]))
    if not d["problemes"]:
        print("  " + lib.t("tables.aucun_probleme", la))
    for p in d["problemes"]:
        print(f"  - {p}")
    return 1 if d["problemes"] else 0


if __name__ == "__main__":
    sys.exit(main())
