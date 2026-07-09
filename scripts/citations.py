#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Moteur de citations pour Scriptorium : BibTeX, formatage, deduplication.

Lit du BibTeX, formate chaque reference en APA 7, Vancouver, Chicago
(auteur-date), MLA (9e ed., auteur-page) ou IEEE (numerique), deduplique par
DOI puis par titre. La recuperation des metadonnees a partir d'un DOI
(Crossref) est optionnelle et reseau (--doi). Tout le reste est hors ligne.

Ancre par citation : le champ BibTeX optionnel `annote` (priorite) ou `note`
porte soit une citation exacte de 25 mots au plus, soit une localisation
(page, section, paragraphe). Une entree sans ce champ, ou dont le champ ne
correspond a aucun des deux formats, est signalee sans ancre (--exiger-ancres
pour en faire une erreur bloquante, sinon un simple signal).

Bascule de format : --bascule ANCIEN NOUVEAU reemet la meme bibliographie
(le fichier .bib est la seule source de verite) dans un nouveau format tout
en affichant l'ancien, avec un compte de references avant et apres (doit
rester identique : aucune entree n'est perdue par un changement de format,
puisque les deux ne sont que deux rendus de la meme liste analysee).

Limites communes aux cinq formats (formats de base couverts, cas exotiques
non couverts) : pas de gestion des auteurs institutionnels, des oeuvres sans
auteur hors du repli "Anonyme", des communications personnelles, des
references legales, ni des styles secondaires de chaque norme (Chicago
notes-bibliographie n'est pas couvert, seul auteur-date l'est ; MLA ne
genere pas la citation dans le texte, qui exige un numero de page absent du
BibTeX ; IEEE n'abrege pas les noms de revue selon la liste IEEE). Chaque
fonction de formatage documente ses propres simplifications dans son
docstring.

Usage :
    python3 citations.py FICHIER.bib --to apa|vancouver|chicago|mla|ieee [--dedupe]
    python3 citations.py FICHIER.bib --bascule ANCIEN NOUVEAU
    python3 citations.py --doi 10.xxxx/yyyy   (reseau, recupere une entree)
    python3 citations.py FICHIER.bib --exiger-ancres
Module importable : parser_bibtex(texte) ; format_apa(e) ; format_vancouver(e) ;
format_chicago(e) ; format_mla(e) ; format_ieee(e) ; FORMATS (dict nom -> fonction) ;
dedupe(entrees) ; ancre_de(entree).
"""
import argparse
import json
import re
import sys

ENTREE = re.compile(r'@(\w+)\s*\{\s*([^,]+)\s*,(.*?)\n\s*\}', re.S)
CHAMP = re.compile(r'(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|"[^"]*"|[^,\n]+)', re.S)

SEUIL_MOTS_CITATION = 25  # documente dans references/integrite-sources.md
LOCATEUR_RE = re.compile(
    r'(?i)\b(pp?\.|pages?|§|sections?|sec\.|chapitres?|chap\.|paragraphes?|par(a)?\.?)'
    r'\s*\d+([.\-]\d+)*\b')


def parser_bibtex(texte):
    entrees = []
    for m in ENTREE.finditer(texte):
        typ, cle, corps = m.group(1).lower(), m.group(2).strip(), m.group(3)
        champs = {}
        for c in CHAMP.finditer(corps):
            k = c.group(1).lower()
            v = c.group(2).strip().strip(',').strip()
            if v and v[0] in '{"' and v[-1] in '}"':
                v = v[1:-1]
            champs[k] = ' '.join(v.split())
        champs["_type"] = typ
        champs["_cle"] = cle
        entrees.append(champs)
    return entrees


def _auteurs(brut):
    """Analyse le champ BibTeX `author` (separateur ' and '). Retourne une
    liste de triplets (nom, initiales, prenoms_complets). `prenoms` porte la
    forme donnee dans le BibTeX (ex. 'Jane'), `initiales` en derive ('J.') :
    APA et Vancouver n'utilisent que les initiales (inchange depuis le lot 1),
    Chicago et MLA preferent le prenom complet quand il est disponible et se
    replient sur les initiales sinon."""
    if not brut:
        return []
    out = []
    for a in re.split(r'\s+and\s+', brut):
        a = a.strip()
        if ',' in a:
            nom, prenoms = [p.strip() for p in a.split(',', 1)]
        else:
            bouts = a.split()
            nom = bouts[-1] if bouts else a
            prenoms = ' '.join(bouts[:-1])
        initiales = ''.join(p[0].upper() + '.' for p in prenoms.split() if p)
        out.append((nom, initiales, prenoms))
    return out


def format_apa(e):
    aut = _auteurs(e.get("author", ""))
    if aut:
        noms = [f"{n}, {i}" for n, i, _p in aut]
        if len(noms) == 1:
            sa = noms[0]
        elif len(noms) <= 7:
            sa = ", ".join(noms[:-1]) + " et " + noms[-1]
        else:
            sa = ", ".join(noms[:6]) + " ... " + noms[-1]
    else:
        sa = "Anonyme"
    an = e.get("year", "s.d.")
    titre = e.get("title", "Sans titre")
    s = f"{sa} ({an}). {titre}."
    if e.get("journal"):
        s += f" {e['journal']}"
        if e.get("volume"):
            s += f", {e['volume']}"
            if e.get("number"):
                s += f"({e['number']})"
        if e.get("pages"):
            s += f", {e['pages'].replace('--', '-')}"
        s += "."
    elif e.get("publisher"):
        s += f" {e['publisher']}."
    if e.get("doi"):
        s += f" https://doi.org/{e['doi']}"
    return s


def format_vancouver(e):
    aut = _auteurs(e.get("author", ""))
    noms = [f"{n} {i.replace('.', '')}" for n, i, _p in aut]
    if len(noms) > 6:
        sa = ", ".join(noms[:6]) + ", et al"
    else:
        sa = ", ".join(noms) if noms else "Anonyme"
    titre = e.get("title", "Sans titre")
    s = f"{sa}. {titre}."
    if e.get("journal"):
        s += f" {e['journal']}."
        s += f" {e.get('year', 's.d.')}"
        if e.get("volume"):
            s += f";{e['volume']}"
            if e.get("number"):
                s += f"({e['number']})"
        if e.get("pages"):
            s += f":{e['pages'].replace('--', '-')}"
        s += "."
    else:
        s += f" {e.get('publisher', '')} {e.get('year', '')}.".replace("  ", " ")
    if e.get("doi"):
        s += f" doi:{e['doi']}"
    return s


def format_chicago(e):
    """Chicago (auteur-date, 17e/18e ed., chicagomanualofstyle.org) : Nom,
    Prenom. Annee. "Titre." Revue Volume(Numero) : pages. Auteur seul inverse
    (Nom, Prenom), auteurs suivants a l'endroit (Prenom Nom), plus de sept
    auteurs abrege en 'et al.' apres le septieme. Limite : seul le style
    auteur-date est couvert, pas le style notes-bibliographie (references
    numerotees en note de bas de page) qui est l'autre moitie de la norme
    Chicago."""
    aut = _auteurs(e.get("author", ""))
    if aut:
        parties = []
        for idx, (n, i, p) in enumerate(aut):
            prenom = p if p else i
            parties.append(f"{n}, {prenom}" if idx == 0 else f"{prenom} {n}")
        if len(parties) > 7:
            sa = ", ".join(parties[:7]) + ", et al."
        elif len(parties) > 1:
            sa = ", ".join(parties[:-1]) + ", et " + parties[-1]
        else:
            sa = parties[0]
    else:
        sa = "Anonyme"
    an = e.get("year", "s.d.")
    titre = e.get("title", "Sans titre")
    s = f"{sa}. {an}. "
    if e.get("journal"):
        s += f'"{titre}." {e["journal"]}'
        if e.get("volume"):
            s += f" {e['volume']}"
            if e.get("number"):
                s += f"({e['number']})"
        if e.get("pages"):
            s += f": {e['pages'].replace('--', '-')}"
        s += "."
    elif e.get("publisher"):
        s += f"{titre}. {e['publisher']}."
    else:
        s += f"{titre}."
    if e.get("doi"):
        s += f" https://doi.org/{e['doi']}"
    return s


def format_mla(e):
    """MLA (9e ed., auteur-page, style.mla.org) : Nom, Prenom. "Titre." Revue,
    vol. X, no Y, Annee, pp. pages. Deux auteurs relies par 'and', trois
    auteurs ou plus abreges directement apres le premier en 'et al.' (regle
    MLA 9 simplifiee, qui ne distingue pas 3 et 30 auteurs). Limite : ne
    produit pas la citation dans le texte (auteur-page), le numero de page
    de la citation precise n'existe pas dans un champ BibTeX standard ;
    conteneurs imbriques (article republie dans un recueil) non couverts."""
    aut = _auteurs(e.get("author", ""))
    if aut:
        n0, i0, p0 = aut[0]
        prenom0 = p0 if p0 else i0
        if len(aut) == 1:
            sa = f"{n0}, {prenom0}."
        elif len(aut) == 2:
            n1, i1, p1 = aut[1]
            prenom1 = p1 if p1 else i1
            sa = f"{n0}, {prenom0}, and {prenom1} {n1}."
        else:
            sa = f"{n0}, {prenom0}, et al."
    else:
        sa = "Anonyme."
    titre = e.get("title", "Sans titre")
    an = e.get("year", "s.d.")
    s = f'{sa} "{titre}."'
    if e.get("journal"):
        s += f" {e['journal']}"
        if e.get("volume"):
            s += f", vol. {e['volume']}"
        if e.get("number"):
            s += f", no. {e['number']}"
        s += f", {an}"
        if e.get("pages"):
            s += f", pp. {e['pages'].replace('--', '-')}"
        s += "."
    elif e.get("publisher"):
        s = f"{sa} {titre}. {e['publisher']}, {an}."
    if e.get("doi"):
        s += f" https://doi.org/{e['doi']}"
    return s


def format_ieee(e):
    """IEEE (numerique, ieeeauthorcenter.ieee.org) : I. Nom, "Titre," Revue,
    vol. X, no. Y, pp. pages, Annee. Auteurs en initiales-prenom (I. Nom),
    plus de six auteurs abrege en 'et al.' apres le sixieme (repli
    IEEE). Le numero d'ordre entre crochets ([n]) est ajoute par l'appelant
    (main() ou l'appelant du module), pas par cette fonction, pour rester
    coherente avec format_apa/format_vancouver qui ne s'auto-numerotent pas
    non plus. Limite : n'abrege pas les noms de revue selon la liste
    d'abreviations IEEE, ne couvre pas les actes de conference ni les
    normes."""
    aut = _auteurs(e.get("author", ""))
    if aut:
        noms = [f"{i} {n}" if i else n for n, i, _p in aut]
        if len(noms) > 6:
            sa = ", ".join(noms[:6]) + ", et al."
        elif len(noms) > 1:
            sa = ", ".join(noms[:-1]) + ", and " + noms[-1]
        else:
            sa = noms[0]
    else:
        sa = "Anonyme"
    titre = e.get("title", "Sans titre")
    s = f'{sa}, "{titre},"'
    if e.get("journal"):
        s += f" {e['journal']}"
        if e.get("volume"):
            s += f", vol. {e['volume']}"
        if e.get("number"):
            s += f", no. {e['number']}"
        if e.get("pages"):
            s += f", pp. {e['pages'].replace('--', '-')}"
        s += f", {e.get('year', 's.d.')}."
    elif e.get("publisher"):
        s += f" {e['publisher']}, {e.get('year', 's.d.')}."
    if e.get("doi"):
        s += f" doi: {e['doi']}."
    return s


FORMATS = {
    "apa": format_apa,
    "vancouver": format_vancouver,
    "chicago": format_chicago,
    "mla": format_mla,
    "ieee": format_ieee,
}

NUMEROTES = {"vancouver", "ieee"}  # styles ou la liste porte un numero d'ordre


def _ligne(ref, style, i):
    if style == "vancouver":
        return f"{i}. {ref}"
    if style == "ieee":
        return f"[{i}] {ref}"
    return ref


def dedupe(entrees):
    vus = {}
    uniques = []
    doublons = []
    for e in entrees:
        cle = (e.get("doi", "").lower().strip()
               or re.sub(r'[^a-z0-9]', '', e.get("title", "").lower()))
        if cle and cle in vus:
            doublons.append(e.get("_cle"))
        else:
            if cle:
                vus[cle] = True
            uniques.append(e)
    return uniques, doublons


def ancre_de(entree):
    """Type d'ancre portee par une entree BibTeX : citation (<=25 mots),
    localisation (page/section/paragraphe), absente, ou invalide (champ
    present mais ni l'un ni l'autre format). Champ `annote` prioritaire sur
    `note`, comme convention de ce module."""
    valeur = entree.get("annote") or entree.get("note") or ""
    valeur = valeur.strip()
    if not valeur:
        return {"type": "absente", "valeur": None}
    if LOCATEUR_RE.search(valeur):
        return {"type": "localisation", "valeur": valeur}
    n_mots = len(valeur.split())
    if n_mots <= SEUIL_MOTS_CITATION:
        return {"type": "citation", "valeur": valeur, "mots": n_mots}
    return {"type": "invalide", "valeur": valeur, "mots": n_mots}


def rapport_ancrage(entrees):
    """Une entree par cle BibTeX avec son type d'ancre, et la liste des
    entrees sans ancre exploitable (absente ou invalide)."""
    detail = []
    sans_ancre = []
    for e in entrees:
        a = ancre_de(e)
        detail.append({"cle": e.get("_cle"), **a})
        if a["type"] in ("absente", "invalide"):
            sans_ancre.append(e.get("_cle"))
    return {"detail": detail, "sans_ancre": sans_ancre}


def fetch_doi(doi):  # reseau, appele seulement avec --doi
    import urllib.request
    url = "https://api.crossref.org/works/" + doi.strip()
    with urllib.request.urlopen(url, timeout=15) as r:
        msg = json.loads(r.read().decode("utf-8"))["message"]
    auteurs = " and ".join(
        f"{a.get('family', '')}, {a.get('given', '')}" for a in msg.get("author", []))
    return {
        "_type": msg.get("type", "article"), "_cle": doi.replace("/", "_"),
        "author": auteurs, "title": " ".join(msg.get("title", ["Sans titre"])),
        "year": str(msg.get("issued", {}).get("date-parts", [[None]])[0][0] or ""),
        "journal": " ".join(msg.get("container-title", [""])),
        "volume": msg.get("volume", ""), "number": msg.get("issue", ""),
        "pages": msg.get("page", ""), "doi": msg.get("DOI", doi),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Moteur de citations BibTeX.")
    ap.add_argument("fichier", nargs="?", help="fichier .bib, ou - pour stdin")
    ap.add_argument("--to", choices=list(FORMATS), default="apa")
    ap.add_argument("--dedupe", action="store_true")
    ap.add_argument("--doi", help="recupere une entree depuis Crossref (reseau)")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--exiger-ancres", action="store_true",
                     help="code de sortie 1 si une entree n'a pas d'ancre exploitable")
    ap.add_argument("--bascule", nargs=2, metavar=("ANCIEN", "NOUVEAU"), choices=list(FORMATS),
                     help="reemet la meme bibliographie (memes entrees) d'un format vers un "
                          "autre, avec un compte de references avant et apres")
    a = ap.parse_args(argv)
    if a.doi:
        e = fetch_doi(a.doi)
        print(format_apa(e) if a.to == "apa" else format_vancouver(e))
        return 0
    texte = sys.stdin.read() if a.fichier in (None, "-") else open(a.fichier, encoding="utf-8").read()
    entrees = parser_bibtex(texte)
    doublons = []
    if a.dedupe:
        entrees, doublons = dedupe(entrees)
    ancrage = rapport_ancrage(entrees)

    if a.bascule:
        ancien, nouveau = a.bascule
        refs_ancien = [FORMATS[ancien](e) for e in entrees]
        refs_nouveau = [FORMATS[nouveau](e) for e in entrees]
        if a.format == "json":
            print(json.dumps({
                "format_ancien": ancien, "format_nouveau": nouveau,
                "references_ancien": refs_ancien, "references_nouveau": refs_nouveau,
                "compte_ancien": len(refs_ancien), "compte_nouveau": len(refs_nouveau),
                "doublons": doublons, "ancrage": ancrage,
            }, ensure_ascii=False, indent=2))
        else:
            print(f"Bascule {ancien} -> {nouveau} "
                  f"(compte inchange : {len(refs_ancien)} avant, {len(refs_nouveau)} apres)\n")
            for i, r in enumerate(refs_nouveau, 1):
                print(_ligne(r, nouveau, i))
            if doublons:
                print(f"\nDoublons ecartes : {doublons}")
        if a.exiger_ancres and ancrage["sans_ancre"]:
            return 1
        return 0

    refs = [FORMATS[a.to](e) for e in entrees]
    if a.format == "json":
        print(json.dumps({"references": refs, "doublons": doublons, "ancrage": ancrage},
                          ensure_ascii=False, indent=2))
    else:
        for i, r in enumerate(refs, 1):
            print(_ligne(r, a.to, i))
        if doublons:
            print(f"\nDoublons ecartes : {doublons}")
        if ancrage["sans_ancre"]:
            print(f"\nEntrees sans ancre exploitable (signal) : {ancrage['sans_ancre']}")
    if a.exiger_ancres and ancrage["sans_ancre"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
