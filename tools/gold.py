#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jeu d'or versionne et porte de regression directionnelle pour Scriptorium.

Un jeu d'eval binaire (evals/run-evals.py) dit si une assertion passe ou
echoue, jamais si la QUALITE d'un script de notation derive dans le temps.
Ce module ajoute un corpus fige (evals/gold/), verifie sa sante, rejoue les
mesures et compare deux rapports pour detecter une regression, sans jamais
bloquer par defaut (voir docs/CONCEPTION.md, "Mesure avant politique").

Sous-commandes :
    python3 tools/gold.py verifier [--format text|json]
        Verifie la sante du jeu d'or lui-meme (invariants I1 a I9, voir
        INVARIANTS ci-dessous). Code de sortie 1 si un invariant casse.
    python3 tools/gold.py mesurer [--format text|json] [--out FICHIER]
        Rejoue le jeu d'or avec les vraies fonctions du depot, ecrit un
        rapport horodate portant la version du plugin. Code de sortie
        toujours 0 (une mesure n'est pas un echec, voir --bloquant sous
        comparer).
    python3 tools/gold.py comparer REFERENCE.json CANDIDAT.json
                           [--format text|json] [--bloquant]
                           [--outrepasser] [--justification TEXTE]
                           [--projet FICHIER]
        Compare un rapport candidat a un rapport de reference, polarite par
        polarite. Consultatif par defaut (code 0 meme en regression) ; exige
        --bloquant pour faire echouer la commande, et alors --outrepasser
        avec la meme friction a 3 crans que tools/check.py pour passer
        outre une regression, journalisee.

INVARIANTS DU JEU D'OR (verifier), chacun nomme dans le rapport s'il casse :
    I1  existence   : chaque cas declare dans le manifeste a son fichier
                      present sur disque (aucun cas fantome).
    I2  orphelin    : chaque fichier present dans cas/ est declare dans le
                      manifeste (aucun cas orphelin).
    I3  unicite     : les id de cas sont uniques dans un meme manifeste.
    I4  champs      : aucun champ de "attendu" declare n'est vide ou None.
    I5  distribution: manifeste.distribution concorde avec le compte reel
                      des "type" des cas declares.
    I6  recalculable: les cles utilisees dans "attendu" (axes du scorecard,
                      severites du linter) appartiennent aux constantes
                      REELLES exposees par scripts/scorecard.py et
                      scripts/lint-style.py (AXES_CONNUS, CRITIQUE, MAJEUR,
                      MINEUR), jamais a une liste recopiee dans ce fichier.
                      L'INVARIANT LE PLUS IMPORTANT : sans lui, le jeu d'or
                      teste une reimplementation parallele plutot que le
                      produit reel.
    I7  contenu     : le fichier de cas n'est pas vide apres nettoyage.
    I8  manifeste   : les champs obligatoires du manifeste sont presents
                      (tache, version_gel, seuil_exactitude_attendu,
                      non_couvert, distribution, cas).
    I9  aveu        : le champ non_couvert n'est pas vide (aveu explicite
                      de ce que le jeu d'or ne couvre pas).

Bibliotheque standard uniquement. Commentaires et docstrings sans accents
(console Windows cp1252) ; les .md et .json de contenu restent accentues.
"""
import argparse
import datetime
import glob
import importlib.util
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.join(ICI, "..", "scriptorium", "scripts")
GOLD_DIR = os.path.join(ICI, "..", "evals", "gold")
PLUGIN_JSON = os.path.join(ICI, "..", "scriptorium", ".claude-plugin", "plugin.json")
FALLBACK = ".outrepassements-gold.json"


def _mod(fichier, nom):
    spec = importlib.util.spec_from_file_location(nom, os.path.join(SCR, fichier))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


score = _mod("scorecard.py", "scorecard")
lint = _mod("lint-style.py", "lint_style")
projet = _mod("project.py", "project")


def version_plugin():
    """Lit la version courante du plugin depuis .claude-plugin/plugin.json.
    Fait precis ou rien : si le fichier manque ou est mal forme, retourne
    None plutot qu'une valeur inventee."""
    try:
        with open(PLUGIN_JSON, encoding="utf-8") as f:
            return json.load(f).get("version")
    except (OSError, json.JSONDecodeError):
        return None


