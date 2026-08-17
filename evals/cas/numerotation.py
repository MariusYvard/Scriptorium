# -*- coding: utf-8 -*-
"""Cas d'eval de la numerotation des objets legendes.

Apparier les numeros ne suffit pas : ce module verifie que traceability.py
controle la SEQUENCE (doublon, saut, depart hors 1, notation mixte) pour les
figures, les tableaux, les equations et les annexes, et qu'une numerotation
correcte ne declenche rien. Il verifie aussi que les cles consommees par
scorecard.py restent presentes dans la sortie d'analyser().
"""

trac = charger("traceability.py", "traceability")
score = charger("scorecard.py", "scorecard")


def anomalies(texte, objet=None):
    """Liste les anomalies de numerotation, filtrees sur un type d'objet."""
    d = trac.analyser(texte)
    return [a for a in d["numerotation_anomalies"]
            if objet is None or a["objet"] == objet]


def genres(texte, objet=None):
    return sorted({a["anomalie"] for a in anomalies(texte, objet)})


# --- Figures : doublon, saut, depart hors 1 ---------------------------------

FIG_FAUTIF = (
    "La figure 1 pose le cadre, la figure 3 le detail, la figure 4 le bilan.\n\n"
    "Figure 1 : cadre general.\n\n"
    "Figure 3 : detail du dispositif.\n\n"
    "Figure 4 : bilan des mesures.\n\n"
    "Figure 4 : bilan corrige.\n")

_a_fig = anomalies(FIG_FAUTIF, "figure")
verifier("numerotation : deux legendes au meme numero de figure sont un doublon",
         any(a["anomalie"] == "numero_duplique" and a["numeros"] == [4]
             for a in _a_fig), str(_a_fig))
verifier("numerotation : le numero saute est nomme, pas seulement compte",
         any(a["anomalie"] == "numero_manquant" and a["numeros"] == [2]
             for a in _a_fig), str(_a_fig))
verifier("numerotation : un depart a 1 ne declenche pas le constat de depart",
         "ne_commence_pas_a_un" not in genres(FIG_FAUTIF, "figure"),
         str(_a_fig))

FIG_DEPART_DEUX = ("Voir la figure 2 puis la figure 3.\n\n"
                   "Figure 2 : premiere planche.\n\n"
                   "Figure 3 : seconde planche.\n")
_a_depart = anomalies(FIG_DEPART_DEUX, "figure")
verifier("numerotation : une suite qui ne commence pas a 1 est signalee",
         [a["anomalie"] for a in _a_depart] == ["ne_commence_pas_a_un"]
         and _a_depart[0]["numeros"] == [2], str(_a_depart))
verifier("numerotation : un depart hors 1 ne fabrique pas de saut",
         trac.analyser(FIG_DEPART_DEUX)["sequences"]["figure"]["manquants"] == [])

# --- Tableaux : meme traitement que les figures -----------------------------

TAB_FAUTIF = ("Le tableau 1 et le tableau 2 resument les series.\n\n"
              "Tableau 1 : caracteristiques de la population.\n\n"
              "Tableau 2 : resultats principaux.\n\n"
              "Tableau 2 : resultats secondaires.\n")
verifier("numerotation : le doublon vaut aussi pour les tableaux",
         genres(TAB_FAUTIF, "tableau") == ["numero_duplique"],
         str(anomalies(TAB_FAUTIF)))

# --- Equations : les trois notations retenues -------------------------------

EQ_LEGENDE = ("Le bilan suit l'equation 1, l'ecart suit l'equation 3.\n\n"
              "Equation 1 : bilan de matiere.\n\n"
              "Equation 3 : ecart relatif.\n")
verifier("numerotation : une equation legendee en toutes lettres est suivie",
         trac.analyser(EQ_LEGENDE)["sequences"]["equation"]["numeros"] == [1, 3])
verifier("numerotation : le saut d'equation est signale comme celui des figures",
         genres(EQ_LEGENDE, "equation") == ["numero_manquant"],
         str(anomalies(EQ_LEGENDE)))

EQ_TAG = ("Le resultat vient de l'equation (1) et de l'equation (3).\n\n"
          "$$ a = b + c \\tag{1}$$\n\n"
          "$$ d = e \\tag{3}$$\n")
_d_tag = trac.analyser(EQ_TAG)
verifier("numerotation : \\tag{n} vaut definition d'equation",
         _d_tag["sequences"]["equation"]["numeros"] == [1, 3],
         str(_d_tag["sequences"]["equation"]))
verifier("numerotation : une equation appelee dans le texte n'est pas dite orpheline",
         _d_tag["equations_definies_non_appelees"] == [],
         str(_d_tag["equations_definies_non_appelees"]))

EQ_DROITE = ("La relation est donnee par l'equation (1).\n\n"
             "$$ y = ax + b $$ (1)\n")
verifier("numerotation : le numero de droite d'une ligne d'affichage est lu",
         trac.analyser(EQ_DROITE)["sequences"]["equation"]["numeros"] == [1])

EQ_ORPHELINE = ("Le calcul renvoie a l'equation 5, qui n'existe pas.\n\n"
                "$$ y = ax + b $$ (1)\n")
