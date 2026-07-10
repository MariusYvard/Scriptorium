#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Charte graphique de Scriptorium : chargement, validation, contraste.

Une charte définit l'identité visuelle appliquée aux figures et aux documents :
couleurs (encre, trait, fond, accent, palette), polices, filigrane, rayon des
angles. Le module normalise une charte fournie, la valide (couleurs bien
formées) et contrôle le contraste texte sur fond selon WCAG, pour qu'une charte
illisible soit signalée avant usage.

La palette de quatre fonds peut être fournie comme une liste de couleurs
hexadécimales, ou comme le nom d'une palette daltonisme-sûre intégrée
("okabe-ito" ou "wong", voir PALETTES). Si la palette est fournie à la main
(liste de couleurs), une vérification approximative signale les paires
proches en vision dichromate rouge-vert (avertissement, jamais une erreur).

La sortie --format latex vérifie, quand fc-list (fontconfig) est présent sur la
machine, que la police demandée par la charte est bien installée, et retombe
sur une famille Latin Modern sinon (backend optionnel, dégradation propre :
sans fc-list, le nom demandé est simplement repris tel quel, comme avant).

Usage :
    python3 theme.py charte.json [--format text|json|css|latex]

Module importable : charger(source) -> dict ; valider(theme) -> (erreurs, avertissements) ;
contraste(hex_a, hex_b) -> float ; distance_dichromate(hex_a, hex_b) -> float ;
css(theme) -> str ; latex(theme) -> str.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys

HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

DEFAUT = {
    "police": "Helvetica, Arial, sans-serif",
    "police_titre": None,
    "graisse_titre": 700,
    "encre": "#2E2A26",
    "trait": "#8A8175",
    "fond": "#FFFFFF",
    "accent": "#6E6356",
    "palette": ["#F4F1EC", "#EEF2F4", "#F1F0EA", "#F4EEF0"],
    "logo_texte": None,
    "rayon": 8,
}

