# -*- coding: utf-8 -*-
"""Cas d'eval du cablage bilingue des onze scripts de controle.

Meme partage que evals/cas/affichage.py, applique au lot suivant :
check-droits, emprunts, check-fuites, check-disponibilite, check-lecture-pdf,
check-presentation, check-temporel, citations, coherence, ai-fingerprint,
tables.

Trois exigences, dans cet ordre.

La non-regression du francais. Les empreintes gelees plus bas ont ete
relevees sur la version HEAD des onze scripts, avant cablage, puis
recomparees apres : les quinze mesures etaient identiques. Les figer en
litteral fait echouer ce module si une sortie francaise bouge, au lieu de
suivre la derive en silence. Les mesures retenues sont deterministes : elles
ne dependent d'aucun backend PDF optionnel, faute de quoi l'empreinte
changerait d'une machine a l'autre sans qu'aucun code ait bouge.

La stabilite des valeurs machine. Verdicts, etats, niveaux de confiance et
noms de regle restent les chaines francaises actuelles meme en affichage
anglais : emprunts.py branche sur les verdicts de check-droits.py, plusieurs
modules de evals/cas/ les comparent litteralement, et tools/gold.py les
confronte aux etiquettes gelees de evals/gold/*/manifeste.json.

L'absence de libelle francais dans un rapport anglais. Le controle porte sur
les LIBELLES, pas sur les mots : un rapport anglais cite legitimement le
texte francais du document analyse, le nom d'une regle ou un titre de
section. Chercher des mots francais y produirait du bruit ; chercher la
chaine francaise exacte d'une cle de libelle ne s'y trompe pas.
"""
import copy
import hashlib
import json
import os
import re
import tempfile

# --- La garde, reprise de affichage.py plutot que reecrite ------------------
# Le module d'a cote definit deja l'heuristique et l'a eprouvee sur un temoin.
# En ecrire une seconde ici les ferait diverger. Seule sa tete est executee,
# celle qui precede ses propres cas : charger et lire sont neutralises, les
# fonctions de garde n'en ont pas besoin.
_SRC_GARDE = os.path.join(ICI, "cas", "affichage.py")
with open(_SRC_GARDE, encoding="utf-8") as _f:
    _TETE = _f.read().split("# --- Les cas ---")[0]
_ESPACE_GARDE = {"charger": lambda *a, **k: None, "lire": lambda *a, **k: "",
                 "verifier": lambda *a, **k: None}
exec(compile(_TETE, _SRC_GARDE, "exec"), _ESPACE_GARDE)
constats_non_cables = _ESPACE_GARDE["constats_non_cables"]

SCRIPTS_DU_LOT = (
    "check-droits.py", "emprunts.py", "check-fuites.py",
    "check-disponibilite.py", "check-lecture-pdf.py", "check-presentation.py",
    "check-temporel.py", "citations.py", "coherence.py", "ai-fingerprint.py",
    "tables.py")


lib_c = charger("libelles.py", "libelles_ctrl")
drt_c = charger("check-droits.py", "check_droits_ctrl")
emp_c = charger("emprunts.py", "emprunts_ctrl")
fui_c = charger("check-fuites.py", "check_fuites_ctrl")
dis_c = charger("check-disponibilite.py", "check_disponibilite_ctrl")
lec_c = charger("check-lecture-pdf.py", "check_lecture_pdf_ctrl")
pre_c = charger("check-presentation.py", "check_presentation_ctrl")
tem_c = charger("check-temporel.py", "check_temporel_ctrl")
cit_c = charger("citations.py", "citations_ctrl")
coh_c = charger("coherence.py", "coherence_ctrl")
aif_c = charger("ai-fingerprint.py", "ai_fingerprint_ctrl")
tab_c = charger("tables.py", "tables_ctrl")


# --- Les entrees -------------------------------------------------------------
# Ecrites ici plutot que posees en fixtures : elles ne servent qu'a ce module,
# et une entree lisible a cote de son attendu se relit sans ouvrir un
# deuxieme fichier. Les seules fixtures utilisees sont les binaires qui
# existent deja.

