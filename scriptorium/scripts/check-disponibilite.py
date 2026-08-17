#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Controle de la declaration de disponibilite des donnees et du code.

Une declaration de disponibilite enonce un fait verifiable, pas une
intention : un lecteur suit l'adresse donnee, un evaluateur demande le jeu,
un editeur controle que l'identifiant resout. Ce script controle la forme de
cette declaration sur le manuscrit source, avant soumission.

Ce qui est mecaniquement verifiable : la presence d'une section de
disponibilite, le regime declare par ses formulations, la presence d'un
identifiant perenne quand l'ouverture est annoncee, la presence d'une licence
quand du code est annonce, une date quand un embargo est annonce, et la
coherence entre le regime declare et ce que la section contient reellement.

Ce script lit une declaration, il ne la valide pas contre le monde : il ne
resout aucun identifiant, n'ouvre aucun depot et ne verifie aucune
autorisation. Meme partage que check-fuites.py, qui inspecte sans nettoyer.

Chaque constat porte une confiance, comme dans check-fuites.py, parce qu'une
annonce contredite par la section et une annonce incomplete ne disent pas la
meme chose :
  confirme    la section contredit ce qu'elle annonce, ou l'element exige par
              le regime declare est absent de bout en bout.
  probable    l'element existe sous une forme qui ne suffit pas (licence
              evoquee sans etre nommee, depot de developpement sans version
              figee).
  informatif  un etat present sans faute a corriger.
  douteux     le constat a de bonnes chances d'etre un faux positif, il est
              rapporte pour ne rien taire, pas pour etre corrige.

Verdict ferme sur cinq valeurs. Consultatif par defaut.

Usage :
  python3 check-disponibilite.py FICHIER.md [--format text|json] [--strict]