# Champs obligatoires du manifeste (I8).
CHAMPS_MANIFESTE = ["tache", "version_gel", "seuil_exactitude_attendu",
                     "non_couvert", "distribution", "cas"]


def taches_declarees():
    """Liste les sous-dossiers de evals/gold/ qui portent un manifeste.json.
    Une tache dont le dossier existe mais le manifeste est absent ou illisible
    n'est pas une tache declaree ici (elle serait de toute facon signalee par
    charger_manifeste au moment ou on tente de la charger)."""
    if not os.path.isdir(GOLD_DIR):
        return []
    out = []
    for nom in sorted(os.listdir(GOLD_DIR)):
        chemin = os.path.join(GOLD_DIR, nom, "manifeste.json")
        if os.path.isfile(chemin):
            out.append(nom)
    return out


def charger_manifeste(dossier_tache):
    chemin = os.path.join(dossier_tache, "manifeste.json")
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def _fichiers_cas_reels(dossier_tache):
    motif = os.path.join(dossier_tache, "cas", "*")
    return {os.path.relpath(p, dossier_tache).replace(os.sep, "/")
            for p in glob.glob(motif) if os.path.isfile(p)}


def _valeur_vide(v):
    return v is None or v == "" or v == [] or v == {}


def _cles_attendu_a_verifier(tache, attendu):
    """Retourne (cles_utilisees, cles_valides) pour l'invariant I6, tache par
    tache. Les cles_valides viennent TOUJOURS d'une constante importee du
    vrai module de mesure, jamais d'une liste recopiee ici : c'est le point
    de l'invariant I6."""
    if tache == "scorecard":
        return set(attendu.get("axes_les_plus_bas") or []), set(score.AXES_CONNUS)
    if tache == "lint-style":
        return set(attendu.keys()), {lint.CRITIQUE, lint.MAJEUR, lint.MINEUR}
    return set(), None


def verifier_tache(nom_tache, dossier_tache):
    """Verifie les invariants I1 a I9 pour une tache. Retourne une liste de
    dicts {invariant, ok, detail}."""
    resultats = []

    def rapporter(inv, ok, detail=""):
        resultats.append({"invariant": inv, "ok": bool(ok), "detail": detail})

    try:
        m = charger_manifeste(dossier_tache)
    except (OSError, json.JSONDecodeError) as e:
        rapporter("I8-manifeste", False, f"manifeste illisible : {e}")
        return resultats

    manquants = [c for c in CHAMPS_MANIFESTE if c not in m]
    rapporter("I8-manifeste", not manquants,
               f"champ(s) manquant(s) : {', '.join(manquants)}" if manquants else "")

    rapporter("I9-aveu", bool(m.get("non_couvert")),
               "non_couvert est vide ou absent" if not m.get("non_couvert") else "")

    cas = m.get("cas", [])

    # I3 : unicite des id
    ids = [c.get("id") for c in cas]
    doublons = sorted({i for i in ids if ids.count(i) > 1})
    rapporter("I3-unicite", not doublons,
               f"id(s) en double : {', '.join(map(str, doublons))}" if doublons else "")

    # I1 : chaque cas declare existe sur disque (cas fantome)
    fantomes = []
    for c in cas:
        chemin = os.path.join(dossier_tache, c.get("fichier", ""))
        if not os.path.isfile(chemin):
            fantomes.append(c.get("id"))
    rapporter("I1-existence", not fantomes,
               f"cas fantome(s), fichier absent : {', '.join(map(str, fantomes))}" if fantomes else "")

    # I2 : chaque fichier present sur disque est declare (cas orphelin)
    declares = {c.get("fichier", "").replace(os.sep, "/") for c in cas}
    reels = _fichiers_cas_reels(dossier_tache)
    orphelins = sorted(reels - declares)
    rapporter("I2-orphelin", not orphelins,
               f"fichier(s) orphelin(s), non declare(s) : {', '.join(orphelins)}" if orphelins else "")


    # I4, I6, I7 : par cas
    champs_vides = []
    cles_invalides = []
    contenus_vides = []
    distribution_reelle = {}
    for c in cas:
        typ = c.get("type")
        distribution_reelle[typ] = distribution_reelle.get(typ, 0) + 1

        attendu = c.get("attendu", {})
        for k, v in attendu.items():
            if _valeur_vide(v):
                champs_vides.append(f"{c.get('id')}.{k}")

        cles_utilisees, cles_valides = _cles_attendu_a_verifier(nom_tache, attendu)
        if cles_valides is not None:
            mauvaises = cles_utilisees - cles_valides
            if mauvaises:
                cles_invalides.append(f"{c.get('id')} : {', '.join(sorted(mauvaises))}")

        chemin = os.path.join(dossier_tache, c.get("fichier", ""))
        if os.path.isfile(chemin):
            with open(chemin, encoding="utf-8") as f:
                if not f.read().strip():
                    contenus_vides.append(c.get("id"))

    rapporter("I4-champs", not champs_vides,
               f"champ(s) attendu vide(s) : {', '.join(champs_vides)}" if champs_vides else "")
    rapporter("I6-recalculable", not cles_invalides,
               "cle(s) hors des constantes reelles du module de mesure : "
               + "; ".join(cles_invalides) if cles_invalides else "")
    rapporter("I7-contenu", not contenus_vides,
               f"cas au contenu vide : {', '.join(map(str, contenus_vides))}" if contenus_vides else "")

    # I5 : distribution annoncee vs reelle
    dist_annoncee = m.get("distribution", {})
    ecarts = []
    for typ in set(dist_annoncee) | set(distribution_reelle):
        a = dist_annoncee.get(typ, 0)
        r = distribution_reelle.get(typ, 0)
        if a != r:
            ecarts.append(f"{typ} (annonce {a}, reel {r})")
    rapporter("I5-distribution", not ecarts,
               f"ecart(s) : {', '.join(ecarts)}" if ecarts else "")

    return resultats


