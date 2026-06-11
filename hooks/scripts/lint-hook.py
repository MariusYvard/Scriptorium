#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hook PostToolUse : applique le linter de style maison apres chaque
ecriture de document.

Lit l'entree JSON du hook sur stdin, ne traite que les fichiers .md et .txt
hors du plugin lui-meme, lance le linter deterministe et bloque la finalisation
si un constat critique subsiste. Toute erreur est silencieuse : le hook ne
casse jamais le flux de travail de l'utilisateur.
"""
import importlib.util
import json
import os
import sys


def charger_linter():
    ici = os.path.dirname(os.path.abspath(__file__))
    chemin = os.path.join(ici, "..", "..", "scripts", "lint-style.py")
    spec = importlib.util.spec_from_file_location("lint_style", chemin)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    try:
        entree = json.load(sys.stdin)
    except Exception:
        return 0
    ti = entree.get("tool_input", {}) or {}
    fp = ti.get("file_path") or ti.get("path") or ""
    if not fp or not fp.lower().endswith((".md", ".txt")):
        return 0
    norm = fp.replace("\\", "/")
    # ne pas analyser les fichiers internes du plugin (ils citent les interdits)
    if "/scriptorium/" in norm and any(
        seg in norm for seg in ("/skills/", "/scripts/", "/agents/", "/hooks/", "/evals/", "/docs/")):
        return 0
    try:
        texte = open(fp, encoding="utf-8").read()
    except OSError:
        return 0
    try:
        linter = charger_linter()
        constats = linter.lint_text(texte, fp)
    except Exception:
        return 0
    crit = [c for c in constats if c.get("severite") == "critique"]
    if not crit:
        return 0
    apercu = "; ".join(
        f"L{c['ligne']} {c['regle']} ({c['trouve']})" for c in crit[:10])
    raison = (
        f"Le document {os.path.basename(fp)} contient {len(crit)} ecart(s) "
        f"critique(s) au style maison : {apercu}. "
        "Corriger avant de finaliser. Detail : "
        "python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lint-style.py \"" + fp + "\"")
    print(json.dumps({"decision": "block", "reason": raison}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