Module importable : reperer_section, detecter_regimes, identifiants_perennes,
analyser, rapport_texte.
"""
import argparse
import json
import os
import re
import sys
import unicodedata

CONFIRME, PROBABLE, INFORMATIF, DOUTEUX = (
    "confirme", "probable", "informatif", "douteux")
ORDRE_CONFIANCE = {CONFIRME: 0, PROBABLE: 1, INFORMATIF: 2, DOUTEUX: 3}

# Liste fermee : un regime nomme ce que la declaration promet pour une
# categorie de materiel. Un article peut en combiner deux (donnees ouvertes,
# code sur demande), ce qui n'est pas une faute.
REGIMES = ("depot-ouvert", "sur-demande", "embargo", "restriction-legale",
           "donnees-de-tiers", "aucune-donnee")

LIBELLE_REGIME = {
    "depot-ouvert": "dépôt public ouvert",
    "sur-demande": "sur demande motivée",
    "embargo": "embargo",
    "restriction-legale": "non partageable pour raison légale",
    "donnees-de-tiers": "données de tiers",
    "aucune-donnee": "aucune donnée nouvelle",
}

VERDICTS = ("declaration absente", "declaration incoherente",
            "regime non identifie", "declaration a completer",
            "declaration conforme")

LIMITE = ("Ce rapport contrôle la forme d'une déclaration, il ne la valide "
          "pas contre le monde : aucun identifiant n'est résolu, aucun dépôt "
          "n'est ouvert, aucune autorisation n'est vérifiée.")

# Titres de section rencontres en francais et en anglais. La detection porte
# sur un titre markdown, pas sur une phrase du corps : une declaration qui
# n'est pas une section ne se retrouve pas a la relecture.
MOTIF_TITRE = re.compile(
    r"disponibilite\s+(?:des\s+donnees|du\s+code|des\s+donnees\s+et\s+du\s+code)"
    r"|acces\s+aux\s+donnees"
    r"|partage\s+des\s+donnees"
    r"|donnees\s+et\s+code"
    r"|data\s+(?:and\s+code\s+)?availability"
    r"|code\s+(?:and\s+data\s+)?availability"
    r"|availability\s+of\s+(?:data|code|materials)"
    r"|data\s+sharing\s+statement"
    r"|data\s+access\s+statement", re.I)

MOTIF_ENTETE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")

# Formulations qui trahissent un regime. Les motifs travaillent sur un texte
# minuscule et sans accents, pour qu'une declaration tombe sur la meme regle
# qu'elle soit ecrite avec ou sans diacritiques.
MOTIFS_REGIME = {
    "depot-ouvert": (
        r"depose(?:e|s|es)?\s+(?:dans|sur|aupres)", r"\bdeposited\s+in\b",
        r"\bopenly\s+available\b", r"\bpublicly\s+available\b",
        r"\bfreely\s+available\b", r"\bacces\s+(?:ouvert|libre)\b",
        r"\ben\s+libre\s+acces\b", r"\bpubliquement\s+accessibles?\b",
        r"\barchive(?:e|s|es)?\s+dans\b", r"\barchived\s+in\b",
        r"\bopen\s+repositor", r"\bdepot\s+public\b",
        r"\bzenodo\b", r"\bdryad\b", r"\bfigshare\b", r"\bosf\.io\b",
        r"\bpangaea\b", r"\bgenbank\b", r"\bdataverse\b"),
    "sur-demande": (
        r"\bsur\s+(?:simple\s+)?demande\b", r"\bupon\s+request\b",
        r"\bon\s+reasonable\s+request\b", r"\bon\s+request\b",
        r"\bauteur\s+correspondant\b", r"\bcorresponding\s+author\b",
        r"\bavailable\s+from\s+the\s+authors?\b"),
    "embargo": (r"\bembargo",),
    "restriction-legale": (
        r"\bne\s+(?:peuvent|peut)\s+pas\s+etre\s+partage",
        r"\bcannot\s+be\s+(?:shared|made\s+publicly)",
        r"\bnot\s+publicly\s+available\b", r"\bne\s+sont\s+pas\s+publiques\b",
        r"\bdonnees\s+a\s+caractere\s+personnel\b", r"\bpersonal\s+data\b",
        r"\bconfidentiel", r"\bconfidential", r"\bsecret\s+(?:industriel|d)",
        r"\btrade\s+secret", r"\bespece\s+protegee\b",
        r"\bprotected\s+species\b", r"\brestriction",
        r"\bdonnees\s+sensibles\b", r"\bsensitive\s+data\b"),
    "donnees-de-tiers": (
        r"\bdonnees\s+de\s+tiers\b", r"\bthird[- ]party\s+data\b",
        r"\bobtenues?\s+aupres\s+d", r"\bobtained\s+from\b",
        r"\bsous\s+licence\s+de\b", r"\bunder\s+licen[cs]e\s+from\b",
        r"\bne\s+sont\s+pas\s+autorises\s+a\s+(?:les\s+)?rediffuser\b",
        r"\bnot\s+permitted\s+to\s+redistribute\b",
        r"\bdetenteur\b", r"\bdata\s+(?:owner|holder)\b"),
    "aucune-donnee": (
        r"\baucune\s+donnee\s+nouvelle\b", r"\bno\s+new\s+data\b",
        r"\bn.a\s+produit\s+aucune\s+donnee\b",
        r"\bno\s+datasets?\s+were\s+(?:generated|created)\b",
        r"\bdata\s+sharing\s+is\s+not\s+applicable\b",
        r"\bpas\s+de\s+donnees\s+nouvelles\b"),
}
MOTIFS_REGIME = {cle: tuple(re.compile(m) for m in motifs)
                 for cle, motifs in MOTIFS_REGIME.items()}

# Identifiants perennes reconnus. Une adresse https ordinaire n'en est pas un :
# c'est le point que ce controle sert a rendre visible.
MOTIFS_IDENTIFIANT = (
    ("doi", re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")),
    ("handle", re.compile(r"\bhdl[:/]\s*\d+(?:\.\d+)*/\S+"
                          r"|hdl\.handle\.net/\S+", re.I)),
    ("ark", re.compile(r"\bark:/?\d+/\S+", re.I)),
    ("swhid", re.compile(r"\bswh:1:(?:cnt|dir|rev|rel|snp):[0-9a-f]{40}", re.I)),
    ("accession", re.compile(
        r"\b(?:PRJ(?:NA|EB|DB)\d+|SAM(?:N|EA|D)\d+|GSE\d+|GSM\d+"
        r"|[SED]R[PRXS]\d+|E-[A-Z]{4}-\d+|PXD\d{6})\b")),
    ("pdb", re.compile(r"\bPDB\s*(?:ID|code|entry)?\s*:?\s*[0-9][A-Za-z0-9]{3}\b",
                       re.I)),
)

# Mention de DOI dont la valeur ne suit pas la syntaxe. Un "doi:" suivi d'une
# valeur invalide se lit comme un identifiant alors qu'il n'en est pas un.
MOTIF_MENTION_DOI = re.compile(
    r"(?:\bdoi\s*[:=]\s*|https?://(?:dx\.)?doi\.org/)(\S+)", re.I)
MOTIF_DOI_VALIDE = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")

MOTIF_DATE = re.compile(
    r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/\d{4}\b"
    r"|\b(?:janvier|fevrier|mars|avril|mai|juin|juillet|aout|septembre|"
    r"octobre|novembre|decembre|january|february|march|april|may|june|july|"
    r"august|september|october|november|december)\s+\d{4}\b"
    r"|\b(?:19|20)\d{2}\b")

MOTIF_LICENCE_NOMMEE = re.compile(
    r"\b(?:MIT|BSD(?:[- ]?\d)?|Apache(?:[- ]?2(?:\.0)?)?"
    r"|(?:L|A)?GPL(?:[- ]?v?\d(?:\.\d)?)?|MPL(?:[- ]?2(?:\.0)?)?|EUPL"
    r"|CeCILL(?:-[ABC])?|ISC|Unlicense|zlib|Artistic|CC0"
    r"|CC[- ]BY(?:[- ](?:SA|NC|ND|NC[- ]SA|NC[- ]ND))?"
    r"|ODbL|PDDL|Creative\s+Commons|domaine\s+public|public\s+domain)\b", re.I)
MOTIF_MOT_LICENCE = re.compile(r"\blicen[cs]e", re.I)

# Le code se reconnait a ce qu'il est nomme, pas a la presence d'un lien.
MOTIF_CODE = re.compile(
    r"\bcode\b|\bscripts?\b|\blogiciel\b|\bsoftware\b|\bnotebooks?\b"
    r"|\bprogrammes?\b|\bpipelines?\b|\bcarnets?\s+de\s+calcul\b", re.I)
MOTIF_HEBERGEUR_CODE = re.compile(
    r"\b(?:github\.com|gitlab\.com|bitbucket\.org|sourceforge\.net"
    r"|codeberg\.org|framagit\.org)\b", re.I)
MOTIF_VERSION_FIGEE = re.compile(
    r"/releases/tag/|\btags?\b|\betiquette\s+de\s+version\b|\bcommit\b"
    r"|\bversion\s+v?\d|\bv\d+\.\d+|\b[0-9a-f]{7,40}\b|\brelease\b", re.I)

# Elements que "sur demande" doit porter pour cesser d'etre une formule
# (criteres ICMJE, voir references/disponibilite.md section 4).
MOTIF_CONTACT = re.compile(
    r"[\w.+-]+@[\w-]+\.[\w.]+|\bauteur\s+correspondant\b"
    r"|\bcorresponding\s+author\b|\bcomite\b|\bcommittee\b"
    r"|\bbureau\s+d\W?acces\b|\bdata\s+access\s+(?:committee|office)\b", re.I)
MOTIF_CRITERE = re.compile(
    r"\bmotivee\b|\breasonable\b|\bcriteres?\b|\bcriteri(?:on|a)\b"
    r"|\baccord\b|\bconvention\b|\bagreement\b|\bapprobation\b|\bapproval\b"
    r"|\bprotocole\s+d\W?acces\b|\bdata\s+use\s+agreement\b", re.I)
MOTIF_DUREE = re.compile(
    r"\bpendant\s+\w+\s+(?:mois|ans?|annees?)\b|\bfor\s+\w+\s+(?:months?|years?)\b"
    r"|\bjusqu\W?(?:au|en|a)\b|\buntil\b|\ba\s+compter\s+de\b"
    r"|\bafter\s+publication\b|\b\d+\s+(?:mois|ans|years|months)\b", re.I)

MOTIF_MOTIF_RESTRICTION = re.compile(
    r"\bdonnees\s+a\s+caractere\s+personnel\b|\bpersonal\s+data\b"
    r"|\bconfidentialite\b|\bconfidential", re.I)
MOTIF_MOTIF_RESTRICTION_2 = re.compile(
    r"\bsecret\b|\bpropriete\s+intellectuelle\b|\bintellectual\s+property\b"
    r"|\bespece\s+protegee\b|\bprotected\s+species\b|\bpatrimo"
    r"|\bethique\b|\bethics\b|\brgpd\b|\bgdpr\b|\bconsentement\b|\bconsent\b"
    r"|\bsecurite\b|\bsecurity\b|\bpatients?\b|\bparticipants?\b", re.I)

# Le detenteur d'un jeu de tiers se lit sur le texte d'origine, casse et
# accents conserves : un nom propre apres "aupres de" ou "from", une adresse
# ou un courriel. "obtained from the authors" ne nomme personne.
MOTIF_DETENTEUR = re.compile(
    r"(?:aupr[èe]s d[eu']|obtenues? de|from)\s+(?:the\s+|la\s+|le\s+|l')?"
    r"[A-ZÀ-Þ][\w'&.-]+"
    r"|https?://\S+|[\w.+-]+@[\w-]+\.[\w.]+")

# Une section de disponibilite plus courte que ce seuil ne dit rien : elle
# porte un titre, pas une declaration.
SEUIL_MOTS_SECTION = 8


def _sans_accents(texte):
    """Minuscules sans diacritiques, pour que deux graphies d'un meme mot,
    l'une accentuee et l'autre non, tombent sur le meme motif."""
    plat = unicodedata.normalize("NFD", texte.lower())
    return "".join(c for c in plat if unicodedata.category(c) != "Mn")


def _constat(regle, detail, confiance, categorie, extrait=None):
    return {"regle": regle, "detail": detail, "confiance": confiance,
            "categorie": categorie, "extrait": extrait}


def _lignes_hors_code(texte):
    """Lignes du document, celles des blocs delimites par ``` retirees.

    Un exemple de declaration cite dans un bloc de code n'est pas la
    declaration du document : le compter en ferait une, et un manuscrit qui
    montre un gabarit passerait pour un manuscrit qui declare.
    """
    dans_code = False
    sortie = []
    for i, ligne in enumerate(texte.splitlines(), 1):
        if ligne.strip().startswith("```"):
            dans_code = not dans_code
            continue
        if dans_code:
            continue
        sortie.append((i, ligne))
    return sortie