import datetime
DATE_REF = datetime.date(2026, 8, 18)

TABLEAU = ("| City | People | Score (out of 10) |\n| --- | --- | --- |\n"
           "| Alpha | 10 | 3 |\n| Beta | 20 |  |\n| Total | 40 | 5 |\n")

TEMPO = ("# Note\n\nLe lancement a eu lieu en 2099 selon la note interne.\n\n"
         "La reforme de 2022 a permis la croissance de 2018.\n\n"
         "C'est le dispositif le plus recent du secteur.\n\n"
         "## References\n\n1. Preprint arXiv 2024, publie dans la revue en "
         "2023.\n")

DISPO = ("<!-- lint-style:langue=en -->\n\n# Article\n\nBody.\n\n"
         "## Data availability\n\nThe data are openly available and the code "
         "is on https://github.com/example/repo. Raw data are available from "
         "the corresponding author upon reasonable request.\n")

BIBLIO = (
    "@article{smith2024,\n author={Smith, Jane and Roe, Paul},\n"
    " title={A repeated measurement of the device},\n"
    " journal={Journal of measurement},\n year={2024},\n volume={12},\n"
    " pages={3--18},\n doi={10.1000/measure.2024},\n"
    " annote={\"The results suggest a rise of 12 % in this sample.\"}\n}\n"
    "@article{incomplet2023,\n title={No author and no year},\n"
    " journal={Journal}\n}\n"
    "@typeinconnu{bizarre,\n title={Unknown shape}\n}\n")

DOC_ANCRE = ("# Control document\n\n"
             "The method demonstrates a rise of 27 % in all subjects. "
             "[smith2024]\n\nA claim with no resolved reference. "
             "[ghost2021]\n")

REGISTRE = {"figures": [
    {"id": "fig-1", "libelle": "Figure 1", "titre": "Load curve",
     "auteur": "Nguyen, Thi", "source": "Journal of measurement",
     "doi": "10.1000/measure.2024",
     "licence": "https://creativecommons.org/licenses/by/4.0/"},
    {"id": "fig-2", "libelle": "Figure 2", "source": "Closed journal",
     "url": "https://example.test/article",
     "licence": "https://www.elsevier.com/tdm/userlicense/1.0/",
     "modifications": "cropping"},
    {"id": "fig-3", "titre": "Overview", "auteur": "Roe, Dan",
     "source": "Internal report",
     "licence": "https://example.test/house-terms"},
    {"id": "fig-4", "libelle": "Figure 4", "titre": "Scatter plot",
     "auteur": "Doe, Jane", "source": "Conference proceedings",
     "doi": "10.1000/proc.2021",
     "licence": "https://creativecommons.org/licenses/by-nd/4.0/",
     "autorisation": {"etat": "demandee"}}]}

IMAGES_EMPRUNT = [
    {"origine": "p001-01.png", "fichier": "p001-01.png", "index": 1},
    {"origine": "p002-01.png", "fichier": "p002-01.png", "index": 2},
    {"origine": "p002-02.png", "fichier": "p002-02.png", "index": 3},
    {"origine": "img-04.png", "fichier": "img-04.png", "index": 4}]

LEGENDES_EMPRUNT = {1: emp_c.reperer_legendes("Figure 1. Load curve\n"),
                    2: emp_c.reperer_legendes("Figure 2. Scatter plot\n")}

ABSENT = os.path.join(FIXT, "fichier-qui-n-existe-pas.pdf")
MAUVAIS = lire("style-mauvais.md")


def _j(x):
    return json.dumps(x, ensure_ascii=False, indent=2, sort_keys=True,
                      default=str)


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _entrees_bib():
    return cit_c.parser_bibtex(BIBLIO)


