#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Métriques de lisibilité déterministes pour Scriptorium (français).

Transforme la règle floue « varier le rythme » en mesure : longueur de
phrase moyenne et écart-type, part de phrases longues et courtes, longueur
de paragraphe, densité lexicale, approximation du taux de passif, indice
LIX (agnostique à la langue, lisible pour le français).

Portee de langue : la mesure du passif depend de la langue. Le motif
francais vit ici (PASSIF_RE), le motif anglais est celui de lint-style.py
(_PASSIF_EN), lu et non recopie. Hors francais et anglais, le taux de passif
n'est pas mesure et se declare tel quel (None), jamais zero : une mesure
impossible se declare, elle ne s'invente pas.

Portabilite des seuils, decidee mesure par mesure :
  - longueurs de phrase (moyenne, ecart-type, part au-dela de 30 mots, part
    en deca de 8) : comptes en mots, transportables tels quels. Les seuils
    de 28, 30 et 8 mots ne sont propres a aucune des deux langues.
  - indice LIX : la formule est agnostique a la langue par construction
    (Bjornsson), le mot long y vaut plus de six caracteres partout. La bande
    attendue 30-56 qu'applique scorecard.py, elle, a ete calibree sur des
    textes francais, dont les mots sont en moyenne plus longs qu'en anglais.
    Elle est conservee faute de calibrage anglais mesure, et cette limite est
    declaree ici plutot que corrigee a l'estime.
  - densite lexicale (TTR) : le seuil de 0,35 est une convention maison. Le
    rapport type sur occurrence depend de la longueur du texte et de la
    morphologie de la langue, il ne se compare pas d'une langue a l'autre.
    Conserve, non transpose.
  - taux de passif : seule mesure reellement dependante de la langue, et
    seule modifiee.

Usage :
    python3 readability.py FICHIER [--format text|json] [--langue fr|en|auto]
    cat doc.md | python3 readability.py -

Le module est importable : mesurer(texte, langue=None) -> dict.
"""
import argparse
import json
import math
import os
import re
import sys

MOT_RE = re.compile(r"\b[\wàâäéèêëîïôöùûüç'-]+\b", re.I)
PHRASE_RE = re.compile(r"[^.!?…]+[.!?…]+", re.S)
PASSIF_RE = re.compile(
    r"\b(est|sont|été|était|étaient|fut|furent|sera|seront|"
    r"a été|ont été|avait été)\s+\w*(é|és|ée|ées)\b", re.I)

LANGUES = ("fr", "en")

_LIB = None


def _lib():
    """Charge libelles.py a la demande, une seule fois. Meme raison que pour
    lint-style.py : le module se lit par chemin, aucun sys.path n'est
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


_LINT = None


