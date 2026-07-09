#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verificateur de tracabilite deterministe pour Scriptorium.

Boucle la chaine preuve-affirmation au niveau mecanique : references citees
mais absentes de la bibliographie (citations pendantes), references listees
mais jamais citees (orphelines), figures et tableaux definis mais non appeles
dans le texte, et appels a une figure ou un tableau inexistant.

Compte aussi les tags normalises de lacune ([LACUNE MATERIELLE] et
[PREUVE FAIBLE], casse stricte) par section, pour exposer une donnee que
scorecard.py peut consommer comme il consomme deja les autres cles de ce
module. Un tag bien forme est un signal honnete de l'auteur, jamais une
penalite : seules les variantes de casse mal formees comptent comme un
probleme, puisqu'elles echappent silencieusement au reperage par grep.

Usage : python3 traceability.py FICHIER [--format text|json]
Module importable : analyser(texte) -> dict.
"""
import argparse
import json
import re
import sys

HEAD_REF = re.compile(r'(?im)^\s{0,3}#{1,6}\s*(r[ée]f[ée]rences?|bibliographie|references|bibliography)\b')
HEAD_SECTION = re.compile(r'(?im)^\s{0,3}(#{1,6})\s+(.+?)\s*$')

TAG_LACUNE_STRICT = re.compile(r'\[LACUNE MATERIELLE\]')
TAG_PREUVE_STRICT = re.compile(r'\[PREUVE FAIBLE\]')
TAG_LACUNE_LARGE = re.compile(r'\[LACUNE MATERIELLE\]', re.I)
TAG_PREUVE_LARGE = re.compile(r'\[PREUVE FAIBLE\]', re.I)


def separer_biblio(texte):
    m = HEAD_REF.search(texte)
    if not m:
        return texte, ""
    return texte[:m.start()], texte[m.start():]


def refs_numerotees(refsec):
    out = set()
    for line in refsec.splitlines():
        m = re.match(r'\s*\[?(\d{1,3})\]?[\.\)]\s+\S', line)
        if m:
            out.add(int(m.group(1)))
    return out


def cites_numerotees(corps):
    out = set()
    for m in re.finditer(r'\[(\d{1,3}(?:\s*[,–-]\s*\d{1,3})*)\]', corps):
        for part in m.group(1).split(','):
            part = part.strip().replace('–', '-')
            if '-' in part:
                a, b = part.split('-', 1)
                if a.strip().isdigit() and b.strip().isdigit():
                    out.update(range(int(a), int(b) + 1))
            elif part.isdigit():
                out.add(int(part))
    return out


def compter(corps, kind):
    capt = re.compile(r'(?im)^\s{0,3}(?:!\[[^\]]*\]\([^\)]*\)\s*)?%s\s+(\d{1,3})\s*[:\.—–-]' % kind)
    tout = re.compile(r'(?i)\b%s\s+(\d{1,3})' % kind)
    captions = {}
    for n in (int(x) for x in capt.findall(corps)):
        captions[n] = captions.get(n, 0) + 1
    mentions = {}
    for n in (int(x) for x in tout.findall(corps)):
        mentions[n] = mentions.get(n, 0) + 1
    definis = set(captions)
    appeles = {n for n, c in mentions.items() if c > captions.get(n, 0)}
    definis_non_appeles = sorted(definis - appeles)
    appeles_non_definis = sorted(appeles - definis)
    return definis_non_appeles, appeles_non_definis


def _sections(texte):
    """Decoupe le texte en sections par titre Markdown. Retourne une liste de
    (titre, contenu) ; le contenu avant le premier titre porte le titre
    "(preambule)"."""
    matches = list(HEAD_SECTION.finditer(texte))
    if not matches:
        return [("(préambule)", texte)]
    out = []
    if matches[0].start() > 0:
        out.append(("(préambule)", texte[:matches[0].start()]))
    for i, m in enumerate(matches):
        fin = matches[i + 1].start() if i + 1 < len(matches) else len(texte)
        out.append((m.group(2).strip(), texte[m.start():fin]))
    return out


def tags_lacune(texte):
    """Compte les tags [LACUNE MATERIELLE] et [PREUVE FAIBLE], casse stricte,
    signale les variantes de casse mal formees, et ventile par section."""
    lacune_stricte = len(TAG_LACUNE_STRICT.findall(texte))
    preuve_stricte = len(TAG_PREUVE_STRICT.findall(texte))
    lacune_large = TAG_LACUNE_LARGE.findall(texte)
    preuve_large = TAG_PREUVE_LARGE.findall(texte)
    variantes = [t for t in lacune_large if t != "[LACUNE MATERIELLE]"]
    variantes += [t for t in preuve_large if t != "[PREUVE FAIBLE]"]
    par_section = {}
    for titre, contenu in _sections(texte):
        n_lac = len(TAG_LACUNE_STRICT.findall(contenu))
        n_pre = len(TAG_PREUVE_STRICT.findall(contenu))
        if n_lac or n_pre:
            par_section[titre] = {"lacune_materielle": n_lac, "preuve_faible": n_pre}
    return {
        "tags_lacune_materielle": lacune_stricte,
        "tags_preuve_faible": preuve_stricte,
        "tags_variantes_mal_formees": variantes,
        "tags_par_section": par_section,
    }


def analyser(texte):
    corps, biblio = separer_biblio(texte)
    definies = refs_numerotees(biblio)
    citees = cites_numerotees(corps)
    pendantes = sorted(citees - definies)
    orphelines = sorted(definies - citees) if definies else []
    fig_nc, fig_nd = compter(corps, 'figure')
    tab_nc, tab_nd = compter(corps, 'tableau')
    resultat = {
        "biblio_presente": bool(biblio),
        "references_definies": sorted(definies),
        "citations_pendantes": pendantes,
        "references_orphelines": orphelines,
        "figures_definies_non_appelees": fig_nc,
        "figures_appelees_non_definies": fig_nd,
        "tableaux_definis_non_appeles": tab_nc,
        "tableaux_appeles_non_definis": tab_nd,
    }
    resultat.update(tags_lacune(texte))
    return resultat


def problemes(d):
    p = []
    if d["citations_pendantes"]:
        p.append(f"Citations pendantes (citees, absentes de la biblio) : {d['citations_pendantes']}")
    if d["references_orphelines"]:
        p.append(f"References orphelines (listees, jamais citees) : {d['references_orphelines']}")
    if d["figures_appelees_non_definies"]:
        p.append(f"Figures appelees mais non definies : {d['figures_appelees_non_definies']}")
    if d["figures_definies_non_appelees"]:
        p.append(f"Figures definies mais jamais appelees : {d['figures_definies_non_appelees']}")
    if d["tableaux_appeles_non_definis"]:
        p.append(f"Tableaux appeles mais non definis : {d['tableaux_appeles_non_definis']}")
    if d["tableaux_definis_non_appeles"]:
        p.append(f"Tableaux definis mais jamais appeles : {d['tableaux_definis_non_appeles']}")
    if d["tags_variantes_mal_formees"]:
        p.append(f"Tags de lacune mal formes (casse non conforme) : {d['tags_variantes_mal_formees']}")
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description="Verificateur de tracabilite.")
    ap.add_argument("fichier")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    a = ap.parse_args(argv)
    texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    d = analyser(texte)
    p = problemes(d)
    if a.format == "json":
        print(json.dumps({"analyse": d, "problemes": p}, ensure_ascii=False, indent=2))
    else:
        print("Tracabilite")
        print(f"  biblio presente : {d['biblio_presente']} | references definies : {len(d['references_definies'])}")
        print(f"  tags [LACUNE MATERIELLE] : {d['tags_lacune_materielle']} | "
              f"tags [PREUVE FAIBLE] : {d['tags_preuve_faible']}")
        if not p:
            print("  Aucun probleme de tracabilite.")
        for x in p:
            print(f"  - {x}")
        if d["tags_par_section"]:
            print("  Repartition par section :")
            for titre, c in d["tags_par_section"].items():
                print(f"    {titre} : lacune={c['lacune_materielle']} preuve_faible={c['preuve_faible']}")
    return 1 if p else 0


if __name__ == "__main__":
    sys.exit(main())