def verifier(taches=None, format_sortie="text"):
    """Verifie la sante du jeu d'or pour les taches donnees (toutes les
    taches declarees si non precise). Retourne (0 ou 1, texte_ou_dict)."""
    noms = taches if taches else taches_declarees()
    rapport = {}
    tout_ok = True
    for nom in noms:
        dossier = os.path.join(GOLD_DIR, nom)
        resultats = verifier_tache(nom, dossier)
        ok_tache = all(r["ok"] for r in resultats)
        tout_ok = tout_ok and ok_tache
        rapport[nom] = {"ok": ok_tache, "invariants": resultats}

    if format_sortie == "json":
        return (0 if tout_ok else 1), json.dumps(rapport, ensure_ascii=False, indent=2)

    lignes = []
    for nom, r in rapport.items():
        lignes.append(f"Tache : {nom}  [{'OK' if r['ok'] else 'ECHEC'}]")
        for inv in r["invariants"]:
            marque = "OK" if inv["ok"] else "ECHEC"
            suffixe = f"  {inv['detail']}" if (inv["detail"] and not inv["ok"]) else ""
            lignes.append(f"  [{marque}] {inv['invariant']}{suffixe}")
    if not noms:
        lignes.append("Aucune tache declaree sous evals/gold/.")
    return (0 if tout_ok else 1), "\n".join(lignes)


# Polarite de chaque metrique : "haut" doit monter pour etre meilleur, "bas"
# doit descendre. La porte (comparer) applique cette polarite a l'ecart,
# jamais l'inverse (voir docs/CONCEPTION.md).
POLARITES = {"exactitude": "haut", "faux_positifs": "bas", "faux_negatifs": "bas"}


def _lire_cas(dossier_tache, c):
    with open(os.path.join(dossier_tache, c["fichier"]), encoding="utf-8") as f:
        return f.read()


def _mesurer_scorecard(dossier_tache, manifeste):
    cas = manifeste.get("cas", [])
    if not cas:
        return {"statut": "en_attente", "motif": "aucun cas dans le manifeste"}
    corrects = faux_pos = faux_neg = 0
    for c in cas:
        texte = _lire_cas(dossier_tache, c)
        r = score.evaluer(texte)
        att = c["attendu"]
        if r["verdict"] == att.get("verdict"):
            corrects += 1
        total = r["total"]
        if total is not None:
            if att.get("total_max") is not None and total > att["total_max"]:
                faux_pos += 1
            elif att.get("total_min") is not None and total < att["total_min"]:
                faux_neg += 1
    n = len(cas)
    return {
        "statut": "mesure",
        "n_cas": n,
        "exactitude": round(corrects / n, 4),
        "faux_positifs": faux_pos,
        "faux_negatifs": faux_neg,
    }


