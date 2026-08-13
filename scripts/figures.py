#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generateur de figures strategiques en SVG pour Scriptorium.

Produit des schemas deterministes et sobres : SWOT, matrice BCG, matrice
d'Ansoff, PESTEL, chaine de valeur de Porter, ainsi que trois cercles imbriques
TAM/SAM/SOM (etude de marche). Applique une charte graphique fournie (--theme
charte.json) : couleurs, polices, filet d'accent, fond, filigrane, rayon des
angles. Un audit (--audit) porte un regard critique sur la figure, charte
comprise (contraste).

Usage :
    python3 figures.py TYPE --out f.svg [--data data.json|-] [--title "T"] [--theme charte.json]
    python3 figures.py TYPE --data - --audit --theme charte.json < data.json

TYPE : swot | bcg | ansoff | pestel | chaine-valeur | tam-sam-som
Module importable : construire(type, data, titre, theme) ; auditer(type, data, theme).
"""
import argparse
import json
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


CONSTRUCTEURS = {"swot": swot, "bcg": bcg, "ansoff": ansoff, "pestel": pestel,
                 "chaine-valeur": chaine_valeur, "tam-sam-som": tam_sam_som}

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
