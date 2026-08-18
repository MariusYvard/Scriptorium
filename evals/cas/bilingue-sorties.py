# -*- coding: utf-8 -*-
"""Cas d'eval des livrables et des detecteurs de style bilingues.

Portee : figures.py (etiquettes des figures strategiques et du schema
PRISMA), ai-fingerprint.py, check-temporel.py et coherence.py.

Deux exigences dominent, dans cet ordre.

La non-regression du francais. Les valeurs francaises gelees plus bas ne
sont pas recopiees de la sortie courante : elles ont ete relevees sur la
version HEAD des quatre scripts, executee dans le meme processus que la
version modifiee, et les vingt-six mesures comparees etaient identiques.
Les figer en litteral fait echouer ce module si un rendu francais bouge,
au lieu de suivre la derive en silence.

Les libelles officiels en anglais. Le schema PRISMA d'une revue publiee en
anglais est lu par des relecteurs qui attendent les libelles de la
declaration PRISMA 2020, pas une traduction : ils sont verifies mot pour
mot, et l'absence de tout mot francais dans le SVG est verifiee en parsant
le document, pas en cherchant dans la chaine.
"""
import datetime
import hashlib
import xml.etree.ElementTree as ET

aifp = charger("ai-fingerprint.py", "ai_fingerprint_bil")
coh = charger("coherence.py", "coherence_bil")
ctmp = charger("check-temporel.py", "check_temporel_bil")
figs = charger("figures.py", "figures_bil")

REF = datetime.date(2026, 8, 17)

# --- Textes de mesure ------------------------------------------------------

FR_TIC = ("De plus, le un. De plus, le deux. De plus, le trois. De plus, le "
          "quatre. De plus, le cinq. De plus, le six. De plus, le sept. "
          "De plus, le huit.")
FR_TRI = ("Le rapport traite des couts, des delais et des risques. La mesure "
          "porte sur la vitesse, la masse et la duree. Il ne s'agit pas "
          "seulement d'un cout mais d'un choix. Les series repetent la meme "
          "mesure, la meme mesure, la meme mesure, la meme mesure.")
FR_PROM = ("Nous montrerons dans la suite que la mesure tient. La section 3 "
           "presente le protocole. Nous y reviendrons plus loin.")
FR_TEMP = ("Le lancement a eu lieu en 2099. La reforme de 2022 a permis la "
           "croissance de 2018. Le modele le plus recent depasse les autres. "
           "A ce jour, aucune replication n'est publiee.")

EN_TIC = ("Moreover, the first result holds. Moreover, the second result "
          "holds. Moreover, the third result holds. Moreover, the fourth "
          "result holds. Moreover, the fifth result holds. Moreover, the "
          "sixth result holds. Moreover, the seventh one holds. Moreover, "
          "the eighth one holds.")
EN_TRI = ("The study covers cost, delay and risk. The model is not only "
          "faster but also cheaper. The sample size, the design and the "
          "outcome are reported.")
EN_PLAT = ("The reported concentration of the compound in the water of the "
           "river of the region is high. The concentration of the compound "
           "in the water of the river is stable over the period. The water "
           "of the river of the region is monitored by the agency.")
EN_PROM = ("We will show that the estimator is consistent. This section "
           "presents the protocol. As discussed below, the bias is small.")
EN_TEMP = ("The launch took place in 2099. The 2022 reform led to the 2018 "
           "growth. The most recent model outperforms the others. To date, "
           "no replication has been published.")

# Jeu de donnees du schema PRISMA, identique dans les deux langues : seules
# les etiquettes ecrites dans le code changent, jamais les cles.
PRISMA_FR = {"identifiees": {"Bases de donnees": 420, "Autres sources": 15},
             "doublons": 60, "examinees": 375,
             "ecartees_titre": [{"motif": "Hors sujet", "n": 150},
                                {"motif": "Langue non couverte", "n": 50}],
             "evaluees": 175,
             "ecartees_texte": [{"motif": "Methode insuffisante", "n": 90},
                                {"motif": "Population differente", "n": 50}],
             "incluses": 35}
PRISMA_EN = {"identifiees": {"Databases": 420, "Registers": 15},
             "doublons": 60, "examinees": 375,
             "ecartees_titre": [{"motif": "Off topic", "n": 150},
                                {"motif": "Language not covered", "n": 50}],
             "evaluees": 175,
             "ecartees_texte": [{"motif": "Insufficient method", "n": 90},
                                {"motif": "Different population", "n": 50}],
             "incluses": 35}