def _mesurer_lint_style(dossier_tache, manifeste):
    cas = manifeste.get("cas", [])
    if not cas:
        return {"statut": "en_attente", "motif": "aucun cas dans le manifeste"}
    corrects = faux_pos = faux_neg = 0
    for c in cas:
        texte = _lire_cas(dossier_tache, c)
        compte = lint.compter(lint.lint_text(texte))
        att = c["attendu"]
        mapping = {"critique": lint.CRITIQUE, "majeur": lint.MAJEUR, "mineur": lint.MINEUR}
        exact = True
        for cle_att, cle_reelle in mapping.items():
            reel = compte[cle_reelle]
            attendu_val = att.get(cle_att, 0)
            if reel != attendu_val:
                exact = False
            if reel > attendu_val:
                faux_pos += reel - attendu_val
            elif reel < attendu_val:
                faux_neg += attendu_val - reel
        if exact:
            corrects += 1
    n = len(cas)
    return {
        "statut": "mesure",
        "n_cas": n,
        "exactitude": round(corrects / n, 4),
        "faux_positifs": faux_pos,
        "faux_negatifs": faux_neg,
    }


TASK_HANDLERS = {
    "scorecard": _mesurer_scorecard,
    "lint-style": _mesurer_lint_style,
}


def mesurer():
    """Rejoue le jeu d'or pour chaque tache declaree. Une tache declaree
    mais pas encore cablee (pas dans TASK_HANDLERS) rend le statut "en
    attente", jamais un plantage ni un faux succes."""
    taches = {}
    mises_en_garde = [
        "corpus de dix cas par tache : une exactitude ponctuelle, pas une "
        "estimation statistiquement stable.",
        "voir le champ non_couvert de chaque manifeste (evals/gold/*/"
        "manifeste.json) pour les limites detaillees de cette tache.",
        "la porte issue de ce rapport reste consultative par defaut ; voir "
        "docs/CONCEPTION.md et tools/gold.py comparer --bloquant.",
    ]
    for nom in taches_declarees():
        dossier = os.path.join(GOLD_DIR, nom)
        try:
            m = charger_manifeste(dossier)
        except (OSError, json.JSONDecodeError) as e:
            taches[nom] = {"statut": "en_attente", "motif": f"manifeste illisible : {e}"}
            continue
        gel = m.get("version_gel")
        actuelle = version_plugin()
        if gel and actuelle and gel != actuelle:
            mises_en_garde.append(
                f"tache {nom} : jeu d'or fige a la version {gel}, mesure a la "
                f"version {actuelle} ; un ecart de version n'est pas en soi "
                "une regression.")
        handler = TASK_HANDLERS.get(nom)
        if handler is None:
            taches[nom] = {"statut": "en_attente",
                            "motif": "tache declaree, non cablee dans TASK_HANDLERS"}
            continue
        taches[nom] = handler(dossier, m)

    return {
        "horodatage": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "version_plugin": version_plugin(),
        "polarites": dict(POLARITES),
        "taches": taches,
        "mises_en_garde": mises_en_garde,
    }


def rapport_mesure_texte(r):
    out = [f"Rapport jeu d'or : version {r.get('version_plugin')}, {r.get('horodatage')}", ""]
    for nom, t in r["taches"].items():
        if t.get("statut") != "mesure":
            out.append(f"  {nom:14} [{t.get('statut', '?')}] {t.get('motif', '')}")
            continue
        out.append(f"  {nom:14} exactitude={t['exactitude']:.2%}  "
                    f"faux_positifs={t['faux_positifs']}  faux_negatifs={t['faux_negatifs']}  "
                    f"(n={t['n_cas']})")
    out.append("")
    out.append("Mises en garde :")
    for mg in r["mises_en_garde"]:
        out.append(f"  - {mg}")
    return "\n".join(out)


EPSILON = 1e-9


