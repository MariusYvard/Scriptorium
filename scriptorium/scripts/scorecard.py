#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scorecard deterministe d'un document pour Scriptorium.

Portions adaptees du projet openscience (Synthetic Sciences, InkVell Inc.),
Apache-2.0, github.com/synthetic-sciences/openscience. Modifications Marius
Yvard, MIT.

Agrege les sorties des scripts en une note de 0 a 100 sur cinq axes, avec des
penalites fixes et le calcul montre. Le modele emet les verdicts qualitatifs,
cette formule donne le nombre, reproductible d'un passage a l'autre.

Axes (20 points chacun) : Style, Sources, Tracabilite, Terminologie et nombres,
Lisibilite. Verdict : >=85 Pret, 70-84 A reviser, <70 A refondre. Ce verdict a
trois valeurs sert de porte de qualite generale, inchange par ce lot.

En plus du verdict a trois valeurs, le rapport porte une decision editoriale a
quatre valeurs (accepter, revision mineure, revision majeure, refus) plombee
par un plancher par axe (--plancher N, defaut 8 sur 20) : un axe sous ce seuil
plafonne la decision independamment du total, avec un sous-type de refus
propose en commentaire (jamais un verdict ferme, un signal mecanique ne peut
pas a lui seul distinguer hors perimetre de premature). Cette decision sert la
revue par consensus et la lettre de decision (voir references/consensus.md et
references/lettre-decision.md).

Ajouts de ce lot (recolte openscience, scholar-evaluation/calculate_scores.py) :
- Rapport texte : barre ASCII proportionnelle par axe (score/plafond, largeur
  fixe), identification automatique du meilleur et du pire axe.
- --poids FICHIER.json : poids personnalises par axe, renormalises a somme 1
  par une seule division (jamais deux, voir _normaliser_poids pour le detail
  du bug corrige dans la source). Sans ce fichier, poids egaux (0.2 chacun),
  total identique au comportement 0.7.0.
- --seuil-type brouillon|rapport|publication : teinte le verdict avec le
  seuil attendu du type de document (65/80/85 par defaut, voir SEUILS_TYPE),
  sans remplacer le verdict a trois valeurs.
- --trajectoire : note d'arret anticipe quand le gain total entre deux
  revues reste sous +3 points sans regression (voir chemins-defaillance.md,
  scenario D6).

Langue de notation : la langue se tranche UNE fois, dans evaluer, et descend
telle quelle dans chaque mesure qui en depend (linter de style, lisibilite,
integrite numerique, tracabilite). L'ordre de priorite est celui de
lint-style.py : --langue explicite, puis auto, puis le pragme du document
(lint-style:langue=en), puis le francais. Le pragme est donc honore par la
notation entiere sans qu'aucune option soit passee, et le comportement
francais par defaut ne bouge pas. Sans cette traversee, un texte anglais se
notait avec les regles francaises : la preposition « on » y declenchait la
regle pronom-on a chaque occurrence et effondrait l'axe Style.

Usage :
    python3 scorecard.py FICHIER [--format text|json] [--plancher N]
                         [--poids POIDS.json] [--seuil-type TYPE]
                         [--langue fr|en|auto]
    python3 scorecard.py --trajectoire RAPPORT_A.json RAPPORT_B.json [--format text|json]

