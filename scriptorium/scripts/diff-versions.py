#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Journal des ecarts entre deux versions d'un document (Markdown).

Compare deux versions et produit un changelog : sections ajoutees, supprimees,
modifiees, avec le compte de mots ajoutes et supprimes. Outil de revision
suivie, deterministe, sans dependance.

Usage : python3 diff-versions.py ANCIEN.md NOUVEAU.md [--format text|json]
                                                      [--langue-affichage fr|en]
Module importable : comparer(ancien, nouveau) -> dict ;
rapport_texte(d, langue_affichage=None) -> str. La comparaison ne connait
aucune langue : elle compte des mots et apparie des titres. La sortie JSON ne
porte que des donnees et des titres de section repris du document, elle ne
change pas avec la langue d'affichage.
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


HEAD = re.compile(r'(?m)^(#{1,6})\s+(.*)$')


def sections(texte):
    out = {}
    pts = [(m.start(), m.group(2).strip()) for m in HEAD.finditer(texte)]
    if not pts:
        return {"(document)": texte}
    for i, (pos, titre) in enumerate(pts):
        fin = pts[i + 1][0] if i + 1 < len(pts) else len(texte)
        corps = texte[pos:fin]
        corps = re.sub(r'^#{1,6}\s+.*\n?', '', corps, count=1)
        out[titre] = corps
    return out


def mots(t):
    return re.findall(r'\w+', t.lower())


def comparer(ancien, nouveau):
    sa, sn = sections(ancien), sections(nouveau)
    ajoutees = [t for t in sn if t not in sa]
    supprimees = [t for t in sa if t not in sn]
    modifiees = []
    for t in sn:
        if t in sa and sa[t].strip() != sn[t].strip():
            ma, mn = mots(sa[t]), mots(sn[t])
            sm = SequenceMatcher(None, ma, mn)
            ajout = sum((j2 - j1) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag in ("insert", "replace"))
            supp = sum((i2 - i1) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag in ("delete", "replace"))
            modifiees.append({"section": t, "mots_ajoutes": ajout, "mots_supprimes": supp})
    ga, gn = mots(ancien), mots(nouveau)
    sm = SequenceMatcher(None, ga, gn)
    return {
        "sections_ajoutees": ajoutees,
        "sections_supprimees": supprimees,
        "sections_modifiees": modifiees,
        "mots_ancien": len(ga),
        "mots_nouveau": len(gn),
        "similitude_globale": round(sm.ratio(), 3),
    }


def rapport_texte(d, langue_affichage=None):
    """Rendu texte. Les titres de section sont ceux du document, repris tels
    quels."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    lignes = [lib.t("diff.titre", la),
              "  " + lib.t("diff.mots", la, avant=d["mots_ancien"],
                           apres=d["mots_nouveau"],
                           similitude=d["similitude_globale"])]
    if d["sections_ajoutees"]:
        lignes.append("  " + lib.t("diff.ajoutees", la,
                                   sections=d["sections_ajoutees"]))
    if d["sections_supprimees"]:
        lignes.append("  " + lib.t("diff.supprimees", la,
                                   sections=d["sections_supprimees"]))
    for m in d["sections_modifiees"]:
        lignes.append("  " + lib.t("diff.modifiee", la, section=m["section"],
                                   ajoutes=m["mots_ajoutes"],
                                   supprimes=m["mots_supprimes"]))
    if not (d["sections_ajoutees"] or d["sections_supprimees"]
            or d["sections_modifiees"]):
        lignes.append("  " + lib.t("diff.aucun_ecart", la))
    return "\n".join(lignes)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Journal des ecarts entre versions.")
    ap.add_argument("ancien")
    ap.add_argument("nouveau")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--langue-affichage", choices=["fr", "en"], default=None,
                    help="langue des libelles du rapport texte. Sans "
                         "l'option : la langue de la nouvelle version (pragme "
                         "lint-style:langue), sinon fr. La sortie JSON reste "
                         "francaise quoi qu'il arrive")
    a = ap.parse_args(argv)
    lib = _lib()
    ancien = open(a.ancien, encoding="utf-8").read()
    nouveau = open(a.nouveau, encoding="utf-8").read()
    d = comparer(ancien, nouveau)
    if a.format == "json":
        # Le JSON ne se traduit pas : les evals et le jeu d'or le lisent.
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print(rapport_texte(d, lib.resoudre_affichage(
            a.langue_affichage, _langue_du_texte(nouveau))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
