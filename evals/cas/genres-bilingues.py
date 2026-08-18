# -*- coding: utf-8 -*-
"""Les playbooks de genre tiennent-ils face au bilinguisme ?

Un audit des vingt-six playbooks a montre que la structure d'un genre n'est
pas toujours portable d'une langue a l'autre. Trois cas coexistent : la
structure vaut telle quelle (UNIVERSEL), le genre existe des deux cotes avec
des attentes differentes (VARIANTE), le genre n'a pas de correspondant
(PROPRE A UNE LANGUE). La reponse retenue est un fichier transverse,
references/genres-anglais.md, charge EN PLUS du playbook du genre pour un
document anglais, sur le modele deja en place du couple style.md et
style-anglais.md.

Ce module verrouille quatre choses.

Le classement des vingt-six genres existe dans le depot, sous forme lisible,
et couvre les vingt-six sans en oublier ni en inventer. Un classement absent
ou partiel rendrait le fichier inutilisable comme point d'entree.

Chaque genre traite porte ce qu'il annonce. Un playbook qui renvoie vers le
fichier transverse doit y avoir une contrepartie, et le fichier transverse ne
doit pas promettre une section qu'il n'ecrit pas.

Les deux genres declares sans equivalent le disent explicitement, dans leur
propre playbook et pas seulement dans le fichier transverse : un auteur qui
charge genre-dissertation.md sans charger genres-anglais.md doit malgre tout
lire que le genre n'a pas de correspondant anglais.

Aucun renvoi n'est casse, et les routeurs sont a jour. langue.md affirmait
que les playbooks etaient monolingues sans exception : cette affirmation est
devenue fausse, le module garde la correction.
"""
import os
import re

PLUGIN = os.path.join(RACINE, "scriptorium")
REFS = os.path.join(PLUGIN, "skills", "produire", "references")
TRANSVERSE = os.path.join(REFS, "genres-anglais.md")
lint_g = charger("lint-style.py", "lint_style_genres")


def _lire(chemin):
    return open(chemin, encoding="utf-8").read()


_genres = sorted(os.path.basename(p)[:-3] for p in
                 [os.path.join(REFS, n) for n in os.listdir(REFS)]
                 if os.path.basename(p).startswith("genre-")
                 and p.endswith(".md"))

verifier("genres : le depot en compte toujours vingt-six",
         len(_genres) == 26, "n=%d" % len(_genres))

verifier("genres-anglais.md existe", os.path.isfile(TRANSVERSE))
_tr = _lire(TRANSVERSE) if os.path.isfile(TRANSVERSE) else ""

# --- 1. Le classement des vingt-six genres est present et complet ----------
# Il vit dans un tableau markdown de genres-anglais.md, une ligne par
# playbook. Le tableau est la forme lisible exigee : un lecteur y trouve la
# categorie sans derouler le fichier entier.
CATEGORIES = ("UNIVERSEL", "VARIANTE", "PROPRE")
_LIGNE = re.compile(r"^\| (genre-[a-z-]+) \| (UNIVERSEL|VARIANTE|PROPRE) \| (.+?) \|$",
                    re.MULTILINE)
_classement = {m.group(1): (m.group(2), m.group(3)) for m in _LIGNE.finditer(_tr)}

verifier("classement : les vingt-six genres y figurent",
         set(_classement) == set(_genres),
         "manquants=%s intrus=%s" % (sorted(set(_genres) - set(_classement)),
                                     sorted(set(_classement) - set(_genres))))

verifier("classement : chaque ligne porte une categorie connue",
         _classement and all(v[0] in CATEGORIES for v in _classement.values()))

verifier("classement : chaque ligne justifie, elle ne se contente pas de classer",
         _classement and all(len(v[1]) >= 40 for v in _classement.values()),
         "trop courtes=%s" % sorted(k for k, v in _classement.items()
                                    if len(v[1]) < 40))

# Les trois categories sont reellement employees. Un classement qui rangerait
# tout en UNIVERSEL serait une non-reponse deguisee en reponse.
_par_cat = {c: sorted(k for k, v in _classement.items() if v[0] == c)
            for c in CATEGORIES}
