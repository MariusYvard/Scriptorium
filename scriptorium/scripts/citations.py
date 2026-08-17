#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Portions adaptees du projet openscience (Synthetic Sciences, InkVell Inc.),
Apache-2.0, github.com/synthetic-sciences/openscience. Modifications Marius
Yvard, MIT.

Moteur de citations pour Scriptorium : BibTeX, formatage, deduplication.

Lit du BibTeX, formate chaque reference en APA 7, Vancouver, Chicago
(auteur-date), MLA (9e ed., auteur-page) ou IEEE (numerique), deduplique par
DOI puis par titre. La recuperation des metadonnees a partir d'un DOI
(Crossref), d'un PMID (NCBI E-utilities) ou d'un identifiant arXiv (API Atom)
est optionnelle et reseau (--doi, --pmid, --arxiv). Tout le reste est hors
ligne.

Ancre par citation : le champ BibTeX optionnel `annote` (priorite) ou `note`
porte soit une citation exacte de 25 mots au plus, soit une localisation
(page, section, paragraphe). Une entree sans ce champ, ou dont le champ ne
correspond a aucun des deux formats, est signalee sans ancre (--exiger-ancres
pour en faire une erreur bloquante, sinon un simple signal).

Ancrage a trois couches (references/integrite-sources.md) : la couche 1
(existence de la reference) reste couverte par verify-sources.py. La couche 2
(qualifier_ancre, rapport_qualification) qualifie une ancre en type ferme
(citation, page, structure, horodatage, aucune) et nomme les formes mal
formees (page nulle ou negative, plage inversee, citation trop longue,
guillemets non fermes) comme un defaut plutot que de les faire passer pour
une ancre valide. La couche 3 (auditer_fidelite, --auditer-fidelite) mesure
l'ecart entre une affirmation et le texte de l'ancre qui la soutient (montee
en force modale, chiffre orphelin, generalisation retiree) sans jamais
emettre de verdict de fidelite global : ce jugement n'est pas mecanisable et
reste consultatif.

Bascule de format : --bascule ANCIEN NOUVEAU reemet la meme bibliographie
(le fichier .bib est la seule source de verite) dans un nouveau format tout
en affichant l'ancien, avec un compte de references avant et apres (doit
rester identique : aucune entree n'est perdue par un changement de format,
puisque les deux ne sont que deux rendus de la meme liste analysee).

Resolution d'identifiant vers BibTeX : --pmid interroge efetch.fcgi (NCBI
E-utilities, XML, endpoint deja cite dans references/veille.md) ; --arxiv
interroge l'API Atom d'arXiv (export.arxiv.org/api/query, endpoint verifie le
2026-07-10). Les deux emettent une entree BibTeX litteral (comme --doi mais
au format texte pret a coller, --format json pour le dict brut) plutot qu'une
reference deja mise en forme APA/Vancouver.

Validation de champs (--valider) : chaque entree est confrontee a la liste
des champs obligatoires de son type BibTeX (article, book, inproceedings,
incollection, phdthesis, mastersthesis, techreport, misc). Un type non
reconnu est signale, pas silencieusement ignore.

Tri stable (--trier cle|annee|auteur) : sorted() de la bibliotheque standard
est un tri stable (Timsort), les entrees a valeur egale ou vide gardent leur
ordre d'origine entre elles.

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
    python3 citations.py FICHIER.bib --valider [--trier cle|annee|auteur]
    python3 citations.py --doi 10.xxxx/yyyy       (reseau, recupere une entree)
    python3 citations.py --pmid 12345678          (reseau, vers BibTeX)
    python3 citations.py --arxiv 1706.03762       (reseau, vers BibTeX)
    python3 citations.py FICHIER.bib --exiger-ancres
    python3 citations.py FICHIER.bib --auditer-fidelite DOCUMENT.md
Module importable : parser_bibtex(texte) ; format_apa(e) ; format_vancouver(e) ;
format_chicago(e) ; format_mla(e) ; format_ieee(e) ; FORMATS (dict nom -> fonction) ;
dedupe(entrees) ; ancre_de(entree) ; qualifier_ancre(valeur) ;
rapport_qualification(entrees) ; extraire_couples(document_md, entrees) ;
auditer_fidelite(document_md, entrees) ; valider_entree(e) ;
rapport_validation(entrees) ; trier_entrees(entrees, cle) ; fetch_doi(doi) ;
fetch_pmid(pmid) ; fetch_arxiv(id) ; entree_vers_bibtex(e).
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

