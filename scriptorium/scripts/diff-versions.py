#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Journal des ecarts entre deux versions d'un document (Markdown).

Compare deux versions et produit un changelog : sections ajoutees, supprimees,
modifiees, avec le compte de mots ajoutes et supprimes. Outil de revision
suivie, deterministe, sans dependance.

Usage : python3 diff-versions.py ANCIEN.md NOUVEAU.md [--format text|json]
Module importable : comparer(ancien, nouveau) -> dict.
"""
import argparse
import json
import re
import sys
from difflib import SequenceMatcher

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


def main(argv=None):
    ap = argparse.ArgumentParser(description="Journal des ecarts entre versions.")
    ap.add_argument("ancien")
    ap.add_argument("nouveau")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    a = ap.parse_args(argv)
    d = comparer(open(a.ancien, encoding="utf-8").read(), open(a.nouveau, encoding="utf-8").read())
    if a.format == "json":
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print("Journal des ecarts")
        print(f"  mots : {d['mots_ancien']} -> {d['mots_nouveau']} | similitude {d['similitude_globale']}")
        if d["sections_ajoutees"]:
            print(f"  Sections ajoutees : {d['sections_ajoutees']}")
        if d["sections_supprimees"]:
            print(f"  Sections supprimees : {d['sections_supprimees']}")
        for m in d["sections_modifiees"]:
            print(f"  Modifiee « {m['section']} » : +{m['mots_ajoutes']} / -{m['mots_supprimes']} mots")
        if not (d["sections_ajoutees"] or d["sections_supprimees"] or d["sections_modifiees"]):
            print("  Aucun ecart de section.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