for _c in CATEGORIES:
    verifier("classement : la categorie %s n'est pas vide" % _c,
             len(_par_cat[_c]) >= 2, "n=%d" % len(_par_cat[_c]))

# Les deux cas nommes par l'audit sont bien ceux qui n'ont pas d'equivalent.
verifier("classement : dissertation est declaree sans equivalent",
         _classement.get("genre-dissertation", ("",))[0] == "PROPRE",
         str(_classement.get("genre-dissertation")))
verifier("classement : conclusions-contentieux est declaree sans equivalent",
         _classement.get("genre-conclusions-contentieux", ("",))[0] == "PROPRE",
         str(_classement.get("genre-conclusions-contentieux")))
# note-juridique porte l'IRAC, universel, sous un vocabulaire de procedure
# francais : c'est une variante, pas un genre sans equivalent.
verifier("classement : note-juridique est une variante, pas un cas sans equivalent",
         _classement.get("genre-note-juridique", ("",))[0] == "VARIANTE",
         str(_classement.get("genre-note-juridique")))

# --- 2. Les six genres scientifiques sont reellement traites --------------
# Ils sont prioritaires parce qu'ils servent. Un renvoi sans contenu serait
# pire qu'une absence : il promettrait une reponse.
SCIENTIFIQUES = ("rapport-scientifique", "article", "revue-litterature",
                 "demande-financement", "poster", "presentation")
# Contenus dont l'audit exige la presence, sous une forme ou une autre.
ATTENDUS = {
    "IMRAD variable selon la revue": ("IMRAD", "IEEE", "Nature", "ICMJE"),
    "temps verbaux par section": ("Methods", "Results", "Discussion", "passé"),
    "abstract, place et forme": ("abstract", "structuré", "250", "200"),
    "mots-cles": ("Thesaurus", "MeSH"),
    "disponibilite des donnees": ("disponibilite.md", "identifiant pérenne"),
    "premiere personne": ("Here we show", "style-anglais.md"),
    "longueur attendue": ("2 500", "4 300", "3 000"),
    "revue de litterature nommee": ("systematic review", "scoping review",
                                    "PROSPERO"),
    "demande de financement": ("Broader Impacts", "Specific Aims"),
    "poster": ("conference abstract",),
    "presentation": ("viva", "defense"),
}
for _etiq, _jetons in ATTENDUS.items():
    _absents = [j for j in _jetons if j not in _tr]
    verifier("genres-anglais.md traite : %s" % _etiq, not _absents,
             "absents=%s" % _absents)

# Chaque genre scientifique renvoie vers le fichier transverse depuis son
# propre playbook : sans ce renvoi, le routeur seul porte la connexion et un
# lecteur qui ouvre le playbook directement ne saura pas que le fichier existe.
for _n in SCIENTIFIQUES:
    _chemin = os.path.join(REFS, "genre-%s.md" % _n)
    if _n == "revue-litterature":
        _chemin = os.path.join(REFS, "revue-litterature.md")
        continue  # la methode de synthese est deja anglophone, traitee en transverse
    verifier("playbook %s : renvoie vers genres-anglais.md" % _n,
             "genres-anglais.md" in _lire(_chemin))

# Le fichier transverse ne repete pas les regles de forme : elles vivent dans
# style-anglais.md, un seul endroit. Garde anti-duplication.
verifier("genres-anglais.md delegue la forme a style-anglais.md",
         "style-anglais.md" in _tr)

# --- 3. Les genres sans equivalent le disent, chez eux --------------------
# L'honnetete prime sur la traduction : le playbook nomme le genre anglais le
# plus proche et ce qui l'en separe, plutot que de laisser croire a une
# equivalence. Ce cas garde la formulation dans le playbook LUI-MEME, pas
# seulement dans le fichier transverse : un auteur peut ouvrir le playbook
# sans charger genres-anglais.md.
SANS_EQUIVALENT = {
    "genre-dissertation": ("academic essay", "thesis statement"),
    "genre-conclusions-contentieux": ("Standard of Review", "Prayer for Relief"),
}
for _n, _proches in SANS_EQUIVALENT.items():
    _t = _lire(os.path.join(REFS, "%s.md" % _n))
    verifier("%s : le playbook declare l'absence d'equivalent" % _n,
             "pas d'équivalent" in _t or "un autre écrit" in _t)
    verifier("%s : le playbook nomme le genre anglais le plus proche" % _n,
             all(p in _t for p in _proches),
             "absents=%s" % [p for p in _proches if p not in _t])
    verifier("%s : le playbook renvoie au fichier transverse" % _n,
             "genres-anglais.md" in _t)

