# -*- coding: utf-8 -*-
"""Les declencheurs des competences et des agents tiennent-ils dans les DEUX
langues ?

C'est la description du frontmatter, et elle seule, qui decide si un modele
choisit une competence ou delegue a un agent quand l'utilisateur formule sa
demande. Une description entierement francaise n'interdit rien a un
anglophone, elle degrade son signal : l'appariement se fait entre une phrase
anglaise et un texte francais. Ce module verrouille l'etat bilingue de ces
neuf descriptions.

Trois exigences, dans cet ordre.

Les deux langues sont reellement presentes. Les tournures citees entre
guillemets sont extraites puis classees par mots outils : une competence porte
au moins six declencheurs de chaque langue, un agent au moins trois.

La croissance reste bornee. Une description sans plafond finit par tout
contenir et ne discrimine plus rien. Le harnais n'avait aucune contrainte de
longueur : elle est posee ici, au-dessus de l'etat courant, comme garde
anti-derive et non comme limite de plateforme.

Le frontmatter reste lisible. Il est reparse par un analyseur minimal, sans
dependance externe (PyYAML n'est installe nulle part dans ce depot), et les
neuf fichiers repassent au linter de style : les declencheurs anglais ajoutes
sont analyses avec les regles FRANCAISES, puisque ces fichiers sont du francais
qui cite de l'anglais, et un mot comme « crucial » ou « pivotal » y serait un
constat critique.

Ce module complete le lint de prompt de run-evals.py (existence des references
citees, presence des cles du frontmatter, chemins de competence perimes) sans
le repeter.
"""
import glob
import os
import re

PLUGIN = os.path.join(RACINE, "scriptorium")
lint_d = charger("lint-style.py", "lint_style_declencheurs")

# Plafonds de longueur de description, en caracteres. Poses au-dessus de
# l'etat courant (2243 pour produire, 1790 pour synthese-sources) avec une
# marge de l'ordre de dix pour cent : de quoi ajouter un declencheur, pas de
# quoi doubler la description sans s'en apercevoir.
PLAFOND_SKILL = 2500
PLAFOND_AGENT = 2000

# Seuils de declencheurs par langue.
MIN_SKILL = 6
MIN_AGENT = 3

# Mots outils qui tranchent la langue d'une tournure courte. Les listes de
# lint-style.py ne conviennent pas ici : elles sont calibrees sur un texte
# entier et ecartent volontairement les homographes, ce qui laisse un
# declencheur de quatre mots sans aucun marqueur. Le francais l'emporte quand
# les deux familles apparaissent, parce qu'un mot comme « a » est francais
# dans « rediger de A a Z » et anglais dans « write a report ».
MARQUEURS_FR = frozenset("""le la les un une des du de mon ma mes ce cet cette
ces qui que qu est sont dans pour en avec sur par plus ou au aux je il elle ne
pas moi nous vous quel quelle si son sa ses leur tout tous fais""".split())
MARQUEURS_EN = frozenset("""the a an my me this these that it is are does do
did what for to from into and of in up off before against i we our us you your
still say says out right be been was were get with about""".split())

_ACCENT = re.compile(r"[àâäçéèêëîïôöùûüÿœæ]", re.I)
_CITATION = re.compile(r'"([^"\n]{3,160})"')
_MOT = re.compile(r"[a-zà-ÿ']+", re.I)


def _langue_declencheur(tournure):
    """Rend 'fr', 'en' ou None. None n'est pas un echec : une tournure comme
    « literature review » ou « version courte » ne porte aucun mot outil et ne
    compte simplement pour aucune des deux langues."""
    mots = {m.lower().strip("'") for m in _MOT.findall(tournure)}
    if _ACCENT.search(tournure) or (mots & MARQUEURS_FR):
        return "fr"
    if mots & MARQUEURS_EN:
        return "en"
    return None


def _frontmatter(texte):
    """Extrait le bloc entre les deux delimiteurs, ou None."""
    if not texte.startswith("---\n"):
        return None
    fin = texte.find("\n---\n", 3)
    if fin < 0:
        return None
    return texte[4:fin + 1], texte[fin + 5:]


_CLE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):\s?(.*)$")


def _cles(bloc):
    """Analyseur minimal du frontmatter : cles de premier niveau, valeurs
    repliees. Suffisant pour ce que le harnais doit garantir (les cles
    attendues sont la, rien ne casse la structure) et sans dependance
    externe. Rend None des qu'une ligne de premier niveau n'est pas une cle,
    ce qui est exactement le symptome d'un frontmatter casse."""
    valeurs, courante = {}, None
    for ligne in bloc.splitlines():
        if not ligne.strip():
            continue
        if ligne[0] in " \t":
            if courante is None:
                return None
            valeurs[courante] = (valeurs[courante] + "\n" + ligne.strip()).strip()
            continue
        if ligne.lstrip().startswith("#"):
            continue
        m = _CLE.match(ligne)
        if not m:
            return None
        courante = m.group(1)
        valeurs[courante] = m.group(2).strip()
    for cle, val in list(valeurs.items()):
        if val.startswith(">") or val.startswith("|"):
            valeurs[cle] = val[1:].lstrip("-+").strip()
    return valeurs


