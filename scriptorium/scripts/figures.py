#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generateur de figures en SVG pour Scriptorium.

Produit des schemas deterministes et sobres. Figures strategiques a cases :
SWOT, matrice BCG, matrice
d'Ansoff, PESTEL, chaine de valeur de Porter, ainsi que trois cercles imbriques
TAM/SAM/SOM (etude de marche). Applique une charte graphique fournie (--theme
charte.json) : couleurs, polices, filet d'accent, fond, filigrane, rayon des
angles. Un audit (--audit) porte un regard critique sur la figure, charte
comprise (contraste).

Usage :
    python3 figures.py TYPE --out f.svg [--data data.json|-] [--title "T"] [--theme charte.json]
    python3 figures.py TYPE --data - --audit --theme charte.json < data.json

TYPE strategiques (a cases) : swot | bcg | ansoff | pestel | chaine-valeur | tam-sam-som
TYPE de donnees (a axes) : courbe | nuage | histogramme | boite | flux | prisma
Module importable : construire(type, data, titre, theme) ; auditer(type, data, theme).
"""
import argparse
import json
import math
import os
import sys
from xml.sax.saxutils import escape

def _charger_theme_module():
    """Charge theme.py par son chemin, sans toucher a sys.path.

    Inserer le dossier scripts/ dans sys.path rendait ses fichiers prioritaires
    sur la bibliotheque standard pour tout le processus : numbers.py masquait
    alors le module standard numbers, dont depend decimal, et l'erreur qui en
    resultait etait avalee plus loin par un except large. Charger par chemin
    explicite supprime la cause.
    """
    import importlib.util
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "theme.py")
    spec = importlib.util.spec_from_file_location("scriptorium_theme", chemin)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


try:
    _theme = _charger_theme_module()
    charger_theme, valider_theme = _theme.charger, _theme.valider
except Exception:
    _DEF = {"police": "Helvetica, Arial, sans-serif", "police_titre": "Helvetica, Arial, sans-serif",
            "graisse_titre": 700, "encre": "#2E2A26", "trait": "#8A8175", "fond": "#FFFFFF",
            "accent": "#6E6356", "palette": ["#F4F1EC", "#EEF2F4", "#F1F0EA", "#F4EEF0"],
            "logo_texte": None, "rayon": 8}
    def charger_theme(s=None):
        return dict(_DEF) if not isinstance(s, dict) else {**_DEF, **s}
    def valider_theme(t):
        return ([], [])

W, H = 900, 620
NL = chr(10)

# Theme courant (mutable), initialise aux valeurs par defaut
ENCRE = "#2E2A26"
TRAIT = "#8A8175"
FOND = "#FFFFFF"
ACCENT = "#6E6356"
FONDS = ["#F4F1EC", "#EEF2F4", "#F1F0EA", "#F4EEF0"]
POLICE = "Helvetica, Arial, sans-serif"
POLICE_TITRE = "Helvetica, Arial, sans-serif"
GRAISSE_TITRE = 700
RAYON = 8
LOGO = None


def appliquer_theme(t):
    global ENCRE, TRAIT, FOND, ACCENT, FONDS, POLICE, POLICE_TITRE, GRAISSE_TITRE, RAYON, LOGO
    ENCRE, TRAIT, FOND, ACCENT = t["encre"], t["trait"], t["fond"], t["accent"]
    FONDS = t["palette"]
    POLICE, POLICE_TITRE = t["police"], t["police_titre"]
    GRAISSE_TITRE, RAYON, LOGO = t["graisse_titre"], t["rayon"], t.get("logo_texte")


def _txt(x, y, s, taille=14, gras=False, ancre="start", couleur=None, police=None):
    couleur = couleur or ENCRE
    police = police or POLICE
    poids = f' font-weight="{GRAISSE_TITRE}"' if gras else ""
    return (f'<text x="{x}" y="{y}" font-family="{police}" font-size="{taille}" '
            f'fill="{couleur}" text-anchor="{ancre}"{poids}>{escape(s)}</text>')


def _lignes(x, y, items, largeur_car=46, taille=12, interligne=17, maxi=7):
    out = []
    n = 0
    for it in items:
        mots = str(it).split()
        ligne = ""
        morceaux = []
        for mot in mots:
            if len(ligne) + len(mot) + 1 > largeur_car:
                morceaux.append(ligne)
                ligne = mot
            else:
                ligne = (ligne + " " + mot).strip()
        if ligne:
            morceaux.append(ligne)
        for j, mc in enumerate(morceaux):
            if n >= maxi:
                out.append(_txt(x, y + n * interligne, "...", taille))
                return NL.join(out)
            puce = "- " if j == 0 else "  "
            out.append(_txt(x, y + n * interligne, puce + mc, taille))
            n += 1
    return NL.join(out)


def _cadre(hauteur=H):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {hauteur}" '
            f'width="{W}" height="{hauteur}"><rect width="{W}" height="{hauteur}" fill="{FOND}"/>')


def _titre(titre):
    if not titre:
        return ""
    out = [_txt(W / 2, 38, titre, 22, gras=True, ancre="middle", couleur=ENCRE, police=POLICE_TITRE)]
    out.append(f'<rect x="{W/2-60:.0f}" y="48" width="120" height="3" fill="{ACCENT}"/>')
    if LOGO:
        out.append(_txt(W - 30, 30, str(LOGO), 13, gras=True, ancre="end", couleur=TRAIT, police=POLICE_TITRE))
    return NL.join(out)


def quadrants(cells, titre, axes=None):
    x0, y0, gx, gy = 40, 60, W - 40, H - 30
    mx, my = (x0 + gx) / 2, (y0 + gy) / 2
    s = [_cadre(), _titre(titre)]
    pos = [(x0, y0), (mx, y0), (x0, my), (mx, my)]
    for (cx, cy), (ct, items, fond) in zip(pos, cells):
        s.append(f'<rect x="{cx+4}" y="{cy+4}" width="{mx-x0-8}" height="{my-y0-8}" rx="{RAYON}" fill="{fond}" stroke="{TRAIT}" stroke-width="1"/>')
        s.append(_txt(cx + 18, cy + 30, ct, 15, gras=True))
        s.append(_lignes(cx + 18, cy + 54, items))
    if axes:
        hx, hy, vx = axes
        s.append(_txt(mx, y0 - 4, hx, 12, gras=True, ancre="middle", couleur=TRAIT))
        s.append(_txt(mx, gy + 22, hy, 12, gras=True, ancre="middle", couleur=TRAIT))
        s.append(f'<text x="22" y="{my}" font-family="{POLICE}" font-size="12" fill="{TRAIT}" text-anchor="middle" font-weight="700" transform="rotate(-90 22 {my})">{escape(vx)}</text>')
    s.append("</svg>")
    return NL.join(s)


def swot(data, titre="Matrice SWOT"):
    return quadrants([
        ("Forces", data.get("forces", []), FONDS[0]),
        ("Faiblesses", data.get("faiblesses", []), FONDS[1]),
        ("Opportunites", data.get("opportunites", []), FONDS[2]),
        ("Menaces", data.get("menaces", []), FONDS[3]),
    ], titre)


def ansoff(data, titre="Matrice d'Ansoff"):
    return quadrants([
        ("Penetration de marche", data.get("penetration", ["Marche actuel, produit actuel"]), FONDS[0]),
        ("Extension de produit", data.get("extension_produit", ["Marche actuel, produit nouveau"]), FONDS[1]),
        ("Extension de marche", data.get("extension_marche", ["Marche nouveau, produit actuel"]), FONDS[2]),
        ("Diversification", data.get("diversification", ["Marche nouveau, produit nouveau"]), FONDS[3]),
    ], titre, axes=("Produit actuel", "Produit nouveau", "Marche"))


def pestel(data, titre="Analyse PESTEL"):
    libelles = [("Politique", "politique"), ("Economique", "economique"),
                ("Social", "social"), ("Technologique", "technologique"),
                ("Environnemental", "environnemental"), ("Legal", "legal")]
    x0, y0 = 40, 60
    cw, ch = (W - 80) / 3, (H - 100) / 2
    s = [_cadre(), _titre(titre)]
    for i, (lib, cle) in enumerate(libelles):
        cx = x0 + (i % 3) * cw
        cy = y0 + (i // 3) * ch
        s.append(f'<rect x="{cx+5}" y="{cy+5}" width="{cw-10}" height="{ch-10}" rx="{RAYON}" fill="{FONDS[i % 4]}" stroke="{TRAIT}"/>')
        s.append(_txt(cx + 16, cy + 28, lib, 14, gras=True))
        s.append(_lignes(cx + 16, cy + 50, data.get(cle, []), largeur_car=30, maxi=5))
    s.append("</svg>")
    return NL.join(s)


def bcg(data, titre="Matrice BCG"):
    x0, y0, gx, gy = 90, 70, W - 60, H - 70
    mx, my = (x0 + gx) / 2, (y0 + gy) / 2
    s = [_cadre(), _titre(titre)]
    labels = [("Vedettes", x0, y0, mx, my), ("Dilemmes", mx, y0, gx, my),
              ("Vaches a lait", x0, my, mx, gy), ("Poids morts", mx, my, gx, gy)]
    for i, (lab, ax, ay, bx, by) in enumerate(labels):
        s.append(f'<rect x="{ax}" y="{ay}" width="{bx-ax}" height="{by-ay}" fill="{FONDS[i % 4]}" stroke="{TRAIT}" stroke-width="1"/>')
        s.append(_txt((ax + bx) / 2, ay + 22, lab, 13, gras=True, ancre="middle", couleur=TRAIT))
    s.append(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{gy}" stroke="{ENCRE}" stroke-width="1.5"/>')
    s.append(f'<line x1="{x0}" y1="{gy}" x2="{gx}" y2="{gy}" stroke="{ENCRE}" stroke-width="1.5"/>')
    s.append(f'<text x="62" y="{my}" font-family="{POLICE}" font-size="12" fill="{ENCRE}" text-anchor="middle" transform="rotate(-90 62 {my})">Taux de croissance</text>')
    s.append(_txt((x0 + gx) / 2, gy + 30, "Part de marche relative (forte a gauche)", 12, ancre="middle"))
    for it in data.get("items", []):
        cr = max(0, min(100, float(it.get("croissance", 50))))
        pa = max(0, min(100, float(it.get("part", 50))))
        taille = max(8, min(40, float(it.get("taille", 18))))
        px = gx - (pa / 100) * (gx - x0)
        py = gy - (cr / 100) * (gy - y0)
        s.append(f'<circle cx="{px:.0f}" cy="{py:.0f}" r="{taille:.0f}" fill="{ACCENT}" fill-opacity="0.55" stroke="{ENCRE}"/>')
        s.append(_txt(px, py - taille - 6, str(it.get("nom", "")), 11, ancre="middle"))
    s.append("</svg>")
    return NL.join(s)


def chaine_valeur(data, titre="Chaine de valeur (Porter)"):
    soutien = data.get("soutien", ["Infrastructure", "Ressources humaines", "Recherche et developpement", "Achats"])
    principales = data.get("principales", ["Logistique entrante", "Production", "Logistique sortante", "Commercialisation", "Services"])
    hh = 380
    x0, larg, hs = 40, W - 130, 28
    s = [_cadre(hh), _titre(titre)]
    s.append(_txt(x0, 62, "Activites de soutien", 12, gras=True, couleur=TRAIT))
    ytop = 72
    for i, a in enumerate(soutien):
        cy = ytop + i * (hs + 6)
        s.append(f'<rect x="{x0}" y="{cy}" width="{larg}" height="{hs}" rx="5" fill="{FONDS[1]}" stroke="{TRAIT}"/>')
        s.append(_txt(x0 + 14, cy + 19, a, 13))
    yend = ytop + len(soutien) * (hs + 6)
    s.append(_txt(x0, yend + 18, "Activites principales", 12, gras=True, couleur=TRAIT))
    yprim = yend + 28
    hp = hh - yprim - 26
    cw = larg / len(principales)
    for i, a in enumerate(principales):
        cx = x0 + i * cw
        s.append(f'<rect x="{cx}" y="{yprim}" width="{cw-6}" height="{hp}" rx="5" fill="{FONDS[0]}" stroke="{TRAIT}"/>')
        s.append(_lignes(cx + 10, yprim + 24, [a], largeur_car=16, taille=12, maxi=4))
    ax = x0 + larg + 6
    amid = (ytop + yprim + hp) / 2
    s.append(f'<path d="M{ax} {ytop} L{ax+44} {amid:.0f} L{ax} {yprim+hp:.0f} Z" fill="{ACCENT}" fill-opacity="0.5" stroke="{TRAIT}"/>')
    s.append(f'<text x="{ax+15}" y="{amid:.0f}" font-family="{POLICE}" font-size="12" fill="{ENCRE}" text-anchor="middle" font-weight="700" transform="rotate(90 {ax+15} {amid:.0f})">Marge</text>')
    s.append("</svg>")
    return NL.join(s)


def tam_sam_som(data, titre="TAM, SAM, SOM"):
    """Trois cercles imbriques (TAM englobe SAM englobe SOM), etude de marche.

    Portions adaptees du projet openscience (Synthetic Sciences, InkVell Inc.), Apache-2.0,
    github.com/synthetic-sciences/openscience (logique du gabarit market-research-reports).
    Modifications Marius Yvard, MIT.

    Donnees attendues : {"tam": {"libelle": "...", "valeur": "..."}, "sam": {...}, "som": {...}}.
    """
    cx, cy = W / 2, 350
    rayons = {"tam": 250, "sam": 172, "som": 95}
    fonds = {"tam": FONDS[0], "sam": FONDS[1 % len(FONDS)], "som": FONDS[2 % len(FONDS)]}
    s = [_cadre(H), _titre(titre)]
    for cle in ("tam", "sam", "som"):
        s.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{rayons[cle]}" fill="{fonds[cle]}" '
                  f'fill-opacity="0.9" stroke="{TRAIT}" stroke-width="1.5"/>')
    for cle in ("tam", "sam", "som"):
        bloc = data.get(cle, {}) or {}
        libelle = str(bloc.get("libelle", "")).strip()
        valeur = str(bloc.get("valeur", "")).strip()
        if cle == "som":
            y = cy
            s.append(_txt(cx, y - 8, cle.upper(), 16, gras=True, ancre="middle"))
            s.append(_txt(cx, y + 16, valeur or "?", 18, gras=True, ancre="middle", couleur=ACCENT))
            if libelle:
                s.append(_txt(cx, y + 36, libelle, 11, ancre="middle", couleur=TRAIT))
        else:
            y = cy - rayons[cle] + 38
            entete = f"{cle.upper()} - {valeur}" if valeur else cle.upper()
            s.append(_txt(cx, y, entete, 17, gras=True, ancre="middle"))
            if libelle:
                s.append(_txt(cx, y + 20, libelle, 12, ancre="middle", couleur=TRAIT))
    s.append("</svg>")
    return NL.join(s)


# ---------------------------------------------------------------------------
# Figures de donnees
#
# Les six figures ci-dessus rangent des elements dans des cases : elles n'ont
# pas d'axes. Celles qui suivent portent des grandeurs chiffrees, donc des axes
# gradues dont chacun porte un titre et son unite (exigence de figure.md).
# Chaque serie se distingue par la couleur ET par un second canal (forme du
# marqueur, style de trait) : la couleur ne porte jamais seule le sens.
# ---------------------------------------------------------------------------

HD = 560                      # hauteur des figures a axes
MG, MDR, MHT, MBS = 92, 695, 80, 470   # cadre de trace : gauche, droite, haut, bas
XLEG = 704                    # colonne de legende, hors du cadre de trace
FORMES = ("cercle", "carre", "triangle", "losange", "croix", "triangle-bas")
TIRETS = ("", "7 4", "2 3", "10 3 2 3", "1 4", "6 3 1 3")
SERIES_REPLI = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00",
                "#56B4E9", "#000000"]
MAX_SERIES = 6                # au-dela, la lecture d'une legende decroche


def _lum(hexa):
    """Luminance relative WCAG d'une couleur #RRGGBB."""
    try:
        h = str(hexa).lstrip("#")
        canaux = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    except (ValueError, IndexError):
        return 0.0
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
           for c in canaux]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def _contraste(a, b):
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def _couleurs_series():
    """Couleurs de trace tirees de la charte.

    La palette d'une charte sert d'abord de fond de case : ses teintes tres
    claires disparaitraient en trait de courbe. Seules les couleurs assez
    contrastees avec le fond sont retenues ; s'il en reste moins de deux, repli
    sur un jeu daltonisme-sur (teintes d'Okabe-Ito).
    """
    gardees = [c for c in FONDS if _contraste(c, FOND) >= 2.0]
    return gardees if len(gardees) >= 2 else list(SERIES_REPLI)


