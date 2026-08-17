# -*- coding: utf-8 -*-
"""Cas d'eval de la preparation de compilation LaTeX (tools/ci-latex.py).

La compilation elle-meme se prouve en integration continue, dans une image
TeX Live (.github/workflows/gabarits-latex.yml) : elle ne peut pas etre
rejouee ici, aucun compilateur n'etant suppose present. Ce module verifie ce
qui peut l'etre sans compilateur, et qui conditionne la valeur de cette
compilation : que le document pilote exerce bien ce que les gabarits
promettent, et non une reecriture complaisante.

Un pilote qui n'inclurait pas d'image, ou dont les renvois viseraient des
etiquettes absentes, compilerait sans rien prouver.
"""
import importlib.util
import os
import re

_chemin_ci = os.path.join(RACINE, "tools", "ci-latex.py")
_spec = importlib.util.spec_from_file_location("ci_latex", _chemin_ci)
cil = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cil)

theme_v = charger("theme.py", "theme_verif")
images_v = charger("images.py", "images_verif")

ASSETS = os.path.join(RACINE, "scriptorium", "assets")


def _lire_gabarit(nom):
    with open(os.path.join(ASSETS, nom), encoding="utf-8") as f:
        return f.read()


RAPPORT = _lire_gabarit("gabarit-rapport.tex")
POSTER = _lire_gabarit("gabarit-poster.tex")

# --- Ce que le lot 0.11.0 a ajoute aux gabarits sans jamais le compiler ---
# Si l'un de ces paquets ou l'une de ces listes disparait du gabarit, le
# pilote compilerait encore mais ne prouverait plus rien de la figure.

for _paquet in ("graphicx", "float", "caption", "subcaption"):
    verifier("gabarit rapport : \\usepackage{%s} charge" % _paquet,
             ("\\usepackage{%s}" % _paquet) in RAPPORT
             or ("{%s}" % _paquet) in RAPPORT)

verifier("gabarit rapport : caption chargee apres hyperref",
         RAPPORT.index("\\usepackage{caption}") > RAPPORT.index("hyperref"))

for _liste in ("\\listoffigures", "\\listoftables"):
    verifier("gabarit rapport : %s appelee dans le corps" % _liste,
             ("\n" + _liste) in RAPPORT)

verifier("gabarit rapport : \\graphicspath declare un dossier de figures",
         "\\graphicspath" in RAPPORT and "figures/" in RAPPORT)

verifier("gabarit poster : graphicx charge (le poster inclut une figure)",
         "\\usepackage{graphicx}" in POSTER)


# --- Injection de la charte : le mecanisme decrit en tete des deux gabarits ---

_bloc = theme_v.latex(theme_v.charger(
    os.path.join(ASSETS, "charte-graphique.exemple.json")))

for _nom, _texte in (("rapport", RAPPORT), ("poster", POSTER)):
    _rendu = cil.injecter_charte(_texte, _bloc)
    verifier("charte %s : le bloc genere remplace le bloc par defaut" % _nom,
             "\\definecolor{ScriptoriumEncre}{HTML}{102857}" in _rendu
             and "{HTML}{2E2A26}" not in _rendu)
    verifier("charte %s : les marqueurs survivent, le gabarit reste injectable" % _nom,
             cil.MARQUE_DEBUT in _rendu and cil.MARQUE_FIN in _rendu
             and cil.injecter_charte(_rendu, _bloc) == _rendu)
    verifier("charte %s : les huit couleurs nommees sont definies" % _nom,
             _rendu.count("\\definecolor{Scriptorium") == 8,
             "n=%d" % _rendu.count("\\definecolor{Scriptorium"))

try:
    cil.injecter_charte(RAPPORT.replace(cil.MARQUE_FIN, "marqueur efface"), _bloc)
    _refus = False
except ValueError:
    _refus = True
verifier("charte : un gabarit dont le marqueur a disparu est refuse, "
         "jamais rendu intact et silencieux", _refus)


# --- Les exemples de figure du gabarit, decommentes verbatim ---

_figures = cil.extraire_figures(RAPPORT)
verifier("figures : les deux exemples commentes du gabarit sont extraits",
         len(_figures) == 2, "n=%d" % len(_figures))
verifier("figures : la seconde est la figure composee (subfigure)",
         len(_figures) == 2 and _figures[1].count("\\begin{subfigure}") == 2
         and "\\end{figure}" in _figures[1])

for _i, _f in enumerate(_figures):
    verifier("figure %d : plus aucune ligne commentee apres decommentage" % _i,
             not any(l.lstrip().startswith("%") for l in _f.splitlines()),
             _f)
    for _macro in ("\\includegraphics", "\\caption", "\\label"):
        verifier("figure %d : %s present" % (_i, _macro), _macro in _f)
    verifier("figure %d : l'ordre documente est tenu "
             "(includegraphics, puis caption, puis label)" % _i,
             _f.index("\\includegraphics") < _f.rindex("\\caption")
             < _f.rindex("\\label"), _f)

# Toute image citee par un exemple doit etre generee par preparer(), sinon la
# compilation echouerait sur un fichier absent au lieu de prouver la figure.
_citees = set()
for _f in _figures:
    _citees |= set(re.findall(r"\\includegraphics\[[^\]]*\]\{([^}]+)\}", _f))
verifier("figures : chaque image citee par un exemple est generee par preparer",
         _citees and _citees <= set(cil.IMAGES),
         "citees=%s generees=%s" % (sorted(_citees), sorted(cil.IMAGES)))