def _sans_chemin(x):
    """Retire le chemin de la machine d'une mesure avant de la geler.

    Les deux mesures sur un fichier PDF absent rapportent le chemin qu'elles
    ont recu, et ce chemin contient la racine du depot : il differe entre une
    machine de developpement Windows et un conteneur Linux. L'empreinte gelee
    echouait donc en conteneur alors que le code etait identique, ce qui fait
    passer une difference d'environnement pour une regression. Seule la partie
    variable est neutralisee, le reste de la mesure reste compare.
    """
    brut = _j(x)
    # Du plus long au plus court : le chemin complet d'abord, sinon il
    # resterait son separateur, antislash sur Windows et barre oblique
    # ailleurs, ce qui suffisait a faire diverger l'empreinte apres que la
    # racine seule eut ete neutralisee.
    for chemin, jeton in ((ABSENT, "<ABSENT>"), (FIXT, "<FIXTURES>"),
                          (RACINE, "<RACINE>")):
        serialise = _j(chemin)[1:-1]
        if serialise:
            brut = brut.replace(serialise, jeton)
    return brut


def _sans_backend_pdf(module, mesure):
    """Force l'absence de tout backend PDF, puis mesure.

    Seconde cause de derive des deux mesures sur PDF, distincte du chemin et
    tout aussi silencieuse : une machine de developpement qui a installe pypdf
    ne rend pas le meme rapport qu'un conteneur vierge. Les deux causes se
    cumulaient, corriger la premiere laissait la seconde. Simuler l'absence
    rend la mesure identique partout, technique deja employee par
    evals/cas/lecture-pdf.py et par le harnais pour check-presentation.
    """
    cible = getattr(module, "_CHKP", module)
    vides = {"extraire_texte_pages": lambda c: (None, "aucun backend"),
             "rendre_pages_basses_res": lambda c, dpi=60: (None,
                                                           "aucun backend"),
             "compter_pages_et_taille": lambda c: (None, 0, "aucun backend")}
    sauve = {n: getattr(cible, n) for n in vides if hasattr(cible, n)}
    for n in sauve:
        setattr(cible, n, vides[n])
    try:
        return mesure()
    finally:
        for n, f in sauve.items():
            setattr(cible, n, f)


# Mesures francaises, toutes deterministes. Les deux qui touchent a un fichier
# PDF absent passent par _sans_chemin, sans quoi leur empreinte depend de
# l'emplacement du depot. Chacune est appelee SANS langue d'affichage,
# c'est-a-dire exactement comme le mode --format json l'appelle.
MESURES = {
    "tables": lambda: tab_c.auditer(TABLEAU),
    "coherence": lambda: {"analyse": coh_c.analyser(MAUVAIS),
                          "problemes": coh_c.problemes(
                              coh_c.analyser(MAUVAIS))},
    "ai_fingerprint": lambda: aif_c.analyser(MAUVAIS),
    "temporel": lambda: tem_c.analyser(TEMPO, date_reference=DATE_REF),
    "presentation": lambda: _sans_backend_pdf(
        pre_c, lambda: pre_c.analyser(ABSENT, 15)),
    "lecture_pdf": lambda: _sans_backend_pdf(
        lec_c, lambda: lec_c.analyser(ABSENT)),
    "fuites_docx": lambda: fui_c.analyser(os.path.join(FIXT,
                                                       "fuites-docx.docx")),
    "fuites_pdf": lambda: fui_c.analyser(
        os.path.join(FIXT, "fuites-pdf-incremental.pdf")),
    "disponibilite": lambda: dis_c.analyser(DISPO, "article.md"),
    "citations": lambda: {
        "ancrage": cit_c.rapport_ancrage(_entrees_bib()),
        "qualification": cit_c.rapport_qualification(_entrees_bib()),
        "validation": cit_c.rapport_validation(_entrees_bib()),
        "audit_fidelite": cit_c.auditer_fidelite(DOC_ANCRE, _entrees_bib())},
    "droits_registre": lambda: drt_c._sans_prive(
        drt_c.analyser(copy.deepcopy(REGISTRE))),
    "droits_licence": lambda: drt_c._sans_prive(
        drt_c.resoudre_doi("10.1000/example")),
    "droits_attribution": lambda: drt_c.ligne_attribution(
        {"id": "fig-9", "source": "Journal X"}),
    "emprunts_refus": lambda: emp_c._sans_prive(
        [emp_c.recuperer({"etat": e}, os.path.join(FIXT, "jamais-ecrit.pdf"))
         for e in ("acces non ouvert", "acces ouvert sans fichier",
                   "localisation inconnue")]),
    "emprunts_appariement": lambda: emp_c._sans_prive({
        "localisation": emp_c.localiser("10.1000/example"),
        "appariement": list(emp_c.apparier(IMAGES_EMPRUNT,
                                           LEGENDES_EMPRUNT)),
        "voies": emp_c.voies_de_repli("licence inconnue", "10.1000/example",
                                      "Nguyen")}),
}

