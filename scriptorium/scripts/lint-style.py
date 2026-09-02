#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Linter de style maison déterministe pour Scriptorium.

Détecte mécaniquement les écarts aux directives strictes, sans jugement de
modèle : tiret cadratin, typographie courbe, lexique promotionnel banni,
paramètres de suivi dans les URL, virgule d'Oxford, métadiscours, pronom
indéfini « on », quantificateurs vagues, verbes tics.

Le moteur connait deux langues. En francais (defaut) le comportement est celui
d'origine. En anglais les regles calibrees sur le francais sont retirees (la
virgule serielle y est recommandee par Chicago, APA et MLA, la signaler serait
un faux positif) et remplacees par des regles propres a l'ecriture scientifique
anglaise.

Usage :
    python3 lint-style.py FICHIER [--format text|json] [--strict] [--quiet]
                          [--langue fr|en|auto]
    cat doc.md | python3 lint-style.py -

Codes de sortie :
    0  aucun constat critique (ni majeur si --strict)
    1  au moins un constat critique (ou majeur si --strict)
    2  erreur d'usage

Pragmas dans le document analysé :
    une ligne contenant « lint-style:ignore » n'est pas analysée.
    un fichier dont les 5 premières lignes contiennent « lint-style:ignore-file »
    est ignoré entièrement.
    un fichier dont les 5 premieres lignes contiennent « lint-style:langue=en »
    est analyse en anglais sans qu'aucune option soit passee.

Langue d'ANALYSE et langue d'AFFICHAGE sont deux choses. La premiere choisit
le jeu de regles applique au texte (--langue), la seconde choisit la langue
des libelles imprimes (--langue-affichage), et prend par defaut la valeur de
la premiere. Les valeurs machine ne bougent dans aucune des deux : le nom de
regle et la severite restent francais partout, y compris en sortie JSON, qui
reste celle d'origine a l'octet pres.

Le module est importable : lint_text(texte, langue=None) -> liste de constats.
"""
import argparse
import json
import os
import re
import sys

CRITIQUE, MAJEUR, MINEUR = "critique", "majeur", "mineur"
ORDRE = {CRITIQUE: 0, MAJEUR: 1, MINEUR: 2}

LANGUES = ("fr", "en")
LANGUE_DEFAUT = "fr"

_LIB = None


def _lib():
    """Charge libelles.py a la demande, une seule fois. Le module vit a cote
    de ce fichier et se lit par chemin plutot que par nom : les scripts du
    plugin sont eux-memes charges depuis des repertoires arbitraires, aucun
    sys.path n'est garanti."""
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


# Mots outils sans ambiguite entre les deux langues. Sont ecartes ceux qui
# existent dans les deux (a, on, or, as, note, son, but, pour un titre anglais
# cite dans un texte francais), qui fausseraient le comptage.
MOTS_OUTILS_FR = frozenset("""le la les des du une dans pour que qui est sont
avec cette ces sur par plus aux leur nous mais comme entre aussi dont ainsi
chaque leurs elle ils sans deja etre ete quand alors donc car""".split())
MOTS_OUTILS_EN = frozenset("""the of and to in is are that for with this these
we was were be been from not which their have has its than such also each
they there where while both any into upon""".split())

# En deca de ce nombre de mots outils reconnus, un echantillon ne tranche rien
# (titre seul, liste de mots-clefs, tableau de chiffres).
SEUIL_DETECTION = 12
# Part minimale du gagnant. Un texte francais qui cite une bibliographie
# anglaise passe sous cette barre et reste classe francais.
PART_DETECTION = 0.60

PRAGMA_LANGUE = re.compile(r"lint-style:langue\s*=\s*(fr|en)", re.I)


def detecter_langue(texte, defaut=LANGUE_DEFAUT):
    """Devine la langue par frequence de mots outils exclusifs a chacune.

    Retourne 'fr' ou 'en'. Rend le defaut quand l'echantillon est trop court
    ou trop partage : la detection ne tranche jamais a la majorite d'une voix.
    """
    mots = re.findall(r"[a-zà-ÿ']+", texte.lower())
    n_fr = sum(1 for m in mots if m in MOTS_OUTILS_FR)
    n_en = sum(1 for m in mots if m in MOTS_OUTILS_EN)
    total = n_fr + n_en
    if total < SEUIL_DETECTION:
        return defaut
    if n_en / total >= PART_DETECTION:
        return "en"
    if n_fr / total >= PART_DETECTION:
        return "fr"
    return defaut


