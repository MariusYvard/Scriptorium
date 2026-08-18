#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verificateur de tracabilite deterministe pour Scriptorium.

Boucle la chaine preuve-affirmation au niveau mecanique : references citees
mais absentes de la bibliographie (citations pendantes), references listees
mais jamais citees (orphelines), figures, tableaux, equations et annexes
definis mais non appeles dans le texte, et appels a un objet inexistant.

Controle aussi la SEQUENCE des numeros, type d'objet par type d'objet : deux
legendes portant le meme numero (doublon), un numero absent de l'intervalle
observe (saut), une suite qui ne commence pas a 1, une numerotation d'annexes
qui melange chiffres et lettres. Apparier les numeros ne suffit pas : un
document ou la figure 2 manque reste coherent au sens des appels alors qu'il
est faux au sens de la lecture.

Compte aussi les tags normalises de lacune ([LACUNE MATERIELLE] et
[PREUVE FAIBLE], casse stricte) par section, pour exposer une donnee que
scorecard.py peut consommer comme il consomme deja les autres cles de ce
module. Un tag bien forme est un signal honnete de l'auteur, jamais une
penalite : seules les variantes de casse mal formees comptent comme un
probleme, puisqu'elles echappent silencieusement au reperage par grep.

Les objets se nomment differemment selon la LANGUE du manuscrit. Le modele de
donnees, lui, ne bouge pas : les cles de sortie gardent les noms francais
(figures, tableaux, equations, annexes), consommes par scorecard.py, seule la
forme cherchee dans le texte change. En anglais un tableau s'ecrit "Table" et
une annexe "Appendix" ; "Figure" s'ecrit de meme dans les deux langues, et les
equations le sont deja par construction (EQ_CAPTION et EQ_MENTION acceptent
"equation" comme "équation").

