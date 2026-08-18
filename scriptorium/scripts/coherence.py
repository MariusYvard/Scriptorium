#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Coherence interne et anti-redite pour Scriptorium.

Repere les paragraphes quasi dupliques (auto-plagiat), les phrases repetees,
et liste les promesses du texte (nous montrerons, la section X presentera) a
verifier. La rigueur passe du paragraphe au document entier.

Portee de langue, verifiee mesure par mesure. Une seule des trois depend de
la langue : la liste des promesses, batie sur des tournures francaises. Les
deux autres ne lisent aucun mot particulier. Le rapprochement de
paragraphes compare des empreintes de trois mots consecutifs, et la
repetition de phrases compare des phrases entieres : l'un et l'autre
travaillent sur les mots du texte, quels qu'ils soient. La segmentation en
phrases s'arrete a la ponctuation forte, commune aux deux langues, et le
motif de mot couvre les lettres latines accentuees ou non. Ces deux mesures
restent donc communes, et le sont declarees ici plutot que dupliquees.

Usage : python3 coherence.py FICHIER [--format text|json]
                                     [--langue fr|en|auto]
Module importable : analyser(texte, langue=None) -> dict.
"""
import argparse
import json
import os
import re
import sys
from collections import Counter

MOT = re.compile(r"\b[\wà-ÿœ]+\b", re.I)
SENT = re.compile(r'[^.!?…]+[.!?…]+', re.S)
PROMESSE = re.compile(r"(?i)\b(nous (?:montrerons|verrons|présenterons|détaillerons|"
                      r"reviendrons|expliquerons)|on (?:montrera|verra|détaillera)|"
                      r"la section \w+ (?:montre|présente|détaille)|nous y reviendrons)\b")
# Promesses de l'article scientifique anglais : annonce au futur a la
# premiere personne, transition explicite vers une section, renvoi a un
# passage a venir. Meme grandeur mesuree qu'en francais, memes trois formes.
PROMESSE_EN = re.compile(
    r"(?i)\b(we (?:will|shall) (?:show|present|discuss|describe|demonstrate|"
    r"detail|argue|return to|see)|we now turn to|"
    r"(?:this|the following|the next) section (?:presents|describes|"
    r"introduces|details|discusses|will present)|"
    r"as (?:discussed|shown|described|detailed) (?:below|later)|"
    r"(?:later|further) in this (?:paper|article|report|chapter)|"
    r"in what follows|we return to this)\b")

LANGUES = ("fr", "en")

_LINT = None


def _lint():
    """Charge lint-style.py par son chemin, une seule fois.

    Le nom du fichier porte un tiret, il n'est pas importable tel quel. La
    resolution de langue y est definie et documentee : elle est lue ici,
    jamais recopiee, sinon deux scripts pourraient trancher differemment la
    langue du meme document.
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
    """Tranche la langue d'analyse, par delegation a lint-style.py.

    Meme ordre de priorite que le linter : option explicite, puis auto, puis
    pragme du document, puis francais. Un code hors fr, en et auto est rendu
    tel quel ; les promesses retombent alors sur le motif francais.
    """
    if langue is not None and langue not in LANGUES and langue != "auto":
        return langue
    return _lint().resoudre_langue(texte, langue)


def _paras(texte):
    return [p.strip() for p in re.split(r'\n\s*\n', texte)
            if p.strip() and not p.strip().startswith('#') and not p.strip().startswith('|')]


def _shingles(t, n=3):
    w = [m.group(0).lower() for m in MOT.finditer(t)]
    return set(tuple(w[i:i + n]) for i in range(len(w) - n + 1)) if len(w) >= n else set()


def _jaccard(a, b):
    return len(a & b) / len(a | b) if (a and b) else 0.0


def analyser(texte, langue=None):
    langue = resoudre_langue(texte, langue)
    paras = _paras(texte)
    sh = [_shingles(p) for p in paras]
    dup = []
    for i in range(len(paras)):
        for j in range(i + 1, len(paras)):
            s = _jaccard(sh[i], sh[j])
            if s >= 0.6 and len(MOT.findall(paras[i])) >= 12:
                dup.append({"para_a": i + 1, "para_b": j + 1, "similitude": round(s, 2)})
    phr = [p.strip().lower() for p in SENT.findall(texte) if len(MOT.findall(p)) >= 6]
    c = Counter(phr)
    repetees = [s for s, n in c.items() if n > 1]
    motif = PROMESSE_EN if langue == "en" else PROMESSE
    promesses = [m.group(0) for m in motif.finditer(texte)]
    return {
        "paragraphes_dupliques": dup,
        "phrases_repetees": len(repetees),
        "exemples_phrases_repetees": repetees[:3],
        "promesses": promesses,
        "langue": langue,
    }


def problemes(d):
    p = []
    for x in d["paragraphes_dupliques"]:
        p.append(f"Paragraphes {x['para_a']} et {x['para_b']} quasi identiques (similitude {x['similitude']}).")
    if d["phrases_repetees"]:
        p.append(f"{d['phrases_repetees']} phrase(s) repetee(s) a l'identique.")
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description="Coherence interne et anti-redite.")
    ap.add_argument("fichier")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--langue", choices=["fr", "en", "auto"], default=None,
                    help="langue d'analyse. Sans l'option : le pragme "
                         "lint-style:langue du document, sinon fr. "
                         "auto lance la détection heuristique")
    a = ap.parse_args(argv)
    texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    d = analyser(texte, a.langue)
    p = problemes(d)
    if a.format == "json":
        print(json.dumps({"analyse": d, "problemes": p}, ensure_ascii=False, indent=2))
    else:
        print("Coherence interne")
        if not p:
            print("  Aucune redite ni duplication detectee.")
        for x in p:
            print(f"  - {x}")
        if d["promesses"]:
            print(f"  Promesses a verifier ({len(d['promesses'])}) : {d['promesses'][:5]}")
    return 1 if p else 0


if __name__ == "__main__":
    sys.exit(main())
