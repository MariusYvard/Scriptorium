# -*- coding: utf-8 -*-
"""Cas d'eval du cablage bilingue des dix scripts d'outillage.

Meme partage que evals/cas/affichage.py et evals/cas/affichage-controles.py,
applique au dernier lot : terminology, numbers, figures, gabarit, logos,
images, plan-check, project, theme, diff-versions.

Quatre exigences, dans cet ordre.

La non-regression du francais. Les treize empreintes gelees plus bas ont ete
relevees sur la version HEAD des dix scripts, extraite dans un dossier
temporaire, puis recomparees a l'arbre cable : les treize mesures etaient
identiques. Les figer en litteral fait echouer ce module si une sortie
francaise bouge, au lieu de suivre la derive en silence. Les mesures retenues
sont deterministes : aucune ne depend d'un backend optionnel, d'un chemin
absolu ni d'un horodatage.

La stabilite des valeurs machine. Verdicts de gabarit et d'images, gravites,
noms de regle, etats d'etape et types d'objet restent les chaines francaises
en affichage anglais, dans les structures comme dans le JSON.

Ce qu'un script ECRIT ne suit pas la langue d'affichage. Trois fichiers sont
en jeu : le catalogue d'images, l'inventaire de gabarit et le journal de
projet. Ce sont des donnees relues plus tard, par une autre commande ou une
autre session ; un fichier dont le contenu changerait de langue selon la
commande qui l'a produit ne se comparerait plus a lui-meme, et le hash de
continuite d'une frontiere de projet changerait sans qu'aucune decision n'ait
bouge.

L'absence de libelle francais dans un rapport anglais. Le controle porte sur
les LIBELLES, pas sur les mots : un rapport anglais cite legitimement un nom
de style, un nom de disposition, une cle de donnees ou un terme de glossaire
venus du fichier analyse. Chercher des mots francais y produirait du bruit ;
chercher la chaine francaise exacte d'une cle de libelle ne s'y trompe pas.
"""
import contextlib
import copy
import hashlib
import io
import json
import os
import shutil
import struct
import tempfile

# --- La garde, reprise de affichage.py plutot que reecrite ------------------
# Deux modules la reprennent deja ainsi. En ecrire une troisieme copie les
# ferait diverger. Seule la tete de affichage.py est executee, celle qui
# precede ses propres cas.
_SRC_GARDE = os.path.join(ICI, "cas", "affichage.py")
with open(_SRC_GARDE, encoding="utf-8") as _f:
    _TETE = _f.read().split("# --- Les cas ---")[0]
_ESPACE_GARDE = {"charger": lambda *a, **k: None, "lire": lambda *a, **k: "",
                 "verifier": lambda *a, **k: None}
exec(compile(_TETE, _SRC_GARDE, "exec"), _ESPACE_GARDE)
constats_non_cables = _ESPACE_GARDE["constats_non_cables"]

SCRIPTS_DU_LOT = ("terminology.py", "numbers.py", "figures.py", "gabarit.py",
                  "logos.py", "images.py", "plan-check.py", "project.py",
                  "theme.py", "diff-versions.py")

lib_o = charger("libelles.py", "libelles_outils")
term_o = charger("terminology.py", "terminology_outils")
nums_o = charger("numbers.py", "numbers_outils")
planc_o = charger("plan-check.py", "plan_check_outils")
diffv_o = charger("diff-versions.py", "diff_versions_outils")
theme_o = charger("theme.py", "theme_outils")
figs_o = charger("figures.py", "figures_outils")
logo_o = charger("logos.py", "logos_outils")
imgs_o = charger("images.py", "images_outils")
gab_o = charger("gabarit.py", "gabarit_outils")
proj_o = charger("project.py", "project_outils")


# --- Les entrees -------------------------------------------------------------
# Ecrites ici plutot que posees en fixtures : elles ne servent qu'a ce module,
# et une entree lisible a cote de son attendu se relit sans ouvrir un
# deuxieme fichier. Les seules fixtures employees sont les binaires qui
# existent deja (gabarits et logos).

TEXTE_TERMINO = (
    "# Note\n\nLa methode HACCP est utilisee partout. Le systeme "
    "d'information (SI) est decrit. Le SI arrive avant sa definition ?\n\n"
    "Le porte-parole et le porteparole se relaient.\n")

TEXTE_NOMBRES = (
    "Un taux de 120 % apparait. Les parts font 40 %, 35 % et 20 %.\n"
    "Valeurs 1,5 et 2.5 melangees.\n")