# Couche 2 (ancrage a trois couches, integrite-sources.md) : qualification
# stricte d'une ancre en types fermes. Plus stricte que LOCATEUR_RE ci-dessus
# (qui ne fait que reperer un indice de localisation dans un texte libre) :
# ces expressions valident la forme entiere du champ et distinguent un
# defaut nomme d'une ancre valide.
PAGE_RE = re.compile(r'(?i)^pp?\.\s*(-?\d+)(?:\s*[-–]\s*(-?\d+))?$')
STRUCTURE_RE = re.compile(
    r'(?i)^(section|tableau|figure|annexe|paragraphe)\s+([a-z0-9]+(?:\.[0-9]+)*)$')
HORODATAGE_RE = re.compile(r'^(?:\d{1,2}:)?[0-5]?\d:[0-5]\d$')

# Champs BibTeX obligatoires par type d'entree. Adapte de required_fields,
# validate_citations.py (openscience). Cas particulier : "book" accepte
# "editor" a la place de "author" (voir valider_entree).
REQUIS_PAR_TYPE = {
    "article": ["author", "title", "journal", "year"],
    "book": ["title", "publisher", "year"],
    "inproceedings": ["author", "title", "booktitle", "year"],
    "incollection": ["author", "title", "booktitle", "publisher", "year"],
    "phdthesis": ["author", "title", "school", "year"],
    "mastersthesis": ["author", "title", "school", "year"],
    "techreport": ["author", "title", "institution", "year"],
    "misc": ["title", "year"],
}

# Ordre de champs pour la serialisation BibTeX litterale (entree_vers_bibtex).
CHAMPS_BIBTEX_ORDRE = ["author", "editor", "title", "journal", "booktitle",
                       "year", "volume", "number", "pages", "publisher",
                       "school", "institution", "doi", "url", "note"]


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


def qualifier_ancre(valeur):
    """Couche 2 (localisation) : qualifie une ancre brute (champ annote ou
    note d'une entree BibTeX, ou toute chaine equivalente) en un type ferme :
    citation, page, structure, horodatage, aucune, ou defaut si la forme est
    reconnaissable mais mal formee. Une ancre mal formee (page nulle ou
    negative, plage inversee, citation de plus de 25 mots, guillemets non
    fermes, ou une forme qui ne correspond a aucun des quatre types valides)
    n'est jamais reclassee en ancre valide : elle porte le type "defaut" et
    un code dans la cle "defaut". Plus strict que ancre_de/LOCATEUR_RE
    ci-dessus (repli historique, conserve pour --exiger-ancres) : ici la
    forme entiere du champ doit correspondre, pas seulement en contenir un
    indice."""
    valeur = (valeur or "").strip()
    if not valeur:
        return {"type": "aucune", "defaut": None, "valeur": None}

    if valeur.count('"') % 2 == 1:
        return {"type": "defaut", "defaut": "guillemets_non_fermes", "valeur": valeur}

    m_cit = re.match(r'^"(.*)"$', valeur, re.S)
    if m_cit:
        texte = m_cit.group(1).strip()
        if not texte:
            return {"type": "defaut", "defaut": "citation_vide", "valeur": valeur}
        n_mots = len(texte.split())
        if n_mots > SEUIL_MOTS_CITATION:
            return {"type": "defaut", "defaut": "citation_trop_longue",
                    "valeur": valeur, "mots": n_mots}
        return {"type": "citation", "valeur": texte, "mots": n_mots}

    m_page = PAGE_RE.match(valeur)
    if m_page:
        debut = int(m_page.group(1))
        fin = int(m_page.group(2)) if m_page.group(2) else None
        if debut <= 0 or (fin is not None and fin <= 0):
            return {"type": "defaut", "defaut": "page_invalide", "valeur": valeur}
        if fin is not None and fin < debut:
            return {"type": "defaut", "defaut": "plage_inversee", "valeur": valeur}
        return {"type": "page", "valeur": valeur, "debut": debut, "fin": fin}

    if STRUCTURE_RE.match(valeur):
        return {"type": "structure", "valeur": valeur}

    if HORODATAGE_RE.match(valeur):
        return {"type": "horodatage", "valeur": valeur}

    return {"type": "defaut", "defaut": "forme_non_reconnue", "valeur": valeur}