Module importable : evaluer(texte, plancher=8, poids=None, seuil_type=None,
langue=None) -> dict, trajectoire(a, b) -> dict.
"""
import argparse
import importlib.util
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))

PLANCHER_DEFAUT = 8  # sur 20 par axe. Sous ce seuil l'axe est repute effondre
                     # et plafonne la decision editoriale, quel que soit le total.

AXES_CONNUS = ["Style", "Sources", "Tracabilite", "Terminologie et nombres", "Lisibilite"]
POIDS_DEFAUT = {axe: 0.2 for axe in AXES_CONNUS}  # 5 axes egaux = comportement 0.7.0 inchange

LARGEUR_BARRE = 30  # caracteres, barre ASCII du rapport texte

# Sous ce nombre de mots, les metriques de lisibilite (ecart-type de longueur
# de phrase, indice LIX) portent trop peu d'echantillon pour signifier quoi que
# ce soit. L'axe est alors declare non evalue plutot que note.
MOTS_MINIMUM_LISIBILITE = 80

SEUILS_TYPE = {  # seuil de score attendu par type de document, sur 100
    "brouillon": 65,
    "rapport": 80,
    "publication": 85,
}


def _mod(fichier, nom):
    spec = importlib.util.spec_from_file_location(nom, os.path.join(ICI, fichier))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


lib = _mod("libelles.py", "scriptorium_libelles")
lint = _mod("lint-style.py", "lint_style")
read = _mod("readability.py", "readability")
vsrc = _mod("verify-sources.py", "verify_sources")
trac = _mod("traceability.py", "traceability")
term = _mod("terminology.py", "terminology")
nums = _mod("numbers.py", "numbers")
aifp = _mod("ai-fingerprint.py", "ai_fingerprint")
coh = _mod("coherence.py", "coherence")


def _axe(depart, regles, langue_affichage=None):
    """regles = liste de (compte, penalite_unitaire, plafond, libelle). Retourne
    (score, deductions). plafond = deduction maximale pour cette regle.

    Le libelle passe par la table VALEURS de libelles.py : il est affiche, pas
    compare. Sans langue_affichage, la chaine francaise d'origine est rendue a
    l'octet pres, ce qui est la sortie JSON."""
    la = lib.resoudre_affichage(langue_affichage)
    score = depart
    deductions = []
    for compte, pen, plafond, libelle in regles:
        if compte > 0:
            d = min(compte * pen, plafond)
            score -= d
            deductions.append(
                f"-{d} {lib.valeur('scorecard.deduction', libelle, la)} "
                f"(x{compte})")
    return max(0, score), deductions


def _normaliser_poids(poids):
    """Renormalise un dict de poids par axe pour qu'il somme exactement a 1.0.

    Bug source (calculate_scores.py, fonction calculate_weighted_average) :
    la fonction divise deja le score pondere par le poids total actif
    (total_score / total_weight), ce qui est la renormalisation correcte et
    suffisante. Elle multiplie ensuite ce resultat une seconde fois par
    (somme de tous les poids declares / poids total actif). Cette seconde
    correction ne s'annule que si les poids declares somment deja exactement
    a 1.0 ; sinon elle compose avec la premiere division et le score depasse
    son echelle propre (exemple source : deux poids a 0,5 chacun mais une
    seule dimension notee a 4/5 rend 8,0/5 au lieu de 4,0/5, cf B2-research.md).
    La correction ici applique une seule division, jamais deux.
    """
    somme = sum(poids.values())
    if somme <= 0:
        raise ValueError("la somme des poids doit etre strictement positive")
    return {axe: v / somme for axe, v in poids.items()}


def _charger_poids(chemin):
    """Charge un fichier JSON de poids par axe. Les 5 axes connus doivent
    tous etre presents : fait precis ou rien, un poids manquant echoue plutot
    que de recevoir une valeur par defaut silencieuse. Une cle inconnue est
    retournee a part pour etre signalee, jamais ignoree en silence."""
    with open(chemin, encoding="utf-8") as f:
        brut = json.load(f)
    manquants = [a for a in AXES_CONNUS if a not in brut]
    if manquants:
        raise ValueError(f"fichier de poids incomplet, axe(s) manquant(s) : {', '.join(manquants)}")
    inconnus = sorted(set(brut) - set(AXES_CONNUS))
    poids = {a: float(brut[a]) for a in AXES_CONNUS}
    if any(v < 0 for v in poids.values()):
        raise ValueError("un poids ne peut pas etre negatif")
    if sum(poids.values()) <= 0:
        raise ValueError("la somme des poids doit etre strictement positive")
    return poids, inconnus


def _total_pondere(axes, poids_normalise):
    """Total sur 100, somme ponderee de chaque axe (fraction de son plafond
    de 20 points) par le poids normalise de l'axe. Poids par defaut egaux
    (0.2 chacun sur 5 axes) : cette formule redonne alors exactement la
    simple somme des scores sur 100, comportement 0.7.0 inchange quand
    --poids n'est pas fourni.

    Un axe non evalue (sa precondition de mesure ne tient pas, par exemple un
    texte trop court pour que la lisibilite veuille dire quelque chose) sort du
    calcul et son poids se redistribue sur les axes reellement mesures. Le
    compter pour zero punirait une mesure absente, le compter pour son plafond
    recompenserait le fait de n'avoir rien mesure : ni l'un ni l'autre. Une
    mesure absente reste absente."""
    mesures = {nom: v for nom, v in axes.items() if v[0] is not None}
    if not mesures:
        return None
    actif = sum(poids_normalise.get(nom, 0.0) for nom in mesures)
    if actif <= 0:
        return None
    brut = sum((score / 20.0) * (poids_normalise.get(nom, 0.0) / actif) * 100.0
               for nom, (score, _) in mesures.items())
    brut = round(brut, 6)
    return int(round(brut)) if brut.is_integer() else round(brut, 1)