EMPREINTES = {nom: _sans_chemin(mesure()) for nom, mesure in MESURES.items()}


# ===== CAS =====

# Empreintes relevees sur HEAD avant cablage, puis recomparees apres : les
# quinze etaient identiques. Gelees en litteral pour qu'une derive future du
# francais fasse echouer un cas au lieu de passer.
GELEES = {
    "ai_fingerprint":
        "06e895d4a0784f1c1f485537aaee498d4ae31cc6248c32634738a753483b2a4e",
    "citations":
        "b3a254098f5dc74eacf08dd42eb96398664836ca8a8ee4ae15e5972126a37d50",
    "coherence":
        "cdec34f2fb910092fafa0eef9ffa6e6557c8a36c2adb56de5acbb9f6cbb9b33d",
    "disponibilite":
        "9293e3b750aa236c342bf671534d90c2bf29218c7f4d51d4f14b23dabe20ba1d",
    "droits_attribution":
        "f3ba091820021d5559e64eaaa2c77e21e716a6b460f80173456afb06cf2b35a1",
    "droits_licence":
        "2678ebb3912104d953f36edd56843565ad6b9046e6bc7c42c7b94c8e0a49712a",
    "droits_registre":
        "d8546c62ebcef3b9308cf473178dbbf0e52371ff75bee6cbf0d4c298043d6ff8",
    "emprunts_appariement":
        "992d692502f56fda95031ef77256fc3455b2366b3dc49243f2d23c8445393d4a",
    "emprunts_refus":
        "0eb217803d0b383eb2d155d9d090d004e2c9d5738f8da749806d9fc9c0c5631c",
    "fuites_docx":
        "30b7cb437aad85d50ce29d73fed65dec1bb4c13584f355d83464912706abbb38",
    "fuites_pdf":
        "5f15e527a34cf484b90dbf19e962c60e41f614bce73cd27b7cd86a4ca81d060c",
    "lecture_pdf":
        "d0e74b07fd23251966816e937ba07ba5894253de02dda34be50493acf5f5da6f",
    "presentation":
        "9bf84acd63503472119a063eedd592a880c16f3360bc663eaa13d40719a6d485",
    "tables":
        "4827233e9834906b7a92567579e1bbfbda64ce821571d0fb10d10f74a1b27741",
    "temporel":
        "b4fa2c2b4caf4519bc772a1d914889b5c7a3a1bbca01eafe93140a5ae17f1822",
}

for _nom in sorted(GELEES):
    verifier("controles fige : %s inchange a l'octet pres" % _nom,
             _sha(EMPREINTES[_nom]) == GELEES[_nom],
             "%s != %s" % (_sha(EMPREINTES[_nom]), GELEES[_nom]))