verifier("figures : aucune image generee ne reste inutilisee",
         set(cil.IMAGES) <= _citees,
         "inutilisees=%s" % sorted(set(cil.IMAGES) - _citees))


# --- Pilote : les renvois visent des etiquettes reellement posees ---

_pilote = cil.pilote(RAPPORT, _figures)
_etiquettes = set(re.findall(r"\\label\{([^}]+)\}", _pilote))
_vises = set(re.findall(r"\\(?:page)?ref\{([^}]+)\}",
                        _pilote[_pilote.index(cil.RENVOIS.strip()[:40]):]))
verifier("pilote : chaque renvoi vise une etiquette posee dans le document",
         _vises and _vises <= _etiquettes,
         "vises=%s poses=%s" % (sorted(_vises), sorted(_etiquettes)))
verifier("pilote : les renvois couvrent figure, sous-figure et tableau",
         {"fig:mesures", "fig:vues-apres", "tab:exemple"} <= _vises,
         "vises=%s" % sorted(_vises))
verifier("pilote : les figures sont inserees avant l'encadre de resultat",
         _pilote.index("\\begin{figure}") < _pilote.index(cil.ANCRE_PILOTE))
verifier("pilote : le corps du gabarit n'est pas ampute",
         "\\listoffigures" in _pilote and "\\listoftables" in _pilote
         and _pilote.count("\\end{document}") == 1)

try:
    cil.pilote(RAPPORT, [])
    _sans_figure = False
except ValueError:
    _sans_figure = True
verifier("pilote : refuse de se construire sans exemple de figure, "
         "plutot que de compiler un document qui ne prouve rien", _sans_figure)


# --- Images generees : de vrais PNG, relus par le lecteur du depot ---

_octets = cil.png(64, 40)
verifier("png : signature de fichier PNG", _octets[:8] == b"\x89PNG\r\n\x1a\n")
_larg, _haut, _fmt = images_v.dimensions(_octets)
verifier("png : dimensions relues par images.dimensions, pas par le generateur",
         (_larg, _haut, _fmt) == (64, 40, "png"),
         "lu=%s" % ((_larg, _haut, _fmt),))
verifier("png : le contenu n'est pas un en-tete vide",
         len(_octets) > 200, "octets=%d" % len(_octets))
try:
    cil.png(0, 10)
    _dim_nulle = False
except ValueError:
    _dim_nulle = True
verifier("png : une dimension nulle est refusee", _dim_nulle)


# --- Rapport de reference du jeu d'or : versionne, donc verifiable ---
#
# Le jeu d'or etait construit, teste et jamais joue : sans rapport de
# reference publie, la porte de regression n'avait rien a quoi comparer.
# Le rapport vit desormais dans le depot ; ces cas verifient qu'il reste
# aligne sur le corpus qu'il pretend mesurer.

import json as _json

_spec_g = importlib.util.spec_from_file_location(
    "gold_verif", os.path.join(RACINE, "tools", "gold.py"))
_gold = importlib.util.module_from_spec(_spec_g)
_spec_g.loader.exec_module(_gold)

CHEMIN_REFERENCE = os.path.join(RACINE, "evals", "gold", "rapport-reference.json")

verifier("jeu d'or : le rapport de reference est versionne dans le depot",
         os.path.isfile(CHEMIN_REFERENCE), CHEMIN_REFERENCE)

with open(CHEMIN_REFERENCE, encoding="utf-8") as _f:
    REFERENCE = _json.load(_f)

verifier("reference : elle porte la version du plugin qui l'a produite",
         isinstance(REFERENCE.get("version_plugin"), str)
         and REFERENCE["version_plugin"],
         "version=%r" % REFERENCE.get("version_plugin"))
verifier("reference : elle porte les polarites de la porte directionnelle",
         REFERENCE.get("polarites") == dict(_gold.POLARITES),
         "pol=%s" % REFERENCE.get("polarites"))
verifier("reference : ses mises en garde ne sont pas vides",
         bool(REFERENCE.get("mises_en_garde")))

_declarees = set(_gold.taches_declarees())
_mesurees = {n for n, t in REFERENCE.get("taches", {}).items()
             if t.get("statut") == "mesure"}
verifier("reference : chaque tache du jeu d'or y est mesuree "
         "(une tache ajoutee sans rafraichir la reference sortirait de la porte)",
         _declarees and _declarees == _mesurees,
         "declarees=%s mesurees=%s" % (sorted(_declarees), sorted(_mesurees)))

for _nom, _t in sorted(REFERENCE.get("taches", {}).items()):
    if _t.get("statut") != "mesure":
        continue
    verifier("reference : la tache %s porte les trois metriques comparees" % _nom,
             all(m in _t for m in _gold.POLARITES), "t=%s" % _t)
    verifier("reference : la tache %s declare un nombre de cas non nul" % _nom,
             _t.get("n_cas"), "n=%s" % _t.get("n_cas"))

_auto = _gold.comparer_rapports(REFERENCE, REFERENCE)
verifier("reference : comparee a elle-meme, aucune regression "
         "(le fichier versionne est lisible par la porte)",
         _auto["comparaisons"] and not _auto["regressions"],
         "reg=%s" % _auto["regressions"])
_code_consultatif, _ = _gold.appliquer_porte(
    _gold.comparer_rapports(REFERENCE, {"version_plugin": "x", "taches": {}}),
    bloquant=False, outrepasser=False, justification="",
    chemin_projet="projet.json")
verifier("porte en integration continue : consultative, une regression "
         "n'y fait pas echouer la commande", _code_consultatif == 0,
         "code=%d" % _code_consultatif)