PLAN = {"genre": "rapport-technique",
        "sections": ["Introduction", "Methode", "Resultats", "Conclusion"]}
DOC_PLAN = "# Introduction\n\nTexte.\n\n# Methode\n\nTexte.\n\n# Annexe\n\nX.\n"

ANCIEN = "# A\n\nun deux trois\n\n# B\n\nancien contenu\n"
NOUVEAU = "# A\n\nun deux trois quatre\n\n# C\n\nnouveau contenu\n"

CHARTE = {"encre": "#8A8A8A", "fond": "#9C9C9C", "accent": "zz",
          "palette": ["#CC3333", "#33CC33", "#F4F1EC", "#EEF2F4"]}

FIG_SWOT = {"forces": ["a"], "faiblesses": ["b"], "opportunites": ["c"]}
FIG_BCG = {"items": [{"nom": "X", "croissance": 50, "part": 140},
                     {"croissance": 10, "part": 20}]}
FIG_TSM = {"tam": {"libelle": "T", "valeur": "10"},
           "sam": {"libelle": "S", "valeur": "50"},
           "som": {"libelle": "O", "valeur": ""}}
FIG_COURBE = {"series": [{"nom": "", "points": [[1, 2], [2, 3]],
                          "erreurs": [1]}]}
FIG_HISTO = {"barres": [{"categorie": "A", "valeur": "x"},
                        {"categorie": "A"}],
             "axe_y": {"titre": "y", "unite": "m", "min": 5}}
FIG_BOITE = {"groupes": [{"nom": "G", "valeurs": [3, 1]},
                         {"nom": "G", "valeurs": []}]}
FIG_FLUX = {"niveaux": [{"titre": "", "boites": [{"libelle": ""}]}]}
FIG_PRISMA = {"identifiees": 100, "doublons": 10, "examinees": 80,
              "evaluees": 40, "incluses": 0,
              "ecartees_titre": [["hors sujet", None]],
              "ecartees_texte": []}

REGISTRE = {"_racine": FIXT, "logos": [
    {"id": "ecole", "fichier": "logo-ecole.png", "rang": 1,
     "usages": ["page-garde", "en-tete"], "respiration": 0.3},
    {"id": "labo", "fichier": "logo-basse-def.png", "rang": 2,
     "usages": ["page-garde", "co-signature"]},
    {"id": "fantome", "fichier": "absent.png", "usages": ["page-garde"]}]}

# Journal de mission ecrit a la main : les horodatages y sont fixes, sinon
# l'empreinte gelee changerait a chaque seconde qui passe.
PROJET = {
    "titre": "Etude de cas", "genre": "memoire-recherche",
    "problematique": "Le dispositif tient-il sur trois exercices ?",
    "glossaire": {"banc d'essai": "montage instrumente"},
    "objets_numerotes": [
        {"type": "figure", "numero": 1, "libelle": "Schema du banc",
         "maj": "2026-08-18T09:00:00+00:00"},
        {"type": "tableau", "numero": 1, "libelle": "Conditions",
         "maj": "2026-08-18T09:00:00+00:00"}],
    "etapes": {"cadrage": {"etat": "termine",
                           "maj": "2026-08-18T09:00:00+00:00"},
               "redaction": {"etat": "saute", "motif": "hors perimetre",
                             "maj": "2026-08-18T09:05:00+00:00"}},
    "artefacts": {"rapport": {"version": "v2",
                              "maj": "2026-08-18T09:10:00+00:00"}},
    "journal": [
        {"type": "frontiere", "horodatage": "2026-08-18T09:15:00+00:00",
         "libelle": "fin de cadrage", "hash": "abc123def456",
         "decision_attente": "choisir le corpus", "seq": 0},
        {"type": "reproductibilite",
         "horodatage": "2026-08-18T09:20:00+00:00",
         "plugin_version": "0.13.0", "modele": "claude",
         "stochasticite_declaree": proj_o.STOCHASTICITE_DECLAREE, "seq": 1},
        {"type": "outrepassement", "horodatage": "2026-08-18T09:25:00+00:00",
         "libelle": "seuil force", "cran": 1, "seq": 2}],
}

SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50">'
       '<rect width="100" height="50" fill="#16314E"/></svg>')