# Une empreinte gelee qui contiendrait un chemin de la machine echouerait
# ailleurs que la ou elle a ete relevee, et signalerait une difference
# d'environnement en la faisant passer pour une regression. Deux d'entre
# elles portaient ce defaut, attrape en conteneur Linux et pas sur la machine
# de developpement. Ce cas garde l'ensemble, pas seulement les deux.
def _porte_un_chemin(empreinte):
    """La racine REELLE de cette machine, et rien d'autre.

    Deux critères plus larges ont ete essayes et abandonnes, chacun sur un
    faux positif instructif. Chercher le nom du dossier racine attrapait
    fuites_pdf, dont la fixture declare Scriptorium Test comme producteur du
    PDF. Chercher une forme de chemin absolu attrapait fuites_docx, dont la
    fixture porte un faux lien vers C:/Users/prenom.nom pour eprouver
    justement la detection de chemin local. Ces deux chemins sont des donnees
    de test, identiques partout, donc deterministes. Le seul defaut a traquer
    est la racine du depot sur la machine qui execute, la seule qui change
    d'un poste a l'autre.
    """
    racines = [r for r in (_j(RACINE)[1:-1], _j(FIXT)[1:-1]) if r]
    return any(r in empreinte for r in racines)


_avec_chemin = sorted(n for n, e in EMPREINTES.items() if _porte_un_chemin(e))
verifier("controles fige : aucune empreinte ne porte un chemin de la machine",
         not _avec_chemin, f"portent un chemin : {_avec_chemin}")


# --- Aucun libelle francais dans un rapport anglais --------------------------
# Le controle porte sur la chaine exacte du libelle, pas sur des mots isoles :
# un rapport anglais cite legitimement le texte francais du document analyse,
# le nom d'une regle ou un titre de section repere dans le document.

def _bascule(fr, en, cles):
    """Cles dont le libelle francais subsiste dans le rapport anglais, ou
    dont le libelle anglais manque, ou dont le francais manque au rapport
    francais. Ce dernier controle interdit de faire passer le cas en
    n'imprimant plus rien du tout.

    Une cle est soit un nom, soit un couple (nom, parametres) : un libelle
    parametre se compare une fois formate, sinon il ne se retrouverait dans
    aucun rapport."""
    restes = []
    for entree in cles:
        cle, params = entree if isinstance(entree, tuple) else (entree, {})
        f, a = lib_c.t(cle, "fr", **params), lib_c.t(cle, "en", **params)
        if f not in fr:
            restes.append("fr manquant dans le rapport fr : " + cle)
        if a not in en:
            restes.append("en manquant dans le rapport en : " + cle)
        if f != a and f in en:
            restes.append("fr residuel dans le rapport en : " + cle)
    return restes


def _ecrire(nom, contenu):
    """Fichier temporaire, pour les commandes qui prennent un chemin."""
    dossier = tempfile.mkdtemp(prefix="scriptorium_ctrl_")
    chemin = os.path.join(dossier, nom)
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenu)
    return chemin


DOCX = os.path.join(FIXT, "fuites-docx.docx")
PDF_NORMAL = os.path.join(FIXT, "pdf-normal.pdf")
PDF_EMPRUNTS = os.path.join(FIXT, "pdf-emprunts.pdf")


import contextlib
import io


def _sortie(mod, argv):
    """Sortie standard d'une commande, capturee : plusieurs de ces scripts
    n'exposent leur rapport texte que par leur ligne de commande."""
    tampon = io.StringIO()
    with contextlib.redirect_stdout(tampon):
        mod.main(argv)
    return tampon.getvalue()


def _paire(mod, argv):
    """Le meme rapport dans les deux langues d'affichage."""
    return _sortie(mod, argv), _sortie(mod, argv + ["--langue-affichage",
                                                    "en"])


TEXTE_PROPRE = ("A short control text. The device holds over three periods. "
                "The measurement is dated and repeated.\n")

_f_tableau = _ecrire("tableau.md", TABLEAU)
_fr, _en = _paire(tab_c, ["audit", _f_tableau])
verifier("anglais : le rapport de tables.py bascule ses libelles",
         not _bascule(_fr, _en, [
             ("tables.titre", {"tables": 1}),
             ("tables.p.cellule_vide",
              {"n": 1, "ligne": 2, "colonne": "Score (out of 10)"}),
             ("tables.p.total_incoherent",
              {"n": 1, "colonne": "Score (out of 10)", "total": 5.0,
               "somme": 3.0})]),
         str(_bascule(_fr, _en, [("tables.titre", {"tables": 1})])))