def _fmt_nb(v):
    """Formate une valeur de graduation, virgule decimale francaise."""
    v = float(v)
    if abs(v) < 1e-12:
        return "0"
    s = "%g" % round(v, 10)
    if "e" in s or "E" in s:
        s = "%.3g" % v
    return s.replace(".", ",")


def _pas_propre(etendue, cible=6):
    """Pas de graduation lisible (1, 2, 2,5 ou 5 fois une puissance de dix).

    Diviser l'etendue par le nombre de points donnerait des reperes a valeurs
    quelconques (0,37 ; 0,74 ...) que personne ne lit.
    """
    if etendue <= 0:
        return 1.0
    brut = etendue / float(max(1, cible))
    exposant = math.floor(math.log10(brut))
    base = brut / (10.0 ** exposant)
    for m in (1.0, 2.0, 2.5, 5.0, 10.0):
        if base <= m + 1e-9:
            return m * (10.0 ** exposant)
    return 10.0 ** (exposant + 1)


def _echelle(vmin, vmax, depart_zero=False, cible=6):
    """Retourne (bas, haut, graduations) arrondis au pas propre."""
    vmin, vmax = float(vmin), float(vmax)
    if depart_zero:
        vmin, vmax = min(0.0, vmin), max(0.0, vmax)
    if vmax <= vmin:
        vmax = vmin + 1.0
    pas = _pas_propre(vmax - vmin, cible)
    bas = math.floor(vmin / pas) * pas
    haut = math.ceil(vmax / pas) * pas
    if depart_zero and bas > 0:
        bas = 0.0
    n = int(round((haut - bas) / pas))
    return bas, haut, [bas + i * pas for i in range(n + 1)]


