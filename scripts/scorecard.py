#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scorecard deterministe d'un document pour Scriptorium.

Agrege les sorties des scripts en une note de 0 a 100 sur cinq axes, avec des
penalites fixes et le calcul montre. Le modele emet les verdicts qualitatifs,
cette formule donne le nombre, reproductible d'un passage a l'autre.

Axes (20 points chacun) : Style, Sources, Tracabilite, Terminologie et nombres,
Lisibilite. Verdict : >=85 Pret, 70-84 A reviser, <70 A refondre.

Usage : python3 scorecard.py FICHIER [--format text|json]
"""
import argparse
import importlib.util
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))


def _mod(fichier, nom):
    spec = importlib.util.spec_from_file_location(nom, os.path.join(ICI, fichier))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


lint = _mod("lint-style.py", "lint_style")
read = _mod("readability.py", "readability")
vsrc = _mod("verify-sources.py", "verify_sources")
trac = _mod("traceability.py", "traceability")
term = _mod("terminology.py", "terminology")
nums = _mod("numbers.py", "numbers")
aifp = _mod("ai-fingerprint.py", "ai_fingerprint")
coh = _mod("coherence.py", "coherence")


def _axe(depart, regles):
    """regles = liste de (compte, penalite_unitaire, plafond, libelle). Retourne
    (score, deductions). plafond = deduction maximale pour cette regle."""
    score = depart
    deductions = []
    for compte, pen, plafond, libelle in regles:
        if compte > 0:
            d = min(compte * pen, plafond)
            score -= d
            deductions.append(f"-{d} {libelle} (x{compte})")
    return max(0, score), deductions


def evaluer(texte):
    axes = {}

    c = lint.lint_text(texte)
    crit = sum(1 for x in c if x["severite"] == "critique")
    maj = sum(1 for x in c if x["severite"] == "majeur")
    mino = sum(1 for x in c if x["severite"] == "mineur")
    nsig = len(aifp.analyser(texte)["signaux"])
    axes["Style"] = _axe(20, [(crit, 7, 20, "ecart critique de style"),
                              (maj, 3, 9, "ecart majeur"),
                              (mino, 1, 4, "ecart mineur"),
                              (nsig, 2, 6, "tic d'ecriture IA")])

    v = vsrc.analyser(texte)
    axes["Sources"] = _axe(20, [(len(v["urls_a_nettoyer"]), 4, 8, "URL a nettoyer"),
                                (len(v["doublons"]), 4, 8, "source en double"),
                                (len(v["dois_invalides"]), 3, 6, "DOI douteux")])

    t = trac.analyser(texte)
    axes["Tracabilite"] = _axe(20, [
        (len(t["citations_pendantes"]), 5, 10, "citation pendante"),
        (len(t["references_orphelines"]), 2, 6, "reference orpheline"),
        (len(t["figures_appelees_non_definies"]) + len(t["tableaux_appeles_non_definis"]), 3, 6, "appel sans definition"),
        (len(t["figures_definies_non_appelees"]) + len(t["tableaux_definis_non_appeles"]), 2, 4, "objet jamais appele"),
        (len(coh.analyser(texte)["paragraphes_dupliques"]), 4, 8, "paragraphe duplique")])

    te = term.analyser(texte)
    nu = nums.analyser(texte)
    axes["Terminologie et nombres"] = _axe(20, [
        (len(te["sigles_non_definis"]), 4, 8, "sigle non defini"),
        (len(te["sigles_avant_definition"]), 2, 4, "sigle avant definition"),
        (len(te["variantes_orthographiques"]), 2, 4, "variante orthographique"),
        (len(nu["pourcentages_impossibles"]), 6, 12, "pourcentage impossible"),
        (len(nu["partitions_incoherentes"]), 3, 6, "partition incoherente"),
        (1 if nu["separateur_decimal_mixte"] else 0, 2, 2, "separateur decimal mixte")])

    m = read.mesurer(texte)
    reg = []
    if m["mots"] >= 80:
        reg.append((1 if m["longueur_phrase_ecart_type"] < 5 else 0, 5, 5, "rythme monotone"))
        reg.append((1 if m["longueur_phrase_moyenne"] > 28 else 0, 4, 4, "phrases trop longues"))
        reg.append((1 if (m["indice_lix"] > 56 or m["indice_lix"] < 30) else 0, 5, 5, "LIX hors bande"))
        reg.append((1 if m["taux_passif_approx_pct"] > 25 else 0, 4, 4, "trop de passif"))
        reg.append((1 if m["densite_lexicale"] < 0.35 else 0, 3, 3, "densite lexicale faible"))
    axes["Lisibilite"] = _axe(20, reg)

    total = sum(s for s, _ in axes.values())
    if total >= 85:
        verdict = "Pret"
    elif total >= 70:
        verdict = "A reviser"
    else:
        verdict = "A refondre"
    return {
        "axes": {k: {"score": s, "deductions": d} for k, (s, d) in axes.items()},
        "total": total,
        "verdict": verdict,
    }


def rapport_texte(r):
    out = [f"Scorecard : {r['total']}/100 — verdict {r['verdict']}", ""]
    for nom, a in r["axes"].items():
        out.append(f"  {nom:26} {a['score']:>2}/20")
        for d in a["deductions"]:
            out.append(f"      {d}")
    out.append("")
    out.append("  Calcul : chaque axe part de 20, penalites fixes plafonnees, somme sur 100.")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Scorecard deterministe.")
    ap.add_argument("fichier")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    a = ap.parse_args(argv)
    texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    r = evaluer(texte)
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.format == "json" else rapport_texte(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
