#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vérificateur de sources déterministe pour Scriptorium.

Extrait les URL et les DOI d'un document, retire les paramètres de suivi,
repère les doublons, contrôle la syntaxe des DOI. La vérification de
résolution réseau est optionnelle (--check-links) et désactivée par défaut.

Usage :
    python3 verify-sources.py FICHIER [--format text|json] [--check-links]
    cat refs.md | python3 verify-sources.py -

Le module est importable : analyser(texte) -> dict.
"""
import argparse
import json
import re
import sys

URL_RE = re.compile(r"https?://[^\s)>\]\"'}]+")
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
TRACKING = re.compile(
    r"(?i)(utm_[a-z]+|fbclid|gclid|mc_eid|mc_cid|igshid|_hsenc|_hsmi|"
    r"vero_id|oly_enc_id|ref|ref_src|spm)=[^&#]*")
PONCTU_FIN = ".,;:!?)]}»\"'"


def nettoyer_url(u):
    """Retire les paramètres de suivi et la ponctuation finale parasite."""
    u = u.rstrip(PONCTU_FIN)
    if "?" not in u and "#" not in u:
        return u
    base, _, reste = u.partition("?")
    frag = ""
    if "#" in reste:
        reste, _, frag = reste.partition("#")
    params = [p for p in reste.split("&") if p and not TRACKING.fullmatch(p)]
    propre = base
    if params:
        propre += "?" + "&".join(params)
    if frag:
        propre += "#" + frag
    return propre


def doi_valide(d):
    d = d.rstrip(PONCTU_FIN)
    return bool(re.fullmatch(r"10\.\d{4,9}/\S+", d))


def analyser(texte):
    urls_brutes = [m.group(0) for m in URL_RE.finditer(texte)]
    dois = sorted({m.group(0).rstrip(PONCTU_FIN) for m in DOI_RE.finditer(texte)})
    propres = []
    sales = []
    vues = {}
    doublons = []
    for u in urls_brutes:
        propre = nettoyer_url(u)
        if propre != u.rstrip(PONCTU_FIN):
            sales.append({"brut": u, "propre": propre})
        cle = propre.lower()
        if cle in vues:
            doublons.append(propre)
        else:
            vues[cle] = True
            propres.append(propre)
    dois_invalides = [d for d in dois if not doi_valide(d)]
    return {
        "urls": propres,
        "urls_a_nettoyer": sales,
        "doublons": sorted(set(doublons)),
        "dois": dois,
        "dois_invalides": dois_invalides,
    }


def verifier_liens(urls, timeout=8):
    """Contrôle de résolution réseau. Appelé seulement avec --check-links."""
    import urllib.request
    import urllib.error
    resultats = []
    for u in urls:
        statut = None
        ok = False
        try:
            req = urllib.request.Request(u, method="HEAD",
                                         headers={"User-Agent": "Scriptorium/0.2"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                statut = r.status
                ok = 200 <= r.status < 400
        except urllib.error.HTTPError as e:
            statut = e.code
            ok = e.code < 400
        except Exception as e:
            statut = f"erreur: {type(e).__name__}"
            ok = False
        resultats.append({"url": u, "statut": statut, "resout": ok})
    return resultats


def rapport_texte(d):
    out = ["Vérificateur de sources"]
    out.append(f"  URL uniques={len(d['urls'])}  à nettoyer={len(d['urls_a_nettoyer'])}"
               f"  doublons={len(d['doublons'])}  DOI={len(d['dois'])}"
               f"  DOI invalides={len(d['dois_invalides'])}")
    if d["urls_a_nettoyer"]:
        out.append("\nURL avec paramètres de suivi :")
        for s in d["urls_a_nettoyer"]:
            out.append(f"  {s['brut']}\n   -> {s['propre']}")
    if d["doublons"]:
        out.append("\nDoublons :")
        out += [f"  {u}" for u in d["doublons"]]
    if d["dois_invalides"]:
        out.append("\nDOI de syntaxe douteuse :")
        out += [f"  {x}" for x in d["dois_invalides"]]
    if "liens" in d:
        out.append("\nRésolution réseau :")
        for r in d["liens"]:
            etat = "OK" if r["resout"] else "ECHEC"
            out.append(f"  [{etat}] {r['statut']} {r['url']}")
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description="Vérificateur de sources Scriptorium.")
    p.add_argument("fichier", help="chemin du fichier, ou - pour stdin")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--check-links", action="store_true",
                   help="contrôle réseau de la résolution des URL (désactivé par défaut)")
    a = p.parse_args(argv)
    try:
        texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    except OSError as e:
        print(f"Erreur de lecture : {e}", file=sys.stderr)
        return 2
    d = analyser(texte)
    if a.check_links:
        d["liens"] = verifier_liens(d["urls"])
    if a.format == "json":
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print(rapport_texte(d))
    # code 1 si doublons, URL sales, DOI invalides, ou lien mort
    pb = bool(d["urls_a_nettoyer"] or d["doublons"] or d["dois_invalides"])
    if "liens" in d:
        pb = pb or any(not r["resout"] for r in d["liens"])
    return 1 if pb else 0


if __name__ == "__main__":
    sys.exit(main())