# Le fichier transverse refuse explicitement de fabriquer une equivalence.
verifier("genres-anglais.md refuse d'inventer une equivalence",
         "Il ne fabrique pas d'équivalence." in _tr)

# --- 4. Les routeurs sont a jour ------------------------------------------
_skill = _lire(os.path.join(PLUGIN, "skills", "produire", "SKILL.md"))
verifier("routeur produire : l'action genre charge le fichier transverse "
         "pour un document anglais",
         "genres-anglais.md" in _skill)
verifier("routeur produire : le chargement reste conditionnel a l'anglais",
         "Un document en français ne le charge pas." in _skill)

_lang = _lire(os.path.join(REFS, "langue.md"))
verifier("langue.md : ne dit plus que les playbooks sont monolingues sans "
         "exception", "ce lot ne les traduit pas" not in _lang)
verifier("langue.md : nomme le fichier transverse",
         "genres-anglais.md" in _lang)
verifier("langue.md : rappelle que ce n'est pas une traduction",
         "traduction" in _lang.split("## Le hook")[0])

# --- 5. Aucun renvoi casse -----------------------------------------------
# Tout `references/x.md` ou `x.md` cite par le fichier transverse doit
# exister. Le premier lot d'anglais avait laisse passer un renvoi fantome
# dans une autre reference : la garde est mecanique, pas de relecture.
_RENVOI = re.compile(r"`(?:references/)?([a-z0-9-]+\.md)`")
_cites = sorted(set(_RENVOI.findall(_tr)))
_manquants = [c for c in _cites
              if not os.path.isfile(os.path.join(REFS, c))
              and not os.path.isfile(os.path.join(
                  PLUGIN, "skills", "atelier", "references", c))]
verifier("genres-anglais.md : aucun renvoi casse", not _manquants,
         "cites=%d manquants=%s" % (len(_cites), _manquants))
verifier("genres-anglais.md : il cite au moins cinq references du plugin",
         len(_cites) >= 5, "n=%d" % len(_cites))

# Les URL de la section Sources sont propres : ni parametre de suivi, ni
# schema absent. Meme exigence que les playbooks existants.
_SOURCES = _tr.split("## Sources")[-1].split("## Voir aussi")[0]
_urls = re.findall(r"https?://\S+", _SOURCES)
verifier("genres-anglais.md : la section Sources porte au moins dix sources",
         len(_urls) >= 10, "n=%d" % len(_urls))
verifier("genres-anglais.md : aucune URL de source ne porte de parametre utm",
         not [u for u in _urls if "utm_" in u])
verifier("genres-anglais.md : toutes les URL de source sont en https",
         all(u.startswith("https://") for u in _urls),
         "http simple=%s" % [u for u in _urls if not u.startswith("https://")])

# --- 6. Le fichier transverse reste du francais qui cite de l'anglais -----
# Meme discipline que les descriptions de declencheurs : le corps est
# francais et passe le linter FRANCAIS. Les termes anglais cites (thesis
# statement, Standard of Review, Broader Impacts) ne doivent reveiller
# aucune regle francaise.
_constats = lint_g.lint_text(_tr)
_crit = sorted({c["regle"] for c in _constats if c["severite"] == "critique"})
_maj = sorted({c["regle"] for c in _constats if c["severite"] == "majeur"})
verifier("genres-anglais.md : aucun constat critique au linter francais",
         not _crit, "regles=%s" % _crit)
verifier("genres-anglais.md : aucun constat majeur au linter francais",
         not _maj, "regles=%s" % _maj)

# La justification de la forme retenue est ecrite, pas seulement appliquee :
# le choix entre vingt-six fichiers, une section par playbook et un fichier
# transverse doit rester lisible pour qui reprendra le lot.
verifier("genres-anglais.md : la forme retenue est justifiee dans le fichier",
         "Pourquoi un fichier et non vingt-six" in _tr)