def reperer_section(texte):
    """Repere la section de disponibilite et rend son titre avec son corps.

    Le corps court du titre jusqu'au prochain titre de niveau egal ou
    superieur, ou jusqu'a la fin du document. Plusieurs sections de
    disponibilite (donnees puis code) sont fusionnees en un seul corps :
    elles repondent ensemble de la meme obligation.
    """
    lignes = _lignes_hors_code(texte)
    sections = []
    courante = None
    for numero, ligne in lignes:
        entete = MOTIF_ENTETE.match(ligne)
        if entete:
            niveau = len(entete.group(1))
            titre = entete.group(2)
            if courante and niveau <= courante["niveau"]:
                sections.append(courante)
                courante = None
            if MOTIF_TITRE.search(_sans_accents(titre)) and courante is None:
                courante = {"titre": titre.strip("# ").strip(),
                            "niveau": niveau, "ligne": numero, "corps": []}
            continue
        if courante is not None:
            courante["corps"].append(ligne)
    if courante:
        sections.append(courante)
    if not sections:
        return {"trouvee": False, "titres": [], "ligne": None, "corps": ""}
    corps = "\n".join("\n".join(s["corps"]).strip() for s in sections).strip()
    return {"trouvee": True, "titres": [s["titre"] for s in sections],
            "ligne": sections[0]["ligne"], "corps": corps}


