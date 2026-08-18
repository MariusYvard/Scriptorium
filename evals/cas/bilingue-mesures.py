# -*- coding: utf-8 -*-
"""Cas d'eval des mesures qui dependent de la langue du document.

La 0.12.0 a donne un mode de langue au seul linter de style. Les quatre
autres mesures notaient toujours en francais : le scorecard n'avait aucun
moyen de dire la langue, readability rendait 0 % de passif sur un texte
anglais integralement passif, numbers criait au separateur decimal mixte sur
"1,234,567.89" et traceability ne voyait ni "Table" ni "Appendix". Ce module
verifie les corrections et, avant tout, qu'elles n'ont RIEN change en
francais.

Non-regression : les valeurs attendues du corpus francais ci-dessous ne sont
pas recalculees, elles sont GELEES en litteral. Elles ont ete relevees sur
les scripts de git HEAD avant modification, puis confrontees a la sortie
actuelle sur les 25 documents francais du depot (fixtures et jeu d'or) :
aucun ecart. Un litteral survit au commit suivant, une comparaison a HEAD
deviendrait tautologique des que le changement est valide.
"""
import os

lint = charger("lint-style.py", "lint_style")
score = charger("scorecard.py", "scorecard")
read = charger("readability.py", "readability")
nums = charger("numbers.py", "numbers")
trac = charger("traceability.py", "traceability")
cita = charger("citations.py", "citations")


FR = """# Methode

Le modele est entraine sur un corpus de 1 234 567 phrases annotees.
Le corpus a ete collecte sur deux serveurs et il est relu par trois annotateurs.
On observe une exactitude de 0,87 sur le jeu reserve, reportee dans le tableau 3.
La base de reference est decrite en annexe B, sous un accord public signe le 12 mars.
Chaque execution est repetee sur cinq graines, et la variance est calculee ensuite.
Les erreurs restantes sont rassemblees dans le tableau 3 et discutees en annexe B.

Tableau 3 : exactitude mesuree pour chaque configuration.

Annexe B : description de la base de reference.
"""

EN = """# Method

The model was trained on a corpus of 1,234,567 annotated sentences.
The corpus was collected on two servers and was reviewed by three annotators.
Accuracy was measured on the held-out split and was reported in Table 3.
A score of 0.87 was obtained on the first run and was confirmed on the second.
The baseline was described in Appendix B and was signed on 12 March.
Each run was repeated on five seeds, and the variance was computed on the results.
The remaining errors are grouped in Table 3 and are discussed in Appendix B.

Table 3: accuracy measured on each configuration.

Appendix B: baseline description, reproduced on request.
"""

EN_PRAGME = "<!-- lint-style:langue=en -->\n" + EN

# Valeurs relevees sur les scripts de git HEAD, avant ce lot.
SCORECARD_FR_GEL = {
    "total": 89,
    "verdict": "Pret",
    "axes": {"Style": 14, "Sources": 20, "Tracabilite": 20,
             "Terminologie et nombres": 20, "Lisibilite": 15},
    "deductions": {
        "Style": ["-3 ecart majeur (x1)", "-1 ecart mineur (x1)",
                  "-2 tic d'ecriture IA (x1)"],
        "Sources": [], "Tracabilite": [], "Terminologie et nombres": [],
        "Lisibilite": ["-5 rythme monotone (x1)"],
    },
}

READ_FR_GEL = {
    "mots": 103, "phrases": 8, "paragraphes": 4,
    "longueur_phrase_moyenne": 12.9, "longueur_phrase_ecart_type": 3.6,
    "phrases_longues_sup30_pct": 0.0, "phrases_courtes_inf8_pct": 12.5,
    "phrases_par_paragraphe_moyenne": 2.2, "densite_lexicale": 0.65,
    "taux_passif_approx_pct": 0.0, "indice_lix": 42.0,
}

TRAC_FR_GEL = {"tableau": [3], "annexe": [2], "figure": [], "equation": []}


# --- Non-regression du francais (5 cas) --------------------------------------

_sc_fr = score.evaluer(FR)
_axes_fr = {n: a["score"] for n, a in _sc_fr["axes"].items()}

verifier("fr : total, verdict et score de chaque axe sont ceux d'avant le lot",
         (_sc_fr["total"], _sc_fr["verdict"]) == (SCORECARD_FR_GEL["total"],
                                                  SCORECARD_FR_GEL["verdict"])
         and _axes_fr == SCORECARD_FR_GEL["axes"],
         "total=%s verdict=%s axes=%s" % (_sc_fr["total"], _sc_fr["verdict"],
                                          _axes_fr))