def _barre_ascii(score, plafond=20, largeur=LARGEUR_BARRE):
    """Barre proportionnelle a score/plafond, largeur fixe (30 caracteres
    par defaut). Caracteres ASCII purs (# rempli, . vide) plutot qu'un bloc
    Unicode plein : une console Windows en codepage heritage (cp1252) leve
    UnicodeEncodeError sur un caractere hors Latin-1, jamais sur de l'ASCII."""
    if plafond <= 0:
        rempli = 0
    else:
        rempli = max(0, min(largeur, round((score / plafond) * largeur)))
    return "#" * rempli + "." * (largeur - rempli)


def _forces_faiblesses(axes_out):
    """Meilleur et pire axe par score. En cas d'egalite, tous les axes a
    egalite sont nommes plutot qu'un choix arbitraire du premier rencontre
    dans le dict."""
    scores = {nom: a["score"] for nom, a in axes_out.items()
              if a.get("score") is not None}
    if not scores:
        return {"meilleurs_axes": [], "score_meilleur": None,
                "pires_axes": [], "score_pire": None, "egalite_totale": None}
    meilleur = max(scores.values())
    pire = min(scores.values())
    return {
        "meilleurs_axes": [nom for nom, s in scores.items() if s == meilleur],
        "score_meilleur": meilleur,
        "pires_axes": [nom for nom, s in scores.items() if s == pire],
        "score_pire": pire,
        "egalite_totale": meilleur == pire,
    }


def _decision_editoriale(axes, total, plancher, langue_affichage=None):
    """Mappe le score sur une decision a quatre valeurs (accepter, revision
    mineure, revision majeure, refus), plafonnee par le pire axe si un axe
    tombe sous le plancher : une seule dimension effondree peut bloquer malgre
    un bon score global. Le sous-type de refus indique en commentaire est une
    proposition, jamais un verdict ferme : seuls les signaux mesurables (total,
    axe effondre) sont mecaniques, le reste (hors perimetre, premature) exige
    une lecture humaine et n'est jamais deduit du score seul.

    La valeur de decision est machine : elle reste francaise dans toutes les
    langues, run-evals.py la compare litteralement. Seul le commentaire, qui
    est de la prose, suit la langue d'affichage."""
    la = lib.resoudre_affichage(langue_affichage)
    effondres = sorted((nom, a["score"]) for nom, a in axes.items()
                       if a.get("score") is not None and a["score"] < plancher)
    if total is None:
        return {
            "decision": "non evaluable",
            "plancher": plancher,
            "axes_effondres": [],
            "commentaire_sous_type": lib.t("scorecard.aucun_axe_mesurable",
                                           la),
        }

    if total >= 85:
        decision = "accepter"
    elif total >= 70:
        decision = "revision mineure"
    elif total >= 55:
        decision = "revision majeure"
    else:
        decision = "refus"

    rang = {"accepter": 0, "revision mineure": 1, "revision majeure": 2, "refus": 3}
    if effondres:
        pire = min(score for _, score in effondres)
        plafond = "refus" if pire <= plancher // 2 else "revision majeure"
        if rang[plafond] > rang[decision]:
            decision = plafond

    commentaire = None
    if decision == "refus":
        if effondres:
            noms = ", ".join(lib.valeur("scorecard.axe", nom, la)
                             for nom, _ in effondres)
            commentaire = lib.t("scorecard.sous_type_axe_effondre", la,
                                noms=noms)
        else:
            commentaire = lib.t("scorecard.sous_type_defaut_fondamental", la,
                                total=total)

    return {
        "decision": decision,
        "plancher": plancher,
        "axes_effondres": [nom for nom, _ in effondres],
        "commentaire_sous_type": commentaire,
    }