def detecter_regimes(corps):
    """Regimes que les formulations du corps declarent, liste fermee.

    Aucun regime detecte ne vaut pas absence de declaration : la section
    existe, elle ne dit simplement pas sous quel regime elle place le
    materiel. Les deux situations restent distinctes dans le verdict.
    """
    plat = _sans_accents(corps)
    trouves = []
    for regime in REGIMES:
        if any(m.search(plat) for m in MOTIFS_REGIME[regime]):
            trouves.append(regime)
    return trouves


def identifiants_perennes(corps):
    """Identifiants perennes lisibles dans le corps, par type.

    Une adresse https ordinaire n'entre pas dans cette liste : c'est le point
    que le controle sert a rendre visible. Un lien vers un depot de
    developpement ne fige aucun etat.
    """
    trouves = []
    for nom, motif in MOTIFS_IDENTIFIANT:
        for m in motif.finditer(corps):
            trouves.append({"type": nom, "valeur": m.group(0)})
    return trouves


def _controler_ouverture(corps, ids, constats):
    """Depot ouvert annonce : l'identifiant perenne est la preuve de
    l'annonce. L'annoncer sans le donner est une incoherence, pas un oubli
    de style."""
    if not ids:
        constats.append(_constat(
            "ouverture-sans-identifiant",
            "un dépôt public ouvert est annoncé sans identifiant pérenne "
            "(DOI, handle, ARK, SWHID, numéro d'accession). Une adresse web "
            "ordinaire ne fixe rien.",
            CONFIRME, "identifiant"))
    elif not any(i["type"] in ("doi", "handle", "ark") for i in ids):
        constats.append(_constat(
            "identifiant-sans-doi",
            "l'ouverture repose sur un %s sans DOI ni handle ni ARK. "
            "Vérifier que le dépôt visé attribue bien un identifiant citable."
            % ", ".join(sorted({i["type"] for i in ids})),
            INFORMATIF, "identifiant"))
    for m in MOTIF_MENTION_DOI.finditer(corps):
        valeur = m.group(1).rstrip(".,;)]}\"'")
        if not MOTIF_DOI_VALIDE.match(valeur):
            constats.append(_constat(
                "doi-mal-forme",
                "la valeur annoncée comme DOI ne suit pas la syntaxe "
                "10.préfixe/suffixe.",
                PROBABLE, "identifiant", valeur))