verifier("fr : les deductions sont les memes, libelle par libelle",
         {n: a["deductions"] for n, a in _sc_fr["axes"].items()}
         == SCORECARD_FR_GEL["deductions"],
         str({n: a["deductions"] for n, a in _sc_fr["axes"].items()}))

_rd_fr = read.mesurer(FR)
verifier("fr : les onze mesures de lisibilite sont inchangees",
         {k: _rd_fr[k] for k in READ_FR_GEL} == READ_FR_GEL,
         str({k: _rd_fr[k] for k in READ_FR_GEL if _rd_fr[k] != READ_FR_GEL[k]}))

_tr_fr = trac.analyser(FR)
verifier("fr : sequences des objets numerotes et separateur decimal inchanges",
         {o: _tr_fr["sequences"][o]["numeros"] for o in TRAC_FR_GEL}
         == TRAC_FR_GEL
         and nums.analyser("Valeurs 1,5 et 2.5.")["separateur_decimal_mixte"] is True
         and nums.analyser(FR)["separateur_decimal_mixte"] is False,
         str({o: _tr_fr["sequences"][o]["numeros"] for o in TRAC_FR_GEL}))

verifier("fr : le pronom indefini on reste releve et le passif accentue "
         "reste mesure",
         any(c["regle"] == "pronom-on" for c in lint.lint_text(FR))
         and read.mesurer("Le rapport est publié par le comité. Les données "
                          "sont vérifiées par deux relecteurs."
                          )["taux_passif_approx_pct"] > 0)


# --- La langue traverse le scorecard (5 cas) ---------------------------------

verifier("scorecard : la langue retenue est rendue, et le defaut reste le "
         "francais sur un texte anglais sans pragme ni option",
         score.evaluer(FR)["langue"] == "fr"
         and score.evaluer(EN, langue="en")["langue"] == "en"
         and score.evaluer(EN)["langue"] == "fr")

verifier("scorecard : le pragme du document est honore sans aucune option, "
         "et l'option explicite prime sur lui",
         score.evaluer(EN_PRAGME)["langue"] == "en"
         and score.evaluer(EN_PRAGME, langue="fr")["langue"] == "fr",
         str(score.evaluer(EN_PRAGME)["langue"]))

_on_fr = sum(1 for c in lint.lint_text(EN, None, "fr") if c["regle"] == "pronom-on")
verifier("scorecard : la preposition anglaise on ne declenche plus la regle "
         "francaise pronom-on",
         _on_fr >= 5 and not any(c["regle"] == "pronom-on"
                                 for c in lint.lint_text(EN, None, "en")),
         "constats en mode fr : %d" % _on_fr)

verifier("scorecard : l'axe Style d'un texte anglais remonte une fois la "
         "langue dite, les faux positifs francais ayant disparu",
         score.evaluer(EN, langue="en")["axes"]["Style"]["score"]
         > score.evaluer(EN)["axes"]["Style"]["score"],
         "fr=%s en=%s" % (score.evaluer(EN)["axes"]["Style"]["score"],
                          score.evaluer(EN, langue="en")["axes"]["Style"]["score"]))

# La langue ne s'arrete pas au linter. Ces deux mesures ne bougent QUE si
# numbers et traceability l'ont recue depuis le scorecard.
EN_NOMBRE = "The budget reached 1,234,567.89 euros in 2024."
EN_ORPHELIN = "The method is described in the text.\n\nTable 7: unused caption.\n"
verifier("scorecard : les axes des nombres et de la tracabilite suivent la "
         "meme langue que le linter",
         "-2 separateur decimal mixte (x1)"
         in score.evaluer(EN_NOMBRE)["axes"]["Terminologie et nombres"]["deductions"]
         and not score.evaluer(EN_NOMBRE, langue="en"
                               )["axes"]["Terminologie et nombres"]["deductions"]
         and "-2 objet jamais appele (x1)"
         in score.evaluer(EN_ORPHELIN, langue="en")["axes"]["Tracabilite"]["deductions"]
         and not score.evaluer(EN_ORPHELIN)["axes"]["Tracabilite"]["deductions"],
         str(score.evaluer(EN_ORPHELIN, langue="en")["axes"]["Tracabilite"]))


# --- Le passif anglais, et la mesure qui se declare non faite (6 cas) --------