def evaluer(texte, plancher=PLANCHER_DEFAUT, poids=None, seuil_type=None,
            langue=None, langue_affichage=None):
    """Note un texte sur cinq axes.

    langue choisit les motifs de mesure, langue_affichage choisit la langue
    des seules chaines destinees a etre lues (libelles de deduction, motif
    d'axe non evalue, commentaire de decision). Rien de ce sur quoi du code
    branche ne change : verdict, decision, noms d'axes et cles de sortie
    restent francais. Sans langue_affichage, le resultat est celui d'origine a
    l'octet pres, et c'est lui que serialise --format json."""
    # Une seule resolution, partagee par toutes les mesures qui dependent de
    # la langue. La faire deux fois exposerait au cas ou deux scripts ne
    # trancheraient pas pareil sur le meme texte.
    langue = lint.resoudre_langue(texte, langue)
    la = lib.resoudre_affichage(langue_affichage)
    axes = {}

    c = lint.lint_text(texte, None, langue)
    crit = sum(1 for x in c if x["severite"] == "critique")
    maj = sum(1 for x in c if x["severite"] == "majeur")
    mino = sum(1 for x in c if x["severite"] == "mineur")
    nsig = len(aifp.analyser(texte, langue=langue)["signaux"])
    axes["Style"] = _axe(20, [(crit, 7, 20, "ecart critique de style"),
                              (maj, 3, 9, "ecart majeur"),
                              (mino, 1, 4, "ecart mineur"),
                              (nsig, 2, 6, "tic d'ecriture IA")], la)

    v = vsrc.analyser(texte)
    axes["Sources"] = _axe(20, [(len(v["urls_a_nettoyer"]), 4, 8, "URL a nettoyer"),
                                (len(v["doublons"]), 4, 8, "source en double"),
                                (len(v["dois_invalides"]), 3, 6, "DOI douteux")], la)

    t = trac.analyser(texte, langue)
    axes["Tracabilite"] = _axe(20, [
        (len(t["citations_pendantes"]), 5, 10, "citation pendante"),
        (len(t["references_orphelines"]), 2, 6, "reference orpheline"),
        (len(t["figures_appelees_non_definies"]) + len(t["tableaux_appeles_non_definis"]), 3, 6, "appel sans definition"),
        (len(t["figures_definies_non_appelees"]) + len(t["tableaux_definis_non_appeles"]), 2, 4, "objet jamais appele"),
        (len(coh.analyser(texte, langue=langue)["paragraphes_dupliques"]), 4, 8,
         "paragraphe duplique")], la)

    te = term.analyser(texte)
    nu = nums.analyser(texte, langue)
    axes["Terminologie et nombres"] = _axe(20, [
        (len(te["sigles_non_definis"]), 4, 8, "sigle non defini"),
        (len(te["sigles_avant_definition"]), 2, 4, "sigle avant definition"),
        (len(te["variantes_orthographiques"]), 2, 4, "variante orthographique"),
        (len(nu["pourcentages_impossibles"]), 6, 12, "pourcentage impossible"),
        (len(nu["partitions_incoherentes"]), 3, 6, "partition incoherente"),
        (1 if nu["separateur_decimal_mixte"] else 0, 2, 2, "separateur decimal mixte")], la)

    m = read.mesurer(texte, langue)
    non_evalues = {}
    non_mesurees = {}
    if m["mots"] >= MOTS_MINIMUM_LISIBILITE:
        reg = [
            (1 if m["longueur_phrase_ecart_type"] < 5 else 0, 5, 5, "rythme monotone"),
            (1 if m["longueur_phrase_moyenne"] > 28 else 0, 4, 4, "phrases trop longues"),
            (1 if (m["indice_lix"] > 56 or m["indice_lix"] < 30) else 0, 5, 5, "LIX hors bande"),
        ]
        # Le taux de passif peut ne pas avoir ete mesure (langue non couverte,
        # aucune phrase mesurable). La regle sort alors du calcul et l'absence
        # de mesure est nommee dans l'axe : sans cette declaration, l'axe
        # gagnerait quatre points gratuits sans que rien ne le dise.
        if m["taux_passif_approx_pct"] is None:
            non_mesurees["Lisibilite"] = list(m.get("mesures_non_faites") or [])
        else:
            reg.append((1 if m["taux_passif_approx_pct"] > 25 else 0, 4, 4,
                        "trop de passif"))
        reg.append((1 if m["densite_lexicale"] < 0.35 else 0, 3, 3,
                    "densite lexicale faible"))
        axes["Lisibilite"] = _axe(20, reg, la)
    else:
        # Sous ce seuil, l'ecart-type de longueur de phrase et l'indice LIX ne
        # veulent rien dire. L'axe sort du calcul plutot que de rendre 20 sur
        # 20 par absence de mesure, ce qui gonflait le total d'un texte court.
        axes["Lisibilite"] = (None, [])
        non_evalues["Lisibilite"] = lib.t(
            "scorecard.motif_texte_court", la, mots=m["mots"],
            seuil=MOTS_MINIMUM_LISIBILITE)

    poids_brut = dict(poids) if poids is not None else dict(POIDS_DEFAUT)
    poids_normalise = _normaliser_poids(poids_brut)
    total = _total_pondere(axes, poids_normalise)

    if total is None:
        verdict = "Non evaluable"
    elif total >= 85:
        verdict = "Pret"
    elif total >= 70:
        verdict = "A reviser"
    else:
        verdict = "A refondre"

    axes_out = {}
    for k, (s, d) in axes.items():
        entree = {"score": s, "deductions": d}
        if k in non_evalues:
            entree["non_evalue"] = True
            entree["motif"] = non_evalues[k]
        if non_mesurees.get(k):
            entree["mesures_non_faites"] = non_mesurees[k]
        axes_out[k] = entree

    resultat = {
        "langue": langue,
        "axes": axes_out,
        "total": total,
        "verdict": verdict,
        "decision_editoriale": _decision_editoriale(axes_out, total, plancher,
                                                    la),
        "forces_faiblesses": _forces_faiblesses(axes_out),
        "poids": {
            "personnalise": poids is not None,
            "brut": poids_brut,
            "normalise": poids_normalise,
        },
    }

    if seuil_type:
        seuil_cible = SEUILS_TYPE[seuil_type]
        resultat["seuil_type"] = {
            "type": seuil_type,
            "seuil": seuil_cible,
            "atteint": total >= seuil_cible,
        }
    else:
        resultat["seuil_type"] = None

    return resultat