def langue_declaree(texte):
    """Lit le pragme de langue dans les cinq premieres lignes, sinon None."""
    for ligne in texte.splitlines()[:5]:
        m = PRAGMA_LANGUE.search(ligne)
        if m:
            return m.group(1).lower()
    return None


def resoudre_langue(texte, demandee=None, defaut=LANGUE_DEFAUT):
    """Tranche la langue d'analyse selon un ordre de priorite fixe.

    1. l'option explicite --langue fr|en, qui prime sur tout ;
    2. --langue auto, qui delegue a la detection ;
    3. le pragme du document, seul canal disponible pour le hook, qui n'a
       aucun moyen de passer une option par document ;
    4. le defaut, francais.

    La detection n'est pas le defaut : le linter est appele sans argument par
    le hook et par scorecard.py, et basculer de langue tout seul changerait en
    silence le verdict d'un document existant.
    """
    if demandee in LANGUES:
        return demandee
    if demandee == "auto":
        return detecter_langue(texte, defaut)
    declaree = langue_declaree(texte)
    if declaree in LANGUES:
        return declaree
    return defaut


# (regex, sévérité, règle, message)
REGLES = [
    (re.compile(r"[—–]"), CRITIQUE, "tiret-cadratin",
     "Tiret cadratin ou demi-cadratin. Utiliser parenthèses ou virgules."),
    (re.compile(r"[‘’“”]"), CRITIQUE, "typographie-courbe",
     "Guillemet ou apostrophe courbe. Utiliser la typographie droite."),
    (re.compile(r"\b(pivotal|pivotale|crucial|cruciale|cruciaux|emblématique|"
                r"incontournable|visionnaire|révolutionnaire)\b", re.I),
     CRITIQUE, "lexique-promo", "Terme promotionnel banni."),
    (re.compile(r"riche tapisserie|façonner le paysage", re.I),
     CRITIQUE, "lexique-promo", "Tournure promotionnelle bannie."),
    (re.compile(r"utm_[a-z]+=|[?&](fbclid|gclid|mc_eid|mc_cid|igshid)=", re.I),
     CRITIQUE, "url-suivi", "Paramètre de suivi dans une URL. Le retirer."),
    (re.compile(r",\s+(et|ou)\s", re.I), MAJEUR, "virgule-oxford",
     "Virgule avant et/ou. Vérifier que ce n'est pas une virgule d'Oxford."),
    (re.compile(r"\b(témoigne de|se présente comme|se positionne comme|"
                r"met en lumière)\b", re.I),
     MAJEUR, "tournure-faible", "Tournure faible. Préférer un verbe simple ou le fait."),
    (re.compile(r"\bau[- ]delà\b", re.I), MAJEUR, "lexique-faible",
     "« au-delà » banni. Reformuler (de plus de, en plus de)."),
    (re.compile(r"(voici (?:le|la|les|un|une)|dans cet article|"
                r"en tant qu'?\s*ia|il est important de noter|"
                r"force est de constater|nous allons voir|"
                r"sans plus attendre)", re.I),
     MAJEUR, "metadiscours", "Métadiscours. Entrer directement en matière."),
    (re.compile(r"\bon\b", re.I), MINEUR, "pronom-on",
     "Pronom indéfini « on ». Préférer une tournure passive ou « nous »."),
    (re.compile(r"\b(plusieurs|nombreux|nombreuses|récemment|la plupart|"
                r"de nombreux|beaucoup de)\b", re.I),
     MINEUR, "quantif-vague", "Quantificateur vague. Chiffrer."),
    (re.compile(r"\b(reflète|souligne|met en avant)\b", re.I),
     MINEUR, "verbe-tic", "Verbe tic fréquent à l'écrit IA. Vérifier qu'il porte un fait."),
    # Surconfiance modale : presenter une affirmation comme absolument
    # etablie sans laisser place au statut epistemique reel (voir
    # controler/references/sophismes-causalite.md section 3). Le defaut de
    # rigueur le plus frequent en ecriture qui s'appuie sur des sources.
    (re.compile(r"\b(il est prouvé que|il est démontré que|"
                r"il ne fait aucun doute que|sans aucun doute,?\s|"
                r"à coup sûr,?\s|il est certain que|nul doute que|"
                r"on sait avec certitude que)", re.I),
     MAJEUR, "surconfiance-modale",
     "Certitude absolue affirmée sans statut épistémique déclaré. Poser le "
     "vrai statut (établi, soutenu, préliminaire, spéculatif, contesté) : "
     "voir controler/references/sophismes-causalite.md section 3."),
    # Modalisateurs empiles : un seul degre de reserve par affirmation,
    # sinon la reserve ne dit plus rien (symetrique de hedge-empile en
    # anglais, ci-dessous dans REGLES_EN).
    (re.compile(r"\b(pourrait|pourraient)\s+(?:potentiellement|peut-être|"
                r"éventuellement)\b"
                r"|\b(?:peut-être|potentiellement|éventuellement)\s+"
                r"(pourrait|pourraient)\b"
                r"|\bil (?:se peut|semblerait) que.{0,20}\bpeut-être\b", re.I),
     MAJEUR, "hedge-empile",
     "Modalisateurs empilés. Un seul degré de réserve par affirmation, sinon "
     "la réserve ne dit plus rien."),
    # Caractères invisibles : ils survivent au copier-coller, cassent la
    # recherche plein texte, l'appariement de citations et les diffs, et
    # certaines revues rejettent les fichiers qui en portent.
    (re.compile(r"[​⁠﻿]"), MAJEUR, "caractere-invisible",
     "Caractère de largeur nulle. Le retirer : il casse recherche et diff."),
    (re.compile(r"­"), MAJEUR, "caractere-invisible",
     "Trait d'union conditionnel invisible. Le retirer."),
    (re.compile(r"[‪-‮⁦-⁩]"), CRITIQUE, "controle-bidi",
     "Contrôle bidirectionnel. Il peut faire lire un texte autrement qu'il "
     "n'est écrit."),
    (re.compile(r"[\U000e0000-\U000e007f]"), CRITIQUE, "caractere-tag",
     "Caractère de tag Unicode, invisible et porteur de données."),
    (re.compile(r"[-]"), MAJEUR, "zone-privee",
     "Caractère de zone à usage privé : son rendu dépend de la police."),
    (re.compile(r"[ -    　]"), MINEUR,
     "espace-exotique",
     "Espace typographique exotique. Préférer l'espace ordinaire ou "
     "l'insécable."),
    # Les liants de largeur nulle portent du sens dans les écritures qui les
    # emploient (arabe, persan, langues indiennes) et dans les séquences
    # d'emoji, où ils composent un seul signe. Les signaler partout produirait
    # un faux positif à chaque drapeau ou famille. Ils ne sont relevés
    # qu'entre deux lettres latines, où ils ne servent à rien.
    (re.compile(r"(?<=[A-Za-zÀ-ÿ])[‌‍](?=[A-Za-zÀ-ÿ])"), MAJEUR,
     "liant-inutile",
     "Liant de largeur nulle entre deux lettres latines, où il ne sert à "
     "rien. En écriture arabe ou indienne il serait légitime."),
]