verifier("passif : un texte anglais integralement passif n'est plus mesure a "
         "zero pour cent",
         read.mesurer(EN, "en")["taux_passif_approx_pct"] > 25
         and read.mesurer(EN, "fr")["taux_passif_approx_pct"] == 0.0,
         "en=%s fr=%s" % (read.mesurer(EN, "en")["taux_passif_approx_pct"],
                          read.mesurer(EN, "fr")["taux_passif_approx_pct"]))

verifier("passif : la regle d'interpretation, injoignable jusqu'ici en "
         "anglais, se declenche enfin",
         any("passif" in n.lower() for n in read.interpreter(read.mesurer(EN, "en"))),
         str(read.interpreter(read.mesurer(EN, "en"))))

verifier("passif : le motif anglais est celui de lint-style.py, pas une copie",
         read._lint()._PASSIF_EN.pattern == lint._PASSIF_EN.pattern
         and "_PASSIF_EN = " not in open(
             os.path.join(SCRIPTS, "readability.py"), encoding="utf-8").read())

_hors = read.mesurer(EN, "de")
verifier("passif : une langue hors perimetre rend None, jamais zero, et "
         "nomme son motif",
         _hors["taux_passif_approx_pct"] is None
         and [m["mesure"] for m in _hors["mesures_non_faites"]]
         == ["taux_passif_approx_pct"]
         and "de" in _hors["mesures_non_faites"][0]["motif"],
         str(_hors["mesures_non_faites"]))

_vide = read.mesurer("   \n\n   ")
verifier("passif : un texte sans phrase mesurable declare la mesure non "
         "faite, et le rapport comme la lecture le disent",
         _vide["taux_passif_approx_pct"] is None
         and "aucune phrase" in _vide["mesures_non_faites"][0]["motif"]
         and "non mesuré" in read.rapport_texte(_hors)
         and any("Mesure non faite" in n for n in read.interpreter(_hors)),
         str(read.interpreter(_hors)))

# Le scorecard consomme une valeur qui peut desormais valoir None. La mesure
# absente doit sortir du calcul ET etre nommee dans l'axe, jamais offrir
# quatre points gratuits en silence. Meme procede de substitution que le cas
# check-presentation de run-evals.py : la vraie fonction est rendue ensuite.
_vrai_mesurer = score.read.mesurer


def _mesurer_sans_passif(texte, langue=None):
    m = dict(_vrai_mesurer(texte, langue))
    m["taux_passif_approx_pct"] = None
    m["mesures_non_faites"] = [{"mesure": "taux_passif_approx_pct",
                                "motif": "substitution d'eval"}]
    return m


score.read.mesurer = _mesurer_sans_passif
_sc_sans = score.evaluer(FR)
score.read.mesurer = _vrai_mesurer

verifier("scorecard : une mesure de lisibilite non faite sort du calcul, est "
         "nommee dans l'axe et reparait dans le rapport texte",
         [m["mesure"] for m in _sc_sans["axes"]["Lisibilite"]["mesures_non_faites"]]
         == ["taux_passif_approx_pct"]
         and not any("passif" in d for d in
                     _sc_sans["axes"]["Lisibilite"]["deductions"])
         and "mesure non faite : taux_passif_approx_pct"
         in score.rapport_texte(_sc_sans),
         str(_sc_sans["axes"]["Lisibilite"]))


# --- Nombres : la convention depend de la langue (5 cas) ---------------------

verifier("nombres : un grand nombre anglais bien forme ne declenche plus "
         "rien, virgule de milliers et point decimal reunis",
         nums.analyser("Revenue of 1,234,567.89 and 12,000.5 dollars.",
                       "en")["separateur_decimal_mixte"] is False)

verifier("nombres : le meme nombre reste un melange en francais, ou la "
         "virgule de milliers n'existe pas",
         nums.analyser("Revenue of 1,234,567.89 dollars.",
                       "fr")["separateur_decimal_mixte"] is True)

verifier("nombres : en anglais, une virgule decimale residuelle a cote d'un "
         "point decimal reste un melange",
         nums.analyser("Two values, 1,5 and 2.5, were compared.",
                       "en")["separateur_decimal_mixte"] is True)

verifier("nombres : une virgule de milliers isolee ne suffit pas a crier au "
         "melange, faute de point decimal",
         nums.analyser("The sample holds 1,234 items.",
                       "en")["separateur_decimal_mixte"] is False)