def _tronquer(s, maxi):
    s = str(s)
    return s if len(s) <= maxi else s[:max(1, maxi - 1)] + "..."


def _envelopper(texte, largeur_car):
    """Coupe un texte en lignes d'au plus largeur_car caracteres."""
    mots, lignes, courante = str(texte).split(), [], ""
    for mot in mots:
        if courante and len(courante) + len(mot) + 1 > largeur_car:
            lignes.append(courante)
            courante = mot
        else:
            courante = (courante + " " + mot).strip()
    if courante:
        lignes.append(courante)
    return lignes or [""]


def _titre_axe(bloc, defaut=""):
    """Assemble 'Titre (unite)' a partir du bloc d'axe."""
    bloc = bloc if isinstance(bloc, dict) else {}
    titre = str(bloc.get("titre", "") or defaut).strip()
    unite = str(bloc.get("unite", "")).strip()
    if titre and unite:
        return f"{titre} ({unite})"
    return titre or unite


def _marqueur(x, y, indice, couleur, r=4.6):
    """Marqueur de forme variable : second canal, redondant avec la couleur."""
    forme = FORMES[indice % len(FORMES)]
    c = f'fill="{couleur}" stroke="{couleur}" stroke-width="1.2"'
    if forme == "cercle":
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" {c}/>'
    if forme == "carre":
        return (f'<rect x="{x-r:.1f}" y="{y-r:.1f}" width="{2*r:.1f}" '
                f'height="{2*r:.1f}" {c}/>')
    if forme == "triangle":
        return (f'<polygon points="{x:.1f},{y-r-1:.1f} {x+r+1:.1f},{y+r:.1f} '
                f'{x-r-1:.1f},{y+r:.1f}" {c}/>')
    if forme == "losange":
        return (f'<polygon points="{x:.1f},{y-r-1:.1f} {x+r+1:.1f},{y:.1f} '
                f'{x:.1f},{y+r+1:.1f} {x-r-1:.1f},{y:.1f}" {c}/>')
    if forme == "croix":
        return (f'<path d="M{x-r:.1f} {y-r:.1f} L{x+r:.1f} {y+r:.1f} '
                f'M{x-r:.1f} {y+r:.1f} L{x+r:.1f} {y-r:.1f}" fill="none" '
                f'stroke="{couleur}" stroke-width="2"/>')
    return (f'<polygon points="{x:.1f},{y+r+1:.1f} {x+r+1:.1f},{y-r:.1f} '
            f'{x-r-1:.1f},{y-r:.1f}" {c}/>')


def _plan(axe_x, axe_y, ech_x, ech_y, categories=None, defaut_x="", defaut_y=""):
    """Trace le cadre, les graduations, les libelles et les titres d'axes.

    ech_x et ech_y valent (bas, haut, graduations). Si categories est fourni,
    l'axe des abscisses devient categoriel et ech_x est ignore. Retourne
    (fragments, projeter_x, projeter_y).
    """
    frag = []
    bas_y, haut_y, ticks_y = ech_y
    etendue_y = (haut_y - bas_y) or 1.0

    def py(v):
        return MBS - (float(v) - bas_y) / etendue_y * (MBS - MHT)

    if categories is not None:
        n = max(1, len(categories))
        largeur_case = (MDR - MG) / float(n)

        def px(i):
            return MG + (float(i) + 0.5) * largeur_case
    else:
        bas_x, haut_x, ticks_x = ech_x
        etendue_x = (haut_x - bas_x) or 1.0

        def px(v):
            return MG + (float(v) - bas_x) / etendue_x * (MDR - MG)

    for v in ticks_y:
        y = py(v)
        frag.append(f'<line x1="{MG}" y1="{y:.1f}" x2="{MDR}" y2="{y:.1f}" '
                    f'stroke="{TRAIT}" stroke-width="0.5" stroke-opacity="0.35"/>')
        frag.append(f'<line x1="{MG-5}" y1="{y:.1f}" x2="{MG}" y2="{y:.1f}" '
                    f'stroke="{ENCRE}" stroke-width="1"/>')
        frag.append(_txt(MG - 9, y + 4, _fmt_nb(v), 11, ancre="end"))

    if categories is not None:
        maxi_car = max(4, int(largeur_case / 6.6))
        for i, cat in enumerate(categories):
            x = px(i)
            frag.append(f'<line x1="{x:.1f}" y1="{MBS}" x2="{x:.1f}" '
                        f'y2="{MBS+5}" stroke="{ENCRE}" stroke-width="1"/>')
            frag.append(_txt(x, MBS + 20, _tronquer(cat, maxi_car), 11,
                             ancre="middle"))
    else:
        for v in ticks_x:
            x = px(v)
            frag.append(f'<line x1="{x:.1f}" y1="{MBS}" x2="{x:.1f}" '
                        f'y2="{MBS+5}" stroke="{ENCRE}" stroke-width="1"/>')
            frag.append(_txt(x, MBS + 20, _fmt_nb(v), 11, ancre="middle"))

    frag.append(f'<line x1="{MG}" y1="{MHT}" x2="{MG}" y2="{MBS}" '
                f'stroke="{ENCRE}" stroke-width="1.5"/>')
    frag.append(f'<line x1="{MG}" y1="{MBS}" x2="{MDR}" y2="{MBS}" '
                f'stroke="{ENCRE}" stroke-width="1.5"/>')
    lib_x = _titre_axe(axe_x, defaut_x)
    lib_y = _titre_axe(axe_y, defaut_y)
    if lib_x:
        frag.append(_txt((MG + MDR) / 2, MBS + 46, _tronquer(lib_x, 70), 13,
                         gras=True, ancre="middle"))
    if lib_y:
        ymil = (MHT + MBS) / 2
        frag.append(f'<text x="30" y="{ymil:.0f}" font-family="{POLICE}" '
                    f'font-size="13" fill="{ENCRE}" text-anchor="middle" '
                    f'font-weight="{GRAISSE_TITRE}" '
                    f'transform="rotate(-90 30 {ymil:.0f})">'
                    f'{escape(_tronquer(lib_y, 46))}</text>')
    return frag, px, py