def rapport_qualification(entrees):
    """Couche 2 sur une bibliographie entiere : qualifier_ancre applique au
    champ annote (priorite) ou note de chaque entree, meme convention de
    priorite que ancre_de. Retourne le detail par cle et la liste des cles
    dont l'ancre est un defaut nomme (jamais confondu avec une ancre absente,
    qui est un type distinct : "aucune")."""
    detail = []
    defauts = []
    for e in entrees:
        brute = e.get("annote") or e.get("note") or ""
        q = qualifier_ancre(brute)
        detail.append({"cle": e.get("_cle"), **q})
        if q["type"] == "defaut":
            defauts.append(e.get("_cle"))
    return {"detail": detail, "defauts": defauts}


# Couche 3 (fidelite, integrite-sources.md) : lexiques fermes pour les
# signaux mecaniques mesures sur le couple affirmation-ancre. Le code ne
# juge jamais si l'affirmation est vraie : il mesure un ecart de forme entre
# le texte de l'ancre (citation exacte uniquement, seul type d'ancre qui
# porte du texte source comparable) et le texte de l'affirmation, et laisse
# le jugement au modele ou au relecteur.
MODALITE_PRUDENTE = {
    "suggere", "suggerent", "est associe", "sont associes", "semble",
    "semblent", "pourrait", "pourraient", "tend a", "tendent a",
    "dans cet echantillon", "dans cette etude", "preliminaire", "possible",
    "eventuellement", "dans certains cas",
}
MODALITE_FORTE = {
    "demontre", "demontrent", "prouve", "prouvent", "cause", "causent",
    "toujours", "jamais", "garantit", "garantissent", "systematiquement",
    "universellement", "quel que soit", "sans aucun doute",
    "de maniere definitive",
}
PORTEE_MARQUEURS = {
    "echantillon", "cohorte", "population", "dans cette etude",
    "dans cet echantillon", "parmi les participants", "chez les patients",
    "dans ce groupe", "sur ce panel",
}
GENERALISATION_MARQUEURS = {
    "tous", "toutes", "tout le monde", "universellement", "systematiquement",
    "en general", "quel que soit", "dans tous les cas", "partout",
}
NUM_RE = re.compile(r'\d[\d.,]*\s?%?')
MARQUEUR_CITATION_RE = re.compile(r'([^.!?\n]*[.!?])\s*\[([\w:-]+)\]')


def _sans_accents(texte):
    """Normalisation minimale (NFKD, bibliotheque standard unicodedata) pour
    une comparaison de lexique insensible aux accents et a la casse."""
    import unicodedata
    d = unicodedata.normalize('NFKD', texte.lower())
    return ''.join(c for c in d if not unicodedata.combining(c))


def _contient_lexique(texte, lexique):
    t = _sans_accents(texte)
    return any(mot in t for mot in lexique)


def _nombres(texte):
    """Chiffres, pourcentages et annees mentionnes dans un texte, normalises
    (virgule francaise vers point) pour comparaison ensembliste."""
    return {n.replace(' ', '').replace(',', '.').rstrip('.') for n in NUM_RE.findall(texte)}


def extraire_couples(document_md, entrees):
    """Convention de marquage : une affirmation se termine par une phrase
    (jusqu'a . ! ou ?) immediatement suivie d'un marqueur [cle_bibtex], la
    cle devant correspondre a une entree de la bibliographie fournie.
    Retourne une liste de couples {cle, affirmation, entree} ; "entree" vaut
    None si la cle ne resout vers aucune entree (signale par
    auditer_fidelite comme reference_introuvable, pas une erreur silencieuse)."""
    index = {e.get("_cle"): e for e in entrees}
    couples = []
    for m in MARQUEUR_CITATION_RE.finditer(document_md):
        cle = m.group(2)
        couples.append({
            "cle": cle,
            "affirmation": m.group(1).strip(),
            "entree": index.get(cle),
        })
    return couples