def _png(largeur, hauteur):
    """PNG minimal : en-tete IHDR aux dimensions voulues. Le catalogue lit les
    dimensions dans l'en-tete, jamais les pixels."""
    ihdr = (b"IHDR" + struct.pack(">II", largeur, hauteur)
            + b"\x08\x06\x00\x00\x00")
    return (b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + ihdr
            + b"\x00\x00\x00\x00" + b"\x00\x00\x00\x00IEND\xaeB`\x82")


def _dossier_images():
    """Dossier d'illustrations en vrac : une photo nette, une capture
    sous-definie, un doublon exact, un vectoriel et un fichier hors
    perimetre. Chaque verdict du catalogue y est represente."""
    d = tempfile.mkdtemp(prefix="scriptorium_outils_")
    with open(os.path.join(d, "photo.png"), "wb") as f:
        f.write(_png(2400, 1600))
    with open(os.path.join(d, "capture.png"), "wb") as f:
        f.write(_png(600, 400))
    with open(os.path.join(d, "z-copie.png"), "wb") as f:
        f.write(_png(2400, 1600))
    with open(os.path.join(d, "figure.svg"), "w", encoding="utf-8") as f:
        f.write(SVG)
    with open(os.path.join(d, "notes.txt"), "w", encoding="utf-8") as f:
        f.write("releve")
    return d


def _j(x):
    return json.dumps(x, ensure_ascii=False, indent=2, sort_keys=True,
                      default=str)


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _sans_backend(fn):
    """Execute fn en declarant qu'aucun backend de conversion SVG n'est
    present : sans cette neutralisation, l'empreinte dependrait des outils
    installes sur la machine."""
    vrais = imgs_o.backends_svg_disponibles
    imgs_o.backends_svg_disponibles = lambda: []
    try:
        return fn()
    finally:
        imgs_o.backends_svg_disponibles = vrais


DOSSIER_IMG = _dossier_images()
GAB_DOCX = os.path.join(FIXT, "gabarit-ecole.docx")
GAB_PPTX = os.path.join(FIXT, "gabarit-deck.pptx")
GAB_PDF = os.path.join(FIXT, "gabarit-rendu.pdf")
DOC_DEVIE = os.path.join(FIXT, "document-devie.docx")
PDF_DEVIE = os.path.join(FIXT, "rendu-devie.pdf")

# Mesures francaises. Chacune est appelee SANS langue d'affichage, c'est-a-dire
# exactement comme le mode --format json les appelle. Les chemins absolus et
# les horodatages sont retires : ils varient d'une machine a l'autre sans
# qu'aucun code n'ait bouge.
D_TERM = term_o.analyser(TEXTE_TERMINO)
D_NUMS = nums_o.analyser(TEXTE_NOMBRES)
TH = theme_o.charger(CHARTE)
ERR_TH, WARN_TH = theme_o.valider(TH)
ERR_LOGO, AVIS_LOGO = logo_o.valider(REGISTRE)
FRAG_LOGO, AVIS_FRAG = logo_o.fragment(REGISTRE, "page-garde", "docx")
CONV = _sans_backend(lambda: imgs_o.convertir(
    os.path.join(DOSSIER_IMG, "figure.svg"),
    os.path.join(DOSSIER_IMG, "figure.png")))
CONV_STABLE = {k: v for k, v in CONV.items() if k not in ("source", "sortie")}
CAT = imgs_o.cataloguer(DOSSIER_IMG, largeur_cm=15.0, usage="impression")
CAT_STABLE = {k: v for k, v in CAT.items()
              if k not in ("dossier", "fichier_catalogue")}
INV = gab_o.inventorier(GAB_DOCX)
INV_STABLE = {k: v for k, v in INV.items() if k != "source_chemin"}
CMP_DEVIE = gab_o.comparer(INV, DOC_DEVIE)
INVP = gab_o.inventorier(GAB_PPTX)
INVPDF = gab_o.inventorier(GAB_PDF)
CMP_PDF = gab_o.comparer(INVPDF, PDF_DEVIE)
PASSATION = proj_o.passation_redacteur(copy.deepcopy(PROJET))