# Famille de chaque regle de REGLES. Une regle commune vaut dans les deux
# langues, une regle « fr » est calibree sur le francais et sort de l'analyse
# anglaise. La virgule d'Oxford est le cas decisif : la virgule serielle est
# recommandee par Chicago, APA et MLA, la signaler en anglais serait un faux
# positif systematique.
FAMILLE = {
    "typographie-courbe": "commune",
    "url-suivi": "commune",
    "caractere-invisible": "commune",
    "controle-bidi": "commune",
    "caractere-tag": "commune",
    "zone-privee": "commune",
    "espace-exotique": "commune",
    "liant-inutile": "commune",
    "tiret-cadratin": "fr",
    "lexique-promo": "fr",
    "virgule-oxford": "fr",
    "tournure-faible": "fr",
    "lexique-faible": "fr",
    "metadiscours": "fr",
    "pronom-on": "fr",
    "quantif-vague": "fr",
    "verbe-tic": "fr",
    "surconfiance-modale": "fr",
    "hedge-empile": "fr",
}

# Contexte statistique explicite. Sa presence sur la ligne rend legitime
# l'emploi de « significant » et fait taire la regle.
_CONTEXTE_STAT = re.compile(
    r"\bp\s*[<>=]|\bp-?values?\b|\bstatistical|\bconfidence intervals?\b"
    r"|\b\d+\s*%\s*CI\b|\banova\b|\bt-tests?\b|\bchi-squared?\b|\bwilcoxon\b"
    r"|\bmann-whitney\b|\bkruskal\b|\bbonferroni\b|\balpha\s*=|\bnon-?significan",
    re.I)