def comparer_rapports(ref, cand):
    """Compare un rapport candidat a un rapport de reference, polarite par
    polarite. Le silence (une metrique presente a la reference et absente
    au candidat) est un signal, jamais un succes : statut "metrique
    disparue". Une tache "en attente" des deux cotes ne produit ni
    plantage ni faux succes, elle est simplement ignoree de la comparaison."""
    comparaisons = []
    taches_ref = ref.get("taches", {})
    taches_cand = cand.get("taches", {})

    for nom, t_ref in taches_ref.items():
        if t_ref.get("statut") != "mesure":
            continue  # rien a comparer, la reference elle-meme n'a pas mesure
        t_cand = taches_cand.get(nom)
        if t_cand is None:
            comparaisons.append({"tache": nom, "metrique": None,
                                  "statut": "tache disparue au candidat",
                                  "regression": True})
            continue
        if t_cand.get("statut") != "mesure":
            comparaisons.append({"tache": nom, "metrique": None,
                                  "statut": f"tache {t_cand.get('statut')} au candidat",
                                  "regression": True})
            continue
        for metrique, polarite in POLARITES.items():
            v_ref = t_ref.get(metrique)
            if v_ref is None:
                continue
            if metrique not in t_cand:
                comparaisons.append({"tache": nom, "metrique": metrique,
                                      "statut": "metrique disparue",
                                      "avant": v_ref, "apres": None,
                                      "regression": True})
                continue
            v_cand = t_cand[metrique]
            delta = v_cand - v_ref
            if polarite == "haut":
                regression = delta < -EPSILON
            else:
                regression = delta > EPSILON
            comparaisons.append({"tache": nom, "metrique": metrique,
                                  "statut": "compare", "polarite": polarite,
                                  "avant": v_ref, "apres": v_cand, "delta": delta,
                                  "regression": regression})

    regressions = [c for c in comparaisons if c["regression"]]
    return {
        "horodatage": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "version_plugin_reference": ref.get("version_plugin"),
        "version_plugin_candidat": cand.get("version_plugin"),
        "comparaisons": comparaisons,
        "regressions": regressions,
        "mises_en_garde": [
            "comparaison directionnelle : une baisse de faux_positifs ou "
            "faux_negatifs n'est jamais lue comme une regression, seule une "
            "hausse l'est (polarite bas) ; seule une baisse d'exactitude "
            "l'est (polarite haut).",
            "une metrique presente a la reference et absente au candidat "
            "est traitee comme une regression silencieuse, pas ignoree.",
        ],
    }


def rapport_comparaison_texte(c):
    out = [f"Comparaison jeu d'or : reference {c['version_plugin_reference']} "
           f"-> candidat {c['version_plugin_candidat']}", ""]
    for cmp in c["comparaisons"]:
        marque = "[REGRESSION]" if cmp["regression"] else "[OK]"
        if cmp["statut"] != "compare":
            out.append(f"  {marque} {cmp['tache']:14} {cmp['statut']}")
            continue
        out.append(f"  {marque} {cmp['tache']:14} {cmp['metrique']:14} "
                    f"{cmp['avant']} -> {cmp['apres']} (delta {cmp['delta']:+g}, "
                    f"polarite {cmp['polarite']})")
    out.append("")
    if c["regressions"]:
        out.append(f"{len(c['regressions'])} regression(s) detectee(s).")
    else:
        out.append("Aucune regression detectee.")
    out.append("")
    out.append("Mises en garde :")
    for mg in c["mises_en_garde"]:
        out.append(f"  - {mg}")
    return "\n".join(out)


