#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit consolide d'un document pour Scriptorium.

Lance le scorecard, le detecteur d'empreinte IA, le controle de coherence et
l'audit de tableaux sur un fichier texte, et produit un rapport unifie.
Pour un PDF ou un Word, la competence auditer-existant extrait d'abord le
texte, puis appelle ce script.

Usage : python3 audit-doc.py FICHIER.md [--format text|json]
                              [--langue fr|en|auto] [--langue-affichage fr|en]

Trois des quatre mesures consolidees ici (empreinte IA, coherence, tableaux)
sont produites par des scripts qui ne sont pas encore cables sur la couche de
libelles : leurs constats restent francais, et le rapport le DECLARE au lieu
de laisser croire a un rapport anglais complet.
"""
import argparse
import importlib.util
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))


def _mod(f, n):
    spec = importlib.util.spec_from_file_location(n, os.path.join(ICI, f))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


lib = _mod("libelles.py", "scriptorium_libelles")
lint = _mod("lint-style.py", "lint_style")
score = _mod("scorecard.py", "scorecard")
aifp = _mod("ai-fingerprint.py", "ai_fingerprint")
coh = _mod("coherence.py", "coherence")
tab = _mod("tables.py", "tables")

# Scripts dont les constats arrivent ici sans passer par la couche de
# libelles. La liste sert au message de declaration, elle se vide a mesure que
# les scripts sont cables.
SECTIONS_NON_CABLEES = ("ai-fingerprint.py", "coherence.py", "tables.py")


def auditer(texte, langue=None, langue_affichage=None):
    """Audit consolide.

    La langue de mesure se resout UNE fois et se transmet a chaque mesure qui
    en depend. Avant, seul le scorecard la resolvait : sur un document
    anglais, l'empreinte IA et la coherence etaient encore cherchees avec les
    motifs francais, et rendaient zero signal sans que rien ne le dise. Sur un
    document francais, la resolution donne fr et rien ne change.
    """
    langue = lint.resoudre_langue(texte, langue)
    return {
        "scorecard": score.evaluer(texte, langue=langue,
                                   langue_affichage=langue_affichage),
        "empreinte_ia": aifp.analyser(texte, langue=langue)["signaux"],
        "coherence": coh.problemes(coh.analyser(texte, langue=langue)),
        "tableaux": tab.auditer(texte)["problemes"],
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Audit consolide.")
    ap.add_argument("fichier")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--langue", choices=["fr", "en", "auto"], default=None,
                    help="langue de mesure, meme option que lint-style.py. "
                         "Sans l'option : le pragme lint-style:langue du "
                         "document, sinon fr")
    ap.add_argument("--langue-affichage", choices=["fr", "en"], default=None,
                    help="langue des libelles du rapport texte. Sans "
                         "l'option : la langue de mesure retenue. La sortie "
                         "JSON reste francaise quoi qu'il arrive")
    a = ap.parse_args(argv)
    texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    if a.format == "json":
        # Le JSON ne se traduit pas : les evals et le jeu d'or le lisent.
        print(json.dumps(auditer(texte, a.langue), ensure_ascii=False,
                         indent=2))
        return 0
    la = lib.resoudre_affichage(a.langue_affichage,
                                lint.resoudre_langue(texte, a.langue))
    d = auditer(texte, a.langue, la)
    sc = d["scorecard"]
    print(lib.t("audit.entete", la, total=sc["total"],
                verdict=lib.valeur("scorecard.verdict", sc["verdict"], la))
          + "\n")
    for nom, ax in sc["axes"].items():
        print("  %-26s %2s/20"
              % (lib.valeur("scorecard.axe", nom, la), ax["score"]))
    sections = (
        ("audit.empreinte", "audit.aucun_signal", d["empreinte_ia"]),
        ("audit.coherence", "audit.aucune_redite", d["coherence"]),
        ("audit.tableaux", "audit.aucun_probleme", d["tableaux"]),
    )
    reste_du_francais = False
    for rang, (cle_section, cle_vide, donnees) in enumerate(sections):
        print(("\n" if rang == 0 else "") + lib.t(cle_section, la))
        print("  " + (lib.t(cle_vide, la) if not donnees
                      else "; ".join(donnees)))
        reste_du_francais = reste_du_francais or bool(donnees)
    if reste_du_francais and la != lib.LANGUE_DEFAUT:
        print("  " + lib.t("audit.non_cable", la,
                           scripts=", ".join(SECTIONS_NON_CABLEES)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