def _garde_significant(ligne, m):
    """Tait la regle quand la ligne ancre deja le mot dans un test statistique."""
    return bool(_CONTEXTE_STAT.search(ligne))


# Regles propres a l'anglais. Meme forme que REGLES, avec un cinquieme element
# optionnel : une garde contextuelle qui annule le constat quand elle rend vrai.
REGLES_EN = [
    # Transposition directe du lexique promotionnel banni. pivotal et crucial
    # figurent aussi au vocabulaire en exces mesure par Kobak et al. (2025).
    (re.compile(r"\b(pivotal|crucial|groundbreaking|revolutionary|visionary|"
                r"game-chang(?:er|ing)|cutting-edge|unparalleled)\b", re.I),
     CRITIQUE, "lexique-promo", "Terme promotionnel banni."),
    (re.compile(r"rich tapestry|shap(?:e|es|ing) the landscape", re.I),
     CRITIQUE, "lexique-promo", "Tournure promotionnelle bannie."),
    # Vocabulaire en exces mesure sur 15 millions de resumes PubMed (Kobak et
    # al., Science Advances 2025) et sur les revues ICLR (Liang et al., ICML
    # 2024). Marqueur de texte assiste, pas faute de langue.
    (re.compile(r"\b(delve[sd]?|delving|intricate|intricacies|intricately|"
                r"realms?|meticulous(?:ly)?|seamless(?:ly)?|commendable|"
                r"multifaceted|interplay|garnered|elucidate[sd]?|"
                r"unveil(?:s|ed|ing)?)\b", re.I),
     MAJEUR, "lexique-ia-en",
     "Terme du vocabulaire en excès mesuré dans les textes assistés par "
     "modèle. Nommer le fait plutôt que le qualifier."),
    (re.compile(r"\b(?:research|academic|scientific|technological|competitive|"
                r"evolving|changing|digital|regulatory|therapeutic)\s+landscape\b"
                r"|\blandscape of\b", re.I),
     MAJEUR, "lexique-ia-en",
     "« landscape » au sens figuré. Nommer le domaine ou l'ensemble visé."),
    (re.compile(r"\b(underscor(?:e|es|ed|ing)|showcas(?:e|es|ed|ing)|"
                r"highlight(?:s|ed|ing)?|foster(?:s|ed|ing)?|"
                r"harness(?:es|ed|ing)?|streamlin(?:e|es|ed|ing)|"
                r"leverag(?:e|es|ed|ing))\b", re.I),
     MINEUR, "verbe-tic",
     "Verbe tic fréquent à l'écrit assisté. Vérifier qu'il porte un fait."),
    (re.compile(r"\bnavigat(?:e|es|ed|ing)\s+(?:the\s+|these\s+|its\s+)?"
                r"(?:complex|challeng|landscape|intricac|difficult|nuanc)", re.I),
     MINEUR, "verbe-tic",
     "« navigate » au sens figuré. Nommer l'action réelle."),
    (re.compile(r"\butili[sz](?:e|es|ed|ing)\b", re.I),
     MINEUR, "lexique-faible",
     "« utilize » sans gain de sens sur « use ». Simplifier."),
    (re.compile(r"(it is worth noting|it is important to note|"
                r"in today's fast-paced|in the ever-evolving|"
                r"in this (?:article|paper|section),? (?:we will|i will)|"
                r"as an ai (?:language )?model|without further ado|"
                r"let us delve|needless to say|"
                r"in conclusion, it can be said)", re.I),
     MAJEUR, "metadiscours", "Métadiscours. Entrer directement en matière."),
    # Regle de fond, pas de style : « significant » sans marque statistique
    # sur la ligne. Recommandation ICMJE, section Results : ne pas employer
    # hors de son sens technique un terme technique de la statistique.
    (re.compile(r"\bsignificant(?:ly)?\b", re.I),
     MAJEUR, "significance-non-statistique",
     "« significant » hors contexte statistique explicite. Le réserver à la "
     "signification statistique et écrire important, substantial ou large "
     "pour l'ampleur.",
     _garde_significant),
    (re.compile(r"\b(?:mak(?:e|es|ing)|made)\s+an?\s+"
                r"(?:assessment|analysis|comparison|evaluation|estimation|"
                r"observation|assumption|selection|determination|decision)\s+of\b"
                r"|\b(?:perform|performs|performed|conduct|conducts|conducted|"
                r"carry out|carried out|undertake|undertook|undertaken)\s+an?\s+"
                r"(?:analysis|assessment|evaluation|examination|investigation|"
                r"comparison|measurement|calculation|review)\s+of\b"
                r"|\b(?:provide|provides|provided|give|gives|given)\s+an?\s+"
                r"(?:description|explanation|overview|indication|assessment)\s+of\b"
                r"|\bis indicative of\b|\bhas the ability to\b"
                r"|\bdue to the fact that\b|\bin the event that\b"
                r"|\bfor the purpose of\b|\bmake use of\b", re.I),
     MINEUR, "nominalisation",
     "Verbe caché sous un substantif. Employer le verbe (assess, analyse, "
     "compare) plutôt que sa périphrase."),
    (re.compile(r"\b(?:may|might|could|can)\s+(?:potentially|possibly|perhaps|"
                r"conceivably|arguably)\b"
                r"|\b(?:potentially|possibly|perhaps)\s+(?:may|might|could)\b"
                r"|\b(?:seems?|appears?)\s+to\s+(?:potentially|possibly)\b"
                r"|\b(?:may|might|could)\s+(?:\w+\s+){0,2}"
                r"(?:suggest|indicate|imply)s?\s+that\s+(?:\w+\s+){0,3}"
                r"(?:may|might|could)\b", re.I),
     MAJEUR, "hedge-empile",
     "Modalisateurs empilés. Un seul degré de réserve par affirmation, sinon "
     "la réserve ne dit plus rien."),
    # Piege du francophone : l'espace avant le signe double, correcte en
    # francais, fautive en anglais. Le tiret qui suit est exclu, sinon la
    # rangee d'alignement d'un tableau markdown ( :--- ) leverait un constat
    # a chaque tableau aligne a gauche.
    (re.compile("(?<=\\S)[   \t]+[;:!?](?!-)"), MAJEUR,
     "espace-avant-ponctuation",
     "Espace avant deux-points, point-virgule, point d'exclamation ou "
     "d'interrogation. Correcte en français, fautive en anglais : coller le "
     "signe au mot."),
    (re.compile(r"\b(informations|researches|evidences|softwares|feedbacks|"
                r"equipments|advices|knowledges|trainings)\b", re.I),
     MAJEUR, "indenombrable-en",
     "Nom indénombrable mis au pluriel. Écrire information, research, "
     "evidence, software au singulier."),
    (re.compile(r"\bactually\b|\beventually\b|\bsensible\b"
                r"|\b(?:to|we|they|it)\s+precise\b|\bprecised\b"
                r"|\bcontrol\s+(?:that|if|whether)\b"
                r"|\ban important\s+(?:number|quantity|amount|part)\s+of\b"
                r"|\b(?:allow|allows|permit|permits|enable|enables)\s+to\s+\w+"
                r"|\bin the frame of\b|\bassist(?:ed|s)?\s+at\s+the\b"
                r"|\binconvenients?\b", re.I),
     MINEUR, "faux-ami",
     "Faux ami ou calque du français. Vérifier le sens visé (actually = en "
     "fait, eventually = finalement, sensible = raisonnable, allow to + verbe "
     "n'existe pas)."),
]