Usage : python3 traceability.py FICHIER [--format text|json] [--langue fr|en|auto]
Module importable : analyser(texte, langue=None) -> dict.
"""
import argparse
import json
import os
import re
import sys

HEAD_REF = re.compile(r'(?im)^\s{0,3}#{1,6}\s*(r[ée]f[ée]rences?|bibliographie|references|bibliography)\b')
HEAD_SECTION = re.compile(r'(?im)^\s{0,3}(#{1,6})\s+(.+?)\s*$')

TAG_LACUNE_STRICT = re.compile(r'\[LACUNE MATERIELLE\]')
TAG_PREUVE_STRICT = re.compile(r'\[PREUVE FAIBLE\]')
TAG_LACUNE_LARGE = re.compile(r'\[LACUNE MATERIELLE\]', re.I)
TAG_PREUVE_LARGE = re.compile(r'\[PREUVE FAIBLE\]', re.I)

# Legende d'un objet numerote : une ligne qui ouvre sur le nom du type suivi de
# son numero et d'un separateur, precedee au besoin d'une image Markdown.
CAPT_MODELE = r'(?im)^\s{0,3}(?:!\[[^\]]*\]\([^\)]*\)\s*)?%s\s+(\d{1,3})\s*[:\.—–-]'
# Appel d'un objet : toute autre mention du nom du type suivi d'un numero.
MENTION_MODELE = r'(?i)\b%s\s+(\d{1,3})'

LANGUES = ("fr", "en")

# Forme cherchee dans le texte pour chaque type d'objet, par langue. Les CLES
# restent les noms francais du modele de donnees : elles nomment les cles de
# sortie que scorecard.py consomme, les renommer casserait la notation en
# silence. "table" n'est actif qu'en anglais a dessein : dans un texte
# francais, "la table 3" designerait un meuble bien plus souvent qu'un
# tableau, et l'ajouter fabriquerait un faux positif francais.
MOT_OBJET = {
    "fr": {"figure": "figure", "tableau": "tableau"},
    "en": {"figure": "figure", "tableau": "table"},
}

# --- Equations ---------------------------------------------------------------
# Trois notations de numero d'equation coexistent dans les sources traitees par
# le plugin, et toutes trois sont retenues :
#   1. legende explicite en tete de ligne, de meme forme qu'une figure,
#      "Equation 3 : bilan de matiere" ;
#   2. balise LaTeX de numero impose, "\tag{3}" ;
#   3. numero de droite en fin de ligne d'affichage, "$$ ... $$ (3)",
#      "\[ ... \] (3)" ou la ligne de fermeture d'un environnement equation.
# Une seule de ces trois formes est comptee par ligne, sans quoi une equation
# portant a la fois \tag{3} et un numero de droite passerait pour un doublon.
# La numerotation automatique de LaTeX (\begin{equation} sans \tag) ne laisse
# aucun numero lisible dans la source : elle sort du perimetre de ce script,
# la sequence etant alors tenue par le compilateur lui-meme.
EQ_CAPTION = re.compile(r'(?im)^\s{0,3}[ée]quations?\s+(\d{1,3})\s*[:\.—–-]')
EQ_TAG = re.compile(r'\\tag\*?\{\s*\(?(\d{1,3})\)?\s*\}')
EQ_NUMERO_DROITE = re.compile(
    r'^[^\n]*(?:\$\$|\\\]|\\end\{equation\*?\})[^\n]*\((\d{1,3})\)\s*$')
# Un appel d'equation se parenthese souvent, "voir l'equation (3)".
EQ_MENTION = re.compile(r'(?i)\b[ée]quations?\s+\(?(\d{1,3})\)?')

# --- Annexes -----------------------------------------------------------------
# Une annexe se numerote en chiffres ("Annexe 2 :") ou en lettres capitales
# ("Annexe B :"). La lettre reste capitale a dessein : sans cette contrainte,
# "l'annexe a ete jointe" passerait pour une annexe nommee A.
ANNEXE_CAPTION = re.compile(r'(?m)^\s{0,3}[Aa]nnexes?\s+(\d{1,3}|[A-Z])\s*[:\.—–-]')
ANNEXE_MENTION = re.compile(r'\b[Aa]nnexes?\s+(\d{1,3}|[A-Z])\b')
# Meme contrainte de capitale en anglais, et pour la meme raison : sans elle,
# "the appendix a reader consults" passerait pour une annexe nommee A.
ANNEXE_CAPTION_EN = re.compile(
    r'(?m)^\s{0,3}[Aa]ppendi(?:x|ces)\s+(\d{1,3}|[A-Z])\s*[:\.—–-]')
ANNEXE_MENTION_EN = re.compile(r'\b[Aa]ppendi(?:x|ces)\s+(\d{1,3}|[A-Z])\b')

ANNEXE_MOTIFS = {
    "fr": (ANNEXE_CAPTION, ANNEXE_MENTION),
    "en": (ANNEXE_CAPTION_EN, ANNEXE_MENTION_EN),
}

OBJETS = ("figure", "tableau", "equation", "annexe")

_LINT = None


def _lint():
    """Charge lint-style.py a la demande, une seule fois. Le nom du fichier
    porte un tiret, il n'est pas importable tel quel. La resolution de langue
    y est definie et documentee : elle est lue ici, jamais recopiee."""
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
    """Tranche la langue d'analyse, par delegation a lint-style.py : option
    explicite, puis auto, puis pragme du document, puis francais. Un code
    hors fr, en et auto n'est pas honore, la resolution ordinaire s'applique
    et la langue retenue est rendue dans la cle "langue" du resultat."""
    if langue is not None and langue not in LANGUES and langue != "auto":
        langue = None
    return _lint().resoudre_langue(texte, langue)


# Le pluriel de chaque type d'objet vit desormais dans la table
# traceability.objets de libelles.py, une seule source pour les deux langues.

# Cle de libelle par type d'anomalie. Le nom d'anomalie, lui, est une valeur
# machine : il figure dans la sortie JSON et ne change pas de langue.
CLES_ANOMALIE = {
    "numero_duplique": "traceability.a.numero_duplique",
    "numero_manquant": "traceability.a.numero_manquant",
    "ne_commence_pas_a_un": "traceability.a.ne_commence_pas_a_un",
    "notation_mixte": "traceability.a.notation_mixte",
}

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


def _compte(paires):
    """Agrege une suite de numeros en dictionnaire numero -> occurrences."""
    d = {}
    for n in paires:
        d[n] = d.get(n, 0) + 1
    return d


def _mot(kind, langue):
    """Forme cherchee dans le texte pour ce type d'objet et cette langue. Une
    langue non couverte retombe sur le francais, jamais sur rien."""
    return MOT_OBJET.get(langue, MOT_OBJET["fr"]).get(kind, kind)


def captions_numerotees(corps, kind, langue="fr"):
    """Numeros portes par les legendes de ce type d'objet, avec leur compte."""
    motif = CAPT_MODELE % _mot(kind, langue)
    return _compte(int(x) for x in re.compile(motif).findall(corps))


