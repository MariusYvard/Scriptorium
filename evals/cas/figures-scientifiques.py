# -*- coding: utf-8 -*-
"""Cas d'eval des figures de donnees (courbe, nuage, histogramme, boite,
flux, prisma).

Deux familles de cas. Le rendu : chaque type produit un SVG bien forme qui
porte ses axes titres, leurs unites, sa legende et le bon nombre d'objets
traces. L'audit : chaque controle structurel attrape son defaut, et des
donnees correctes ne declenchent aucun avis (un detecteur qui crie toujours
ne sert a rien).
"""
import xml.etree.ElementTree as ET

figs = charger("figures.py", "figures_donnees")

SVG = "{http://www.w3.org/2000/svg}"


def _arbre(svg):
    return ET.fromstring(svg)


def _compter(racine, balise):
    return len(list(racine.iter(SVG + balise)))


def _textes(racine):
    return [e.text or "" for e in racine.iter(SVG + "text")]


AXES = {"axe_x": {"titre": "Duree", "unite": "h"},
        "axe_y": {"titre": "Concentration", "unite": "mg/L"}}

D_COURBE = dict(AXES, series=[
    {"nom": "Temoin", "points": [[0, 1.2], [2, 3.4], [4, 5.1]],
     "erreurs": [0.2, 0.3, 0.25]},
    {"nom": "Traite", "points": [[0, 1.1], [2, 2.0], [4, 2.4]]}])

D_NUAGE = {"axe_x": {"titre": "Masse", "unite": "kg"},
           "axe_y": {"titre": "Rendement", "unite": "%"},
           "series": [{"nom": "Lot A", "points": [[1, 12], [2, 15], [3, 19],
                                                  [4, 21], [5, 26]],
                       "ajustement": True},
                      {"nom": "Lot B", "points": [[1, 8], [2, 9], [3, 13]]}]}

D_HIST = {"axe_x": {"titre": "Classe d'age"},
          "axe_y": {"titre": "Effectif", "unite": "individus"},
          "barres": [{"categorie": "18-24", "valeur": 42},
                     {"categorie": "25-34", "valeur": 67},
                     {"categorie": "35-49", "valeur": 51},
                     {"categorie": "50-64", "valeur": 30},
                     {"categorie": "65 et plus", "valeur": 12}]}

D_BOITE = {"axe_x": {"titre": "Groupe"},
           "axe_y": {"titre": "Duree de sejour", "unite": "jours"},
           "groupes": [{"nom": "Temoin", "valeurs": [3, 4, 5, 5, 6, 7, 8, 9, 20]},
                       {"nom": "Traite", "min": 2, "q1": 3, "mediane": 4,
                        "q3": 6, "max": 9},
                       {"nom": "Placebo", "valeurs": [4, 5, 6, 6, 7, 8, 8, 10]}]}

D_FLUX = {"niveaux": [
    {"titre": "Recrutement",
     "boites": [{"libelle": "Patients evalues", "effectif": 300,
                 "exclusions": [{"libelle": "Criteres non remplis",
                                 "effectif": 80}]}]},
    {"titre": "Repartition",
     "boites": [{"libelle": "Patients randomises", "effectif": 220}]},
    {"titre": "Analyse",
     "boites": [{"libelle": "Patients analyses", "effectif": 220}]}]}

D_PRISMA = {"identifiees": {"Bases de donnees": 420, "Autres sources": 15},
            "doublons": 60, "examinees": 375,
            "ecartees_titre": [{"motif": "Hors sujet", "n": 150},
                               {"motif": "Langue non couverte", "n": 50}],
            "evaluees": 175,
            "ecartees_texte": [{"motif": "Methode insuffisante", "n": 90},
                               {"motif": "Population differente", "n": 50}],
            "incluses": 35}

TOUS = (("courbe", D_COURBE), ("nuage", D_NUAGE), ("histogramme", D_HIST),
        ("boite", D_BOITE), ("flux", D_FLUX), ("prisma", D_PRISMA))

# --- Rendu : le SVG est bien forme et tient dans son viewBox ---------------

for _typ, _don in TOUS:
    _svg = figs.construire(_typ, _don, "Titre d'essai")
    try:
        _r = _arbre(_svg)
        _vb = [float(v) for v in _r.get("viewBox").split()]
        _dedans = all(0 <= float(e.get("x")) <= _vb[2]
                      and 0 <= float(e.get("y")) <= _vb[3]
                      for e in _r.iter(SVG + "text"))
        _ok = len(list(_r.iter())) > 10 and _dedans
        _detail = f"elements={len(list(_r.iter()))} textes_dedans={_dedans}"
    except (ET.ParseError, TypeError, ValueError) as exc:
        _ok, _detail = False, str(exc)
    verifier(f"figure {_typ} : SVG bien forme, textes dans le viewBox",
             _ok, _detail)

_c = _arbre(figs.construire("courbe", D_COURBE, "Cinetique"))
verifier("courbe : une polyligne et une legende par serie, axes titres avec "
         "leur unite",
         _compter(_c, "polyline") == 2
         and "Duree (h)" in _textes(_c)
         and "Concentration (mg/L)" in _textes(_c)
         and "Temoin" in _textes(_c) and "Traite" in _textes(_c),
         f"polylignes={_compter(_c, 'polyline')} textes={_textes(_c)}")
verifier("courbe : une barre d'erreur par point de la serie qui en porte",
         _compter(_c, "path") == 3, f"n={_compter(_c, 'path')}")