def auditer_fidelite(document_md, entrees):
    """Couche 3 : audit de fidelite affirmation-ancre. Pour chaque couple
    (extraire_couples), mesure trois signaux fermes quand le texte source est
    disponible (ancre de type citation uniquement) : montee en force modale
    (lexique prudent dans l'ancre, lexique fort dans l'affirmation), chiffre
    orphelin (nombre, pourcentage ou annee present dans l'affirmation et
    absent de l'ancre), generalisation retiree (portee nommee dans l'ancre,
    marqueur de generalisation dans l'affirmation sans reprise de cette
    portee). N'emet jamais de verdict global (soutenue/extrapolee/non
    verifiable/contredite) : ce jugement n'est pas mecanisable, voir
    references/integrite-sources.md. N'affecte jamais le code de sortie
    (verification consultative, CONTRIBUTING.md regle 5)."""
    rapport = []
    for c in extraire_couples(document_md, entrees):
        entree = c["entree"]
        brute = (entree.get("annote") or entree.get("note") or "") if entree else ""
        ancre = qualifier_ancre(brute)
        signaux = []
        if entree is None:
            signaux.append({"signal": "reference_introuvable", "detail": c["cle"]})
        elif ancre["type"] == "defaut":
            signaux.append({"signal": "ancre_malformee", "detail": ancre["defaut"]})

        source_texte = ancre["valeur"] if ancre["type"] == "citation" else None
        if source_texte is None:
            non_mesurable = ["montee_en_force", "chiffre_orphelin", "generalisation_retiree"]
        else:
            non_mesurable = []
            if (_contient_lexique(source_texte, MODALITE_PRUDENTE)
                    and _contient_lexique(c["affirmation"], MODALITE_FORTE)):
                signaux.append({"signal": "montee_en_force", "detail": None})

            orphelins = sorted(_nombres(c["affirmation"]) - _nombres(source_texte))
            if orphelins:
                signaux.append({"signal": "chiffre_orphelin", "detail": orphelins})

            if (_contient_lexique(source_texte, PORTEE_MARQUEURS)
                    and _contient_lexique(c["affirmation"], GENERALISATION_MARQUEURS)
                    and not _contient_lexique(c["affirmation"], PORTEE_MARQUEURS)):
                signaux.append({"signal": "generalisation_retiree", "detail": None})

        rapport.append({
            "cle": c["cle"], "affirmation": c["affirmation"], "ancre": ancre,
            "signaux": signaux, "non_mesurable": non_mesurable,
        })
    return rapport


def valider_entree(e):
    """Confronte une entree a la liste des champs obligatoires de son type
    (REQUIS_PAR_TYPE). Cas particulier : "book" accepte "editor" a la place
    de "author" (une monographie dirigee n'a pas toujours d'auteur unique).
    Un type hors de la table est signale non reconnu, jamais ignore en
    silence."""
    typ = e.get("_type", "misc")
    if typ not in REQUIS_PAR_TYPE:
        return {"cle": e.get("_cle"), "type": typ, "manquants": [], "type_reconnu": False}
    manquants = []
    for champ in REQUIS_PAR_TYPE[typ]:
        if champ == "author" and typ == "book":
            if not e.get("author") and not e.get("editor"):
                manquants.append("author ou editor")
            continue
        if not e.get(champ):
            manquants.append(champ)
    return {"cle": e.get("_cle"), "type": typ, "manquants": manquants, "type_reconnu": True}


def rapport_validation(entrees):
    """Rapport de validation par entree : champs obligatoires manquants par
    type BibTeX (REQUIS_PAR_TYPE), et types non reconnus par la table."""
    detail = [valider_entree(e) for e in entrees]
    incompletes = [d["cle"] for d in detail if d["manquants"]]
    non_reconnues = [d["cle"] for d in detail if not d["type_reconnu"]]
    return {"detail": detail, "incompletes": incompletes, "types_non_reconnus": non_reconnues}


def trier_entrees(entrees, cle):
    """Tri stable sur cle|annee|auteur. sorted() (bibliotheque standard) est
    un tri stable (Timsort) : deux entrees a valeur egale ou vide gardent
    leur ordre d'origine entre elles, une entree sans la valeur demandee se
    retrouve en fin de liste plutot que d'etre placee arbitrairement."""
    def cle_tri(e):
        if cle == "annee":
            v = e.get("year", "")
        elif cle == "auteur":
            aut = _auteurs(e.get("author", ""))
            v = aut[0][0] if aut else ""
        else:
            v = e.get("_cle", "")
        return (v == "", v)
    return sorted(entrees, key=cle_tri)


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