_f_propre = _ecrire("propre.md", TEXTE_PROPRE)
_fr, _en = _paire(coh_c, [_f_propre])
verifier("anglais : le rapport de coherence.py bascule ses libelles",
         not _bascule(_fr, _en, ["coherence.titre",
                                 "coherence.aucune_redite"]),
         str(_bascule(_fr, _en, ["coherence.titre",
                                 "coherence.aucune_redite"])))

_fr, _en = _paire(aif_c, [_f_propre])
verifier("anglais : le rapport de ai-fingerprint.py bascule ses libelles",
         not _bascule(_fr, _en, ["aifp.titre", "aifp.aucun_signal"]),
         str(_bascule(_fr, _en, ["aifp.titre", "aifp.aucun_signal"])))


_f_tempo = _ecrire("tempo.md", TEMPO)
_fr, _en = _paire(tem_c, [_f_tempo, "--date-reference", "2026-08-18"])
verifier("anglais : le rapport de check-temporel.py bascule ses libelles",
         not _bascule(_fr, _en, [
             ("temporel.titre", {"chemin": _f_tempo}),
             ("temporel.m.langage_peremption",
              {"tournure": "le plus recent"})]),
         str(_bascule(_fr, _en, [("temporel.titre", {"chemin": _f_tempo})])))

_CLES_PRESENTATION = [("presentation.titre",
                       {"fichier": os.path.basename(ABSENT)}),
                      ("presentation.m.fichier_introuvable",
                       {"chemin": ABSENT}),
                      "presentation.info_aucune", "presentation.problemes"]
_fr, _en = _paire(pre_c, [ABSENT, "--duree", "15"])
verifier("anglais : le rapport de check-presentation.py bascule ses libelles",
         not _bascule(_fr, _en, _CLES_PRESENTATION),
         str(_bascule(_fr, _en, _CLES_PRESENTATION)))

_CLES_LECTURE = [("lecture.titre", {"fichier": os.path.basename(ABSENT)}),
                 ("lecture.m.fichier_introuvable", {"chemin": ABSENT}),
                 "lecture.info_aucune", "lecture.problemes"]
_fr, _en = _paire(lec_c, [ABSENT])
verifier("anglais : le rapport de check-lecture-pdf.py bascule ses libelles",
         not _bascule(_fr, _en, _CLES_LECTURE),
         str(_bascule(_fr, _en, _CLES_LECTURE)))

_CLES_FUITES = ["fuites.partage", "fuites.non_verifie", "fuites.nv.contenu",
                "fuites.nv.images", "fuites.cat.identite"]
_fr, _en = _paire(fui_c, [DOCX])
verifier("anglais : le rapport de check-fuites.py bascule ses libelles",
         not _bascule(_fr, _en, _CLES_FUITES),
         str(_bascule(_fr, _en, _CLES_FUITES)))

_CLES_DISPO = ["dispo.non_verifie", "dispo.nv.identifiant", "dispo.nv.depot",
               "dispo.cat.regime"]
_f_dispo = _ecrire("dispo.md", DISPO)
# Le manuscrit porte le pragme lint-style:langue=en : la langue d'affichage
# par defaut le suit, et il faut demander le francais explicitement pour
# obtenir le rapport francais. C'est ce que verifie le cas suivant.
_fr = _sortie(dis_c, [_f_dispo, "--langue-affichage", "fr"])
_en = _sortie(dis_c, [_f_dispo, "--langue-affichage", "en"])
verifier("anglais : le rapport de check-disponibilite.py bascule ses "
         "libelles",
         not _bascule(_fr, _en, _CLES_DISPO),
         str(_bascule(_fr, _en, _CLES_DISPO)))

verifier("defaut : le pragme du document suffit, sans option le rapport de "
         "check-disponibilite.py sort dans la langue du manuscrit",
         _sortie(dis_c, [_f_dispo]) == _en
         and _en != _fr,
         _sortie(dis_c, [_f_dispo]).splitlines()[0])