FICHIERS = [("skill", p) for p in
            sorted(glob.glob(os.path.join(PLUGIN, "skills", "*", "SKILL.md")))]
FICHIERS += [("agent", p) for p in
             sorted(glob.glob(os.path.join(PLUGIN, "agents", "*.md")))]

verifier("declencheurs : les neuf fichiers a description sont vus",
         len([1 for k, _ in FICHIERS if k == "skill"]) == 4
         and len([1 for k, _ in FICHIERS if k == "agent"]) == 5,
         f"n={len(FICHIERS)}")


for _genre, _chemin in FICHIERS:
    _nom = os.path.basename(_chemin)
    if _genre == "skill":
        _nom = os.path.basename(os.path.dirname(_chemin))
        _attendu, _plafond, _mini = _nom, PLAFOND_SKILL, MIN_SKILL
    else:
        _nom = _nom[:-3]
        _attendu, _plafond, _mini = _nom, PLAFOND_AGENT, MIN_AGENT
    _etiq = "%s %s" % (_genre, _nom)

    _texte = open(_chemin, encoding="utf-8").read()
    _decoupe = _frontmatter(_texte)
    verifier("%s : frontmatter delimite par deux ---" % _etiq,
             _decoupe is not None)
    _bloc, _corps = _decoupe if _decoupe else ("", "")
    _fm = _cles(_bloc) if _decoupe else None
    verifier("%s : frontmatter reparse, avec name et description" % _etiq,
             bool(_fm) and _fm.get("name") == _attendu and _fm.get("description"),
             f"cles={sorted(_fm) if _fm else None}")

    _desc = (_fm or {}).get("description", "")
    _tournures = _CITATION.findall(_desc)
    _fr = [t for t in _tournures if _langue_declencheur(t) == "fr"]
    _en = [t for t in _tournures if _langue_declencheur(t) == "en"]
    verifier("%s : au moins %d declencheurs francais cites" % (_etiq, _mini),
             len(_fr) >= _mini, f"n={len(_fr)} sur {len(_tournures)} citations")
    verifier("%s : au moins %d declencheurs anglais cites" % (_etiq, _mini),
             len(_en) >= _mini, f"n={len(_en)} sur {len(_tournures)} citations")

    verifier("%s : description sous le plafond de %d caracteres"
             % (_etiq, _plafond), len(_desc) <= _plafond, f"len={len(_desc)}")

    # Le linter tourne sur la DESCRIPTION seule, pas sur le fichier entier.
    # Le corps de controle-qualite enumere le lexique banni pour le faire
    # appliquer (« pivotal, crucial, emblematique ») et declenche donc la
    # regle qu'il enseigne : un constat legitime, hors sujet ici. Ce qui est
    # garde, c'est que les declencheurs anglais ajoutes a la description ne
    # reveillent aucune regle francaise, tiret cadratin et typographie courbe
    # comprises.
    _crit = sorted({c["regle"] for c in lint_d.lint_text(_desc)
                    if c["severite"] == "critique"})
    verifier("%s : aucun constat critique dans la description" % _etiq,
             not _crit, f"regles={_crit}")


# --- La langue de travail, ecrite dans les routeurs ------------------------
# La regle retenue : la langue de la CONVERSATION ne determine pas la langue
# du DOCUMENT. Un francophone commande un article en anglais, un anglophone
# commande un rapport en francais. La langue du document se fixe au cadrage,
# explicitement, puis se propage par le pragme et par --langue. Un routeur qui
# la deduirait de la langue de la demande basculerait un rapport francais en
# anglais sur une seule question posee en anglais. Ces cas verrouillent la
# presence de la regle dans le corps des quatre routeurs, pas seulement dans
# leur description.
ROUTEURS = ("atelier", "produire", "controler", "livrer")
# Les trois routeurs qui peuvent avoir a trancher : ils POSENT la question
# plutot que de retomber en silence sur le francais. livrer n'y figure pas,
# il herite de la langue du document deja valide.
POSENT_LA_QUESTION = ("atelier", "produire", "controler")

for _nom in ROUTEURS:
    _t = open(os.path.join(PLUGIN, "skills", _nom, "SKILL.md"),
              encoding="utf-8").read()
    _decoupe = _frontmatter(_t)
    _corps = _decoupe[1] if _decoupe else ""
    verifier("routeur %s : le corps separe langue du document et langue de la "
             "conversation" % _nom, "langue de la conversation" in _corps)
    verifier("routeur %s : le corps renvoie a la reference de langue" % _nom,
             "langue.md" in _corps)

for _nom in POSENT_LA_QUESTION:
    _t = open(os.path.join(PLUGIN, "skills", _nom, "SKILL.md"),
              encoding="utf-8").read()
    _corps = _frontmatter(_t)[1]
    verifier("routeur %s : la langue absente se demande, elle ne se suppose "
             "pas" % _nom, "question fermée" in _corps)
