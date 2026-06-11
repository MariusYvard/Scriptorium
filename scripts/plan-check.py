#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Controle de conformite au plan pour Scriptorium.

Confronte un plan (plan.json produit au cadrage) au document : chaque section
prevue existe-t-elle, le texte a-t-il derive (sections hors plan), quelle est
la couverture. La boucle cadrage vers redaction devient verifiable.

plan.json : {"genre": "...", "problematique": "...",
             "sections": ["Introduction", "Methode", ...]}
  ou sections = [{"titre": "...", "message": "..."}]

Usage : python3 plan-check.py PLAN.json DOCUMENT.md [--format text|json]
Module importable : analyser(plan, texte) -> dict.
"""
import argparse
import json
import re
import sys
from difflib import SequenceMatcher

HEAD = re.compile(r'(?m)^#{1,6}\s+(.*)$')


def _norm(s):
    return re.sub(r'[^a-z0-9àâäéèêëîïôöùûüç ]', '', s.lower()).strip()


def _titres_plan(plan):
    secs = plan.get("sections", [])
    out = []
    for s in secs:
        out.append(s["titre"] if isinstance(s, dict) else s)
    return out


def _match(a, b):
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return False
    if na in nb or nb in na:
        return True
    return SequenceMatcher(None, na, nb).ratio() > 0.8


def analyser(plan, texte):
    prevues = _titres_plan(plan)
    titres_doc = [m.group(1).strip() for m in HEAD.finditer(texte)]
    presentes, manquantes = [], []
    for p in prevues:
        if any(_match(p, h) for h in titres_doc):
            presentes.append(p)
        else:
            manquantes.append(p)
    derive = [h for h in titres_doc if not any(_match(p, h) for p in prevues)]
    couverture = round(100 * len(presentes) / len(prevues), 1) if prevues else 100.0
    return {
        "sections_prevues": len(prevues),
        "sections_presentes": presentes,
        "sections_manquantes": manquantes,
        "sections_hors_plan": derive,
        "couverture_pct": couverture,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Conformite au plan.")
    ap.add_argument("plan")
    ap.add_argument("document")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    a = ap.parse_args(argv)
    plan = json.load(open(a.plan, encoding="utf-8"))
    texte = open(a.document, encoding="utf-8").read()
    d = analyser(plan, texte)
    if a.format == "json":
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print(f"Conformite au plan : couverture {d['couverture_pct']}%")
        if d["sections_manquantes"]:
            print(f"  Sections prevues absentes : {d['sections_manquantes']}")
        if d["sections_hors_plan"]:
            print(f"  Sections hors plan (derive) : {d['sections_hors_plan']}")
        if not d["sections_manquantes"] and not d["sections_hors_plan"]:
            print("  Document conforme au plan.")
    return 1 if d["sections_manquantes"] else 0


if __name__ == "__main__":
    sys.exit(main())