_f_bib = _ecrire("biblio.bib", BIBLIO)
_CLES_CITATIONS = [("citations.champs_manquants", {"n": 1}),
                   ("citations.type_non_reconnu", {"types": ["bizarre"]})]
_fr, _en = _paire(cit_c, [_f_bib, "--to", "vancouver", "--valider"])
verifier("anglais : le rapport de citations.py bascule ses libelles",
         not _bascule(_fr, _en, _CLES_CITATIONS),
         str(_bascule(_fr, _en, _CLES_CITATIONS)))

_f_registre = _ecrire("registre.json", json.dumps(REGISTRE,
                                                  ensure_ascii=False))
_CLES_DROITS = [("droits.reg.figures", {"n": 4}),
                "droits.c.attribution_complete",
                ("droits.lic.limite",
                 {"limite": lib_c.t("droits.limite", "fr")})]
_fr, _en = _paire(drt_c, ["registre", _f_registre])
verifier("anglais : le rapport de check-droits.py bascule ses libelles",
         not _bascule(_fr, _en, [c for c in _CLES_DROITS
                                 if c != _CLES_DROITS[2]])
         and lib_c.t("droits.limite", "en") in _en
         and lib_c.t("droits.limite", "fr") not in _en,
         str(_bascule(_fr, _en, _CLES_DROITS[:2])))

_CLES_EMPRUNTS = [("emprunts.loc.titre", {"doi": "10.1000/example"}),
                  ("emprunts.garde_fou_ligne",
                   {"garde_fou": lib_c.t("emprunts.garde_fou", "fr")})]
_fr, _en = _paire(emp_c, ["localiser", "--doi", "10.1000/example"])
verifier("anglais : le rapport de emprunts.py bascule ses libelles",
         not _bascule(_fr, _en, [_CLES_EMPRUNTS[0]])
         and lib_c.t("emprunts.garde_fou", "en") in _en
         and lib_c.t("emprunts.garde_fou", "fr") not in _en,
         str(_bascule(_fr, _en, [_CLES_EMPRUNTS[0]])))


# --- Le refus d'emprunts.py, aussi ferme en anglais qu'en francais ----------
# Ce message n'est pas un incident technique a contourner : il dit pourquoi
# le script ne descendra pas plus bas. Une version anglaise attenuee le
# ferait lire comme un obstacle a franchir.

_refus = emp_c.recuperer({"etat": "acces non ouvert"}, "x.pdf")
_refus_en = emp_c.recuperer({"etat": "acces non ouvert"}, "x.pdf",
                            langue_affichage="en")

verifier("refus : la version anglaise nomme le refus, la conduite a tenir et "
         "le garde-fou, tient la meme longueur, et l'etat machine ne bouge "
         "pas",
         all(m in _refus_en["message"]
             for m in ("Retrieval refused", "is not worked around",
                       "references/droits-figures.md", "no credentials"))
         and lib_c.t("emprunts.garde_fou", "en") in _refus_en["message"]
         and 0.75 <= (len(_refus_en["message"])
                      / len(_refus["message"])) <= 1.25
         and _refus_en["etat"] == _refus["etat"] == "refus source non ouverte",
         "%s | %d vs %d | %s" % (_refus_en["message"][:60],
                                 len(_refus_en["message"]),
                                 len(_refus["message"]), _refus_en["etat"]))


# --- Les valeurs machine ne bougent pas en affichage anglais -----------------

_dr_en = drt_c._sans_prive(drt_c.analyser(copy.deepcopy(REGISTRE),
                                          langue_affichage="en"))
_dr_fr = drt_c._sans_prive(drt_c.analyser(copy.deepcopy(REGISTRE)))
verifier("machine : les verdicts de check-droits.py restent francais en "
         "affichage anglais, et sa sortie JSON passe par le chemin sans "
         "langue",
         _dr_en["verdict"] == _dr_fr["verdict"]
         and _dr_en["verdict"] in drt_c.VERDICTS_REGISTRE
         and [f["verdict"] for f in _dr_en["figures"]]
         == [f["verdict"] for f in _dr_fr["figures"]]
         and all(f["verdict"] in drt_c.VERDICTS for f in _dr_en["figures"])
         and _j(_dr_fr) == EMPREINTES["droits_registre"],
         str(_dr_en["verdict"]))

