#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scorecard deterministe d'un document pour Scriptorium.

Agrege les sorties des scripts en une note de 0 a 100 sur cinq axes, avec des
penalites fixes et le calcul montre. Le modele emet les verdicts qualitatifs,
cette formule donne le nombre, reproductible d'un passage a l'autre.

Axes (20 points chacun) : Style, Sources, Tracabilite, Terminologie et nombres,
Lisibilite. Verdict : >=85 Pret, 70-84 A reviser, <70 A refondre. Ce verdict a
trois valeurs sert de porte de qualite generale, inchange par ce lot.

En plus du verdict a trois valeurs, le rapport porte une decision editoriale a
quatre valeurs (accepter, revision mineure, revision majeure, refus) plombee
par un plancher par axe (--plancher N, defaut 8 sur 20) : un axe sous ce seuil
plafonne la decision independamment du total, avec un sous-type de refus
propose en commentaire (jamais un verdict ferme, un signal mecanique ne peut
pas a lui seul distinguer hors perimetre de premature). Cette decision sert la
revue par consensus et la lettre de decision (voir references/consensus.md et
references/lettre-decision.md).

Usage :
    python3 scorecard.py FICHIER [--format text|json] [--plancher N]
    python3 scorecard.py --trajectoire RAPPORT_A.json RAPPORT_B.json [--format text|json]

Module importable : evaluer(texte, plancher=8) -> dict, trajectoire(a, b) -> dict.
"""
import argparse
import importlib.util
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))

PLANCHER_DEFAUT = 8  # sur 20 par axe. Sous ce seuil l'axe est repute effondre
                     # et plafonne la decision editoriale, quel que soit le total.


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


def _decision_editoriale(axes, total, plancher):
    """Mappe le score sur une decision a quatre valeurs (accepter, revision
    mineure, revision majeure, refus), plafonnee par le pire axe si un axe
    tombe sous le plancher : une seule dimension effondree peut bloquer malgre
    un bon score global. Le sous-type de refus indique en commentaire est une
    proposition, jamais un verdict ferme : seuls les signaux mesurables (total,
    axe effondre) sont mecaniques, le reste (hors perimetre, premature) exige
    une lecture humaine et n'est jamais deduit du score seul."""
    effondres = sorted((nom, a["score"]) for nom, a in axes.items() if a["score"] < plancher)

    if total >= 85:
        decision = "accepter"
    elif total >= 70:
        decision = "revision mineure"
    elif total >= 55:
        decision = "revision majeure"
    else:
        decision = "refus"

    rang = {"accepter": 0, "revision mineure": 1, "revision majeure": 2, "refus": 3}
    if effondres:
        pire = min(score for _, score in effondres)
        plafond = "refus" if pire <= plancher // 2 else "revision majeure"
        if rang[plafond] > rang[decision]:
            decision = plafond

    commentaire = None
    if decision == "refus":
        if effondres:
            noms = ", ".join(nom for nom, _ in effondres)
            commentaire = (f"sous-type propose : a retravailler en profondeur "
                            f"(axe effondre sous plancher/2 : {noms})")
        else:
            commentaire = (f"sous-type propose : defaut fondamental (score global {total} "
                            "tres bas) ; a confirmer en lecture humaine, hors perimetre et "
                            "premature ne se deduisent pas du score seul")

    return {
        "decision": decision,
        "plancher": plancher,
        "axes_effondres": [nom for nom, _ in effondres],
        "commentaire_sous_type": commentaire,
    }


def evaluer(texte, plancher=PLANCHER_DEFAUT):
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

    axes_out = {k: {"score": s, "deductions": d} for k, (s, d) in axes.items()}
    return {
        "axes": axes_out,
        "total": total,
        "verdict": verdict,
        "decision_editoriale": _decision_editoriale(axes_out, total, plancher),
    }


