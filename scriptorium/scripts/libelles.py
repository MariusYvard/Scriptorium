#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Couche d'affichage bilingue de Scriptorium.

Le plugin mesure en deux langues depuis 0.13.0, mais rend compte en francais
seulement. Ce module porte les libelles des deux langues et la resolution qui
les choisit. Il ne touche a aucune valeur machine.

Ce que ce module ne fait PAS, et pourquoi. Les verdicts fermes (« conforme »,
« ecarts majeurs », « fuites confirmees », « licence inconnue », « autorisation
requise », « lecture fiable », « Pret », « A reviser », « refus »...) ne sont
pas de l'affichage : emprunts.py branche sur les verdicts de check-droits.py,
plusieurs modules de evals/cas/ les comparent litteralement et tools/gold.py
les confronte aux etiquettes gelees de evals/gold/*/manifeste.json. Ils
restent donc les chaines francaises actuelles dans les structures de donnees
et dans les sorties JSON, en francais comme en anglais. Seul le LIBELLE
AFFICHE change de langue, et il passe par la table VALEURS, explicite : un
verdict ajoute sans libelle ressort marque plutot que traduit en silence.

Forme retenue : une cle plate a espace de noms par script (« scorecard.entete »,
« traceability.titre »), chaque cle portant un dictionnaire langue -> chaine.
Trois raisons. L'espace de noms rend le cablage verifiable script par script,
c'est ce que lit la garde de evals/cas/affichage.py. Le couple fr/en tenu sur
une seule entree rend une omission visible a la lecture, la ou deux blocs par
langue la cacheraient. Le formatage se fait a parametres NOMMES (« {total} »)
et non positionnels : l'ordre des mots change d'une langue a l'autre, un
format positionnel se casserait a la premiere inversion.

Bibliotheque standard seule. La langue se resout avec le mecanisme existant de
lint-style.py (resoudre_langue), jamais avec un second mecanisme.

Module importable : t(cle, langue, **params), valeur(espace, machine, langue),
motif(motif_fr, langue), cles_manquantes(langue), valeurs_sans_libelle(langue).
"""
import re

LANGUES = ("fr", "en")
LANGUE_DEFAUT = "fr"

# Un libelle absent d'une langue retombe sur le francais en le DECLARANT :
# l'utilisateur voit qu'il lit une chaine non traduite, il ne recoit ni une
# cle brute ni une exception. Une valeur machine absente de sa table sort
# marquee autrement, pour que les deux manques ne se confondent pas.
MARQUE_REPLI = "[fr] "
MARQUE_INCONNU = "[?] "


# --- Libelles d'affichage ---------------------------------------------------
# Une entree par cle, les deux langues cote a cote. Les chaines francaises sont
# celles deja imprimees par les scripts, recopiees a l'octet pres : c'est ce
# qui garantit qu'un rapport francais ne bouge pas.

LIBELLES = {

    # lint-style.py
    "lint.titre": {
        "fr": "Linter de style maison : {titre}",
        "en": "House style linter: {titre}"},
    "lint.langue_analysee": {
        "fr": "langue analysée : {langue}",
        "en": "analysis language: {langue}"},
    "lint.comptes": {
        "fr": "critiques={critiques}  majeurs={majeurs}  mineurs={mineurs}",
        "en": "critical={critiques}  major={majeurs}  minor={mineurs}"},
    "lint.aucun_ecart": {
        "fr": "Aucun écart détecté.",
        "en": "No deviation found."},
    "lint.constat": {
        "fr": "L{ligne}:{colonne} ({regle}) « {trouve} » -> {message}",
        "en": "L{ligne}:{colonne} ({regle}) \"{trouve}\" -> {message}"},
    "lint.erreur_lecture": {
        "fr": "Erreur de lecture : {erreur}",
        "en": "Read error: {erreur}"},
    "lint.msg.orthographe_melangee": {
        "fr": "Orthographes britannique et américaine mêlées dans le même "
              "document. Choisir une variante et la tenir partout.",
        "en": "British and American spellings mixed in the same document. "
              "Pick one variant and keep it throughout."},
    "lint.extrait.orthographe_melangee": {
        "fr": "britannique : {gb} / américain : {us}",
        "en": "British: {gb} / American: {us}"},
    "lint.msg.tiret_densite": {
        "fr": "Tiret cadratin employé {n} fois pour {mots} mots. La "
              "ponctuation est légitime en anglais, sa densité est un marqueur "
              "d'écriture assistée : en garder deux ou trois par document.",
        "en": "Em dash used {n} times for {mots} words. The punctuation is "
              "legitimate in English, its density is a marker of assisted "
              "writing: keep two or three per document."},
    "lint.extrait.tiret_densite": {
        "fr": "densité mesurée : {densite} pour mille mots",
        "en": "measured density: {densite} per thousand words"},
    "lint.msg.passif": {
        "fr": "Voix passive sur {n} phrases sur {total}. La section Methods "
              "l'admet (APA 7, section 4.13), le reste du texte gagne au "
              "sujet explicite.",
        "en": "Passive voice in {n} sentences out of {total}. The Methods "
              "section allows it (APA 7, section 4.13), the rest of the text "
              "gains from an explicit subject."},
    "lint.extrait.passif": {
        "fr": "part mesurée : {pct} %",
        "en": "measured share: {pct} %"},

    # scorecard.py
    "scorecard.entete": {
        "fr": "Scorecard : {total}/100, verdict {verdict}",
        "en": "Scorecard: {total}/100, verdict {verdict}"},
    "scorecard.entete_sans_total": {
        "fr": "Scorecard : {verdict}",
        "en": "Scorecard: {verdict}"},
    "scorecard.seuil": {
        "fr": " | seuil {type} {seuil}/100 : {tag}",
        "en": " | {type} threshold {seuil}/100: {tag}"},
    "scorecard.seuil_atteint": {"fr": "atteint", "en": "met"},
    "scorecard.seuil_non_atteint": {"fr": "non atteint", "en": "not met"},
    "scorecard.langue_notee": {
        "fr": "langue notee : {langue}",
        "en": "scored language: {langue}"},
    "scorecard.axe_non_evalue": {
        "fr": "non evalue, hors calcul",
        "en": "not assessed, outside the calculation"},
    "scorecard.mesure_non_faite": {
        "fr": "mesure non faite : {mesure} ({motif})",
        "en": "measurement not made: {mesure} ({motif})"},
    "scorecard.aucun_axe_mesure": {
        "fr": "Aucun axe mesure, ni force ni faiblesse a nommer.",
        "en": "No axis measured, no strength or weakness to name."},
    "scorecard.egalite": {
        "fr": "Tous les axes a egalite ({score}/20).",
        "en": "All axes tied ({score}/20)."},
    "scorecard.forces": {
        "fr": "Force(s) : {axes} ({score}/20)",
        "en": "Strength(s): {axes} ({score}/20)"},
    "scorecard.faiblesses": {
        "fr": "Faiblesse(s) : {axes} ({score}/20)",
        "en": "Weakness(es): {axes} ({score}/20)"},
    "scorecard.calcul": {
        "fr": "Calcul : chaque axe part de 20, penalites fixes plafonnees, "
              "somme ponderee sur 100.",
        "en": "Calculation: each axis starts from 20, fixed penalties capped, "
              "weighted sum out of 100."},
    "scorecard.poids_personnalises": {
        "fr": "Poids personnalises (renormalisation a somme 1.0, une seule "
              "division) :",
        "en": "Custom weights (renormalised to sum 1.0, a single division):"},
    "scorecard.poids_ligne": {
        "fr": "brut {brut} -> normalise {normalise}",
        "en": "raw {brut} -> normalised {normalise}"},
    "scorecard.decision_editoriale": {
        "fr": "Decision editoriale (plancher {plancher}/20 par axe) : "
              "{decision}",
        "en": "Editorial decision (floor {plancher}/20 per axis): {decision}"},
    "scorecard.axes_effondres": {
        "fr": "axe(s) sous le plancher : {axes}",
        "en": "axis or axes below the floor: {axes}"},

    # scorecard.py : chaines portees par la structure de donnees, traduites
    # au moment de produire le rapport, jamais dans le JSON.
    "scorecard.motif_texte_court": {
        "fr": "texte de {mots} mots, sous le seuil de {seuil} ou la "
              "lisibilite se mesure",
        "en": "text of {mots} words, below the {seuil}-word threshold where "
              "readability can be measured"},
    "scorecard.sous_type_axe_effondre": {
        "fr": "sous-type propose : a retravailler en profondeur (axe "
              "effondre sous plancher/2 : {noms})",
        "en": "proposed sub-type: needs deep rework (axis collapsed below "
              "floor/2: {noms})"},
    "scorecard.sous_type_defaut_fondamental": {
        "fr": "sous-type propose : defaut fondamental (score global {total} "
              "tres bas) ; a confirmer en lecture humaine, hors perimetre et "
              "premature ne se deduisent pas du score seul",
        "en": "proposed sub-type: fundamental flaw (overall score {total} "
              "very low); to be confirmed by human reading, out of scope and "
              "premature cannot be inferred from the score alone"},
    "scorecard.aucun_axe_mesurable": {
        "fr": "aucun axe n'a pu etre mesure, aucune decision editoriale "
              "n'est deduite",
        "en": "no axis could be measured, no editorial decision is inferred"},

    # scorecard.py : trajectoire entre deux rapports
    "scorecard.traj_entete": {
        "fr": "Trajectoire : {avant}/100 vers {apres}/100 (delta total "
              "{delta})",
        "en": "Trajectory: {avant}/100 to {apres}/100 (total delta {delta})"},
    "scorecard.traj_regression": {"fr": "[REGRESSION]", "en": "[REGRESSION]"},
    "scorecard.traj_axes_ignores": {
        "fr": "Axes ignores (absents d'un rapport) : {axes}",
        "en": "Axes ignored (absent from one report): {axes}"},
    "scorecard.traj_point_controle": {
        "fr": "Point de controle : regression de plus de 3 points sur {axes}.",
        "en": "Checkpoint: regression of more than 3 points on {axes}."},
    "scorecard.traj_options_regression": {
        "fr": "Trois options : accepter le compromis, reviser cible sur l'axe "
              "regresse,\n  ou restaurer la version anterieure de la section "
              "concernee.",
        "en": "Three options: accept the trade-off, revise narrowly on the "
              "regressed axis,\n  or restore the previous version of the "
              "section concerned."},
    "scorecard.traj_arret": {
        "fr": "Note d'arret anticipe : le gain total est de {delta} point(s), "
              "sous le seuil de +3 et sans regression.",
        "en": "Early-stop note: the total gain is {delta} point(s), below the "
              "+3 threshold and without regression."},
    "scorecard.traj_options_arret": {
        "fr": "Continuer a boucler sur la meme correction a peu de chances "
              "d'apporter plus.\n  Trois options : accepter l'etat actuel, "
              "cibler un seul axe precis avec l'utilisateur,\n  ou revoir le "
              "seuil ensemble (voir chemins-defaillance.md, scenario D6).",
        "en": "Looping further on the same fix is unlikely to bring more."
              "\n  Three options: accept the current state, target a single "
              "precise axis with the user,\n  or revisit the threshold "
              "together (see chemins-defaillance.md, scenario D6)."},
    "scorecard.traj_normal": {
        "fr": "Aucune regression de plus de 3 points : trajectoire normale.",
        "en": "No regression of more than 3 points: normal trajectory."},
    "scorecard.traj_verdict": {
        "fr": "Verdict : {avant} -> {apres}",
        "en": "Verdict: {avant} -> {apres}"},
    "scorecard.err_fichier_requis": {
        "fr": "Erreur : fichier requis (sauf en mode --trajectoire).",
        "en": "Error: a file is required (except in --trajectoire mode)."},
    "scorecard.err_poids": {
        "fr": "Erreur de poids : {erreur}",
        "en": "Weight error: {erreur}"},
    "scorecard.avert_axes_inconnus": {
        "fr": "Avertissement : axe(s) ignore(s) dans le fichier de poids : "
              "{axes}",
        "en": "Warning: axis or axes ignored in the weight file: {axes}"},

    # readability.py
    "readability.titre": {
        "fr": "Métriques de lisibilité", "en": "Readability metrics"},
    "readability.langue_mesuree": {
        "fr": "langue mesurée : {langue}",
        "en": "measured language: {langue}"},
    "readability.non_mesure": {"fr": "non mesuré", "en": "not measured"},
    "readability.lecture": {"fr": "Lecture :", "en": "Reading:"},
    "readability.m.mots": {"fr": "Mots", "en": "Words"},
    "readability.m.phrases": {"fr": "Phrases", "en": "Sentences"},
    "readability.m.paragraphes": {"fr": "Paragraphes", "en": "Paragraphs"},
    "readability.m.longueur_phrase_moyenne": {
        "fr": "Longueur phrase (moy.)", "en": "Sentence length (mean)"},
    "readability.m.longueur_phrase_ecart_type": {
        "fr": "Longueur phrase (écart-type)",
        "en": "Sentence length (std. dev.)"},
    "readability.m.phrases_longues_sup30_pct": {
        "fr": "Phrases > 30 mots (%)", "en": "Sentences > 30 words (%)"},
    "readability.m.phrases_courtes_inf8_pct": {
        "fr": "Phrases < 8 mots (%)", "en": "Sentences < 8 words (%)"},
    "readability.m.phrases_par_paragraphe_moyenne": {
        "fr": "Phrases / paragraphe (moy.)",
        "en": "Sentences / paragraph (mean)"},
    "readability.m.densite_lexicale": {
        "fr": "Densité lexicale (TTR)", "en": "Lexical density (TTR)"},
    "readability.m.taux_passif_approx_pct": {
        "fr": "Passif approx. (%)", "en": "Approx. passive (%)"},
    "readability.m.indice_lix": {"fr": "Indice LIX", "en": "LIX index"},
    "readability.n.rythme_monotone": {
        "fr": "Écart-type faible : rythme monotone, varier la longueur des "
              "phrases.",
        "en": "Low standard deviation: monotonous rhythm, vary sentence "
              "length."},
    "readability.n.phrases_longues": {
        "fr": "Phrases longues en moyenne : fatigue l'attention, intercaler "
              "des phrases courtes.",
        "en": "Long sentences on average: tiring to read, interleave short "
              "sentences."},
    "readability.n.peu_de_courtes": {
        "fr": "Peu de phrases courtes : réserver des phrases brèves aux "
              "messages clés.",
        "en": "Few short sentences: save brief sentences for key messages."},
    "readability.n.lix_eleve": {
        "fr": "LIX élevé (texte difficile), acceptable pour un lectorat "
              "expert, lourd sinon.",
        "en": "High LIX (difficult text), acceptable for an expert "
              "readership, heavy otherwise."},
    "readability.n.lix_bas": {
        "fr": "LIX bas (texte très simple), vérifier que la précision n'est "
              "pas sacrifiée.",
        "en": "Low LIX (very simple text), check that precision is not "
              "sacrificed."},
    "readability.n.densite_faible": {
        "fr": "Densité lexicale faible : répétitions probables, varier le "
              "vocabulaire.",
        "en": "Low lexical density: repetitions likely, vary the "
              "vocabulary."},
    "readability.n.mesure_non_faite": {
        "fr": "Mesure non faite ({mesure}) : {motif}.",
        "en": "Measurement not made ({mesure}): {motif}."},
    "readability.n.passif_eleve": {
        "fr": "Taux de passif élevé : préférer des verbes d'action quand "
              "c'est possible.",
        "en": "High passive rate: prefer action verbs where possible."},
    "readability.n.dans_les_bornes": {
        "fr": "Rythme et lisibilité dans les bornes attendues.",
        "en": "Rhythm and readability within the expected bounds."},
    "readability.erreur_lecture": {
        "fr": "Erreur de lecture : {erreur}",
        "en": "Read error: {erreur}"},

    # traceability.py
    "traceability.titre": {"fr": "Tracabilite", "en": "Traceability"},
    "traceability.langue_analysee": {
        "fr": "langue analysee : {langue}",
        "en": "analysis language: {langue}"},
    "traceability.biblio": {
        "fr": "biblio presente : {presente} | references definies : {n}",
        "en": "bibliography present: {presente} | references defined: {n}"},
    "traceability.tags": {
        "fr": "tags [LACUNE MATERIELLE] : {lacune} | tags [PREUVE FAIBLE] : "
              "{preuve}",
        "en": "[LACUNE MATERIELLE] tags: {lacune} | [PREUVE FAIBLE] tags: "
              "{preuve}"},
    "traceability.objets_numerotes": {
        "fr": "objets numerotes : {compte}",
        "en": "numbered objects: {compte}"},
    "traceability.objet_compte": {
        "fr": "{objet} : {n}", "en": "{objet}: {n}"},
    "traceability.aucun_probleme": {
        "fr": "Aucun probleme de tracabilite.",
        "en": "No traceability problem."},
    "traceability.repartition": {
        "fr": "Repartition par section :",
        "en": "Breakdown by section:"},
    "traceability.repartition_ligne": {
        "fr": "{titre} : lacune={lacune} preuve_faible={preuve}",
        "en": "{titre}: gap={lacune} weak_evidence={preuve}"},
    "traceability.p.citations_pendantes": {
        "fr": "Citations pendantes (citees, absentes de la biblio) : {n}",
        "en": "Dangling citations (cited, absent from the bibliography): {n}"},
    "traceability.p.references_orphelines": {
        "fr": "References orphelines (listees, jamais citees) : {n}",
        "en": "Orphan references (listed, never cited): {n}"},
    "traceability.p.figures_appelees": {
        "fr": "Figures appelees mais non definies : {n}",
        "en": "Figures called but not defined: {n}"},
    "traceability.p.figures_definies": {
        "fr": "Figures definies mais jamais appelees : {n}",
        "en": "Figures defined but never called: {n}"},
    "traceability.p.tableaux_appeles": {
        "fr": "Tableaux appeles mais non definis : {n}",
        "en": "Tables called but not defined: {n}"},
    "traceability.p.tableaux_definis": {
        "fr": "Tableaux definis mais jamais appeles : {n}",
        "en": "Tables defined but never called: {n}"},
    "traceability.p.equations_appelees": {
        "fr": "Equations appelees mais non definies : {n}",
        "en": "Equations called but not defined: {n}"},
    "traceability.p.equations_definies": {
        "fr": "Equations definies mais jamais appelees : {n}",
        "en": "Equations defined but never called: {n}"},
    "traceability.p.annexes_appelees": {
        "fr": "Annexes appelees mais non definies : {n}",
        "en": "Appendices called but not defined: {n}"},
    "traceability.p.annexes_definies": {
        "fr": "Annexes definies mais jamais appelees : {n}",
        "en": "Appendices defined but never called: {n}"},
    "traceability.p.tags_mal_formes": {
        "fr": "Tags de lacune mal formes (casse non conforme) : {n}",
        "en": "Malformed gap tags (non-compliant case): {n}"},
    "traceability.a.numero_duplique": {
        "fr": "Numeros de {objet} en double (plusieurs legendes, un seul "
              "numero) : {numeros}",
        "en": "Duplicate {objet} numbers (several captions, a single "
              "number): {numeros}"},
    "traceability.a.numero_manquant": {
        "fr": "Saut dans la suite des {objet} (numero jamais defini) : "
              "{numeros}",
        "en": "Gap in the {objet} sequence (number never defined): "
              "{numeros}"},
    "traceability.a.ne_commence_pas_a_un": {
        "fr": "La suite des {objet} ne commence pas a 1 : premier numero "
              "{numeros}",
        "en": "The {objet} sequence does not start at 1: first number "
              "{numeros}"},
    "traceability.a.notation_mixte": {
        "fr": "Numerotation des {objet} melangee (chiffres et lettres) : "
              "{numeros}",
        "en": "Mixed {objet} numbering (digits and letters): {numeros}"},

    # verify-sources.py
    "verify.titre": {
        "fr": "Vérificateur de sources", "en": "Source verifier"},
    "verify.comptes": {
        "fr": "URL uniques={urls}  à nettoyer={sales}  doublons={doublons}"
              "  DOI={dois}  DOI invalides={invalides}",
        "en": "unique URLs={urls}  to clean={sales}  duplicates={doublons}"
              "  DOIs={dois}  invalid DOIs={invalides}"},
    "verify.urls_a_nettoyer": {
        "fr": "URL avec paramètres de suivi :",
        "en": "URLs with tracking parameters:"},
    "verify.doublons": {"fr": "Doublons :", "en": "Duplicates:"},
    "verify.dois_douteux": {
        "fr": "DOI de syntaxe douteuse :", "en": "DOIs of doubtful syntax:"},
    "verify.paliers": {
        "fr": "Paliers de domaine (indice mécanique, sans réseau) :",
        "en": "Domain tiers (mechanical hint, no network):"},
    "verify.resolution": {
        "fr": "Résolution réseau :", "en": "Network resolution:"},
    "verify.lien_ok": {"fr": "OK", "en": "OK"},
    "verify.lien_echec": {"fr": "ECHEC", "en": "FAIL"},
    "verify.triangulation": {
        "fr": "Triangulation multi-index (verdict par DOI) :",
        "en": "Multi-index triangulation (verdict per DOI):"},
    "verify.retractation": {
        "fr": "Statut de rétractation (fait distinct de l'existence) :",
        "en": "Retraction status (a fact distinct from existence):"},
    "verify.retractation_ligne": {
        "fr": "(déclaré par {sources}{avis}{date})",
        "en": "(declared by {sources}{avis}{date})"},
    "verify.retractation_avis": {
        "fr": ", avis {doi}", "en": ", notice {doi}"},
    "verify.retractation_inconnue": {
        "fr": "Statut de rétractation inconnu pour {n} DOI : aucun index "
              "consulté ne le déclare, ce qui n'est pas une preuve d'absence "
              "de rétractation.",
        "en": "Retraction status unknown for {n} DOIs: no index consulted "
              "declares it, which is not proof that no retraction exists."},
    "verify.contamination": {
        "fr": "Signaux de contamination (preprints récents) :",
        "en": "Contamination signals (recent preprints):"},
    "verify.contamination_ligne": {
        "fr": "{identifiant} (année estimée {annee}) : {signal}",
        "en": "{identifiant} (estimated year {annee}): {signal}"},
    "verify.erreur_lecture": {
        "fr": "Erreur de lecture : {erreur}",
        "en": "Read error: {erreur}"},
    "verify.d.titres_concordants": {
        "fr": "titres concordants entre {n} index (similarite {sim})",
        "en": "matching titles across {n} indexes (similarity {sim})"},
    "verify.d.titres_discordants": {
        "fr": "titres discordants entre index (similarite {sim} < {seuil})",
        "en": "diverging titles across indexes (similarity {sim} < {seuil})"},
    "verify.d.resolu_seul": {
        "fr": "resolu par {index} seul, non trouve par {manques}",
        "en": "resolved by {index} alone, not found by {manques}"},
    "verify.d.resolu_unique_index": {
        "fr": "resolu par {index} (seul index consulte avec succes)",
        "en": "resolved by {index} (only index queried successfully)"},
    "verify.d.non_trouve_plusieurs": {
        "fr": "non trouve independamment par {n} index ({index})",
        "en": "not found independently by {n} indexes ({index})"},
    "verify.d.non_trouve_unique": {
        "fr": "non trouve par le seul index consulte ({index}), a verifier "
              "autrement",
        "en": "not found by the only index queried ({index}), to be checked "
              "another way"},
    "verify.d.aucun_index": {
        "fr": "aucun index consulte avec succes (reseau indisponible, cles "
              "absentes)",
        "en": "no index queried successfully (network unavailable, keys "
              "missing)"},
    "verify.s.non_verifie": {
        "fr": "non verifie (Semantic Scholar injoignable)",
        "en": "not checked (Semantic Scholar unreachable)"},
    "verify.s.retrouve": {
        "fr": "preprint recent, retrouve dans un index (signal reduit)",
        "en": "recent preprint, found in an index (signal reduced)"},
    "verify.s.absent": {
        "fr": "preprint recent absent de l'index consulte : a verifier "
              "manuellement",
        "en": "recent preprint absent from the index queried: to be checked "
              "manually"},
    "verify.s.hors_reseau": {
        "fr": "preprint recent, --reseau desactive : a verifier manuellement",
        "en": "recent preprint, --reseau disabled: to be checked manually"},

    # audit-doc.py
    "audit.entete": {
        "fr": "AUDIT CONSOLIDE — scorecard {total}/100 ({verdict})",
        "en": "CONSOLIDATED AUDIT: scorecard {total}/100 ({verdict})"},
    "audit.empreinte": {"fr": "Empreinte IA :", "en": "AI fingerprint:"},
    "audit.aucun_signal": {"fr": "aucun signal", "en": "no signal"},
    "audit.coherence": {"fr": "Coherence :", "en": "Coherence:"},
    "audit.aucune_redite": {"fr": "aucune redite", "en": "no repetition"},
    "audit.tableaux": {"fr": "Tableaux :", "en": "Tables:"},
    "audit.aucun_probleme": {"fr": "aucun probleme", "en": "no problem"},
    # Les trois sections ci-dessus viennent de scripts non encore cables. Une
    # section non traduite se declare, elle ne se maquille pas : sans cette
    # ligne, un lecteur anglophone prendrait du francais residuel pour une
    # sortie normale.
    "audit.non_cable": {
        "fr": "(constats rendus par {scripts}, non encore cables sur la "
              "couche de libelles : ils restent en francais)",
        "en": "(findings produced by {scripts}, not yet wired to the label "
              "layer: they remain in French)"},
    "audit.erreur_lecture": {
        "fr": "Erreur de lecture : {erreur}",
        "en": "Read error: {erreur}"},

    # tables.py
    "tables.titre": {
        "fr": "Audit de tableaux ({tables} table(s))",
        "en": "Table audit ({tables} table(s))"},
    "tables.aucun_probleme": {
        "fr": "Aucun probleme de tableau.", "en": "No table problem."},
    "tables.ecrit": {
        "fr": "Tableau ecrit : {chemin}", "en": "Table written: {chemin}"},
    "tables.p.cellule_vide": {
        "fr": "Tableau {n} : cellule vide ligne {ligne}, colonne "
              "« {colonne} ».",
        "en": "Table {n}: empty cell at row {ligne}, column \"{colonne}\"."},
    "tables.p.colonne_sans_unite": {
        "fr": "Tableau {n} : colonne numerique « {colonne} » sans unite dans "
              "l'en-tete.",
        "en": "Table {n}: numeric column \"{colonne}\" carries no unit in "
              "its header."},
    "tables.p.total_incoherent": {
        "fr": "Tableau {n} : Total colonne « {colonne} » = {total}, somme = "
              "{somme}.",
        "en": "Table {n}: Total for column \"{colonne}\" = {total}, sum of "
              "the rows = {somme}."},

    # coherence.py
    "coherence.titre": {
        "fr": "Coherence interne", "en": "Internal coherence"},
    "coherence.aucune_redite": {
        "fr": "Aucune redite ni duplication detectee.",
        "en": "No repetition or duplication found."},
    "coherence.promesses": {
        "fr": "Promesses a verifier ({n}) : {exemples}",
        "en": "Promises to check ({n}): {exemples}"},
    "coherence.p.paragraphes_dupliques": {
        "fr": "Paragraphes {a} et {b} quasi identiques (similitude "
              "{similitude}).",
        "en": "Paragraphs {a} and {b} are near duplicates (similarity "
              "{similitude})."},
    "coherence.p.phrases_repetees": {
        "fr": "{n} phrase(s) repetee(s) a l'identique.",
        "en": "{n} sentence(s) repeated word for word."},

    # ai-fingerprint.py
    "aifp.titre": {"fr": "Empreinte IA", "en": "AI fingerprint"},
    "aifp.mesures": {
        "fr": "ecart-type longueur={ecart_type} | ouverture max={ouverture}%"
              " | connecteurs/phrase={connecteurs} | triples/1000={triples}",
        "en": "length std. dev.={ecart_type} | max opening={ouverture}%"
              " | connectives/sentence={connecteurs} | triples/1000"
              "={triples}"},
    "aifp.aucun_signal": {
        "fr": "Aucun signal marque d'empreinte IA.",
        "en": "No marked sign of an AI fingerprint."},
    "aifp.s.variabilite_faible": {
        "fr": "Variabilite de longueur faible (ecart-type {ecart_type}), "
              "rythme uniforme.",
        "en": "Low length variability (standard deviation {ecart_type}), "
              "uniform rhythm."},
    "aifp.s.ouvertures_repetitives": {
        "fr": "Ouvertures repetitives ({pct}% commencent par « {mot} »).",
        "en": "Repetitive openings ({pct}% start with \"{mot}\")."},
    "aifp.s.connecteurs": {
        "fr": "Connecteurs suremployes ({densite} par phrase).",
        "en": "Overused connectives ({densite} per sentence)."},
    "aifp.s.cadence_ternaire": {
        "fr": "Cadence ternaire dense ({densite} enumerations triples / 1000 "
              "mots).",
        "en": "Dense three-part cadence ({densite} triple enumerations per "
              "1000 words)."},
    "aifp.s.bigramme": {
        "fr": "Bigramme repete {n} fois : « {bigramme} ».",
        "en": "Bigram repeated {n} times: \"{bigramme}\"."},
    "aifp.s.amplification": {
        "fr": "Amplification contrastive (« {forme} ») x{n}.",
        "en": "Contrastive amplification (\"{forme}\") x{n}."},

    # check-temporel.py
    "temporel.titre": {
        "fr": "Vérification temporelle : {chemin}",
        "en": "Temporal check: {chemin}"},
    "temporel.stdin": {"fr": "(stdin)", "en": "(stdin)"},
    "temporel.comptes": {
        "fr": "signaux={signaux}  avertissements={avertissements}",
        "en": "signals={signaux}  warnings={avertissements}"},
    "temporel.aucun_constat": {
        "fr": "Aucune défaillance chronologique détectée.",
        "en": "No chronological failure found."},
    "temporel.constat": {
        "fr": "L{ligne} ({severite}) {message}\n      « {extrait} »",
        "en": "L{ligne} ({severite}) {message}\n      \"{extrait}\""},
    "temporel.err_lecture": {
        "fr": "Erreur de lecture : {erreur}", "en": "Read error: {erreur}"},
    "temporel.err_glossaire": {
        "fr": "Erreur de lecture du glossaire de versions : {erreur}",
        "en": "Could not read the version glossary: {erreur}"},
    "temporel.err_date": {
        "fr": "Date de référence invalide : {erreur}",
        "en": "Invalid reference date: {erreur}"},
    "temporel.m.futur_au_passe": {
        "fr": "Année {annee} postérieure à la référence ({reference}) "
              "associée à un marqueur de passé dans la même phrase : "
              "vérifier si le fait est déjà survenu.",
        "en": "Year {annee} is later than the reference year ({reference}) "
              "yet carries a past-tense marker in the same sentence: check "
              "whether the event has already taken place."},
    "temporel.m.version_anterieure": {
        "fr": "« {nom} » mentionné avec une année antérieure à sa date "
              "connue ({date}).",
        "en": "\"{nom}\" cited alongside a year earlier than its known "
              "release date ({date})."},
    "temporel.m.inversion_causale": {
        "fr": "Connecteur causal « {connecteur} » : la date associée à la "
              "cause ({cause}) suit celle de l'effet ({effet}) au lieu de la "
              "précéder.",
        "en": "Causal connective \"{connecteur}\": the date attached to the "
              "cause ({cause}) comes after the one attached to the effect "
              "({effet}) instead of before it."},
    "temporel.m.langage_peremption": {
        "fr": "« {tournure} » non ancré à une date ou une version dans la "
              "phrase.",
        "en": "\"{tournure}\" is anchored to no date and no version in the "
              "sentence."},
    "temporel.m.chaine_incoherente": {
        "fr": "Référence : le preprint ({preprint}) est daté après la "
              "version publiée ({publie}).",
        "en": "Reference: the preprint ({preprint}) is dated after the "
              "published version ({publie})."},

    # check-presentation.py
    "presentation.titre": {
        "fr": "Validation de presentation : {fichier}",
        "en": "Presentation check: {fichier}"},
    "presentation.info": {"fr": "Information :", "en": "Information:"},
    "presentation.info_aucune": {
        "fr": "Information : aucune", "en": "Information: none"},
    "presentation.avertissements": {
        "fr": "Avertissements :", "en": "Warnings:"},
    "presentation.avertissements_aucun": {
        "fr": "Avertissements : aucun", "en": "Warnings: none"},
    "presentation.problemes": {"fr": "Problemes :", "en": "Problems:"},
    "presentation.problemes_aucun": {
        "fr": "Problemes : aucun", "en": "Problems: none"},
    "presentation.suite": {"fr": ", ...", "en": ", ..."},
    "presentation.m.fichier_introuvable": {
        "fr": "Fichier introuvable : {chemin}",
        "en": "File not found: {chemin}"},
    "presentation.m.extension": {
        "fr": "Extension non .pdf : concu pour un deck exporte en PDF (voir "
              "livrer, action document).",
        "en": "Extension is not .pdf: this check expects a deck exported to "
              "PDF (see livrer, action document)."},
    "presentation.m.pages_indeterminees": {
        "fr": "Nombre de pages indetermine : aucun backend disponible "
              "(installer pypdf, ou poppler-utils pour pdfinfo).",
        "en": "Page count undetermined: no backend available (install "
              "pypdf, or poppler-utils for pdfinfo)."},
    "presentation.m.pages": {
        "fr": "Pages : {n} (source : {backend}).",
        "en": "Pages: {n} (source: {backend})."},
    "presentation.m.dimensions": {
        "fr": "Dimensions de la premiere page : {largeur} x {hauteur} pts "
              "(ratio {ratio}).",
        "en": "First page size: {largeur} x {hauteur} pts (ratio {ratio})."},
    "presentation.m.repere": {
        "fr": "Repere pour {duree} min (regle ~1-2 diapositives/minute) : "
              "{lo} a {hi} diapositives.",
        "en": "Reference range for {duree} min (rule of thumb ~1-2 slides "
              "per minute): {lo} to {hi} slides."},
    "presentation.m.trop_peu": {
        "fr": "{n} diapositives pour {duree} min : en dessous de {lo}, le "
              "temps risque d'etre trop court pour le contenu ou le rythme "
              "trop lent.",
        "en": "{n} slides for {duree} min: below {lo}, either the time is "
              "short for the content or the pace is slow."},
    "presentation.m.trop": {
        "fr": "{n} diapositives pour {duree} min : au-dessus de {hi}, risque "
              "de depassement du temps annonce.",
        "en": "{n} slides for {duree} min: above {hi}, the announced time is "
              "likely to be overrun."},
    "presentation.m.dans_le_repere": {
        "fr": "Nombre de diapositives dans le repere de la duree annoncee.",
        "en": "Slide count within the range expected for the announced "
              "duration."},
    "presentation.m.densite_sautee": {
        "fr": "Densite de texte non calculee : aucun backend disponible "
              "(pypdf ou pdftotext), verification sautee plutot qu'estimee.",
        "en": "Text density not computed: no backend available (pypdf or "
              "pdftotext), the check is skipped rather than estimated."},
    "presentation.m.densite_calculee": {
        "fr": "Densite de texte calculee sur {n} page(s) (source : "
              "{backend}), seuil {seuil} mots/diapositive.",
        "en": "Text density computed over {n} page(s) (source: {backend}), "
              "threshold {seuil} words per slide."},
    "presentation.m.pages_denses_texte": {
        "fr": "Diapositives au-dessus de {seuil} mots : {liste}{suite}. Une "
              "diapositive de fond porte peu de texte (voir "
              "produire/references/genre-presentation.md).",
        "en": "Slides above {seuil} words: {liste}{suite}. A backdrop slide "
              "carries little text (see "
              "produire/references/genre-presentation.md)."},
    "presentation.item.mots": {
        "fr": "page {page} ({n} mots)", "en": "page {page} ({n} words)"},
    "presentation.m.rendu_saute": {
        "fr": "Rendu image non effectue : aucun backend disponible (PyMuPDF "
              "ou pdftoppm/poppler-utils), verification des pages denses "
              "sautee.",
        "en": "No image rendering: no backend available (PyMuPDF or "
              "pdftoppm/poppler-utils), the dense-page check is skipped."},
    "presentation.m.rendu": {
        "fr": "Rendu bas-DPI ({dpi} dpi) de {n} page(s) via {backend}, "
              "repere {seuil} octet/pixel.",
        "en": "Low-DPI rendering ({dpi} dpi) of {n} page(s) via {backend}, "
              "reference {seuil} byte per pixel."},
    "presentation.m.pages_denses_rendu": {
        "fr": "Pages au rendu dense (repere approximatif par octet/pixel, "
              "pas une mesure de lisibilite reelle) : {liste}{suite}. "
              "Verifier a l'oeil a la distance de projection.",
        "en": "Pages that render densely (rough byte-per-pixel indicator, "
              "not a measure of actual legibility): {liste}{suite}. Check "
              "them by eye at projection distance."},
    "presentation.item.octets": {
        "fr": "page {page} ({valeur} o/px)",
        "en": "page {page} ({valeur} B/px)"},

    # check-lecture-pdf.py
    "lecture.titre": {
        "fr": "Preflight d'integrite de lecture PDF : {fichier}",
        "en": "PDF read-integrity preflight: {fichier}"},
    "lecture.verdict": {
        "fr": "Verdict : {verdict}", "en": "Verdict: {verdict}"},
    "lecture.pages": {
        "fr": "Pages : {total} au total, {avec_texte} avec texte extrait.",
        "en": "Pages: {total} in all, {avec_texte} with text extracted."},
    "lecture.taux": {
        "fr": "Taux de couverture texte (pages ancrables) : {taux} %",
        "en": "Text coverage rate (anchorable pages): {taux} %"},
    "lecture.ancrables": {
        "fr": "Pages ancrables : {pages}",
        "en": "Anchorable pages: {pages}"},
    "lecture.non_ancrables": {
        "fr": "Pages NON ancrables (ancrage a refuser) : {pages}",
        "en": "Pages NOT anchorable (refuse to anchor there): {pages}"},
    "lecture.info": {"fr": "Information :", "en": "Information:"},
    "lecture.info_aucune": {
        "fr": "Information : aucune", "en": "Information: none"},
    "lecture.avertissements": {
        "fr": "Avertissements :", "en": "Warnings:"},
    "lecture.avertissements_aucun": {
        "fr": "Avertissements : aucun", "en": "Warnings: none"},
    "lecture.problemes": {"fr": "Problemes :", "en": "Problems:"},
    "lecture.problemes_aucun": {
        "fr": "Problemes : aucun", "en": "Problems: none"},
    "lecture.reste": {
        "fr": ", ... (+{reste})", "en": ", ... (+{reste})"},
    "lecture.m.fichier_introuvable": {
        "fr": "Fichier introuvable : {chemin}",
        "en": "File not found: {chemin}"},
    "lecture.m.extension": {
        "fr": "Extension non .pdf : ce preflight est concu pour un PDF.",
        "en": "Extension is not .pdf: this preflight expects a PDF."},
    "lecture.m.erreur_binaire": {
        "fr": "lecture binaire impossible : {erreur}",
        "en": "binary read failed: {erreur}"},
    "lecture.m.entete_absent": {
        "fr": "En-tete %PDF- absent en tete de fichier : non reconnaissable "
              "comme PDF.",
        "en": "No %PDF- header at the start of the file: not recognisable "
              "as a PDF."},
    "lecture.m.eof_absent": {
        "fr": "Marqueur %%EOF absent dans les {n} derniers octets : fichier "
              "tronque ou mal ferme.",
        "en": "No %%EOF marker in the last {n} bytes: the file is truncated "
              "or was closed badly."},
    "lecture.m.xref_absent": {
        "fr": "Table xref/startxref introuvable : structure PDF illisible.",
        "en": "No xref/startxref table found: the PDF structure cannot be "
              "read."},
    "lecture.m.chiffre": {
        "fr": "Marqueur /Encrypt present : PDF chiffre ou protege. "
              "Extraction potentiellement partielle ou vide. Aucun "
              "contournement tente ici.",
        "en": "/Encrypt marker present: the PDF is encrypted or protected. "
              "Extraction may be partial or empty. No circumvention is "
              "attempted here."},
    "lecture.m.chkp_absent": {
        "fr": "check-presentation.py introuvable : cascade de backends PDF "
              "indisponible.",
        "en": "check-presentation.py not found: the PDF backend cascade is "
              "unavailable."},
    "lecture.m.pages_source": {
        "fr": "Pages : {n} (source : {backend}).",
        "en": "Pages: {n} (source: {backend})."},
    "lecture.m.pages_indeterminees": {
        "fr": "Nombre de pages indetermine : aucun backend disponible pour "
              "le compter.",
        "en": "Page count undetermined: no backend available to count "
              "them."},
    "lecture.m.texte_non_extrait": {
        "fr": "Texte non extrait : aucun backend disponible (pypdf ou "
              "pdftotext). Couverture non mesurable, ancrage a refuser par "
              "prudence.",
        "en": "No text extracted: no backend available (pypdf or pdftotext). "
              "Coverage cannot be measured, so anchoring is to be refused "
              "as a precaution."},
    "lecture.m.texte_extrait": {
        "fr": "Texte extrait via {backend} sur {n} page(s).",
        "en": "Text extracted with {backend} over {n} page(s)."},
    "lecture.m.divergence": {
        "fr": "Comptage de pages ({pages}, {backend_pages}) et extraction de "
              "texte ({textes}, {backend_texte}) divergent.",
        "en": "Page count ({pages}, {backend_pages}) and text extraction "
              "({textes}, {backend_texte}) disagree."},
    "lecture.m.pages_sans_texte": {
        "fr": "Pages sans texte extrait, ancrage refuse : {pages}.",
        "en": "Pages with no text extracted, anchoring refused: {pages}."},
    "lecture.m.pages_cassees": {
        "fr": "Pages a l'encodage suspect (mojibake ou caracteres de "
              "remplacement), ancrage refuse : {pages}.",
        "en": "Pages with suspect encoding (mojibake or replacement "
              "characters), anchoring refused: {pages}."},
    "lecture.m.aucun_texte_chiffre": {
        "fr": "Aucune page ne rend de texte, et le PDF est signale "
              "chiffre/protege : l'extraction vide vient probablement de la "
              "protection, pas d'un scan sans OCR.",
        "en": "No page yields any text, and the PDF is flagged as "
              "encrypted or protected: the empty extraction most likely "
              "comes from the protection, not from a scan without OCR."},
    "lecture.m.aucun_texte": {
        "fr": "Aucune page ne rend de texte alors que le fichier a des "
              "pages : probable PDF scanne sans OCR.",
        "en": "No page yields any text although the file has pages: most "
              "likely a scanned PDF without OCR."},

    # check-fuites.py : decor du rapport
    "fuites.entete": {
        "fr": "{fichier} : {verdict}", "en": "{fichier}: {verdict}"},
    "fuites.aucune_trace": {
        "fr": "aucune trace lisible dans les parties inspectees",
        "en": "no readable trace in the parts inspected"},
    "fuites.constat": {
        "fr": "[{confiance}] {regle} : {detail}{valeur}",
        "en": "[{confiance}] {regle}: {detail}{valeur}"},
    "fuites.valeur": {"fr": " -> {valeur}", "en": " -> {valeur}"},
    "fuites.comptes": {
        "fr": "{confirmes} confirme(s), {probables} probable(s), "
              "{informatifs} informatif(s), {douteux} douteux",
        "en": "{confirmes} confirmed, {probables} probable, {informatifs} "
              "informative, {douteux} doubtful"},
    "fuites.partage": {
        "fr": "Ce controle inspecte, il ne nettoie pas : retirer une trace"
              "\nest une decision de l'auteur, la reperer est une mesure.",
        "en": "This check inspects, it does not clean: removing a trace is"
              "\nthe author's decision, finding it is a measurement."},
    "fuites.non_verifie": {
        "fr": "Non verifie ici :", "en": "Not checked here:"},
    "fuites.cat.identite": {
        "fr": "Identite et organisation", "en": "Identity and organisation"},
    "fuites.cat.historique": {
        "fr": "Historique d'edition", "en": "Editing history"},
    "fuites.cat.residu": {
        "fr": "Residus de travail", "en": "Leftovers of the work"},
    "fuites.cat.chemin": {"fr": "Chemins locaux", "en": "Local paths"},
    "fuites.cat.integrite": {
        "fr": "Integrite du fichier", "en": "File integrity"},
    "fuites.err_introuvable": {
        "fr": "fichier introuvable : {chemin}",
        "en": "file not found: {chemin}"},
    "fuites.err_format": {
        "fr": "{fichier} n'est ni un PDF ni une archive : format non couvert",
        "en": "{fichier} is neither a PDF nor an archive: format not "
              "covered"},
    "fuites.err_archive": {
        "fr": "{fichier} est une archive d'un format non couvert",
        "en": "{fichier} is an archive of a format that is not covered"},

    # check-fuites.py : detail des constats
    "fuites.d.auteur_origine": {
        "fr": "auteur d'origine", "en": "original author"},
    "fuites.d.dernier_enregistrement": {
        "fr": "derniere personne a avoir enregistre",
        "en": "last person to have saved the file"},
    "fuites.d.titre": {
        "fr": "titre enregistre dans le fichier",
        "en": "title stored inside the file"},
    "fuites.d.sujet": {
        "fr": "sujet enregistre", "en": "subject stored in the file"},
    "fuites.d.description": {
        "fr": "description enregistree",
        "en": "description stored in the file"},
    "fuites.d.mots_cles": {
        "fr": "mots-cles enregistres", "en": "keywords stored in the file"},
    "fuites.d.categorie": {
        "fr": "categorie enregistree", "en": "category stored in the file"},
    "fuites.d.organisation": {"fr": "organisation", "en": "organisation"},
    "fuites.d.responsable": {
        "fr": "responsable declare", "en": "declared manager"},
    "fuites.d.logiciel_production": {
        "fr": "logiciel de production", "en": "producing software"},
    "fuites.d.logiciel_creation": {
        "fr": "logiciel de creation", "en": "creating software"},
    "fuites.d.gabarit": {
        "fr": "gabarit d'origine", "en": "template it came from"},
    "fuites.d.auteur_declare": {
        "fr": "auteur declare", "en": "declared author"},
    "fuites.d.enregistrements": {
        "fr": "le fichier declare {n} enregistrements successifs",
        "en": "the file declares {n} successive saves"},
    "fuites.d.temps_edition": {
        "fr": "temps d'edition cumule declare : {n} minutes",
        "en": "declared cumulative editing time: {n} minutes"},
    "fuites.d.duree_edition": {
        "fr": "duree d'edition cumulee declaree : {duree}",
        "en": "declared cumulative editing time: {duree}"},
    "fuites.d.modifications_suivies": {
        "fr": "{insertions} insertion(s) et {suppressions} suppression(s) "
              "non acceptees restent dans le document",
        "en": "{insertions} insertion(s) and {suppressions} deletion(s) are "
              "still in the document, unaccepted"},
    "fuites.d.registre_suivi": {
        "fr": "le document porte un registre de modifications suivies",
        "en": "the document carries a tracked-changes record"},
    "fuites.d.texte_masque": {
        "fr": "{n} passage(s) en texte masque, invisibles a l'ecran mais "
              "presents dans le fichier",
        "en": "{n} passage(s) in hidden text, invisible on screen yet "
              "present in the file"},
    "fuites.d.commentaires_docx": {
        "fr": "{n} commentaire(s) restent dans le document{auteurs}",
        "en": "{n} comment(s) are still in the document{auteurs}"},
    "fuites.d.commentaires_auteurs": {
        "fr": ", de {auteurs}", "en": ", by {auteurs}"},
    "fuites.d.custom_xml": {
        "fr": "le fichier porte un dossier customXml, souvent laisse par un "
              "outil de gestion documentaire",
        "en": "the file carries a customXml folder, often left behind by a "
              "document management tool"},
    "fuites.d.collaborateurs": {
        "fr": "le fichier liste les personnes ayant contribue : {noms}",
        "en": "the file lists the people who contributed: {noms}"},
    "fuites.d.notes_presentateur": {
        "fr": "{n} diapositive(s) portent des notes, visibles par qui ouvre "
              "le fichier",
        "en": "{n} slide(s) carry speaker notes, visible to anyone who opens "
              "the file"},
    "fuites.d.commentaires_pptx": {
        "fr": "{n} partie(s) de commentaires dans la presentation",
        "en": "{n} comment part(s) in the presentation"},
    "fuites.d.chemin_local": {
        "fr": "un lien pointe vers un chemin de votre machine",
        "en": "a link points to a path on your own machine"},
    "fuites.d.incremental": {
        "fr": "le fichier porte {eof} marqueurs de fin et {prev} renvoi(s) "
              "vers une table anterieure : les versions precedentes du "
              "document restent dans le fichier et sont recuperables, y "
              "compris des metadonnees que l'on croirait supprimees",
        "en": "the file carries {eof} end markers and {prev} pointer(s) to "
              "an earlier table: the previous versions of the document are "
              "still inside the file and can be recovered, including "
              "metadata one would believe deleted"},
    "fuites.d.xmp": {
        "fr": "le fichier porte un bloc XMP{auteur}",
        "en": "the file carries an XMP block{auteur}"},
    "fuites.d.xmp_auteur": {
        "fr": ", avec un champ d'auteur", "en": ", with an author field"},
    "fuites.d.chiffrement": {
        "fr": "le PDF est chiffre : son contenu n'a pas ete inspecte en "
              "detail",
        "en": "the PDF is encrypted: its content was not inspected in "
              "detail"},
    "fuites.d.fichier_embarque": {
        "fr": "le PDF embarque au moins un fichier joint, qui part avec lui",
        "en": "the PDF embeds at least one attached file, which travels "
              "with it"},
    "fuites.d.annotations": {
        "fr": "le PDF porte des annotations de type note",
        "en": "the PDF carries note-type annotations"},

    # check-fuites.py : angles morts declares
    "fuites.nv.contenu": {
        "fr": "le contenu redactionnel n'est pas juge ici, seules les traces "
              "le sont",
        "en": "the editorial content is not judged here, only the traces "
              "are"},
    "fuites.nv.images": {
        "fr": "les metadonnees des images incorporees ne sont pas ouvertes "
              "une par une (voir images.py extract puis manifest)",
        "en": "the metadata of embedded images is not opened one by one "
              "(see images.py extract, then manifest)"},
    "fuites.nv.pdf_chiffre": {
        "fr": "un PDF chiffre n'est pas inspecte au dela de son enveloppe",
        "en": "an encrypted PDF is not inspected beyond its envelope"},
    "fuites.nv.flux_compresse": {
        "fr": "les objets ranges dans un flux compresse echappent a la "
              "lecture binaire : l'absence de constat n'est pas une preuve "
              "d'absence",
        "en": "objects stored inside a compressed stream escape the binary "
              "read: no finding is not proof that there is nothing"},
    "fuites.nv.macros": {
        "fr": "les macros et le code embarque ne sont pas analyses",
        "en": "macros and embedded code are not analysed"},
    "fuites.nv.champ_non_standard": {
        "fr": "un champ efface par l'application mais conserve dans une "
              "partie non standard peut echapper a ce controle",
        "en": "a field cleared by the application yet kept in a "
              "non-standard part can escape this check"},

    # check-disponibilite.py : decor du rapport
    "dispo.entete": {
        "fr": "{fichier} : {verdict}", "en": "{fichier}: {verdict}"},
    "dispo.texte": {"fr": "(texte)", "en": "(text)"},
    "dispo.entree_standard": {
        "fr": "(entrée standard)", "en": "(standard input)"},
    "dispo.section": {"fr": "Section : {section}", "en": "Section: {section}"},
    "dispo.section_situee": {
        "fr": "{titres} (ligne {ligne})", "en": "{titres} (line {ligne})"},
    "dispo.section_absente": {"fr": "absente", "en": "absent"},
    "dispo.regimes": {"fr": "Régimes : {regimes}", "en": "Regimes: {regimes}"},
    "dispo.aucun_regime": {
        "fr": "aucun identifié", "en": "none identified"},
    "dispo.identifiants": {
        "fr": "Identifiants pérennes : {identifiants}",
        "en": "Persistent identifiers: {identifiants}"},
    "dispo.aucun_constat": {
        "fr": "aucun constat : la déclaration porte ce que son régime exige",
        "en": "no finding: the statement carries what its regime requires"},
    "dispo.constat": {
        "fr": "[{confiance}] {regle} : {detail}{extrait}",
        "en": "[{confiance}] {regle}: {detail}{extrait}"},
    "dispo.extrait": {"fr": " -> {extrait}", "en": " -> {extrait}"},
    "dispo.comptes": {
        "fr": "{confirmes} confirmé(s), {probables} probable(s), "
              "{informatifs} informatif(s), {douteux} douteux",
        "en": "{confirmes} confirmed, {probables} probable, {informatifs} "
              "informative, {douteux} doubtful"},
    "dispo.limite_ligne": {
        "fr": "Limite : {limite}", "en": "Limit: {limite}"},
    "dispo.non_verifie": {
        "fr": "Non vérifié ici :", "en": "Not checked here:"},
    "dispo.err_introuvable": {
        "fr": "fichier introuvable : {chemin}",
        "en": "file not found: {chemin}"},
    "dispo.cat.structure": {
        "fr": "Structure de la déclaration",
        "en": "Structure of the statement"},
    "dispo.cat.regime": {
        "fr": "Régime déclaré", "en": "Declared regime"},
    "dispo.cat.identifiant": {
        "fr": "Identifiant pérenne", "en": "Persistent identifier"},
    "dispo.cat.code": {"fr": "Code", "en": "Code"},
    "dispo.limite": {
        "fr": "Ce rapport contrôle la forme d'une déclaration, il ne la "
              "valide pas contre le monde : aucun identifiant n'est résolu, "
              "aucun dépôt n'est ouvert, aucune autorisation n'est vérifiée.",
        "en": "This report checks the form of a statement, it does not "
              "validate it against the world: no identifier is resolved, no "
              "repository is opened, no authorisation is checked."},

    # check-disponibilite.py : detail des constats
    "dispo.d.section_absente": {
        "fr": "aucune section de disponibilité des données ou du code. Les "
              "revues la réclament, les financeurs publics en font une "
              "obligation contractuelle.",
        "en": "no data or code availability section. Journals ask for one, "
              "and public funders make it a contractual obligation."},
    "dispo.d.section_vide": {
        "fr": "la section de disponibilité porte un titre sans déclaration "
              "lisible ({mots} mots).",
        "en": "the availability section has a heading but no readable "
              "statement ({mots} words)."},
    "dispo.d.regime_non_identifie": {
        "fr": "la section existe mais aucune formulation n'y désigne un "
              "régime connu ({regimes}).",
        "en": "the section exists but no wording in it points to a known "
              "regime ({regimes})."},
    "dispo.d.ouverture_sans_identifiant": {
        "fr": "un dépôt public ouvert est annoncé sans identifiant pérenne "
              "(DOI, handle, ARK, SWHID, numéro d'accession). Une adresse "
              "web ordinaire ne fixe rien.",
        "en": "an open public repository is announced with no persistent "
              "identifier (DOI, handle, ARK, SWHID, accession number). An "
              "ordinary web address fixes nothing."},
    "dispo.d.identifiant_sans_doi": {
        "fr": "l'ouverture repose sur un {types} sans DOI ni handle ni ARK. "
              "Vérifier que le dépôt visé attribue bien un identifiant "
              "citable.",
        "en": "the openness rests on a {types} with no DOI, handle or ARK. "
              "Check that the repository does mint a citable identifier."},
    "dispo.d.doi_mal_forme": {
        "fr": "la valeur annoncée comme DOI ne suit pas la syntaxe "
              "10.préfixe/suffixe.",
        "en": "the value announced as a DOI does not follow the "
              "10.prefix/suffix syntax."},
    "dispo.d.embargo_sans_date": {
        "fr": "un embargo est annoncé sans date de levée. Sans date, la "
              "déclaration ne se distingue pas d'un refus de partage.",
        "en": "an embargo is announced with no lifting date. Without a date, "
              "the statement is indistinguishable from a refusal to share."},
    "dispo.d.demande_sans_conditions": {
        "fr": "un accès sur demande est annoncé sans {manques}. Une demande "
              "sans conditions déclarées est la formulation la moins suivie "
              "d'effet.",
        "en": "access on request is announced without {manques}. A request "
              "with no stated conditions is the wording least often acted "
              "upon."},
    "dispo.manque.contact": {
        "fr": "le contact qui décide", "en": "the contact who decides"},
    "dispo.manque.criteres": {
        "fr": "les critères d'accès", "en": "the access criteria"},
    "dispo.manque.duree": {
        "fr": "la durée de disponibilité",
        "en": "how long it stays available"},
    "dispo.d.licence_non_nommee": {
        "fr": "du code est annoncé et une licence est évoquée sans être "
              "nommée. Nommer la licence exacte (MIT, Apache 2.0, GPL).",
        "en": "code is announced and a licence is mentioned without being "
              "named. Name the exact licence (MIT, Apache 2.0, GPL)."},
    "dispo.d.code_sans_licence": {
        "fr": "du code est annoncé sans aucune licence. Sans licence "
              "explicite, le code reste sous droit d'auteur par défaut, donc "
              "lisible et non réutilisable.",
        "en": "code is announced with no licence at all. Without an explicit "
              "licence the code stays under copyright by default, so it can "
              "be read and not reused."},
    "dispo.d.code_sans_version_figee": {
        "fr": "le code renvoie à un dépôt de développement sans version "
              "figée (étiquette, DOI d'archive, empreinte de commit). Un "
              "dépôt se renomme, passe en privé, se réécrit.",
        "en": "the code points to a development repository with no frozen "
              "version (tag, archive DOI, commit hash). A repository gets "
              "renamed, turned private, rewritten."},
    "dispo.d.restriction_sans_motif": {
        "fr": "un partage restreint est annoncé sans motif nommé (données à "
              "caractère personnel, secret industriel, espèce protégée, "
              "patrimoine, sécurité).",
        "en": "restricted sharing is announced with no stated ground "
              "(personal data, trade secret, protected species, heritage, "
              "security)."},
    "dispo.d.tiers_sans_detenteur": {
        "fr": "des données de tiers sont annoncées sans nommer leur "
              "détenteur ni la procédure d'accès auprès de lui.",
        "en": "third-party data is announced without naming its holder or "
              "the procedure for obtaining access from them."},
    "dispo.d.regimes_contradictoires": {
        "fr": "la section déclare l'absence de donnée nouvelle et, dans le "
              "même corps, un régime de partage ({regimes}).",
        "en": "the section declares that no new data was produced and, in "
              "the same body, a sharing regime ({regimes})."},
    "dispo.d.regimes_multiples": {
        "fr": "la section combine {regimes}. Cette combinaison est légitime "
              "si chaque régime nomme le matériel qu'il couvre.",
        "en": "the section combines {regimes}. That combination is "
              "legitimate provided each regime names the material it "
              "covers."},

    # check-disponibilite.py : angles morts declares
    "dispo.nv.identifiant": {
        "fr": "aucun identifiant n'est résolu : un DOI bien formé peut ne "
              "pointer sur rien",
        "en": "no identifier is resolved: a well-formed DOI may point at "
              "nothing"},
    "dispo.nv.depot": {
        "fr": "le contenu du dépôt n'est pas ouvert : rien ne dit qu'il "
              "porte ce que la déclaration annonce",
        "en": "the content of the repository is not opened: nothing says it "
              "holds what the statement announces"},
    "dispo.nv.autorisation": {
        "fr": "aucune autorisation n'est vérifiée (consentement des "
              "personnes, accord de l'employeur, licence des données de "
              "tiers)",
        "en": "no authorisation is checked (consent of the people involved, "
              "employer agreement, licence of third-party data)"},
    "dispo.nv.revue": {
        "fr": "la politique de la revue cible n'est pas lue : elle peut "
              "exiger d'autres éléments ou un autre emplacement",
        "en": "the policy of the target journal is not read: it may require "
              "other elements or another location"},
    "dispo.nv.hors_section": {
        "fr": "une déclaration exacte mais placée hors d'une section titrée "
              "échappe à la détection, qui porte sur un titre",
        "en": "an accurate statement placed outside a titled section escapes "
              "the detection, which works on headings"},

    # citations.py
    "citations.audit_aucun_couple": {
        "fr": "Audit de fidelite : aucun couple affirmation-ancre repere "
              "(convention : phrase suivie de [cle_bibtex]).",
        "en": "Fidelity audit: no claim-anchor pair found (convention: a "
              "sentence followed by [bibtex_key])."},
    "citations.audit_couple": {
        "fr": "[{cle}] {affirmation}", "en": "[{cle}] {affirmation}"},
    "citations.audit_ancre": {
        "fr": "ancre : {type}{defaut}", "en": "anchor: {type}{defaut}"},
    "citations.audit_defaut": {
        "fr": " ({defaut})", "en": " ({defaut})"},
    "citations.audit_signal": {
        "fr": "signal : {signal}{detail}",
        "en": "signal: {signal}{detail}"},
    "citations.audit_signal_detail": {
        "fr": " -- {detail}", "en": " -- {detail}"},
    "citations.audit_aucun_signal": {
        "fr": "signal : aucun", "en": "signal: none"},
    "citations.audit_non_mesurable": {
        "fr": "non mesurable (pas de texte source dans l'ancre) : {mesures}",
        "en": "not measurable (the anchor carries no source text): "
              "{mesures}"},
    "citations.bascule": {
        "fr": "Bascule {ancien} -> {nouveau} (compte inchange : {avant} "
              "avant, {apres} apres)",
        "en": "Switch {ancien} -> {nouveau} (count unchanged: {avant} "
              "before, {apres} after)"},
    "citations.doublons": {
        "fr": "Doublons ecartes : {doublons}",
        "en": "Duplicates set aside: {doublons}"},
    "citations.sans_ancre": {
        "fr": "Entrees sans ancre exploitable (signal) : {cles}",
        "en": "Entries with no usable anchor (signal): {cles}"},
    "citations.champs_manquants": {
        "fr": "Champs obligatoires manquants ({n} entree(s)) :",
        "en": "Required fields missing ({n} entry or entries):"},
    "citations.champ_ligne": {
        "fr": "{cle} ({type}) : {manquants}",
        "en": "{cle} ({type}): {manquants}"},
    "citations.type_non_reconnu": {
        "fr": "Type BibTeX non reconnu (non valide) : {types}",
        "en": "BibTeX type not recognised (not validated): {types}"},

    # check-droits.py : limite, conditions de licence, alternative
    "droits.limite": {
        "fr": "Ce rapport dit ce que la licence déclare, il ne prononce pas "
              "la légalité d'un usage. Le contrat signé avec une revue, la "
              "politique d'un employeur ou le droit applicable peuvent en "
              "décider autrement.",
        "en": "This report states what the licence declares, it does not "
              "rule on the lawfulness of a use. The contract signed with a "
              "journal, an employer's policy or the applicable law may "
              "decide otherwise."},
    "droits.c.attribution_non_exigee": {
        "fr": "Attribution non exigée par la licence, conservée par "
              "honnêteté de sourçage.",
        "en": "Attribution is not required by the licence, kept out of "
              "honesty about sourcing."},
    "droits.c.attribution_complete": {
        "fr": "Attribution complète : titre, auteur, source, licence.",
        "en": "Full attribution: title, author, source, licence."},
    "droits.c.mention_modifications": {
        "fr": "Mention des modifications si la figure est retouchée.",
        "en": "State the modifications if the figure is altered."},
    "droits.c.partage_identique": {
        "fr": "Le document dérivé se diffuse sous la même licence.",
        "en": "The derived document is released under the same licence."},
    "droits.c.destination_contrainte": {
        "fr": "Vérifier que la destination accepte cette contrainte.",
        "en": "Check that the destination accepts that constraint."},
    "droits.c.commercial_ferme_exemples": {
        "fr": "Usage commercial fermé (livre vendu, rapport facturé, support "
              "de formation payante).",
        "en": "Commercial use is closed (a book sold, a report invoiced, "
              "material for paid training)."},
    "droits.c.commercial_ferme": {
        "fr": "Usage commercial fermé.", "en": "Commercial use is closed."},
    "droits.c.aucune_adaptation_legende": {
        "fr": "Aucune adaptation : ni recadrage, ni retouche, ni traduction "
              "de la légende incrustée.",
        "en": "No adaptation: no cropping, no retouching, no translation of "
              "the caption burnt into the image."},
    "droits.c.figure_entiere": {
        "fr": "La figure se reproduit entière ou pas du tout.",
        "en": "The figure is reproduced whole or not at all."},
    "droits.c.aucune_adaptation": {
        "fr": "Aucune adaptation : ni recadrage, ni retouche.",
        "en": "No adaptation: no cropping, no retouching."},
    "droits.c.demande_ecrite": {
        "fr": "Demande écrite à l'éditeur avant toute reproduction.",
        "en": "Written request to the publisher before any reproduction."},
    "droits.c.fouille_pas_republication": {
        "fr": "Une licence de fouille de textes ne couvre pas la "
              "republication d'une figure.",
        "en": "A text and data mining licence does not cover republishing a "
              "figure."},
    "droits.alt.voie": {
        "fr": "redessin depuis les données publiées",
        "en": "redrawing from the published data"},
    "droits.alt.mention": {
        "fr": "D'après les données de {auteur}",
        "en": "After data from {auteur}"},
    "droits.alt.auteur_inconnu": {
        "fr": "l'auteur de la source", "en": "the author of the source"},
    "droits.alt.note": {
        "fr": "Relever les valeurs publiées (texte, tableau, données "
              "supplémentaires), puis tracer avec la charte du document. Ne "
              "pas décalquer le rendu d'origine, qui est la partie protégée. "
              "Voir references/figures-catalogue.md.",
        "en": "Read off the published values (text, table, supplementary "
              "data), then plot them with the document's own style. Do not "
              "trace over the original rendering, which is the protected "
              "part. See references/figures-catalogue.md."},

    # check-droits.py : resolution d'une licence par son DOI
    "droits.d.reseau_desactive": {
        "fr": "--reseau désactivé : aucune licence consultée. Renseigner la "
              "licence à la main dans le registre.",
        "en": "--reseau is off: no licence was queried. Fill the licence in "
              "by hand in the register."},
    "droits.d.licence_declaree": {
        "fr": "licence {licence} déclarée par {index}",
        "en": "licence {licence} declared by {index}"},
    "droits.d.index_generique": {
        "fr": "un index", "en": "an index"},
    "droits.d.aucune_reconnue": {
        "fr": "{n} licence(s) déclarée(s) mais aucune reconnue par la table "
              "locale : lire les conditions à la source avant de reproduire.",
        "en": "{n} licence(s) declared but none recognised by the local "
              "table: read the terms at the source before reproducing."},
    "droits.d.aucune_declaree": {
        "fr": "source trouvée par {index}, aucune licence déclarée : absence "
              "d'information, ni interdiction ni permission.",
        "en": "source found by {index}, no licence declared: an absence of "
              "information, neither a ban nor a permission."},
    "droits.d.doi_non_trouve": {
        "fr": "DOI non trouvé par {index} : la licence reste inconnue.",
        "en": "DOI not found by {index}: the licence remains unknown."},
    "droits.d.aucun_index": {
        "fr": "aucun index joignable (réseau indisponible) : mesure omise, "
              "jamais remplacée par une valeur supposée.",
        "en": "no index reachable (network unavailable): the measurement is "
              "omitted, never replaced by an assumed value."},

    # check-droits.py : ligne de credit
    "droits.attr.marque": {
        "fr": "[À COMPLÉTER : {element}]", "en": "[TO COMPLETE: {element}]"},
    "droits.attr.figure_defaut": {"fr": "Figure", "en": "Figure"},
    "droits.attr.modifiee": {
        "fr": "Figure modifiée ({modifications}).",
        "en": "Figure modified ({modifications})."},
    "droits.attr.sans_modification": {
        "fr": "Figure reproduite sans modification.",
        "en": "Figure reproduced without modification."},
    "droits.attr.source_lien": {
        "fr": "{source} ({lien})", "en": "{source} ({lien})"},
    "droits.attr.texte": {
        "fr": "{libelle} : \"{titre}\", {auteur}, {source}, sous licence "
              "{licence}. {modification}",
        "en": "{libelle}: \"{titre}\", {auteur}, {source}, under the "
              "{licence} licence. {modification}"},
    "droits.attr.html": {
        "fr": "<p class=\"credit-figure\">{libelle} : &quot;{titre}&quot;, "
              "{auteur}, {source}, sous licence {licence}. "
              "{modification}</p>",
        "en": "<p class=\"credit-figure\">{libelle}: &quot;{titre}&quot;, "
              "{auteur}, {source}, under the {licence} licence. "
              "{modification}</p>"},
    "droits.attr.latex_corps": {
        "fr": "{titre}. {auteur}, {source}, sous licence {licence}. "
              "{modification}",
        "en": "{titre}. {auteur}, {source}, under the {licence} licence. "
              "{modification}"},
    "droits.credits.titre_md": {
        "fr": "## Crédits des figures", "en": "## Figure credits"},
    "droits.credits.titre_html": {
        "fr": "Crédits des figures", "en": "Figure credits"},
    "droits.credits.titre_latex": {
        "fr": "Crédits des figures", "en": "Figure credits"},

    # check-droits.py : validation du registre
    "droits.v.pas_un_objet": {
        "fr": "Le registre n'est pas un objet JSON.",
        "en": "The register is not a JSON object."},
    "droits.v.figures_absentes": {
        "fr": "Clé \"figures\" absente, vide ou mal formée.",
        "en": "Key \"figures\" is absent, empty or malformed."},
    "droits.v.entree_pas_objet": {
        "fr": "Entrée {rang} : ce n'est pas un objet.",
        "en": "Entry {rang}: this is not an object."},
    "droits.v.rang": {"fr": "entrée {rang}", "en": "entry {rang}"},
    "droits.v.id_absent": {
        "fr": "Entrée {rang} : clé \"id\" absente.",
        "en": "Entry {rang}: key \"id\" is absent."},
    "droits.v.id_duplique": {
        "fr": "Figure {rang} : identifiant dupliqué.",
        "en": "Figure {rang}: duplicate identifier."},
    "droits.v.source_absente": {
        "fr": "Figure {rang} : clé \"source\" absente, la ligne de crédit ne "
              "peut pas être écrite.",
        "en": "Figure {rang}: key \"source\" is absent, the credit line "
              "cannot be written."},
    "droits.v.titre_absent": {
        "fr": "Figure {rang} : titre absent, la ligne de crédit restera "
              "incomplète.",
        "en": "Figure {rang}: no title, the credit line will stay "
              "incomplete."},
    "droits.v.auteur_absent": {
        "fr": "Figure {rang} : auteur absent, la ligne de crédit restera "
              "incomplète.",
        "en": "Figure {rang}: no author, the credit line will stay "
              "incomplete."},
    "droits.v.sans_lien": {
        "fr": "Figure {rang} : ni DOI ni URL, la source n'est pas résoluble "
              "par un lecteur.",
        "en": "Figure {rang}: neither DOI nor URL, a reader cannot resolve "
              "the source."},
    "droits.v.verdict_hors_liste": {
        "fr": "Figure {rang} : verdict \"{verdict}\" hors de la liste fermée "
              "({liste}).",
        "en": "Figure {rang}: verdict \"{verdict}\" is outside the closed "
              "list ({liste})."},
    "droits.v.verdict_incompatible": {
        "fr": "Figure {rang} : verdict déclaré \"{declare}\" incompatible "
              "avec la licence déclarée {licence}, qui donne \"{calcule}\".",
        "en": "Figure {rang}: declared verdict \"{declare}\" is "
              "incompatible with the declared licence {licence}, which "
              "gives \"{calcule}\"."},
    "droits.v.licence_non_reconnue": {
        "fr": "Figure {rang} : licence \"{licence}\" non reconnue par la "
              "table locale, conditions à lire à la source.",
        "en": "Figure {rang}: licence \"{licence}\" is not recognised by the "
              "local table, read the terms at the source."},
    "droits.v.modification_interdite": {
        "fr": "Figure {rang} : modification déclarée ({modifications}) sous "
              "une licence {licence}, qui interdit toute adaptation, donc "
              "tout recadrage.",
        "en": "Figure {rang}: a modification is declared ({modifications}) "
              "under a {licence} licence, which forbids any adaptation, "
              "hence any cropping."},
    "droits.v.autorisation_mal_formee": {
        "fr": "Figure {rang} : clé \"autorisation\" mal formée.",
        "en": "Figure {rang}: key \"autorisation\" is malformed."},
    "droits.v.etat_hors_liste": {
        "fr": "Figure {rang} : état d'autorisation \"{etat}\" hors de la "
              "liste fermée ({liste}).",
        "en": "Figure {rang}: permission state \"{etat}\" is outside the "
              "closed list ({liste})."},
    "droits.v.autorisation_refusee": {
        "fr": "Figure {rang} : autorisation refusée, la figure ne peut pas "
              "être reproduite. La retirer ou la redessiner depuis les "
              "données.",
        "en": "Figure {rang}: permission refused, the figure cannot be "
              "reproduced. Remove it or redraw it from the data."},
    "droits.v.autorisation_requise": {
        "fr": "Figure {rang} : autorisation requise, état \"{etat}\". "
              "Obtenir l'accord écrit de l'éditeur avant diffusion.",
        "en": "Figure {rang}: permission required, state \"{etat}\". Obtain "
              "the publisher's written agreement before release."},
    "droits.v.etat_non_renseigne": {
        "fr": "non renseigné", "en": "not filled in"},
    "droits.v.licence_inconnue": {
        "fr": "Figure {rang} : licence inconnue. Une absence d'information "
              "n'est pas une permission : établir la licence ou redessiner "
              "depuis les données.",
        "en": "Figure {rang}: licence unknown. An absence of information is "
              "not a permission: establish the licence or redraw from the "
              "data."},

    # check-droits.py : rapports texte
    "droits.lic.titre": {
        "fr": "Droits de réutilisation : {doi}",
        "en": "Reuse rights: {doi}"},
    "droits.lic.verdict": {
        "fr": "Verdict : {verdict}", "en": "Verdict: {verdict}"},
    "droits.lic.motif": {"fr": "Motif : {motif}", "en": "Reason: {motif}"},
    "droits.lic.titre_source": {
        "fr": "Titre : {titre}", "en": "Title: {titre}"},
    "droits.lic.acces_ouvert": {
        "fr": "Accès ouvert : {ouvert} (statut {statut})",
        "en": "Open access: {ouvert} (status {statut})"},
    "droits.lic.index": {
        "fr": "Index {nom} : consulté={consulte} trouvé={trouve} "
              "licences={licences}",
        "en": "Index {nom}: queried={consulte} found={trouve} "
              "licences={licences}"},
    "droits.lic.licences": {
        "fr": "Licences déclarées :", "en": "Declared licences:"},
    "droits.lic.licence_ligne": {
        "fr": "[{etat}] {nom} ({origine})",
        "en": "[{etat}] {nom} ({origine})"},
    "droits.lic.reconnue": {"fr": "reconnue", "en": "recognised"},
    "droits.lic.non_reconnue": {
        "fr": "non reconnue", "en": "not recognised"},
    "droits.lic.conditions": {"fr": "Conditions :", "en": "Conditions:"},
    "droits.lic.alternative": {
        "fr": "Alternative sans emprunt : {voie}",
        "en": "Alternative without borrowing: {voie}"},
    "droits.lic.mention": {
        "fr": "Mention : {mention}", "en": "Credit line: {mention}"},
    "droits.lic.types_figures": {
        "fr": "Types de figures de données : {types}",
        "en": "Types of data figure: {types}"},
    "droits.lic.limite": {
        "fr": "Limite : {limite}", "en": "Limit: {limite}"},
    "droits.reg.titre": {
        "fr": "Registre des figures empruntées : {fichier}",
        "en": "Register of borrowed figures: {fichier}"},
    "droits.reg.en_memoire": {
        "fr": "(en mémoire)", "en": "(in memory)"},
    "droits.reg.verdict": {
        "fr": "Verdict : {verdict}", "en": "Verdict: {verdict}"},
    "droits.reg.figures": {
        "fr": "Figures : {n}", "en": "Figures: {n}"},
    "droits.reg.figure": {
        "fr": "[{verdict}] {id}", "en": "[{verdict}] {id}"},
    "droits.reg.source": {
        "fr": "Source : {source}", "en": "Source: {source}"},
    "droits.reg.source_absente": {"fr": "absente", "en": "absent"},
    "droits.reg.licence": {
        "fr": "Licence : {licence} ({etat})",
        "en": "Licence: {licence} ({etat})"},
    "droits.reg.autorisation": {
        "fr": "Autorisation : {etat}", "en": "Permission: {etat}"},
    "droits.reg.resolution": {
        "fr": "Résolution réseau : {detail}",
        "en": "Network resolution: {detail}"},
    "droits.reg.condition": {
        "fr": "Condition : {condition}", "en": "Condition: {condition}"},
    "droits.reg.credit": {
        "fr": "Crédit : {credit}", "en": "Credit: {credit}"},
    "droits.reg.manques": {
        "fr": "Éléments manquants : {elements}",
        "en": "Missing elements: {elements}"},
    "droits.reg.alternative": {
        "fr": "Alternative : {voie}, mention \"{mention}\", figures {types}",
        "en": "Alternative: {voie}, credit line \"{mention}\", figures "
              "{types}"},
    "droits.reg.erreurs": {"fr": "Erreurs :", "en": "Errors:"},
    "droits.reg.erreurs_aucune": {
        "fr": "Erreurs : aucune", "en": "Errors: none"},
    "droits.reg.avertissements": {
        "fr": "Avertissements :", "en": "Warnings:"},
    "droits.reg.avertissements_aucun": {
        "fr": "Avertissements : aucun", "en": "Warnings: none"},
    "droits.err_registre": {
        "fr": "Erreur de lecture du registre : {erreur}",
        "en": "Could not read the register: {erreur}"},

    # emprunts.py : garde-fou et refus. Ces trois refus ne sont pas des
    # messages d'erreur ordinaires : ils disent pourquoi le script ne
    # descendra pas plus bas. L'anglais est aussi net que le francais, sans
    # attenuation ni tournure d'excuse, sinon le garde-fou se lit comme un
    # incident technique a contourner.
    "emprunts.limite": {
        "fr": "Ce rapport dit ce que l'index déclare et ce que les fichiers "
              "montrent. L'appariement d'une image et d'une légende est une "
              "heuristique de mise en page, jamais une lecture de la figure. "
              "Ce que la licence permet reste l'affaire de check-droits.py.",
        "en": "This report states what the index declares and what the files "
              "show. Pairing an image with a caption is a page-layout "
              "heuristic, never a reading of the figure. What the licence "
              "permits remains the business of check-droits.py."},
    "emprunts.garde_fou": {
        "fr": "Le script ne récupère un fichier que depuis une localisation "
              "déclarée en accès ouvert par l'index. Il ne contourne aucun "
              "contrôle d'accès, ne présente aucun identifiant et ne tente "
              "aucune adresse devinée.",
        "en": "The script retrieves a file only from a location the index "
              "declares to be open access. It works around no access "
              "control, presents no credentials and tries no guessed "
              "address."},
    "emprunts.refus_non_ouvert": {
        "fr": "Récupération refusée : la source n'est pas déclarée en accès "
              "ouvert par l'index. {garde_fou} Un article sous abonnement se "
              "demande à son éditeur, il ne se contourne pas : suivre la "
              "procédure de demande d'autorisation de "
              "references/droits-figures.md, puis consigner la réponse "
              "écrite dans le registre des figures empruntées.",
        "en": "Retrieval refused: the index does not declare this source to "
              "be open access. {garde_fou} An article behind a subscription "
              "is asked of its publisher, it is not worked around: follow "
              "the permission request procedure in "
              "references/droits-figures.md, then record the written answer "
              "in the register of borrowed figures."},
    "emprunts.refus_adresse_absente": {
        "fr": "Récupération refusée : l'index déclare la source ouverte mais "
              "ne publie aucune adresse de fichier. {garde_fou} Ouvrir la "
              "page de dépôt à la main et enregistrer le fichier, plutôt que "
              "d'essayer une adresse supposée.",
        "en": "Retrieval refused: the index declares the source open but "
              "publishes no file address. {garde_fou} Open the repository "
              "page by hand and save the file, rather than trying an assumed "
              "address."},
    "emprunts.refus_localisation_inconnue": {
        "fr": "Récupération refusée : l'état d'accès de la source n'est pas "
              "établi. Une absence d'information n'est ni une interdiction, "
              "ni une permission, et elle ne vaut pas licence de "
              "télécharger. {garde_fou}",
        "en": "Retrieval refused: the access state of the source is not "
              "established. An absence of information is neither a ban nor a "
              "permission, and it is no licence to download. {garde_fou}"},

    # emprunts.py : appariement image-legende-page
    "emprunts.a.sans_backend": {
        "fr": "aucun backend de texte : la légende n'est pas lisible, elle "
              "n'est pas inventée",
        "en": "no text backend: the caption cannot be read, and it is not "
              "invented"},
    "emprunts.a.page_inconnue": {
        "fr": "page d'origine non fournie par le backend {backend} : "
              "l'appariement à une légende est impossible",
        "en": "the {backend} backend does not give the source page: pairing "
              "with a caption is impossible"},
    "emprunts.a.backend_defaut": {
        "fr": "d'extraction", "en": "extraction"},
    "emprunts.a.aucune_legende": {
        "fr": "aucune légende repérée sur la page {page} : la figure y est "
              "peut-être sans numéro, ou son texte est dans l'image",
        "en": "no caption found on page {page}: the figure there may carry "
              "no number, or its text may be inside the image"},
    "emprunts.a.plus_d_images": {
        "fr": "plus d'images que de légendes sur la page {page} : cette "
              "image reste sans légende",
        "en": "more images than captions on page {page}: this image stays "
              "without a caption"},
    "emprunts.a.direct": {
        "fr": "une seule image et une seule légende sur la page {page} : "
              "appariement direct",
        "en": "a single image and a single caption on page {page}: direct "
              "pairing"},
    "emprunts.a.par_ordre": {
        "fr": "{images} images et {legendes} légendes sur la page {page} : "
              "appariement par ordre de lecture, à vérifier",
        "en": "{images} images and {legendes} captions on page {page}: "
              "paired in reading order, to be checked"},
    "emprunts.a.comptes_divergents": {
        "fr": "{images} images pour {legendes} légendes sur la page {page} : "
              "les comptes divergent, appariement peu sûr, à vérifier",
        "en": "{images} images for {legendes} captions on page {page}: the "
              "counts disagree, the pairing is unsafe, to be checked"},

    # emprunts.py : notes de l'inventaire
    "emprunts.n.fichier_introuvable": {
        "fr": "Fichier introuvable : {source}",
        "en": "File not found: {source}"},
    "emprunts.n.images_absent": {
        "fr": "images.py introuvable : extraction impossible, rien n'est "
              "supposé.",
        "en": "images.py not found: extraction is impossible, nothing is "
              "assumed."},
    "emprunts.n.sans_backend_texte": {
        "fr": "Aucun backend de texte (pypdf ou pdftotext) : les images sont "
              "rendues sans légende, et aucune légende n'est inventée. "
              "Installer un backend, ou apparier à la main.",
        "en": "No text backend (pypdf or pdftotext): the images come back "
              "without captions, and no caption is invented. Install a "
              "backend, or pair them by hand."},
    "emprunts.n.legendes_orphelines": {
        "fr": "{n} légende(s) sans image extraite : la figure est "
              "probablement vectorielle, tracée dans la page plutôt que "
              "posée comme image. Passer par une capture de la zone.",
        "en": "{n} caption(s) with no image extracted: the figure is most "
              "likely vector art, drawn into the page rather than placed as "
              "an image. Capture the area instead."},
    "emprunts.n.appariements_douteux": {
        "fr": "{n} appariement(s) de confiance moyenne ou faible : vérifier "
              "la page avant de citer le numéro de figure.",
        "en": "{n} pairing(s) of medium or low confidence: check the page "
              "before citing the figure number."},

    # emprunts.py : localisation
    "emprunts.l.reseau_desactive": {
        "fr": "--reseau désactivé : aucun index consulté, la localisation "
              "reste inconnue et rien n'est téléchargé.",
        "en": "--reseau is off: no index queried, the location stays unknown "
              "and nothing is downloaded."},
    "emprunts.l.vsrc_absent": {
        "fr": "verify-sources.py introuvable : la requête d'index est "
              "impossible.",
        "en": "verify-sources.py not found: the index query is impossible."},
    "emprunts.l.injoignable": {
        "fr": "OpenAlex injoignable : mesure omise, jamais remplacée par une "
              "valeur supposée.",
        "en": "OpenAlex unreachable: the measurement is omitted, never "
              "replaced by an assumed value."},
    "emprunts.l.doi_non_trouve": {
        "fr": "DOI non trouvé par OpenAlex : l'état d'accès reste inconnu.",
        "en": "DOI not found by OpenAlex: the access state stays unknown."},
    "emprunts.l.statut_non_precise": {
        "fr": "statut non précisé", "en": "status not stated"},
    "emprunts.l.ouvert_avec_pdf": {
        "fr": "accès ouvert déclaré ({statut}), adresse de PDF publiée par "
              "l'index.",
        "en": "open access declared ({statut}), PDF address published by the "
              "index."},
    "emprunts.l.ouvert_sans_pdf": {
        "fr": "accès ouvert déclaré ({statut}) mais aucune adresse de PDF "
              "publiée : ouvrir la page de dépôt à la main, aucune adresse "
              "n'est devinée ici.",
        "en": "open access declared ({statut}) but no PDF address "
              "published: open the repository page by hand, no address is "
              "guessed here."},
    "emprunts.l.non_ouvert": {
        "fr": "l'index déclare la source hors accès ouvert (statut "
              "{statut}).",
        "en": "the index declares the source outside open access (status "
              "{statut})."},
    "emprunts.l.indetermine": {
        "fr": "l'index ne déclare pas l'état d'accès de cette source : ni "
              "ouverte, ni fermée, indéterminée.",
        "en": "the index does not declare the access state of this source: "
              "neither open, nor closed, undetermined."},

    # emprunts.py : recuperation
    "emprunts.r.injoignable": {
        "fr": "Adresse ouverte injoignable ({erreur}) : rien n'est écrit, et "
              "aucune autre adresse n'est tentée.",
        "en": "The open address is unreachable ({erreur}): nothing is "
              "written, and no other address is tried."},
    "emprunts.r.pas_un_pdf": {
        "fr": "La réponse n'est pas un PDF (en-tête %PDF- absent) : probable "
              "page intermédiaire du dépôt. Rien n'est écrit.",
        "en": "The response is not a PDF (no %PDF- header): most likely an "
              "intermediate page of the repository. Nothing is written."},
    "emprunts.r.recuperee": {
        "fr": "Fichier récupéré depuis la localisation ouverte déclarée par "
              "l'index.",
        "en": "File retrieved from the open location declared by the "
              "index."},

    # emprunts.py : entree de registre et voies de repli
    "emprunts.e.libelle_defaut": {
        "fr": "Figure {numero}", "en": "Figure {numero}"},
    "emprunts.v.entete": {
        "fr": "Reproduction non acquise, deux voies restent ouvertes.",
        "en": "Reproduction is not secured, two paths remain open."},
    "emprunts.v.demande": {
        "fr": "demande écrite d'autorisation à l'éditeur",
        "en": "written permission request to the publisher"},
    "emprunts.v.doi_defaut": {
        "fr": "de la source", "en": "of the source"},
    "emprunts.v.etape_titulaire": {
        "fr": "Identifier le titulaire : l'éditeur le plus souvent, l'auteur "
              "quand il a conservé ses droits, une agence pour une "
              "photographie.",
        "en": "Identify the rights holder: the publisher most of the time, "
              "the author when they kept their rights, an agency for a "
              "photograph."},
    "emprunts.v.etape_figure": {
        "fr": "Décrire la figure sans ambiguïté : DOI {doi}, numéro de "
              "figure, page.",
        "en": "Describe the figure unambiguously: DOI {doi}, figure number, "
              "page."},
    "emprunts.v.etape_usage": {
        "fr": "Décrire l'usage : support, diffusion, langue, tirage, "
              "caractère commercial ou non, et les modifications prévues.",
        "en": "Describe the use: medium, distribution, language, print run, "
              "commercial or not, and the modifications planned."},
    "emprunts.v.etape_reponse": {
        "fr": "Conserver la réponse écrite avec sa date et sa référence, "
              "puis la consigner dans le registre (clé \"autorisation\").",
        "en": "Keep the written answer with its date and reference, then "
              "record it in the register (key \"autorisation\")."},

    # emprunts.py : etapes de la chaine
    "emprunts.c.source_locale": {
        "fr": "Fichier déjà possédé : aucune requête, aucun téléchargement.",
        "en": "File already held: no request, no download."},
    "emprunts.c.inventaire_fait": {
        "fr": "{images} image(s), {appariements} appariement(s).",
        "en": "{images} image(s), {appariements} pairing(s)."},
    "emprunts.c.sans_fichier": {
        "fr": "Aucun fichier disponible : l'inventaire n'a rien à apparier.",
        "en": "No file available: the inventory has nothing to pair."},
    "emprunts.c.droits_absent": {
        "fr": "check-droits.py introuvable.",
        "en": "check-droits.py not found."},
    "emprunts.c.registre": {
        "fr": "{entrees} entrée(s), {erreurs} erreur(s), {avertissements} "
              "avertissement(s).",
        "en": "{entrees} entry or entries, {erreurs} error(s), "
              "{avertissements} warning(s)."},

    # emprunts.py : rapports texte
    "emprunts.inv.titre": {
        "fr": "Inventaire des figures : {source}",
        "en": "Inventory of figures: {source}"},
    "emprunts.inv.verdict": {
        "fr": "Verdict : {verdict}", "en": "Verdict: {verdict}"},
    "emprunts.inv.images": {
        "fr": "Images : {uniques} unique(s), {doublons} doublon(s), backend "
              "{backend}",
        "en": "Images: {uniques} unique, {doublons} duplicate(s), backend "
              "{backend}"},
    "emprunts.inv.texte": {
        "fr": "Texte : {pages} page(s), backend {backend}",
        "en": "Text: {pages} page(s), backend {backend}"},
    "emprunts.inv.aucun_backend": {"fr": "aucun", "en": "none"},
    "emprunts.inv.appariement": {
        "fr": "[{niveau}] {libelle}", "en": "[{niveau}] {libelle}"},
    "emprunts.inv.non_identifiee": {
        "fr": "figure non identifiée", "en": "figure not identified"},
    "emprunts.inv.fichier": {
        "fr": "Fichier : {fichier} (page {page})",
        "en": "File: {fichier} (page {page})"},
    "emprunts.inv.page_inconnue": {"fr": "inconnue", "en": "unknown"},
    "emprunts.inv.legende": {
        "fr": "Légende : {legende}", "en": "Caption: {legende}"},
    "emprunts.inv.legende_absente": {
        "fr": "absente, non inventée", "en": "absent, not invented"},
    "emprunts.inv.confiance": {
        "fr": "Confiance : {valeur}, {motif}",
        "en": "Confidence: {valeur}, {motif}"},
    "emprunts.inv.sans_image": {
        "fr": "[SANS IMAGE] {libelle} (page {page}) : {legende}",
        "en": "[NO IMAGE] {libelle} (page {page}): {legende}"},
    "emprunts.inv.legende_vide": {
        "fr": "légende absente", "en": "caption absent"},
    "emprunts.inv.notes": {"fr": "Notes :", "en": "Notes:"},
    "emprunts.inv.notes_aucune": {
        "fr": "Notes : aucune", "en": "Notes: none"},
    "emprunts.limite_ligne": {
        "fr": "Limite : {limite}", "en": "Limit: {limite}"},
    "emprunts.garde_fou_ligne": {
        "fr": "Garde-fou : {garde_fou}", "en": "Guard rail: {garde_fou}"},
    "emprunts.loc.titre": {
        "fr": "Localisation en accès ouvert : {doi}",
        "en": "Open-access location: {doi}"},
    "emprunts.loc.etat": {"fr": "État : {etat}", "en": "State: {etat}"},
    "emprunts.loc.motif": {"fr": "Motif : {motif}", "en": "Reason: {motif}"},
    "emprunts.loc.index": {
        "fr": "Index consulté : {reponse}", "en": "Index queried: {reponse}"},
    "emprunts.loc.oui": {"fr": "oui", "en": "yes"},
    "emprunts.loc.non": {"fr": "non", "en": "no"},
    "emprunts.loc.titre_source": {
        "fr": "Titre : {titre}", "en": "Title: {titre}"},
    "emprunts.loc.revue": {
        "fr": "Revue : {revue}", "en": "Journal: {revue}"},
    "emprunts.loc.auteur": {
        "fr": "Auteur : {auteur}", "en": "Author: {auteur}"},
    "emprunts.loc.acces": {
        "fr": "Accès ouvert : {ouvert} (statut {statut})",
        "en": "Open access: {ouvert} (status {statut})"},
    "emprunts.loc.statut_non_declare": {
        "fr": "non déclaré", "en": "not declared"},
    "emprunts.loc.licence": {
        "fr": "Licence déclarée : {licence}",
        "en": "Declared licence: {licence}"},
    "emprunts.loc.pdf": {
        "fr": "PDF ouvert : {url}", "en": "Open PDF: {url}"},
    "emprunts.loc.page": {
        "fr": "Page de dépôt : {url}", "en": "Repository page: {url}"},
    "emprunts.rec.titre": {
        "fr": "Récupération : {etat}", "en": "Retrieval: {etat}"},
    "emprunts.rec.adresse": {
        "fr": "Adresse : {url}", "en": "Address: {url}"},
    "emprunts.rec.fichier": {
        "fr": "Fichier : {fichier} ({octets} octets)",
        "en": "File: {fichier} ({octets} bytes)"},
    "emprunts.ch.titre": {
        "fr": "Chaîne d'emprunt : {doi}", "en": "Borrowing chain: {doi}"},
    "emprunts.ch.verdict": {
        "fr": "Verdict : {verdict}", "en": "Verdict: {verdict}"},
    "emprunts.ch.entree": {
        "fr": "Entrée de registre {id}", "en": "Register entry {id}"},
    "emprunts.ch.libelle": {
        "fr": "Libellé : {libelle}", "en": "Label: {libelle}"},
    "emprunts.ch.a_etablir": {"fr": "à établir", "en": "to establish"},
    "emprunts.ch.legende_origine": {
        "fr": "Légende d'origine : {legende}",
        "en": "Original caption: {legende}"},
    "emprunts.ch.absente": {"fr": "absente", "en": "absent"},
    "emprunts.ch.source": {
        "fr": "Source : {source}", "en": "Source: {source}"},
    "emprunts.ch.licence": {
        "fr": "Licence : {licence}", "en": "Licence: {licence}"},
    "emprunts.ch.licence_inconnue": {"fr": "inconnue", "en": "unknown"},
    "emprunts.ch.verdict_entree": {
        "fr": "Verdict : {verdict}", "en": "Verdict: {verdict}"},
    "emprunts.ch.indetermine": {
        "fr": "indéterminé", "en": "undetermined"},
    "emprunts.ch.modifications": {
        "fr": "Modifications : {modifications}",
        "en": "Modifications: {modifications}"},
    "emprunts.ch.fichier": {
        "fr": "Fichier : {fichier}", "en": "File: {fichier}"},
    "emprunts.ch.aucun_fichier": {"fr": "aucun", "en": "none"},
    "emprunts.ch.confiance": {
        "fr": "Confiance d'appariement : {confiance}",
        "en": "Pairing confidence: {confiance}"},
    "emprunts.ch.erreurs_registre": {
        "fr": "Erreurs de registre :", "en": "Register errors:"},
    "emprunts.ch.avertissements_registre": {
        "fr": "Avertissements de registre :", "en": "Register warnings:"},
    "emprunts.ch.registre_ecrit": {
        "fr": "Registre écrit : {chemin}", "en": "Register written: {chemin}"},
    "emprunts.v.voie_1": {
        "fr": "1. {voie} ({reference})", "en": "1. {voie} ({reference})"},
    "emprunts.v.voie_2": {"fr": "2. {voie}", "en": "2. {voie}"},
    "emprunts.v.mention": {
        "fr": "Mention : {mention}", "en": "Credit line: {mention}"},
    "emprunts.v.types": {
        "fr": "Types de figures : {types}", "en": "Figure types: {types}"},
}


# --- Valeurs machine et leur libelle ----------------------------------------
# La CLE de chaque entree est la valeur machine, celle qui circule dans les
# structures de donnees et dans le JSON. Elle ne change jamais, dans aucune
# langue. Seule la valeur du dictionnaire change de langue. La table est
# explicite a dessein : une valeur ajoutee au code sans etre ajoutee ici sort
# marquee par valeur(), et valeurs_sans_libelle() la nomme.

VALEURS = {

    "scorecard.verdict": {
        "Pret": {"fr": "Pret", "en": "Ready"},
        "A reviser": {"fr": "A reviser", "en": "To revise"},
        "A refondre": {"fr": "A refondre", "en": "To rework"},
        "Non evaluable": {"fr": "Non evaluable", "en": "Not assessable"},
    },
    "scorecard.decision": {
        "accepter": {"fr": "accepter", "en": "accept"},
        "revision mineure": {"fr": "revision mineure",
                             "en": "minor revision"},
        "revision majeure": {"fr": "revision majeure",
                             "en": "major revision"},
        "refus": {"fr": "refus", "en": "reject"},
        "non evaluable": {"fr": "non evaluable", "en": "not assessable"},
    },
    "scorecard.axe": {
        "Style": {"fr": "Style", "en": "Style"},
        "Sources": {"fr": "Sources", "en": "Sources"},
        "Tracabilite": {"fr": "Tracabilite", "en": "Traceability"},
        "Terminologie et nombres": {"fr": "Terminologie et nombres",
                                    "en": "Terminology and numbers"},
        "Lisibilite": {"fr": "Lisibilite", "en": "Readability"},
    },
    "scorecard.deduction": {
        "ecart critique de style": {"fr": "ecart critique de style",
                                    "en": "critical style deviation"},
        "ecart majeur": {"fr": "ecart majeur", "en": "major deviation"},
        "ecart mineur": {"fr": "ecart mineur", "en": "minor deviation"},
        "tic d'ecriture IA": {"fr": "tic d'ecriture IA",
                              "en": "AI writing tic"},
        "URL a nettoyer": {"fr": "URL a nettoyer", "en": "URL to clean"},
        "source en double": {"fr": "source en double",
                             "en": "duplicate source"},
        "DOI douteux": {"fr": "DOI douteux", "en": "doubtful DOI"},
        "citation pendante": {"fr": "citation pendante",
                              "en": "dangling citation"},
        "reference orpheline": {"fr": "reference orpheline",
                                "en": "orphan reference"},
        "appel sans definition": {"fr": "appel sans definition",
                                  "en": "call without definition"},
        "objet jamais appele": {"fr": "objet jamais appele",
                                "en": "object never called"},
        "paragraphe duplique": {"fr": "paragraphe duplique",
                                "en": "duplicate paragraph"},
        "sigle non defini": {"fr": "sigle non defini",
                             "en": "undefined acronym"},
        "sigle avant definition": {"fr": "sigle avant definition",
                                   "en": "acronym before its definition"},
        "variante orthographique": {"fr": "variante orthographique",
                                    "en": "spelling variant"},
        "pourcentage impossible": {"fr": "pourcentage impossible",
                                   "en": "impossible percentage"},
        "partition incoherente": {"fr": "partition incoherente",
                                  "en": "inconsistent partition"},
        "separateur decimal mixte": {"fr": "separateur decimal mixte",
                                     "en": "mixed decimal separator"},
        "rythme monotone": {"fr": "rythme monotone",
                            "en": "monotonous rhythm"},
        "phrases trop longues": {"fr": "phrases trop longues",
                                 "en": "sentences too long"},
        "LIX hors bande": {"fr": "LIX hors bande", "en": "LIX out of band"},
        "trop de passif": {"fr": "trop de passif", "en": "too much passive"},
        "densite lexicale faible": {"fr": "densite lexicale faible",
                                    "en": "low lexical density"},
    },
    "lint.severite": {
        "critique": {"fr": "critique", "en": "critical"},
        "majeur": {"fr": "majeur", "en": "major"},
        "mineur": {"fr": "mineur", "en": "minor"},
    },
    "traceability.objet": {
        "figure": {"fr": "figure", "en": "figure"},
        "tableau": {"fr": "tableau", "en": "table"},
        "equation": {"fr": "equation", "en": "equation"},
        "annexe": {"fr": "annexe", "en": "appendix"},
    },
    # Pluriel employe par les constats de numerotation.
    "traceability.objets": {
        "figure": {"fr": "figures", "en": "figures"},
        "tableau": {"fr": "tableaux", "en": "tables"},
        "equation": {"fr": "equations", "en": "equations"},
        "annexe": {"fr": "annexes", "en": "appendices"},
    },
    "verify.palier": {
        "revue-a-comite": {"fr": "revue-a-comite", "en": "peer-reviewed"},
        "preprint": {"fr": "preprint", "en": "preprint"},
        "institutionnel": {"fr": "institutionnel", "en": "institutional"},
        "encyclopedie": {"fr": "encyclopedie", "en": "encyclopedia"},
        "presse-blog": {"fr": "presse-blog", "en": "press-blog"},
        "non-classe": {"fr": "non-classe", "en": "unclassified"},
    },
    "verify.verdict_doi": {
        "verifie": {"fr": "verifie", "en": "verified"},
        "plausible": {"fr": "plausible", "en": "plausible"},
        "inverifiable": {"fr": "inverifiable", "en": "unverifiable"},
        "fabrique": {"fr": "fabrique", "en": "fabricated"},
    },
    "verify.statut_retractation": {
        "retracte": {"fr": "retracte", "en": "retracted"},
        "avis de retractation": {"fr": "avis de retractation",
                                 "en": "retraction notice"},
        "non declare": {"fr": "non declare", "en": "not declared"},
        "inconnu": {"fr": "inconnu", "en": "unknown"},
    },
    "temporel.severite": {
        "signal": {"fr": "signal", "en": "signal"},
        "avertissement": {"fr": "avertissement", "en": "warning"},
    },
    "lecture.verdict": {
        "lecture fiable": {"fr": "lecture fiable", "en": "reliable read"},
        "lecture partielle": {"fr": "lecture partielle",
                              "en": "partial read"},
        "lecture non fiable": {"fr": "lecture non fiable",
                               "en": "unreliable read"},
        "non mesurable": {"fr": "non mesurable", "en": "not measurable"},
    },
    "fuites.verdict": {
        "fuites confirmees": {"fr": "fuites confirmees",
                              "en": "confirmed leaks"},
        "fuites probables": {"fr": "fuites probables",
                             "en": "probable leaks"},
        "traces sans identite lisible": {
            "fr": "traces sans identite lisible",
            "en": "traces with no readable identity"},
        "rien a signaler": {"fr": "rien a signaler",
                            "en": "nothing to report"},
    },
    # Les libelles de confiance sont alignes sur une largeur fixe : le
    # rapport les imprime entre crochets en tete de chaque constat, et une
    # colonne qui bouge rend la lecture penible. Le francais garde les
    # chaines actuelles a l'octet pres, l'anglais s'aligne sur le plus long
    # de ses propres mots.
    "fuites.confiance": {
        "confirme": {"fr": "CONFIRME ", "en": "CONFIRMED  "},
        "probable": {"fr": "probable ", "en": "probable   "},
        "informatif": {"fr": "informatif", "en": "informative"},
        "douteux": {"fr": "douteux   ", "en": "doubtful   "},
    },
    "fuites.regle": {
        "propriete de document": {"fr": "propriete de document",
                                  "en": "document property"},
        "historique d'edition": {"fr": "historique d'edition",
                                 "en": "editing history"},
        "modifications suivies": {"fr": "modifications suivies",
                                  "en": "tracked changes"},
        "texte masque": {"fr": "texte masque", "en": "hidden text"},
        "commentaires": {"fr": "commentaires", "en": "comments"},
        "donnees applicatives": {"fr": "donnees applicatives",
                                 "en": "application data"},
        "collaborateurs": {"fr": "collaborateurs", "en": "contributors"},
        "notes du presentateur": {"fr": "notes du presentateur",
                                  "en": "speaker notes"},
        "chemin local": {"fr": "chemin local", "en": "local path"},
        "mise a jour incrementale": {"fr": "mise a jour incrementale",
                                     "en": "incremental update"},
        "metadonnees XMP": {"fr": "metadonnees XMP", "en": "XMP metadata"},
        "chiffrement": {"fr": "chiffrement", "en": "encryption"},
        "fichier embarque": {"fr": "fichier embarque",
                             "en": "embedded file"},
    },
    "dispo.verdict": {
        "declaration absente": {"fr": "declaration absente",
                                "en": "statement absent"},
        "declaration incoherente": {"fr": "declaration incoherente",
                                    "en": "statement inconsistent"},
        "regime non identifie": {"fr": "regime non identifie",
                                 "en": "regime not identified"},
        "declaration a completer": {"fr": "declaration a completer",
                                    "en": "statement to complete"},
        "declaration conforme": {"fr": "declaration conforme",
                                 "en": "statement compliant"},
    },
    "dispo.regime": {
        "depot-ouvert": {"fr": "dépôt public ouvert",
                         "en": "open public repository"},
        "sur-demande": {"fr": "sur demande motivée",
                        "en": "on motivated request"},
        "embargo": {"fr": "embargo", "en": "embargo"},
        "restriction-legale": {"fr": "non partageable pour raison légale",
                               "en": "not shareable on legal grounds"},
        "donnees-de-tiers": {"fr": "données de tiers",
                             "en": "third-party data"},
        "aucune-donnee": {"fr": "aucune donnée nouvelle",
                          "en": "no new data"},
    },
    # Meme alignement que fuites.confiance, et pour la meme raison.
    "dispo.confiance": {
        "confirme": {"fr": "CONFIRME ", "en": "CONFIRMED  "},
        "probable": {"fr": "probable ", "en": "probable   "},
        "informatif": {"fr": "informatif", "en": "informative"},
        "douteux": {"fr": "douteux   ", "en": "doubtful   "},
    },
    "droits.verdict": {
        "reutilisable avec attribution": {
            "fr": "reutilisable avec attribution",
            "en": "reusable with attribution"},
        "reutilisable sous conditions": {
            "fr": "reutilisable sous conditions",
            "en": "reusable under conditions"},
        "autorisation requise": {"fr": "autorisation requise",
                                 "en": "permission required"},
        "licence inconnue": {"fr": "licence inconnue",
                             "en": "licence unknown"},
    },
    "droits.verdict_registre": {
        "registre invalide": {"fr": "registre invalide",
                              "en": "register invalid"},
        "autorisations a obtenir": {"fr": "autorisations a obtenir",
                                    "en": "permissions to obtain"},
        "licences a etablir": {"fr": "licences a etablir",
                               "en": "licences to establish"},
        "credits complets": {"fr": "credits complets",
                             "en": "credits complete"},
    },
    "droits.autorisation": {
        "non demandee": {"fr": "non demandee", "en": "not requested"},
        "demandee": {"fr": "demandee", "en": "requested"},
        "obtenue": {"fr": "obtenue", "en": "granted"},
        "refusee": {"fr": "refusee", "en": "refused"},
    },
    # Nom d'une famille de licence, indexe par son CODE : le code est la
    # valeur machine, il ne bouge pas. Un sigle Creative Commons est le meme
    # dans les deux langues, seules deux entrees ont un nom traduisible.
    "droits.licence": {
        "cc0": {"fr": "CC0", "en": "CC0"},
        "domaine-public": {"fr": "Domaine public", "en": "Public domain"},
        "cc-by": {"fr": "CC BY", "en": "CC BY"},
        "cc-by-sa": {"fr": "CC BY-SA", "en": "CC BY-SA"},
        "cc-by-nc": {"fr": "CC BY-NC", "en": "CC BY-NC"},
        "cc-by-nc-sa": {"fr": "CC BY-NC-SA", "en": "CC BY-NC-SA"},
        "cc-by-nd": {"fr": "CC BY-ND", "en": "CC BY-ND"},
        "cc-by-nc-nd": {"fr": "CC BY-NC-ND", "en": "CC BY-NC-ND"},
        "tous-droits-reserves": {"fr": "Tous droits réservés",
                                 "en": "All rights reserved"},
    },
    # Conditions d'editeur rencontrees dans le tableau license de Crossref.
    # La cle est le libelle francais porte par la fiche, donc par le JSON.
    "droits.editeur": {
        "Elsevier, licence de fouille de textes et de données": {
            "fr": "Elsevier, licence de fouille de textes et de données",
            "en": "Elsevier, text and data mining licence"},
        "Elsevier, licence utilisateur": {
            "fr": "Elsevier, licence utilisateur",
            "en": "Elsevier, user licence"},
        "Springer Nature, fouille de textes et de données": {
            "fr": "Springer Nature, fouille de textes et de données",
            "en": "Springer Nature, text and data mining"},
        "Springer, fouille de textes et de données": {
            "fr": "Springer, fouille de textes et de données",
            "en": "Springer, text and data mining"},
        "Wiley, conditions générales": {
            "fr": "Wiley, conditions générales",
            "en": "Wiley, terms and conditions"},
        "ACS, politique de droits": {
            "fr": "ACS, politique de droits", "en": "ACS, rights policy"},
        "IEEE, politique de droits": {
            "fr": "IEEE, politique de droits", "en": "IEEE, rights policy"},
        "AIP, droits et permissions": {
            "fr": "AIP, droits et permissions",
            "en": "AIP, rights and permissions"},
        "RSC, licences et permissions": {
            "fr": "RSC, licences et permissions",
            "en": "RSC, licences and permissions"},
    },
    "droits.element": {
        "titre": {"fr": "titre", "en": "title"},
        "auteur": {"fr": "auteur", "en": "author"},
        "source": {"fr": "source", "en": "source"},
        "licence": {"fr": "licence", "en": "licence"},
    },
    "emprunts.etat_localisation": {
        "acces ouvert confirme": {"fr": "acces ouvert confirme",
                                  "en": "open access confirmed"},
        "acces ouvert sans fichier": {"fr": "acces ouvert sans fichier",
                                      "en": "open access without a file"},
        "acces non ouvert": {"fr": "acces non ouvert",
                             "en": "access not open"},
        "localisation inconnue": {"fr": "localisation inconnue",
                                  "en": "location unknown"},
    },
    "emprunts.etat_recuperation": {
        "recuperee": {"fr": "recuperee", "en": "retrieved"},
        "refus source non ouverte": {"fr": "refus source non ouverte",
                                     "en": "refused, source not open"},
        "refus adresse absente": {"fr": "refus adresse absente",
                                  "en": "refused, no address"},
        "refus localisation inconnue": {"fr": "refus localisation inconnue",
                                        "en": "refused, location unknown"},
        "echec reseau": {"fr": "echec reseau", "en": "network failure"},
        "echec contenu non pdf": {"fr": "echec contenu non pdf",
                                  "en": "failure, content is not a PDF"},
    },
    "emprunts.confiance": {
        "elevee": {"fr": "elevee", "en": "high"},
        "moyenne": {"fr": "moyenne", "en": "medium"},
        "faible": {"fr": "faible", "en": "low"},
        "nulle": {"fr": "nulle", "en": "none"},
    },
    "emprunts.verdict_inventaire": {
        "inventaire apparie": {"fr": "inventaire apparie",
                               "en": "inventory paired"},
        "inventaire partiel": {"fr": "inventaire partiel",
                               "en": "inventory partial"},
        "inventaire sans legende": {"fr": "inventaire sans legende",
                                    "en": "inventory without captions"},
        "inventaire non apparie": {"fr": "inventaire non apparie",
                                   "en": "inventory not paired"},
        "extraction impossible": {"fr": "extraction impossible",
                                  "en": "extraction impossible"},
    },
    "emprunts.verdict_chaine": {
        "emprunt prepare": {"fr": "emprunt prepare",
                            "en": "borrowing prepared"},
        "autorisation a demander": {"fr": "autorisation a demander",
                                    "en": "permission to request"},
        "licence a etablir": {"fr": "licence a etablir",
                              "en": "licence to establish"},
        "source non ouverte": {"fr": "source non ouverte",
                               "en": "source not open"},
        "chaine incomplete": {"fr": "chaine incomplete",
                              "en": "chain incomplete"},
    },
    # Statuts d'etape qui n'appartiennent a aucun des espaces fermes
    # ci-dessus : ils sont propres a l'enchainement.
    "emprunts.statut_etape": {
        "source locale fournie": {"fr": "source locale fournie",
                                  "en": "local source provided"},
        "non exécutée": {"fr": "non exécutée", "en": "not run"},
        "indisponible": {"fr": "indisponible", "en": "unavailable"},
        "valide": {"fr": "valide", "en": "valid"},
        "invalide": {"fr": "invalide", "en": "invalid"},
    },
}


# Messages des regles de lint-style.py. La cle est le message francais tel
# qu'il figure dans REGLES et REGLES_EN : c'est lui la valeur portee par le
# constat, donc par le JSON. Les messages construits avec des nombres
# (orthographe melangee, densite de tirets, part de passif) ne sont pas ici,
# ils passent par une cle parametree de LIBELLES.
VALEURS["lint.message"] = {
    "Tiret cadratin ou demi-cadratin. Utiliser parenthèses ou virgules.": {
        "fr": "Tiret cadratin ou demi-cadratin. Utiliser parenthèses ou "
              "virgules.",
        "en": "Em dash or en dash. Use parentheses or commas."},
    "Guillemet ou apostrophe courbe. Utiliser la typographie droite.": {
        "fr": "Guillemet ou apostrophe courbe. Utiliser la typographie "
              "droite.",
        "en": "Curly quotation mark or apostrophe. Use straight typography."},
    "Terme promotionnel banni.": {
        "fr": "Terme promotionnel banni.",
        "en": "Banned promotional term."},
    "Tournure promotionnelle bannie.": {
        "fr": "Tournure promotionnelle bannie.",
        "en": "Banned promotional phrase."},
    "Paramètre de suivi dans une URL. Le retirer.": {
        "fr": "Paramètre de suivi dans une URL. Le retirer.",
        "en": "Tracking parameter in a URL. Remove it."},
    "Virgule avant et/ou. Vérifier que ce n'est pas une virgule d'Oxford.": {
        "fr": "Virgule avant et/ou. Vérifier que ce n'est pas une virgule "
              "d'Oxford.",
        "en": "Comma before et/ou. Check that it is not a serial comma."},
    "Tournure faible. Préférer un verbe simple ou le fait.": {
        "fr": "Tournure faible. Préférer un verbe simple ou le fait.",
        "en": "Weak phrasing. Prefer a plain verb or the fact itself."},
    "« au-delà » banni. Reformuler (de plus de, en plus de).": {
        "fr": "« au-delà » banni. Reformuler (de plus de, en plus de).",
        "en": "\"au-delà\" is banned. Rephrase (de plus de, en plus de)."},
    "Métadiscours. Entrer directement en matière.": {
        "fr": "Métadiscours. Entrer directement en matière.",
        "en": "Metadiscourse. Get to the point directly."},
    "Pronom indéfini « on ». Préférer une tournure passive ou « nous ».": {
        "fr": "Pronom indéfini « on ». Préférer une tournure passive ou "
              "« nous ».",
        "en": "Indefinite pronoun \"on\". Prefer a passive form or \"nous\"."},
    "Quantificateur vague. Chiffrer.": {
        "fr": "Quantificateur vague. Chiffrer.",
        "en": "Vague quantifier. Give a figure."},
    "Verbe tic fréquent à l'écrit IA. Vérifier qu'il porte un fait.": {
        "fr": "Verbe tic fréquent à l'écrit IA. Vérifier qu'il porte un fait.",
        "en": "Verbal tic common in AI writing. Check that it carries a "
              "fact."},
    "Caractère de largeur nulle. Le retirer : il casse recherche et diff.": {
        "fr": "Caractère de largeur nulle. Le retirer : il casse recherche "
              "et diff.",
        "en": "Zero-width character. Remove it: it breaks search and diff."},
    "Trait d'union conditionnel invisible. Le retirer.": {
        "fr": "Trait d'union conditionnel invisible. Le retirer.",
        "en": "Invisible soft hyphen. Remove it."},
    "Contrôle bidirectionnel. Il peut faire lire un texte autrement qu'il "
    "n'est écrit.": {
        "fr": "Contrôle bidirectionnel. Il peut faire lire un texte autrement "
              "qu'il n'est écrit.",
        "en": "Bidirectional control. It can make a text read otherwise than "
              "it is written."},
    "Caractère de tag Unicode, invisible et porteur de données.": {
        "fr": "Caractère de tag Unicode, invisible et porteur de données.",
        "en": "Unicode tag character, invisible and data-bearing."},
    "Caractère de zone à usage privé : son rendu dépend de la police.": {
        "fr": "Caractère de zone à usage privé : son rendu dépend de la "
              "police.",
        "en": "Private use area character: its rendering depends on the "
              "font."},
    "Espace typographique exotique. Préférer l'espace ordinaire ou "
    "l'insécable.": {
        "fr": "Espace typographique exotique. Préférer l'espace ordinaire ou "
              "l'insécable.",
        "en": "Exotic typographic space. Prefer the ordinary or "
              "non-breaking space."},
    "Liant de largeur nulle entre deux lettres latines, où il ne sert à "
    "rien. En écriture arabe ou indienne il serait légitime.": {
        "fr": "Liant de largeur nulle entre deux lettres latines, où il ne "
              "sert à rien. En écriture arabe ou indienne il serait "
              "légitime.",
        "en": "Zero-width joiner between two Latin letters, where it serves "
              "no purpose. In Arabic or Indic script it would be "
              "legitimate."},
}

VALEURS["lint.message"].update({
    "Terme du vocabulaire en excès mesuré dans les textes assistés par "
    "modèle. Nommer le fait plutôt que le qualifier.": {
        "fr": "Terme du vocabulaire en excès mesuré dans les textes assistés "
              "par modèle. Nommer le fait plutôt que le qualifier.",
        "en": "Term from the vocabulary measured in excess in "
              "model-assisted texts. Name the fact rather than qualify it."},
    "« landscape » au sens figuré. Nommer le domaine ou l'ensemble visé.": {
        "fr": "« landscape » au sens figuré. Nommer le domaine ou l'ensemble "
              "visé.",
        "en": "\"landscape\" in a figurative sense. Name the field or the "
              "set meant."},
    "Verbe tic fréquent à l'écrit assisté. Vérifier qu'il porte un fait.": {
        "fr": "Verbe tic fréquent à l'écrit assisté. Vérifier qu'il porte un "
              "fait.",
        "en": "Verbal tic common in assisted writing. Check that it carries "
              "a fact."},
    "« navigate » au sens figuré. Nommer l'action réelle.": {
        "fr": "« navigate » au sens figuré. Nommer l'action réelle.",
        "en": "\"navigate\" in a figurative sense. Name the actual action."},
    "« utilize » sans gain de sens sur « use ». Simplifier.": {
        "fr": "« utilize » sans gain de sens sur « use ». Simplifier.",
        "en": "\"utilize\" adds nothing over \"use\". Simplify."},
    "« significant » hors contexte statistique explicite. Le réserver à la "
    "signification statistique et écrire important, substantial ou large "
    "pour l'ampleur.": {
        "fr": "« significant » hors contexte statistique explicite. Le "
              "réserver à la signification statistique et écrire important, "
              "substantial ou large pour l'ampleur.",
        "en": "\"significant\" outside an explicit statistical context. "
              "Reserve it for statistical significance and write important, "
              "substantial or large for magnitude."},
    "Verbe caché sous un substantif. Employer le verbe (assess, analyse, "
    "compare) plutôt que sa périphrase.": {
        "fr": "Verbe caché sous un substantif. Employer le verbe (assess, "
              "analyse, compare) plutôt que sa périphrase.",
        "en": "Verb hidden under a noun. Use the verb (assess, analyse, "
              "compare) rather than its periphrasis."},
    "Modalisateurs empilés. Un seul degré de réserve par affirmation, sinon "
    "la réserve ne dit plus rien.": {
        "fr": "Modalisateurs empilés. Un seul degré de réserve par "
              "affirmation, sinon la réserve ne dit plus rien.",
        "en": "Stacked hedges. One degree of reservation per claim, "
              "otherwise the reservation says nothing."},
    "Espace avant deux-points, point-virgule, point d'exclamation ou "
    "d'interrogation. Correcte en français, fautive en anglais : coller le "
    "signe au mot.": {
        "fr": "Espace avant deux-points, point-virgule, point d'exclamation "
              "ou d'interrogation. Correcte en français, fautive en anglais : "
              "coller le signe au mot.",
        "en": "Space before a colon, semicolon, exclamation or question "
              "mark. Correct in French, wrong in English: attach the mark to "
              "the word."},
    "Nom indénombrable mis au pluriel. Écrire information, research, "
    "evidence, software au singulier.": {
        "fr": "Nom indénombrable mis au pluriel. Écrire information, "
              "research, evidence, software au singulier.",
        "en": "Uncountable noun put in the plural. Write information, "
              "research, evidence, software in the singular."},
    "Faux ami ou calque du français. Vérifier le sens visé (actually = en "
    "fait, eventually = finalement, sensible = raisonnable, allow to + verbe "
    "n'existe pas).": {
        "fr": "Faux ami ou calque du français. Vérifier le sens visé "
              "(actually = en fait, eventually = finalement, sensible = "
              "raisonnable, allow to + verbe n'existe pas).",
        "en": "False friend or calque from French. Check the intended sense "
              "(actually = en fait, eventually = finalement, sensible = "
              "raisonnable, allow to + verb does not exist)."},
})


# Motifs de mesure non faite, portes par les donnees de readability.py et
# recopies par scorecard.py. Deux formes seulement, dont une parametree : la
# table les reconnait par motif ancre, jamais par sous-chaine, pour qu'un
# motif inconnu ressorte marque au lieu d'etre traduit de travers.
LIBELLES.update({
    "motif.aucune_phrase": {
        "fr": "aucune phrase mesurable dans le texte",
        "en": "no measurable sentence in the text"},
    "motif.langue_non_couverte": {
        "fr": "langue « {langue} » hors des langues couvertes ({langues})",
        "en": "language \"{langue}\" outside the covered languages "
              "({langues})"},
})

MOTIFS_MESURE = (
    (re.compile(r"\Aaucune phrase mesurable dans le texte\Z"),
     "motif.aucune_phrase"),
    (re.compile(r"\Alangue « (?P<langue>[^»]*) » hors des langues couvertes "
                r"\((?P<langues>[^)]*)\)\Z"),
     "motif.langue_non_couverte"),
)


# --- Lot des dix outils -----------------------------------------------------
# terminology, numbers, figures, gabarit, logos, images, plan-check, project,
# theme, diff-versions. Meme regle que les dix-sept scripts precedents : la
# valeur machine ne bouge pas, seuls le rapport texte et les messages de la
# ligne de commande passent par ces cles. Les chaines francaises sont
# recopiees a l'octet pres depuis les scripts.

LIBELLES.update({

    # terminology.py
    "terminology.titre": {"fr": "Terminologie", "en": "Terminology"},
    "terminology.glossaire": {"fr": "Glossaire :", "en": "Glossary:"},
    "terminology.aucun_probleme": {
        "fr": "Aucun probleme terminologique.",
        "en": "No terminology problem."},
    "terminology.p.non_definis": {
        "fr": "Sigles employes sans definition : {n}",
        "en": "Acronyms used without a definition: {n}"},
    "terminology.p.avant_definition": {
        "fr": "Sigles employes avant leur definition : {n}",
        "en": "Acronyms used before their definition: {n}"},
    "terminology.p.variantes": {
        "fr": "Variantes d'un meme terme (trait d'union) : {formes}",
        "en": "Variant spellings of one term (hyphen): {formes}"},

    # numbers.py
    "numbers.titre": {"fr": "Integrite numerique",
                      "en": "Numerical integrity"},
    "numbers.langue_analysee": {
        "fr": "langue analysee : {langue}",
        "en": "analysis language: {langue}"},
    "numbers.aucun_probleme": {
        "fr": "Aucun probleme numerique detecte.",
        "en": "No numerical problem found."},
    "numbers.p.impossibles": {
        "fr": "Pourcentages superieurs a 100 : {n}",
        "en": "Percentages above 100: {n}"},
    "numbers.p.partition": {
        "fr": "Partition de pourcentages qui ne somme pas a 100 : {valeurs} "
              "(somme {somme})",
        "en": "Percentage breakdown that does not add up to 100: {valeurs} "
              "(sum {somme})"},
    "numbers.p.separateur_mixte": {
        "fr": "Separateur decimal mixte (virgule et point). Choisir une "
              "seule convention.",
        "en": "Mixed decimal separators (comma and full stop). Pick one "
              "convention and keep it."},
    "numbers.p.espacement": {
        "fr": "Espacement du signe pourcent contraire a la convention "
              "({attendu}) : {occurrences}",
        "en": "Spacing of the percent sign against the convention "
              "({attendu}): {occurrences}"},
    "numbers.attendu_en": {
        "fr": "le signe pourcent se colle au nombre en anglais",
        "en": "the percent sign is attached to the number in English"},
    "numbers.attendu_fr": {
        "fr": "une espace precede le signe pourcent en francais",
        "en": "a space precedes the percent sign in French"},

    # plan-check.py
    "plan.titre": {
        "fr": "Conformite au plan : couverture {couverture}%",
        "en": "Plan conformance: {couverture}% coverage"},
    "plan.manquantes": {
        "fr": "Sections prevues absentes : {sections}",
        "en": "Planned sections missing: {sections}"},
    "plan.hors_plan": {
        "fr": "Sections hors plan (derive) : {sections}",
        "en": "Sections outside the plan (drift): {sections}"},
    "plan.conforme": {
        "fr": "Document conforme au plan.",
        "en": "Document conforms to the plan."},

    # diff-versions.py
    "diff.titre": {"fr": "Journal des ecarts", "en": "Change log"},
    "diff.mots": {
        "fr": "mots : {avant} -> {apres} | similitude {similitude}",
        "en": "words: {avant} -> {apres} | similarity {similitude}"},
    "diff.ajoutees": {
        "fr": "Sections ajoutees : {sections}",
        "en": "Sections added: {sections}"},
    "diff.supprimees": {
        "fr": "Sections supprimees : {sections}",
        "en": "Sections removed: {sections}"},
    "diff.modifiee": {
        "fr": "Modifiee « {section} » : +{ajoutes} / -{supprimes} mots",
        "en": "Modified \"{section}\": +{ajoutes} / -{supprimes} words"},
    "diff.aucun_ecart": {
        "fr": "Aucun ecart de section.",
        "en": "No section-level change."},

    # theme.py : messages de validation seulement. Le CSS et le preambule
    # LaTeX sont des livrables, ils ne passent jamais par ces cles.
    "theme.titre": {
        "fr": "Charte graphique normalisee :",
        "en": "Normalised graphic charter:"},
    "theme.erreurs": {"fr": "Erreurs :", "en": "Errors:"},
    "theme.erreurs_aucune": {"fr": "Erreurs : aucune", "en": "Errors: none"},
    "theme.avertissements": {"fr": "Avertissements :", "en": "Warnings:"},
    "theme.avertissements_aucun": {
        "fr": "Avertissements : aucun", "en": "Warnings: none"},
    "theme.err_lecture": {
        "fr": "Erreur de lecture : {erreur}",
        "en": "Read error: {erreur}"},
    "theme.v.palette_inconnue": {
        "fr": "Palette nommée '{nom}' inconnue (attendu : {noms}) ; repli "
              "sur la palette par défaut.",
        "en": "Named palette '{nom}' unknown (expected: {noms}); falling "
              "back to the default palette."},
    "theme.v.couleur_invalide": {
        "fr": "Couleur '{cle}' invalide : {valeur} (attendu #RRGGBB).",
        "en": "Colour '{cle}' invalid: {valeur} (expected #RRGGBB)."},
    "theme.v.palette_invalide": {
        "fr": "palette[{i}] invalide : {valeur} (attendu #RRGGBB).",
        "en": "palette[{i}] invalid: {valeur} (expected #RRGGBB)."},
    "theme.v.contraste_fond": {
        "fr": "Contraste encre sur fond {ratio:.1f}:1 (< 4.5), texte peu "
              "lisible.",
        "en": "Ink on background contrast {ratio:.1f}:1 (< 4.5), text hard "
              "to read."},
    "theme.v.contraste_palette": {
        "fr": "Contraste encre sur palette[{i}] {ratio:.1f}:1 (< 4.5).",
        "en": "Ink on palette[{i}] contrast {ratio:.1f}:1 (< 4.5)."},
    "theme.v.dichromate": {
        "fr": "Vision dichromate (approximation) : palette[{i}] et "
              "palette[{j}] proches (distance {distance:.0f} < {seuil}) ; "
              "ajouter une forme, un motif ou un libellé pour les distinguer "
              "sans la couleur seule.",
        "en": "Dichromatic vision (approximation): palette[{i}] and "
              "palette[{j}] are close (distance {distance:.0f} < {seuil}); "
              "add a shape, a pattern or a label so they can be told apart "
              "without colour alone."},

    # logos.py
    "logos.etiquette_entree": {"fr": "entree {n}", "en": "entry {n}"},
    "logos.e.aucun_logo": {
        "fr": "le registre ne declare aucun logo",
        "en": "the register declares no logo"},
    "logos.e.id_manquant": {
        "fr": "{etiquette} : champ id manquant",
        "en": "{etiquette}: missing id field"},
    "logos.e.id_double": {
        "fr": "{etiquette} : identifiant en double",
        "en": "{etiquette}: duplicate identifier"},
    "logos.e.fichier_manquant": {
        "fr": "{etiquette} : champ fichier manquant",
        "en": "{etiquette}: missing file field"},
    "logos.e.fichier_absent": {
        "fr": "{etiquette} : fichier absent ({fichier})",
        "en": "{etiquette}: file missing ({fichier})"},
    "logos.e.usage_inconnu": {
        "fr": "{etiquette} : usage inconnu {usages}",
        "en": "{etiquette}: unknown use {usages}"},
    "logos.e.ratio": {
        "fr": "{etiquette} : ratio {reel:.3f} contre {attendu:.3f} declare",
        "en": "{etiquette}: ratio {reel:.3f} against {attendu:.3f} declared"},
    "logos.a.dimensions": {
        "fr": "{etiquette} : dimensions illisibles, resolution non mesuree",
        "en": "{etiquette}: dimensions unreadable, resolution not measured"},
    "logos.a.sous_seuil": {
        "fr": "{etiquette} en {usage} : {dpi} dpi a {cible:.1f} cm, sous le "
              "seuil de {seuil} dpi",
        "en": "{etiquette} in {usage}: {dpi} dpi at {cible:.1f} cm, below "
              "the {seuil} dpi threshold"},
    "logos.a.matriciel": {
        "fr": "{etiquette} : format {ext}, un vectoriel resisterait mieux a "
              "l'agrandissement",
        "en": "{etiquette}: {ext} format, a vector file would hold up better "
              "when enlarged"},
    "logos.a.aucun_pour_usage": {
        "fr": "aucun logo declare pour l'usage {usage}",
        "en": "no logo declared for the {usage} use"},
    "logos.a.cosignature_seul": {
        "fr": "co-signature demandee avec un seul logo, le rang protocolaire "
              "ne joue pas",
        "en": "co-signature asked for with a single logo, precedence order "
              "does not apply"},
    "logos.a.ecarte": {
        "fr": "{etiquette} : fichier absent, ecarte du placement plutot que "
              "reference a vide",
        "en": "{etiquette}: file missing, left out of the placement rather "
              "than referenced empty"},
    "logos.a.docx": {
        "fr": "en docx, ces chemins se passent a gabarit.py remplir --logo, "
              "qui ecrit la relation et le manifeste",
        "en": "in docx, these paths go to gabarit.py remplir --logo, which "
              "writes the relationship and the manifest"},
    "logos.err_registre": {
        "fr": "registre introuvable : {chemin}",
        "en": "register not found: {chemin}"},
    "logos.ligne_erreur": {
        "fr": "erreur        {message}",
        "en": "error         {message}"},
    "logos.ligne_avertissement": {
        "fr": "avertissement {message}",
        "en": "warning       {message}"},
    "logos.conforme": {
        "fr": "registre conforme, {n} logos",
        "en": "register valid, {n} logos"},
    "logos.comptes": {
        "fr": "{erreurs} erreurs, {avis} avertissements",
        "en": "{erreurs} errors, {avis} warnings"},
    "logos.avertissement": {
        "fr": "avertissement : {message}",
        "en": "warning: {message}"},

    # images.py. Le manifeste d'extraction et le catalogue ECRITS sur le
    # disque restent francais : ce sont des donnees relues plus tard, pas de
    # l'affichage. Seule leur restitution a l'ecran suit la langue demandee.
    "images.err_dossier": {
        "fr": "dossier introuvable : {dossier}",
        "en": "directory not found: {dossier}"},
    "images.pas_de_manifest": {
        "fr": "Pas de manifest.json dans ce dossier.",
        "en": "No manifest.json in this directory."},
    "images.cat.titre": {
        "fr": "Catalogue : {dossier}", "en": "Catalogue: {dossier}"},
    "images.cat.largeur": {
        "fr": "Largeur d'insertion prevue : {largeur:.1f} cm, usage {usage}, "
              "seuil {seuil} dpi",
        "en": "Planned insertion width: {largeur:.1f} cm, {usage} use, "
              "{seuil} dpi threshold"},
    "images.cat.comptes": {
        "fr": "{uniques} illustration(s) unique(s), {doublons} doublon(s), "
              "{faibles} sous le seuil",
        "en": "{uniques} unique illustration(s), {doublons} duplicate(s), "
              "{faibles} below the threshold"},
    "images.cat.col_n": {"fr": "n", "en": "n"},
    "images.cat.col_fichier": {"fr": "fichier", "en": "file"},
    "images.cat.col_format": {"fr": "format", "en": "format"},
    "images.cat.col_dimensions": {"fr": "dimensions", "en": "dimensions"},
    "images.cat.col_dpi": {"fr": "dpi", "en": "dpi"},
    "images.cat.col_verdict": {"fr": "verdict", "en": "verdict"},
    "images.cat.doublon_de": {
        "fr": " (doublon de {fichier})", "en": " (duplicate of {fichier})"},
    "images.cat.ignore": {
        "fr": "ignore : {fichier} ({raison})",
        "en": "skipped: {fichier} ({raison})"},
    "images.cat.note": {"fr": "note : {note}", "en": "note: {note}"},
    "images.n.sous_seuil": {
        "fr": "{n} illustration(s) sous {seuil} dpi a {largeur:.1f} cm : "
              "reduire la largeur d'insertion (colonne largeur_cm_max), "
              "retrouver le fichier d'origine, ou refaire la prise de vue ou "
              "la capture.",
        "en": "{n} illustration(s) below {seuil} dpi at {largeur:.1f} cm: "
              "reduce the insertion width (column largeur_cm_max), find the "
              "original file, or take the photograph or the screenshot "
              "again."},
    "images.n.vecteur": {
        "fr": "Illustrations vectorielles presentes : la voie Word passe par "
              "images.py convertir.",
        "en": "Vector illustrations present: the Word route goes through "
              "images.py convertir."},
    "images.n.illisible": {
        "fr": "Dimensions illisibles sur au moins un fichier : format non "
              "couvert par la lecture d'en-tete, mesurer autrement plutot "
              "que supposer.",
        "en": "Dimensions unreadable on at least one file: format not "
              "covered by the header reader, measure another way rather "
              "than assume."},
    "images.conv.ligne": {
        "fr": "{statut} : {backend}", "en": "{statut}: {backend}"},
    "images.conv.aucun_backend": {
        "fr": "aucun backend", "en": "no backend"},
    "images.conv.sans_extension": {
        "fr": "sans extension", "en": "no extension"},
    "images.conv.source_absente": {
        "fr": "Fichier source introuvable : {source}",
        "en": "Source file not found: {source}"},
    "images.conv.source_non_svg": {
        "fr": "Source attendue en .svg, recue en {ext}.",
        "en": "Source expected as .svg, received as {ext}."},
    "images.conv.aucun_backend_note": {
        "fr": "Aucun backend de conversion SVG present (essayes dans "
              "l'ordre : {backends}). Le fichier source n'est pas en cause.",
        "en": "No SVG conversion backend present (tried in order: "
              "{backends}). The source file is not at fault."},
    "images.conv.installation": {
        "fr": "Installer l'un de ces backends : librsvg (commande "
              "rsvg-convert, paquet librsvg2-bin sous Debian, librsvg sous "
              "Homebrew), Inkscape (inkscape.org), le module Python cairosvg "
              "(pip install cairosvg), ou ImageMagick (imagemagick.org, "
              "commande magick).",
        "en": "Install one of these backends: librsvg (command rsvg-convert, "
              "package librsvg2-bin on Debian, librsvg on Homebrew), "
              "Inkscape (inkscape.org), the Python module cairosvg (pip "
              "install cairosvg), or ImageMagick (imagemagick.org, command "
              "magick)."},
    "images.conv.repli": {
        "fr": "Sans backend, garder le SVG pour les voies HTML, LaTeX et "
              "PDF, qui l'affichent, et signaler la figure manquante dans la "
              "voie Word.",
        "en": "With no backend, keep the SVG for the HTML, LaTeX and PDF "
              "routes, which display it, and report the missing figure on "
              "the Word route."},
    "images.conv.backend_echec": {
        "fr": "Backend {backend} essaye sans succes.",
        "en": "Backend {backend} tried without success."},
    "images.conv.echec_tous": {
        "fr": "Tous les backends presents ont echoue : le SVG lui-meme est "
              "en cause (syntaxe, police absente, reference externe).",
        "en": "Every backend present failed: the SVG itself is at fault "
              "(syntax, missing font, external reference)."},

    # figures.py : le REGARD CRITIQUE de --audit seulement. Les etiquettes
    # dessinees dans le SVG suivent --langue et vivent dans la table LIBELLES
    # interne de figures.py : elles partent dans le livrable, celles-ci
    # restent au terminal. Les noms cites entre apostrophes (cles de donnees,
    # noms de series, motifs PRISMA) viennent des donnees fournies : ils sont
    # repris tels quels dans les deux langues, sans quoi le lecteur
    # chercherait dans son fichier un nom qui n'y figure pas.
    "figures.titre_audit": {
        "fr": "Regard critique sur la figure :",
        "en": "Critical read of the figure:"},
    "figures.ecrite": {
        "fr": "Figure ecrite : {chemin} ({octets} octets)",
        "en": "Figure written: {chemin} ({octets} bytes)"},
    "figures.rien_a_faire": {
        "fr": "Rien a faire : --out pour le SVG ou --audit pour la critique.",
        "en": "Nothing to do: --out for the SVG or --audit for the "
              "critique."},
    "figures.a.aucun_defaut": {
        "fr": "Aucun defaut structurel detecte. Verifier a l'oeil le titre, "
              "la source et l'honnetete des echelles.",
        "en": "No structural flaw found. Check by eye the title, the source "
              "and the honesty of the scales."},
    "figures.a.charte": {"fr": "Charte : {message}",
                         "en": "Charter: {message}"},
    "figures.a.case_vide": {
        "fr": "Case '{cle}' vide : une figure a case vide parait incomplete "
              "ou malhonnete.",
        "en": "Cell '{cle}' empty: a figure with an empty cell reads as "
              "incomplete or dishonest."},
    "figures.a.case_trop_pleine": {
        "fr": "Case '{cle}' : {n} elements, plus de 7 et la lisibilite chute "
              "(le rendu tronque).",
        "en": "Cell '{cle}': {n} items, past 7 legibility drops (the "
              "rendering truncates)."},
    "figures.a.case_element_long": {
        "fr": "Case '{cle}' : un element depasse 90 caracteres, le resumer.",
        "en": "Cell '{cle}': one item runs past 90 characters, shorten it."},
    "figures.a.desequilibre": {
        "fr": "Desequilibre fort entre les cases : une case ecrase les "
              "autres, reequilibrer ou justifier.",
        "en": "Strong imbalance between cells: one cell crushes the others, "
              "rebalance or justify."},
    "figures.a.bcg_vide": {
        "fr": "Matrice BCG sans aucun domaine d'activite place.",
        "en": "BCG matrix with no business unit placed."},
    "figures.a.bcg_sans_nom": {
        "fr": "Un point BCG n'a pas de nom : un point non etiquete n'est pas "
              "lisible.",
        "en": "One BCG point has no name: an unlabelled point cannot be "
              "read."},
    "figures.a.bcg_axe_manquant": {
        "fr": "Point '{nom}' : '{axe}' manquant, position arbitraire.",
        "en": "Point '{nom}': '{axe}' missing, arbitrary position."},
    "figures.a.bcg_axe_hors_bornes": {
        "fr": "Point '{nom}' : '{axe}'={valeur} hors de 0-100, echelle "
              "faussee.",
        "en": "Point '{nom}': '{axe}'={valeur} outside 0-100, scale "
              "distorted."},
    "figures.a.bcg_trop_de_bulles": {
        "fr": "Plus de 10 bulles : surcharge, regrouper les domaines "
              "mineurs.",
        "en": "More than 10 bubbles: overload, group the minor units."},
    "figures.a.tsm_bloc_absent": {
        "fr": "Bloc '{cle}' absent ou mal forme : attendu un objet avec "
              "'libelle' et 'valeur'.",
        "en": "Block '{cle}' missing or malformed: an object with 'libelle' "
              "and 'valeur' was expected."},
    "figures.a.tsm_libelle_vide": {
        "fr": "Bloc '{cle}' : libelle vide, un cercle sans libelle n'est pas "
              "lisible.",
        "en": "Block '{cle}': empty label, a circle with no label cannot be "
              "read."},
    "figures.a.tsm_valeur_vide": {
        "fr": "Bloc '{cle}' : valeur vide.",
        "en": "Block '{cle}': empty value."},
    "figures.a.tsm_ordre": {
        "fr": "Ordre attendu TAM >= SAM >= SOM non respecte (tam={tam:g}, "
              "sam={sam:g}, som={som:g}) : verifier les valeurs ou le sens "
              "des cercles.",
        "en": "Expected order TAM >= SAM >= SOM not held (tam={tam:g}, "
              "sam={sam:g}, som={som:g}): check the values or the direction "
              "of the circles."},
    "figures.a.tsm_non_numerique": {
        "fr": "Valeurs non toutes numeriques de facon univoque : ordre "
              "TAM >= SAM >= SOM non verifie automatiquement, a controler a "
              "l'oeil.",
        "en": "Values not all unambiguously numeric: the TAM >= SAM >= SOM "
              "order was not checked automatically, check it by eye."},
    "figures.a.axe_sans_titre": {
        "fr": "Axe des {axe} sans titre : nommer la grandeur portee.",
        "en": "The {axe} axis has no title: name the quantity it carries."},
    "figures.a.axe_sans_unite": {
        "fr": "Axe des {axe} sans unite : preciser l'unite de mesure (ou "
              "'sans unite' quand la grandeur n'en a pas).",
        "en": "The {axe} axis has no unit: state the unit of measurement (or "
              "'sans unite' when the quantity has none)."},
    "figures.a.aucune_serie": {
        "fr": "Aucune serie de donnees : la figure serait vide.",
        "en": "No data series: the figure would be empty."},
    "figures.a.serie_vide": {
        "fr": "Serie '{serie}' vide : aucun point exploitable, la retirer ou "
              "fournir ses donnees.",
        "en": "Series '{serie}' empty: no usable point, remove it or supply "
              "its data."},
    "figures.a.serie_sans_nom": {
        "fr": "Serie {i} sans nom : ses points ne sont pas etiquetes, la "
              "legende ne peut pas les designer.",
        "en": "Series {i} has no name: its points are unlabelled, the legend "
              "cannot name them."},
    "figures.a.erreurs_desappariees": {
        "fr": "Serie '{serie}' : {barres} barres d'erreur pour {points} "
              "points, correspondance rompue.",
        "en": "Series '{serie}': {barres} error bars for {points} points, "
              "the pairing is broken."},
    "figures.a.ajustement_court": {
        "fr": "Serie '{serie}' : droite d'ajustement sur moins de 3 points, "
              "ajustement sans portee.",
        "en": "Series '{serie}': fitted line on fewer than 3 points, a fit "
              "without reach."},
    "figures.a.trop_de_series": {
        "fr": "{n} series tracees : au-dela de {maxi} la figure devient "
              "illisible, en separer.",
        "en": "{n} series plotted: past {maxi} the figure becomes "
              "unreadable, split some out."},
    "figures.a.categorie_sans_libelle": {
        "fr": "{quoi} sans libelle : une barre ou une boite anonyme ne se "
              "lit pas.",
        "en": "{quoi} with no label: an anonymous bar or box cannot be "
              "read."},
    "figures.a.categorie_double": {
        "fr": "{quoi} '{libelle}' en double : deux entrees de meme nom se "
              "confondent a la lecture.",
        "en": "{quoi} '{libelle}' duplicated: two entries with the same name "
              "blur together when read."},
    "figures.a.aucune_barre": {
        "fr": "Aucune barre : l'histogramme serait vide.",
        "en": "No bar: the histogram would be empty."},
    "figures.a.barre_non_numerique": {
        "fr": "Barre '{categorie}' : valeur '{valeur}' non numerique.",
        "en": "Bar '{categorie}': value '{valeur}' is not numeric."},
    "figures.a.barre_sans_valeur": {
        "fr": "Barre '{categorie}' sans valeur.",
        "en": "Bar '{categorie}' has no value."},
    "figures.a.base_tronquee": {
        "fr": "Echelle des ordonnees tronquee (base = {base}) : une base non "
              "nulle exagere l'ecart entre barres, c'est une faute "
              "d'honnetete. Repartir de zero.",
        "en": "Truncated vertical scale (baseline = {base}): a non-zero "
              "baseline exaggerates the gap between bars, which is a "
              "dishonesty. Start again from zero."},
    "figures.a.trop_de_barres": {
        "fr": "{n} barres : au-dela de 20 les libelles se chevauchent, "
              "regrouper les classes.",
        "en": "{n} bars: past 20 the labels overlap, group the classes."},
    "figures.a.aucun_groupe": {
        "fr": "Aucun groupe : la figure a moustaches serait vide.",
        "en": "No group: the box plot would be empty."},
    "figures.a.groupe_valeurs_vides": {
        "fr": "Groupe '{nom}' : liste de valeurs vide.",
        "en": "Group '{nom}': empty list of values."},
    "figures.a.groupe_sans_stats": {
        "fr": "Groupe '{nom}' : ni valeurs brutes ni les cinq nombres (min, "
              "q1, mediane, q3, max).",
        "en": "Group '{nom}': neither raw values nor the five numbers (min, "
              "q1, median, q3, max)."},
    "figures.a.moustaches_incoherentes": {
        "fr": "Groupe '{nom}' : moustaches incoherentes, l'ordre min <= Q1 "
              "<= mediane <= Q3 <= max n'est pas respecte (min={mini}, "
              "q1={q1}, mediane={mediane}, q3={q3}, max={maxi}).",
        "en": "Group '{nom}': inconsistent whiskers, the order min <= Q1 <= "
              "median <= Q3 <= max is not held (min={mini}, q1={q1}, "
              "median={mediane}, q3={q3}, max={maxi})."},
    "figures.a.groupe_peu_de_points": {
        "fr": "Groupe '{nom}' : {n} valeurs, une boite a moustaches sur si "
              "peu de points egare plus qu'elle n'informe.",
        "en": "Group '{nom}': {n} values, a box plot on so few points "
              "misleads more than it informs."},
    "figures.a.trop_de_groupes": {
        "fr": "{n} groupes : au-dela de 12 les boites deviennent trop "
              "etroites.",
        "en": "{n} groups: past 12 the boxes become too narrow."},
    "figures.a.aucun_niveau": {
        "fr": "Aucun niveau : le diagramme de flux serait vide.",
        "en": "No level: the flow diagram would be empty."},
    "figures.a.niveau_sans_titre": {
        "fr": "Niveau {i} sans titre d'etape.",
        "en": "Level {i} has no stage title."},
    "figures.a.niveau_sans_boite": {
        "fr": "Niveau {i} sans aucune boite.",
        "en": "Level {i} has no box at all."},
    "figures.a.boite_sans_libelle": {
        "fr": "Niveau {i} : une boite sans libelle.",
        "en": "Level {i}: a box with no label."},
    "figures.a.boite_sans_effectif": {
        "fr": "Boite '{libelle}' sans effectif : un flux sans compte ne se "
              "verifie pas.",
        "en": "Box '{libelle}' has no count: a flow without counts cannot be "
              "checked."},
    "figures.a.exclusion_sans_effectif": {
        "fr": "Exclusion de '{libelle}' sans effectif.",
        "en": "Exclusion from '{libelle}' has no count."},
    "figures.a.compte_absent": {
        "fr": "Compte '{compte}' absent ou non numerique : le schema PRISMA "
              "ne se boucle pas sans lui.",
        "en": "Count '{compte}' missing or non-numeric: the PRISMA diagram "
              "does not balance without it."},
    "figures.a.aucun_motif": {
        "fr": "Aucun motif d'ecart a l'etape {etape} : chaque exclusion "
              "porte son motif (PRISMA).",
        "en": "No exclusion reason at the {etape} stage: every exclusion "
              "carries its reason (PRISMA)."},
    "figures.a.ecart_sans_motif": {
        "fr": "Ecart a l'etape {etape} sans motif nomme.",
        "en": "Exclusion at the {etape} stage with no reason named."},
    "figures.a.ecart_sans_effectif": {
        "fr": "Ecart '{motif}' ({etape}) sans effectif.",
        "en": "Exclusion '{motif}' ({etape}) has no count."},
    "figures.a.identification_non_bouclee": {
        "fr": "Comptes non boucles a l'identification : identifiees "
              "({identifiees}) moins doublons ({doublons}) fait {attendu}, "
              "or examinees vaut {examinees}.",
        "en": "Counts do not balance at identification: identified "
              "({identifiees}) minus duplicates ({doublons}) makes "
              "{attendu}, yet screened is {examinees}."},
    "figures.a.criblage_non_boucle": {
        "fr": "Comptes non boucles au criblage : la somme des motifs d'ecart "
              "({somme}) ne fait pas la difference entre examinees "
              "({examinees}) et evaluees ({evaluees}), soit {ecart}.",
        "en": "Counts do not balance at screening: the sum of exclusion "
              "reasons ({somme}) does not match the difference between "
              "screened ({examinees}) and assessed ({evaluees}), that is "
              "{ecart}."},
    "figures.a.texte_non_boucle": {
        "fr": "Comptes non boucles en texte integral : la somme des motifs "
              "d'ecart ({somme}) ne fait pas la difference entre evaluees "
              "({evaluees}) et incluses ({incluses}), soit {ecart}.",
        "en": "Counts do not balance at full text: the sum of exclusion "
              "reasons ({somme}) does not match the difference between "
              "assessed ({evaluees}) and included ({incluses}), that is "
              "{ecart}."},
    "figures.a.aucune_incluse": {
        "fr": "Aucune etude incluse : verifier les criteres avant de publier "
              "un schema qui ne retient rien.",
        "en": "No study included: check the criteria before publishing a "
              "diagram that keeps nothing."},
    "figures.a.flux_grossit": {
        "fr": "Etape {etape} : le compte sortant ({sortant}) depasse le "
              "compte entrant ({entrant}), un flux ne grossit pas.",
        "en": "Stage {etape}: the outgoing count ({sortant}) exceeds the "
              "incoming count ({entrant}), a flow does not grow."},

    # project.py. Ce que le journal de mission ENREGISTRE dans projet.json
    # (etats, libelles poses par l'utilisateur, declaration de stochasticite)
    # est de la DONNEE : un projet relu dans l'autre langue doit dire la meme
    # chose. Seuls le tableau de bord, la passation et les messages de la
    # ligne de commande passent par ces cles.
    "project.tableau": {
        "fr": "=== Tableau de bord : {titre} ===",
        "en": "=== Dashboard: {titre} ==="},
    "project.sans_titre": {"fr": "(sans titre)", "en": "(untitled)"},
    "project.genre": {"fr": "Genre : {genre}", "en": "Genre: {genre}"},
    "project.etapes": {"fr": "Etapes :", "en": "Stages:"},
    "project.aucune_etape": {
        "fr": "(aucune etape suivie)", "en": "(no stage tracked)"},
    "project.etape_ligne": {
        "fr": "{sym} {nom:<20} {etat}{motif}",
        "en": "{sym} {nom:<20} {etat}{motif}"},
    "project.etape_motif": {
        "fr": " (motif : {motif})", "en": " (reason: {motif})"},
    "project.artefacts": {"fr": "Artefacts :", "en": "Artefacts:"},
    "project.aucun_artefact": {
        "fr": "(aucun artefact enregistre)", "en": "(no artefact recorded)"},
    "project.artefact_ligne": {
        "fr": "{nom:<20} {version}", "en": "{nom:<20} {version}"},
    "project.objets": {
        "fr": "Objets numerotes :", "en": "Numbered objects:"},
    "project.aucun": {"fr": "(aucun)", "en": "(none)"},
    "project.objet_ligne": {
        "fr": "{objet} {numero:<3} {libelle}",
        "en": "{objet} {numero:<3} {libelle}"},
    "project.repro": {
        "fr": "Reproductibilite :", "en": "Reproducibility:"},
    "project.aucune_repro": {
        "fr": "(aucune configuration de generation enregistree)",
        "en": "(no generation configuration recorded)"},
    "project.repro_ligne": {
        "fr": "plugin {version:<10} modele {modele:<15} {horodatage} "
              "(rejeu non garanti)",
        "en": "plugin {version:<10} model {modele:<15} {horodatage} "
              "(replay not guaranteed)"},
    "project.decisions_attente": {
        "fr": "Decisions en attente :", "en": "Pending decisions:"},
    "project.decision_ligne": {
        "fr": "[{hash}] {decision}", "en": "[{hash}] {decision}"},
    "project.frontieres": {"fr": "Frontieres :", "en": "Checkpoints:"},
    "project.frontiere_ligne": {
        "fr": "[{hash}] {libelle} ({horodatage}) - {statut}",
        "en": "[{hash}] {libelle} ({horodatage}) - {statut}"},
    "project.outrepassements": {
        "fr": "Outrepassements : {n}{suffixe}",
        "en": "Overrides: {n}{suffixe}"},
    "project.cran_courant": {
        "fr": " (cran courant : {cran})", "en": " (current step: {cran})"},

    "project.pass.titre": {
        "fr": "=== Passation vers le redacteur ===",
        "en": "=== Handover to the writer ==="},
    "project.pass.problematique": {
        "fr": "Problematique : {problematique}",
        "en": "Research question: {problematique}"},
    "project.pass.glossaire": {
        "fr": "Glossaire (termes fixes, a employer tels quels, sans "
              "synonyme) :",
        "en": "Glossary (fixed terms, to be used as they stand, with no "
              "synonym):"},
    "project.pass.aucun_terme": {
        "fr": "(aucun terme fixe)", "en": "(no fixed term)"},
    "project.pass.terme": {
        "fr": "{terme} : {definition}", "en": "{terme}: {definition}"},
    "project.pass.objets": {
        "fr": "Objets deja numerotes (ne pas renumeroter, ne pas "
              "reutiliser) :",
        "en": "Objects already numbered (do not renumber, do not reuse):"},
    "project.pass.aucun_objet": {
        "fr": "(aucun objet numerote)", "en": "(no numbered object)"},
    "project.pass.objet": {
        "fr": "{objet} {numero} : {libelle}",
        "en": "{objet} {numero}: {libelle}"},
    "project.pass.prochain": {
        "fr": "Prochain numero libre : {liste}",
        "en": "Next free number: {liste}"},

    "project.e.etat_inconnu": {
        "fr": "etat inconnu : '{etat}' (valides : {valides}).",
        "en": "unknown state: '{etat}' (valid: {valides})."},
    "project.e.motif_requis": {
        "fr": "La transition vers 'saute' exige un motif (--motif TEXTE).",
        "en": "Moving to 'saute' requires a reason (--motif TEXT)."},
    "project.e.transition": {
        "fr": "Transition illegale : '{nom}' est '{ancien}', passage a "
              "'{nouveau}' refuse (autorise depuis '{ancien}' : {legales}).",
        "en": "Illegal transition: '{nom}' is '{ancien}', moving to "
              "'{nouveau}' refused (allowed from '{ancien}': {legales})."},
    "project.e.type_objet": {
        "fr": "type d'objet inconnu : '{objet}' (valides : {valides}).",
        "en": "unknown object type: '{objet}' (valid: {valides})."},
    "project.e.numero_non_entier": {
        "fr": "numero non entier : {numero}.",
        "en": "number is not an integer: {numero}."},
    "project.e.numero_borne": {
        "fr": "numero hors bornes : {numero} (le premier rang est 1).",
        "en": "number out of range: {numero} (the first rank is 1)."},
    "project.e.libelle_vide": {
        "fr": "un objet numerote porte un libelle non vide.",
        "en": "a numbered object carries a non-empty label."},
    "project.e.numero_pris": {
        "fr": "{objet} {numero} est deja pris par '{libelle}' : choisir un "
              "autre numero plutot que reaffecter celui-ci.",
        "en": "{objet} {numero} is already taken by '{libelle}': pick "
              "another number rather than reassign this one."},
    "project.e.frontiere_absente": {
        "fr": "Aucune frontiere avec le hash '{hash}'.",
        "en": "No checkpoint with hash '{hash}'."},
    "project.e.double_reprise": {
        "fr": "Cette frontiere a deja ete reprise le {horodatage} (double "
              "reprise refusee).",
        "en": "This checkpoint was already resumed on {horodatage} (a second "
              "resume is refused)."},
    "project.e.cran2": {
        "fr": "cran 2 : --justification \"texte\" est requise.",
        "en": "step 2: --justification \"text\" is required."},
    "project.e.cran3": {
        "fr": "cran {cran} : justification d'au moins 100 caracteres "
              "requise ({n} fournis).",
        "en": "step {cran}: a justification of at least 100 characters is "
              "required ({n} given)."},

    "project.existe": {
        "fr": "{fichier} existe deja, inchange.",
        "en": "{fichier} already exists, left unchanged."},
    "project.creee": {
        "fr": "Memoire de projet creee : {fichier}",
        "en": "Project memory created: {fichier}"},
    "project.journal_refuse": {
        "fr": "Refuse : 'journal' est append-only. Utiliser "
              "etape/artefact/frontiere/reprendre/decision/outrepasser.",
        "en": "Refused: 'journal' is append-only. Use "
              "etape/artefact/frontiere/reprendre/decision/outrepasser."},
    "project.maj": {
        "fr": "{cle} mis a jour dans {fichier}.",
        "en": "{cle} updated in {fichier}."},
    "project.erreur": {
        "fr": "Erreur : {erreur}", "en": "Error: {erreur}"},
    "project.etape_changee": {
        "fr": "Etape '{nom}' : {ancien} -> {nouveau}.",
        "en": "Stage '{nom}': {ancien} -> {nouveau}."},
    "project.artefact_enregistre": {
        "fr": "Artefact '{nom}' enregistre : {version}.",
        "en": "Artefact '{nom}' recorded: {version}."},
    "project.frontiere_posee": {
        "fr": "Frontiere posee : {hash} - {libelle}",
        "en": "Checkpoint set: {hash} - {libelle}"},
    "project.decision_rattachee": {
        "fr": "Decision en attente rattachee : {decision}",
        "en": "Pending decision attached: {decision}"},
    "project.reprise": {
        "fr": "Reprise de la frontiere '{libelle}' ({horodatage}).",
        "en": "Resumed from checkpoint '{libelle}' ({horodatage})."},
    "project.reprise_etapes": {
        "fr": "Etapes : {etapes}", "en": "Stages: {etapes}"},
    "project.reprise_artefacts": {
        "fr": "Artefacts : {artefacts}", "en": "Artefacts: {artefacts}"},
    "project.reprise_decision": {
        "fr": "Decision en attente, a reposer a l'utilisateur : {decision}",
        "en": "Pending decision, to be put back to the user: {decision}"},
    "project.aucune_decision": {
        "fr": "Aucune decision en attente.", "en": "No pending decision."},
    "project.decision_journalisee": {
        "fr": "Decision journalisee : {libelle}",
        "en": "Decision logged: {libelle}"},
    "project.objet_pose": {
        "fr": "{objet} {numero} : {libelle}",
        "en": "{objet} {numero}: {libelle}"},
    "project.outrepassement": {
        "fr": "Outrepassement journalise (cran {cran}) : {libelle}",
        "en": "Override logged (step {cran}): {libelle}"},
    "project.repro_enregistree": {
        "fr": "Reproductibilite enregistree : plugin {version}, modele "
              "{modele}, {horodatage}.",
        "en": "Reproducibility recorded: plugin {version}, model {modele}, "
              "{horodatage}."},
    "project.rappel": {
        "fr": "Rappel : {declaration}", "en": "Reminder: {declaration}"},
    # Le francais de cette cle est la chaine EXACTE de
    # project.STOCHASTICITE_DECLAREE, celle qui est recopiee dans chaque
    # entree de journal. Un cas d'eval verifie qu'elles ne divergent pas.
    "project.stochasticite": {
        "fr": "Cette entree documente la configuration de generation au "
              "moment ou elle a ete enregistree (version du plugin, modele "
              "nomme, date). Elle ne garantit pas qu'un rejeu ulterieur, "
              "meme avec la meme version et le meme modele nomme, produise "
              "un texte identique : un modele de langage reste stochastique "
              "par nature, sauf configuration deterministe explicite non "
              "couverte ici.",
        "en": "This entry documents the generation configuration at the "
              "moment it was recorded (plugin version, named model, date). "
              "It does not guarantee that a later replay, even with the same "
              "version and the same named model, produces an identical text: "
              "a language model remains stochastic by nature, barring an "
              "explicit deterministic configuration not covered here."},

    # gabarit.py. L'INVENTAIRE est ecrit sur le disque et relu par la
    # comparaison : ses lacunes, son motif de non-remplissage et les libelles
    # de ses espaces reserves restent francais dans les donnees et se
    # traduisent au rendu (tables VALEURS gab.lacune, gab.motif,
    # gab.espace). La COMPARAISON et le rapport de remplissage ne sont
    # jamais ecrits : leurs details, parametres compris, se composent
    # directement dans la langue demandee.
    "gab.inv.titre": {
        "fr": "Gabarit : {source} ({format}, famille {famille})",
        "en": "Template: {source} ({format}, {famille} family)"},
    "gab.inv.dispositions": {
        "fr": "Dispositions declarees : {n}",
        "en": "Declared layouts: {n}"},
    "gab.inv.disposition_ligne": {
        "fr": "{nom:<28} {zones}", "en": "{nom:<28} {zones}"},
    "gab.inv.aucune_zone": {"fr": "aucune zone", "en": "no area"},
    "gab.inv.diapositives": {
        "fr": "Diapositives : {n}", "en": "Slides: {n}"},
    "gab.inv.dispositions_employees": {
        "fr": "Dispositions employees : {noms}",
        "en": "Layouts used: {noms}"},
    "gab.inv.diapositive_taille": {
        "fr": "Diapositive : {largeur} x {hauteur} cm, {orientation}, ratio "
              "{ratio}",
        "en": "Slide: {largeur} x {hauteur} cm, {orientation}, ratio "
              "{ratio}"},
    "gab.inv.version_pdf": {
        "fr": "Version PDF : {version}", "en": "PDF version: {version}"},
    "gab.inv.pages": {"fr": "Pages : {pages}", "en": "Pages: {pages}"},
    "gab.inv.illisible": {"fr": "illisible", "en": "unreadable"},
    "gab.inv.page_pdf": {
        "fr": "Page : {largeur} x {hauteur} cm, {orientation}{format_nomme}",
        "en": "Page: {largeur} x {hauteur} cm, "
              "{orientation}{format_nomme}"},
    "gab.inv.format_nomme": {
        "fr": ", format {nom}", "en": ", {nom} format"},
    "gab.inv.format_page_ligne": {
        "fr": "{largeur} x {hauteur} cm sur {pages} page(s)",
        "en": "{largeur} x {hauteur} cm on {pages} page(s)"},
    "gab.inv.polices_incorporees": {
        "fr": "Polices incorporees : {n} sur {total} nommees",
        "en": "Embedded fonts: {n} of {total} named"},
    "gab.inv.chiffrement": {
        "fr": "Chiffrement : present, contenu non inspecte",
        "en": "Encryption: present, contents not inspected"},
    "gab.inv.styles": {
        "fr": "Styles declares : {n}", "en": "Declared styles: {n}"},
    "gab.inv.titres": {"fr": "Titres : {paires}",
                       "en": "Headings: {paires}"},
    "gab.inv.aucun_titre": {
        "fr": "Titres : aucun style de titre reconnu",
        "en": "Headings: no heading style recognised"},
    "gab.inv.corps": {"fr": "Corps : {style}", "en": "Body: {style}"},
    "gab.inv.non_identifie": {
        "fr": "non identifie", "en": "not identified"},
    "gab.inv.page": {
        "fr": "Page : {largeur} x {hauteur} cm, {orientation}, marges "
              "h{top} b{bottom} g{left} d{right}",
        "en": "Page: {largeur} x {hauteur} cm, {orientation}, margins "
              "t{top} b{bottom} l{left} r{right}"},
    "gab.inv.entete_pied": {
        "fr": "{role} : {texte}{champs}", "en": "{role}: {texte}{champs}"},
    "gab.inv.vide": {"fr": "(vide)", "en": "(empty)"},
    "gab.inv.champs": {"fr": ", champs {champs}",
                       "en": ", fields {champs}"},
    "gab.inv.polices": {
        "fr": "Polices nommees : {noms}", "en": "Named fonts: {noms}"},
    "gab.inv.protection": {
        "fr": "Protection : {edition}{applique}",
        "en": "Protection: {edition}{applique}"},
    "gab.inv.appliquee": {"fr": " (appliquee)", "en": " (enforced)"},
    "gab.inv.remplissage_impossible": {
        "fr": "Remplissage : impossible, {motif}",
        "en": "Filling: impossible, {motif}"},
    "gab.inv.format_non_ecrit": {
        "fr": "format non ecrit", "en": "format not written"},
    "gab.inv.lacunes": {
        "fr": "Ce que cet inventaire ne couvre pas :",
        "en": "What this inventory does not cover:"},
    "gab.inv.ecrit": {
        "fr": "Inventaire ecrit dans {chemin}",
        "en": "Inventory written to {chemin}"},

    "gab.cmp.titre": {
        "fr": "{document} contre {gabarit}",
        "en": "{document} against {gabarit}"},
    "gab.cmp.ecart": {
        "fr": "[{gravite}] {regle} : {detail}",
        "en": "[{gravite}] {regle}: {detail}"},
    "gab.cmp.aucun_ecart": {
        "fr": "aucun ecart de forme releve",
        "en": "no deviation of form found"},
    "gab.cmp.verdict": {
        "fr": "Verdict : {verdict} ({majeurs} majeurs, {mineurs} mineurs)",
        "en": "Verdict: {verdict} ({majeurs} major, {mineurs} minor)"},
    "gab.cmp.non_verifie": {
        "fr": "Non verifie ici :", "en": "Not checked here:"},

    "gab.d.mise_en_page_absente": {
        "fr": "la mesure {mesure} du gabarit ({valeur} cm) n'est pas "
              "declaree dans le document",
        "en": "the template's {mesure} measurement ({valeur} cm) is not "
              "declared in the document"},
    "gab.d.mise_en_page_divergente": {
        "fr": "{mesure} : gabarit {attendu} cm, document {obtenu} cm",
        "en": "{mesure}: template {attendu} cm, document {obtenu} cm"},
    "gab.d.orientation": {
        "fr": "gabarit {attendu}, document {obtenu}",
        "en": "template {attendu}, document {obtenu}"},
    "gab.d.disposition_non_identifiable": {
        "fr": "{partie} ne se reclame d'aucune disposition lisible",
        "en": "{partie} claims no readable layout"},
    "gab.d.disposition_hors_gabarit": {
        "fr": "{partie} emploie la disposition {disposition}, absente du "
              "gabarit",
        "en": "{partie} uses the {disposition} layout, absent from the "
              "template"},
    "gab.d.disposition_jamais_employee": {
        "fr": "le gabarit propose la disposition {disposition}, aucune "
              "diapositive ne l'emploie",
        "en": "the template offers the {disposition} layout, no slide uses "
              "it"},
    "gab.d.presentation_vide": {
        "fr": "le document ne porte aucune diapositive",
        "en": "the document carries no slide"},
    "gab.d.espace_non_repris": {
        "fr": "{partie} laisse vides les zones {zones} prevues par "
              "{disposition}",
        "en": "{partie} leaves empty the {zones} areas planned by "
              "{disposition}"},
    "gab.d.format_page": {
        "fr": "gabarit {attendu}, document {obtenu}",
        "en": "template {attendu}, document {obtenu}"},
    "gab.d.formats_melanges": {
        "fr": "le document mele {n} formats de page differents",
        "en": "the document mixes {n} different page formats"},
    "gab.d.limite_pages": {
        "fr": "{pages} pages pour une limite de {limite}",
        "en": "{pages} pages for a limit of {limite}"},
    "gab.d.chiffre": {
        "fr": "le PDF est chiffre : son contenu n'a pas ete inspecte",
        "en": "the PDF is encrypted: its contents were not inspected"},
    "gab.d.police_non_incorporee": {
        "fr": "aucun nom de police ne porte de prefixe de sous-ensemble : le "
              "rendu depend des polices installees chez le lecteur",
        "en": "no font name carries a subset prefix: the rendering depends "
              "on the fonts installed on the reader's machine"},
    "gab.d.pagination_illisible": {
        "fr": "le compte de pages n'a pas pu se lire en binaire, "
              "probablement un flux d'objets compresse",
        "en": "the page count could not be read from the binary, most "
              "likely a compressed object stream"},
    "gab.d.style_hors_gabarit": {
        "fr": "le style {style} est applique {n} fois et n'existe pas dans "
              "le gabarit",
        "en": "style {style} is applied {n} times and does not exist in the "
              "template"},
    "gab.d.style_jamais_employe": {
        "fr": "le style {style} est prevu par le gabarit et n'apparait pas",
        "en": "style {style} is planned by the template and does not "
              "appear"},
    "gab.d.entete_pied_manquant": {
        "fr": "le gabarit declare un {role}, le document n'en a pas",
        "en": "the template declares a {role}, the document has none"},

    "gab.nv.contenu": {
        "fr": "le contenu redactionnel n'est pas juge ici, seule la forme "
              "l'est",
        "en": "the written content is not judged here, only the form is"},
    "gab.nv.hors_fichier": {
        "fr": "un element de forme decrit hors du fichier gabarit echappe a "
              "cette comparaison",
        "en": "a requirement of form stated outside the template file "
              "escapes this comparison"},
    "gab.nv.espaces": {
        "fr": "la position et la taille des espaces reserves ne sont pas "
              "mesurees",
        "en": "the position and size of placeholders are not measured"},
    "gab.nv.masque": {
        "fr": "le masque de diapositive et le theme ne sont pas compares",
        "en": "the slide master and the theme are not compared"},
    "gab.nv.marges_pdf": {
        "fr": "les marges d'un PDF ne sont pas une donnee du fichier et ne "
              "se comparent pas",
        "en": "the margins of a PDF are not data held in the file and are "
              "not compared"},
    "gab.nv.styles_pdf": {
        "fr": "le respect des styles de titre ne survit pas a l'export PDF",
        "en": "adherence to heading styles does not survive the PDF export"},
    "gab.nv.lecture_pdf": {
        "fr": "l'integrite de lecture du texte se controle avec "
              "check-lecture-pdf.py",
        "en": "the text extraction integrity is checked with "
              "check-lecture-pdf.py"},
    "gab.nv.styles_automatiques": {
        "fr": "les styles automatiques nes d'une mise en forme directe sont "
              "ignores",
        "en": "automatic styles born of direct formatting are ignored"},

    "gab.rem.diapositives": {
        "fr": "{n} diapositives ajoutees dans {sortie}, disposition "
              "{disposition}",
        "en": "{n} slides added to {sortie}, layout {disposition}"},
    "gab.rem.paragraphes": {
        "fr": "{n} paragraphes injectes dans {sortie}",
        "en": "{n} paragraphs injected into {sortie}"},
    "gab.rem.logo": {
        "fr": "Logo : {fichier}, {largeur} cm de large",
        "en": "Logo: {fichier}, {largeur} cm wide"},
    "gab.rem.avertissement": {
        "fr": "avertissement : {message}", "en": "warning: {message}"},
    "gab.a.niveau_titre": {
        "fr": "niveau de titre {niveau} absent du gabarit, rendu en style de "
              "corps",
        "en": "heading level {niveau} absent from the template, rendered in "
              "the body style"},
    "gab.a.disposition_defaut": {
        "fr": "aucune disposition ne porte a la fois un titre et un corps, "
              "la premiere declaree ({disposition}) est employee",
        "en": "no layout carries both a title and a body, the first one "
              "declared ({disposition}) is used"},
    "gab.a.logo_diapositive": {
        "fr": "le placement d'un logo en diapositive suit le masque du "
              "gabarit : le poser par diapositive le dupliquerait",
        "en": "placing a logo on a slide follows the template master: "
              "setting it slide by slide would duplicate it"},

    "gab.fmt.titre": {
        "fr": "Formats reconnus par gabarit.py",
        "en": "Formats recognised by gabarit.py"},
    "gab.fmt.actions": {
        "fr": "inventorier, comparer", "en": "inventorier, comparer"},
    "gab.fmt.actions_remplir": {
        "fr": "inventorier, comparer, remplir",
        "en": "inventorier, comparer, remplir"},

    "gab.e.introuvable": {
        "fr": "fichier introuvable : {chemin}",
        "en": "file not found: {chemin}"},
    "gab.e.non_reconnu": {
        "fr": "{fichier} n'est ni un PDF ni une archive : format non reconnu",
        "en": "{fichier} is neither a PDF nor an archive: format not "
              "recognised"},
    "gab.e.archive_inconnue": {
        "fr": "{fichier} est une archive, mais d'aucun format de document "
              "reconnu",
        "en": "{fichier} is an archive, but of no recognised document "
              "format"},
    "gab.e.piece_manquante": {
        "fr": "{fichier} ne porte pas {piece} : format inattendu",
        "en": "{fichier} does not carry {piece}: unexpected format"},
    "gab.e.archive_illisible": {
        "fr": "{fichier} n'est pas une archive lisible",
        "en": "{fichier} is not a readable archive"},
    "gab.e.familles": {
        "fr": "le gabarit est de famille {attendue} et le document de "
              "famille {obtenue} : comparaison sans objet",
        "en": "the template is of the {attendue} family and the document of "
              "the {obtenue} family: the comparison has no object"},
    "gab.e.image_introuvable": {
        "fr": "image introuvable : {chemin}",
        "en": "image not found: {chemin}"},
    "gab.e.source_introuvable": {
        "fr": "gabarit source introuvable ({chemin}) : passer --source",
        "en": "source template not found ({chemin}): pass --source"},
    "gab.e.non_remplissable": {
        "fr": "remplissage impossible pour un gabarit {famille} : {motif}",
        "en": "filling impossible for a {famille} template: {motif}"},
    "gab.e.protege": {
        "fr": "gabarit protege en edition ({edition}) : le remplissage "
              "s'arrete plutot que de produire un fichier douteux",
        "en": "template protected against editing ({edition}): filling "
              "stops rather than produce a doubtful file"},
    "gab.e.restriction": {
        "fr": "restriction declaree", "en": "declared restriction"},
    "gab.e.corps_illisible": {
        "fr": "corps du document illisible, remplissage annule",
        "en": "document body unreadable, filling cancelled"},
    "gab.e.aucune_disposition": {
        "fr": "le gabarit ne declare aucune disposition",
        "en": "the template declares no layout"},
    "gab.e.disposition_absente": {
        "fr": "disposition {disposition} absente du gabarit. Disponibles : "
              "{noms}",
        "en": "layout {disposition} absent from the template. Available: "
              "{noms}"},
    "gab.e.aucune_diapositive": {
        "fr": "le contenu ne produit aucune diapositive",
        "en": "the content produces no slide"},
    "gab.e.presentation_illisible": {
        "fr": "presentation.xml illisible, remplissage annule",
        "en": "presentation.xml unreadable, filling cancelled"},

})


VALEURS.update({
    # gabarit.py : tout ce qui est porte par l'inventaire ecrit sur le disque
    # ou par la sortie JSON reste la chaine francaise, ici comme la-bas.
    "gab.gravite": {
        "majeur": {"fr": "majeur", "en": "major"},
        "mineur": {"fr": "mineur", "en": "minor"},
        "info": {"fr": "info", "en": "info"},
    },
    "gab.verdict": {
        "conforme": {"fr": "conforme", "en": "compliant"},
        "ecarts mineurs": {"fr": "ecarts mineurs",
                           "en": "minor deviations"},
        "ecarts majeurs": {"fr": "ecarts majeurs",
                           "en": "major deviations"},
    },
    "gab.famille": {
        "texte-ooxml": {"fr": "texte-ooxml", "en": "ooxml-text"},
        "diapositives-ooxml": {"fr": "diapositives-ooxml",
                               "en": "ooxml-slides"},
        "texte-odf": {"fr": "texte-odf", "en": "odf-text"},
        "diapositives-odf": {"fr": "diapositives-odf", "en": "odf-slides"},
        "page-fixe": {"fr": "page-fixe", "en": "fixed-page"},
    },
    "gab.orientation": {
        "portrait": {"fr": "portrait", "en": "portrait"},
        "paysage": {"fr": "paysage", "en": "landscape"},
    },
    "gab.role": {
        "en-tete": {"fr": "en-tete", "en": "header"},
        "pied": {"fr": "pied", "en": "footer"},
    },
    "gab.regle": {
        "mise en page absente": {"fr": "mise en page absente",
                                 "en": "page setup missing"},
        "mise en page divergente": {"fr": "mise en page divergente",
                                    "en": "page setup diverging"},
        "orientation divergente": {"fr": "orientation divergente",
                                   "en": "orientation diverging"},
        "disposition non identifiable": {
            "fr": "disposition non identifiable",
            "en": "layout not identifiable"},
        "disposition hors gabarit": {"fr": "disposition hors gabarit",
                                     "en": "layout outside the template"},
        "disposition jamais employee": {"fr": "disposition jamais employee",
                                        "en": "layout never used"},
        "presentation vide": {"fr": "presentation vide",
                              "en": "empty presentation"},
        "espace reserve non repris": {"fr": "espace reserve non repris",
                                      "en": "placeholder not taken up"},
        "format de page divergent": {"fr": "format de page divergent",
                                     "en": "page format diverging"},
        "formats de page melanges": {"fr": "formats de page melanges",
                                     "en": "page formats mixed"},
        "limite de pages depassee": {"fr": "limite de pages depassee",
                                     "en": "page limit exceeded"},
        "document chiffre": {"fr": "document chiffre",
                             "en": "encrypted document"},
        "aucune police incorporee": {"fr": "aucune police incorporee",
                                     "en": "no embedded font"},
        "pagination illisible": {"fr": "pagination illisible",
                                 "en": "pagination unreadable"},
        "style hors gabarit": {"fr": "style hors gabarit",
                               "en": "style outside the template"},
        "style du gabarit jamais employe": {
            "fr": "style du gabarit jamais employe",
            "en": "template style never used"},
        "en-tete ou pied manquant": {"fr": "en-tete ou pied manquant",
                                     "en": "header or footer missing"},
    },
    # Libelles d'espace reserve, portes par l'inventaire (cle libelle).
    "gab.espace": {
        "titre": {"fr": "titre", "en": "title"},
        "titre centre": {"fr": "titre centre", "en": "centred title"},
        "sous-titre": {"fr": "sous-titre", "en": "subtitle"},
        "corps": {"fr": "corps", "en": "body"},
        "objet": {"fr": "objet", "en": "object"},
        "tableau": {"fr": "tableau", "en": "table"},
        "graphique": {"fr": "graphique", "en": "chart"},
        "image": {"fr": "image", "en": "picture"},
        "media": {"fr": "media", "en": "media"},
        "date": {"fr": "date", "en": "date"},
        "pied": {"fr": "pied", "en": "footer"},
        "en-tete": {"fr": "en-tete", "en": "header"},
        "numero de diapositive": {"fr": "numero de diapositive",
                                  "en": "slide number"},
    },
    # Motifs de non-remplissage, portes par l'inventaire ecrit.
    "gab.motif": {
        "le remplissage ODF n'est pas implemente ; l'inventaire et la "
        "comparaison le sont": {
            "fr": "le remplissage ODF n'est pas implemente ; l'inventaire et "
                  "la comparaison le sont",
            "en": "ODF filling is not implemented; the inventory and the "
                  "comparison are"},
        "un PDF est une page deja composee : il se compare, il ne se remplit "
        "pas. Remplir le gabarit d'origine puis exporter": {
            "fr": "un PDF est une page deja composee : il se compare, il ne "
                  "se remplit pas. Remplir le gabarit d'origine puis "
                  "exporter",
            "en": "a PDF is an already typeset page: it can be compared, not "
                  "filled. Fill the original template, then export"},
    },
    # Lacunes de l'inventaire, portees par l'inventaire ecrit.
    "gab.lacune": {
        "aucune mise en page lisible dans le fichier": {
            "fr": "aucune mise en page lisible dans le fichier",
            "en": "no readable page setup in the file"},
        "aucun style de titre reconnu, la hierarchie est a declarer a la "
        "main": {
            "fr": "aucun style de titre reconnu, la hierarchie est a "
                  "declarer a la main",
            "en": "no heading style recognised, the hierarchy has to be "
                  "declared by hand"},
        "aucun en-tete ni pied declare dans le gabarit": {
            "fr": "aucun en-tete ni pied declare dans le gabarit",
            "en": "no header or footer declared in the template"},
        "aucune disposition lisible, le gabarit ne propose pas de mise en "
        "page nommee": {
            "fr": "aucune disposition lisible, le gabarit ne propose pas de "
                  "mise en page nommee",
            "en": "no readable layout, the template offers no named page "
                  "layout"},
        "la position et la taille exactes de chaque espace reserve ne sont "
        "pas comparees, seule leur presence l'est": {
            "fr": "la position et la taille exactes de chaque espace reserve "
                  "ne sont pas comparees, seule leur presence l'est",
            "en": "the exact position and size of each placeholder are not "
                  "compared, only their presence is"},
        "les styles automatiques nes d'une mise en forme directe sont "
        "ignores, seuls les styles nommes du document comptent comme regle": {
            "fr": "les styles automatiques nes d'une mise en forme directe "
                  "sont ignores, seuls les styles nommes du document "
                  "comptent comme regle",
            "en": "automatic styles born of direct formatting are ignored, "
                  "only the document's named styles count as a rule"},
        "un PDF ne declare pas de marges : elles sont une propriete du "
        "dessin, pas une donnee du fichier, et ne sont donc pas "
        "inventoriees": {
            "fr": "un PDF ne declare pas de marges : elles sont une "
                  "propriete du dessin, pas une donnee du fichier, et ne "
                  "sont donc pas inventoriees",
            "en": "a PDF declares no margins: they are a property of the "
                  "drawing, not data held in the file, and so are not "
                  "inventoried"},
        "les objets ranges dans un flux compresse echappent a la lecture "
        "binaire : un compte de pages absent se declare plutot que de se "
        "deviner": {
            "fr": "les objets ranges dans un flux compresse echappent a la "
                  "lecture binaire : un compte de pages absent se declare "
                  "plutot que de se deviner",
            "en": "objects stored in a compressed stream escape the binary "
                  "reader: a missing page count is declared rather than "
                  "guessed"},
        "nombre de pages illisible sur ce fichier": {
            "fr": "nombre de pages illisible sur ce fichier",
            "en": "page count unreadable on this file"},
        "les polices listees sont celles nommees dans le fichier, leur "
        "presence sur la machine n'est pas verifiee": {
            "fr": "les polices listees sont celles nommees dans le fichier, "
                  "leur presence sur la machine n'est pas verifiee",
            "en": "the fonts listed are those named in the file, their "
                  "presence on the machine is not checked"},
        "une consigne de forme donnee hors du fichier (reglement PDF, page "
        "web, courriel) n'est pas couverte par cet inventaire": {
            "fr": "une consigne de forme donnee hors du fichier (reglement "
                  "PDF, page web, courriel) n'est pas couverte par cet "
                  "inventaire",
            "en": "a requirement of form given outside the file (PDF "
                  "regulations, web page, e-mail) is not covered by this "
                  "inventory"},
    },
})


VALEURS.update({
    # project.py : etats d'etape, types d'objet et statut de frontiere. Ce
    # sont les chaines ecrites dans projet.json et tapees sur la ligne de
    # commande : elles restent francaises dans les donnees, seul leur libelle
    # a l'ecran change.
    "project.etat": {
        "en_attente": {"fr": "en_attente", "en": "pending"},
        "en_cours": {"fr": "en_cours", "en": "in progress"},
        "termine": {"fr": "termine", "en": "done"},
        "saute": {"fr": "saute", "en": "skipped"},
        "bloque": {"fr": "bloque", "en": "blocked"},
    },
    "project.type_objet": {
        "figure": {"fr": "figure", "en": "figure"},
        "tableau": {"fr": "tableau", "en": "table"},
        "equation": {"fr": "equation", "en": "equation"},
        "annexe": {"fr": "annexe", "en": "appendix"},
    },
    "project.statut_frontiere": {
        "reprise": {"fr": "reprise", "en": "resumed"},
        "non reprise": {"fr": "non reprise", "en": "not resumed"},
    },
})


VALEURS.update({
    # figures.py : noms d'axe, d'objet compte et d'etape PRISMA. Ce sont des
    # mots du rapport d'audit, pas des cles de donnees : les cles de donnees
    # (forces, identifiees, doublons) restent telles quelles a l'ecran.
    "figures.axe": {
        "abscisses": {"fr": "abscisses", "en": "x"},
        "ordonnees": {"fr": "ordonnees", "en": "y"},
    },
    "figures.quoi": {
        "Categorie": {"fr": "Categorie", "en": "Category"},
        "Groupe": {"fr": "Groupe", "en": "Group"},
    },
    "figures.etape": {
        "criblage": {"fr": "criblage", "en": "screening"},
        "texte integral": {"fr": "texte integral", "en": "full text"},
    },
})


VALEURS.update({
    # images.py : verdicts fermes du catalogue, usages et motifs d'exclusion.
    # La valeur machine reste la chaine francaise, ici et dans le catalogue
    # ecrit sur le disque.
    "images.verdict": {
        "utilisable": {"fr": "utilisable", "en": "usable"},
        "sous le seuil": {"fr": "sous le seuil", "en": "below threshold"},
        "doublon": {"fr": "doublon", "en": "duplicate"},
        "dimensions illisibles": {"fr": "dimensions illisibles",
                                  "en": "dimensions unreadable"},
        "vecteur, resolution sans objet": {
            "fr": "vecteur, resolution sans objet",
            "en": "vector, resolution not applicable"},
        "hors perimetre": {"fr": "hors perimetre", "en": "out of scope"},
    },
    "images.usage": {
        "impression": {"fr": "impression", "en": "print"},
        "ecran": {"fr": "ecran", "en": "screen"},
    },
    "images.raison_ignore": {
        "fichier illisible": {"fr": "fichier illisible",
                              "en": "file unreadable"},
    },
    "images.statut_conversion": {
        "converti": {"fr": "converti", "en": "converted"},
        "source-absente": {"fr": "source-absente", "en": "source-missing"},
        "source-non-svg": {"fr": "source-non-svg", "en": "source-not-svg"},
        "aucun-backend": {"fr": "aucun-backend", "en": "no-backend"},
        "echec-backend": {"fr": "echec-backend", "en": "backend-failure"},
    },
})


# --- Resolution et acces ----------------------------------------------------

def resoudre_affichage(demandee=None, langue_analyse=None):
    """Langue d'affichage : l'option explicite, sinon la langue d'analyse,
    sinon le francais.

    La langue d'analyse est celle que resout lint-style.py (resoudre_langue) :
    ce module ne refait pas cette resolution, il en recoit le resultat. Un
    code hors fr et en retombe sur le francais SANS marque de repli : ce n'est
    pas un libelle manquant, c'est une langue d'affichage non couverte, et la
    mesure qui en depend le declare deja de son cote.
    """
    if demandee in LANGUES:
        return demandee
    if langue_analyse in LANGUES:
        return langue_analyse
    return LANGUE_DEFAUT


def t(cle, langue=None, /, **params):
    """Libelle d'affichage pour cette cle, dans cette langue.

    Les deux premiers parametres sont positionnels SEULEMENT (barre oblique) :
    sans cela, un libelle qui porte un parametre nomme « cle » ou « langue »
    entrerait en collision avec la signature, et l'appel echouerait au lieu de
    formater. Un libelle est libre de nommer ses parametres comme il veut.

    Une cle absente de la langue demandee retombe sur le francais et le
    DECLARE (prefixe MARQUE_REPLI) : le lecteur voit qu'il lit une chaine non
    traduite. Une cle inconnue de la table sort marquee elle aussi, jamais
    sous forme de cle brute silencieuse et jamais en levant une exception.

    Un parametre manquant, lui, leve : c'est une faute de programmation dans
    l'appelant, pas une donnee de l'utilisateur, et la garde des evals doit la
    voir plutot que la voir passer.
    """
    langue = langue if langue in LANGUES else LANGUE_DEFAUT
    entree = LIBELLES.get(cle)
    if entree is None:
        return MARQUE_INCONNU + str(cle)
    prefixe = ""
    modele = entree.get(langue)
    if modele is None:
        modele = entree.get(LANGUE_DEFAUT)
        prefixe = MARQUE_REPLI
    if modele is None:
        return MARQUE_INCONNU + str(cle)
    return prefixe + (modele.format(**params) if params else modele)


def valeur(espace, machine, langue=None):
    """Libelle d'une valeur machine (verdict, decision, axe, palier...).

    La valeur machine passee en entree n'est jamais modifiee : elle sert de
    cle. Une valeur absente de la table sort marquee MARQUE_INCONNU, ce qui
    rend visible un verdict ajoute au code sans libelle.
    """
    langue = langue if langue in LANGUES else LANGUE_DEFAUT
    entree = (VALEURS.get(espace) or {}).get(machine)
    if entree is None:
        return MARQUE_INCONNU + str(machine)
    libelle = entree.get(langue)
    if libelle is None:
        return MARQUE_REPLI + entree.get(LANGUE_DEFAUT, str(machine))
    return libelle


def motif(motif_fr, langue=None):
    """Libelle d'un motif de mesure non faite, porte par les donnees.

    Le motif circule en francais dans la structure et dans le JSON. Il est
    reconnu ici par motif ancre, ses parametres sont relus et reinjectes dans
    le libelle de la langue demandee. Un motif non reconnu sort marque.
    """
    langue = langue if langue in LANGUES else LANGUE_DEFAUT
    for regex, cle in MOTIFS_MESURE:
        m = regex.match(motif_fr or "")
        if m:
            return t(cle, langue, **m.groupdict())
    if langue == LANGUE_DEFAUT:
        return motif_fr
    return MARQUE_INCONNU + str(motif_fr)


# --- Controle de completude -------------------------------------------------

def cles_manquantes(langue):
    """Cles de LIBELLES sans libelle dans cette langue."""
    return sorted(c for c, e in LIBELLES.items() if not e.get(langue))


def valeurs_sans_libelle(langue):
    """Couples (espace, valeur machine) sans libelle dans cette langue."""
    return sorted((espace, machine)
                  for espace, table in VALEURS.items()
                  for machine, e in table.items() if not e.get(langue))