_fu_en = fui_c.analyser(DOCX, langue_affichage="en")
_fu_fr = fui_c.analyser(DOCX)
verifier("machine : verdict, regle, confiance et categorie de "
         "check-fuites.py restent francais en affichage anglais",
         _fu_en["verdict"] == _fu_fr["verdict"]
         and [(c["regle"], c["confiance"], c["categorie"])
              for c in _fu_en["constats"]]
         == [(c["regle"], c["confiance"], c["categorie"])
             for c in _fu_fr["constats"]],
         str(_fu_en["verdict"]))

_di_en = dis_c.analyser(DISPO, "article.md", langue_affichage="en")
_di_fr = dis_c.analyser(DISPO, "article.md")
verifier("machine : verdict, regime et nom de regle de "
         "check-disponibilite.py restent francais en affichage anglais",
         _di_en["verdict"] == _di_fr["verdict"]
         and _di_en["regimes"] == _di_fr["regimes"]
         and _di_en["verdict"] in dis_c.VERDICTS
         and all(r in dis_c.REGIMES for r in _di_en["regimes"])
         and [c["regle"] for c in _di_en["constats"]]
         == [c["regle"] for c in _di_fr["constats"]],
         str(_di_en["verdict"]))


_ap_en = emp_c.apparier(IMAGES_EMPRUNT, LEGENDES_EMPRUNT,
                        langue_affichage="en")[0]
_ap_fr = emp_c.apparier(IMAGES_EMPRUNT, LEGENDES_EMPRUNT)[0]
verifier("machine : niveau de confiance et etat de emprunts.py restent "
         "francais, seuls motif et detail changent de langue",
         [a["niveau"] for a in _ap_en] == [a["niveau"] for a in _ap_fr]
         and all(a["niveau"] in emp_c.NIVEAUX_CONFIANCE for a in _ap_en)
         and emp_c.localiser("10.1000/x", langue_affichage="en")["etat"]
         == "localisation inconnue"
         and [sorted(a) for a in _ap_en] == [sorted(a) for a in _ap_fr]
         and any(a["motif"] != b["motif"] for a, b in zip(_ap_en, _ap_fr)),
         str([a["niveau"] for a in _ap_en]))

_json_dispo = _sortie(dis_c, [_f_dispo, "--format", "json",
                              "--langue-affichage", "en"])
_json_fuites = _sortie(fui_c, [DOCX, "--format", "json",
                               "--langue-affichage", "en"])
verifier("cli : --format json reste francais meme quand l'anglais est "
         "demande, sur un manuscrit comme sur un binaire",
         lib_c.t("dispo.nv.identifiant", "fr") in _json_dispo
         and lib_c.t("dispo.nv.identifiant", "en") not in _json_dispo
         and lib_c.t("fuites.nv.contenu", "fr") in _json_fuites
         and lib_c.t("fuites.nv.contenu", "en") not in _json_fuites,
         _json_dispo[:60] + " | " + _json_fuites[:60])


# --- La garde du lot precedent ne releve plus rien sur les onze -------------

_restes = {f: constats_non_cables(os.path.join(SCRIPTS, f))
           for f in SCRIPTS_DU_LOT}
# Le compte et l'existence des onze fichiers entrent dans la condition : sans
# eux, le cas passerait sur une liste vide, ce qui ne prouverait rien.
verifier("garde : aucun des onze scripts de controle n'imprime encore une "
         "chaine francaise hors libelles",
         len(_restes) == 11
         and all(os.path.isfile(os.path.join(SCRIPTS, f))
                 for f in SCRIPTS_DU_LOT)
         and not any(_restes.values()),
         str({f: v for f, v in _restes.items() if v} or sorted(_restes)))