SWOT = {"forces": ["a", "b"], "faiblesses": ["c"], "opportunites": ["d"],
        "menaces": ["e"]}


def _sha(svg):
    return hashlib.sha256(svg.encode("utf-8")).hexdigest()


def _textes(svg):
    """Contenu des elements <text> du SVG, lu par un parseur XML : une
    recherche de sous-chaine trouverait aussi les noms de police et les
    attributs, et ne prouverait rien sur ce que le lecteur voit."""
    racine = ET.fromstring(svg)
    return [(e.text or "").strip()
            for e in racine.iter("{http://www.w3.org/2000/svg}text")
            if (e.text or "").strip()]


# --- Non-regression du francais, valeurs relevees sur HEAD -----------------

_fr_tic = aifp.analyser(FR_TIC)
verifier("fr : empreinte IA, les trois signaux du texte a tics sont "
         "inchanges",
         _fr_tic["signaux"] == [
             "Variabilite de longueur faible (ecart-type 0.0), rythme "
             "uniforme.",
             "Ouvertures repetitives (100.0% commencent par « de »).",
             "Connecteurs suremployes (1.0 par phrase).",
         ], str(_fr_tic["signaux"]))

verifier("fr : empreinte IA, les six mesures chiffrees sont inchangees et "
         "la langue reste le francais sans option ni pragme",
         (_fr_tic["phrases"], _fr_tic["ecart_type_longueur"],
          _fr_tic["ouverture_max_pct"], _fr_tic["densite_connecteurs"],
          _fr_tic["densite_triples"], _fr_tic["amplificateurs"],
          _fr_tic["langue"])
         == (8, 0.0, 100.0, 1.0, 0.0, 0, "fr"),
         str(_fr_tic))

_fr_tri = aifp.analyser(FR_TRI)
verifier("fr : empreinte IA, bigramme et amplification contrastive "
         "inchanges, message francais",
         _fr_tri["bigramme_max"] == {"bigramme": "meme mesure", "compte": 4}
         and _fr_tri["signaux"][-1]
         == "Amplification contrastive (« non seulement ... mais ») x1.",
         str(_fr_tri["signaux"]))


_fr_prom = coh.analyser(FR_PROM)
verifier("fr : coherence, les promesses francaises sont inchangees",
         _fr_prom["promesses"] == ["Nous montrerons", "Nous y reviendrons"],
         str(_fr_prom["promesses"]))

_fr_temp = ctmp.analyser(FR_TEMP, date_reference=REF)
verifier("fr : temporel, les quatre constats attendus sont inchanges",
         [c["type"] for c in _fr_temp["constats"]]
         == ["futur-au-passe", "inversion-causale", "langage-peremption",
             "langage-peremption"],
         str([c["type"] for c in _fr_temp["constats"]]))

verifier("fr : figures, les SVG du schema PRISMA et du SWOT sont identiques "
         "a l'octet pres",
         (_sha(figs.construire("prisma", PRISMA_FR)),
          _sha(figs.construire("swot", SWOT)))
         == ("ebcafaa0e0776b6a5c9412e90cc1632d8b107390c1bd606bf144b69002a2d861",
             "8900d01302dd57acf431a8df4f8a61d4ad63c5986be4e42aabe4eade3d77e3d7"),
         "%s %s" % (_sha(figs.construire("prisma", PRISMA_FR)),
                    _sha(figs.construire("swot", SWOT))))


# --- Schema PRISMA en anglais ---------------------------------------------

_svg_en = figs.construire("prisma", PRISMA_EN, None, None, "en")
_txt_en = _textes(_svg_en)

verifier("prisma en : les libelles de boite sont ceux de PRISMA 2020",
         all(any(lab in t for t in _txt_en) for lab in (
             "Records identified", "Records removed before screening",
             "Records screened", "Records excluded",
             "Reports assessed for eligibility", "Reports excluded",
             "Studies included in review", "Study selection (PRISMA)",
             "(n = 435)")),
         str(_txt_en))

verifier("prisma en : les trois bandes de phase de PRISMA 2020, Eligibility "
         "ayant disparu depuis 2009",
         [t for t in _txt_en
          if t in ("Identification", "Screening", "Included", "Eligibility")]
         == ["Identification", "Screening", "Included"],
         str([t for t in _txt_en if len(t.split()) == 1]))