def _cran_local(chemin):
    if not os.path.isfile(chemin):
        return 1
    try:
        arr = json.load(open(chemin, encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        arr = []
    return len(arr) + 1


def _journaliser_local(chemin, libelle, cran, justification):
    arr = []
    if os.path.isfile(chemin):
        try:
            arr = json.load(open(chemin, encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            arr = []
    arr.append({
        "horodatage": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "type": "outrepassement-gold",
        "libelle": libelle,
        "cran": cran,
        "justification": justification or "",
    })
    json.dump(arr, open(chemin, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def appliquer_porte(rapport_comparaison, bloquant, outrepasser, justification, chemin_projet):
    """Applique le mode bloquant de la porte, derriere le drapeau explicite
    --bloquant (la porte nait consultative, voir docs/CONCEPTION.md). Meme
    friction a 3 crans que tools/check.py pour un outrepassement : cran 1
    accepte avec avertissement, cran 2 exige une justification non vide,
    cran 3 et au-dela exige au moins 100 caracteres. Retourne (code, message)."""
    if not bloquant:
        return 0, "Porte consultative (--bloquant absent) : aucune regression ne fait echouer la commande."
    if not rapport_comparaison["regressions"]:
        return 0, "Porte bloquante : aucune regression, commande reussie."
    if not outrepasser:
        return 1, f"Porte bloquante : {len(rapport_comparaison['regressions'])} regression(s), --outrepasser absent."

    projet_existe = os.path.isfile(chemin_projet)
    cran = projet.prochain_cran(projet.charger(chemin_projet)) if projet_existe else _cran_local(FALLBACK)
    try:
        projet.valider_justification(cran, justification)
    except ValueError as e:
        return 1, f"Outrepassement refuse : {e}"

    noms = sorted({c["tache"] for c in rapport_comparaison["regressions"]})
    libelle = f"regression jeu d'or sur {len(rapport_comparaison['regressions'])} " \
              f"metrique(s), tache(s) : {', '.join(noms)}"
    if projet_existe:
        projet.journaliser_outrepassement(chemin_projet, libelle, cran, justification or None)
        trace = chemin_projet
    else:
        _journaliser_local(FALLBACK, libelle, cran, justification)
        trace = FALLBACK
    msg = f"[OUTREPASSE] cran {cran} journalise dans {trace}."
    if cran == 1:
        msg += " Avertissement : 1er outrepassement, aucune justification requise. Le 2e en exigera une."
    return 0, msg


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="gold.py",
        description="Jeu d'or versionne et porte de regression directionnelle.")
    sous = ap.add_subparsers(dest="commande", required=True)

    p_v = sous.add_parser("verifier", help="verifie la sante du jeu d'or (invariants I1-I9)")
    p_v.add_argument("--format", choices=["text", "json"], default="text")
    p_v.add_argument("--tache", action="append", default=None,
                      help="limiter a une tache (repetable) ; toutes par defaut")

    p_m = sous.add_parser("mesurer", help="rejoue le jeu d'or et ecrit un rapport")
    p_m.add_argument("--format", choices=["text", "json"], default="text")
    p_m.add_argument("--out", default=None, help="ecrire le rapport JSON dans ce fichier")

    p_c = sous.add_parser("comparer", help="compare un rapport candidat a une reference")
    p_c.add_argument("reference")
    p_c.add_argument("candidat")
    p_c.add_argument("--format", choices=["text", "json"], default="text")
    p_c.add_argument("--bloquant", action="store_true",
                      help="fait echouer la commande sur regression (defaut : consultatif)")
    p_c.add_argument("--outrepasser", action="store_true",
                      help="passer outre une regression en mode --bloquant (journalise)")
    p_c.add_argument("--justification", default="",
                      help="justification de l'outrepassement (requise a partir du 2e cran)")
    p_c.add_argument("--projet", default="projet.json",
                      help="chemin du projet.json pour journaliser l'outrepassement")

    a = ap.parse_args(argv)

    if a.commande == "verifier":
        code, sortie = verifier(taches=a.tache, format_sortie=a.format)
        print(sortie)
        return code

    if a.commande == "mesurer":
        r = mesurer()
        if a.out:
            with open(a.out, "w", encoding="utf-8") as f:
                json.dump(r, f, ensure_ascii=False, indent=2)
                f.write("\n")
        print(json.dumps(r, ensure_ascii=False, indent=2) if a.format == "json"
              else rapport_mesure_texte(r))
        return 0

    if a.commande == "comparer":
        with open(a.reference, encoding="utf-8") as f:
            ref = json.load(f)
        with open(a.candidat, encoding="utf-8") as f:
            cand = json.load(f)
        c = comparer_rapports(ref, cand)
        print(json.dumps(c, ensure_ascii=False, indent=2) if a.format == "json"
              else rapport_comparaison_texte(c))
        code, msg = appliquer_porte(c, a.bloquant, a.outrepasser, a.justification, a.projet)
        print(msg)
        return code

    return 2


if __name__ == "__main__":
    sys.exit(main())