def trajectoire(a, b):
    """Delta par axe entre deux rapports JSON produits par --format json
    (revue puis re-revue). Regression : delta sous -3 sur un axe. Ne compare
    que les axes presents dans les deux rapports, un axe absent d'un cote est
    signale a part plutot que suppose a zero.

    Le champ arret_anticipe signale un gain marginal (delta_total sous +3
    points) sans aucune regression : continuer a boucler sur la meme
    correction a peu de chances d'apporter plus, voir chemins-defaillance.md
    (scenario D6) pour le chemin de recuperation propose a l'utilisateur."""
    axes_a, axes_b = a.get("axes", {}), b.get("axes", {})
    communs = [n for n in axes_a if n in axes_b]
    ignores = sorted(set(axes_a) ^ set(axes_b))

    deltas = []
    non_mesures = []
    for n in communs:
        sa, sb = axes_a[n]["score"], axes_b[n]["score"]
        if sa is None or sb is None:
            # Un axe non evalue d'un cote ne produit pas de delta : le comparer
            # a zero fabriquerait une regression ou un gain qui n'existe pas.
            non_mesures.append(n)
            continue
        d = sb - sa
        deltas.append({"axe": n, "avant": sa, "apres": sb, "delta": d, "regression": d < -3})

    total_a, total_b = a.get("total"), b.get("total")
    if total_a is None or total_b is None:
        delta_total = None
    else:
        delta_total = total_b - total_a
    regressions = [d["axe"] for d in deltas if d["regression"]]

    return {
        "deltas": deltas,
        "axes_ignores": ignores,
        "axes_non_mesures": non_mesures,
        "total_avant": total_a,
        "total_apres": total_b,
        "delta_total": delta_total,
        "regressions": regressions,
        "verdict_avant": a.get("verdict"),
        "verdict_apres": b.get("verdict"),
        "arret_anticipe": (delta_total is not None and delta_total < 3
                           and not regressions),
    }


