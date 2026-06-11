#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Linter de style maison déterministe pour Scriptorium.

Détecte mécaniquement les écarts aux directives strictes, sans jugement de
modèle : tiret cadratin, typographie courbe, lexique promotionnel banni,
paramètres de suivi dans les URL, virgule d'Oxford, métadiscours, pronom
indéfini « on », quantificateurs vagues, verbes tics.

Usage :
    python3 lint-style.py FICHIER [--format text|json] [--strict] [--quiet]
    cat doc.md | python3 lint-style.py -

Codes de sortie :
    0  aucun constat critique (ni majeur si --strict)
    1  au moins un constat critique (ou majeur si --strict)
    2  erreur d'usage

Pragmas dans le document analysé :
    une ligne contenant « lint-style:ignore » n'est pas analysée.
    un fichier dont les 5 premières lignes contiennent « lint-style:ignore-file »
    est ignoré entièrement.

Le module est importable : lint_text(texte) -> liste de constats.
"""
import argparse
import json
import re
import sys

CRITIQUE, MAJEUR, MINEUR = "critique", "majeur", "mineur"
ORDRE = {CRITIQUE: 0, MAJEUR: 1, MINEUR: 2}

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
]

# Termes bannis cités par les fichiers de référence du plugin : on n'analyse
# pas ces fichiers (ils énoncent les interdits). Détection par marqueur.
MARQUEUR_FICHIER = "lint-style:ignore-file"
MARQUEUR_LIGNE = "lint-style:ignore"


def lint_text(texte, chemin=None):
    """Analyse un texte et retourne la liste des constats.

    Chaque constat est un dict : ligne, colonne, severite, regle, message, extrait.
    """
    lignes = texte.splitlines()
    if any(MARQUEUR_FICHIER in l for l in lignes[:5]):
        return []
    constats = []
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
        for regex, severite, regle, message in REGLES:
            for m in regex.finditer(ligne):
                deb = max(0, m.start() - 20)
                fin = min(len(ligne), m.end() + 20)
                extrait = ligne[deb:fin].strip()
                constats.append({
                    "ligne": i,
                    "colonne": m.start() + 1,
                    "severite": severite,
                    "regle": regle,
                    "message": message,
                    "extrait": extrait,
                    "trouve": m.group(0),
                })
    constats.sort(key=lambda c: (ORDRE[c["severite"]], c["ligne"], c["colonne"]))
    return constats


def compter(constats):
    n = {CRITIQUE: 0, MAJEUR: 0, MINEUR: 0}
    for c in constats:
        n[c["severite"]] += 1
    return n


def rapport_texte(constats, chemin):
    n = compter(constats)
    out = []
    titre = chemin or "(stdin)"
    out.append(f"Linter de style maison : {titre}")
    out.append(f"  critiques={n[CRITIQUE]}  majeurs={n[MAJEUR]}  mineurs={n[MINEUR]}")
    if not constats:
        out.append("  Aucun écart détecté.")
        return "\n".join(out)
    sev_courante = None
    for c in constats:
        if c["severite"] != sev_courante:
            sev_courante = c["severite"]
            out.append(f"\n[{sev_courante.upper()}]")
        out.append(f"  L{c['ligne']}:{c['colonne']} ({c['regle']}) "
                   f"« {c['trouve']} » -> {c['message']}")
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
    a = p.parse_args(argv)
    try:
        if a.fichier == "-":
            texte = sys.stdin.read()
            chemin = None
        else:
            with open(a.fichier, encoding="utf-8") as f:
                texte = f.read()
            chemin = a.fichier
    except OSError as e:
        print(f"Erreur de lecture : {e}", file=sys.stderr)
        return 2
    constats = lint_text(texte, chemin)
    if not a.quiet:
        if a.format == "json":
            print(json.dumps({
                "fichier": chemin,
                "compte": compter(constats),
                "constats": constats,
            }, ensure_ascii=False, indent=2))
        else:
            print(rapport_texte(constats, chemin))
    return code_sortie(constats, a.strict)


if __name__ == "__main__":
    sys.exit(main())