def trajectoire(a, b):
    """Delta par axe entre deux rapports JSON produits par --format json
    (revue puis re-revue). Regression : delta sous -3 sur un axe. Ne compare
    que les axes presents dans les deux rapports, un axe absent d'un cote est
    signale a part plutot que suppose a zero."""
    axes_a, axes_b = a.get("axes", {}), b.get("axes", {})
    communs = [n for n in axes_a if n in axes_b]
    ignores = sorted(set(axes_a) ^ set(axes_b))

    deltas = []
    for n in communs:
        sa, sb = axes_a[n]["score"], axes_b[n]["score"]
        d = sb - sa
        deltas.append({"axe": n, "avant": sa, "apres": sb, "delta": d, "regression": d < -3})

    total_a, total_b = a.get("total", 0), b.get("total", 0)
    return {
        "deltas": deltas,
        "axes_ignores": ignores,
        "total_avant": total_a,
        "total_apres": total_b,
        "delta_total": total_b - total_a,
        "regressions": [d["axe"] for d in deltas if d["regression"]],
        "verdict_avant": a.get("verdict"),
        "verdict_apres": b.get("verdict"),
    }


def rapport_texte(r):
    out = [f"Scorecard : {r['total']}/100 — verdict {r['verdict']}", ""]
    for nom, a in r["axes"].items():
        out.append(f"  {nom:26} {a['score']:>2}/20")
        for d in a["deductions"]:
            out.append(f"      {d}")
    out.append("")
    out.append("  Calcul : chaque axe part de 20, penalites fixes plafonnees, somme sur 100.")
    de = r["decision_editoriale"]
    out.append("")
    out.append(f"  Decision editoriale (plancher {de['plancher']}/20 par axe) : {de['decision']}")
    if de["axes_effondres"]:
        out.append(f"      axe(s) sous le plancher : {', '.join(de['axes_effondres'])}")
    if de["commentaire_sous_type"]:
        out.append(f"      {de['commentaire_sous_type']}")
    return "\n".join(out)


def rapport_trajectoire_texte(t):
    out = [f"Trajectoire : {t['total_avant']}/100 vers {t['total_apres']}/100 "
           f"(delta total {t['delta_total']:+d})", ""]
    for d in t["deltas"]:
        marque = "  [REGRESSION]" if d["regression"] else ""
        out.append(f"  {d['axe']:26} {d['avant']:>2} -> {d['apres']:>2} (delta {d['delta']:+d}){marque}")
    if t["axes_ignores"]:
        out.append("")
        out.append(f"  Axes ignores (absents d'un rapport) : {', '.join(t['axes_ignores'])}")
    out.append("")
    if t["regressions"]:
        out.append(f"  Point de controle : regression de plus de 3 points sur {', '.join(t['regressions'])}.")
        out.append("  Trois options : accepter le compromis, reviser cible sur l'axe regresse,")
        out.append("  ou restaurer la version anterieure de la section concernee.")
    else:
        out.append("  Aucune regression de plus de 3 points : trajectoire normale.")
    out.append(f"  Verdict : {t['verdict_avant']} -> {t['verdict_apres']}")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Scorecard deterministe.")
    ap.add_argument("fichier", nargs="?", default=None)
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--plancher", type=int, default=PLANCHER_DEFAUT,
                     help=f"seuil par axe sur 20 (defaut {PLANCHER_DEFAUT})")
    ap.add_argument("--trajectoire", nargs=2, metavar=("RAPPORT_A", "RAPPORT_B"),
                     help="compare deux rapports JSON (sorties de --format json)")
    a = ap.parse_args(argv)

    if a.trajectoire:
        chemin_a, chemin_b = a.trajectoire
        rapport_a = json.load(open(chemin_a, encoding="utf-8"))
        rapport_b = json.load(open(chemin_b, encoding="utf-8"))
        t = trajectoire(rapport_a, rapport_b)
        print(json.dumps(t, ensure_ascii=False, indent=2) if a.format == "json" else rapport_trajectoire_texte(t))
        return 0

    if not a.fichier:
        print("Erreur : fichier requis (sauf en mode --trajectoire).", file=sys.stderr)
        return 2

    texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    r = evaluer(texte, plancher=a.plancher)
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.format == "json" else rapport_texte(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
