#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Memoire de projet pour Scriptorium : un fichier projet.json conserve le
brief, la charte, le glossaire, la bibliotheque de sources, le profil de
discipline et le plan, plus un journal append-only horodate (etapes,
decisions, artefacts, frontieres, reprises, outrepassements), l'etat de
chaque etape et la version courante de chaque artefact. Recharge au debut
de chaque session, il evite de repartir de zero. Lit sans casser les
projet.json ecrits avant cette extension : les cles manquantes (journal,
etapes, artefacts, objets_numerotes) sont completees en memoire avec des
valeurs vides.

Il porte aussi le contrat de passation vers l'agent redacteur, qui rend son
texte au parent sans ecrire dans le projet : le glossaire des termes fixes et
la liste des objets deja numerotes (figures, tableaux, equations, annexes)
voyagent explicitement, pour qu'une section redigee en deuxieme passe
n'invente ni un synonyme ni un numero deja pris.

Usage :
    python3 project.py init [--out projet.json]
    python3 project.py show [--file projet.json]
    python3 project.py get CLE [--file projet.json]
    python3 project.py set CLE VALEUR [--file projet.json]
        Refuse la cle "journal" (append-only, voir les sous-commandes
        dediees ci-dessous).
    python3 project.py etape NOM ETAT [--motif TEXTE] [--file projet.json]
        ETAT parmi : en_attente, en_cours, termine, saute, bloque. Les
        transitions hors de TRANSITIONS_LEGALES sont refusees (ex. "termine"
        n'est atteignable que depuis "en_cours" ; "saute" exige --motif).
    python3 project.py artefact NOM [--file projet.json]
        Enregistre une nouvelle version (v1, v2, ...) de l'artefact NOM,
        strictement croissante et jamais reutilisee. L'ancienne version
        reste consultable dans le journal.
    python3 project.py frontiere LIBELLE [--decision-attente TEXTE] [--file projet.json]
        Pose une frontiere de reprise. Le hash est un SHA-256 tronque a 12
        caracteres hexadecimaux de la serialisation JSON canonique (cles
        triees, separateurs compacts, UTF-8) de toutes les entrees de
        journal qui precedent la frontiere. Canonicalisation maison
        inspiree de RFC 8785 (JSON Canonicalization Scheme,
        datatracker.ietf.org/doc/html/rfc8785), PAS une implementation
        conforme : pas de normalisation Unicode NFC, pas de formatage des
        nombres flottants selon l'algorithme ECMAScript Number::toString.
        Suffisant ici car le journal ne contient que des chaines, entiers,
        listes et dictionnaires simples.
    python3 project.py reprendre HASH [--file projet.json]
        Retrouve la frontiere portant ce hash, refuse une deuxieme reprise
        de la meme frontiere, affiche un accuse (etapes, artefacts,
        decision en attente le cas echeant, a reposer a l'utilisateur) et
        journalise la reprise.
    python3 project.py decision LIBELLE [--file projet.json]
        Journalise une decision cle, pour le bilan de fin de mission.
    python3 project.py objet TYPE NUMERO LIBELLE [--file projet.json]
        Fixe le numero d'un objet legende (figure, tableau, equation,
        annexe) pour toute la mission. Reenregistrer le meme numero avec
        le meme libelle ne fait rien ; avec un libelle different, refus.
    python3 project.py passation [--format text|json] [--file projet.json]
        Emet le contrat de passation vers l'agent redacteur : glossaire,
        objets deja numerotes, prochain numero libre par type. Se colle
        dans le prompt du sous-agent, qui n'a que Read, Glob et Grep et ne
        peut donc pas lire le projet lui-meme.
    python3 project.py outrepasser LIBELLE [--justification TEXTE] [--file projet.json]
        Journalise un outrepassement au cran de friction courant (voir
        prochain_cran). tools/check.py appelle en pratique la fonction
        journaliser_outrepassement() directement plutot que cette
        sous-commande, qui reste utile pour un outrepassement hors check.py.
    python3 project.py status [--file projet.json]
        Tableau de bord texte : etapes avec symbole d'etat, artefacts et
        version courante, objets numerotes, decisions en attente,
        frontieres et hashes, compte d'outrepassements, configuration(s)
        de reproductibilite.
    python3 project.py reproductibilite --plugin-version X --modele NOM [--file projet.json]
        Documente une configuration de generation (version du plugin,
        modele nomme, date automatique) dans le journal (type
        reproductibilite). Ne garantit PAS le rejeu a l'identique : chaque
        entree porte une declaration de stochasticite fixe (voir
        STOCHASTICITE_DECLAREE), rappelee aussi a l'ecran. Affichee par
        --status.

Module importable : charger(path) ; sauver(path, d) ; changer_etat(d, nom,
etat, motif) ; enregistrer_artefact(d, nom) ; poser_frontiere(d, libelle,
decision_attente) ; reprendre(d, hash_) ; journaliser_outrepassement(path,
libelle, cran, justification) ; prochain_cran(d) ; compter_outrepassements(d) ;
valider_justification(cran, justification) ; enregistrer_reproductibilite(d,
plugin_version, modele) ; statut_texte(d) ; enregistrer_objet(d, type_objet,
numero, libelle) ; prochain_numero(d, type_objet) ; passation_redacteur(d) ;
passation_texte(d).
"""
import argparse
import copy
import datetime
import hashlib
import json
import os
import sys

SQUELETTE = {
    "titre": "",
    "genre": "",
    "problematique": "",
    "brief": "",
    "charte": "charte-graphique.json",
    "profil": "profil.json",
    "plan": "plan.json",
    "glossaire": {},
    "objets_numerotes": [],
    "sources": [],
    "notes": "",
}

ETATS_VALIDES = ("en_attente", "en_cours", "termine", "saute", "bloque")

# Objets legendes dont le numero se fixe une fois pour toute la mission.
TYPES_OBJET = ("figure", "tableau", "equation", "annexe")

# Transitions legales : cle = etat de depart, valeur = ensemble des etats
# d'arrivee autorises (l'etat de depart s'y trouve toujours, une transition
# vers soi-meme est un no-op accepte). "termine" n'est atteignable que
# depuis "en_cours" : pas de raccourci direct depuis en_attente, saute ou
# bloque. "termine" est terminal (aucune sortie).
TRANSITIONS_LEGALES = {
    "en_attente": {"en_attente", "en_cours", "saute", "bloque"},
    "en_cours": {"en_cours", "termine", "saute", "bloque"},
    "bloque": {"bloque", "en_cours", "saute"},
    "saute": {"saute", "en_cours"},
    "termine": {"termine"},
}

SYMBOLES_ETAT = {
    "en_attente": "[ ]",
    "en_cours": "[~]",
    "termine": "[x]",
    "saute": "[-]",
    "bloque": "[!]",
}

STOCHASTICITE_DECLAREE = (
    "Cette entree documente la configuration de generation au moment ou "
    "elle a ete enregistree (version du plugin, modele nomme, date). Elle "
    "ne garantit pas qu'un rejeu ulterieur, meme avec la meme version et "
    "le meme modele nomme, produise un texte identique : un modele de "
    "langage reste stochastique par nature, sauf configuration "
    "deterministe explicite non couverte ici."
)


def _squelette_v2():
    # copie profonde : SQUELETTE porte des conteneurs mutables (glossaire,
    # objets_numerotes, sources) qu'une copie de surface ferait partager
    # entre deux projets charges dans le meme processus.
    d = copy.deepcopy(SQUELETTE)
    d["journal"] = []
    d["etapes"] = {}
    d["artefacts"] = {}
    return d


def charger(path):
    if not os.path.exists(path):
        return _squelette_v2()
    d = json.load(open(path, encoding="utf-8"))
    # Upgrade en memoire d'un projet.json ecrit avant le journal : ajoute
    # les cles manquantes sans rien ecraser de l'existant.
    if "journal" not in d:
        d["journal"] = []
    if "etapes" not in d:
        d["etapes"] = {}
    if "artefacts" not in d:
        d["artefacts"] = {}
    # Meme regle pour la liste des objets numerotes, arrivee apres : un
    # projet.json ecrit sans elle se lit sans erreur, la cle est completee
    # a vide en memoire et le fichier reste inchange sur le disque.
    if "objets_numerotes" not in d:
        d["objets_numerotes"] = []
    if "glossaire" not in d:
        d["glossaire"] = {}
    return d


def sauver(path, d):
    json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def _horodatage():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _canon(obj):
    """Serialisation JSON canonique maison : cles triees, separateurs
    compacts, UTF-8. Inspiree de RFC 8785 mais non conforme (voir docstring
    du module)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _hash_continuite(entrees_precedentes):
    return hashlib.sha256(_canon(entrees_precedentes)).hexdigest()[:12]


def _ajouter_journal(d, entree):
    """Ajoute une entree au journal, ne la reecrit jamais. Le journal est
    append-only par construction : aucune fonction de ce module n'indexe
    dans d['journal'] pour ecrire, seul .append() est utilise. 'seq' fixe
    la position au moment de l'ajout (longueur courante), ce qui rend une
    reecriture d'entree existante structurellement impossible plutot que
    seulement proscrite par convention."""
    d.setdefault("journal", [])
    entree = dict(entree)
    entree["seq"] = len(d["journal"])
    d["journal"].append(entree)
    return entree


def changer_etat(d, nom, nouveau, motif=None):
    if nouveau not in ETATS_VALIDES:
        raise ValueError(f"etat inconnu : '{nouveau}' (valides : {', '.join(ETATS_VALIDES)}).")
    etapes = d.setdefault("etapes", {})
    ancien = etapes.get(nom, {}).get("etat", "en_attente")
    motif_propre = (motif or "").strip()
    if nouveau == "saute" and not motif_propre:
        raise ValueError("La transition vers 'saute' exige un motif (--motif TEXTE).")
    legales = TRANSITIONS_LEGALES.get(ancien, {ancien})
    if nouveau not in legales:
        raise ValueError(
            f"Transition illegale : '{nom}' est '{ancien}', passage a '{nouveau}' refuse "
            f"(autorise depuis '{ancien}' : {', '.join(sorted(legales))})."
        )
    info = {"etat": nouveau, "maj": _horodatage()}
    if motif_propre:
        info["motif"] = motif_propre
    etapes[nom] = info
    entree = {"type": "etape", "horodatage": _horodatage(), "nom": nom, "etat_avant": ancien, "etat_apres": nouveau}
    if motif_propre:
        entree["motif"] = motif_propre
    _ajouter_journal(d, entree)
    return ancien, nouveau


def enregistrer_artefact(d, nom):
    artefacts = d.setdefault("artefacts", {})
    courante = artefacts.get(nom)
    if courante is None:
        nouvelle = "v1"
    else:
        nouvelle = f"v{int(courante['version'][1:]) + 1}"
    artefacts[nom] = {"version": nouvelle, "maj": _horodatage()}
    entree = {"type": "artefact", "horodatage": _horodatage(), "nom": nom, "version": nouvelle}
    _ajouter_journal(d, entree)
    return nouvelle


def enregistrer_objet(d, type_objet, numero, libelle):
    """Fixe le numero d'un objet legende pour toute la mission.

    Un document long se redige section par section : sans numero fixe, la
    deuxieme passe rouvre la numerotation a 1 ou saute un rang. Reenregistrer
    le meme couple (type, numero) avec le meme libelle est un no-op accepte,
    avec un libelle different c'est un refus, parce que deux figures 3 dans un
    meme document ne se rattrapent plus a la mise en forme.
    """
    if type_objet not in TYPES_OBJET:
        raise ValueError(
            f"type d'objet inconnu : '{type_objet}' (valides : {', '.join(TYPES_OBJET)}).")
    try:
        numero = int(numero)
    except (TypeError, ValueError):
        raise ValueError(f"numero non entier : {numero!r}.")
    if numero < 1:
        raise ValueError(f"numero hors bornes : {numero} (le premier rang est 1).")
    libelle_propre = (libelle or "").strip()
    if not libelle_propre:
        raise ValueError("un objet numerote porte un libelle non vide.")
    objets = d.setdefault("objets_numerotes", [])
    for o in objets:
        if o.get("type") == type_objet and o.get("numero") == numero:
            if o.get("libelle") == libelle_propre:
                return o
            raise ValueError(
                f"{type_objet} {numero} est deja pris par '{o.get('libelle')}' : "
                f"choisir un autre numero plutot que reaffecter celui-ci.")
    objet = {"type": type_objet, "numero": numero, "libelle": libelle_propre,
             "maj": _horodatage()}
    objets.append(objet)
    _ajouter_journal(d, {"type": "objet", "horodatage": _horodatage(),
                         "objet": type_objet, "numero": numero,
                         "libelle": libelle_propre})
    return objet


def prochain_numero(d, type_objet):
    """Premier numero libre pour un type d'objet : le maximum pose, plus un."""
    poses = [o["numero"] for o in d.get("objets_numerotes") or []
             if o.get("type") == type_objet and isinstance(o.get("numero"), int)]
    return max(poses) + 1 if poses else 1


def passation_redacteur(d):
    """Contrat de passation vers l'agent redacteur.

    L'agent redacteur n'a que Read, Glob et Grep et rend son texte au parent :
    il ne lit pas projet.json et n'y ecrit rien. Ce que le parent ne lui passe
    pas explicitement n'existe pas pour lui, donc le glossaire des termes
    fixes et les objets deja numerotes voyagent ici, avec le prochain numero
    libre par type pour que la section suivante ne rouvre pas la serie.
    """
    return {
        "genre": d.get("genre", ""),
        "problematique": d.get("problematique", ""),
        "glossaire": dict(d.get("glossaire") or {}),
        "objets_numerotes": [dict(o) for o in (d.get("objets_numerotes") or [])],
        "prochains_numeros": {t: prochain_numero(d, t) for t in TYPES_OBJET},
    }


def passation_texte(p):
    """Passation en texte, a coller dans le prompt du sous-agent redacteur."""
    lignes = ["=== Passation vers le redacteur ==="]
    if p.get("genre"):
        lignes.append(f"Genre : {p['genre']}")
    if p.get("problematique"):
        lignes.append(f"Problematique : {p['problematique']}")
    lignes.append("")
    lignes.append("Glossaire (termes fixes, a employer tels quels, sans synonyme) :")
    if not p["glossaire"]:
        lignes.append("  (aucun terme fixe)")
    else:
        for terme in sorted(p["glossaire"]):
            lignes.append(f"  {terme} : {p['glossaire'][terme]}")
    lignes.append("")
    lignes.append("Objets deja numerotes (ne pas renumeroter, ne pas reutiliser) :")
    if not p["objets_numerotes"]:
        lignes.append("  (aucun objet numerote)")
    else:
        for o in sorted(p["objets_numerotes"],
                        key=lambda x: (x.get("type", ""), x.get("numero", 0))):
            lignes.append(f"  {o.get('type')} {o.get('numero')} : {o.get('libelle')}")
    lignes.append("")
    lignes.append("Prochain numero libre : "
                  + ", ".join(f"{t} {p['prochains_numeros'][t]}"
                              for t in sorted(p["prochains_numeros"])))
    return "\n".join(lignes)


def enregistrer_reproductibilite(d, plugin_version, modele):
    """Documente une configuration de generation dans le journal (type
    reproductibilite) : version du plugin, modele nomme, date automatique,
    plus la declaration de stochasticite fixe (STOCHASTICITE_DECLAREE)
    recopiee dans l'entree elle-meme pour qu'elle reste lisible meme hors
    contexte. N'ecrase jamais une entree precedente (append-only, comme
    tout le reste du journal) : documenter un changement de modele en
    cours de mission ajoute une nouvelle entree, elle ne remplace pas
    l'ancienne."""
    entree = {
        "type": "reproductibilite",
        "horodatage": _horodatage(),
        "plugin_version": plugin_version,
        "modele": modele,
        "stochasticite_declaree": STOCHASTICITE_DECLAREE,
    }
    return _ajouter_journal(d, entree)


def poser_frontiere(d, libelle, decision_attente=None):
    hash_ = _hash_continuite(d.get("journal", []))
    entree = {"type": "frontiere", "horodatage": _horodatage(), "libelle": libelle, "hash": hash_}
    decision_propre = (decision_attente or "").strip()
    if decision_propre:
        entree["decision_attente"] = decision_propre
    return _ajouter_journal(d, entree)


def trouver_frontiere(d, hash_):
    for e in d.get("journal", []):
        if e.get("type") == "frontiere" and e.get("hash") == hash_:
            return e
    return None


def deja_reprise(d, hash_):
    for e in d.get("journal", []):
        if e.get("type") == "reprise" and e.get("hash_reference") == hash_:
            return e
    return None


def reprendre(d, hash_):
    fr = trouver_frontiere(d, hash_)
    if fr is None:
        raise ValueError(f"Aucune frontiere avec le hash '{hash_}'.")
    deja = deja_reprise(d, hash_)
    if deja is not None:
        raise ValueError(
            f"Cette frontiere a deja ete reprise le {deja['horodatage']} (double reprise refusee)."
        )
    accuse = {
        "libelle_frontiere": fr["libelle"],
        "horodatage_frontiere": fr["horodatage"],
        "etapes": dict(d.get("etapes", {})),
        "artefacts": dict(d.get("artefacts", {})),
        "decision_attente": fr.get("decision_attente"),
    }
    entree = {"type": "reprise", "horodatage": _horodatage(), "hash_reference": hash_}
    _ajouter_journal(d, entree)
    return accuse


def compter_outrepassements(d):
    return sum(1 for e in d.get("journal", []) if e.get("type") == "outrepassement")


def prochain_cran(d):
    return compter_outrepassements(d) + 1


def valider_justification(cran, justification):
    """Regle de friction a 3 crans. Cran 1 : aucune justification requise
    (avertissement simple). Cran 2 : justification non vide requise. Cran 3
    et au-dela : justification d'au moins 100 caracteres requise. Leve
    ValueError si la justification manque ou est trop courte pour le cran."""
    j = (justification or "").strip()
    if cran <= 1:
        return
    if cran == 2:
        if not j:
            raise ValueError("cran 2 : --justification \"texte\" est requise.")
        return
    if len(j) < 100:
        raise ValueError(f"cran {cran} : justification d'au moins 100 caracteres requise ({len(j)} fournis).")


def journaliser_outrepassement(path, libelle, cran, justification=None):
    """Charge PATH, valide la justification requise pour CRAN, journalise
    l'outrepassement, sauvegarde. Fonction appelee par tools/check.py quand
    un projet.json existe au chemin --projet."""
    valider_justification(cran, justification)
    d = charger(path)
    entree = {"type": "outrepassement", "horodatage": _horodatage(), "libelle": libelle, "cran": cran}
    if justification:
        entree["justification"] = justification
    _ajouter_journal(d, entree)
    sauver(path, d)
    return entree


def statut_texte(d):
    lignes = []
    titre = d.get("titre") or "(sans titre)"
    lignes.append(f"=== Tableau de bord : {titre} ===")
    if d.get("genre"):
        lignes.append(f"Genre : {d['genre']}")
    lignes.append("")
    lignes.append("Etapes :")
    etapes = d.get("etapes", {})
    if not etapes:
        lignes.append("  (aucune etape suivie)")
    else:
        for nom in sorted(etapes):
            info = etapes[nom]
            sym = SYMBOLES_ETAT.get(info.get("etat"), "[?]")
            motif = f" (motif : {info['motif']})" if info.get("motif") else ""
            lignes.append(f"  {sym} {nom:<20} {info.get('etat')}{motif}")
    lignes.append("")
    lignes.append("Artefacts :")
    artefacts = d.get("artefacts", {})
    if not artefacts:
        lignes.append("  (aucun artefact enregistre)")
    else:
        for nom in sorted(artefacts):
            lignes.append(f"  {nom:<20} {artefacts[nom]['version']}")
    lignes.append("")
    lignes.append("Objets numerotes :")
    objets = d.get("objets_numerotes") or []
    if not objets:
        lignes.append("  (aucun)")
    else:
        for o in sorted(objets, key=lambda x: (x.get("type", ""), x.get("numero", 0))):
            lignes.append(f"  {o.get('type')} {o.get('numero'):<3} {o.get('libelle')}")
    lignes.append("")
    repro = [e for e in d.get("journal", []) if e.get("type") == "reproductibilite"]
    lignes.append("Reproductibilite :")
    if not repro:
        lignes.append("  (aucune configuration de generation enregistree)")
    else:
        for e in repro:
            lignes.append(
                f"  plugin {e['plugin_version']:<10} modele {e['modele']:<15} "
                f"{e['horodatage']} (rejeu non garanti)"
            )
    lignes.append("")
    journal = d.get("journal", [])
    frontieres = [e for e in journal if e.get("type") == "frontiere"]
    reprises = {e["hash_reference"] for e in journal if e.get("type") == "reprise"}
    attente = [f for f in frontieres if f.get("decision_attente") and f["hash"] not in reprises]
    lignes.append("Decisions en attente :")
    if not attente:
        lignes.append("  (aucune)")
    else:
        for f in attente:
            lignes.append(f"  [{f['hash']}] {f['decision_attente']}")
    lignes.append("")
    lignes.append("Frontieres :")
    if not frontieres:
        lignes.append("  (aucune)")
    else:
        for f in frontieres:
            statut = "reprise" if f["hash"] in reprises else "non reprise"
            lignes.append(f"  [{f['hash']}] {f['libelle']} ({f['horodatage']}) - {statut}")
    lignes.append("")
    n = compter_outrepassements(d)
    suffixe = f" (cran courant : {min(n, 3)})" if n else ""
    lignes.append(f"Outrepassements : {n}{suffixe}")
    return "\n".join(lignes)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Memoire de projet.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("init")
    i.add_argument("--out", default="projet.json")

    sh = sub.add_parser("show")
    sh.add_argument("--file", default="projet.json")

    g = sub.add_parser("get")
    g.add_argument("cle")
    g.add_argument("--file", default="projet.json")

    s = sub.add_parser("set")
    s.add_argument("cle")
    s.add_argument("valeur")
    s.add_argument("--file", default="projet.json")

    et = sub.add_parser("etape")
    et.add_argument("nom")
    et.add_argument("etat", choices=list(ETATS_VALIDES))
    et.add_argument("--motif", default="")
    et.add_argument("--file", default="projet.json")

    ar = sub.add_parser("artefact")
    ar.add_argument("nom")
    ar.add_argument("--file", default="projet.json")

    fr = sub.add_parser("frontiere")
    fr.add_argument("libelle")
    fr.add_argument("--decision-attente", default="", dest="decision_attente")
    fr.add_argument("--file", default="projet.json")

    rp = sub.add_parser("reprendre")
    rp.add_argument("hash")
    rp.add_argument("--file", default="projet.json")

    dc = sub.add_parser("decision")
    dc.add_argument("libelle")
    dc.add_argument("--file", default="projet.json")

    ob = sub.add_parser("objet")
    ob.add_argument("type_objet", choices=list(TYPES_OBJET))
    ob.add_argument("numero", type=int)
    ob.add_argument("libelle")
    ob.add_argument("--file", default="projet.json")

    ps = sub.add_parser("passation")
    ps.add_argument("--format", choices=("text", "json"), default="text")
    ps.add_argument("--file", default="projet.json")

    op = sub.add_parser("outrepasser")
    op.add_argument("libelle")
    op.add_argument("--justification", default="")
    op.add_argument("--file", default="projet.json")

    rc = sub.add_parser("reproductibilite")
    rc.add_argument("--plugin-version", required=True, dest="plugin_version")
    rc.add_argument("--modele", required=True)
    rc.add_argument("--file", default="projet.json")

    st = sub.add_parser("status")
    st.add_argument("--file", default="projet.json")

    a = ap.parse_args(argv)

    if a.cmd == "init":
        if os.path.exists(a.out):
            print(f"{a.out} existe deja, inchange.")
            return 0
        sauver(a.out, _squelette_v2())
        print(f"Memoire de projet creee : {a.out}")
        return 0

    if a.cmd == "show":
        print(json.dumps(charger(a.file), ensure_ascii=False, indent=2))
        return 0

    if a.cmd == "get":
        print(json.dumps(charger(a.file).get(a.cle, None), ensure_ascii=False))
        return 0

    if a.cmd == "set":
        if a.cle == "journal":
            print("Refuse : 'journal' est append-only. Utiliser etape/artefact/frontiere/reprendre/decision/outrepasser.")
            return 1
        d = charger(a.file)
        try:
            val = json.loads(a.valeur)
        except json.JSONDecodeError:
            val = a.valeur
        d[a.cle] = val
        sauver(a.file, d)
        print(f"{a.cle} mis a jour dans {a.file}.")
        return 0

    if a.cmd == "etape":
        d = charger(a.file)
        try:
            ancien, nouveau = changer_etat(d, a.nom, a.etat, a.motif)
        except ValueError as e:
            print(f"Erreur : {e}")
            return 1
        sauver(a.file, d)
        print(f"Etape '{a.nom}' : {ancien} -> {nouveau}.")
        return 0

    if a.cmd == "artefact":
        d = charger(a.file)
        version = enregistrer_artefact(d, a.nom)
        sauver(a.file, d)
        print(f"Artefact '{a.nom}' enregistre : {version}.")
        return 0

    if a.cmd == "frontiere":
        d = charger(a.file)
        entree = poser_frontiere(d, a.libelle, a.decision_attente or None)
        sauver(a.file, d)
        print(f"Frontiere posee : {entree['hash']} - {a.libelle}")
        if entree.get("decision_attente"):
            print(f"Decision en attente rattachee : {entree['decision_attente']}")
        return 0

    if a.cmd == "reprendre":
        d = charger(a.file)
        try:
            accuse = reprendre(d, a.hash)
        except ValueError as e:
            print(f"Erreur : {e}")
            return 1
        sauver(a.file, d)
        print(f"Reprise de la frontiere '{accuse['libelle_frontiere']}' ({accuse['horodatage_frontiere']}).")
        print(f"Etapes : {json.dumps(accuse['etapes'], ensure_ascii=False)}")
        print(f"Artefacts : {json.dumps(accuse['artefacts'], ensure_ascii=False)}")
        if accuse["decision_attente"]:
            print(f"Decision en attente, a reposer a l'utilisateur : {accuse['decision_attente']}")
        else:
            print("Aucune decision en attente.")
        return 0

    if a.cmd == "decision":
        d = charger(a.file)
        entree = {"type": "decision", "horodatage": _horodatage(), "libelle": a.libelle}
        _ajouter_journal(d, entree)
        sauver(a.file, d)
        print(f"Decision journalisee : {a.libelle}")
        return 0

    if a.cmd == "objet":
        d = charger(a.file)
        try:
            objet = enregistrer_objet(d, a.type_objet, a.numero, a.libelle)
        except ValueError as e:
            print(f"Erreur : {e}")
            return 1
        sauver(a.file, d)
        print(f"{objet['type']} {objet['numero']} : {objet['libelle']}")
        return 0

    if a.cmd == "passation":
        p = passation_redacteur(charger(a.file))
        print(json.dumps(p, ensure_ascii=False, indent=2)
              if a.format == "json" else passation_texte(p))
        return 0

    if a.cmd == "outrepasser":
        d = charger(a.file)
        cran = prochain_cran(d)
        try:
            journaliser_outrepassement(a.file, a.libelle, cran, a.justification or None)
        except ValueError as e:
            print(f"Erreur : {e}")
            return 1
        print(f"Outrepassement journalise (cran {cran}) : {a.libelle}")
        return 0

    if a.cmd == "reproductibilite":
        d = charger(a.file)
        entree = enregistrer_reproductibilite(d, a.plugin_version, a.modele)
        sauver(a.file, d)
        print(f"Reproductibilite enregistree : plugin {entree['plugin_version']}, "
              f"modele {entree['modele']}, {entree['horodatage']}.")
        print(f"Rappel : {STOCHASTICITE_DECLAREE}")
        return 0

    if a.cmd == "status":
        d = charger(a.file)
        print(statut_texte(d))
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
