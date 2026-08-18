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
                                                    [--langue-affichage fr|en]
Module importable : analyser(plan, texte) -> dict ;
rapport_texte(d, langue_affichage=None) -> str. L'analyse ne connait aucune
langue : elle apparie des titres, quels qu'ils soient. La sortie JSON ne
porte que des donnees, elle ne change pas avec la langue d'affichage.
"""
import argparse
import importlib.util
import json
import os
import re
import sys
from difflib import SequenceMatcher

_LIB = None


def _lib():
    """Charge libelles.py par son chemin, une seule fois : le module se lit
    par chemin, aucun sys.path n'est garanti."""
    global _LIB
    if _LIB is None:
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "libelles.py")
        spec = importlib.util.spec_from_file_location("scriptorium_libelles",
                                                      chemin)
        _LIB = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_LIB)
    return _LIB


def _langue_du_texte(texte):
    """Langue du document, par delegation a lint-style.py. Elle ne sert qu'a
    choisir la langue d'affichage par defaut. Si le linter n'est pas la, le
    francais fait office de defaut plutot qu'une erreur."""
    try:
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "lint-style.py")
        spec = importlib.util.spec_from_file_location("lint_style", chemin)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.resoudre_langue(texte)
    except Exception:
        return None


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


def rapport_texte(d, langue_affichage=None):
    """Rendu texte. Les titres de section viennent du plan et du document :
    ils sont repris tels quels, jamais traduits."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    lignes = [lib.t("plan.titre", la, couverture=d["couverture_pct"])]
    if d["sections_manquantes"]:
        lignes.append("  " + lib.t("plan.manquantes", la,
                                   sections=d["sections_manquantes"]))
    if d["sections_hors_plan"]:
        lignes.append("  " + lib.t("plan.hors_plan", la,
                                   sections=d["sections_hors_plan"]))
    if not d["sections_manquantes"] and not d["sections_hors_plan"]:
        lignes.append("  " + lib.t("plan.conforme", la))
    return "\n".join(lignes)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Conformite au plan.")
    ap.add_argument("plan")
    ap.add_argument("document")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--langue-affichage", choices=["fr", "en"], default=None,
                    help="langue des libelles du rapport texte. Sans "
                         "l'option : la langue du document (pragme "
                         "lint-style:langue), sinon fr. La sortie JSON reste "
                         "francaise quoi qu'il arrive")
    a = ap.parse_args(argv)
    lib = _lib()
    plan = json.load(open(a.plan, encoding="utf-8"))
    texte = open(a.document, encoding="utf-8").read()
    d = analyser(plan, texte)
    if a.format == "json":
        # Le JSON ne se traduit pas : les evals et le jeu d'or le lisent.
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print(rapport_texte(d, lib.resoudre_affichage(
            a.langue_affichage, _langue_du_texte(texte))))
    return 1 if d["sections_manquantes"] else 0


if __name__ == "__main__":
    sys.exit(main())
