#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Portions adaptees du projet openscience (Synthetic Sciences, InkVell Inc.),
Apache-2.0, github.com/synthetic-sciences/openscience. Modifications Marius
Yvard, MIT.

Vérificateur de sources déterministe pour Scriptorium.

Extrait les URL et les DOI d'un document, retire les paramètres de suivi,
repère les doublons, contrôle la syntaxe des DOI. Classe chaque URL par
palier de source (table locale de domaines, sans réseau : voir
PALIERS_DOMAINES). La vérification de résolution réseau des liens est
optionnelle (--check-links) et désactivée par défaut.

Paliers de domaine (sans réseau) : chaque URL du document est confrontée à
une table locale d'une vingtaine de domaines connus (revue à comité de
lecture, prépublication, institutionnel, encyclopédie, presse ou blog).
Un domaine absent de la table est classé "non-classe", jamais rangé par
défaut dans une catégorie qu'il ne mérite pas forcément. Le palier est un
indice mécanique de premier tri, pas un jugement de fiabilité définitif : voir
references/hierarchie-preuve.md pour la fiche de notation complète.

Mode réseau étendu (--reseau) : triangule chaque DOI trouvé auprès de trois
index bibliographiques (Crossref, OpenAlex, Semantic Scholar), en urllib pur,
avec délais courts et dégradation gracieuse (un index qui ne répond pas est
ignoré, jamais compté comme un échec de la référence). Calcule un verdict
gradué par référence (verifie / plausible / inverifiable / fabrique) et
signale les identifiants arXiv récents absents des index consultés (signal
de contamination, consultatif, jamais une preuve à lui seul).

Usage :
    python3 verify-sources.py FICHIER [--format text|json] [--check-links]
    python3 verify-sources.py FICHIER --reseau [--openalex-cle CLE] [--annee-reference AAAA]
    cat refs.md | python3 verify-sources.py -

OpenAlex exige désormais une clé API gratuite (constaté le 2026-07-08 sur
developers.openalex.org/api-reference/authentication). Sans clé fournie par
--openalex-cle ou la variable d'environnement OPENALEX_API_KEY, cet index est
ignoré et compté comme non consulté, jamais comme un échec.