def rapport_texte(r, langue_affichage=None):
    """Rapport lisible. Les chaines deja portees par r (deductions, motif,
    commentaire) sont rendues telles quelles : elles ont ete composees dans la
    langue d'affichage par evaluer(). Ce qui est traduit ici, ce sont les
    valeurs machine (verdict, decision, noms d'axes) et le decor du rapport."""
    la = lib.resoudre_affichage(langue_affichage)
    verdict = lib.valeur("scorecard.verdict", r["verdict"], la)
    entete = (lib.t("scorecard.entete", la, total=r["total"], verdict=verdict)
              if r["total"] is not None
              else lib.t("scorecard.entete_sans_total", la, verdict=verdict))
    if r.get("seuil_type"):
        st = r["seuil_type"]
        tag = lib.t("scorecard.seuil_atteint" if st["atteint"]
                    else "scorecard.seuil_non_atteint", la)
        entete += lib.t("scorecard.seuil", la, type=st["type"],
                        seuil=st["seuil"], tag=tag)
    out = [entete,
           "  " + lib.t("scorecard.langue_notee", la, langue=r.get("langue")),
           ""]
    for nom, a in r["axes"].items():
        libelle_axe = lib.valeur("scorecard.axe", nom, la)
        if a.get("non_evalue"):
            out.append(f"  {libelle_axe:26} "
                       + lib.t("scorecard.axe_non_evalue", la))
            out.append(f"      {a.get('motif', '')}")
            continue
        out.append(f"  {libelle_axe:26} {a['score']:>2}/20  "
                   f"{_barre_ascii(a['score'])}")
        for d in a["deductions"]:
            out.append(f"      {d}")
        for nf in a.get("mesures_non_faites", []):
            out.append("      " + lib.t(
                "scorecard.mesure_non_faite", la, mesure=nf["mesure"],
                motif=lib.motif(nf["motif"], la)))
    out.append("")

    ff = r["forces_faiblesses"]
    if ff["egalite_totale"] is None:
        out.append("  " + lib.t("scorecard.aucun_axe_mesure", la))
    elif ff["egalite_totale"]:
        out.append("  " + lib.t("scorecard.egalite", la,
                                score=ff["score_meilleur"]))
    else:
        out.append("  " + lib.t(
            "scorecard.forces", la, score=ff["score_meilleur"],
            axes=", ".join(lib.valeur("scorecard.axe", n, la)
                           for n in ff["meilleurs_axes"])))
        out.append("  " + lib.t(
            "scorecard.faiblesses", la, score=ff["score_pire"],
            axes=", ".join(lib.valeur("scorecard.axe", n, la)
                           for n in ff["pires_axes"])))

    out.append("")
    out.append("  " + lib.t("scorecard.calcul", la))
    p = r["poids"]
    if p["personnalise"]:
        out.append("  " + lib.t("scorecard.poids_personnalises", la))
        for nom in r["axes"]:
            out.append("      %-26s " % lib.valeur("scorecard.axe", nom, la)
                       + lib.t("scorecard.poids_ligne", la,
                               brut="%.3f" % p["brut"][nom],
                               normalise="%.3f" % p["normalise"][nom]))

    de = r["decision_editoriale"]
    out.append("")
    out.append("  " + lib.t(
        "scorecard.decision_editoriale", la, plancher=de["plancher"],
        decision=lib.valeur("scorecard.decision", de["decision"], la)))
    if de["axes_effondres"]:
        out.append("      " + lib.t(
            "scorecard.axes_effondres", la,
            axes=", ".join(lib.valeur("scorecard.axe", n, la)
                           for n in de["axes_effondres"])))
    if de["commentaire_sous_type"]:
        out.append(f"      {de['commentaire_sous_type']}")
    return "\n".join(out)