def fetch_pmid(pmid, email=None):  # reseau, appele seulement avec --pmid
    """Resout un PMID via NCBI E-utilities (efetch.fcgi, XML), endpoint deja
    cite dans references/veille.md. Retourne le meme schema de dict que
    fetch_doi. Port stdlib (urllib + xml.etree.ElementTree) d'extract_from_pmid,
    extract_metadata.py (openscience) : la source utilise `requests`, ici
    urllib.request suffit et evite toute dependance."""
    import urllib.parse
    import urllib.request
    import xml.etree.ElementTree as ET
    pmid = pmid.strip()
    params = {"db": "pubmed", "id": pmid, "retmode": "xml", "rettype": "abstract"}
    if email:
        params["email"] = email
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"
           + urllib.parse.urlencode(params))
    with urllib.request.urlopen(url, timeout=15) as r:
        root = ET.fromstring(r.read())
    article = root.find(".//PubmedArticle")
    if article is None:
        raise ValueError(f"PMID introuvable ou reponse vide : {pmid}")
    art = article.find(".//Article")
    journal = art.find(".//Journal") if art is not None else None
    auteurs = []
    for a in article.findall(".//AuthorList/Author"):
        nom = a.findtext("LastName", "")
        prenom = a.findtext("ForeName", "")
        if nom:
            auteurs.append(f"{nom}, {prenom}" if prenom else nom)
    doi = ""
    for aid in article.findall(".//ArticleIdList/ArticleId"):
        if aid.get("IdType") == "doi":
            doi = aid.text or ""
    annee = journal.findtext(".//JournalIssue/PubDate/Year", "") if journal is not None else ""
    if not annee and journal is not None:
        medline_date = journal.findtext(".//JournalIssue/PubDate/MedlineDate", "") or ""
        m = re.search(r"\d{4}", medline_date)
        annee = m.group() if m else ""
    return {
        "_type": "article", "_cle": f"pmid_{pmid}",
        "author": " and ".join(auteurs),
        "title": art.findtext(".//ArticleTitle", "Sans titre") if art is not None else "Sans titre",
        "year": annee,
        "journal": journal.findtext(".//Title", "") if journal is not None else "",
        "volume": journal.findtext(".//JournalIssue/Volume", "") if journal is not None else "",
        "number": journal.findtext(".//JournalIssue/Issue", "") if journal is not None else "",
        "pages": art.findtext(".//Pagination/MedlinePgn", "") if art is not None else "",
        "doi": doi, "pmid": pmid,
    }


def fetch_arxiv(arxiv_id):  # reseau, appele seulement avec --arxiv
    """Resout un identifiant arXiv via l'API Atom (export.arxiv.org/api/query),
    endpoint verifie le 2026-07-10 (reponse Atom valide sur un identifiant
    connu). Retourne le meme schema de dict que fetch_doi. Port stdlib
    (urllib + xml.etree.ElementTree) d'extract_from_arxiv, extract_metadata.py
    (openscience). Type "article" si un DOI de publication existe (version
    revue parue), sinon "misc" avec la reference arXiv en guise de venue."""
    import urllib.parse
    import urllib.request
    import xml.etree.ElementTree as ET
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    aid = arxiv_id.strip()
    for prefixe in ("arXiv:", "arxiv:"):
        if aid.startswith(prefixe):
            aid = aid[len(prefixe):]
    url = ("http://export.arxiv.org/api/query?"
           + urllib.parse.urlencode({"id_list": aid, "max_results": 1}))
    with urllib.request.urlopen(url, timeout=15) as r:
        root = ET.fromstring(r.read())
    entry = root.find("atom:entry", ns)
    if entry is None:
        raise ValueError(f"Identifiant arXiv introuvable : {arxiv_id}")
    titre = " ".join((entry.findtext("atom:title", "", ns) or "").split())
    auteurs = " and ".join(
        (a.findtext("atom:name", "", ns) or "") for a in entry.findall("atom:author", ns))
    publie = entry.findtext("atom:published", "", ns) or ""
    annee = publie[:4] if publie else ""
    doi_elem = entry.find("arxiv:doi", ns)
    doi = doi_elem.text if doi_elem is not None and doi_elem.text else ""
    ref_elem = entry.find("arxiv:journal_ref", ns)
    ref = ref_elem.text if ref_elem is not None and ref_elem.text else ""
    return {
        "_type": "article" if doi else "misc", "_cle": f"arxiv_{aid}",
        "author": auteurs, "title": titre or "Sans titre", "year": annee,
        "journal": ref or ("" if doi else f"arXiv:{aid}"),
        "volume": "", "number": "", "pages": "", "doi": doi, "arxiv": aid,
    }


