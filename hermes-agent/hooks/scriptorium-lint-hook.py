#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Hook Hermes pre_verify : portage du hook Claude Code PostToolUse de
Scriptorium (scriptorium/hooks/hooks.json + hooks/scripts/lint-hook.py).

Sous Claude Code, le hook original tourne apres chaque Write|Edit et bloque
la FINALISATION du tour (pas l'ecriture elle-meme) si le fichier .md/.txt
ecrit contient un ecart critique au style maison. Sous Hermes il n'existe pas
de hook "apres write_file, avant que le tour se termine" avec pouvoir de
blocage : post_tool_call existe mais est un simple observateur (retour
ignore). pre_verify est le vrai equivalent : il se declenche une fois par
tour ayant modifie du code/texte, juste avant que l'agent conclue, et peut
renvoyer {"decision":"block","reason":...} pour le faire continuer au lieu
de s'arreter -- exactement le comportement cible.

Limite assumee : pre_verify ne fournit pas la liste des fichiers modifies
avant l'appel (elle vit dans changed_paths, fourni par Hermes), donc ce hook
relit chaque chemin de changed_paths qui finit en .md/.txt, au lieu de ne
lire que le fichier du dernier write_file comme le fait l'original.
Consequence pratique : un tour qui touche plusieurs documents les lint tous
d'un coup plutot qu'un par un, ce qui est strictement plus complet.

Se declenche une seule fois par tour (idempotent via `attempt`), comme
documente pour pre_verify.

Erreurs silencieuses : ce hook ne casse jamais le flux de travail.

Installation : ce fichier source vit dans le repo Scriptorium
(hermes-agent/hooks/scriptorium-lint-hook.py) et est copie tel quel par
update-hermes-skills.sh vers ~/.hermes/agent-hooks/ (ou l'equivalent
profile). Le chemin du checkout Scriptorium n'est jamais code en dur ici :
il se resout depuis la variable d'environnement SCRIPTORIUM_ROOT (ecrite par
le script d'installation dans le wrapper cron) ou, a defaut, depuis la
position du fichier lui-meme si jamais il tourne directement depuis le repo.
"""
import importlib.util
import json
import os
import sys


def resoudre_scriptorium_root() -> str:
    env = os.environ.get("SCRIPTORIUM_ROOT")
    if env:
        return env
    # Repli : si ce fichier tourne directement depuis le repo
    # (hermes-agent/hooks/ -> ../../scriptorium), utile en test local.
    ici = os.path.dirname(os.path.abspath(__file__))
    repli = os.path.normpath(os.path.join(ici, "..", "..", "scriptorium"))
    return repli


SCRIPTORIUM_ROOT = resoudre_scriptorium_root()


def charger_linter():
    if not SCRIPTORIUM_ROOT:
        return None
    chemin = os.path.join(SCRIPTORIUM_ROOT, "scripts", "lint-style.py")
    if not os.path.isfile(chemin):
        return None
    spec = importlib.util.spec_from_file_location("lint_style", chemin)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def concerne(fp: str) -> bool:
    if not fp or not fp.lower().endswith((".md", ".txt")):
        return False
    norm = fp.replace("\\", "/")
    # ne pas analyser les fichiers internes du plugin (ils citent les interdits)
    if "/scriptorium/" in norm and any(
        seg in norm for seg in ("/skills/", "/scripts/", "/agents/", "/hooks/", "/evals/", "/docs/")
    ):
        return False
    return True


def main():
    try:
        entree = json.load(sys.stdin)
    except Exception:
        print("{}")
        return 0

    extra = entree.get("extra") or {}
    # attempt > 0 : ce tour a deja ete relance une fois par ce hook (ou un
    # autre pre_verify) -- ne pas boucler indefiniment sur le meme constat.
    if extra.get("attempt"):
        print("{}")
        return 0

    changed_paths = extra.get("changed_paths") or []
    cibles = [p for p in changed_paths if concerne(p)]
    if not cibles:
        print("{}")
        return 0

    linter = charger_linter()
    if linter is None:
        print("{}")
        return 0

    rapports = []
    for fp in cibles:
        try:
            with open(fp, encoding="utf-8") as f:
                texte = f.read()
        except OSError:
            continue
        try:
            constats = linter.lint_text(texte, fp)
        except Exception:
            continue
        crit = [c for c in constats if c.get("severite") == "critique"]
        if crit:
            apercu = "; ".join(f"L{c['ligne']} {c['regle']} ({c['trouve']})" for c in crit[:6])
            rapports.append(f"{os.path.basename(fp)} ({len(crit)} ecart(s)) : {apercu}")

    if not rapports:
        print("{}")
        return 0

    raison = (
        "Style maison Scriptorium : ecart(s) critique(s) avant finalisation -- "
        + " | ".join(rapports)
        + f". Detail : python3 \"{SCRIPTORIUM_ROOT}/scripts/lint-style.py\" FICHIER"
    )
    print(json.dumps({"decision": "block", "reason": raison}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
