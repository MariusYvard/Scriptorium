#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generation et audit de tableaux pour Scriptorium.

Genere un tableau Markdown autonome a partir d'un CSV ou d'un JSON (en-tetes,
unites, source) et audite les tableaux Markdown d'un document : cellules vides,
colonne numerique sans unite dans l'en-tete, ligne Total incoherente. Les
tableaux sont l'autre moitie du principe « une figure est du contenu ».

Usage :
    python3 tables.py gen DATA.csv|.json [--caption "..."] [--source "..."]
    python3 tables.py audit DOCUMENT.md [--format text|json]
Module importable : generer(...) ; auditer(texte) -> dict.
"""
import argparse
import csv
import json
import re
import sys

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


def auditer(texte):
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
                    problemes.append(f"Tableau {ti} : cellule vide ligne {ri}, colonne « {h} ».")
        for ci, h in enumerate(headers):
            col = [r[ci] for r in data if ci < len(r)]
            num = [v for v in col if NUM.fullmatch(v.replace(' ', ''))]
            if num and len(num) >= max(1, len(col) // 2) and not UNITE.search(h):
                problemes.append(f"Tableau {ti} : colonne numerique « {h} » sans unite dans l'en-tete.")
        for ci in range(len(headers)):
            for r in data:
                if r and re.match(r'\s*total\b', r[0].lower()) and ci < len(r) and NUM.fullmatch(r[ci].replace(' ', '')):
                    comps = [float(x[ci].replace(',', '.').replace(' ', '')) for x in data
                             if x is not r and ci < len(x) and NUM.fullmatch(x[ci].replace(' ', ''))]
                    tot = float(r[ci].replace(',', '.').replace(' ', ''))
                    if comps and abs(sum(comps) - tot) > 0.01:
                        h = headers[ci] if ci < len(headers) else ci + 1
                        problemes.append(f"Tableau {ti} : Total colonne « {h} » = {tot}, somme = {round(sum(comps), 2)}.")
    return {"tables": len(tables), "problemes": problemes}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generation et audit de tableaux.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gen")
    g.add_argument("data")
    g.add_argument("--caption")
    g.add_argument("--source")
    g.add_argument("--out")
    au = sub.add_parser("audit")
    au.add_argument("fichier")
    au.add_argument("--format", choices=["text", "json"], default="text")
    a = ap.parse_args(argv)
    if a.cmd == "gen":
        md = generer(a.data, a.caption, a.source)
        if a.out:
            open(a.out, "w", encoding="utf-8").write(md)
            print(f"Tableau ecrit : {a.out}")
        else:
            print(md)
        return 0
    texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    d = auditer(texte)
    if a.format == "json":
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print(f"Audit de tableaux ({d['tables']} table(s))")
        if not d["problemes"]:
            print("  Aucun probleme de tableau.")
        for p in d["problemes"]:
            print(f"  - {p}")
    return 1 if d["problemes"] else 0


if __name__ == "__main__":
    sys.exit(main())