def _controler_embargo(corps, constats):
    """Un embargo sans date de levee est un embargo sans fin : l'element qui
    le distingue d'un refus est justement sa date."""
    if not MOTIF_DATE.search(_sans_accents(corps)):
        constats.append(_constat(
            "embargo-sans-date",
            "un embargo est annoncé sans date de levée. Sans date, la "
            "déclaration ne se distingue pas d'un refus de partage.",
            CONFIRME, "regime"))


def _controler_demande(corps, regimes, ids, constats):
    """"Disponibles sur demande" est la formulation la moins suivie d'effet
    (references/disponibilite.md, section 1). Elle reste acceptable quand
    elle porte un contact, des criteres d'acces et une duree."""
    manques = []
    if not MOTIF_CONTACT.search(corps):
        manques.append("le contact qui décide")
    if not MOTIF_CRITERE.search(_sans_accents(corps)):
        manques.append("les critères d'accès")
    if not MOTIF_DUREE.search(_sans_accents(corps)):
        manques.append("la durée de disponibilité")
    if not manques:
        return
    # Quand le corps annonce aussi un depot ouvert identifie, la mention
    # "sur demande" porte souvent sur un element secondaire : le constat est
    # rapporte sans etre presente comme une faute a corriger.
    confiance = (DOUTEUX if "depot-ouvert" in regimes and ids else PROBABLE)
    constats.append(_constat(
        "demande-sans-conditions",
        "un accès sur demande est annoncé sans %s. Une demande sans "
        "conditions déclarées est la formulation la moins suivie d'effet."
        % ", ".join(manques),
        confiance, "regime"))


