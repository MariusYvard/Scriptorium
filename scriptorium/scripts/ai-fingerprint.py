#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Detecteur d'empreinte IA pour Scriptorium.

Mesure les marqueurs statistiques d'un texte genere : faible variabilite de
longueur de phrase, ouvertures de phrases repetitives, cadence ternaire
systematique, connecteurs suremployes, bigrammes repetes, amplification
contrastive (non seulement ... mais). Tes directives proscrivent ces tics,
ce script les rend mesurables.

Portee de langue. Quatre des six signaux lisent des motifs de langue :
connecteurs, cadence ternaire (qui exige « et » ou « ou »), amplification
contrastive, et la liste de mots outils qui filtre les bigrammes. Sur un
texte anglais analyse avec les motifs francais, ces quatre signaux rendent
zero, et la liste de mots outils vide fait compter « the », « of » et
« and » comme des mots pleins : le bigramme le plus repete devient un
bigramme de mots vides, faux positif systematique. Chaque jeu de motifs
existe donc par langue. Les deux signaux restants (ecart-type de longueur
de phrase, repetition de l'ouverture) ne lisent aucun mot et ne changent
pas. La structure de sortie est la meme dans les deux langues.

Ce que ce script ne mesure pas, et pourquoi. Le vocabulaire en exces mesure
sur les textes assistes par modele (delve, intricate, meticulous : Kobak et
al. 2025, Liang et al. 2024, liste dans skills/produire/references/
style-anglais.md) est deja porte par la regle « lexique-ia-en » de
lint-style.py. Le recopier ici le compterait deux fois dans l'axe Style du
scorecard, qui additionne les constats du linter et les signaux d'ici.

Usage : python3 ai-fingerprint.py FICHIER [--format text|json]
                                          [--langue fr|en|auto]
                                          [--langue-affichage fr|en]
Module importable : analyser(texte, langue=None, langue_affichage=None)
-> dict.
"""
import argparse
import json
import math
import os
import re
import sys
from collections import Counter

SENT = re.compile(r'[^.!?…]+[.!?…]+', re.S)
MOT = re.compile(r"\b[\wàâäéèêëîïôöùûüçœ'-]+\b", re.I)
TRIPLE = re.compile(r"\b[\wà-ÿœ]+,\s+[\wà-ÿœ]+\s+(?:et|ou)\s+[\wà-ÿœ]+\b", re.I)
AMPLI = re.compile(r"(?i)non seulement\b.{1,80}?\bmais\b|"
                   r"ne\s+\w+\s+pas seulement\b.{1,80}?\bmais\b|"
                   r"il ne s'agit pas seulement\b.{1,80}?\bmais\b")
CONNECTEURS = ["par ailleurs", "en effet", "de plus", "en outre", "notamment",
               "cependant", "néanmoins", "toutefois", "de surcroît", "en somme",
               "par conséquent", "ainsi", "en définitive"]
STOP = set("le la les un une de des du et ou a à en pour par sur dans que qui se "
           "ne pas plus est sont ce cette son sa ses leur au aux d l il elle on "
           "nous vous ils elles avec sans mais donc or ni car".split())

# --- Motifs anglais ---------------------------------------------------------
#
# Les connecteurs sont la transposition terme a terme de la liste francaise :
# c'est la meme grandeur qui est mesuree, la densite de marqueurs de discours
# par phrase, avec les marqueurs de l'autre langue. Ils ne viennent pas d'une
# etude de frequence, et le seuil de declenchement reste celui du francais.
CONNECTEURS_EN = ["moreover", "furthermore", "in addition", "additionally",
                  "however", "nevertheless", "nonetheless", "notably",
                  "importantly", "therefore", "consequently", "thus",
                  "overall", "in conclusion", "indeed"]
TRIPLE_EN = re.compile(r"\b[\w']+,\s+[\w']+\s+(?:and|or)\s+[\w']+\b", re.I)
AMPLI_EN = re.compile(r"(?i)not only\b.{1,80}?\bbut\b|"
                      r"\bis not (?:just|merely|simply)\b.{1,80}?\bbut\b|"
                      r"\bit is not (?:just|merely|simply) about\b.{1,80}?\bbut\b|"
                      r"\brather than (?:just|merely|simply)\b.{1,80}?\bit\b")

LANGUES = ("fr", "en")
LANGUE_DEFAUT = "fr"

_LINT = None


def _lint():
    """Charge lint-style.py par son chemin, une seule fois.

    Le nom du fichier porte un tiret, il n'est pas importable tel quel. La
    resolution de langue et la liste de mots outils anglais y sont definies
    et documentees : elles sont lues ici, jamais recopiees, sinon deux
    versions de la meme liste divergeraient sans que rien ne le signale.
    """
    global _LINT
    if _LINT is None:
        import importlib.util
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "lint-style.py")
        spec = importlib.util.spec_from_file_location("lint_style", chemin)
        _LINT = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_LINT)
    return _LINT


# Mots outils exclus des bigrammes, en plus de ceux que lint-style.py retient
# pour la detection de langue. Sa liste ecarte volontairement tout mot qui
# existe aussi en francais (a, on, or, as, but, son), ce qui la rend juste
# pour trancher une langue et incomplete pour filtrer des bigrammes. Le
# complement ne porte que des mots de trois lettres et plus : le filtre du
# script ecarte deja tout mot de deux lettres ou moins.
STOP_EN_COMPLEMENT = frozenset("""but our can may will would could should had
those more most other others between during after before under over only all
some many one two three when then thus here out about however therefore""".split())

_STOP_EN = None


def _stop_en():
    """Liste de mots outils anglais, calculee une fois."""
    global _STOP_EN
    if _STOP_EN is None:
        _STOP_EN = set(_lint().MOTS_OUTILS_EN) | set(STOP_EN_COMPLEMENT)
    return _STOP_EN


def resoudre_langue(texte, langue=None):
    """Tranche la langue d'analyse, par delegation a lint-style.py.

    Meme ordre de priorite que le linter : option explicite, puis auto, puis
    pragme du document, puis francais. Un code hors fr, en et auto est rendu
    tel quel ; les motifs retombent alors sur le francais par defaut, ce que
    _motifs declare.
    """
    if langue is not None and langue not in LANGUES and langue != "auto":
        return langue
    return _lint().resoudre_langue(texte, langue)


def _motifs(langue):
    """Jeu de motifs de la langue : connecteurs, ternaire, amplification,
    mots outils. Hors anglais, le jeu francais, qui est le defaut."""
    if langue == "en":
        return CONNECTEURS_EN, TRIPLE_EN, AMPLI_EN, _stop_en()
    return CONNECTEURS, TRIPLE, AMPLI, STOP


def _ecart_type(vals):
    if len(vals) < 2:
        return 0.0
    m = sum(vals) / len(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


_LIB = None


def _lib():
    """Charge libelles.py par son chemin, une seule fois. Meme raison que
    pour lint-style.py : le module se lit par chemin, aucun sys.path n'est
    garanti."""
    global _LIB
    if _LIB is None:
        import importlib.util
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "libelles.py")
        spec = importlib.util.spec_from_file_location("scriptorium_libelles",
                                                      chemin)
        _LIB = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_LIB)
    return _LIB


def analyser(texte, langue=None, langue_affichage=None):
    """Signaux d'empreinte IA du texte.

    Sans langue_affichage, les signaux sont les chaines francaises d'origine
    a l'octet pres : c'est cette liste que serialise le mode --format json,
    et que consolide audit-doc.py. La langue d'ANALYSE, elle, choisit les
    motifs cherches et ne se confond pas avec celle de l'affichage."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    langue = resoudre_langue(texte, langue)
    connecteurs, triple_re, ampli_re, stop = _motifs(langue)
    phrases = [p.strip() for p in SENT.findall(texte) if p.strip()]
    longueurs = [len(MOT.findall(p)) for p in phrases]
    longueurs = [l for l in longueurs if l > 0]
    mots = MOT.findall(texte)
    nmots = len(mots) or 1
    nph = len(longueurs) or 1
    premiers = [MOT.findall(p)[0].lower() for p in phrases if MOT.findall(p)]
    cnt = Counter(premiers)
    top = cnt.most_common(1)[0] if cnt else ("", 0)
    pct_ouverture = round(100 * top[1] / len(premiers), 1) if premiers else 0.0
    bas = texte.lower()
    nconn = sum(bas.count(c) for c in connecteurs)
    dens_conn = round(nconn / nph, 2)
    ntriple = len(triple_re.findall(texte))
    dens_triple = round(1000 * ntriple / nmots, 1)
    cw = [m.lower() for m in mots if m.lower() not in stop and len(m) > 2]
    bg = Counter(zip(cw, cw[1:]))
    bigr = bg.most_common(1)[0] if bg else (("", ""), 0)
    nampli = len(ampli_re.findall(texte))
    et = round(_ecart_type(longueurs), 1)
    signaux = []
    if nph >= 8 and et < 5:
        signaux.append(lib.t("aifp.s.variabilite_faible", la, ecart_type=et))
    if len(premiers) >= 8 and pct_ouverture > 25:
        signaux.append(lib.t("aifp.s.ouvertures_repetitives", la,
                             pct=pct_ouverture, mot=top[0]))
    if dens_conn > 0.5:
        signaux.append(lib.t("aifp.s.connecteurs", la, densite=dens_conn))
    if dens_triple > 6:
        signaux.append(lib.t("aifp.s.cadence_ternaire", la,
                             densite=dens_triple))
    if bigr[1] >= 4:
        signaux.append(lib.t("aifp.s.bigramme", la, n=bigr[1],
                             bigramme="%s %s" % (bigr[0][0], bigr[0][1])))
    if nampli >= 1:
        # La forme citee est celle des motifs cherches : elle suit la langue
        # d'ANALYSE, pas celle de l'affichage. Un rapport anglais sur un
        # texte francais doit nommer la tournure francaise reperee.
        forme = "not only ... but" if langue == "en" else "non seulement ... mais"
        signaux.append(lib.t("aifp.s.amplification", la, forme=forme,
                             n=nampli))
    return {
        "phrases": nph, "ecart_type_longueur": et, "ouverture_max_pct": pct_ouverture,
        "densite_connecteurs": dens_conn, "densite_triples": dens_triple,
        "bigramme_max": {"bigramme": " ".join(bigr[0]).strip(), "compte": bigr[1]},
        "amplificateurs": nampli, "signaux": signaux,
        "langue": langue,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Detecteur d'empreinte IA.")
    ap.add_argument("fichier")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--langue", choices=["fr", "en", "auto"], default=None,
                    help="langue d'analyse. Sans l'option : le pragme "
                         "lint-style:langue du document, sinon fr. "
                         "auto lance la détection heuristique")
    ap.add_argument("--langue-affichage", choices=["fr", "en"], default=None,
                    help="langue des libelles du rapport texte. Sans "
                         "l'option : la langue d'analyse retenue. La sortie "
                         "JSON reste francaise quoi qu'il arrive")
    a = ap.parse_args(argv)
    lib = _lib()
    texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    if a.format == "json":
        # Le JSON ne se traduit pas : les evals et le jeu d'or le lisent.
        print(json.dumps(analyser(texte, a.langue), ensure_ascii=False,
                         indent=2))
        return 0
    la = lib.resoudre_affichage(a.langue_affichage,
                                resoudre_langue(texte, a.langue))
    d = analyser(texte, a.langue, la)
    print(lib.t("aifp.titre", la))
    print("  " + lib.t("aifp.mesures", la,
                       ecart_type=d["ecart_type_longueur"],
                       ouverture=d["ouverture_max_pct"],
                       connecteurs=d["densite_connecteurs"],
                       triples=d["densite_triples"]))
    if not d["signaux"]:
        print("  " + lib.t("aifp.aucun_signal", la))
    for s in d["signaux"]:
        print(f"  - {s}")
    return 1 if len(d["signaux"]) >= 2 else 0


if __name__ == "__main__":
    sys.exit(main())