def _legende(entrees):
    """Legende en colonne reservee, jamais posee sur les donnees.

    entrees : (libelle, couleur, indice_forme ou None, tirets ou None).
    """
    if not entrees:
        return []
    montrees = entrees[:12]
    hauteur = 16 + 21 * len(montrees) + (16 if len(entrees) > 12 else 0)
    frag = [f'<rect x="{XLEG}" y="{MHT}" width="{W-XLEG-22}" '
            f'height="{hauteur}" rx="{RAYON}" fill="{FOND}" stroke="{TRAIT}" '
            f'stroke-width="0.8"/>']
    for i, (lib, couleur, forme, tirets) in enumerate(montrees):
        y = MHT + 26 + 21 * i
        if tirets is not None:
            dash = f' stroke-dasharray="{tirets}"' if tirets else ""
            frag.append(f'<line x1="{XLEG+10}" y1="{y-4:.0f}" x2="{XLEG+34}" '
                        f'y2="{y-4:.0f}" stroke="{couleur}" '
                        f'stroke-width="2.2"{dash}/>')
        if forme is not None:
            frag.append(_marqueur(XLEG + 22, y - 4, forme, couleur, 4.2))
        # une entree sans echantillon recupere la place du gabarit : son
        # libelle dispose alors de toute la largeur du cartouche
        xt = XLEG + (10 if (forme is None and tirets is None) else 42)
        frag.append(_txt(xt, y, _tronquer(lib, int((W - 26 - xt) / 6.4)), 11))
    if len(entrees) > 12:
        frag.append(_txt(XLEG + 12, MHT + 26 + 21 * len(montrees),
                         f"... {len(entrees)-12} de plus", 11, couleur=TRAIT))
    return frag


def _points(serie):
    """Normalise les points d'une serie en liste de couples (x, y)."""
    bruts = serie.get("points") or []
    sortie = []
    for p in bruts:
        try:
            if isinstance(p, dict):
                sortie.append((float(p.get("x")), float(p.get("y"))))
            else:
                sortie.append((float(p[0]), float(p[1])))
        except (TypeError, ValueError, IndexError):
            continue
    return sortie


def _erreur(serie, i):
    """Demi-hauteur de barre d'erreur du point i, 0 si absente."""
    err = serie.get("erreurs")
    if isinstance(err, (int, float)):
        return abs(float(err))
    if isinstance(err, list) and i < len(err):
        try:
            return abs(float(err[i]))
        except (TypeError, ValueError):
            return 0.0
    return 0.0


def courbe(data, titre="Courbe"):
    """Une ou plusieurs series x/y, axes gradues, legende, barres d'erreur.

    Donnees : {"axe_x": {"titre": "Duree", "unite": "h"},
               "axe_y": {"titre": "Concentration", "unite": "mg/L"},
               "depart_zero": true,
               "series": [{"nom": "Temoin", "points": [[0, 1.2], [1, 2.4]],
                           "marqueurs": true, "erreurs": [0.1, 0.2]}]}
    """
    series = [s for s in (data.get("series") or []) if isinstance(s, dict)]
    couleurs = _couleurs_series()
    xs, ys = [], []
    for s in series:
        for i, (x, y) in enumerate(_points(s)):
            e = _erreur(s, i)
            xs.append(x)
            ys.extend([y - e, y + e])
    ech_x = _echelle(min(xs) if xs else 0.0, max(xs) if xs else 1.0)
    ech_y = _echelle(min(ys) if ys else 0.0, max(ys) if ys else 1.0,
                     depart_zero=bool(data.get("depart_zero")))
    frag, px, py = _plan(data.get("axe_x"), data.get("axe_y"), ech_x, ech_y)
    entrees = []
    for i, s in enumerate(series):
        pts = _points(s)
        if not pts:
            continue
        couleur = couleurs[i % len(couleurs)]
        tirets = TIRETS[i % len(TIRETS)]
        dash = f' stroke-dasharray="{tirets}"' if tirets else ""
        chemin = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in pts)
        frag.append(f'<polyline points="{chemin}" fill="none" '
                    f'stroke="{couleur}" stroke-width="2.2"{dash}/>')
        for j, (x, y) in enumerate(pts):
            e = _erreur(s, j)
            if e:
                hx, h1, h2 = px(x), py(y - e), py(y + e)
                frag.append(f'<path d="M{hx:.1f} {h1:.1f} L{hx:.1f} {h2:.1f} '
                            f'M{hx-4:.1f} {h1:.1f} L{hx+4:.1f} {h1:.1f} '
                            f'M{hx-4:.1f} {h2:.1f} L{hx+4:.1f} {h2:.1f}" '
                            f'fill="none" stroke="{couleur}" stroke-width="1.2"/>')
            if s.get("marqueurs", True):
                frag.append(_marqueur(px(x), py(y), i, couleur, 4.0))
        entrees.append((str(s.get("nom", f"Serie {i+1}")), couleur,
                        i if s.get("marqueurs", True) else None, tirets))
    frag.extend(_legende(entrees))
    return NL.join([_cadre(HD), _titre(titre)] + frag + ["</svg>"])


def nuage(data, titre="Nuage de points"):
    """Nuage de points, series distinguees par couleur et par forme.

    Donnees : {"axe_x": {"titre": "Masse", "unite": "kg"},
               "axe_y": {"titre": "Rendement", "unite": "%"},
               "series": [{"nom": "Lot A", "points": [[1, 2], [3, 4]],
                           "ajustement": true}]}
    L'ajustement est une droite des moindres carres, declaree comme telle dans
    la legende : elle n'est pas une donnee mesuree.
    """
    series = [s for s in (data.get("series") or []) if isinstance(s, dict)]
    couleurs = _couleurs_series()
    xs, ys = [], []
    for s in series:
        for x, y in _points(s):
            xs.append(x)
            ys.append(y)
    ech_x = _echelle(min(xs) if xs else 0.0, max(xs) if xs else 1.0)
    ech_y = _echelle(min(ys) if ys else 0.0, max(ys) if ys else 1.0,
                     depart_zero=bool(data.get("depart_zero")))
    frag, px, py = _plan(data.get("axe_x"), data.get("axe_y"), ech_x, ech_y)
    entrees = []
    for i, s in enumerate(series):
        pts = _points(s)
        if not pts:
            continue
        couleur = couleurs[i % len(couleurs)]
        for x, y in pts:
            frag.append(_marqueur(px(x), py(y), i, couleur))
        entrees.append((str(s.get("nom", f"Serie {i+1}")), couleur, i, None))
        if s.get("ajustement") and len(pts) >= 2:
            droite = _moindres_carres(pts)
            if droite:
                a, b = droite
                x1, x2 = ech_x[0], ech_x[1]
                frag.append(f'<line x1="{px(x1):.1f}" y1="{py(a*x1+b):.1f}" '
                            f'x2="{px(x2):.1f}" y2="{py(a*x2+b):.1f}" '
                            f'stroke="{couleur}" stroke-width="1.6" '
                            f'stroke-dasharray="7 4"/>')
                entrees.append((f"{s.get('nom', 'Serie')} : ajustement",
                                couleur, None, "7 4"))
    frag.extend(_legende(entrees))
    return NL.join([_cadre(HD), _titre(titre)] + frag + ["</svg>"])


def _moindres_carres(pts):
    """Pente et ordonnee a l'origine, None si les x sont tous confondus."""
    n = float(len(pts))
    sx = sum(p[0] for p in pts)
    sy = sum(p[1] for p in pts)
    sxx = sum(p[0] * p[0] for p in pts)
    sxy = sum(p[0] * p[1] for p in pts)
    den = n * sxx - sx * sx
    if abs(den) < 1e-12:
        return None
    a = (n * sxy - sx * sy) / den
    return a, (sy - a * sx) / n