verifier("nombres : l'espace avant le signe pourcent est fautive en anglais "
         "et attendue en francais",
         nums.analyser("The share reached 42 % of the total.", "en"
                       )["espacement_pourcent"]
         and not nums.analyser("La part atteint 42 % du total.", "fr"
                               )["espacement_pourcent"]
         and not nums.analyser("The share reached 42% of the total.", "en"
                               )["espacement_pourcent"]
         and nums.analyser("La part atteint 42% du total.", "fr"
                           )["espacement_pourcent"])


# --- Tracabilite : Table et Appendix (4 cas) ---------------------------------

_tr_en = trac.analyser(EN, "en")

verifier("tracabilite : Table 3 est enfin reconnue comme un tableau defini "
         "et appele dans un manuscrit anglais",
         _tr_en["sequences"]["tableau"]["numeros"] == [3]
         and _tr_en["tableaux_definis_non_appeles"] == []
         and _tr_en["tableaux_appeles_non_definis"] == [],
         str(_tr_en["sequences"]["tableau"]))

verifier("tracabilite : Appendix B est reconnu, en notation alphabetique",
         _tr_en["sequences"]["annexe"]["numeros"] == [2]
         and _tr_en["sequences"]["annexe"]["notation"] == "alphabetique",
         str(_tr_en["sequences"]["annexe"]))

verifier("tracabilite : le controle de sequence de la 0.11.0 s'applique aux "
         "objets anglais, sans faire du mot table un objet en francais",
         any(a["objet"] == "tableau" and a["anomalie"] == "numero_manquant"
             and a["numeros"] == [2]
             for a in trac.analyser(
                 "See Table 1 and Table 3.\n\nTable 1: first.\n\n"
                 "Table 3: third.\n", "en")["numerotation_anomalies"])
         and trac.analyser("La table 3 de la salle est occupee.\n\n"
                           "Table 3 : plan de salle.\n", "fr"
                           )["sequences"]["tableau"]["numeros"] == [])

verifier("tracabilite : aucune cle consommee par le scorecard n'a disparu",
         all(c in _tr_en for c in (
             "citations_pendantes", "references_orphelines",
             "figures_appelees_non_definies", "figures_definies_non_appelees",
             "tableaux_appeles_non_definis", "tableaux_definis_non_appeles",
             "sequences", "numerotation_anomalies", "tags_lacune_materielle")))


# --- Citations : deux normes anglaises n'etaient pas anglaises (3 cas) -------

BIB = ("@article{k1,\n author={Doe, Jane and Roe, Ann and Poe, Al},\n"
       " title={Un titre},\n journal={Revue},\n year={2024}\n}\n"
       "@misc{k2,\n publisher={P}\n}\n")
_e1, _e2 = cita.parser_bibtex(BIB)

verifier("citations : APA 7 relie le dernier auteur par l'esperluette en "
         "anglais, et garde et en francais",
         cita.format_apa(_e1, "en").startswith("Doe, J., Roe, A., & Poe, A.")
         and cita.format_apa(_e1).startswith("Doe, J., Roe, A. et Poe, A."),
         cita.format_apa(_e1, "en"))

verifier("citations : Chicago relie le dernier auteur par and en anglais, et "
         "garde et en francais",
         cita.format_chicago(_e1, "en").startswith(
             "Doe, Jane, Ann Roe, and Al Poe.")
         and cita.format_chicago(_e1).startswith(
             "Doe, Jane, Ann Roe, et Al Poe."),
         cita.format_chicago(_e1, "en"))

verifier("citations : les replis anglais sont Anonymous, Untitled et n.d. "
         "dans les cinq formats, MLA et IEEE gardent leur liste d'auteurs, "
         "et le francais reste le defaut",
         all("Anonymous" in cita.FORMATS[s](_e2, "en")
             and "Untitled" in cita.FORMATS[s](_e2, "en") for s in cita.FORMATS)
         and "n.d." in cita.format_apa(_e2, "en")
         and not any(x in cita.format_apa(_e2, "en")
                     for x in ("Anonyme", "Sans titre", "s.d."))
         and all(cita.FORMATS[s](_e1) == cita.FORMATS[s](_e1, "en")
                 for s in ("mla", "ieee"))
         and all(cita.FORMATS[s](_e1) == cita.FORMATS[s](_e1, "fr")
                 for s in cita.FORMATS),
         str([cita.FORMATS[s](_e2, "en") for s in cita.FORMATS]))