Le module est importable : analyser(texte) -> dict ; trianguler_doi(doi) ;
detecter_contamination(texte) ; palier_domaine(url).
"""
import argparse
import datetime
import difflib
import json
import os
import re
import sys

URL_RE = re.compile(r"https?://[^\s)>\]\"'}]+")
DOI_RE = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
ARXIV_RE = re.compile(r"\barXiv:\s?(\d{2})(\d{2})\.(\d{4,5})\b", re.I)
TRACKING = re.compile(
    r"(?i)(utm_[a-z]+|fbclid|gclid|mc_eid|mc_cid|igshid|_hsenc|_hsmi|"
    r"vero_id|oly_enc_id|ref|ref_src|spm)=[^&#]*")
PONCTU_FIN = ".,;:!?)]}»\"'"

SEUIL_SIMILARITE = 0.70  # documenté dans references/integrite-sources.md
FENETRE_CONTAMINATION_ANS = 2  # un preprint est "recent" dans cette fenetre
INDEX_TIMEOUT = 8
USER_AGENT_RESEAU = "Scriptorium/0.7 (+https://github.com/MariusYvard/Scriptorium)"

# Table locale domaine -> palier de source, sans reseau. Cinq paliers :
# revue-a-comite (revue evaluee par les pairs, editeur academique etabli),
# preprint (serveur de prepublication), institutionnel (gouvernement,
# organisation internationale, base bibliographique publique), encyclopedie,
# presse-blog (presse generaliste ou billet non evalue). Adapte de la logique
# de detection de palier de lookup.py (research-lookup, openscience), qui
# classe par sous-chaine d'URL de facon deterministe et sans dependance ;
# taxonomie et liste de domaines propres a Scriptorium (les paliers d'origine
# jugeaient la notoriete d'une revue, pas la nature de la source).
PALIERS_DOMAINES = {
    "nature.com": "revue-a-comite",
    "science.org": "revue-a-comite",
    "cell.com": "revue-a-comite",
    "nejm.org": "revue-a-comite",
    "thelancet.com": "revue-a-comite",
    "jamanetwork.com": "revue-a-comite",
    "sciencedirect.com": "revue-a-comite",
    "springer.com": "revue-a-comite",
    "link.springer.com": "revue-a-comite",
    "wiley.com": "revue-a-comite",
    "onlinelibrary.wiley.com": "revue-a-comite",
    "ieee.org": "revue-a-comite",
    "ieeexplore.ieee.org": "revue-a-comite",
    "acm.org": "revue-a-comite",
    "dl.acm.org": "revue-a-comite",
    "arxiv.org": "preprint",
    "biorxiv.org": "preprint",
    "medrxiv.org": "preprint",
    "ssrn.com": "preprint",
    "ncbi.nlm.nih.gov": "institutionnel",
    "pubmed.ncbi.nlm.nih.gov": "institutionnel",
    "europa.eu": "institutionnel",
    "oecd.org": "institutionnel",
    "who.int": "institutionnel",
    "equator-network.org": "institutionnel",
    "wikipedia.org": "encyclopedie",
    "medium.com": "presse-blog",
    "substack.com": "presse-blog",
}


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


def palier_domaine(url):
    """Classe le domaine d'une URL par palier de source, table locale sans
    réseau (PALIERS_DOMAINES). Priorité : domaine exact, puis suffixe
    .gouv.fr ou .gov (institutions publiques francaises et anglophones),
    puis suffixe d'un domaine connu (sous-domaines, ex. pubmed.ncbi.nlm.nih.gov
    via ncbi.nlm.nih.gov). Un domaine absent de toutes ces regles est
    "non-classe", jamais range par defaut."""
    import urllib.parse
    hote = urllib.parse.urlparse(url).netloc.lower()
    hote = hote.split("@")[-1].split(":")[0]  # retire user-info et port
    if hote.startswith("www."):
        hote = hote[4:]
    if not hote:
        return "non-classe"
    if hote in PALIERS_DOMAINES:
        return PALIERS_DOMAINES[hote]
    if hote.endswith(".gouv.fr") or hote.endswith(".gov"):
        return "institutionnel"
    for domaine, palier in PALIERS_DOMAINES.items():
        if hote.endswith("." + domaine):
            return palier
    return "non-classe"


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
    paliers = [{"url": u, "palier": palier_domaine(u)} for u in propres]
    return {
        "urls": propres,
        "urls_a_nettoyer": sales,
        "doublons": sorted(set(doublons)),
        "dois": dois,
        "dois_invalides": dois_invalides,
        "paliers": paliers,
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


def similarite_titre(a, b):
    """Similarite de deux titres, difflib.SequenceMatcher, seuil documente 0,70."""
    if not a or not b:
        return 0.0
    norm = lambda s: re.sub(r"\s+", " ", s.strip().lower())
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def _requete_json(url, timeout=INDEX_TIMEOUT):
    """GET generique. Retourne (code_http_ou_None, donnees_ou_None).

    code None = index injoignable (reseau, timeout, erreur serveur 5xx) :
    ne compte pas comme "consulte". Un code 404 est un miss propre d'un
    index joignable : compte comme "consulte" et "non trouve".
    """
    import urllib.request
    import urllib.error
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT_RESEAU,
                                                     "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return 404, None
        return None, None  # 429, 5xx, etc. : degradation par omission
    except Exception:
        return None, None  # timeout, DNS, JSON invalide, etc.


def verifier_crossref_doi(doi, timeout=INDEX_TIMEOUT):
    code, data = _requete_json(f"https://api.crossref.org/works/{doi}", timeout)
    if code is None:
        return {"consulte": False, "trouve": False, "titre": None}
    if code == 404:
        return {"consulte": True, "trouve": False, "titre": None}
    titres = data.get("message", {}).get("title") or []
    return {"consulte": True, "trouve": True, "titre": titres[0] if titres else None}


def verifier_semantic_scholar_doi(doi, timeout=INDEX_TIMEOUT):
    url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=title"
    code, data = _requete_json(url, timeout)
    if code is None:
        return {"consulte": False, "trouve": False, "titre": None}
    if code == 404:
        return {"consulte": True, "trouve": False, "titre": None}
    return {"consulte": True, "trouve": True, "titre": data.get("title")}


def verifier_semantic_scholar_arxiv(identifiant, timeout=INDEX_TIMEOUT):
    url = f"https://api.semanticscholar.org/graph/v1/paper/ARXIV:{identifiant}?fields=title"
    code, data = _requete_json(url, timeout)
    if code is None:
        return {"consulte": False, "trouve": False, "titre": None}
    if code == 404:
        return {"consulte": True, "trouve": False, "titre": None}
    return {"consulte": True, "trouve": True, "titre": data.get("title")}


def verifier_openalex_doi(doi, timeout=INDEX_TIMEOUT, api_key=None):
    """OpenAlex exige une cle API (constate 2026-07-08). Sans cle : non consulte,
    par omission, jamais traite comme un echec de la reference."""
    if not api_key:
        return {"consulte": False, "trouve": False, "titre": None,
                "motif": "cle API OpenAlex absente"}
    url = f"https://api.openalex.org/works/https://doi.org/{doi}?api_key={api_key}"
    code, data = _requete_json(url, timeout)
    if code is None:
        return {"consulte": False, "trouve": False, "titre": None}
    if code == 404:
        return {"consulte": True, "trouve": False, "titre": None}
    return {"consulte": True, "trouve": True, "titre": data.get("title")}


def trianguler_doi(doi, timeout=INDEX_TIMEOUT, api_key_openalex=None):
    """Triangule un DOI aupres de Crossref, OpenAlex et Semantic Scholar.

    Retourne un verdict gradue : verifie, plausible, inverifiable, fabrique.
    Voir references/integrite-sources.md section 3 pour la definition de
    chaque valeur. Un verdict "fabrique" signale un cas a trancher par un
    humain, il ne le tranche pas lui-meme.
    """
    index = {
        "crossref": verifier_crossref_doi(doi, timeout),
        "openalex": verifier_openalex_doi(doi, timeout, api_key_openalex),
        "semantic_scholar": verifier_semantic_scholar_doi(doi, timeout),
    }
    consultes = [nom for nom, r in index.items() if r["consulte"]]
    trouves = [(nom, r["titre"]) for nom, r in index.items() if r["consulte"] and r["trouve"]]

    if len(trouves) >= 2:
        titres = [t for _, t in trouves if t]
        sim_min = 1.0
        for i in range(len(titres)):
            for j in range(i + 1, len(titres)):
                sim_min = min(sim_min, similarite_titre(titres[i], titres[j]))
        if sim_min >= SEUIL_SIMILARITE:
            verdict = "verifie"
            detail = f"titres concordants entre {len(trouves)} index (similarite {sim_min:.2f})"
        else:
            verdict = "inverifiable"
            detail = f"titres discordants entre index (similarite {sim_min:.2f} < {SEUIL_SIMILARITE})"
    elif len(trouves) == 1:
        manques_explicites = [n for n in consultes if n not in [t[0] for t in trouves]]
        if manques_explicites:
            verdict = "plausible"
            detail = f"resolu par {trouves[0][0]} seul, non trouve par {', '.join(manques_explicites)}"
        else:
            verdict = "verifie"
            detail = f"resolu par {trouves[0][0]} (seul index consulte avec succes)"
    else:
        if len(consultes) >= 2:
            verdict = "fabrique"
            detail = f"non trouve independamment par {len(consultes)} index ({', '.join(consultes)})"
        elif len(consultes) == 1:
            verdict = "inverifiable"
            detail = f"non trouve par le seul index consulte ({consultes[0]}), a verifier autrement"
        else:
            verdict = "inverifiable"
            detail = "aucun index consulte avec succes (reseau indisponible, cles absentes)"

    return {
        "doi": doi,
        "verdict": verdict,
        "detail": detail,
        "index": {nom: {"consulte": r["consulte"], "trouve": r["trouve"], "titre": r.get("titre")}
                  for nom, r in index.items()},
    }


def detecter_contamination(texte, reseau=False, timeout=INDEX_TIMEOUT, annee_reference=None):
    """Signale les identifiants arXiv recents. Signal consultatif seul, jamais
    une preuve de fabrication : un preprint recent peut simplement ne pas
    encore etre repris ailleurs."""
    if annee_reference is None:
        annee_reference = datetime.date.today().year
    resultats = []
    vus = set()
    for m in ARXIV_RE.finditer(texte):
        yy, mm, num = m.groups()
        identifiant = f"{yy}{mm}.{num}"
        if identifiant in vus:
            continue
        vus.add(identifiant)
        annee_estimee = 2000 + int(yy)
        if annee_reference - annee_estimee > FENETRE_CONTAMINATION_ANS:
            continue
        entree = {"identifiant": f"arXiv:{identifiant}", "annee_estimee": annee_estimee}
        if reseau:
            r = verifier_semantic_scholar_arxiv(identifiant, timeout)
            if not r["consulte"]:
                entree["signal"] = "non verifie (Semantic Scholar injoignable)"
            elif r["trouve"]:
                entree["signal"] = "preprint recent, retrouve dans un index (signal reduit)"
            else:
                entree["signal"] = "preprint recent absent de l'index consulte : a verifier manuellement"
        else:
            entree["signal"] = "preprint recent, --reseau desactive : a verifier manuellement"
        resultats.append(entree)
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
    if d.get("paliers"):
        out.append("\nPaliers de domaine (indice mécanique, sans réseau) :")
        for p in d["paliers"]:
            out.append(f"  [{p['palier']}] {p['url']}")
    if "liens" in d:
        out.append("\nRésolution réseau :")
        for r in d["liens"]:
            etat = "OK" if r["resout"] else "ECHEC"
            out.append(f"  [{etat}] {r['statut']} {r['url']}")
    if "triangulation" in d:
        out.append("\nTriangulation multi-index (verdict par DOI) :")
        for t in d["triangulation"]:
            out.append(f"  [{t['verdict'].upper()}] {t['doi']} -> {t['detail']}")
    if "contamination" in d and d["contamination"]:
        out.append("\nSignaux de contamination (preprints récents) :")
        for c in d["contamination"]:
            out.append(f"  {c['identifiant']} (année estimée {c['annee_estimee']}) : {c['signal']}")
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description="Vérificateur de sources Scriptorium.")
    p.add_argument("fichier", help="chemin du fichier, ou - pour stdin")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--check-links", action="store_true",
                   help="contrôle réseau de la résolution des URL (désactivé par défaut)")
    p.add_argument("--reseau", action="store_true",
                   help="triangulation Crossref/OpenAlex/Semantic Scholar des DOI, "
                        "et signaux de contamination arXiv (désactivé par défaut)")
    p.add_argument("--openalex-cle",
                   help="clé API OpenAlex (défaut : variable OPENALEX_API_KEY ; "
                        "sans clé, OpenAlex est ignoré, pas compté comme un échec)")
    p.add_argument("--annee-reference", type=int,
                   help="année de référence pour le signal de contamination "
                        "(défaut : année courante)")
    a = p.parse_args(argv)
    try:
        texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    except OSError as e:
        print(f"Erreur de lecture : {e}", file=sys.stderr)
        return 2
    d = analyser(texte)
    if a.check_links:
        d["liens"] = verifier_liens(d["urls"])
    if a.reseau:
        cle = a.openalex_cle or os.environ.get("OPENALEX_API_KEY")
        dois_valides = [x for x in d["dois"] if x not in d["dois_invalides"]]
        d["triangulation"] = [trianguler_doi(doi, api_key_openalex=cle) for doi in dois_valides]
        d["contamination"] = detecter_contamination(texte, reseau=True,
                                                     annee_reference=a.annee_reference)
    if a.format == "json":
        print(json.dumps(d, ensure_ascii=False, indent=2))
    else:
        print(rapport_texte(d))
    # code 1 si doublons, URL sales, DOI invalides, lien mort, ou reference fabriquee
    pb = bool(d["urls_a_nettoyer"] or d["doublons"] or d["dois_invalides"])
    if "liens" in d:
        pb = pb or any(not r["resout"] for r in d["liens"])
    if "triangulation" in d:
        pb = pb or any(t["verdict"] == "fabrique" for t in d["triangulation"])
    return 1 if pb else 0


if __name__ == "__main__":
    sys.exit(main())