# Palettes daltonisme-sûres nommées, valeurs hexadécimales vérifiées le 2026-07-10 contre deux
# sources vivantes et concordantes : jfly.uni-koeln.de/color/ (Okabe M., Ito K., 2008, "Color
# Universal Design (CUD) : How to make figures and presentations that are friendly to Colorblind
# people") et sa reprise en table hexadécimale explicite par siegal.bio.nyu.edu/color-palette/.
# "wong" reprend les 7 teintes chromatiques d'Okabe-Ito sans le noir : Wong B. (2011), "Points of
# view: Color blindness", Nature Methods 8, 441, doi.org/10.1038/nmeth.1618, cite explicitement
# Okabe et Ito comme origine de sa palette ; l'article n'étant pas en accès libre, les valeurs hex
# reprises ici sont celles d'Okabe-Ito vérifiées ci-dessus (pas une extraction indépendante de la
# figure de Wong), le noir en moins puisque Wong le réserve au texte et aux axes.
PALETTES = {
    "okabe-ito": ["#000000", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"],
    "wong": ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"],
}

# Seuil de l'approximation dichromate ci-dessous (distance sur un plan projeté 0-360 environ).
SEUIL_DICHROMATE = 40


def _hex_ok(c):
    return isinstance(c, str) and bool(HEX.match(c))


def charger(source):
    """source = chemin d'un JSON, dict déjà chargé, ou None. Retourne un thème
    normalisé fusionné avec les valeurs par défaut."""
    if source is None:
        brut = {}
    elif isinstance(source, dict):
        brut = source
    else:
        with open(source, encoding="utf-8") as f:
            brut = json.load(f)
    couleurs = brut.get("couleurs", {}) if isinstance(brut.get("couleurs"), dict) else {}
    t = dict(DEFAUT)
    for k in ("police", "police_titre", "graisse_titre", "logo_texte", "rayon"):
        if brut.get(k) is not None:
            t[k] = brut[k]
    for k in ("encre", "trait", "fond", "accent"):
        v = brut.get(k, couleurs.get(k))
        if v is not None:
            t[k] = v
    pal = brut.get("palette", couleurs.get("palette"))
    source_palette = "manuelle"
    if isinstance(pal, str):
        nom = pal.strip().lower()
        if nom in PALETTES:
            pal = list(PALETTES[nom])
            source_palette = nom
        else:
            t["_palette_nom_inconnu"] = pal
            pal = None
    if pal:
        pal = list(pal)
        if source_palette == "manuelle":
            while len(pal) < 4:
                pal.append(DEFAUT["palette"][len(pal)])
            pal = pal[:4]
        t["palette"] = pal
    else:
        source_palette = "defaut" if source_palette == "manuelle" else source_palette
    t["palette_source"] = source_palette
    if not t["police_titre"]:
        t["police_titre"] = t["police"]
    return t


def _lum(c):
    c = c.lstrip("#")
    rgb = [int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [(v / 12.92) if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contraste(a, b):
    """Ratio de contraste WCAG entre deux couleurs hexadécimales."""
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _projection_dichromate(hexcolor):
    """Projection grossière (moyenne rouge-vert, bleu) qui approxime ce qui reste
    discernable à un dichromate rouge-vert. Méthode dite "par moyenne" : plus simple
    qu'une matrice de simulation (Brettel, Vienot, Machado), documentée comme telle,
    jamais présentée comme une simulation clinique."""
    c = hexcolor.lstrip("#")
    r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    return ((r + g) / 2.0, float(b))


def distance_dichromate(a, b):
    """Distance approximative entre deux couleurs hexadécimales, vues par un
    dichromate rouge-vert (voir _projection_dichromate). Une distance faible
    signale une paire à risque de confusion, jamais une certitude clinique."""
    ma, ba = _projection_dichromate(a)
    mb, bb = _projection_dichromate(b)
    return ((ma - mb) ** 2 + (ba - bb) ** 2) ** 0.5


def valider(t):
    """Retourne (erreurs, avertissements). Une erreur invalide la charte,
    un avertissement signale un risque de lisibilité."""
    err, warn = [], []
    if t.get("_palette_nom_inconnu"):
        noms = ", ".join(sorted(PALETTES))
        warn.append(f"Palette nommée '{t['_palette_nom_inconnu']}' inconnue (attendu : {noms}) ; repli sur la palette par défaut.")
    for k in ("encre", "trait", "fond", "accent"):
        if not _hex_ok(t[k]):
            err.append(f"Couleur '{k}' invalide : {t[k]} (attendu #RRGGBB).")
    for i, c in enumerate(t["palette"]):
        if not _hex_ok(c):
            err.append(f"palette[{i}] invalide : {c} (attendu #RRGGBB).")
    if _hex_ok(t["encre"]) and _hex_ok(t["fond"]):
        r = contraste(t["encre"], t["fond"])
        if r < 4.5:
            warn.append(f"Contraste encre sur fond {r:.1f}:1 (< 4.5), texte peu lisible.")
    if _hex_ok(t["encre"]):
        for i, c in enumerate(t["palette"]):
            if _hex_ok(c) and contraste(t["encre"], c) < 4.5:
                warn.append(f"Contraste encre sur palette[{i}] {contraste(t['encre'], c):.1f}:1 (< 4.5).")
    if t.get("palette_source") == "manuelle":
        pal = t["palette"]
        for i in range(len(pal)):
            for j in range(i + 1, len(pal)):
                if _hex_ok(pal[i]) and _hex_ok(pal[j]):
                    d = distance_dichromate(pal[i], pal[j])
                    if d < SEUIL_DICHROMATE:
                        warn.append(
                            f"Vision dichromate (approximation) : palette[{i}] et palette[{j}] "
                            f"proches (distance {d:.0f} < {SEUIL_DICHROMATE}) ; ajouter une forme, "
                            f"un motif ou un libellé pour les distinguer sans la couleur seule."
                        )
    return err, warn


def css(t):
    """Emet une feuille de style de document derivee d'une charte normalisee.

    Tokens en :root, proprietes logiques, mesure fluide, focus visible et
    styles d'impression. Pas de !important ni de couleur pure (#000/#fff).
    """
    pal = t["palette"]
    return f""":root {{
  --police: {t['police']};
  --police-titre: {t['police_titre']};
  --graisse-titre: {t['graisse_titre']};
  --encre: {t['encre']};
  --trait: {t['trait']};
  --fond: {t['fond']};
  --accent: {t['accent']};
  --rayon: {t['rayon']}px;
  --pal-1: {pal[0]};
  --pal-2: {pal[1]};
  --pal-3: {pal[2]};
  --pal-4: {pal[3] if len(pal) > 3 else pal[0]};
}}
*, *::before, *::after {{ box-sizing: border-box; }}
body {{
  font-family: var(--police);
  color: var(--encre);
  background: var(--fond);
  line-height: 1.55;
  max-inline-size: clamp(45ch, 90%, 75ch);
  margin-inline: auto;
  margin-block: 2rem;
  padding-inline: 1.25rem;
  text-align: justify;
  text-wrap: pretty;
}}
h1, h2, h3 {{ font-family: var(--police-titre); font-weight: var(--graisse-titre); color: var(--encre); line-height: 1.2; text-wrap: balance; }}
h1 {{ font-size: 2rem; border-block-end: 3px solid var(--accent); padding-block-end: .3rem; }}
h2 {{ font-size: 1.4rem; margin-block-start: 2rem; }}
h3 {{ font-size: 1.15rem; }}
a {{ color: var(--accent); }}
a:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
nav {{ background: var(--pal-1); border-radius: var(--rayon); padding: 1rem 1.25rem; }}
nav a {{ text-decoration: none; }}
figure {{ margin-block: 1.5rem; }}
figure svg, figure img {{ max-inline-size: 100%; height: auto; }}
figcaption {{ font-size: .9rem; color: var(--trait); border-block-start: 1px solid var(--trait); padding-block-start: .3rem; }}
table {{ border-collapse: collapse; inline-size: 100%; margin-block: 1.5rem; }}
caption {{ caption-side: top; font-weight: var(--graisse-titre); text-align: start; padding-block-end: .4rem; }}
th, td {{ border: 1px solid var(--trait); padding: .5rem .6rem; text-align: start; }}
thead th {{ background: var(--pal-2); }}
blockquote {{ border-inline-start: 4px solid var(--accent); margin-block: 1rem; padding: .4rem 1rem; background: var(--pal-3); border-radius: var(--rayon); }}
.encadre {{ background: var(--pal-4); border-radius: var(--rayon); padding: 1rem 1.25rem; margin-block: 1.5rem; }}
code {{ font-family: ui-monospace, "Cascadia Code", monospace; }}
@media print {{
  @page {{ margin: 2cm; }}
  body {{ max-inline-size: none; margin: 0; }}
  h1, h2 {{ break-after: avoid; }}
  figure, table {{ break-inside: avoid; }}
  a {{ color: var(--encre); }}
  *, *::before, *::after {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
}}"""


def _slug_hex(c):
    return c.lstrip("#").upper()


_GENERIQUES_LATEX = {
    "serif": "Latin Modern Roman",
    "sans-serif": "Latin Modern Sans",
    "monospace": "Latin Modern Mono",
}


def _polices_installees():
    """Ensemble des noms de famille connus de fontconfig (fc-list), en minuscules.
    None si fc-list est absent : disponibilité inconnue, jamais supposée vraie à l'aveugle."""
    if not shutil.which("fc-list"):
        return None
    try:
        out = subprocess.run(["fc-list", "--format", "%{family[0]}\n"],
                              capture_output=True, text=True, timeout=10).stdout
        return {ligne.strip().lower() for ligne in out.splitlines() if ligne.strip()}
    except Exception:
        return None


def _police_latex(pile_css):
    """Choisit un nom de police pour fontspec depuis une pile CSS du type
    'Georgia, "Times New Roman", serif' : essaie chaque nom dans l'ordre contre les
    polices installées (fc-list, si présent sur la machine), retient le premier trouvé.
    Sans fc-list (disponibilité inconnue), retient le premier nom précis sans le vérifier,
    comme avant. Si aucun nom précis ne correspond à une police installée, retombe sur la
    famille Latin Modern indiquée par le dernier mot-clé générique de la pile (serif,
    sans-serif, monospace), présente dans toute distribution TeX Live standard.

    Retourne (nom_retenu, avertissement_ou_None). L'avertissement est un texte à faire
    remonter (jamais une erreur : la compilation xelatex reste possible avec le repli)."""
    noms = [n.strip().strip("'\"") for n in pile_css.split(",") if n.strip()]
    disponibles = _polices_installees()
    repli = "Latin Modern Roman"
    demandes_precises = []
    for n in noms:
        if n.lower() in _GENERIQUES_LATEX:
            repli = _GENERIQUES_LATEX[n.lower()]
            continue
        demandes_precises.append(n)
        if disponibles is None or n.lower() in disponibles:
            return n, None
    if demandes_precises:
        return repli, (f"aucune des polices demandées ({', '.join(demandes_precises)}) "
                        f"n'a été trouvée par fc-list, repli sur {repli}.")
    return repli, None


def latex(t):
    """Emet un préambule LaTeX (couleurs puis polices) dérivé d'une charte normalisée,
    même logique que css(t) : un bloc à coller dans le préambule d'un gabarit compilé
    par xelatex ou lualatex (voir assets/gabarit-rapport.tex, assets/gabarit-poster.tex,
    entre le chargement de xcolor/fontspec et \\begin{document}). Ce module reste sans
    dépendance : il n'invoque aucun compilateur, la compilation reste optionnelle et
    externe (voir produire/references/equation.md pour la même convention).
    """
    pal = t["palette"]
    noms_pal = ["ScriptoriumPalUn", "ScriptoriumPalDeux", "ScriptoriumPalTrois", "ScriptoriumPalQuatre"]
    lignes = [
        "% Préambule de couleurs et polices dérivé de la charte graphique (theme.py --format latex)",
        "% À coller entre \\usepackage{xcolor} (et fontspec) et \\begin{document}.",
        f"\\definecolor{{ScriptoriumEncre}}{{HTML}}{{{_slug_hex(t['encre'])}}}",
        f"\\definecolor{{ScriptoriumTrait}}{{HTML}}{{{_slug_hex(t['trait'])}}}",
        f"\\definecolor{{ScriptoriumFond}}{{HTML}}{{{_slug_hex(t['fond'])}}}",
        f"\\definecolor{{ScriptoriumAccent}}{{HTML}}{{{_slug_hex(t['accent'])}}}",
    ]
    for nom, c in zip(noms_pal, pal[:4]):
        if _hex_ok(c):
            lignes.append(f"\\definecolor{{{nom}}}{{HTML}}{{{_slug_hex(c)}}}")
    police_principale, avert_princ = _police_latex(t['police'])
    if avert_princ:
        lignes.append(f"% Attention : {avert_princ}")
    lignes.append(f"\\setmainfont{{{police_principale}}}")
    if t["police_titre"] and t["police_titre"] != t["police"]:
        police_titre, avert_titre = _police_latex(t["police_titre"])
        if avert_titre:
            lignes.append(f"% Attention : {avert_titre}")
        lignes.append(f"\\newfontfamily\\policetitre{{{police_titre}}}")
    return "\n".join(lignes)


def main(argv=None):
    p = argparse.ArgumentParser(description="Validation d'une charte graphique.")
    p.add_argument("fichier", help="chemin du JSON de charte")
    p.add_argument("--format", choices=["text", "json", "css", "latex"], default="text")
    a = p.parse_args(argv)
    try:
        t = charger(a.fichier)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Erreur de lecture : {e}", file=sys.stderr)
        return 2
    err, warn = valider(t)
    if a.format == "json":
        print(json.dumps({"theme": t, "erreurs": err, "avertissements": warn},
                         ensure_ascii=False, indent=2))
    elif a.format == "css":
        print(css(t))
    elif a.format == "latex":
        print(latex(t))
    else:
        print("Charte graphique normalisee :")
        for k, v in t.items():
            if k.startswith("_"):
                continue
            print(f"  {k}: {v}")
        print("Erreurs :" if err else "Erreurs : aucune")
        for e in err:
            print(f"  - {e}")
        print("Avertissements :" if warn else "Avertissements : aucun")
        for w in warn:
            print(f"  - {w}")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