# Termes bannis cités par les fichiers de référence du plugin : on n'analyse
# pas ces fichiers (ils énoncent les interdits). Détection par marqueur.
MARQUEUR_FICHIER = "lint-style:ignore-file"
MARQUEUR_LIGNE = "lint-style:ignore"

# Formes exclusivement britanniques et exclusivement americaines. Le suffixe
# -ize ne figure pas cote americain : l'orthographe d'Oxford (OED, Oxford
# University Press, Nature) ecrit -ize en anglais britannique, donc -ize ne
# prouve aucune appartenance. Seules les formes -ise de verbes qui admettent
# -ize sont retenues cote britannique. Les verbes toujours en -ise (exercise,
# comprise, revise, surprise, supervise, advertise, improvise, devise) sont
# hors liste par construction : aucune regle n'emploie de motif general
# en -ise, qui les prendrait tous pour des britannismes.
ORTHOGRAPHE_GB = frozenset("""colour colours coloured behaviour behaviours
favour favours labour honour neighbour endeavour centre centres metre metres
litre litres fibre fibres theatre defence offence licence practise practised
analyse analysed analysing paralyse catalyse catalysed modelling modelled
labelling labelled travelling travelled sulphur organise organised organising
organisation recognise recognised recognising characterise characterised
characterisation summarise summarised emphasise emphasised standardise
standardised normalise normalised minimise minimised maximise maximised
generalise generalised hypothesise categorise prioritise optimise optimised
optimisation realise realised specialised visualise visualised""".split())
ORTHOGRAPHE_US = frozenset("""color colors colored behavior behaviors favor
favors labor honor neighbor endeavor center centers liter liters fiber fibers
theater defense offense analyze analyzed analyzing paralyze catalyze modeling
modeled labeling labeled traveling traveled sulfur""".split())