MESURES = {
    "terminology": _j({"analyse": D_TERM,
                       "problemes": term_o.problemes(D_TERM)}),
    "numbers": _j({"analyse": D_NUMS, "problemes": nums_o.problemes(D_NUMS)}),
    "plan_check": _j(planc_o.analyser(PLAN, DOC_PLAN)),
    "diff_versions": _j(diffv_o.comparer(ANCIEN, NOUVEAU)),
    "theme": _j({"theme": TH, "erreurs": ERR_TH, "avertissements": WARN_TH}),
    "figures_audit": _j({
        "swot": figs_o.auditer("swot", FIG_SWOT),
        "bcg": figs_o.auditer("bcg", FIG_BCG),
        "tam-sam-som": figs_o.auditer("tam-sam-som", FIG_TSM),
        "courbe": figs_o.auditer("courbe", FIG_COURBE),
        "histogramme": figs_o.auditer("histogramme", FIG_HISTO),
        "boite": figs_o.auditer("boite", FIG_BOITE),
        "flux": figs_o.auditer("flux", FIG_FLUX),
        "prisma": figs_o.auditer("prisma", FIG_PRISMA),
        "charte": figs_o.auditer("swot", FIG_SWOT, CHARTE)}),
    "logos": _j({"erreurs": ERR_LOGO, "avertissements": AVIS_LOGO,
                 "fragment_avis": AVIS_FRAG}),
    "images": _j({"catalogue": CAT_STABLE, "conversion": CONV_STABLE}),
    "gabarit_inventaire": _j(INV_STABLE),
    "gabarit_comparaison": _j(CMP_DEVIE),
    "gabarit_pptx": _j({k: v for k, v in INVP.items()
                        if k != "source_chemin"}),
    "gabarit_pdf": _j({"inventaire": {k: v for k, v in INVPDF.items()
                                      if k != "source_chemin"},
                       "comparaison": CMP_PDF}),
    "project": _j({"passation": PASSATION,
                   "passation_texte": proj_o.passation_texte(PASSATION),
                   "statut_texte": proj_o.statut_texte(PROJET)}),
}


# ===== CAS =====

# --- 1. Le francais ne bouge pas ---------------------------------------------
# Empreintes relevees sur HEAD avant cablage, dans un dossier temporaire ou
# les vingt-sept scripts d'origine ont ete extraits, puis recomparees apres :
# les treize etaient identiques. Gelees ici en litteral pour qu'une derive
# future du francais fasse echouer un cas au lieu de passer.
GELEES = {
    "diff_versions":
        "6a9f0fdee29a637e3e3342188eef456068219a7a7a029bcfebf8b8e534e3249b",
    "figures_audit":
        "48ca4fc9130fb0ea79202b35804ffda8de680cf1e58b62369d81b59b41746a66",
    "gabarit_comparaison":
        "f9370fa857e7a6a1632d0cf136bc3c667c1eb08e45238b922f822a4174d05e0b",
    "gabarit_inventaire":
        "d0839aab016a3325091a336f6e69609b2e9936eb92cd634c9d9da9adbdb2fdb1",
    "gabarit_pdf":
        "04a3209b6c32cc78c0501f95f94024c9356914111ab9416551dce83e80649b37",
    "gabarit_pptx":
        "034a389e1c53cdf3c563fd942e8f53fba03a877636844d58e10e69be86d13e1f",
    "images":
        "cc35c100f552fb5351a127f4c0d597ac4e817b0d251409c91ef55e5da1093660",
    "logos":
        "94d86c8c003a1d44b33e13e59e6ea4a66d04e56c3f8fa76065970b672a3ebd92",
    "numbers":
        "89e7065b9e23b359d11edd2212b8a048a17f63b904e4c76907129512e567e301",
    "plan_check":
        "82a7da811262c516956447d55272c0eeb5d097e6e40e9c76d1a538870804af91",
    "project":
        "c7e2e55e1c4dbbc78588324715ad17fdbe27253d28002af448bcecadba7b39bb",
    "terminology":
        "dc1f7f7a6615c7a2df45a671ffde71384af3b9b2892e24d2eead8d452fbfce5b",
    "theme":
        "7efcbb4f8038469e4728ab370f7bd37d8a181bb3e3b87c825516eb70dd5076c2",
}

for _nom in sorted(GELEES):
    verifier("outils fige : %s inchange a l'octet pres" % _nom,
             _sha(MESURES[_nom]) == GELEES[_nom],
             "%s != %s" % (_sha(MESURES[_nom]), GELEES[_nom]))


# --- 2. Aucun libelle francais dans un rapport anglais -----------------------

