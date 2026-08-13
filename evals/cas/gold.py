# -*- coding: utf-8 -*-
"""Cas d'eval du harnais de jeu d'or lui-meme (tools/gold.py).

Construit un jeu d'or synthetique dans un dossier temporaire, avec des cas
deliberement casses, pour verifier que chaque invariant (I1 a I9) casse bien
quand il doit et seulement la. Verifie aussi la mesure, la comparaison
directionnelle entre deux rapports et la porte a friction a 3 crans.
"""
import importlib.util
import json
import os
import tempfile

_spec = importlib.util.spec_from_file_location("gold", os.path.join(RACINE, "tools", "gold.py"))
gold = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gold)

TEXTE_A = "Le protocole decrit trois etapes independantes, chacune datee et documentee par un releve horodate precis. " * 4
TEXTE_B = "Les resultats convergent vers une valeur stable sur l'ensemble des series mesurees pendant la campagne. " * 4


def construire_tache_scorecard(dossier):
    """Construit une tache 'scorecard' synthetique valide, deux cas, en
    appelant la vraie fonction scorecard.evaluer (pas de reimplementation)."""
    os.makedirs(os.path.join(dossier, "cas"), exist_ok=True)
    cas_src = [("cas-a", TEXTE_A), ("cas-b", TEXTE_B)]
    cas = []
    dist = {}
    for cid, texte in cas_src:
        chemin_rel = f"cas/{cid}.md"
        with open(os.path.join(dossier, chemin_rel), "w", encoding="utf-8") as f:
            f.write(texte)
        r = gold.score.evaluer(texte)
        cas.append({
            "id": cid, "fichier": chemin_rel, "type": "propre",
            "attendu": {"verdict": r["verdict"],
                        "axes_les_plus_bas": r["forces_faiblesses"]["pires_axes"]},
        })
        dist["propre"] = dist.get("propre", 0) + 1
    manifeste = {
        "tache": "scorecard",
        "version_gel": "0.9.0",
        "seuil_exactitude_attendu": 0.9,
        "non_couvert": ["synthetique, sert uniquement a eprouver le harnais"],
        "distribution": dist,
        "cas": cas,
    }
    with open(os.path.join(dossier, "manifeste.json"), "w", encoding="utf-8") as f:
        json.dump(manifeste, f, ensure_ascii=False, indent=2)
    return manifeste


def invariants_echoues(resultats):
    return {r["invariant"] for r in resultats if not r["ok"]}