_MOT = re.compile(r"[A-Za-zÀ-ÿ']+")
_FIN_DE_PHRASE = re.compile(r"[.!?]+\s|\n")
_PASSIF_EN = re.compile(
    r"\b(?:is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?"
    r"(?:\w{3,}ed|shown|given|taken|known|drawn|written|chosen|made|found|"
    r"seen|held|built|done|sent|kept)\b", re.I)

# Le tiret cadratin est une ponctuation legitime en anglais : seul son exces
# fait signal. Aucune norme ne fixe de densite, ces deux seuils sont une
# convention maison, reglable, pas une mesure.
SEUIL_TIRET_POUR_MILLE = 3.0
SEUIL_TIRET_MINIMUM = 3
SEUIL_PASSIF = 0.50
SEUIL_PASSIF_PHRASES = 6


def regles_pour(langue):
    """Retourne les regles applicables a la langue demandee.

    Le francais rejoue REGLES telle quelle, dans son ordre d'origine : c'est
    ce qui garantit qu'aucun constat ne bouge d'une version a l'autre.
    """
    if langue == "en":
        return ([r for r in REGLES if FAMILLE.get(r[2]) == "commune"]
                + REGLES_EN)
    return REGLES


def _constat(ligne, colonne, severite, regle, message, extrait, trouve):
    return {"ligne": ligne, "colonne": colonne, "severite": severite,
            "regle": regle, "message": message, "extrait": extrait,
            "trouve": trouve}


def _premiere_ligne(utiles, mots_cibles):
    """Numero de la premiere ligne analysable portant un des mots vises."""
    for numero, ligne in utiles:
        for m in _MOT.finditer(ligne):
            if m.group(0).lower() in mots_cibles:
                return numero
    return utiles[0][0] if utiles else 1