def entree_vers_bibtex(e, cle=None):
    """Serialise un dict d'entree (meme forme que fetch_doi/fetch_pmid/
    fetch_arxiv) en texte BibTeX litteral, pret a coller dans un fichier
    .bib. Adapte de metadata_to_bibtex, extract_metadata.py (openscience)."""
    cle = cle or e.get("_cle") or "entree"
    typ = e.get("_type", "misc")
    lignes = [f"@{typ}{{{cle},"]
    for champ in CHAMPS_BIBTEX_ORDRE:
        valeur = e.get(champ)
        if valeur:
            lignes.append(f"  {champ} = {{{valeur}}},")
    if lignes[-1].endswith(","):
        lignes[-1] = lignes[-1][:-1]
    lignes.append("}")
    return "\n".join(lignes)


def main(argv=None):
    # Une console Windows en page de code heritee ne sait pas encoder tout ce
    # qu'un index renvoie (titre en japonais, tiret long, guillemet courbe).
    # Sans garde, l'impression leve UnicodeEncodeError et la commande echoue
    # alors que la mesure est juste : le caractere se degrade, jamais le
    # resultat. Rien n'est reconfigure quand la sortie est deja detournee.
    for _flux in (sys.stdout, sys.stderr):
        try:
            _flux.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description="Moteur de citations BibTeX.")
    ap.add_argument("fichier", nargs="?", help="fichier .bib, ou - pour stdin")
    ap.add_argument("--to", choices=list(FORMATS), default="apa")
    ap.add_argument("--dedupe", action="store_true")
    ap.add_argument("--doi", help="recupere une entree depuis Crossref (reseau)")
    ap.add_argument("--pmid", help="recupere une entree depuis PubMed E-utilities, vers BibTeX (reseau)")
    ap.add_argument("--arxiv", help="recupere une entree depuis l'API arXiv, vers BibTeX (reseau)")
    ap.add_argument("--email", help="email transmis a NCBI E-utilities par courtoisie (optionnel, --pmid)")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--exiger-ancres", action="store_true",
                     help="code de sortie 1 si une entree n'a pas d'ancre exploitable")
    ap.add_argument("--auditer-fidelite", metavar="DOCUMENT.md",
                     help="couche 3 : audit de fidelite affirmation-ancre du document Markdown "
                          "contre la bibliographie du fichier .bib fourni en argument "
                          "positionnel ; convention [cle_bibtex] apres la phrase citee ; "
                          "consultatif, code de sortie toujours 0")
    ap.add_argument("--valider", action="store_true",
                     help="rapport des champs BibTeX obligatoires manquants, par type d'entree")
    ap.add_argument("--trier", choices=["cle", "annee", "auteur"],
                     help="tri stable des entrees avant formatage")
    ap.add_argument("--bascule", nargs=2, metavar=("ANCIEN", "NOUVEAU"), choices=list(FORMATS),
                     help="reemet la meme bibliographie (memes entrees) d'un format vers un "
                          "autre, avec un compte de references avant et apres")
    a = ap.parse_args(argv)

    if a.pmid:
        e = fetch_pmid(a.pmid, email=a.email)
        print(json.dumps(e, ensure_ascii=False, indent=2) if a.format == "json"
              else entree_vers_bibtex(e))
        return 0
    if a.arxiv:
        e = fetch_arxiv(a.arxiv)
        print(json.dumps(e, ensure_ascii=False, indent=2) if a.format == "json"
              else entree_vers_bibtex(e))
        return 0
    if a.doi:
        e = fetch_doi(a.doi)
        print(format_apa(e) if a.to == "apa" else format_vancouver(e))
        return 0

    texte = sys.stdin.read() if a.fichier in (None, "-") else open(a.fichier, encoding="utf-8").read()
    entrees = parser_bibtex(texte)

    if a.auditer_fidelite:
        doc_texte = open(a.auditer_fidelite, encoding="utf-8").read()
        rapport = auditer_fidelite(doc_texte, entrees)
        if a.format == "json":
            print(json.dumps({"audit_fidelite": rapport}, ensure_ascii=False, indent=2))
        elif not rapport:
            print("Audit de fidelite : aucun couple affirmation-ancre repere "
                  "(convention : phrase suivie de [cle_bibtex]).")
        else:
            for r in rapport:
                print(f"[{r['cle']}] {r['affirmation']}")
                defaut = f" ({r['ancre']['defaut']})" if r['ancre'].get('defaut') else ""
                print(f"  ancre : {r['ancre']['type']}{defaut}")
                if r["signaux"]:
                    for s in r["signaux"]:
                        detail = f" -- {s['detail']}" if s['detail'] else ""
                        print(f"  signal : {s['signal']}{detail}")
                else:
                    print("  signal : aucun")
                if r["non_mesurable"]:
                    print("  non mesurable (pas de texte source dans l'ancre) : "
                          + ", ".join(r["non_mesurable"]))
                print()
        return 0  # couche 3 consultative : n'affecte jamais le code de sortie

    doublons = []
    if a.dedupe:
        entrees, doublons = dedupe(entrees)
    if a.trier:
        entrees = trier_entrees(entrees, a.trier)
    ancrage = rapport_ancrage(entrees)
    validation = rapport_validation(entrees) if a.valider else None

    if a.bascule:
        ancien, nouveau = a.bascule
        refs_ancien = [FORMATS[ancien](e) for e in entrees]
        refs_nouveau = [FORMATS[nouveau](e) for e in entrees]
        if a.format == "json":
            sortie = {
                "format_ancien": ancien, "format_nouveau": nouveau,
                "references_ancien": refs_ancien, "references_nouveau": refs_nouveau,
                "compte_ancien": len(refs_ancien), "compte_nouveau": len(refs_nouveau),
                "doublons": doublons, "ancrage": ancrage,
            }
            if validation is not None:
                sortie["validation"] = validation
            print(json.dumps(sortie, ensure_ascii=False, indent=2))
        else:
            print(f"Bascule {ancien} -> {nouveau} "
                  f"(compte inchange : {len(refs_ancien)} avant, {len(refs_nouveau)} apres)\n")
            for i, r in enumerate(refs_nouveau, 1):
                print(_ligne(r, nouveau, i))
            if doublons:
                print(f"\nDoublons ecartes : {doublons}")
            if validation is not None and validation["incompletes"]:
                print(f"\nChamps obligatoires manquants ({len(validation['incompletes'])} entree(s)) :")
                for d in validation["detail"]:
                    if d["manquants"]:
                        print(f"  {d['cle']} ({d['type']}) : {', '.join(d['manquants'])}")
            if validation is not None and validation["types_non_reconnus"]:
                print(f"\nType BibTeX non reconnu (non valide) : {validation['types_non_reconnus']}")
        probleme = bool(a.exiger_ancres and ancrage["sans_ancre"])
        probleme = probleme or bool(validation is not None and validation["incompletes"])
        return 1 if probleme else 0

    refs = [FORMATS[a.to](e) for e in entrees]
    if a.format == "json":
        sortie = {"references": refs, "doublons": doublons, "ancrage": ancrage}
        if validation is not None:
            sortie["validation"] = validation
        print(json.dumps(sortie, ensure_ascii=False, indent=2))
    else:
        for i, r in enumerate(refs, 1):
            print(_ligne(r, a.to, i))
        if doublons:
            print(f"\nDoublons ecartes : {doublons}")
        if ancrage["sans_ancre"]:
            print(f"\nEntrees sans ancre exploitable (signal) : {ancrage['sans_ancre']}")
        if validation is not None and validation["incompletes"]:
            print(f"\nChamps obligatoires manquants ({len(validation['incompletes'])} entree(s)) :")
            for d in validation["detail"]:
                if d["manquants"]:
                    print(f"  {d['cle']} ({d['type']}) : {', '.join(d['manquants'])}")
        if validation is not None and validation["types_non_reconnus"]:
            print(f"\nType BibTeX non reconnu (non valide) : {validation['types_non_reconnus']}")
    probleme = bool(a.exiger_ancres and ancrage["sans_ancre"])
    probleme = probleme or bool(validation is not None and validation["incompletes"])
    return 1 if probleme else 0


if __name__ == "__main__":
    sys.exit(main())