def _controler_code(corps, constats):
    """Le code obeit a des regles voisines des donnees, avec deux exigences
    propres : une licence nommee et une version figee."""
    if not MOTIF_CODE.search(corps):
        return
    if not MOTIF_LICENCE_NOMMEE.search(corps):
        if MOTIF_MOT_LICENCE.search(corps):
            constats.append(_constat(
                "licence-non-nommee",
                "du code est annoncé et une licence est évoquée sans être "
                "nommée. Nommer la licence exacte (MIT, Apache 2.0, GPL).",
                PROBABLE, "code"))
        else:
            constats.append(_constat(
                "code-sans-licence",
                "du code est annoncé sans aucune licence. Sans licence "
                "explicite, le code reste sous droit d'auteur par défaut, "
                "donc lisible et non réutilisable.",
                CONFIRME, "code"))
    if MOTIF_HEBERGEUR_CODE.search(corps) and not MOTIF_VERSION_FIGEE.search(corps):
        constats.append(_constat(
            "code-sans-version-figee",
            "le code renvoie à un dépôt de développement sans version figée "
            "(étiquette, DOI d'archive, empreinte de commit). Un dépôt se "
            "renomme, passe en privé, se réécrit.",
            PROBABLE, "code"))


def _controler_restriction(corps, constats):
    """Une restriction sans motif nomme se lit comme un refus sans raison."""
    plat = _sans_accents(corps)
    if not (MOTIF_MOTIF_RESTRICTION.search(plat)
            or MOTIF_MOTIF_RESTRICTION_2.search(plat)):
        constats.append(_constat(
            "restriction-sans-motif",
            "un partage restreint est annoncé sans motif nommé (données à "
            "caractère personnel, secret industriel, espèce protégée, "
            "patrimoine, sécurité).",
            PROBABLE, "regime"))


def _controler_tiers(corps, constats):
    """Des donnees de tiers sans detenteur nomme laissent le lecteur sans
    porte a laquelle frapper."""
    if not MOTIF_DETENTEUR.search(corps):
        constats.append(_constat(
            "tiers-sans-detenteur",
            "des données de tiers sont annoncées sans nommer leur détenteur "
            "ni la procédure d'accès auprès de lui.",
            PROBABLE, "regime"))