def rapport_trajectoire_texte(t, langue_affichage=None):
    la = lib.resoudre_affichage(langue_affichage)

    def _axes(noms):
        return ", ".join(lib.valeur("scorecard.axe", n, la) for n in noms)

    out = [lib.t("scorecard.traj_entete", la, avant=t["total_avant"],
                 apres=t["total_apres"],
                 delta="%+g" % t["delta_total"]), ""]
    for d in t["deltas"]:
        marque = ("  " + lib.t("scorecard.traj_regression", la)
                  if d["regression"] else "")
        out.append("  %-26s %2s -> %2s (delta %+d)%s"
                   % (lib.valeur("scorecard.axe", d["axe"], la), d["avant"],
                      d["apres"], d["delta"], marque))
    if t["axes_ignores"]:
        out.append("")
        out.append("  " + lib.t("scorecard.traj_axes_ignores", la,
                                axes=_axes(t["axes_ignores"])))
    out.append("")
    if t["regressions"]:
        out.append("  " + lib.t("scorecard.traj_point_controle", la,
                                axes=_axes(t["regressions"])))
        out.append("  " + lib.t("scorecard.traj_options_regression", la))
    elif t["arret_anticipe"]:
        out.append("  " + lib.t("scorecard.traj_arret", la,
                                delta="%+g" % t["delta_total"]))
        out.append("  " + lib.t("scorecard.traj_options_arret", la))
    else:
        out.append("  " + lib.t("scorecard.traj_normal", la))
    out.append("  " + lib.t(
        "scorecard.traj_verdict", la,
        avant=lib.valeur("scorecard.verdict", t["verdict_avant"], la),
        apres=lib.valeur("scorecard.verdict", t["verdict_apres"], la)))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Scorecard deterministe.")
    ap.add_argument("fichier", nargs="?", default=None)
    ap.add_argument("--format", choices=["text", "json"], default="text")
    ap.add_argument("--plancher", type=int, default=PLANCHER_DEFAUT,
                     help=f"seuil par axe sur 20 (defaut {PLANCHER_DEFAUT})")
    ap.add_argument("--poids", metavar="FICHIER.json", default=None,
                     help="poids personnalises par axe, JSON, renormalise a somme 1 "
                          "(les 5 axes doivent tous etre presents)")
    ap.add_argument("--seuil-type", choices=sorted(SEUILS_TYPE), default=None,
                     help="teinte le verdict avec le seuil du type de document ("
                          + ", ".join(f"{k} {v}" for k, v in SEUILS_TYPE.items()) + ")")
    ap.add_argument("--langue", choices=["fr", "en", "auto"], default=None,
                     help="langue de notation, meme option que lint-style.py. "
                          "Sans l'option : le pragme lint-style:langue du "
                          "document, sinon fr. auto lance la detection")
    ap.add_argument("--langue-affichage", choices=["fr", "en"], default=None,
                     help="langue des libelles du rapport texte. Sans "
                          "l'option : la langue de notation retenue. La sortie "
                          "JSON reste francaise quoi qu'il arrive")
    ap.add_argument("--trajectoire", nargs=2, metavar=("RAPPORT_A", "RAPPORT_B"),
                     help="compare deux rapports JSON (sorties de --format json)")
    a = ap.parse_args(argv)
    la_option = a.langue_affichage

    if a.trajectoire:
        chemin_a, chemin_b = a.trajectoire
        rapport_a = json.load(open(chemin_a, encoding="utf-8"))
        rapport_b = json.load(open(chemin_b, encoding="utf-8"))
        t = trajectoire(rapport_a, rapport_b)
        # Les deux rapports portent leur propre langue de notation ; celle du
        # second fait foi, c'est l'etat courant du document.
        la = lib.resoudre_affichage(la_option, rapport_b.get("langue"))
        print(json.dumps(t, ensure_ascii=False, indent=2)
              if a.format == "json" else rapport_trajectoire_texte(t, la))
        return 0

    if not a.fichier:
        print(lib.t("scorecard.err_fichier_requis",
                    lib.resoudre_affichage(la_option)), file=sys.stderr)
        return 2

    poids_brut = None
    if a.poids:
        try:
            poids_brut, inconnus = _charger_poids(a.poids)
        except (OSError, ValueError, json.JSONDecodeError) as e:
            print(lib.t("scorecard.err_poids",
                        lib.resoudre_affichage(la_option), erreur=e),
                  file=sys.stderr)
            return 2
        if inconnus:
            print(lib.t("scorecard.avert_axes_inconnus",
                        lib.resoudre_affichage(la_option),
                        axes=", ".join(inconnus)), file=sys.stderr)

    texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    # Le JSON ne se traduit pas : le jeu d'or et les evals le lisent.
    if a.format == "json":
        r = evaluer(texte, plancher=a.plancher, poids=poids_brut,
                    seuil_type=a.seuil_type, langue=a.langue)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    la = lib.resoudre_affichage(la_option,
                                lint.resoudre_langue(texte, a.langue))
    r = evaluer(texte, plancher=a.plancher, poids=poids_brut,
                seuil_type=a.seuil_type, langue=a.langue, langue_affichage=la)
    print(rapport_texte(r, la))
    return 0


if __name__ == "__main__":
    sys.exit(main())