def _bascule(fr, en, cles):
    """Cles dont le libelle francais subsiste dans le rapport anglais, ou dont
    le libelle anglais manque, ou dont le francais manque au rapport francais.
    Ce dernier controle interdit de faire passer le cas en n'imprimant plus
    rien du tout.

    Une cle est soit un nom, soit un couple (nom, parametres) : un libelle
    parametre se compare une fois formate, sinon il ne se retrouverait dans
    aucun rapport."""
    restes = []
    for entree in cles:
        cle, params = entree if isinstance(entree, tuple) else (entree, {})
        f, a = lib_o.t(cle, "fr", **params), lib_o.t(cle, "en", **params)
        if f not in fr:
            restes.append("fr manquant dans le rapport fr : " + cle)
        if a not in en:
            restes.append("en manquant dans le rapport en : " + cle)
        if f != a and f in en:
            restes.append("fr residuel dans le rapport en : " + cle)
    return restes


def _sortie(mod, argv):
    """Sortie standard d'une commande, capturee."""
    tampon = io.StringIO()
    with contextlib.redirect_stdout(tampon):
        mod.main(argv)
    return tampon.getvalue()


def _ecrire(nom, contenu):
    dossier = tempfile.mkdtemp(prefix="scriptorium_outils_")
    chemin = os.path.join(dossier, nom)
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenu)
    return chemin


def _cas_bascule(nom, fr, en, cles):
    verifier("anglais : le rapport de %s bascule ses libelles" % nom,
             not _bascule(fr, en, cles), str(_bascule(fr, en, cles)))


_f_term = _ecrire("note.md", TEXTE_TERMINO)
_cas_bascule(
    "terminology.py", _sortie(term_o, [_f_term]),
    _sortie(term_o, [_f_term, "--langue-affichage", "en"]),
    ["terminology.titre",
     ("terminology.p.non_definis", {"n": D_TERM["sigles_non_definis"]}),
     ("terminology.p.variantes",
      {"formes": D_TERM["variantes_orthographiques"][0]})])

_f_nums = _ecrire("nombres.md", TEXTE_NOMBRES)
_cas_bascule(
    "numbers.py", _sortie(nums_o, [_f_nums]),
    _sortie(nums_o, [_f_nums, "--langue-affichage", "en"]),
    ["numbers.titre", ("numbers.langue_analysee", {"langue": "fr"}),
     ("numbers.p.impossibles", {"n": D_NUMS["pourcentages_impossibles"]}),
     "numbers.p.separateur_mixte"])

_D_PLAN = planc_o.analyser(PLAN, DOC_PLAN)
_cas_bascule(
    "plan-check.py", planc_o.rapport_texte(_D_PLAN),
    planc_o.rapport_texte(_D_PLAN, "en"),
    [("plan.titre", {"couverture": _D_PLAN["couverture_pct"]}),
     ("plan.manquantes", {"sections": _D_PLAN["sections_manquantes"]}),
     ("plan.hors_plan", {"sections": _D_PLAN["sections_hors_plan"]})])

_D_DIFF = diffv_o.comparer(ANCIEN, NOUVEAU)
_cas_bascule(
    "diff-versions.py", diffv_o.rapport_texte(_D_DIFF),
    diffv_o.rapport_texte(_D_DIFF, "en"),
    ["diff.titre", ("diff.mots", {"avant": _D_DIFF["mots_ancien"],
                                  "apres": _D_DIFF["mots_nouveau"],
                                  "similitude": _D_DIFF["similitude_globale"]}),
     ("diff.ajoutees", {"sections": _D_DIFF["sections_ajoutees"]}),
     ("diff.supprimees", {"sections": _D_DIFF["sections_supprimees"]})])

_f_charte = _ecrire("charte.json", json.dumps(CHARTE, ensure_ascii=False))
_cas_bascule(
    "theme.py", _sortie(theme_o, [_f_charte]),
    _sortie(theme_o, [_f_charte, "--langue-affichage", "en"]),
    ["theme.titre", "theme.erreurs", "theme.avertissements",
     ("theme.v.couleur_invalide", {"cle": "accent", "valeur": "zz"})])


_cas_bascule(
    "figures.py", "\n".join(figs_o.auditer("prisma", FIG_PRISMA)),
    "\n".join(figs_o.auditer("prisma", FIG_PRISMA, langue_affichage="en")),
    # Les cles retenues ne portent que des parametres chiffres. Un libelle
    # dont un parametre se traduit lui-meme (le nom d'etape PRISMA) ne se
    # compare pas ainsi : le meme couple de parametres donnerait deux phrases
    # differentes, et le controle mordrait sur sa propre mise en forme.
    ["figures.a.aucune_incluse",
     ("figures.a.identification_non_bouclee",
      {"identifiees": 100, "doublons": 10, "attendu": 90, "examinees": 80})])