def analyser(texte, nom=None):
    """Controle la declaration de disponibilite d'un manuscrit.

    Prend le texte du manuscrit (comme traceability.analyser), pas un chemin :
    les cas d'eval travaillent alors sur des declarations ecrites en clair.
    N'ecrit jamais, ne corrige jamais.
    """
    section = reperer_section(texte or "")
    rapport = {"fichier": nom, "section": {"trouvee": section["trouvee"],
                                           "titres": section["titres"],
                                           "ligne": section["ligne"]},
               "regimes": [], "identifiants": [], "constats": [],
               "comptes": {}, "verdict": "declaration absente",
               "limite": LIMITE, "non_verifie": _non_verifie()}
    constats = []
    if not section["trouvee"]:
        constats.append(_constat(
            "section-absente",
            "aucune section de disponibilité des données ou du code. Les "
            "revues la réclament, les financeurs publics en font une "
            "obligation contractuelle.",
            CONFIRME, "structure"))
        return _fermer(rapport, constats)

    corps = section["corps"]
    if len(corps.split()) < SEUIL_MOTS_SECTION:
        constats.append(_constat(
            "section-vide",
            "la section de disponibilité porte un titre sans déclaration "
            "lisible (%d mots)." % len(corps.split()),
            CONFIRME, "structure"))
        return _fermer(rapport, constats)

    regimes = detecter_regimes(corps)
    ids = identifiants_perennes(corps)
    rapport["regimes"] = regimes
    rapport["identifiants"] = ids

    if not regimes:
        constats.append(_constat(
            "regime-non-identifie",
            "la section existe mais aucune formulation n'y désigne un régime "
            "connu (%s)." % ", ".join(LIBELLE_REGIME[r] for r in REGIMES),
            PROBABLE, "regime"))
    if "depot-ouvert" in regimes:
        _controler_ouverture(corps, ids, constats)
    if "embargo" in regimes:
        _controler_embargo(corps, constats)
    if "sur-demande" in regimes:
        _controler_demande(corps, regimes, ids, constats)
    if "restriction-legale" in regimes:
        _controler_restriction(corps, constats)
    if "donnees-de-tiers" in regimes:
        _controler_tiers(corps, constats)
    _controler_code(corps, constats)

    autres = [r for r in regimes if r != "aucune-donnee"]
    if "aucune-donnee" in regimes and autres:
        constats.append(_constat(
            "regimes-contradictoires",
            "la section déclare l'absence de donnée nouvelle et, dans le même "
            "corps, un régime de partage (%s)."
            % ", ".join(LIBELLE_REGIME[r] for r in autres),
            CONFIRME, "regime"))
    elif len(regimes) > 1:
        constats.append(_constat(
            "regimes-multiples",
            "la section combine %s. Cette combinaison est légitime si chaque "
            "régime nomme le matériel qu'il couvre."
            % " et ".join(LIBELLE_REGIME[r] for r in regimes),
            INFORMATIF, "regime"))
    return _fermer(rapport, constats)


def _fermer(rapport, constats):
    """Trie les constats et ferme le verdict sur cinq valeurs.

    L'ordre compte : une section absente ne se juge pas sur son contenu, une
    incoherence prime sur un regime introuvable, et un regime introuvable
    prime sur un manque de detail.
    """
    constats.sort(key=lambda c: (ORDRE_CONFIANCE[c["confiance"]], c["regle"]))
    comptes = {n: sum(1 for c in constats if c["confiance"] == n)
               for n in (CONFIRME, PROBABLE, INFORMATIF, DOUTEUX)}
    regles = {c["regle"] for c in constats}
    if "section-absente" in regles:
        verdict = "declaration absente"
    elif comptes[CONFIRME]:
        verdict = "declaration incoherente"
    elif "regime-non-identifie" in regles:
        verdict = "regime non identifie"
    elif comptes[PROBABLE]:
        verdict = "declaration a completer"
    else:
        verdict = "declaration conforme"
    rapport["constats"] = constats
    rapport["comptes"] = comptes
    rapport["verdict"] = verdict
    return rapport


def _non_verifie():
    """Ce que ce controle ne regarde pas, dit plutot que taise.

    Un rapport qui ne nomme pas ses angles morts se lit comme un quitus.
    """
    return [
        "aucun identifiant n'est résolu : un DOI bien formé peut ne pointer "
        "sur rien",
        "le contenu du dépôt n'est pas ouvert : rien ne dit qu'il porte ce "
        "que la déclaration annonce",
        "aucune autorisation n'est vérifiée (consentement des personnes, "
        "accord de l'employeur, licence des données de tiers)",
        "la politique de la revue cible n'est pas lue : elle peut exiger "
        "d'autres éléments ou un autre emplacement",
        "une déclaration exacte mais placée hors d'une section titrée échappe "
        "à la détection, qui porte sur un titre",
    ]