def _appels(captions, mentions):
    """Un numero est appele quand il est mentionne plus souvent qu'il n'est
    legende : la legende elle-meme compte comme une mention."""
    definis = set(captions)
    appeles = {n for n, c in mentions.items() if c > captions.get(n, 0)}
    return sorted(definis - appeles), sorted(appeles - definis)


def compter(corps, kind, langue="fr"):
    captions = captions_numerotees(corps, kind, langue)
    motif = MENTION_MODELE % _mot(kind, langue)
    mentions = _compte(int(x) for x in re.compile(motif).findall(corps))
    return _appels(captions, mentions)


def equations(corps):
    """Legendes et appels d'equations. Rend (captions, definies_non_appelees,
    appelees_non_definies)."""
    # Seule la legende en toutes lettres ("Equation 3 :") est relue comme une
    # mention par EQ_MENTION : \tag{3} et le numero de droite n'emploient pas
    # le mot. La soustraction des mentions ne porte donc que sur la premiere
    # forme, sinon un appel legitime serait absorbe par sa propre legende.
    captions_mot = _compte(int(x) for x in EQ_CAPTION.findall(corps))
    captions = dict(captions_mot)
    for ligne in corps.splitlines():
        if EQ_CAPTION.match(ligne):
            continue
        m = EQ_TAG.search(ligne) or EQ_NUMERO_DROITE.match(ligne)
        if m:
            n = int(m.group(1))
            captions[n] = captions.get(n, 0) + 1
    mentions = _compte(int(x) for x in EQ_MENTION.findall(corps))
    definis = set(captions)
    appeles = {n for n, c in mentions.items() if c > captions_mot.get(n, 0)}
    return captions, sorted(definis - appeles), sorted(appeles - definis)


def _annexe_numero(brut):
    """Ramene un identifiant d'annexe a un rang entier. Rend (rang, notation)."""
    if brut.isdigit():
        return int(brut), "numerique"
    return ord(brut.upper()) - 64, "alphabetique"


def annexes(texte, langue="fr"):
    """Legendes et appels d'annexes, lus sur le texte entier : une annexe se
    place apres la bibliographie, donc hors du corps decoupe par
    separer_biblio. Rend (captions, definies_non_appelees,
    appelees_non_definies, notation)."""
    caption_re, mention_re = ANNEXE_MOTIFS.get(langue, ANNEXE_MOTIFS["fr"])
    captions, notations = {}, set()
    for brut in caption_re.findall(texte):
        rang, notation = _annexe_numero(brut)
        captions[rang] = captions.get(rang, 0) + 1
        notations.add(notation)
    mentions = {}
    for brut in mention_re.findall(texte):
        rang, _ = _annexe_numero(brut)
        mentions[rang] = mentions.get(rang, 0) + 1
    if len(notations) > 1:
        notation = "mixte"
    elif notations:
        notation = notations.pop()
    else:
        notation = "aucune"
    nc, nd = _appels(captions, mentions)
    return captions, nc, nd, notation