_ERR_LOGO_EN, _AVIS_LOGO_EN = logo_o.valider(REGISTRE, "en")
_cas_bascule(
    "logos.py", "\n".join(ERR_LOGO + AVIS_LOGO),
    "\n".join(_ERR_LOGO_EN + _AVIS_LOGO_EN),
    [("logos.e.fichier_absent", {"etiquette": "fantome",
                                 "fichier": "absent.png"}),
     ("logos.a.matriciel", {"etiquette": "ecole", "ext": "png"}),
     ("logos.a.matriciel", {"etiquette": "labo", "ext": "png"})])

_cas_bascule(
    "images.py", imgs_o.catalogue_texte(CAT),
    imgs_o.catalogue_texte(CAT, "en"),
    [("images.cat.titre", {"dossier": CAT["dossier"]}),
     ("images.cat.comptes", {"uniques": CAT["count"],
                             "doublons": CAT["doublons"],
                             "faibles": CAT["sous_le_seuil"]}),
     ("images.n.sous_seuil", {"n": CAT["sous_le_seuil"], "seuil": 300,
                              "largeur": 15.0}),
     "images.n.vecteur"])

# Le rapport anglais de images.py doit aussi traduire l'usage et les verdicts,
# qui sont des valeurs machine du catalogue.
_CAT_EN = imgs_o.catalogue_texte(CAT, "en")
verifier("anglais : le catalogue de images.py traduit usage et verdicts, qui "
         "restent francais dans le fichier",
         lib_o.valeur("images.usage", "impression", "en") in _CAT_EN
         and lib_o.valeur("images.verdict", "sous le seuil", "en") in _CAT_EN
         and "impression" not in _CAT_EN
         and CAT["usage"] == "impression",
         _CAT_EN.splitlines()[1])

_f_inv = _ecrire("inv.json", json.dumps(INV, ensure_ascii=False))
_cas_bascule(
    "gabarit.py", _sortie(gab_o, ["comparer", _f_inv, DOC_DEVIE]),
    _sortie(gab_o, ["comparer", _f_inv, DOC_DEVIE,
                    "--langue-affichage", "en"]),
    ["gab.cmp.non_verifie", "gab.nv.contenu", "gab.nv.hors_fichier",
     ("gab.d.style_hors_gabarit", {"style": "StyleInconnu", "n": 1})])

_cas_bascule(
    "project.py", proj_o.statut_texte(PROJET),
    proj_o.statut_texte(PROJET, "en"),
    [("project.tableau", {"titre": "Etude de cas"}), "project.etapes",
     "project.artefacts", "project.objets", "project.repro",
     "project.decisions_attente", "project.frontieres",
     ("project.etape_motif", {"motif": "hors perimetre"})])


# --- 3. Les trois points de vigilance ----------------------------------------

# figures.py porte DEUX langues qu'il ne faut pas confondre : celle des
# etiquettes dessinees dans le SVG (--langue, une piece du livrable) et celle
# du regard critique de --audit (--langue-affichage, un diagnostic qui reste
# au terminal). Le cas les croise dans les quatre combinaisons.
_SVG_FR = figs_o.construire("swot", FIG_SWOT, None, None, "fr")
_SVG_EN = figs_o.construire("swot", FIG_SWOT, None, None, "en")
_AUDIT_FR = "\n".join(figs_o.auditer("swot", FIG_SWOT))
_AUDIT_EN = "\n".join(figs_o.auditer("swot", FIG_SWOT,
                                     langue_affichage="en"))
verifier("figures : la langue de DESSIN et la langue d'AFFICHAGE sont deux "
         "choses, elles se croisent sans se contaminer",
         ">Forces<" in _SVG_FR and ">Strengths<" in _SVG_EN
         and lib_o.t("figures.a.case_vide", "fr", cle="menaces") in _AUDIT_FR
         and lib_o.t("figures.a.case_vide", "en", cle="menaces") in _AUDIT_EN
         and "Strengths" not in _AUDIT_EN and "Forces" not in _SVG_EN
         # Un SVG anglais audite en francais reste un SVG anglais : le
         # livrable ne suit pas le diagnostic.
         and figs_o.construire("swot", FIG_SWOT, None, None, "en") == _SVG_EN,
         _AUDIT_EN.splitlines()[0])

