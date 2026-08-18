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
plugin_version, modele) ; statut_texte(d, langue_affichage=None) ;
enregistrer_objet(d, type_objet, numero, libelle) ; prochain_numero(d,
type_objet) ; passation_redacteur(d) ; passation_texte(d,
langue_affichage=None).

LANGUE : le journal de mission ECRIT dans projet.json ne depend d'aucune
langue d'affichage. Les etats d'etape, les types d'objet, les libelles poses
par l'utilisateur et la declaration de stochasticite y restent les chaines
francaises, quelle que soit la langue demandee a la commande qui les a
ecrits. Sans cela un projet commence en francais et repris en anglais se
contredirait a la relecture, et le hash de continuite d'une frontiere, qui
porte sur la serialisation du journal, changerait de valeur sans qu'aucune
decision n'ait bouge. Seuls le tableau de bord, la passation et les messages
de la ligne de commande suivent --langue-affichage (defaut fr : un projet
n'est pas un manuscrit, il ne porte pas de pragme de langue).
"""
import argparse
import copy
import datetime
import hashlib
import importlib.util
import json
import os
import sys

_LIB = None


def _lib():
    """Charge libelles.py par son chemin, une seule fois : le module se lit
    par chemin, aucun sys.path n'est garanti."""
    global _LIB
    if _LIB is None:
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "libelles.py")
        spec = importlib.util.spec_from_file_location("scriptorium_libelles",
                                                      chemin)
        _LIB = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_LIB)
    return _LIB


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


def changer_etat(d, nom, nouveau, motif=None, langue_affichage=None):
    """Change l'etat d'une etape et le journalise.

    Les etats nommes dans les messages d'erreur restent les chaines tapees
    sur la ligne de commande : c'est ce que l'utilisateur doit corriger, le
    traduire l'egarerait. Seule la phrase autour suit la langue demandee."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    if nouveau not in ETATS_VALIDES:
        raise ValueError(lib.t("project.e.etat_inconnu", la, etat=nouveau,
                               valides=", ".join(ETATS_VALIDES)))
    etapes = d.setdefault("etapes", {})
    ancien = etapes.get(nom, {}).get("etat", "en_attente")
    motif_propre = (motif or "").strip()
    if nouveau == "saute" and not motif_propre:
        raise ValueError(lib.t("project.e.motif_requis", la))
    legales = TRANSITIONS_LEGALES.get(ancien, {ancien})
    if nouveau not in legales:
        raise ValueError(lib.t("project.e.transition", la, nom=nom,
                               ancien=ancien, nouveau=nouveau,
                               legales=", ".join(sorted(legales))))
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


def enregistrer_objet(d, type_objet, numero, libelle, langue_affichage=None):
    """Fixe le numero d'un objet legende pour toute la mission.

    Un document long se redige section par section : sans numero fixe, la
    deuxieme passe rouvre la numerotation a 1 ou saute un rang. Reenregistrer
    le meme couple (type, numero) avec le meme libelle est un no-op accepte,
    avec un libelle different c'est un refus, parce que deux figures 3 dans un
    meme document ne se rattrapent plus a la mise en forme.

    Le type d'objet ENREGISTRE reste la chaine francaise de TYPES_OBJET :
    c'est une donnee du projet, relue plus tard par la passation. Seuls les
    messages d'erreur suivent langue_affichage.
    """
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    if type_objet not in TYPES_OBJET:
        raise ValueError(lib.t("project.e.type_objet", la, objet=type_objet,
                               valides=", ".join(TYPES_OBJET)))
    try:
        numero = int(numero)
    except (TypeError, ValueError):
        raise ValueError(lib.t("project.e.numero_non_entier", la,
                               numero=repr(numero)))
    if numero < 1:
        raise ValueError(lib.t("project.e.numero_borne", la, numero=numero))
    libelle_propre = (libelle or "").strip()
    if not libelle_propre:
        raise ValueError(lib.t("project.e.libelle_vide", la))
    objets = d.setdefault("objets_numerotes", [])
    for o in objets:
        if o.get("type") == type_objet and o.get("numero") == numero:
            if o.get("libelle") == libelle_propre:
                return o
            raise ValueError(lib.t(
                "project.e.numero_pris", la,
                objet=lib.valeur("project.type_objet", type_objet, la),
                numero=numero, libelle=o.get("libelle")))
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


def passation_texte(p, langue_affichage=None):
    """Passation en texte, a coller dans le prompt du sous-agent redacteur.

    Le glossaire et les libelles d'objet viennent du projet : ils sont repris
    tels quels, jamais traduits, sinon le redacteur emploierait un terme qui
    ne figure pas dans le glossaire fixe. Seule la charpente du texte suit la
    langue demandee."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    lignes = [lib.t("project.pass.titre", la)]
    if p.get("genre"):
        lignes.append(lib.t("project.genre", la, genre=p["genre"]))
    if p.get("problematique"):
        lignes.append(lib.t("project.pass.problematique", la,
                            problematique=p["problematique"]))
    lignes.append("")
    lignes.append(lib.t("project.pass.glossaire", la))
    if not p["glossaire"]:
        lignes.append("  " + lib.t("project.pass.aucun_terme", la))
    else:
        for terme in sorted(p["glossaire"]):
            lignes.append("  " + lib.t("project.pass.terme", la, terme=terme,
                                       definition=p["glossaire"][terme]))
    lignes.append("")
    lignes.append(lib.t("project.pass.objets", la))
    if not p["objets_numerotes"]:
        lignes.append("  " + lib.t("project.pass.aucun_objet", la))
    else:
        for o in sorted(p["objets_numerotes"],
                        key=lambda x: (x.get("type", ""), x.get("numero", 0))):
            lignes.append("  " + lib.t(
                "project.pass.objet", la,
                objet=lib.valeur("project.type_objet", o.get("type"), la),
                numero=o.get("numero"), libelle=o.get("libelle")))
    lignes.append("")
    lignes.append(lib.t(
        "project.pass.prochain", la,
        liste=", ".join(
            "%s %s" % (lib.valeur("project.type_objet", t, la),
                       p["prochains_numeros"][t])
            for t in sorted(p["prochains_numeros"]))))
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