def verifier_sequence(captions, notation="numerique"):
    """Controle la suite des numeros de legende d'un type d'objet.

    captions : dictionnaire numero -> nombre de legendes portant ce numero.
    Rend les doublons, les numeros absents de l'intervalle observe, le premier
    numero de la suite et la notation employee."""
    numeros = sorted(captions)
    doublons = [n for n in numeros if captions[n] > 1]
    manquants = ([n for n in range(numeros[0], numeros[-1] + 1) if n not in captions]
                 if numeros else [])
    return {
        "numeros": numeros,
        "doublons": doublons,
        "manquants": manquants,
        "commence_a": numeros[0] if numeros else None,
        "commence_a_un": numeros[0] == 1 if numeros else True,
        "notation": notation,
    }


def anomalies_numerotation(sequences):
    """Aplatit les sequences en une liste de constats nommes, un par defaut
    reel. Une liste vide signifie une numerotation saine."""
    out = []
    for objet in OBJETS:
        s = sequences[objet]
        if s["doublons"]:
            out.append({"objet": objet, "anomalie": "numero_duplique",
                        "numeros": s["doublons"]})
        if s["manquants"]:
            out.append({"objet": objet, "anomalie": "numero_manquant",
                        "numeros": s["manquants"]})
        if s["numeros"] and not s["commence_a_un"]:
            out.append({"objet": objet, "anomalie": "ne_commence_pas_a_un",
                        "numeros": [s["commence_a"]]})
        if s["notation"] == "mixte":
            out.append({"objet": objet, "anomalie": "notation_mixte",
                        "numeros": s["numeros"]})
    return out


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


def analyser(texte, langue=None):
    langue = resoudre_langue(texte, langue)
    corps, biblio = separer_biblio(texte)
    definies = refs_numerotees(biblio)
    citees = cites_numerotees(corps)
    pendantes = sorted(citees - definies)
    orphelines = sorted(definies - citees) if definies else []
    fig_nc, fig_nd = compter(corps, 'figure', langue)
    tab_nc, tab_nd = compter(corps, 'tableau', langue)
    eq_capt, eq_nc, eq_nd = equations(corps)
    anx_capt, anx_nc, anx_nd, anx_notation = annexes(texte, langue)
    sequences = {
        "figure": verifier_sequence(captions_numerotees(corps, 'figure', langue)),
        "tableau": verifier_sequence(captions_numerotees(corps, 'tableau', langue)),
        "equation": verifier_sequence(eq_capt),
        "annexe": verifier_sequence(anx_capt, anx_notation),
    }
    resultat = {
        "langue": langue,
        "biblio_presente": bool(biblio),
        "references_definies": sorted(definies),
        "citations_pendantes": pendantes,
        "references_orphelines": orphelines,
        "figures_definies_non_appelees": fig_nc,
        "figures_appelees_non_definies": fig_nd,
        "tableaux_definis_non_appeles": tab_nc,
        "tableaux_appeles_non_definis": tab_nd,
        "equations_definies_non_appelees": eq_nc,
        "equations_appelees_non_definies": eq_nd,
        "annexes_definies_non_appelees": anx_nc,
        "annexes_appelees_non_definies": anx_nd,
        "sequences": sequences,
        "numerotation_anomalies": anomalies_numerotation(sequences),
    }
    resultat.update(tags_lacune(texte))
    return resultat


def _rendre(numeros, notation):
    """Rend une liste de rangs dans la notation observee : les annexes lettrees
    se relisent en lettres, sans quoi le constat designerait un objet que
    l'auteur ne trouverait pas dans son texte."""
    if notation == "alphabetique":
        return [chr(64 + n) if 1 <= n <= 26 else n for n in numeros]
    return numeros