# project.py ecrit un journal persistant : ce qu'il ENREGISTRE est de la
# donnee. Une meme suite d'operations demandee en anglais doit produire le
# meme projet.json, au hash de continuite pres, sans quoi un projet relu dans
# l'autre langue deviendrait incoherent.
def _mission(la):
    d = proj_o._squelette_v2()
    d["titre"] = "Mission"
    proj_o.changer_etat(d, "cadrage", "en_cours", None, la)
    proj_o.changer_etat(d, "cadrage", "termine", None, la)
    proj_o.enregistrer_objet(d, "figure", 1, "Schema", la)
    proj_o.enregistrer_reproductibilite(d, "0.13.0", "claude")
    # Les horodatages sont les seules valeurs qui bougent d'un appel a
    # l'autre : ils sont neutralises avant comparaison.
    for e in d["journal"]:
        e["horodatage"] = "fixe"
    for info in d["etapes"].values():
        info["maj"] = "fixe"
    for o in d["objets_numerotes"]:
        o["maj"] = "fixe"
    return d


_PROJ_FR, _PROJ_EN = _mission("fr"), _mission("en")
verifier("project : ce que le journal ENREGISTRE ne depend pas de la langue "
         "d'affichage, hash de continuite compris",
         _j(_PROJ_FR) == _j(_PROJ_EN)
         and proj_o._hash_continuite(_PROJ_FR["journal"])
         == proj_o._hash_continuite(_PROJ_EN["journal"])
         and _PROJ_EN["etapes"]["cadrage"]["etat"] == "termine"
         and _PROJ_EN["objets_numerotes"][0]["type"] == "figure"
         and _PROJ_EN["journal"][-1]["stochasticite_declaree"]
         == proj_o.STOCHASTICITE_DECLAREE,
         _j(_PROJ_EN)[:80])

# theme.py emet du CSS et un preambule LaTeX : ce sont des livrables, ils
# partent dans le document et ne connaissent aucune langue d'affichage.
_TH_OK = theme_o.charger({"encre": "#16314E", "fond": "#FFFFFF",
                          "accent": "#C8102E"})
verifier("theme : le CSS et le preambule LaTeX sont des livrables, ils ne "
         "bougent pas avec la langue d'affichage",
         theme_o.css(_TH_OK) == theme_o.css(theme_o.charger(
             {"encre": "#16314E", "fond": "#FFFFFF", "accent": "#C8102E"}))
         and _sortie(theme_o, [_f_charte, "--format", "css"])
         == _sortie(theme_o, [_f_charte, "--format", "css",
                              "--langue-affichage", "en"])
         and _sortie(theme_o, [_f_charte, "--format", "latex"])
         == _sortie(theme_o, [_f_charte, "--format", "latex",
                              "--langue-affichage", "en"]),
         "le CSS ou le preambule LaTeX a change de langue")


# --- 4. Les valeurs machine ne bougent pas en affichage anglais --------------

_CMP_EN = gab_o.comparer(INV, DOC_DEVIE, langue_affichage="en")
verifier("machine : verdict, gravite et nom de regle de gabarit.py restent "
         "francais en affichage anglais, seul le detail change de langue",
         _CMP_EN["verdict"] == CMP_DEVIE["verdict"] == "ecarts majeurs"
         and [(e["gravite"], e["regle"]) for e in _CMP_EN["ecarts"]]
         == [(e["gravite"], e["regle"]) for e in CMP_DEVIE["ecarts"]]
         and all(e["gravite"] in ("majeur", "mineur", "info")
                 for e in _CMP_EN["ecarts"])
         and any(a["detail"] != b["detail"]
                 for a, b in zip(_CMP_EN["ecarts"], CMP_DEVIE["ecarts"])),
         str(_CMP_EN["verdict"]))

_D_EN = proj_o._squelette_v2()
proj_o.changer_etat(_D_EN, "cadrage", "en_cours", None, "en")
verifier("machine : l'etat d'etape et le type d'objet ecrits par project.py "
         "restent les chaines francaises, meme demandes en anglais",
         _D_EN["etapes"]["cadrage"]["etat"] == "en_cours"
         and _D_EN["journal"][0]["etat_apres"] == "en_cours"
         and proj_o.enregistrer_objet(_D_EN, "tableau", 1, "T",
                                      "en")["type"] == "tableau"
         and lib_o.valeur("project.etat", "en_cours", "en") == "in progress"
         # La declaration de stochasticite recopiee dans chaque entree de
         # journal et son libelle francais sont la meme chaine : elles ne
         # peuvent pas diverger sans faire echouer ce cas.
         and proj_o.STOCHASTICITE_DECLAREE
         == lib_o.t("project.stochasticite", "fr")
         and lib_o.t("project.stochasticite", "en")
         != proj_o.STOCHASTICITE_DECLAREE,
         str(_D_EN["etapes"]))