verifier("prisma en : la bande Screening couvre deux niveaux sans etre "
         "dessinee deux fois",
         _txt_en.count("Screening") == 1, str(_txt_en))

_MOTS_FR = ("References", "Doublons", "retires", "examinees", "resume",
            "ecartees", "ecartes", "Articles", "evalues", "texte",
            "integral", "Etudes", "incluses", "synthese", "Selection",
            "etudes", "Criblage", "Eligibilite", "Inclusion")
verifier("prisma en : aucun mot francais ne subsiste dans les elements de "
         "texte du SVG",
         not [m for m in _MOTS_FR for t in _txt_en if m in t.split()],
         str([m for m in _MOTS_FR for t in _txt_en if m in t.split()]))



# --- Autres figures strategiques en anglais -------------------------------

# Les activites principales de la chaine de valeur passent par
# l'enveloppement a 16 caracteres : leurs libelles arrivent coupes en
# morceaux, en anglais comme en francais (« - Logistique » puis
# « entrante »). Le cas lit donc aussi le SVG remis a plat.
_attendus_en = {
    "swot": (SWOT, {"Strengths", "Weaknesses", "Opportunities", "Threats"}),
    "bcg": ({"items": []}, {"Stars", "Question marks", "Cash cows", "Dogs",
                            "Market growth rate"}),
    "ansoff": ({}, {"Market penetration", "Product development",
                    "Market development", "Existing product"}),
    "pestel": ({}, {"Political", "Economic", "Technological", "Legal"}),
    "chaine-valeur": ({}, {"Support activities", "Primary activities",
                           "Margin", "Procurement", "Inbound logistics"}),
}
_manques = {}
for _type, (_data, _attendu) in sorted(_attendus_en.items()):
    _vus = _textes(figs.construire(_type, _data, None, None, "en"))
    _plat = " ".join(_vus).replace("- ", "")
    _absents = {a for a in _attendu if a not in _vus and a not in _plat}
    if _absents:
        _manques[_type] = sorted(_absents)
verifier("figures en : les cinq figures strategiques a etiquettes fixes "
         "portent leurs termes anglais",
         not _manques, str(_manques))


# --- Empreinte IA en anglais ----------------------------------------------

_en_tic = aifp.analyser(EN_TIC, "en")
verifier("en : les connecteurs anglais suremployes sont comptes, la ou les "
         "motifs francais en trouvaient zero",
         _en_tic["densite_connecteurs"] >= 1.0
         and any("Connecteurs suremployes" in s for s in _en_tic["signaux"])
         and aifp.analyser(EN_TIC, "fr")["densite_connecteurs"] == 0.0,
         str((_en_tic["densite_connecteurs"],
              aifp.analyser(EN_TIC, "fr")["densite_connecteurs"])))

_en_tri = aifp.analyser(EN_TRI, "en")
verifier("en : la cadence ternaire se lit sur and et or, pas sur et et ou",
         _en_tri["densite_triples"] > 0
         and aifp.analyser(EN_TRI, "fr")["densite_triples"] == 0.0,
         str((_en_tri["densite_triples"],
              aifp.analyser(EN_TRI, "fr")["densite_triples"])))

verifier("en : l'amplification contrastive anglaise est detectee et nommee "
         "dans sa langue",
         _en_tri["amplificateurs"] == 1
         and any("not only ... but" in s for s in _en_tri["signaux"]),
         str(_en_tri["signaux"]))

_bg_en = aifp.analyser(EN_PLAT, "en")["bigramme_max"]
_bg_fr = aifp.analyser(EN_PLAT, "fr")["bigramme_max"]
verifier("en : les mots outils anglais ne gonflent plus le bigramme repete",
         "the" not in _bg_en["bigramme"].split()
         and "of" not in _bg_en["bigramme"].split()
         and "the" in _bg_fr["bigramme"].split(),
         "en=%s fr=%s" % (_bg_en, _bg_fr))


# --- Coherence et verification temporelle en anglais ----------------------

verifier("en : coherence, les promesses de l'article anglais sont listees",
         coh.analyser(EN_PROM, "en")["promesses"]
         == ["We will show", "This section presents", "As discussed below"],
         str(coh.analyser(EN_PROM, "en")["promesses"]))