def regles_document_en(utiles, langue_affichage=LANGUE_DEFAUT):
    """Constats anglais qui ne se lisent qu'a l'echelle du document entier.

    utiles est la liste des couples (numero de ligne, ligne) reellement
    analysees, blocs de code et lignes ignorees deja retires.

    Ces trois messages portent des nombres mesures : ils se composent ici, dans
    la langue d'affichage demandee, plutot que de se traduire apres coup. Sans
    langue_affichage, le francais d'origine est rendu a l'octet pres.
    """
    lib = _lib()
    la = langue_affichage
    constats = []
    texte = "\n".join(ligne for _, ligne in utiles)
    mots = [m.group(0).lower() for m in _MOT.finditer(texte)]
    if not mots:
        return constats

    gb = sorted({m for m in mots if m in ORTHOGRAPHE_GB})
    us = sorted({m for m in mots if m in ORTHOGRAPHE_US})
    if gb and us:
        constats.append(_constat(
            _premiere_ligne(utiles, ORTHOGRAPHE_US), 1, MAJEUR,
            "orthographe-melangee",
            lib.t("lint.msg.orthographe_melangee", la),
            lib.t("lint.extrait.orthographe_melangee", la,
                  gb=", ".join(gb[:3]), us=", ".join(us[:3])),
            us[0]))

    n_cadratin = texte.count("—")
    if (n_cadratin >= SEUIL_TIRET_MINIMUM
            and n_cadratin * 1000.0 / len(mots) > SEUIL_TIRET_POUR_MILLE):
        constats.append(_constat(
            _premiere_ligne(utiles, frozenset()), 1, MINEUR,
            "tiret-cadratin-densite",
            lib.t("lint.msg.tiret_densite", la, n=n_cadratin, mots=len(mots)),
            lib.t("lint.extrait.tiret_densite", la,
                  densite="%.1f" % (n_cadratin * 1000.0 / len(mots))),
            "—"))

    phrases = [p for p in _FIN_DE_PHRASE.split(texte) if len(p.split()) >= 4]
    if len(phrases) >= SEUIL_PASSIF_PHRASES:
        n_passives = sum(1 for p in phrases if _PASSIF_EN.search(p))
        part = n_passives / len(phrases)
        if part > SEUIL_PASSIF:
            constats.append(_constat(
                _premiere_ligne(utiles, frozenset()), 1, MINEUR,
                "passif-excessif",
                lib.t("lint.msg.passif", la, n=n_passives,
                      total=len(phrases)),
                lib.t("lint.extrait.passif", la, pct=round(part * 100)),
                "passive"))
    return constats


def lint_text(texte, chemin=None, langue=None, langue_affichage=None):
    """Analyse un texte et retourne la liste des constats.

    Chaque constat est un dict : ligne, colonne, severite, regle, message, extrait.
    langue vaut fr, en, auto ou None. None conserve le comportement d'origine :
    le pragme du document s'il en porte un, sinon le francais.

    langue_affichage ne touche que deux champs de confort, message et extrait.
    Les champs sur lesquels du code branche (regle, severite, ligne, colonne,
    trouve) ne bougent pas. Sans langue_affichage, la sortie est celle
    d'origine a l'octet pres : c'est ce que serialise le mode --format json,
    qui ne passe jamais cette option.
    """
    lignes = texte.splitlines()
    if any(MARQUEUR_FICHIER in l for l in lignes[:5]):
        return []
    langue = resoudre_langue(texte, langue)
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage, LANGUE_DEFAUT)
    regles = regles_pour(langue)
    constats = []
    utiles = []
    dans_code = False
    for i, ligne in enumerate(lignes, start=1):
        depouille = ligne.strip()
        if depouille.startswith("```"):
            dans_code = not dans_code
            continue
        if dans_code:
            continue
        if MARQUEUR_LIGNE in ligne:
            continue
        utiles.append((i, ligne))
        for definition in regles:
            regex, severite, regle, message = definition[:4]
            garde = definition[4] if len(definition) > 4 else None
            for m in regex.finditer(ligne):
                if garde is not None and garde(ligne, m):
                    continue
                deb = max(0, m.start() - 20)
                fin = min(len(ligne), m.end() + 20)
                extrait = ligne[deb:fin].strip()
                constats.append({
                    "ligne": i,
                    "colonne": m.start() + 1,
                    "severite": severite,
                    "regle": regle,
                    "message": lib.valeur("lint.message", message, la),
                    "extrait": extrait,
                    "trouve": m.group(0),
                })
    if langue == "en":
        constats.extend(regles_document_en(utiles, la))
    constats.sort(key=lambda c: (ORDRE[c["severite"]], c["ligne"], c["colonne"]))
    return constats