def _lint():
    """Charge lint-style.py a la demande, une seule fois.

    Le nom du fichier porte un tiret, il n'est pas importable tel quel. La
    resolution de langue et le motif de passif anglais y sont definis et
    documentes : ils sont lus ici, jamais recopies, sinon deux versions du
    meme motif divergeraient sans que rien ne le signale.
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


def resoudre_langue(texte, langue=None):
    """Tranche la langue de mesure, par delegation a lint-style.py.

    Meme ordre de priorite que le linter : option explicite, puis auto, puis
    pragme du document, puis francais. Un code de langue hors fr, en et auto
    est rendu tel quel plutot que ramene au francais : la mesure qui en
    depend se declarera non faite, ce qui est l'information juste.
    """
    if langue is not None and langue not in LANGUES and langue != "auto":
        return langue
    return _lint().resoudre_langue(texte, langue)


def _passif(propre, langue):
    """Occurrences de voix passive selon la langue, ou None si la langue
    n'est pas couverte. None n'est pas zero : c'est l'absence de mesure."""
    if langue == "fr":
        return len(PASSIF_RE.findall(propre))
    if langue == "en":
        return len(_lint()._PASSIF_EN.findall(propre))
    return None


def nettoyer(texte):
    # retire les blocs de code et la syntaxe markdown lourde
    texte = re.sub(r"```.*?```", " ", texte, flags=re.S)
    texte = re.sub(r"`[^`]*`", " ", texte)
    texte = re.sub(r"^\s{0,3}[#>|].*$", " ", texte, flags=re.M)
    texte = re.sub(r"[*_#>]+", " ", texte)
    return texte


def ecart_type(valeurs):
    if len(valeurs) < 2:
        return 0.0
    moy = sum(valeurs) / len(valeurs)
    var = sum((v - moy) ** 2 for v in valeurs) / (len(valeurs) - 1)
    return math.sqrt(var)


def mesurer(texte, langue=None):
    langue = resoudre_langue(texte, langue)
    propre = nettoyer(texte)
    phrases = [p.strip() for p in PHRASE_RE.findall(propre) if p.strip()]
    if not phrases:
        phrases = [propre.strip()] if propre.strip() else []
    longueurs = [len(MOT_RE.findall(p)) for p in phrases]
    longueurs = [l for l in longueurs if l > 0]
    mots = MOT_RE.findall(propre)
    n_mots = len(mots)
    n_phr = len(longueurs) or 1
    paras = [b for b in re.split(r"\n\s*\n", texte) if b.strip()]
    phr_par_para = []
    for b in paras:
        bp = nettoyer(b)
        phr_par_para.append(max(1, len(PHRASE_RE.findall(bp))))
    mots_longs = sum(1 for m in mots if len(m) > 6)
    types = {m.lower() for m in mots}
    n_passif = _passif(propre, langue)
    # Deux raisons de ne pas mesurer le passif : la langue n'est pas couverte,
    # ou le texte ne porte aucune phrase mesurable. Dans les deux cas la valeur
    # rendue est None et le motif est nomme. Rendre zero laisserait croire a un
    # texte sans passif et rendrait la regle d'interpretation injoignable.
    non_faites = []
    if not longueurs:
        taux_passif = None
        non_faites.append({"mesure": "taux_passif_approx_pct",
                           "motif": "aucune phrase mesurable dans le texte"})
    elif n_passif is None:
        taux_passif = None
        non_faites.append({"mesure": "taux_passif_approx_pct",
                           "motif": "langue « %s » hors des langues couvertes "
                                    "(%s)" % (langue, ", ".join(LANGUES))})
    else:
        taux_passif = round(100 * n_passif / n_phr, 1)
    moy_phr = (sum(longueurs) / n_phr) if longueurs else 0.0
    lix = (moy_phr + 100.0 * mots_longs / n_mots) if n_mots else 0.0
    return {
        "langue": langue,
        "mesures_non_faites": non_faites,
        "mots": n_mots,
        "phrases": len(longueurs),
        "paragraphes": len(paras),
        "longueur_phrase_moyenne": round(moy_phr, 1),
        "longueur_phrase_ecart_type": round(ecart_type(longueurs), 1),
        "phrases_longues_sup30_pct": round(100 * sum(1 for l in longueurs if l > 30) / n_phr, 1),
        "phrases_courtes_inf8_pct": round(100 * sum(1 for l in longueurs if l < 8) / n_phr, 1),
        "phrases_par_paragraphe_moyenne": round(sum(phr_par_para) / len(phr_par_para), 1) if phr_par_para else 0.0,
        "densite_lexicale": round(len(types) / n_mots, 3) if n_mots else 0.0,
        "taux_passif_approx_pct": taux_passif,
        "indice_lix": round(lix, 1),
    }


def interpreter(m, langue_affichage=None):
    """Lecture des metriques, en prose. Sans langue_affichage, les notes sont
    celles d'origine a l'octet pres : ce sont elles que porte la cle lecture
    de la sortie JSON, qui ne se traduit pas."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    notes = []
    if m["longueur_phrase_ecart_type"] < 5 and m["phrases"] >= 5:
        notes.append(lib.t("readability.n.rythme_monotone", la))
    if m["longueur_phrase_moyenne"] > 28:
        notes.append(lib.t("readability.n.phrases_longues", la))
    if m["phrases_courtes_inf8_pct"] < 8 and m["phrases"] >= 6:
        notes.append(lib.t("readability.n.peu_de_courtes", la))
    if m["indice_lix"] > 56:
        notes.append(lib.t("readability.n.lix_eleve", la))
    if m["indice_lix"] < 34 and m["mots"] > 120:
        notes.append(lib.t("readability.n.lix_bas", la))
    if m["densite_lexicale"] < 0.35 and m["mots"] > 200:
        notes.append(lib.t("readability.n.densite_faible", la))
    if m["taux_passif_approx_pct"] is None:
        # Une mesure absente se dit, elle ne se tait pas : sans cette ligne, un
        # texte dont le passif n'a pas ete mesure se lirait comme un texte dont
        # le passif a ete mesure et juge acceptable.
        for nf in m.get("mesures_non_faites", []):
            notes.append(lib.t("readability.n.mesure_non_faite", la,
                               mesure=nf["mesure"],
                               motif=lib.motif(nf["motif"], la)))
    elif m["taux_passif_approx_pct"] > 25:
        notes.append(lib.t("readability.n.passif_eleve", la))
    if not notes:
        notes.append(lib.t("readability.n.dans_les_bornes", la))
    return notes