def histogramme(data, titre="Histogramme"):
    """Barres verticales, categories ou classes, ordonnees partant de zero.

    Donnees : {"axe_x": {"titre": "Classe d'age"},
               "axe_y": {"titre": "Effectif", "unite": "individus"},
               "barres": [{"categorie": "18-24", "valeur": 42, "erreur": 3}]}
    L'axe des ordonnees part toujours de zero : une base tronquee exagere les
    ecarts entre barres, ce que l'audit signale.
    """
    barres = [b for b in (data.get("barres") or []) if isinstance(b, dict)]
    couleurs = _couleurs_series()
    valeurs, cats = [], []
    for b in barres:
        try:
            v = float(b.get("valeur"))
        except (TypeError, ValueError):
            v = 0.0
        e = abs(float(b.get("erreur") or 0))
        valeurs.append(v)
        cats.append(str(b.get("categorie", "")))
        valeurs.extend([v - e, v + e])
    ech_y = _echelle(min(valeurs) if valeurs else 0.0,
                     max(valeurs) if valeurs else 1.0, depart_zero=True)
    frag, px, py = _plan(data.get("axe_x"), data.get("axe_y"), None, ech_y,
                         categories=cats or [""])
    largeur_case = (MDR - MG) / float(max(1, len(cats)))
    lb = max(6.0, largeur_case * 0.62)
    zero = py(0)
    for i, b in enumerate(barres):
        try:
            v = float(b.get("valeur"))
        except (TypeError, ValueError):
            continue
        couleur = couleurs[i % len(couleurs)] if data.get("couleur_par_barre") \
            else couleurs[0]
        x, y = px(i), py(v)
        haut, bas = min(y, zero), abs(zero - y)
        frag.append(f'<rect x="{x-lb/2:.1f}" y="{haut:.1f}" width="{lb:.1f}" '
                    f'height="{max(1.0, bas):.1f}" fill="{couleur}" '
                    f'fill-opacity="0.85" stroke="{ENCRE}" stroke-width="0.8"/>')
        e = abs(float(b.get("erreur") or 0))
        if e:
            h1, h2 = py(v - e), py(v + e)
            frag.append(f'<path d="M{x:.1f} {h1:.1f} L{x:.1f} {h2:.1f} '
                        f'M{x-4:.1f} {h1:.1f} L{x+4:.1f} {h1:.1f} '
                        f'M{x-4:.1f} {h2:.1f} L{x+4:.1f} {h2:.1f}" fill="none" '
                        f'stroke="{ENCRE}" stroke-width="1.2"/>')
        if data.get("valeurs_affichees", True) and len(barres) <= 14:
            frag.append(_txt(x, haut - (10 if e else 6), _fmt_nb(v), 10,
                             ancre="middle", couleur=ENCRE))
    frag.append(f'<line x1="{MG}" y1="{zero:.1f}" x2="{MDR}" y2="{zero:.1f}" '
                f'stroke="{ENCRE}" stroke-width="1.5"/>')
    return NL.join([_cadre(HD), _titre(titre)] + frag + ["</svg>"])


def _quartiles(valeurs):
    """Cinq nombres et points aberrants (regle de 1,5 ecart interquartile)."""
    v = sorted(float(x) for x in valeurs)
    n = len(v)

    def q(p):
        if n == 1:
            return v[0]
        pos = p * (n - 1)
        bas, haut = int(math.floor(pos)), int(math.ceil(pos))
        return v[bas] + (v[haut] - v[bas]) * (pos - bas)

    q1, med, q3 = q(0.25), q(0.5), q(0.75)
    ei = q3 - q1
    binf, bsup = q1 - 1.5 * ei, q3 + 1.5 * ei
    dedans = [x for x in v if binf <= x <= bsup] or v
    return {"q1": q1, "mediane": med, "q3": q3, "min": min(dedans),
            "max": max(dedans),
            "aberrants": [x for x in v if x < binf or x > bsup]}


def _stats_groupe(g):
    """Cinq nombres d'un groupe : calcules si des valeurs brutes sont fournies,
    lus tels quels sinon."""
    vals = g.get("valeurs")
    if isinstance(vals, list) and vals:
        try:
            return _quartiles(vals)
        except (TypeError, ValueError):
            return None
    try:
        st = {c: float(g[c]) for c in ("min", "q1", "mediane", "q3", "max")}
    except (KeyError, TypeError, ValueError):
        return None
    st["aberrants"] = [float(x) for x in (g.get("aberrants") or [])]
    return st


def boite(data, titre="Boites a moustaches"):
    """Une boite par groupe : mediane, quartiles, moustaches, points aberrants.

    Donnees : {"axe_x": {"titre": "Groupe"},
               "axe_y": {"titre": "Duree", "unite": "min"},
               "groupes": [{"nom": "Temoin", "valeurs": [12, 14, 19, 22]},
                           {"nom": "Traite", "min": 8, "q1": 11, "mediane": 13,
                            "q3": 16, "max": 20, "aberrants": [31]}]}
    Les valeurs brutes donnent les quartiles par la regle de 1,5 ecart
    interquartile ; les cinq nombres peuvent aussi etre fournis tels quels.
    """
    groupes = [g for g in (data.get("groupes") or []) if isinstance(g, dict)]
    couleurs = _couleurs_series()
    stats, noms = [], []
    for g in groupes:
        st = _stats_groupe(g)
        stats.append(st)
        noms.append(str(g.get("nom", "")))
    toutes = []
    for st in stats:
        if st:
            toutes.extend([st["min"], st["max"]] + list(st["aberrants"]))
    ech_y = _echelle(min(toutes) if toutes else 0.0,
                     max(toutes) if toutes else 1.0,
                     depart_zero=bool(data.get("depart_zero")))
    frag, px, py = _plan(data.get("axe_x"), data.get("axe_y"), None, ech_y,
                         categories=noms or [""], defaut_x="Groupe")
    largeur_case = (MDR - MG) / float(max(1, len(noms)))
    lb = max(14.0, min(70.0, largeur_case * 0.5))
    for i, st in enumerate(stats):
        if not st:
            continue
        couleur = couleurs[i % len(couleurs)]
        x = px(i)
        yq1, yq3, ymed = py(st["q1"]), py(st["q3"]), py(st["mediane"])
        ymin, ymax = py(st["min"]), py(st["max"])
        frag.append(f'<path d="M{x:.1f} {ymin:.1f} L{x:.1f} {yq1:.1f} '
                    f'M{x:.1f} {yq3:.1f} L{x:.1f} {ymax:.1f} '
                    f'M{x-lb/4:.1f} {ymin:.1f} L{x+lb/4:.1f} {ymin:.1f} '
                    f'M{x-lb/4:.1f} {ymax:.1f} L{x+lb/4:.1f} {ymax:.1f}" '
                    f'fill="none" stroke="{ENCRE}" stroke-width="1.2"/>')
        frag.append(f'<rect x="{x-lb/2:.1f}" y="{min(yq1, yq3):.1f}" '
                    f'width="{lb:.1f}" height="{max(1.0, abs(yq1-yq3)):.1f}" '
                    f'fill="{couleur}" fill-opacity="0.45" stroke="{ENCRE}" '
                    f'stroke-width="1"/>')
        frag.append(f'<line x1="{x-lb/2:.1f}" y1="{ymed:.1f}" '
                    f'x2="{x+lb/2:.1f}" y2="{ymed:.1f}" stroke="{ENCRE}" '
                    f'stroke-width="2.4"/>')
        for ab in st["aberrants"]:
            frag.append(f'<circle cx="{x:.1f}" cy="{py(ab):.1f}" r="3.2" '
                        f'fill="none" stroke="{ENCRE}" stroke-width="1.2"/>')
    frag.extend(_legende([("Boite : Q1 a Q3", couleurs[0], None, ""),
                          ("Trait epais : mediane", ENCRE, None, ""),
                          ("Cercle vide : aberrant", ENCRE, None, None)]
                         if stats else []))
    return NL.join([_cadre(HD), _titre(titre)] + frag + ["</svg>"])


# --- Diagrammes de flux ----------------------------------------------------

FX_TITRE, FX_TITRE_L = 30, 118        # colonne des intitules d'etape
FX_BOITE, FX_BOITE_L = 168, 322       # colonne des boites principales
FX_EXCL, FX_EXCL_L = 552, 318         # colonne des exclusions


def _fleche(x1, y1, x2, y2, couleur=None):
    """Segment termine par une pointe pleine, dessinee sans marqueur SVG."""
    couleur = couleur or ENCRE
    dx, dy = x2 - x1, y2 - y1
    lg = math.hypot(dx, dy) or 1.0
    ux, uy = dx / lg, dy / lg
    bx, by = x2 - ux * 9, y2 - uy * 9
    nx, ny = -uy * 4.5, ux * 4.5
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" '
            f'stroke="{couleur}" stroke-width="1.4"/>'
            f'<polygon points="{x2:.1f},{y2:.1f} {bx+nx:.1f},{by+ny:.1f} '
            f'{bx-nx:.1f},{by-ny:.1f}" fill="{couleur}"/>')