def reprendre(d, hash_, langue_affichage=None):
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    fr = trouver_frontiere(d, hash_)
    if fr is None:
        raise ValueError(lib.t("project.e.frontiere_absente", la,
                               hash=hash_))
    deja = deja_reprise(d, hash_)
    if deja is not None:
        raise ValueError(lib.t("project.e.double_reprise", la,
                               horodatage=deja["horodatage"]))
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


def valider_justification(cran, justification, langue_affichage=None):
    """Regle de friction a 3 crans. Cran 1 : aucune justification requise
    (avertissement simple). Cran 2 : justification non vide requise. Cran 3
    et au-dela : justification d'au moins 100 caracteres requise. Leve
    ValueError si la justification manque ou est trop courte pour le cran."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    j = (justification or "").strip()
    if cran <= 1:
        return
    if cran == 2:
        if not j:
            raise ValueError(lib.t("project.e.cran2", la))
        return
    if len(j) < 100:
        raise ValueError(lib.t("project.e.cran3", la, cran=cran, n=len(j)))


def journaliser_outrepassement(path, libelle, cran, justification=None,
                               langue_affichage=None):
    """Charge PATH, valide la justification requise pour CRAN, journalise
    l'outrepassement, sauvegarde. Fonction appelee par tools/check.py quand
    un projet.json existe au chemin --projet."""
    valider_justification(cran, justification, langue_affichage)
    d = charger(path)
    entree = {"type": "outrepassement", "horodatage": _horodatage(), "libelle": libelle, "cran": cran}
    if justification:
        entree["justification"] = justification
    _ajouter_journal(d, entree)
    sauver(path, d)
    return entree


def statut_texte(d, langue_affichage=None):
    """Tableau de bord lisible.

    Les etats d'etape, les types d'objet et le statut d'une frontiere sont
    des valeurs machine : le projet les porte en francais, ils sont traduits
    ici a l'affichage seulement. Les titres, motifs, libelles de frontiere et
    noms d'artefact viennent de l'utilisateur, ils sont repris tels quels."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    lignes = []
    titre = d.get("titre") or lib.t("project.sans_titre", la)
    lignes.append(lib.t("project.tableau", la, titre=titre))
    if d.get("genre"):
        lignes.append(lib.t("project.genre", la, genre=d["genre"]))
    lignes.append("")
    lignes.append(lib.t("project.etapes", la))
    etapes = d.get("etapes", {})
    if not etapes:
        lignes.append("  " + lib.t("project.aucune_etape", la))
    else:
        for nom in sorted(etapes):
            info = etapes[nom]
            sym = SYMBOLES_ETAT.get(info.get("etat"), "[?]")
            motif = (lib.t("project.etape_motif", la, motif=info["motif"])
                     if info.get("motif") else "")
            lignes.append("  " + lib.t(
                "project.etape_ligne", la, sym=sym, nom=nom,
                etat=lib.valeur("project.etat", info.get("etat"), la),
                motif=motif))
    lignes.append("")
    lignes.append(lib.t("project.artefacts", la))
    artefacts = d.get("artefacts", {})
    if not artefacts:
        lignes.append("  " + lib.t("project.aucun_artefact", la))
    else:
        for nom in sorted(artefacts):
            lignes.append("  " + lib.t("project.artefact_ligne", la, nom=nom,
                                       version=artefacts[nom]["version"]))
    lignes.append("")
    lignes.append(lib.t("project.objets", la))
    objets = d.get("objets_numerotes") or []
    if not objets:
        lignes.append("  " + lib.t("project.aucun", la))
    else:
        for o in sorted(objets, key=lambda x: (x.get("type", ""), x.get("numero", 0))):
            lignes.append("  " + lib.t(
                "project.objet_ligne", la,
                objet=lib.valeur("project.type_objet", o.get("type"), la),
                numero=o.get("numero"), libelle=o.get("libelle")))
    lignes.append("")
    repro = [e for e in d.get("journal", []) if e.get("type") == "reproductibilite"]
    lignes.append(lib.t("project.repro", la))
    if not repro:
        lignes.append("  " + lib.t("project.aucune_repro", la))
    else:
        for e in repro:
            lignes.append("  " + lib.t(
                "project.repro_ligne", la, version=e["plugin_version"],
                modele=e["modele"], horodatage=e["horodatage"]))
    lignes.append("")
    journal = d.get("journal", [])
    frontieres = [e for e in journal if e.get("type") == "frontiere"]
    reprises = {e["hash_reference"] for e in journal if e.get("type") == "reprise"}
    attente = [f for f in frontieres if f.get("decision_attente") and f["hash"] not in reprises]
    lignes.append(lib.t("project.decisions_attente", la))
    if not attente:
        lignes.append("  " + lib.t("project.aucun", la))
    else:
        for f in attente:
            lignes.append("  " + lib.t("project.decision_ligne", la,
                                       hash=f["hash"],
                                       decision=f["decision_attente"]))
    lignes.append("")
    lignes.append(lib.t("project.frontieres", la))
    if not frontieres:
        lignes.append("  " + lib.t("project.aucun", la))
    else:
        for f in frontieres:
            statut = "reprise" if f["hash"] in reprises else "non reprise"
            lignes.append("  " + lib.t(
                "project.frontiere_ligne", la, hash=f["hash"],
                libelle=f["libelle"], horodatage=f["horodatage"],
                statut=lib.valeur("project.statut_frontiere", statut, la)))
    lignes.append("")
    n = compter_outrepassements(d)
    suffixe = (lib.t("project.cran_courant", la, cran=min(n, 3))
               if n else "")
    lignes.append(lib.t("project.outrepassements", la, n=n, suffixe=suffixe))
    return "\n".join(lignes)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Memoire de projet.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    # Option commune a toutes les sous-commandes : posee sur un parent, elle
    # s'ecrit apres la sous-commande comme dans les dix-sept scripts deja
    # cables. Elle ne touche que l'affichage : ce que projet.json enregistre
    # ne change pas de langue.
    commun = argparse.ArgumentParser(add_help=False)
    commun.add_argument("--langue-affichage", choices=("fr", "en"),
                        default=None,
                        help="langue des messages et du tableau de bord "
                             "(defaut fr : un projet n'est pas un manuscrit, "
                             "il ne porte pas de pragme de langue). Le "
                             "journal ecrit dans projet.json reste francais")

    i = sub.add_parser("init", parents=[commun])
    i.add_argument("--out", default="projet.json")

    sh = sub.add_parser("show", parents=[commun])
    sh.add_argument("--file", default="projet.json")

    g = sub.add_parser("get", parents=[commun])
    g.add_argument("cle")
    g.add_argument("--file", default="projet.json")

    s = sub.add_parser("set", parents=[commun])
    s.add_argument("cle")
    s.add_argument("valeur")
    s.add_argument("--file", default="projet.json")

    et = sub.add_parser("etape", parents=[commun])
    et.add_argument("nom")
    et.add_argument("etat", choices=list(ETATS_VALIDES))
    et.add_argument("--motif", default="")
    et.add_argument("--file", default="projet.json")

    ar = sub.add_parser("artefact", parents=[commun])
    ar.add_argument("nom")
    ar.add_argument("--file", default="projet.json")

    fr = sub.add_parser("frontiere", parents=[commun])
    fr.add_argument("libelle")
    fr.add_argument("--decision-attente", default="", dest="decision_attente")
    fr.add_argument("--file", default="projet.json")

    rp = sub.add_parser("reprendre", parents=[commun])
    rp.add_argument("hash")
    rp.add_argument("--file", default="projet.json")

    dc = sub.add_parser("decision", parents=[commun])
    dc.add_argument("libelle")
    dc.add_argument("--file", default="projet.json")

    ob = sub.add_parser("objet", parents=[commun])
    ob.add_argument("type_objet", choices=list(TYPES_OBJET))
    ob.add_argument("numero", type=int)
    ob.add_argument("libelle")
    ob.add_argument("--file", default="projet.json")

    ps = sub.add_parser("passation", parents=[commun])
    ps.add_argument("--format", choices=("text", "json"), default="text")
    ps.add_argument("--file", default="projet.json")

    op = sub.add_parser("outrepasser", parents=[commun])
    op.add_argument("libelle")
    op.add_argument("--justification", default="")
    op.add_argument("--file", default="projet.json")

    rc = sub.add_parser("reproductibilite", parents=[commun])
    rc.add_argument("--plugin-version", required=True, dest="plugin_version")
    rc.add_argument("--modele", required=True)
    rc.add_argument("--file", default="projet.json")

    st = sub.add_parser("status", parents=[commun])
    st.add_argument("--file", default="projet.json")

    a = ap.parse_args(argv)
    lib = _lib()
    la = lib.resoudre_affichage(a.langue_affichage)

    if a.cmd == "init":
        if os.path.exists(a.out):
            print(lib.t("project.existe", la, fichier=a.out))
            return 0
        sauver(a.out, _squelette_v2())
        print(lib.t("project.creee", la, fichier=a.out))
        return 0

    if a.cmd == "show":
        print(json.dumps(charger(a.file), ensure_ascii=False, indent=2))
        return 0

    if a.cmd == "get":
        print(json.dumps(charger(a.file).get(a.cle, None), ensure_ascii=False))
        return 0

    if a.cmd == "set":
        if a.cle == "journal":
            print(lib.t("project.journal_refuse", la))
            return 1
        d = charger(a.file)
        try:
            val = json.loads(a.valeur)
        except json.JSONDecodeError:
            val = a.valeur
        d[a.cle] = val
        sauver(a.file, d)
        print(lib.t("project.maj", la, cle=a.cle, fichier=a.file))
        return 0

    if a.cmd == "etape":
        d = charger(a.file)
        try:
            ancien, nouveau = changer_etat(d, a.nom, a.etat, a.motif, la)
        except ValueError as e:
            print(lib.t("project.erreur", la, erreur=e))
            return 1
        sauver(a.file, d)
        print(lib.t("project.etape_changee", la, nom=a.nom,
                    ancien=lib.valeur("project.etat", ancien, la),
                    nouveau=lib.valeur("project.etat", nouveau, la)))
        return 0

    if a.cmd == "artefact":
        d = charger(a.file)
        version = enregistrer_artefact(d, a.nom)
        sauver(a.file, d)
        print(lib.t("project.artefact_enregistre", la, nom=a.nom,
                    version=version))
        return 0

    if a.cmd == "frontiere":
        d = charger(a.file)
        entree = poser_frontiere(d, a.libelle, a.decision_attente or None)
        sauver(a.file, d)
        print(lib.t("project.frontiere_posee", la, hash=entree["hash"],
                    libelle=a.libelle))
        if entree.get("decision_attente"):
            print(lib.t("project.decision_rattachee", la,
                        decision=entree["decision_attente"]))
        return 0

    if a.cmd == "reprendre":
        d = charger(a.file)
        try:
            accuse = reprendre(d, a.hash, la)
        except ValueError as e:
            print(lib.t("project.erreur", la, erreur=e))
            return 1
        sauver(a.file, d)
        print(lib.t("project.reprise", la,
                    libelle=accuse["libelle_frontiere"],
                    horodatage=accuse["horodatage_frontiere"]))
        print(lib.t("project.reprise_etapes", la,
                    etapes=json.dumps(accuse["etapes"], ensure_ascii=False)))
        print(lib.t("project.reprise_artefacts", la,
                    artefacts=json.dumps(accuse["artefacts"],
                                         ensure_ascii=False)))
        if accuse["decision_attente"]:
            print(lib.t("project.reprise_decision", la,
                        decision=accuse["decision_attente"]))
        else:
            print(lib.t("project.aucune_decision", la))
        return 0

    if a.cmd == "decision":
        d = charger(a.file)
        entree = {"type": "decision", "horodatage": _horodatage(), "libelle": a.libelle}
        _ajouter_journal(d, entree)
        sauver(a.file, d)
        print(lib.t("project.decision_journalisee", la, libelle=a.libelle))
        return 0

    if a.cmd == "objet":
        d = charger(a.file)
        try:
            objet = enregistrer_objet(d, a.type_objet, a.numero, a.libelle,
                                      la)
        except ValueError as e:
            print(lib.t("project.erreur", la, erreur=e))
            return 1
        sauver(a.file, d)
        print(lib.t("project.objet_pose", la,
                    objet=lib.valeur("project.type_objet", objet["type"], la),
                    numero=objet["numero"], libelle=objet["libelle"]))
        return 0

    if a.cmd == "passation":
        p = passation_redacteur(charger(a.file))
        # Le JSON ne se traduit pas : c'est le contrat lu par le parent.
        print(json.dumps(p, ensure_ascii=False, indent=2)
              if a.format == "json" else passation_texte(p, la))
        return 0

    if a.cmd == "outrepasser":
        d = charger(a.file)
        cran = prochain_cran(d)
        try:
            journaliser_outrepassement(a.file, a.libelle, cran,
                                       a.justification or None, la)
        except ValueError as e:
            print(lib.t("project.erreur", la, erreur=e))
            return 1
        print(lib.t("project.outrepassement", la, cran=cran,
                    libelle=a.libelle))
        return 0

    if a.cmd == "reproductibilite":
        d = charger(a.file)
        entree = enregistrer_reproductibilite(d, a.plugin_version, a.modele)
        sauver(a.file, d)
        print(lib.t("project.repro_enregistree", la,
                    version=entree["plugin_version"], modele=entree["modele"],
                    horodatage=entree["horodatage"]))
        # L'entree du journal porte la declaration francaise ; le rappel a
        # l'ecran est le meme texte, dans la langue demandee.
        print(lib.t("project.rappel", la,
                    declaration=lib.t("project.stochasticite", la)))
        return 0

    if a.cmd == "status":
        d = charger(a.file)
        print(statut_texte(d, la))
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