verifier("numerotation : une equation appelee sans definition est signalee",
         trac.analyser(EQ_ORPHELINE)["equations_appelees_non_definies"] == [5],
         str(trac.analyser(EQ_ORPHELINE)["equations_appelees_non_definies"]))

# --- Annexes : lettres, notation mixte, faux positif -------------------------

ANX_LETTRES = ("Le protocole est en annexe A, les donnees en annexe C.\n\n"
               "## References\n\n1. Une source citee [1].\n\n"
               "Annexe A : protocole detaille.\n\n"
               "Annexe C : donnees brutes.\n")
_d_anx = trac.analyser(ANX_LETTRES)
verifier("numerotation : les annexes se lisent apres la bibliographie",
         _d_anx["sequences"]["annexe"]["notation"] == "alphabetique"
         and _d_anx["sequences"]["annexe"]["numeros"] == [1, 3],
         str(_d_anx["sequences"]["annexe"]))
verifier("numerotation : le saut d'annexe se restitue en lettres, pas en rangs",
         any("'B'" in p for p in trac.problemes(_d_anx)),
         str(trac.problemes(_d_anx)))

ANX_MIXTE = ("Voir annexe 1 et annexe B.\n\n"
             "Annexe 1 : premiere piece.\n\n"
             "Annexe B : seconde piece.\n")
verifier("numerotation : chiffres et lettres melanges dans les annexes sont signales",
         genres(ANX_MIXTE, "annexe") == ["notation_mixte"],
         str(anomalies(ANX_MIXTE)))

ANX_FAUX_POSITIF = ("L'annexe a ete jointe au dossier. "
                    "Le rapport et son annexe ont ete transmis ensemble.\n")
verifier("numerotation : une phrase ou annexe est suivie d'un mot ne cree pas d'objet",
         trac.analyser(ANX_FAUX_POSITIF)["sequences"]["annexe"]["numeros"] == []
         and anomalies(ANX_FAUX_POSITIF) == [])

# --- Cas negatifs : une numerotation correcte ne declenche rien --------------

SAIN_FIGURES = ("Le cadre est pose par la figure 1, le detail par la figure 2, "
                "le bilan par la figure 3.\n\n"
                "Figure 1 : cadre general.\n\n"
                "Figure 2 : detail du dispositif.\n\n"
                "Figure 3 : bilan des mesures.\n")
verifier("numerotation : trois figures numerotees dans l'ordre ne declenchent rien",
         anomalies(SAIN_FIGURES) == [], str(anomalies(SAIN_FIGURES)))

SAIN_MIXTE = ("La figure 1 illustre le tableau 1, l'equation 1 les relie, "
              "le detail est en annexe A.\n\n"
              "Figure 1 : illustration.\n\n"
              "Tableau 1 : donnees sources.\n\n"
              "Equation 1 : relation entre les deux.\n\n"
              "Annexe A : calcul detaille.\n")
verifier("numerotation : quatre types d'objets corrects ne declenchent rien",
         anomalies(SAIN_MIXTE) == [], str(anomalies(SAIN_MIXTE)))

SAIN_VIDE = ("Un texte suivi, sans figure, sans tableau, sans equation "
             "et sans annexe. Il enonce un fait date de 2025.\n")
_d_vide = trac.analyser(SAIN_VIDE)
verifier("numerotation : un texte sans objet numerote ne declenche rien",
         _d_vide["numerotation_anomalies"] == []
         and all(_d_vide["sequences"][o]["numeros"] == []
                 for o in ("figure", "tableau", "equation", "annexe")),
         str(_d_vide["sequences"]))

# --- Contrat de sortie : les cles lues ailleurs restent presentes ------------

# Cles consommees par scorecard.py (axe Tracabilite) et par run-evals.py.
# Ajouter une cle est permis, en renommer une casse le scorecard en silence.
CLES_CONSOMMEES = (
    "citations_pendantes", "references_orphelines",
    "figures_appelees_non_definies", "figures_definies_non_appelees",
    "tableaux_appeles_non_definis", "tableaux_definis_non_appeles",
    "biblio_presente", "references_definies",
    "tags_lacune_materielle", "tags_preuve_faible",
    "tags_variantes_mal_formees", "tags_par_section",
)
_sortie = trac.analyser(FIG_FAUTIF)
_absentes = [c for c in CLES_CONSOMMEES if c not in _sortie]
verifier("numerotation : aucune cle consommee par le scorecard n'a disparu",
         not _absentes, f"absentes={_absentes}")

_nouvelles = ("equations_definies_non_appelees", "equations_appelees_non_definies",
              "annexes_definies_non_appelees", "annexes_appelees_non_definies",
              "sequences", "numerotation_anomalies")
verifier("numerotation : les cles ajoutees sont toutes exposees",
         all(c in _sortie for c in _nouvelles),
         f"manquantes={[c for c in _nouvelles if c not in _sortie]}")

_sc = score.evaluer(FIG_FAUTIF)
verifier("numerotation : le scorecard traverse toujours l'axe Tracabilite",
         _sc["axes"]["Tracabilite"]["score"] is not None, str(_sc["axes"]["Tracabilite"]))