# Cle de donnee -> cle de libelle, dans l'ordre d'impression. La cle de
# donnee est machine, elle ne change pas de langue.
CONSTATS_AFFICHES = (
    ("citations_pendantes", "traceability.p.citations_pendantes"),
    ("references_orphelines", "traceability.p.references_orphelines"),
    ("figures_appelees_non_definies", "traceability.p.figures_appelees"),
    ("figures_definies_non_appelees", "traceability.p.figures_definies"),
    ("tableaux_appeles_non_definis", "traceability.p.tableaux_appeles"),
    ("tableaux_definis_non_appeles", "traceability.p.tableaux_definis"),
    ("equations_appelees_non_definies", "traceability.p.equations_appelees"),
    ("equations_definies_non_appelees", "traceability.p.equations_definies"),
    ("annexes_appelees_non_definies", "traceability.p.annexes_appelees"),
    ("annexes_definies_non_appelees", "traceability.p.annexes_definies"),
)


def problemes(d, langue_affichage=None):
    """Constats lisibles tires de l'analyse.

    Sans langue_affichage, les chaines sont celles d'origine a l'octet pres :
    c'est cette liste que serialise la cle problemes du mode --format json."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    p = []
    for cle, libelle in CONSTATS_AFFICHES:
        if d[cle]:
            p.append(lib.t(libelle, la, n=d[cle]))
    for a in d["numerotation_anomalies"]:
        notation = d["sequences"][a["objet"]]["notation"]
        p.append(lib.t(CLES_ANOMALIE[a["anomalie"]], la,
                       objet=lib.valeur("traceability.objets", a["objet"], la),
                       numeros=_rendre(a["numeros"], notation)))
    if d["tags_variantes_mal_formees"]:
        p.append(lib.t("traceability.p.tags_mal_formes", la,
                       n=d["tags_variantes_mal_formees"]))
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(description="Verificateur de tracabilite.")
    ap.add_argument("fichier")
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--langue", choices=["fr", "en", "auto"], default=None,
                     help="langue des noms d'objets cherches. Sans l'option : "
                          "le pragme lint-style:langue du document, sinon fr")
    ap.add_argument("--langue-affichage", choices=["fr", "en"], default=None,
                     help="langue des libelles du rapport texte. Sans "
                          "l'option : la langue d'analyse retenue. La sortie "
                          "JSON reste francaise quoi qu'il arrive")
    a = ap.parse_args(argv)
    lib = _lib()
    texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    d = analyser(texte, a.langue)
    if a.format == "json":
        # Le JSON ne se traduit pas : les evals et le jeu d'or le lisent.
        p = problemes(d)
        print(json.dumps({"analyse": d, "problemes": p},
                         ensure_ascii=False, indent=2))
        return 1 if p else 0
    la = lib.resoudre_affichage(a.langue_affichage, d["langue"])
    p = problemes(d, la)
    print(lib.t("traceability.titre", la))
    print("  " + lib.t("traceability.langue_analysee", la,
                       langue=d["langue"]))
    print("  " + lib.t("traceability.biblio", la,
                       presente=d["biblio_presente"],
                       n=len(d["references_definies"])))
    print("  " + lib.t("traceability.tags", la,
                       lacune=d["tags_lacune_materielle"],
                       preuve=d["tags_preuve_faible"]))
    compte = " | ".join(
        lib.t("traceability.objet_compte", la,
              objet=lib.valeur("traceability.objet", o, la),
              n=len(d["sequences"][o]["numeros"])) for o in OBJETS)
    print("  " + lib.t("traceability.objets_numerotes", la, compte=compte))
    if not p:
        print("  " + lib.t("traceability.aucun_probleme", la))
    for x in p:
        print(f"  - {x}")
    if d["tags_par_section"]:
        print("  " + lib.t("traceability.repartition", la))
        for titre, c in d["tags_par_section"].items():
            print("    " + lib.t("traceability.repartition_ligne", la,
                                 titre=titre, lacune=c["lacune_materielle"],
                                 preuve=c["preuve_faible"]))
    return 1 if p else 0


if __name__ == "__main__":
    sys.exit(main())