LIBELLE_CONFIANCE = {CONFIRME: "CONFIRME ", PROBABLE: "probable ",
                     INFORMATIF: "informatif", DOUTEUX: "douteux   "}

TITRES_CATEGORIE = {"structure": "Structure de la déclaration",
                    "regime": "Régime déclaré",
                    "identifiant": "Identifiant pérenne",
                    "code": "Code"}


def rapport_texte(r):
    """Rendu texte du rapport. Voir analyser() pour la structure."""
    lignes = ["%s : %s" % (r.get("fichier") or "(texte)", r["verdict"].upper())]
    s = r["section"]
    lignes.append("  Section : %s"
                  % (", ".join(s["titres"]) + " (ligne %s)" % s["ligne"]
                     if s["trouvee"] else "absente"))
    lignes.append("  Régimes : %s"
                  % (", ".join(LIBELLE_REGIME[x] for x in r["regimes"])
                     or "aucun identifié"))
    if r["identifiants"]:
        lignes.append("  Identifiants pérennes : %s"
                      % ", ".join("%s %s" % (i["type"], i["valeur"])
                                  for i in r["identifiants"]))
    lignes.append("")
    par_categorie = {}
    for c in r["constats"]:
        par_categorie.setdefault(c["categorie"], []).append(c)
    if not r["constats"]:
        lignes.append("  aucun constat : la déclaration porte ce que son "
                      "régime exige")
    for cat in ("structure", "regime", "identifiant", "code"):
        groupe = par_categorie.get(cat)
        if not groupe:
            continue
        lignes.append("  %s" % TITRES_CATEGORIE[cat])
        for c in groupe:
            extrait = (" -> %s" % c["extrait"]) if c["extrait"] else ""
            lignes.append("    [%s] %s : %s%s"
                          % (LIBELLE_CONFIANCE[c["confiance"]], c["regle"],
                             c["detail"], extrait))
        lignes.append("")
    lignes.append("  %d confirmé(s), %d probable(s), %d informatif(s), "
                  "%d douteux"
                  % (r["comptes"][CONFIRME], r["comptes"][PROBABLE],
                     r["comptes"][INFORMATIF], r["comptes"][DOUTEUX]))
    lignes.append("")
    lignes.append("Limite : %s" % r.get("limite", LIMITE))
    lignes.append("Non vérifié ici :")
    for m in r["non_verifie"]:
        lignes.append("  - %s" % m)
    return "\n".join(lignes)


def main(argv=None):
    # Une console Windows en page de code heritee ne sait pas encoder tout ce
    # qu'un manuscrit porte. Sans garde, l'impression leve UnicodeEncodeError
    # alors que la mesure est juste : le caractere se degrade, jamais le
    # resultat. Meme garde que check-droits.py.
    for _flux in (sys.stdout, sys.stderr):
        try:
            _flux.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    p = argparse.ArgumentParser(
        description="Contrôle de la déclaration de disponibilité des données "
                    "et du code d'un manuscrit : présence, régime déclaré, "
                    "identifiant pérenne, licence du code, date d'embargo. "
                    "Consultatif par défaut.",
        epilog=LIMITE)
    p.add_argument("fichier", help="manuscrit Markdown, ou - pour l'entrée standard")
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--strict", action="store_true",
                   help="code de sortie 1 hors du verdict "
                        "\"declaration conforme\"")
    a = p.parse_args(argv)

    if a.fichier == "-":
        texte, nom = sys.stdin.read(), "(entrée standard)"
    else:
        if not os.path.isfile(a.fichier):
            print("fichier introuvable : %s" % a.fichier, file=sys.stderr)
            return 2
        with open(a.fichier, encoding="utf-8") as f:
            texte = f.read()
        nom = os.path.basename(a.fichier)

    r = analyser(texte, nom)
    if a.format == "json":
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(rapport_texte(r))
    return 1 if (a.strict and r["verdict"] != "declaration conforme") else 0


if __name__ == "__main__":
    sys.exit(main())