def _lignes_boite(b, largeur_car):
    """Libelle avec son effectif entre parentheses, puis les sous-lignes."""
    libelle = str(b.get("libelle", b.get("motif", ""))).strip()
    eff = b.get("effectif", b.get("n"))
    if eff is not None and str(eff).strip() != "":
        libelle = f"{libelle} (n = {eff})" if libelle else f"n = {eff}"
    tetes = _envelopper(libelle, largeur_car)
    sous = []
    for s in (b.get("sous") or []):
        if isinstance(s, dict):
            n = s.get("effectif", s.get("n"))
            texte = str(s.get("libelle", s.get("motif", "")))
            s = f"{texte} : {n}" if n is not None else texte
        sous.extend(_envelopper("- " + str(s), largeur_car + 4))
    return tetes, sous


def _hauteur_boite(tetes, sous):
    return 16 + 18 * len(tetes) + 15 * len(sous) + 8


def _rendre_boite(x, y, larg, tetes, sous, fond):
    haut = _hauteur_boite(tetes, sous)
    frag = [f'<rect x="{x}" y="{y:.1f}" width="{larg}" height="{haut}" '
            f'rx="{RAYON}" fill="{fond}" stroke="{TRAIT}" stroke-width="1"/>']
    yc = y + 24
    for t in tetes:
        frag.append(_txt(x + 14, yc, t, 13, gras=True))
        yc += 18
    yc += 2
    for s in sous:
        frag.append(_txt(x + 14, yc, s, 11, couleur=TRAIT))
        yc += 15
    return frag, haut


def flux(data, titre="Diagramme de flux"):
    """Boites reliees par des fleches, a niveaux, effectifs entre parentheses.

    Donnees : {"niveaux": [{"titre": "Identification",
                            "boites": [{"libelle": "References trouvees",
                                        "effectif": 435,
                                        "sous": ["Bases : 420", "Autres : 15"],
                                        "exclusions": [{"libelle": "Doublons",
                                                        "effectif": 60}]}]}]}
    Chaque boite porte son effectif ; les exclusions sortent lateralement a
    droite, reliees par une fleche horizontale.
    """
    niveaux = [n for n in (data.get("niveaux") or []) if isinstance(n, dict)]
    plans = []
    y = 76
    for niv in niveaux:
        boites = [b for b in (niv.get("boites") or []) if isinstance(b, dict)]
        larg = FX_BOITE_L / float(max(1, len(boites))) - 10
        rendus = []
        haut_niv = 0
        for b in boites:
            tetes, sous = _lignes_boite(b, max(10, int((larg - 30) / 7.6)))
            h = _hauteur_boite(tetes, sous)
            excls = []
            for e in (b.get("exclusions") or []):
                if not isinstance(e, dict):
                    continue
                te, so = _lignes_boite(e, int((FX_EXCL_L - 30) / 7.6))
                excls.append((te, so, _hauteur_boite(te, so)))
            rendus.append((tetes, sous, h, excls))
            haut_niv = max(haut_niv, h, sum(e[2] + 10 for e in excls))
        plans.append((niv, boites, larg, rendus, y, haut_niv))
        y += haut_niv + 46
    hauteur = max(HD, int(y) + 10)

    frag = [_cadre(hauteur), _titre(titre)]
    centres = []
    for niv, boites, larg, rendus, ytop, haut_niv in plans:
        if niv.get("titre"):
            frag.append(f'<rect x="{FX_TITRE}" y="{ytop:.1f}" '
                        f'width="{FX_TITRE_L}" height="{haut_niv:.1f}" '
                        f'rx="{RAYON}" fill="{FONDS[1 % len(FONDS)]}" '
                        f'stroke="{TRAIT}" stroke-width="0.8"/>')
            ym = ytop + haut_niv / 2
            frag.append(f'<text x="{FX_TITRE+FX_TITRE_L/2:.0f}" y="{ym:.0f}" '
                        f'font-family="{POLICE_TITRE}" font-size="12" '
                        f'fill="{ENCRE}" text-anchor="middle" '
                        f'font-weight="{GRAISSE_TITRE}" transform="rotate(-90 '
                        f'{FX_TITRE+FX_TITRE_L/2:.0f} {ym:.0f})">'
                        f'{escape(_tronquer(str(niv["titre"]), 26))}</text>')
        rang = []
        y_excl = ytop
        for i, (tetes, sous, h, excls) in enumerate(rendus):
            x = FX_BOITE + i * (larg + 10)
            f2, _ = _rendre_boite(x, ytop, larg, tetes, sous, FONDS[0])
            frag.extend(f2)
            rang.append((x + larg / 2, ytop, ytop + h))
            for te, so, he in excls:
                f3, _ = _rendre_boite(FX_EXCL, y_excl, FX_EXCL_L, te, so,
                                      FONDS[3 % len(FONDS)])
                frag.extend(f3)
                frag.append(_fleche(x + larg, y_excl + he / 2, FX_EXCL - 2,
                                    y_excl + he / 2))
                y_excl += he + 10
        centres.append(rang)
    for i in range(len(centres) - 1):
        for j, (cx, _, ybas) in enumerate(centres[i]):
            cible = centres[i + 1][j] if j < len(centres[i + 1]) \
                else centres[i + 1][0]
            frag.append(_fleche(cx, ybas, cible[0], cible[1] - 2))
    frag.append("</svg>")
    return NL.join(frag)


def _cpt(v):
    """Lit un effectif entier, None si la valeur n'en est pas un."""
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


def _prisma_comptes(data):
    """Normalise les comptes du schema PRISMA (references/prisma.md).

    Retourne sources (libelle, effectif), identifiees, doublons, examinees,
    ecartees au criblage, evaluees, ecartees en texte integral, incluses.
    """
    ident = data.get("identifiees")
    sources, total = [], None
    if isinstance(ident, dict):
        total = 0
        for cle, val in ident.items():
            n = _cpt(val)
            sources.append((str(cle), n))
            if n is not None:
                total += n
    else:
        total = _cpt(ident)

    def motifs(cle):
        sortie = []
        for e in (data.get(cle) or []):
            if isinstance(e, dict):
                sortie.append((str(e.get("motif", e.get("libelle", ""))),
                               _cpt(e.get("n", e.get("effectif")))))
        return sortie

    return {"sources": sources, "identifiees": total,
            "doublons": _cpt(data.get("doublons")),
            "examinees": _cpt(data.get("examinees")),
            "ecartees_titre": motifs("ecartees_titre"),
            "evaluees": _cpt(data.get("evaluees")),
            "ecartees_texte": motifs("ecartees_texte"),
            "incluses": _cpt(data.get("incluses"))}


def prisma(data, titre="Selection des etudes (PRISMA)"):
    """Diagramme PRISMA de selection des etudes, bati sur le moteur de flux.

    Donnees : {"identifiees": {"Bases de donnees": 420, "Autres sources": 15},
               "doublons": 60, "examinees": 375,
               "ecartees_titre": [{"motif": "Hors sujet", "n": 200}],
               "evaluees": 175,
               "ecartees_texte": [{"motif": "Methode insuffisante", "n": 140}],
               "incluses": 35}
    "identifiees" accepte aussi un entier unique. Les comptes doivent boucler :
    identifiees moins doublons egale examinees, et ainsi de suite jusqu'aux
    incluses ; l'audit le verifie.
    """
    c = _prisma_comptes(data)
    sous_src = [f"{nom} : {n if n is not None else '?'}"
                for nom, n in c["sources"]]
    som_t = sum(n for _, n in c["ecartees_titre"] if n is not None)
    som_x = sum(n for _, n in c["ecartees_texte"] if n is not None)
    niveaux = [
        {"titre": "Identification",
         "boites": [{"libelle": "References identifiees",
                     "effectif": c["identifiees"], "sous": sous_src,
                     "exclusions": [{"libelle": "Doublons retires",
                                     "effectif": c["doublons"]}]
                     if c["doublons"] is not None else []}]},
        {"titre": "Criblage",
         "boites": [{"libelle": "References examinees (titre et resume)",
                     "effectif": c["examinees"],
                     "exclusions": [{"libelle": "References ecartees",
                                     "effectif": som_t,
                                     "sous": [{"libelle": m, "n": n}
                                              for m, n in c["ecartees_titre"]]}]
                     if c["ecartees_titre"] else []}]},
        {"titre": "Eligibilite",
         "boites": [{"libelle": "Articles evalues en texte integral",
                     "effectif": c["evaluees"],
                     "exclusions": [{"libelle": "Articles ecartes",
                                     "effectif": som_x,
                                     "sous": [{"libelle": m, "n": n}
                                              for m, n in c["ecartees_texte"]]}]
                     if c["ecartees_texte"] else []}]},
        {"titre": "Inclusion",
         "boites": [{"libelle": "Etudes incluses dans la synthese",
                     "effectif": c["incluses"]}]},
    ]
    return flux({"niveaux": niveaux}, titre)