def compter(constats):
    n = {CRITIQUE: 0, MAJEUR: 0, MINEUR: 0}
    for c in constats:
        n[c["severite"]] += 1
    return n


def rapport_texte(constats, chemin, langue=LANGUE_DEFAUT,
                  langue_affichage=None):
    """Rapport lisible. langue est la langue ANALYSEE, rapportee telle quelle
    dans le rapport ; langue_affichage est celle des libelles, francaise par
    defaut."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage, LANGUE_DEFAUT)
    n = compter(constats)
    out = []
    titre = chemin or "(stdin)"
    out.append(lib.t("lint.titre", la, titre=titre))
    out.append("  " + lib.t("lint.langue_analysee", la, langue=langue))
    out.append("  " + lib.t("lint.comptes", la, critiques=n[CRITIQUE],
                            majeurs=n[MAJEUR], mineurs=n[MINEUR]))
    if not constats:
        out.append("  " + lib.t("lint.aucun_ecart", la))
        return "\n".join(out)
    sev_courante = None
    for c in constats:
        if c["severite"] != sev_courante:
            sev_courante = c["severite"]
            out.append("\n[%s]" % lib.valeur("lint.severite", sev_courante,
                                             la).upper())
        out.append("  " + lib.t("lint.constat", la, ligne=c["ligne"],
                                colonne=c["colonne"], regle=c["regle"],
                                trouve=c["trouve"], message=c["message"]))
    return "\n".join(out)


def code_sortie(constats, strict):
    n = compter(constats)
    if n[CRITIQUE] > 0:
        return 1
    if strict and n[MAJEUR] > 0:
        return 1
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="Linter de style maison Scriptorium.")
    p.add_argument("fichier", help="chemin du fichier, ou - pour stdin")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--strict", action="store_true",
                   help="code de sortie 1 aussi sur constat majeur")
    p.add_argument("--quiet", action="store_true",
                   help="n'imprime rien, renvoie seulement le code de sortie")
    p.add_argument("--langue", choices=["fr", "en", "auto"], default=None,
                   help="langue d'analyse. Sans l'option : le pragme "
                        "lint-style:langue du document, sinon fr. "
                        "auto lance la détection heuristique")
    p.add_argument("--langue-affichage", choices=["fr", "en"], default=None,
                   help="langue des libellés du rapport texte. Sans "
                        "l'option : la langue d'analyse retenue. La sortie "
                        "JSON reste française quoi qu'il arrive")
    a = p.parse_args(argv)
    lib = _lib()
    try:
        if a.fichier == "-":
            texte = sys.stdin.read()
            chemin = None
        else:
            with open(a.fichier, encoding="utf-8") as f:
                texte = f.read()
            chemin = a.fichier
    except OSError as e:
        print(lib.t("lint.erreur_lecture",
                    lib.resoudre_affichage(a.langue_affichage), erreur=e),
              file=sys.stderr)
        return 2
    langue = resoudre_langue(texte, a.langue)
    # Le JSON n'est jamais traduit : c'est la sortie que lisent le jeu d'or,
    # les evals et tout outil tiers. Seul le rapport texte change de langue.
    if a.format == "json":
        constats = lint_text(texte, chemin, langue)
    else:
        la = lib.resoudre_affichage(a.langue_affichage, langue)
        constats = lint_text(texte, chemin, langue, la)
    if not a.quiet:
        if a.format == "json":
            print(json.dumps({
                "fichier": chemin,
                "langue": langue,
                "compte": compter(constats),
                "constats": constats,
            }, ensure_ascii=False, indent=2))
        else:
            print(rapport_texte(constats, chemin, langue, la))
    return code_sortie(constats, a.strict)


if __name__ == "__main__":
    sys.exit(main())
