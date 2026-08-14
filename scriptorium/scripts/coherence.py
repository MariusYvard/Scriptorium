#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Coherence interne et anti-redite pour Scriptorium.

Repere les paragraphes quasi dupliques (auto-plagiat), les phrases repetees,
et liste les promesses du texte (nous montrerons, la section X presentera) a
verifier. La rigueur passe du paragraphe au document entier.

Usage : python3 coherence.py FICHIER [--format text|json]
Module importable : analyser(texte) -> dict.
"""
import argparse
import json
import re
import sys
from collections import Counter

MOT = re.compile(r"\b[\wà-ÿœ]+\b", re.I)
SENT = re.compile(r'[^.!?…]+[.!?…]+', re.S)
PROMESSE = re.compile(r"(?i)\b(nous (?:montrerons|verrons|présenterons|détaillerons|"
                      r"reviendrons|expliquerons)|on (?:montrera|verra|détaillera)|"
                      r"la section \w+ (?:montre|présente|détaille)|nous y reviendrons)\b")


def _paras(texte):
    return [p.strip() for p in re.split(r'\n\s*\n', texte)
            if p.strip() and not p.strip().startswith('#') and not p.strip().startswith('|')]


def _shingles(t, n=3):
    w = [m.group(0).lower() for m in MOT.finditer(t)]
    return set(tuple(w[i:i + n]) for i in range(len(w) - n + 1)) if len(w) >= n else set()


def _jaccard(a, b):
    return len(a & b) / len(a | b) if (a and b) else 0.0


def analyser(texte):
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
    promesses = [m.group(0) for m in PROMESSE.finditer(texte)]
    return {
        "paragraphes_dupliques": dup,
        "phrases_repetees": len(repetees),
        "exemples_phrases_repetees": repetees[:3],
        "promesses": promesses,
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
    a = ap.parse_args(argv)
    texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    d = analyser(texte)
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
