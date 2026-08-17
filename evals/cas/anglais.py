# -*- coding: utf-8 -*-
"""Cas d'eval du mode de langue du linter de style.

Deux exigences dominent. La non-regression du francais : un texte francais
rend exactement les memes constats qu'avant l'ajout de l'anglais, virgule
d'Oxford comprise. L'absence de faux positif en anglais : une phrase
scientifique correcte, virgule serielle incluse, ne declenche rien.
"""

lint = charger("lint-style.py", "lint_style")


def regles(texte, langue=None):
    return {c["regle"] for c in lint.lint_text(texte, None, langue)}


def severite(texte, langue, nom):
    return {c["severite"] for c in lint.lint_text(texte, None, langue)
            if c["regle"] == nom}


# --- Non-regression du francais ---

FR = ("Le rapport presente les resultats, et la mesure. On observe cette "
      "tendance dans plusieurs series de valeurs.")

verifier("fr par defaut : la virgule d'Oxford se declenche toujours",
         "virgule-oxford" in regles(FR), str(regles(FR)))

verifier("fr par defaut : pronom on et quantificateur vague toujours releves",
         {"pronom-on", "quantif-vague"} <= regles(FR), str(regles(FR)))

verifier("fr : le tiret cadratin reste un constat critique",
         severite("Un fait — puis un autre.", None, "tiret-cadratin")
         == {"critique"})

verifier("fr : le jeu de regles est REGLES telle quelle, dans son ordre",
         lint.regles_pour("fr") is lint.REGLES)

verifier("fr : chaque regle de REGLES declare sa famille",
         set(lint.FAMILLE) >= {r[2] for r in lint.REGLES},
         str({r[2] for r in lint.REGLES} - set(lint.FAMILLE)))


# --- Absence de faux positif en anglais ---

EN_PROPRE = ("We measured the response of the sample, the reference, and the "
             "control. The difference was statistically significant "
             "(p < 0.001). Figure 1 shows the calibration curve.")

verifier("en : une phrase scientifique correcte ne declenche aucun constat",
         lint.lint_text(EN_PROPRE, None, "en") == [],
         str(regles(EN_PROPRE, "en")))

verifier("en : les regles calibrees sur le francais sortent du jeu anglais, "
         "virgule serielle en tete",
         not ({"virgule-oxford", "pronom-on", "quantif-vague",
               "tiret-cadratin"} & {r[2] for r in lint.regles_pour("en")}))

verifier("en : significant ancre dans un test statistique ne declenche rien",
         "significance-non-statistique" not in regles(EN_PROPRE, "en"))

ISE = ("The authors exercise caution. The dataset comprises three cohorts. "
       "We revise the model and advertise the color of each marker.")

US_SEUL = "We analyzed the color and the behavior of the fiber at the center."
GB_SEUL = "We analysed the colour and the behaviour of the fibre at the centre."

verifier("en : une variante unique et les verbes toujours en -ise ne font "
         "pas un melange orthographique",
         not any("orthographe-melangee" in regles(t, "en")
                 for t in (ISE, US_SEUL, GB_SEUL)),
         str(regles(ISE, "en") | regles(US_SEUL, "en") | regles(GB_SEUL, "en")))

verifier("en : deux tirets cadratins ne sont ni critiques ni trop denses",
         not regles("The result — a modest gain — was confirmed by the "
                    "second run of the experiment.", "en"))


# --- Regles propres a l'anglais ---

verifier("en : lexique promotionnel transpose, en critique",
         severite("This pivotal work offers a cutting-edge method.", "en",
                  "lexique-promo") == {"critique"})

verifier("en : vocabulaire en exces mesure releve en majeur",
         severite("We delve into the intricate details with meticulous care.",
                  "en", "lexique-ia-en") == {"majeur"})

verifier("en : landscape au sens figure repere par cooccurrence",
         "lexique-ia-en" in regles("The research landscape has changed.", "en"))

verifier("en : verbes tics releves en mineur",
         severite("The results underscore the value and showcase the method.",
                  "en", "verbe-tic") == {"mineur"})

verifier("en : utilize renvoye vers use",
         "lexique-faible" in regles("We utilize a new solver.", "en"))

verifier("en : metadiscours anglais releve en majeur",
         severite("It is worth noting that the effect holds.", "en",
                  "metadiscours") == {"majeur"})