with tempfile.TemporaryDirectory(prefix="scriptorium-gold-") as racine:

    # Cas 1 : jeu d'or synthetique bien forme, aucun invariant ne casse.
    d_ok = os.path.join(racine, "t-ok")
    construire_tache_scorecard(d_ok)
    r_ok = gold.verifier_tache("scorecard", d_ok)
    verifier("synthetique bien forme : tous les invariants passent",
             not invariants_echoues(r_ok), f"echoues={invariants_echoues(r_ok)}")

    # Cas 2 : I1, cas fantome (declare, fichier absent).
    d_i1 = os.path.join(racine, "t-i1")
    m = construire_tache_scorecard(d_i1)
    os.remove(os.path.join(d_i1, "cas", "cas-b.md"))
    r_i1 = gold.verifier_tache("scorecard", d_i1)
    verifier("I1 casse sur un cas fantome (fichier declare absent)",
             "I1-existence" in invariants_echoues(r_i1), f"echoues={invariants_echoues(r_i1)}")

    # Cas 3 : I2, fichier orphelin (present, non declare).
    d_i2 = os.path.join(racine, "t-i2")
    construire_tache_scorecard(d_i2)
    with open(os.path.join(d_i2, "cas", "cas-orphelin.md"), "w", encoding="utf-8") as f:
        f.write("Un cas jamais declare dans le manifeste.")
    r_i2 = gold.verifier_tache("scorecard", d_i2)
    verifier("I2 casse sur un fichier orphelin (present, non declare)",
             "I2-orphelin" in invariants_echoues(r_i2), f"echoues={invariants_echoues(r_i2)}")

    # Cas 4 : I3, id de cas duplique.
    d_i3 = os.path.join(racine, "t-i3")
    construire_tache_scorecard(d_i3)
    chemin_m = os.path.join(d_i3, "manifeste.json")
    mm = json.load(open(chemin_m, encoding="utf-8"))
    mm["cas"][1]["id"] = mm["cas"][0]["id"]
    json.dump(mm, open(chemin_m, "w", encoding="utf-8"))
    r_i3 = gold.verifier_tache("scorecard", d_i3)
    verifier("I3 casse sur un id de cas duplique",
             "I3-unicite" in invariants_echoues(r_i3), f"echoues={invariants_echoues(r_i3)}")

    # Cas 5 : I4, champ attendu vide.
    d_i4 = os.path.join(racine, "t-i4")
    construire_tache_scorecard(d_i4)
    chemin_m = os.path.join(d_i4, "manifeste.json")
    mm = json.load(open(chemin_m, encoding="utf-8"))
    mm["cas"][0]["attendu"]["verdict"] = ""
    json.dump(mm, open(chemin_m, "w", encoding="utf-8"))
    r_i4 = gold.verifier_tache("scorecard", d_i4)
    verifier("I4 casse sur un champ attendu vide",
             "I4-champs" in invariants_echoues(r_i4), f"echoues={invariants_echoues(r_i4)}")

    # Cas 6 : I5, distribution annoncee incorrecte.
    d_i5 = os.path.join(racine, "t-i5")
    construire_tache_scorecard(d_i5)
    chemin_m = os.path.join(d_i5, "manifeste.json")
    mm = json.load(open(chemin_m, encoding="utf-8"))
    mm["distribution"]["propre"] = 99
    json.dump(mm, open(chemin_m, "w", encoding="utf-8"))
    r_i5 = gold.verifier_tache("scorecard", d_i5)
    verifier("I5 casse sur une distribution annoncee fausse",
             "I5-distribution" in invariants_echoues(r_i5), f"echoues={invariants_echoues(r_i5)}")

    # Cas 7 : I6, l'invariant le plus important. Un axe invente n'appartient
    # pas a scorecard.AXES_CONNUS (la vraie constante), sans reimplementation.
    d_i6 = os.path.join(racine, "t-i6")
    construire_tache_scorecard(d_i6)
    chemin_m = os.path.join(d_i6, "manifeste.json")
    mm = json.load(open(chemin_m, encoding="utf-8"))
    mm["cas"][0]["attendu"]["axes_les_plus_bas"] = ["Axe-Invente-Qui-N-Existe-Pas"]
    json.dump(mm, open(chemin_m, "w", encoding="utf-8"))
    r_i6 = gold.verifier_tache("scorecard", d_i6)
    verifier("I6 casse sur un axe absent de scorecard.AXES_CONNUS (invariant cle)",
             "I6-recalculable" in invariants_echoues(r_i6), f"echoues={invariants_echoues(r_i6)}")
    verifier("I6 : une vraie renomination d'axe dans scorecard.py serait detectee "
             "(la liste valide vient de AXES_CONNUS importe, pas d'une copie)",
             set(gold.score.AXES_CONNUS) == {"Style", "Sources", "Tracabilite",
                                              "Terminologie et nombres", "Lisibilite"})

    # Cas 8 : I7, contenu de cas vide.
    d_i7 = os.path.join(racine, "t-i7")
    construire_tache_scorecard(d_i7)
    with open(os.path.join(d_i7, "cas", "cas-a.md"), "w", encoding="utf-8") as f:
        f.write("   \n  ")
    r_i7 = gold.verifier_tache("scorecard", d_i7)
    verifier("I7 casse sur un fichier de cas vide",
             "I7-contenu" in invariants_echoues(r_i7), f"echoues={invariants_echoues(r_i7)}")

    # Cas 9 : I8, champ obligatoire du manifeste absent.
    d_i8 = os.path.join(racine, "t-i8")
    construire_tache_scorecard(d_i8)
    chemin_m = os.path.join(d_i8, "manifeste.json")
    mm = json.load(open(chemin_m, encoding="utf-8"))
    del mm["seuil_exactitude_attendu"]
    json.dump(mm, open(chemin_m, "w", encoding="utf-8"))
    r_i8 = gold.verifier_tache("scorecard", d_i8)
    verifier("I8 casse sur un champ de manifeste obligatoire absent",
             "I8-manifeste" in invariants_echoues(r_i8), f"echoues={invariants_echoues(r_i8)}")

    # Cas 10 : I9, aveu de couverture vide.
    d_i9 = os.path.join(racine, "t-i9")
    construire_tache_scorecard(d_i9)
    chemin_m = os.path.join(d_i9, "manifeste.json")
    mm = json.load(open(chemin_m, encoding="utf-8"))
    mm["non_couvert"] = []
    json.dump(mm, open(chemin_m, "w", encoding="utf-8"))
    r_i9 = gold.verifier_tache("scorecard", d_i9)
    verifier("I9 casse sur un aveu non_couvert vide",
             "I9-aveu" in invariants_echoues(r_i9), f"echoues={invariants_echoues(r_i9)}")

    # Cas 11 : mesurer() sur une tache declaree mais non cablee -> statut
    # "en attente", jamais un plantage ni un faux succes.
    d_multi = os.path.join(racine, "t-multi")
    construire_tache_scorecard(os.path.join(d_multi, "scorecard"))
    os.makedirs(os.path.join(d_multi, "tache-experimentale"), exist_ok=True)
    json.dump({
        "tache": "tache-experimentale", "version_gel": "0.9.0",
        "seuil_exactitude_attendu": 0.9,
        "non_couvert": ["harnais non cable pour cette tache, expres"],
        "distribution": {}, "cas": [],
    }, open(os.path.join(d_multi, "tache-experimentale", "manifeste.json"), "w", encoding="utf-8"))
    gold_dir_original = gold.GOLD_DIR
    try:
        gold.GOLD_DIR = d_multi
        r_mes = gold.mesurer()
    finally:
        gold.GOLD_DIR = gold_dir_original
    verifier("mesurer : tache cablee rend un statut mesure",
             r_mes["taches"]["scorecard"]["statut"] == "mesure",
             f"statut={r_mes['taches']['scorecard'].get('statut')}")
    verifier("mesurer : tache declaree non cablee rend 'en_attente', pas un plantage",
             r_mes["taches"]["tache-experimentale"]["statut"] == "en_attente",
             f"statut={r_mes['taches']['tache-experimentale'].get('statut')}")
    verifier("mesurer : le champ mises_en_garde n'est jamais vide",
             len(r_mes["mises_en_garde"]) > 0)

    # Cas 12 : porte directionnelle, une baisse de faux_positifs (polarite
    # bas, donc une amelioration) n'est jamais lue comme une regression.
    ref = {"version_plugin": "0.9.0", "taches": {
        "scorecard": {"statut": "mesure", "n_cas": 10, "exactitude": 0.9,
                      "faux_positifs": 3, "faux_negatifs": 1}}}
    cand_ameliore = {"version_plugin": "0.9.1", "taches": {
        "scorecard": {"statut": "mesure", "n_cas": 10, "exactitude": 0.9,
                      "faux_positifs": 1, "faux_negatifs": 1}}}
    c1 = gold.comparer_rapports(ref, cand_ameliore)
    verifier("porte : une baisse de faux_positifs n'est jamais une regression",
             not c1["regressions"], f"regressions={c1['regressions']}")

    cand_regresse = {"version_plugin": "0.9.1", "taches": {
        "scorecard": {"statut": "mesure", "n_cas": 10, "exactitude": 0.7,
                      "faux_positifs": 3, "faux_negatifs": 1}}}
    c2 = gold.comparer_rapports(ref, cand_regresse)
    verifier("porte : une baisse d'exactitude est une regression",
             any(c["metrique"] == "exactitude" for c in c2["regressions"]),
             f"regressions={c2['regressions']}")

    cand_sans_metrique = {"version_plugin": "0.9.1", "taches": {
        "scorecard": {"statut": "mesure", "n_cas": 10, "exactitude": 0.9,
                      "faux_negatifs": 1}}}
    c3 = gold.comparer_rapports(ref, cand_sans_metrique)
    verifier("porte : une metrique disparue au candidat est un signal, pas un succes",
             any(c["statut"] == "metrique disparue" and c["regression"] for c in c3["comparaisons"]),
             f"comparaisons={c3['comparaisons']}")

    # Cas 13-15 : la porte nait consultative, son mode bloquant est derriere
    # un drapeau explicite, et l'outrepassement suit la friction a 3 crans.
    code_a, _ = gold.appliquer_porte(c2, bloquant=False, outrepasser=False,
                                      justification="", chemin_projet="projet.json")
    verifier("porte consultative (sans --bloquant) : code 0 malgre la regression",
             code_a == 0, f"code={code_a}")

    code_b, _ = gold.appliquer_porte(c2, bloquant=True, outrepasser=False,
                                      justification="", chemin_projet="projet.json")
    verifier("porte bloquante sans --outrepasser : code 1 sur regression",
             code_b == 1, f"code={code_b}")

    ancien_cwd = os.getcwd()
    d_friction = os.path.join(racine, "t-friction")
    os.makedirs(d_friction, exist_ok=True)
    try:
        os.chdir(d_friction)
        code_c, msg_c = gold.appliquer_porte(c2, bloquant=True, outrepasser=True,
                                              justification="", chemin_projet="projet-absent.json")
        verifier("porte bloquante + --outrepasser, 1er cran : accepte, journalise",
                 code_c == 0 and os.path.isfile(gold.FALLBACK), f"code={code_c} msg={msg_c}")
    finally:
        os.chdir(ancien_cwd)