# --- Audit structurel des figures de donnees -------------------------------

TYPES_DONNEES = ("courbe", "nuage", "histogramme", "boite", "flux", "prisma")


def _audit_axe(data, cle, nom, avert, exiger_unite=True):
    """Un axe sans titre ni unite laisse le lecteur deviner la grandeur."""
    bloc = data.get(cle) if isinstance(data.get(cle), dict) else {}
    if not str(bloc.get("titre", "")).strip():
        avert.append(f"Axe des {nom} sans titre : nommer la grandeur portee.")
    if exiger_unite and not str(bloc.get("unite", "")).strip():
        avert.append(f"Axe des {nom} sans unite : preciser l'unite de mesure "
                     f"(ou 'sans unite' quand la grandeur n'en a pas).")


def _audit_series(data, avert, exiger_ajustement=False):
    series = [s for s in (data.get("series") or []) if isinstance(s, dict)]
    if not series:
        avert.append("Aucune serie de donnees : la figure serait vide.")
    for i, s in enumerate(series):
        pts = _points(s)
        nom = str(s.get("nom", "")).strip()
        if not pts:
            avert.append(f"Serie '{nom or i + 1}' vide : aucun point "
                         f"exploitable, la retirer ou fournir ses donnees.")
        if not nom:
            avert.append(f"Serie {i + 1} sans nom : ses points ne sont pas "
                         f"etiquetes, la legende ne peut pas les designer.")
        err = s.get("erreurs")
        if isinstance(err, list) and pts and len(err) != len(pts):
            avert.append(f"Serie '{nom or i + 1}' : {len(err)} barres d'erreur "
                         f"pour {len(pts)} points, correspondance rompue.")
        if exiger_ajustement and s.get("ajustement") and len(pts) < 3:
            avert.append(f"Serie '{nom or i + 1}' : droite d'ajustement sur "
                         f"moins de 3 points, ajustement sans portee.")
    if len(series) > MAX_SERIES:
        avert.append(f"{len(series)} series tracees : au-dela de "
                     f"{MAX_SERIES} la figure devient illisible, en separer.")
    return series


def _audit_categories(libelles, avert, quoi="Categorie"):
    vus = set()
    for lib in libelles:
        lib = str(lib).strip()
        if not lib:
            avert.append(f"{quoi} sans libelle : une barre ou une boite "
                         f"anonyme ne se lit pas.")
        elif lib in vus:
            avert.append(f"{quoi} '{lib}' en double : deux entrees de meme "
                         f"nom se confondent a la lecture.")
        else:
            vus.add(lib)


def _auditer_donnees(type_fig, data, avert):
    """Controles structurels propres aux figures a axes et aux flux."""
    if type_fig == "courbe":
        _audit_axe(data, "axe_x", "abscisses", avert)
        _audit_axe(data, "axe_y", "ordonnees", avert)
        _audit_series(data, avert)
    if type_fig == "nuage":
        _audit_axe(data, "axe_x", "abscisses", avert)
        _audit_axe(data, "axe_y", "ordonnees", avert)
        _audit_series(data, avert, exiger_ajustement=True)
    if type_fig == "histogramme":
        _audit_axe(data, "axe_x", "abscisses", avert, exiger_unite=False)
        _audit_axe(data, "axe_y", "ordonnees", avert)
        barres = [b for b in (data.get("barres") or []) if isinstance(b, dict)]
        if not barres:
            avert.append("Aucune barre : l'histogramme serait vide.")
        _audit_categories([b.get("categorie", "") for b in barres], avert)
        for b in barres:
            if _cpt(b.get("valeur")) is None and b.get("valeur") is not None:
                avert.append(f"Barre '{b.get('categorie', '?')}' : valeur "
                             f"'{b.get('valeur')}' non numerique.")
            elif b.get("valeur") is None:
                avert.append(f"Barre '{b.get('categorie', '?')}' sans valeur.")
        base = (data.get("axe_y") or {}).get("min") if isinstance(
            data.get("axe_y"), dict) else None
        if base is None:
            base = data.get("y_min")
        if base is not None and _cpt(base) not in (0, None):
            avert.append(f"Echelle des ordonnees tronquee (base = {base}) : "
                         f"une base non nulle exagere l'ecart entre barres, "
                         f"c'est une faute d'honnetete. Repartir de zero.")
        if len(barres) > 20:
            avert.append(f"{len(barres)} barres : au-dela de 20 les libelles "
                         f"se chevauchent, regrouper les classes.")
    if type_fig == "boite":
        _audit_axe(data, "axe_x", "abscisses", avert, exiger_unite=False)
        _audit_axe(data, "axe_y", "ordonnees", avert)
        groupes = [g for g in (data.get("groupes") or [])
                   if isinstance(g, dict)]
        if not groupes:
            avert.append("Aucun groupe : la figure a moustaches serait vide.")
        _audit_categories([g.get("nom", "") for g in groupes], avert,
                          quoi="Groupe")
        for g in groupes:
            nom = str(g.get("nom", "?"))
            vals = g.get("valeurs")
            if isinstance(vals, list) and not vals:
                avert.append(f"Groupe '{nom}' : liste de valeurs vide.")
            st = _stats_groupe(g)
            if st is None:
                avert.append(f"Groupe '{nom}' : ni valeurs brutes ni les cinq "
                             f"nombres (min, q1, mediane, q3, max).")
                continue
            ordre = [st["min"], st["q1"], st["mediane"], st["q3"], st["max"]]
            if any(ordre[i] > ordre[i + 1] for i in range(4)):
                avert.append(
                    f"Groupe '{nom}' : moustaches incoherentes, l'ordre "
                    f"min <= Q1 <= mediane <= Q3 <= max n'est pas respecte "
                    f"(min={_fmt_nb(ordre[0])}, q1={_fmt_nb(ordre[1])}, "
                    f"mediane={_fmt_nb(ordre[2])}, q3={_fmt_nb(ordre[3])}, "
                    f"max={_fmt_nb(ordre[4])}).")
            if isinstance(vals, list) and 0 < len(vals) < 5:
                avert.append(f"Groupe '{nom}' : {len(vals)} valeurs, une boite "
                             f"a moustaches sur si peu de points egare plus "
                             f"qu'elle n'informe.")
        if len(groupes) > 12:
            avert.append(f"{len(groupes)} groupes : au-dela de 12 les boites "
                         f"deviennent trop etroites.")
    if type_fig == "flux":
        niveaux = [n for n in (data.get("niveaux") or [])
                   if isinstance(n, dict)]
        if not niveaux:
            avert.append("Aucun niveau : le diagramme de flux serait vide.")
        for i, niv in enumerate(niveaux):
            if not str(niv.get("titre", "")).strip():
                avert.append(f"Niveau {i + 1} sans titre d'etape.")
            boites = [b for b in (niv.get("boites") or [])
                      if isinstance(b, dict)]
            if not boites:
                avert.append(f"Niveau {i + 1} sans aucune boite.")
            for b in boites:
                lib = str(b.get("libelle", "")).strip()
                if not lib:
                    avert.append(f"Niveau {i + 1} : une boite sans libelle.")
                if _cpt(b.get("effectif")) is None:
                    avert.append(f"Boite '{lib or '?'}' sans effectif : un flux "
                                 f"sans compte ne se verifie pas.")
                for e in (b.get("exclusions") or []):
                    if isinstance(e, dict) and _cpt(e.get("effectif")) is None:
                        avert.append(f"Exclusion de '{lib or '?'}' sans "
                                     f"effectif.")
    if type_fig == "prisma":
        _auditer_prisma(data, avert)