_n = _arbre(figs.construire("nuage", D_NUAGE, "Rendement"))
verifier("nuage : series distinguees par la forme du marqueur autant que par "
         "la couleur, ajustement declare comme tel",
         _compter(_n, "circle") == 6 and _compter(_n, "rect") >= 5
         and any("ajustement" in t for t in _textes(_n)),
         f"cercles={_compter(_n, 'circle')} carres={_compter(_n, 'rect')} "
         f"textes={_textes(_n)}")

_h = _arbre(figs.construire("histogramme", D_HIST, "Repartition"))
verifier("histogramme : une barre par categorie, categories etiquetees, "
         "graduation zero presente",
         _compter(_h, "rect") == 2 + len(D_HIST["barres"])
         and "0" in _textes(_h)
         and all(any(c in t for t in _textes(_h))
                 for c in ("18-24", "25-34", "65 et")),
         f"rects={_compter(_h, 'rect')} textes={_textes(_h)}")

_b = _arbre(figs.construire("boite", D_BOITE, "Sejour"))
verifier("boite : une boite par groupe, groupes nommes, point aberrant trace "
         "a part",
         _compter(_b, "rect") == 6 and _compter(_b, "circle") == 1
         and all(g in _textes(_b) for g in ("Temoin", "Traite", "Placebo")),
         f"rects={_compter(_b, 'rect')} cercles={_compter(_b, 'circle')}")

_f = _arbre(figs.construire("flux", D_FLUX, "Parcours"))
verifier("flux : une fleche par transition et un effectif par boite",
         _compter(_f, "polygon") == 3
         and sum(1 for t in _textes(_f) if "(n = " in t) >= 4,
         f"fleches={_compter(_f, 'polygon')} textes={_textes(_f)}")

_p = _arbre(figs.construire("prisma", D_PRISMA))
_tp = _textes(_p)
_jetons = set(" ".join(_tp).split())
verifier("prisma : quatre etapes normalisees, comptes de chaque etape, motifs "
         "d'ecart rendus",
         all(e in _tp for e in ("Identification", "Criblage", "Eligibilite",
                                "Inclusion"))
         and {"435)", "375)", "175)", "35)"} <= _jetons
         and any("Hors sujet" in t for t in _tp)
         and any("Methode insuffisante" in t for t in _tp),
         str(_tp))

# --- Audit : chaque controle attrape son defaut ----------------------------


def _attrape(typ, don, fragment):
    return any(fragment in a for a in figs.auditer(typ, don))


verifier("audit : serie vide signalee",
         _attrape("courbe", dict(AXES, series=[{"nom": "A", "points": []}]),
                  "vide"))

verifier("audit : axe sans titre signale",
         _attrape("courbe", {"axe_y": {"titre": "M", "unite": "g"},
                             "series": [{"nom": "A", "points": [[0, 1]]}]},
                  "sans titre"))

verifier("audit : axe sans unite signale",
         _attrape("courbe", {"axe_x": {"titre": "Duree"},
                             "axe_y": {"titre": "M", "unite": "g"},
                             "series": [{"nom": "A", "points": [[0, 1]]}]},
                  "sans unite"))

verifier("audit : trop de series pour rester lisible",
         _attrape("nuage", dict(AXES, series=[{"nom": str(i),
                                               "points": [[0, i], [1, i]]}
                                              for i in range(8)]),
                  "illisible"))

verifier("audit : serie sans nom, donc points non etiquetes",
         _attrape("nuage", dict(AXES, series=[{"points": [[0, 1], [1, 2]]}]),
                  "ne sont pas etiquetes"))

verifier("audit : echelle des ordonnees tronquee sur un histogramme",
         _attrape("histogramme",
                  dict(D_HIST, axe_y={"titre": "Effectif", "unite": "n",
                                      "min": 20}),
                  "tronquee"))

verifier("audit : categories en doublon",
         _attrape("histogramme",
                  dict(D_HIST, barres=[{"categorie": "A", "valeur": 3},
                                       {"categorie": "A", "valeur": 5}]),
                  "en double"))

verifier("audit : moustaches incoherentes (quartile hors ordre)",
         _attrape("boite",
                  dict(D_BOITE, groupes=[{"nom": "A", "min": 1, "q1": 4,
                                          "mediane": 3, "q3": 5, "max": 9}]),
                  "moustaches incoherentes"))

# PRISMA : un schema dont les comptes ne bouclent pas est faux, quel que soit
# le soin de son rendu. Trois jonctions a verifier, une par etape.
verifier("audit prisma : comptes non boucles a l'identification",
         _attrape("prisma", dict(D_PRISMA, doublons=10),
                  "Comptes non boucles a l'identification"))

verifier("audit prisma : somme des exclusions fausse au criblage",
         _attrape("prisma", dict(D_PRISMA, evaluees=200),
                  "Comptes non boucles au criblage"))

verifier("audit prisma : somme des exclusions fausse en texte integral",
         _attrape("prisma",
                  dict(D_PRISMA, ecartees_texte=[{"motif": "Methode", "n": 90}]),
                  "Comptes non boucles en texte integral"))

# --- Cas negatifs : des donnees correctes ne declenchent aucun avis --------

for _nom, _don in TOUS:
    _av = figs.auditer(_nom, _don)
    verifier(f"audit {_nom} : donnees correctes, aucun avis",
             len(_av) == 1 and _av[0].startswith("Aucun defaut"), str(_av))