_en_temp = ctmp.analyser(EN_TEMP, date_reference=REF, langue="en")
verifier("en : temporel, date future au passe et inversion causale "
         "detectees",
         {"futur-au-passe", "inversion-causale"}
         <= {c["type"] for c in _en_temp["constats"]},
         str([c["type"] for c in _en_temp["constats"]]))

verifier("en : temporel, les deictiques anglais sont releves",
         sum(1 for c in _en_temp["constats"]
             if c["type"] == "langage-peremption") == 2,
         str([c["extrait"] for c in _en_temp["constats"]]))

_EN_BIB = ("Text.\n\n## References\n\n"
           "1. Doe J. Title. Preprint arXiv, 2024. Proceedings of the ACM "
           "symposium, 2020.\n")
verifier("en : temporel, un preprint date apres sa version publiee est vu "
         "sur un marqueur anglais",
         any(c["type"] == "chaine-incoherente"
             for c in ctmp.analyser(_EN_BIB, date_reference=REF,
                                    langue="en")["constats"]),
         str(ctmp.analyser(_EN_BIB, date_reference=REF,
                           langue="en")["constats"]))


# --- Routage par le pragme du document ------------------------------------

_PRAGME = ("<!-- lint-style:langue=en -->\n\n" + EN_PROM)
verifier("pragme : un document declare en anglais bascule les detecteurs "
         "sans qu'aucune option soit passee",
         coh.analyser(_PRAGME)["langue"] == "en"
         and aifp.analyser(_PRAGME)["langue"] == "en"
         and ctmp.analyser(_PRAGME)["langue"] == "en",
         str((coh.analyser(_PRAGME)["langue"],
              aifp.analyser(_PRAGME)["langue"],
              ctmp.analyser(_PRAGME)["langue"])))


# --- Cas negatifs : ce que le mode anglais ne doit PAS declencher ---------

EN_SOBRE = ("The calibration curve was measured on three independent "
            "samples. Concentrations ranged from 0.2 to 4.8 milligrams per "
            "litre, with a median of 1.1. Two outliers were excluded after "
            "visual inspection of the residual plot, and the reason is "
            "recorded in the supplementary material. The remaining series "
            "follow the reference line within the stated uncertainty.")
verifier("neg en : une methode sobre ne declenche aucun signal d'empreinte",
         aifp.analyser(EN_SOBRE, "en")["signaux"] == [],
         str(aifp.analyser(EN_SOBRE, "en")["signaux"]))

EN_ANCRE = ("The latest release, dated March 2024, is stable. As of "
            "September 2025 the most recent revision adds two endpoints.")
verifier("neg en : un deictique ancre par un mois anglais ne leve rien",
         not [c for c in ctmp.analyser(EN_ANCRE, date_reference=REF,
                                       langue="en")["constats"]
              if c["type"] == "langage-peremption"],
         str(ctmp.analyser(EN_ANCRE, date_reference=REF,
                           langue="en")["constats"]))

verifier("neg en : un texte sans annonce ne fabrique aucune promesse",
         coh.analyser(EN_SOBRE, "en")["promesses"] == [],
         str(coh.analyser(EN_SOBRE, "en")["promesses"]))

verifier("neg en : une chronologie saine ne leve ni date future ni "
         "inversion causale",
         not [c for c in ctmp.analyser(
             "The 2018 reform led to the 2022 growth measured last year.",
             date_reference=REF, langue="en")["constats"]
             if c["type"] in ("futur-au-passe", "inversion-causale")],
         str(ctmp.analyser(
             "The 2018 reform led to the 2022 growth measured last year.",
             date_reference=REF, langue="en")["constats"]))

verifier("neg fr : un texte francais soigne ne compte aucun connecteur "
         "anglais",
         aifp.analyser("Le protocole tient sur trois series datees. La "
                       "mesure porte sur cinq echantillons.")["signaux"]
         == [], "les motifs anglais ne doivent pas fuir dans le mode fr")

verifier("neg : une langue inconnue rend la figure en francais plutot que "
         "d'interrompre le rendu",
         _sha(figs.construire("prisma", PRISMA_FR, None, None, "de"))
         == _sha(figs.construire("prisma", PRISMA_FR, None, None, "fr")))

# Le module rend la langue au francais : les autres modules de cas chargent
# leur propre instance de figures.py, mais un etat de module laisse en
# anglais serait un piege pour toute lecture ulterieure de celle-ci.
figs.appliquer_langue("fr")