# Ordre d'impression des metriques. Les CLES sont celles de la sortie JSON,
# elles ne changent pas de langue ; seul leur libelle en change.
METRIQUES_AFFICHEES = (
    "mots", "phrases", "paragraphes", "longueur_phrase_moyenne",
    "longueur_phrase_ecart_type", "phrases_longues_sup30_pct",
    "phrases_courtes_inf8_pct", "phrases_par_paragraphe_moyenne",
    "densite_lexicale", "taux_passif_approx_pct", "indice_lix",
)


def rapport_texte(m, langue_affichage=None):
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    out = [lib.t("readability.titre", la),
           "  " + lib.t("readability.langue_mesuree", la,
                        langue=m.get("langue"))]
    for k in METRIQUES_AFFICHEES:
        valeur = (lib.t("readability.non_mesure", la) if m[k] is None
                  else m[k])
        out.append("  %-32s %s" % (lib.t("readability.m." + k, la), valeur))
    out.append("\n" + lib.t("readability.lecture", la))
    out += [f"  - {n}" for n in interpreter(m, la)]
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description="Métriques de lisibilité Scriptorium.")
    p.add_argument("fichier", help="chemin du fichier, ou - pour stdin")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--langue", choices=["fr", "en", "auto"], default=None,
                   help="langue de mesure. Sans l'option : le pragme "
                        "lint-style:langue du document, sinon fr. "
                        "auto lance la détection heuristique")
    p.add_argument("--langue-affichage", choices=["fr", "en"], default=None,
                   help="langue des libellés du rapport texte. Sans "
                        "l'option : la langue de mesure retenue. La sortie "
                        "JSON reste française quoi qu'il arrive")
    a = p.parse_args(argv)
    lib = _lib()
    try:
        texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    except OSError as e:
        print(lib.t("readability.erreur_lecture",
                    lib.resoudre_affichage(a.langue_affichage), erreur=e),
              file=sys.stderr)
        return 2
    m = mesurer(texte, a.langue)
    if a.format == "json":
        # La cle lecture reste francaise : elle est lue par des outils, pas
        # seulement par un humain.
        print(json.dumps({"metriques": m, "lecture": interpreter(m)},
                         ensure_ascii=False, indent=2))
    else:
        print(rapport_texte(
            m, lib.resoudre_affichage(a.langue_affichage, m.get("langue"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
