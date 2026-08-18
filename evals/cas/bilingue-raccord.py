"""Le scorecard transmet-il la langue a TOUTES les mesures qui en dependent ?

Une langue resolue mais non transmise est le defaut le plus discret de cette
famille : la mesure existe, elle est juste, et elle n'est jamais appelee avec
le bon jeu de motifs. Le symptome n'est pas une erreur, c'est une note fausse.
Ces cas verrouillent la chaine complete plutot que chaque script pris a part.
"""
import inspect

sc_r = charger("scorecard.py", "scorecard_raccord")
lint_r = charger("lint-style.py", "lint_raccord")

_SOURCE = inspect.getsource(sc_r.evaluer)

# Chaque mesure dependante de la langue doit la recevoir, litteralement.
_ATTENDUS = [
    ("lint_text", "regles de style"),
    ("aifp.analyser", "empreinte IA"),
    ("coh.analyser", "coherence et promesses"),
    ("trac.analyser", "tracabilite et objets numerotes"),
    ("nums.analyser", "conventions de nombres"),
    ("read.mesurer", "lisibilite et passif"),
]
for appel, quoi in _ATTENDUS:
    _i = _SOURCE.find(appel)
    _extrait = _SOURCE[_i:_i + 120] if _i >= 0 else ""
    verifier("raccord : la langue atteint %s" % quoi,
             _i >= 0 and "langue" in _extrait,
             f"appel={appel} extrait={_extrait[:80]!r}")

verifier("raccord : la langue est resolue une seule fois",
         _SOURCE.count("resoudre_langue") == 1,
         f"n={_SOURCE.count('resoudre_langue')}")

# Un texte anglais au passif dense doit etre note comme tel des lors que la
# langue est declaree, et non plus recevoir les motifs francais.
_EN = ("The corpus was collected on three sites and the model was trained on "
       "a held-out split. Moreover, the effect was significant in every "
       "setting. Furthermore, results were measured on the validation set. "
       "However, the analysis was limited by sample size. ") * 4

_fr = sc_r.evaluer(_EN, langue="fr")
_en = sc_r.evaluer(_EN, langue="en")
verifier("raccord : la langue declaree change reellement la note",
         _fr["total"] != _en["total"] or
         _fr["axes"]["Style"]["score"] != _en["axes"]["Style"]["score"],
         f"fr={_fr['total']} en={_en['total']}")
verifier("raccord : la langue retenue est rapportee dans le resultat",
         _en.get("langue") == "en" and _fr.get("langue") == "fr",
         f"fr={_fr.get('langue')} en={_en.get('langue')}")
verifier("raccord : le pronom francais ne mord pas sur la preposition anglaise",
         not any("mineur" in d and "18" in d
                 for d in _en["axes"]["Style"]["deductions"]),
         f"d={_en['axes']['Style']['deductions']}")

# Le pragme du document suffit : la notation n'a pas besoin qu'on lui dise.
_avec_pragme = "<!-- lint-style:langue=en -->\n" + _EN
verifier("raccord : le pragme du document est honore par la notation",
         sc_r.evaluer(_avec_pragme)["langue"] == "en",
         f"vu={sc_r.evaluer(_avec_pragme).get('langue')}")

# Non-regression : un texte francais garde exactement sa note.
_FR = ("Le corpus a été collecté sur trois sites et le modèle a été entraîné "
       "sur un jeu réservé. De plus, l'effet est net dans chaque situation. "
       "En outre, les résultats ont été mesurés sur le jeu de validation. ") * 4
_a = sc_r.evaluer(_FR)
_b = sc_r.evaluer(_FR, langue="fr")
verifier("raccord : le francais explicite et le francais par defaut coincident",
         _a["total"] == _b["total"] and _a["axes"] == _b["axes"],
         f"a={_a['total']} b={_b['total']}")