def _auditer_prisma(data, avert):
    """Le controle le plus utile : un PRISMA dont les comptes ne bouclent pas
    est faux, quelle que soit la qualite de son rendu."""
    c = _prisma_comptes(data)
    for cle, nom in (("identifiees", "identifiees"), ("doublons", "doublons"),
                     ("examinees", "examinees"), ("evaluees", "evaluees"),
                     ("incluses", "incluses")):
        if c[cle] is None:
            avert.append(f"Compte '{nom}' absent ou non numerique : le schema "
                         f"PRISMA ne se boucle pas sans lui.")
    for lot, etape in (("ecartees_titre", "criblage"),
                       ("ecartees_texte", "texte integral")):
        if not c[lot]:
            avert.append(f"Aucun motif d'ecart a l'etape {etape} : chaque "
                         f"exclusion porte son motif (PRISMA).")
        for motif, n in c[lot]:
            if not motif.strip():
                avert.append(f"Ecart a l'etape {etape} sans motif nomme.")
            if n is None:
                avert.append(f"Ecart '{motif or '?'}' ({etape}) sans effectif.")
    if (c["identifiees"] is not None and c["doublons"] is not None
            and c["examinees"] is not None):
        attendu = c["identifiees"] - c["doublons"]
        if attendu != c["examinees"]:
            avert.append(
                f"Comptes non boucles a l'identification : identifiees "
                f"({c['identifiees']}) moins doublons ({c['doublons']}) fait "
                f"{attendu}, or examinees vaut {c['examinees']}.")
    som_t = sum(n for _, n in c["ecartees_titre"] if n is not None)
    if c["examinees"] is not None and c["evaluees"] is not None and c["ecartees_titre"]:
        ecart = c["examinees"] - c["evaluees"]
        if som_t != ecart:
            avert.append(
                f"Comptes non boucles au criblage : la somme des motifs "
                f"d'ecart ({som_t}) ne fait pas la difference entre examinees "
                f"({c['examinees']}) et evaluees ({c['evaluees']}), soit "
                f"{ecart}.")
    som_x = sum(n for _, n in c["ecartees_texte"] if n is not None)
    if c["evaluees"] is not None and c["incluses"] is not None and c["ecartees_texte"]:
        ecart = c["evaluees"] - c["incluses"]
        if som_x != ecart:
            avert.append(
                f"Comptes non boucles en texte integral : la somme des motifs "
                f"d'ecart ({som_x}) ne fait pas la difference entre evaluees "
                f"({c['evaluees']}) et incluses ({c['incluses']}), soit "
                f"{ecart}.")
    if c["incluses"] == 0:
        avert.append("Aucune etude incluse : verifier les criteres avant de "
                     "publier un schema qui ne retient rien.")
    for etape, (a, b) in (("criblage", (c["examinees"], c["evaluees"])),
                          ("texte integral", (c["evaluees"], c["incluses"]))):
        if a is not None and b is not None and b > a:
            avert.append(f"Etape {etape} : le compte sortant ({b}) depasse le "
                         f"compte entrant ({a}), un flux ne grossit pas.")


CONSTRUCTEURS = {"swot": swot, "bcg": bcg, "ansoff": ansoff, "pestel": pestel,
                 "chaine-valeur": chaine_valeur, "tam-sam-som": tam_sam_som,
                 "courbe": courbe, "nuage": nuage,
                 "histogramme": histogramme, "boite": boite,
                 "flux": flux, "prisma": prisma}

CASES = {
    "swot": ["forces", "faiblesses", "opportunites", "menaces"],
    "ansoff": ["penetration", "extension_produit", "extension_marche", "diversification"],
    "pestel": ["politique", "economique", "social", "technologique", "environnemental", "legal"],
}


def _numero(v):
    """Interprete une valeur comme un nombre si c'est sans ambiguite (separateurs milliers,
    virgule decimale, un seul symbole de devise ou pourcentage tolere), sinon None : pas de
    comparaison numerique risquee sur un suffixe d'unite (k, M, Md) qui demanderait une mise
    a l'echelle non geree ici."""
    s = str(v).strip().replace(" ", "").replace(" ", "")
    if not s:
        return None
    for symb in ("€", "$", "%"):
        s = s.replace(symb, "")
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def auditer(type_fig, data, theme=None):
    avert = []
    if type_fig in CASES:
        comptes = {}
        for cle in CASES[type_fig]:
            items = data.get(cle, [])
            comptes[cle] = len(items)
            if not items:
                avert.append(f"Case '{cle}' vide : une figure a case vide parait incomplete ou malhonnete.")
            if len(items) > 7:
                avert.append(f"Case '{cle}' : {len(items)} elements, plus de 7 et la lisibilite chute (le rendu tronque).")
            for it in items:
                if len(str(it)) > 90:
                    avert.append(f"Case '{cle}' : un element depasse 90 caracteres, le resumer.")
        valeurs = [c for c in comptes.values() if c]
        if valeurs and max(valeurs) >= 4 * max(1, min(valeurs)):
            avert.append("Desequilibre fort entre les cases : une case ecrase les autres, reequilibrer ou justifier.")
    if type_fig == "bcg":
        items = data.get("items", [])
        if not items:
            avert.append("Matrice BCG sans aucun domaine d'activite place.")
        for it in items:
            if not str(it.get("nom", "")).strip():
                avert.append("Un point BCG n'a pas de nom : un point non etiquete n'est pas lisible.")
            for axe in ("croissance", "part"):
                v = it.get(axe)
                if v is None:
                    avert.append(f"Point '{it.get('nom','?')}' : '{axe}' manquant, position arbitraire.")
                elif not (0 <= float(v) <= 100):
                    avert.append(f"Point '{it.get('nom','?')}' : '{axe}'={v} hors de 0-100, echelle faussee.")
        if len(items) > 10:
            avert.append("Plus de 10 bulles : surcharge, regrouper les domaines mineurs.")
    if type_fig == "tam-sam-som":
        blocs = {}
        for cle in ("tam", "sam", "som"):
            bloc = data.get(cle)
            if not isinstance(bloc, dict):
                avert.append(f"Bloc '{cle}' absent ou mal forme : attendu un objet avec 'libelle' et 'valeur'.")
                continue
            blocs[cle] = bloc
            if not str(bloc.get("libelle", "")).strip():
                avert.append(f"Bloc '{cle}' : libelle vide, un cercle sans libelle n'est pas lisible.")
            if not str(bloc.get("valeur", "")).strip():
                avert.append(f"Bloc '{cle}' : valeur vide.")
        if len(blocs) == 3:
            nums = {cle: _numero(blocs[cle].get("valeur")) for cle in ("tam", "sam", "som")}
            if all(n is not None for n in nums.values()):
                if not (nums["tam"] >= nums["sam"] >= nums["som"]):
                    avert.append(
                        f"Ordre attendu TAM >= SAM >= SOM non respecte (tam={nums['tam']:g}, "
                        f"sam={nums['sam']:g}, som={nums['som']:g}) : verifier les valeurs ou le sens des cercles."
                    )
            else:
                avert.append("Valeurs non toutes numeriques de facon univoque : ordre TAM >= SAM >= SOM non verifie automatiquement, a controler a l'oeil.")
    if type_fig in TYPES_DONNEES:
        _auditer_donnees(type_fig, data, avert)
    if theme is not None:
        t = charger_theme(theme)
        err, warn = valider_theme(t)
        for e in err:
            avert.append("Charte : " + e)
        for w in warn:
            avert.append("Charte : " + w)
    if not avert:
        avert.append("Aucun defaut structurel detecte. Verifier a l'oeil le titre, la source et l'honnetete des echelles.")
    return avert


def construire(type_fig, data, titre=None, theme=None):
    appliquer_theme(charger_theme(theme))
    fn = CONSTRUCTEURS[type_fig]
    return fn(data, titre) if titre else fn(data)


def main(argv=None):
    p = argparse.ArgumentParser(description="Generateur de figures strategiques.")
    p.add_argument("type", choices=sorted(CONSTRUCTEURS))
    p.add_argument("--out", help="fichier .svg de sortie")
    p.add_argument("--data", help="fichier JSON, ou - pour lire stdin")
    p.add_argument("--title", help="titre de la figure")
    p.add_argument("--theme", help="charte graphique JSON")
    p.add_argument("--audit", action="store_true", help="regard critique deterministe")
    a = p.parse_args(argv)
    data = {}
    if a.data == "-":
        brut = sys.stdin.read().strip()
        if brut:
            data = json.loads(brut)
    elif a.data:
        with open(a.data, encoding="utf-8") as f:
            data = json.load(f)
    if a.audit:
        print("Regard critique sur la figure :")
        for av in auditer(a.type, data, a.theme):
            print(f"  - {av}")
    if a.out:
        svg = construire(a.type, data, a.title, a.theme)
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"Figure ecrite : {a.out} ({len(svg)} octets)")
    elif not a.audit:
        print("Rien a faire : --out pour le SVG ou --audit pour la critique.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