verifier("en : significant hors contexte statistique est un majeur",
         severite("This is a significant improvement in usability.", "en",
                  "significance-non-statistique") == {"majeur"})

verifier("en : nominalisation lourde relevee",
         "nominalisation" in regles(
             "We make an assessment of the data and perform an analysis of "
             "the residuals.", "en"))

verifier("en : modalisateurs empiles releves en majeur",
         severite("The findings may potentially suggest an effect.", "en",
                  "hedge-empile") == {"majeur"})


# --- Pieges du francophone ---

verifier("en : espace avant le signe double relevee en majeur, sans piege "
         "sur la rangee d'alignement d'un tableau markdown",
         severite("The result is clear : the effect holds ; the model fits.",
                  "en", "espace-avant-ponctuation") == {"majeur"}
         and not severite("| Metric | Value |\n| --- | :--- |\n| R | 0.9 |\n",
                          "en", "espace-avant-ponctuation"))

verifier("en : pluriel d'un nom indenombrable releve en majeur",
         severite("We collected informations and researches from three sites.",
                  "en", "indenombrable-en") == {"majeur"})

verifier("en : faux amis et calques releves en mineur",
         severite("We actually control that the sample is complete.", "en",
                  "faux-ami") == {"mineur"})

# --- Regles anglaises lues a l'echelle du document ---

MELANGE = ("We analysed the colour of the fiber and the behavior measured at "
           "the center of the plate.")
c_melange = [c for c in lint.lint_text(MELANGE, None, "en")
             if c["regle"] == "orthographe-melangee"]

verifier("en : le melange des deux orthographes est un majeur unique, qui "
         "nomme les formes trouvees de chaque cote",
         len(c_melange) == 1 and c_melange[0]["severite"] == "majeur"
         and "colour" in c_melange[0]["extrait"]
         and "behavior" in c_melange[0]["extrait"],
         str([(c["regle"], c.get("extrait"))
              for c in lint.lint_text(MELANGE, None, "en")]))

verifier("en : le tiret cadratin est signale sur sa densite, en mineur",
         severite("One — two — three — four.", "en",
                  "tiret-cadratin-densite") == {"mineur"})

PASSIF = ("The samples were collected in June. The data were reviewed by two "
          "readers. The protocol was approved by the committee. The results "
          "are reported below. The figures were prepared by the first author. "
          "The manuscript was written by all authors. The study was funded by "
          "a public grant.")

verifier("en : la part de phrases passives est mesuree sur le document",
         "passif-excessif" in regles(PASSIF, "en"), str(regles(PASSIF, "en")))


# --- Regles communes aux deux langues ---

COMMUN = ("The “quoted” passage cites "
          "https://exemple.fr/page?utm_source=lettre in full.")

verifier("en : typographie courbe et parametre de suivi restent critiques",
         {"typographie-courbe", "url-suivi"} <= regles(COMMUN, "en"),
         str(regles(COMMUN, "en")))

# --- Determination de la langue ---

TXT_FR = ("Le rapport presente les resultats de la mesure dans les conditions "
          "decrites par la methode, avec les incertitudes qui sont associees "
          "a chaque valeur, sans que cette limite soit levee.")
TXT_EN = ("The study was designed to compare the two methods that are used in "
          "this field, and the results are reported with their confidence "
          "intervals.")

verifier("detection : un texte francais et un texte anglais sont separes",
         lint.detecter_langue(TXT_FR) == "fr"
         and lint.detecter_langue(TXT_EN) == "en",
         "%s / %s" % (lint.detecter_langue(TXT_FR),
                      lint.detecter_langue(TXT_EN)))

verifier("detection : un echantillon trop court rend le defaut, pas un pari",
         lint.detecter_langue("Titre court.", "en") == "en"
         and lint.detecter_langue("Titre court.") == "fr")

verifier("langue : le pragme du document est lu, sinon le francais",
         lint.resoudre_langue("<!-- lint-style:langue=en -->\nSome text.")
         == "en"
         and lint.resoudre_langue("Un texte sans pragme.") == "fr")

verifier("langue : l'option explicite prime sur le pragme du document",
         lint.resoudre_langue("<!-- lint-style:langue=en -->\nSome text.",
                              "fr") == "fr")
