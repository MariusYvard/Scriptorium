#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Charte graphique de Scriptorium : chargement, validation, contraste.

Une charte définit l'identité visuelle appliquée aux figures et aux documents :
couleurs (encre, trait, fond, accent, palette), polices, filigrane, rayon des
angles. Le module normalise une charte fournie, la valide (couleurs bien
formées) et contrôle le contraste texte sur fond selon WCAG, pour qu'une charte
illisible soit signalée avant usage.

Usage :
    python3 theme.py charte.json [--format text|json]

Module importable : charger(source) -> dict ; valider(theme) -> (erreurs, avertissements) ;
contraste(hex_a, hex_b) -> float.
"""
import argparse
import json
import re
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
    if pal:
        pal = list(pal)
        while len(pal) < 4:
            pal.append(DEFAUT["palette"][len(pal)])
        t["palette"] = pal[:4]
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


def valider(t):
    """Retourne (erreurs, avertissements). Une erreur invalide la charte,
    un avertissement signale un risque de lisibilité."""
    err, warn = [], []
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
    return err, warn


def main(argv=None):
    p = argparse.ArgumentParser(description="Validation d'une charte graphique.")
    p.add_argument("fichier", help="chemin du JSON de charte")
    p.add_argument("--format", choices=["text", "json"], default="text")
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
    else:
        print("Charte graphique normalisee :")
        for k, v in t.items():
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