_json_term = _sortie(term_o, [_f_term, "--format", "json",
                              "--langue-affichage", "en"])
_json_nums = _sortie(nums_o, [_f_nums, "--format", "json",
                              "--langue-affichage", "en"])
_json_gab = _sortie(gab_o, ["comparer", _f_inv, DOC_DEVIE, "--format", "json",
                            "--langue-affichage", "en"])
verifier("cli : --format json reste francais meme quand l'anglais est "
         "demande, sur un manuscrit comme sur un binaire",
         lib_o.t("terminology.p.non_definis", "fr",
                 n=D_TERM["sigles_non_definis"]) in _json_term
         and lib_o.t("numbers.p.separateur_mixte", "fr") in _json_nums
         and lib_o.t("numbers.p.separateur_mixte", "en") not in _json_nums
         and lib_o.t("gab.nv.contenu", "fr") in _json_gab
         and lib_o.t("gab.nv.contenu", "en") not in _json_gab,
         _json_nums[:60] + " | " + _json_gab[:60])


# --- 5. Ce qui est ECRIT ne suit pas la langue d'affichage -------------------

_dossier_en = _dossier_images()
_sortie(imgs_o, ["catalogue", _dossier_en, "--langue-affichage", "en"])
with open(os.path.join(_dossier_en, "catalogue.json"), encoding="utf-8") as _f:
    _cat_ecrit = json.load(_f)
_inv_ecrit_chemin = os.path.join(tempfile.mkdtemp(), "inv.json")
_sortie(gab_o, ["inventorier", GAB_PDF, "--out", _inv_ecrit_chemin,
                "--langue-affichage", "en"])
with open(_inv_ecrit_chemin, encoding="utf-8") as _f:
    _inv_ecrit = json.load(_f)

verifier("ecrit : le catalogue d'images et l'inventaire de gabarit poses sur "
         "le disque restent francais meme quand le rapport est demande en "
         "anglais",
         all(i["verdict"] in imgs_o.VERDICTS
             for i in _cat_ecrit["illustrations"])
         and _cat_ecrit["usage"] == "impression"
         and lib_o.t("images.n.vecteur", "fr") in _cat_ecrit["notes"]
         and lib_o.t("images.n.vecteur", "en") not in _cat_ecrit["notes"]
         and _inv_ecrit["famille"] == "page-fixe"
         and all(lib_o.valeur("gab.lacune", m, "fr") == m
                 for m in _inv_ecrit["lacunes"])
         # Le statut de conversion est lui aussi une valeur machine : il ne
         # change pas quand le rapport passe a l'anglais.
         and CONV["statut"] == _sans_backend(lambda: imgs_o.convertir(
             os.path.join(DOSSIER_IMG, "figure.svg"),
             os.path.join(DOSSIER_IMG, "figure.png"),
             langue_affichage="en"))["statut"] == "aucun-backend",
         str(_cat_ecrit["notes"])[:80])
shutil.rmtree(_dossier_en, ignore_errors=True)


# --- 6. La preuve que le chantier est fini ----------------------------------
# La garde ne vise plus un lot : elle passe sur TOUT scriptorium/scripts/. Un
# script ajoute demain sans cablage fera echouer ce cas, quel que soit son
# nom : la liste n'est pas ecrite ici, elle est lue sur le disque.

_TOUS = sorted(n for n in os.listdir(SCRIPTS) if n.endswith(".py"))
_restes = {f: constats_non_cables(os.path.join(SCRIPTS, f)) for f in _TOUS}
verifier("garde : plus aucun script du plugin n'imprime une chaine francaise "
         "hors libelles, les vingt-sept sont cables",
         len(_TOUS) >= 28
         and set(SCRIPTS_DU_LOT) <= set(_TOUS)
         and not any(_restes.values()),
         str({f: v for f, v in _restes.items() if v} or "%d fichiers vus"
             % len(_TOUS)))

shutil.rmtree(DOSSIER_IMG, ignore_errors=True)
