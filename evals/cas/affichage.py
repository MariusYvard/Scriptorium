# -*- coding: utf-8 -*-
"""Cas d'eval de la couche d'affichage bilingue (scriptorium/scripts/libelles.py).

Trois exigences dominent, dans cet ordre.

La non-regression du francais. Les empreintes gelees plus bas ont ete relevees
sur la version HEAD des six scripts, avant toute modification, puis
recomparees apres cablage : les douze mesures etaient identiques. Les figer en
litteral fait echouer ce module si une sortie francaise bouge, au lieu de
suivre la derive en silence.

La stabilite des valeurs machine. Un verdict, une decision, un nom d'axe, un
nom de regle et une severite restent les chaines francaises actuelles meme
quand l'affichage passe a l'anglais : emprunts.py branche sur les verdicts,
plusieurs modules de evals/cas/ les comparent litteralement, tools/gold.py les
confronte aux etiquettes gelees de evals/gold/*/manifeste.json.

L'absence de francais residuel dans un rapport anglais, verifiee mot a mot sur
les rapports reellement produits, et une garde qui attrape une chaine
d'affichage non cablee dans les scripts deja traites.
"""
import ast
import contextlib
import hashlib
import inspect
import io
import json
import os

lib = charger("libelles.py", "libelles_aff")
lint_a = charger("lint-style.py", "lint_style_aff")
score_a = charger("scorecard.py", "scorecard_aff")
read_a = charger("readability.py", "readability_aff")
trac_a = charger("traceability.py", "traceability_aff")
vsrc_a = charger("verify-sources.py", "verify_sources_aff")
audit_a = charger("audit-doc.py", "audit_doc_aff")


# --- La garde : une chaine d'affichage francaise non cablee ------------------
# Heuristique volontairement etroite. Elle lit l'arbre syntaxique, pas le
# texte : un commentaire n'y figure pas du tout, et une docstring est une
# instruction d'expression, jamais un argument d'appel. Les deux sont donc
# hors d'atteinte par construction, pas par liste d'exceptions.
#
# Est signalee une chaine litterale qui reunit trois conditions : elle
# ressemble a du francais, elle se trouve dans une fonction qui produit de
# l'affichage, et elle occupe une position d'affichage (argument de print, de
# write, de .append ou .extend, ou element ajoute a une liste).
#
# Trois exclusions evitent les faux positifs sur les valeurs machine, qui
# restent francaises a dessein : une cle de dictionnaire, une cle
# d'indexation (d["doublons"]) et l'argument d'un .get() ne sont jamais
# affiches, ils designent. Une chaine produite par lib.t(), lib.valeur() ou
# lib.motif() est deja cablee : le sous-arbre de ces appels n'est pas visite.

APPELS_AFFICHAGE = ("print", "write", "append", "extend")
APPELS_CABLES = ("t", "valeur", "motif")
# Appels dont les arguments sont des cles, jamais du texte a lire.
APPELS_DE_CLE = ("get", "startswith", "endswith", "count", "split",
                 "setdefault", "pop")
# Fonctions qui produisent de l'affichage. Hors d'elles, une chaine francaise
# est une valeur machine ou une donnee, pas un libelle.
FONCTIONS_AFFICHAGE = ("rapport_texte", "rapport_trajectoire_texte",
                       "problemes", "interpreter", "main")

ACCENTS_FR = set("àâäçéèêëîïôöùûüÀÂÄÇÉÈÊËÎÏÔÖÙÛÜœŒ«»")

# Mots francais frequents dans les rapports du plugin et qui n'existent pas
# en anglais. Les mots communs aux deux langues sont volontairement absents :
# part, force, index, section, style, table, note, source, decision, passive,
# plus, phrases, references, suite, declare, premier, commence, axe, axes,
# vague, linter, par, citations, preprints, contamination, critiques,
# monotone, deductions. Chacun fabriquerait un faux positif a chaque rapport
# anglais correct. La liste vise a n'avoir aucun faux positif, quitte a
# laisser passer un mot rare : la garde signale, elle ne juge pas.
MOTS_FR = frozenset("""le la les des du une dans pour que qui est sont avec
aux nous mais aussi ainsi sans alors donc dont entre leur leurs cette ces sur
aucun aucune chaque hors jamais tous sous trop deja etre ete
langue langues notee analysee mesuree tracabilite lisibilite
metriques verificateur doublons paliers domaine reseau suivi empreinte redite
numerotes numerote biblio presente presentes repartition evalue
evaluee evalues faite faites egalite atteint numeros
numero melangee chiffres lettres saut formes casse conforme ecart ecarts
majeur majeurs mineur mineurs maison detecte nettoyer
invalides syntaxe douteuse statut retractation inconnu signaux
recents annee estimee consulte verifie fabrique inverifiable
penalites plafonnees ponderee somme plancher editoriale pendantes orphelines
appelees appeles definies definis tableaux probleme problemes
calcul faiblesse faiblesses seuil sigle pourcentage
incoherente separateur mixte rythme longues densite lexicale faible
passif effondre effondres tirets cadratin courbe promotionnel banni bannie
retirer reformuler verbe pronom quantificateur chiffrer""".split())

_MOT_RE = __import__("re").compile(r"[A-Za-zÀ-ÿ']+")


def _ressemble_au_francais(texte):
    """Une chaine ressemble au francais si elle porte un signe diacritique du
    francais ou un mot de MOTS_FR."""
    if any(c in ACCENTS_FR for c in texte):
        return True
    return any(m.lower() in MOTS_FR for m in _MOT_RE.findall(texte))


def _est_appel_cable(noeud):
    f = getattr(noeud, "func", None)
    nom = getattr(f, "attr", None) or getattr(f, "id", None)
    return nom in APPELS_CABLES


def _chaines_visibles(noeud):
    """Chaines litterales reellement affichees dans ce sous-arbre.

    Les champs d'une f-string sont des expressions, pas des constantes : ils
    ne sont jamais rapportes ici. Les cles de dictionnaire, les cles
    d'indexation et les arguments d'un appel de cle sont ecartes : ce sont des
    valeurs machine, elles restent francaises a dessein."""
    if isinstance(noeud, ast.Constant):
        return [noeud] if isinstance(noeud.value, str) else []
    if isinstance(noeud, ast.Call):
        if _est_appel_cable(noeud):
            return []
        if getattr(noeud.func, "attr", None) in APPELS_DE_CLE:
            return _chaines_visibles(noeud.func)
        sous = list(noeud.args) + [k.value for k in noeud.keywords]
        sous.append(noeud.func)
        return [c for s in sous for c in _chaines_visibles(s)]
    if isinstance(noeud, ast.Subscript):
        return _chaines_visibles(noeud.value)
    if isinstance(noeud, ast.Dict):
        return [c for v in noeud.values for c in _chaines_visibles(v)]
    if isinstance(noeud, ast.Attribute):
        return _chaines_visibles(noeud.value)
    return [c for e in ast.iter_child_nodes(noeud)
            for c in _chaines_visibles(e)]


def _positions_d_affichage(fonction):
    """Expressions imprimees ou accumulees dans un rapport, dans cette
    fonction."""
    cibles = []
    for noeud in ast.walk(fonction):
        if isinstance(noeud, ast.Call):
            nom = (getattr(noeud.func, "attr", None)
                   or getattr(noeud.func, "id", None))
            if nom in APPELS_AFFICHAGE and not _est_appel_cable(noeud):
                cibles.extend(noeud.args)
        elif (isinstance(noeud, ast.AugAssign)
              and isinstance(noeud.op, ast.Add)):
            cibles.append(noeud.value)
    return cibles


def constats_non_cables(chemin):
    """Chaines d'affichage francaises non cablees dans ce fichier.

    Rend une liste de (numero de ligne, chaine tronquee). Une liste vide
    signifie que tout ce qui s'imprime dans ce fichier passe par la couche de
    libelles."""
    with open(chemin, encoding="utf-8") as f:
        arbre = ast.parse(f.read(), chemin)
    suspects = []
    for noeud in ast.walk(arbre):
        if not isinstance(noeud, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if noeud.name not in FONCTIONS_AFFICHAGE:
            continue
        for cible in _positions_d_affichage(noeud):
            for c in _chaines_visibles(cible):
                if _ressemble_au_francais(c.value):
                    suspects.append((c.lineno, c.value[:60]))
    return sorted(set(suspects))


# --- Les cas ----------------------------------------------------------------

MAUVAIS = lire("style-mauvais.md")
PROPRE = lire("style-propre.md")
SALES = lire("sources-sales.md")
LACUNES = lire("lacunes-tagguees.md")
ANGLAIS = lire("rapport-anglais.md")


def _j(x):
    return json.dumps(x, ensure_ascii=False, indent=2, sort_keys=True)


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# Empreintes relevees sur HEAD avant tout cablage, puis recomparees apres :
# les douze etaient identiques. Elles sont gelees ici en litteral pour que
# toute derive future du francais fasse echouer un cas au lieu de passer.
GELEES = {
    "lint_mauvais":
        "ce3d45e00b23cbf24a22bb0ae461defa88fcf4dc907fbb4a21765f626d2684e7",
    "lint_propre":
        "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945",
    "score_mauvais":
        "4cc9f6a35db7fe030acfed604d00601b52b4fcb3ca74eee2786535bd1a1015eb",
    "score_propre":
        "b57189d6f93801b113c13e16ef46c06c7fc35f39298362db86470d1bb4db6ca3",
    "read_propre":
        "78d849bb56a9ae32d31a66e1dcb6ca7c6b6e9ada4873cea47b632314dbe8c823",
    "trac_lacunes":
        "44304d861f026c22d06e7d9de8a57b8a0ea19d1da3da2e030717946e30d784fe",
    "vsrc_sales":
        "09e98ae7ec96bfddb5dac6a7400e1cb630828fdfa7281392be1349f2c95a121c",
    "audit_mauvais":
        "96edb187875dc15f1ee247ce6c514391a50c6b7cde029daad13579e45c64209c",
    "txt_lint_mauvais":
        "e29851b902965fe36a138659e400c7b2a47bd360a2f4edc1ef880ed86a5153f4",
    "txt_score_mauvais":
        "14f8a84ad0d06515cc066f0e7effeecd51d7fe52a08de769fca475b2d9ef56f6",
    "txt_read_propre":
        "40e73477ab0d23979471636468d01c8d5edcdafdf85a39d7a547d93f4eccc8e7",
    "txt_vsrc_sales":
        "9fc539dc9ebebb2953848696be77769a48722d1e4db9468defa7069761a3ced0",
}

_m_read = read_a.mesurer(PROPRE)
MESURES = {
    "lint_mauvais": _j(lint_a.lint_text(MAUVAIS)),
    "lint_propre": _j(lint_a.lint_text(PROPRE)),
    "score_mauvais": _j(score_a.evaluer(MAUVAIS)),
    "score_propre": _j(score_a.evaluer(PROPRE)),
    "read_propre": _j({"metriques": _m_read,
                       "lecture": read_a.interpreter(_m_read)}),
    "trac_lacunes": _j({"analyse": trac_a.analyser(LACUNES),
                        "problemes": trac_a.problemes(
                            trac_a.analyser(LACUNES))}),
    "vsrc_sales": _j(vsrc_a.analyser(SALES)),
    "audit_mauvais": _j(audit_a.auditer(MAUVAIS)),
    "txt_lint_mauvais": lint_a.rapport_texte(lint_a.lint_text(MAUVAIS),
                                             "f.md"),
    "txt_score_mauvais": score_a.rapport_texte(score_a.evaluer(MAUVAIS)),
    "txt_read_propre": read_a.rapport_texte(_m_read),
    "txt_vsrc_sales": vsrc_a.rapport_texte(vsrc_a.analyser(SALES)),
}

for _nom in sorted(GELEES):
    verifier("francais fige : %s inchange a l'octet pres" % _nom,
             _sha(MESURES[_nom]) == GELEES[_nom],
             "%s != %s" % (_sha(MESURES[_nom]), GELEES[_nom]))


# --- Les valeurs machine ne bougent pas quand l'affichage passe a l'anglais --

_sc_fr = score_a.evaluer(ANGLAIS)
_sc_en = score_a.evaluer(ANGLAIS, langue_affichage="en")

verifier("machine : le verdict du scorecard reste francais en affichage "
         "anglais",
         _sc_en["verdict"] == _sc_fr["verdict"]
         and _sc_en["verdict"] in ("Pret", "A reviser", "A refondre",
                                   "Non evaluable"),
         str(_sc_en["verdict"]))

verifier("machine : la decision editoriale reste francaise en affichage "
         "anglais",
         _sc_en["decision_editoriale"]["decision"]
         == _sc_fr["decision_editoriale"]["decision"],
         str(_sc_en["decision_editoriale"]["decision"]))

verifier("machine : les cinq noms d'axes restent les cles francaises",
         list(_sc_en["axes"]) == score_a.AXES_CONNUS,
         str(list(_sc_en["axes"])))

verifier("machine : les cles de sortie du scorecard sont identiques dans les "
         "deux affichages",
         sorted(_sc_en) == sorted(_sc_fr)
         and sorted(_sc_en["poids"]) == sorted(_sc_fr["poids"]),
         str(sorted(set(_sc_en) ^ set(_sc_fr))))

verifier("machine : les scores chiffres ne dependent pas de la langue "
         "d'affichage",
         _sc_en["total"] == _sc_fr["total"]
         and all(_sc_en["axes"][k]["score"] == _sc_fr["axes"][k]["score"]
                 for k in _sc_fr["axes"]),
         "%s / %s" % (_sc_en["total"], _sc_fr["total"]))

_lint_en = lint_a.lint_text(ANGLAIS, None, "en", "en")
_lint_fr = lint_a.lint_text(ANGLAIS, None, "en")
verifier("machine : nom de regle et severite restent francais en affichage "
         "anglais",
         [(c["regle"], c["severite"]) for c in _lint_en]
         == [(c["regle"], c["severite"]) for c in _lint_fr],
         str([c["regle"] for c in _lint_en][:3]))

verifier("machine : seuls message et extrait changent avec l'affichage",
         all(a["message"] != b["message"]
             or a["extrait"] == b["extrait"]
             for a, b in zip(_lint_en, _lint_fr))
         and any(a["message"] != b["message"]
                 for a, b in zip(_lint_en, _lint_fr)),
         "aucun message n'a change de langue")

_trac_d = trac_a.analyser(ANGLAIS)
verifier("machine : l'analyse de tracabilite ne depend pas de l'affichage, "
         "seuls les constats en dependent",
         trac_a.problemes(_trac_d, "en") != trac_a.problemes(_trac_d, "fr")
         and _j(_trac_d) == _j(trac_a.analyser(ANGLAIS)),
         str(trac_a.problemes(_trac_d, "en")[:1]))

verifier("machine : valeur() lit la table sans jamais modifier la valeur "
         "d'entree",
         lib.valeur("scorecard.verdict", "A reviser", "en") == "To revise"
         and lib.VALEURS["scorecard.verdict"]["A reviser"]["fr"]
         == "A reviser")


# --- Aucun mot francais dans un rapport anglais ------------------------------
# Les identifiants de regle (« tiret-cadratin », « url-suivi ») sont des
# valeurs machine imprimees a dessein : ce sont eux que l'auteur grep et que
# du code compare. Ils sont retires avant le controle, et un cas dedie plus
# haut verifie justement qu'ils restent francais.

SLUGS_REGLES = ({r[2] for r in lint_a.regles_pour("fr")}
                | {r[2] for r in lint_a.regles_pour("en")}
                | {"orthographe-melangee", "tiret-cadratin-densite",
                   "passif-excessif"})


def _prose(texte):
    for slug in sorted(SLUGS_REGLES, key=len, reverse=True):
        texte = texte.replace(slug, "")
    return texte


def _mots_francais(texte):
    trouves = set()
    for mot in _MOT_RE.findall(_prose(texte)):
        if mot.lower() in MOTS_FR:
            trouves.add(mot)
    for ligne in _prose(texte).splitlines():
        if any(c in ACCENTS_FR for c in ligne):
            trouves.add(ligne.strip()[:50])
    return sorted(trouves)


_RAPPORTS_EN = {
    "lint": lint_a.rapport_texte(_lint_en, "doc.md", "en", "en"),
    "scorecard": score_a.rapport_texte(_sc_en, "en"),
    "readability": read_a.rapport_texte(read_a.mesurer(ANGLAIS), "en"),
    "traceability": "\n".join(trac_a.problemes(_trac_d, "en")),
    "verify-sources": vsrc_a.rapport_texte(vsrc_a.analyser(ANGLAIS), "en"),
    "trajectoire": score_a.rapport_trajectoire_texte(
        score_a.trajectoire(_sc_en, _sc_en), "en"),
}
_restes_fr = {n: _mots_francais(r) for n, r in _RAPPORTS_EN.items()}
verifier("anglais : aucun des six rapports produits ne porte de mot francais",
         not any(_restes_fr.values()),
         str({n: v for n, v in _restes_fr.items() if v}))

verifier("anglais : les rapports controles ne sont pas vides, le cas mordrait "
         "sinon sur du blanc",
         all(len(r.splitlines()) >= 3 for r in _RAPPORTS_EN.values()),
         str({k: len(v.splitlines()) for k, v in _RAPPORTS_EN.items()}))

verifier("temoin : le meme controle attrape bien le rapport francais",
         bool(_mots_francais(MESURES["txt_score_mauvais"])),
         "le detecteur de francais ne detecte rien, il ne prouve rien")

verifier("anglais : le rapport texte est bien celui de l'anglais, pas une "
         "copie du francais",
         _RAPPORTS_EN["scorecard"] != score_a.rapport_texte(_sc_fr))


# --- Repli declare, valeur inconnue, completude ------------------------------

_SAUVE = lib.LIBELLES.get("scorecard.calcul")
lib.LIBELLES["scorecard.calcul"] = {"fr": _SAUVE["fr"]}
_replie = lib.t("scorecard.calcul", "en")
lib.LIBELLES["scorecard.calcul"] = _SAUVE

verifier("repli : un libelle absent d'une langue retombe sur le francais en "
         "le DECLARANT",
         _replie.startswith(lib.MARQUE_REPLI)
         and _replie.endswith(_SAUVE["fr"]), repr(_replie))

verifier("repli : une cle inconnue sort marquee, ni cle brute ni exception",
         lib.t("scorecard.cle_qui_n_existe_pas", "en")
         == lib.MARQUE_INCONNU + "scorecard.cle_qui_n_existe_pas",
         repr(lib.t("scorecard.cle_qui_n_existe_pas", "en")))

verifier("repli : un verdict machine sans libelle sort marque, il ne se "
         "traduit pas en silence",
         lib.valeur("scorecard.verdict", "Verdict inedit", "en")
         == lib.MARQUE_INCONNU + "Verdict inedit",
         repr(lib.valeur("scorecard.verdict", "Verdict inedit", "en")))

verifier("repli : un espace de valeurs inconnu se comporte pareil",
         lib.valeur("espace.inexistant", "x", "en")
         == lib.MARQUE_INCONNU + "x")

verifier("completude : aucune cle de libelle ne manque en anglais",
         not lib.cles_manquantes("en"), str(lib.cles_manquantes("en")))

verifier("completude : aucune valeur machine ne manque de libelle anglais",
         not lib.valeurs_sans_libelle("en"),
         str(lib.valeurs_sans_libelle("en")))

verifier("completude : les deux langues declarees sont bien fr et en",
         lib.LANGUES == ("fr", "en") and lib.LANGUE_DEFAUT == "fr")

verifier("resolution : l'option explicite prime sur la langue d'analyse",
         lib.resoudre_affichage("fr", "en") == "fr"
         and lib.resoudre_affichage("en", "fr") == "en")

verifier("resolution : sans option, la langue d'analyse decide",
         lib.resoudre_affichage(None, "en") == "en"
         and lib.resoudre_affichage(None, "fr") == "fr")

verifier("resolution : une langue non couverte retombe sur le francais SANS "
         "marque de repli, ce n'est pas un libelle manquant",
         lib.resoudre_affichage(None, "de") == "fr"
         and lib.resoudre_affichage("de", None) == "fr")

_m_de = read_a.mesurer("Ein kurzer Satz. Noch ein Satz hier.", "de")
verifier("resolution : un rapport en langue non couverte reste lisible en "
         "francais, sans marque",
         lib.MARQUE_REPLI not in read_a.rapport_texte(
             _m_de, lib.resoudre_affichage(None, _m_de.get("langue"))),
         str(_m_de.get("langue")))

verifier("motif : un motif de mesure non faite se relit et se retraduit avec "
         "son parametre",
         lib.motif("langue « de » hors des langues couvertes (fr, en)", "en")
         == 'language "de" outside the covered languages (fr, en)',
         lib.motif("langue « de » hors des langues couvertes (fr, en)", "en"))

verifier("motif : un motif inconnu sort marque plutot que traduit de travers",
         lib.motif("un motif jamais vu", "en")
         == lib.MARQUE_INCONNU + "un motif jamais vu"
         and lib.motif("un motif jamais vu") == "un motif jamais vu")


# --- La garde du lot suivant -------------------------------------------------

SCRIPTS_CABLES = ("lint-style.py", "scorecard.py", "readability.py",
                  "traceability.py", "verify-sources.py", "audit-doc.py",
                  "libelles.py")

_restes = {f: constats_non_cables(os.path.join(SCRIPTS, f))
           for f in SCRIPTS_CABLES}
verifier("garde : aucun des sept fichiers cables n'imprime encore une chaine "
         "francaise hors libelles",
         not any(_restes.values()),
         str({f: v for f, v in _restes.items() if v}))

_TEMOIN = '''# -*- coding: utf-8 -*-
"""Docstring en francais : ce module verifie chaque paragraphe du rapport."""


def rapport_texte(d, lib, la):
    # Un commentaire en francais qui parle des ecarts et de chaque mesure.
    """Rapport lisible, avec les axes et le plancher de chaque mesure."""
    out = [lib.t("audit.entete", la)]
    out.append("  " + lib.valeur("scorecard.axe", d["axe"], la))
    out.append("  %s" % d["doublons"])
    print("  Aucun ecart de style detecte dans ce document.")
    return "\\n".join(out)
'''

import tempfile as _tf
_dossier = _tf.mkdtemp(prefix="scriptorium_affichage_")
_temoin = os.path.join(_dossier, "temoin.py")
with open(_temoin, "w", encoding="utf-8") as _fh:
    _fh.write(_TEMOIN)
_vus = constats_non_cables(_temoin)

verifier("garde : une chaine d'affichage non cablee, introduite expres, est "
         "attrapee",
         len(_vus) == 1 and "Aucun ecart de style" in _vus[0][1], str(_vus))

verifier("garde : la ligne signalee est celle du print, pas une autre",
         _vus and _vus[0][0] == 11, str(_vus))

verifier("garde : ni la docstring ni le commentaire francais ne sont "
         "signales, ils sont hors de l'arbre visite",
         not [c for c in _vus if "Docstring" in c[1] or "commentaire" in c[1]
              or "Rapport lisible" in c[1]], str(_vus))

verifier("garde : une cle machine indexee (d[\"doublons\"]) n'est pas prise "
         "pour un libelle",
         not [c for c in _vus if "doublons" in c[1]], str(_vus))

verifier("garde : un appel deja cable (lib.t, lib.valeur) n'est pas "
         "signale",
         not [c for c in _vus if "audit.entete" in c[1]
              or "scorecard.axe" in c[1]], str(_vus))

# Temoin : la garde doit trouver du francais quelque part, sinon elle ne
# prouve rien. Sa cible a suivi le cablage : check-droits.py au lot de
# fondation, puis terminology.py au lot des controles. Depuis le lot des
# outils, PLUS AUCUN script du plugin n'est non cable, et viser un fichier
# reel ferait mentir ce cas. La cible est donc le fichier temoin ecrit
# ci-dessus, seul non cable qui subsiste ; la preuve que la garde ne releve
# plus rien nulle part vit dans evals/cas/affichage-outils.py.
verifier("garde : elle a des dents, elle trouve du francais dans un fichier "
         "non cable",
         bool(constats_non_cables(_temoin)),
         "la garde ne trouve rien nulle part, elle ne prouve rien")


# --- audit-doc : consolidation, langue transmise, sections non cablees -------

def _sortie_de(argv):
    tampon = io.StringIO()
    with contextlib.redirect_stdout(tampon):
        audit_a.main(argv)
    return tampon.getvalue()


_CHEMIN_EN = os.path.join(FIXT, "rapport-anglais.md")
_CHEMIN_FR = os.path.join(FIXT, "style-mauvais.md")
_audit_fr = _sortie_de([_CHEMIN_FR])
_audit_en = _sortie_de([_CHEMIN_EN, "--langue-affichage", "en"])

verifier("audit-doc : le rapport francais garde son entete d'origine",
         _audit_fr.startswith("AUDIT CONSOLIDE — scorecard"),
         _audit_fr.splitlines()[0])

verifier("audit-doc : le rapport anglais nomme ses axes en anglais",
         "Terminology and numbers" in _audit_en
         and "CONSOLIDATED AUDIT" in _audit_en,
         _audit_en.splitlines()[0])

# Avant ce lot, auditer() laissait chaque mesure resoudre la langue de son
# cote : le scorecard la resolvait, l'empreinte IA et la coherence gardaient
# leurs motifs francais et rendaient zero signal sans que rien ne le dise.
# Le defaut se lit dans le code (la langue doit atteindre chaque appel) ET
# dans le resultat (sur un texte anglais a tics, les deux ne comptent plus
# pareil).
_SRC_AUDIT = inspect.getsource(audit_a.auditer)
_sans_langue = [a for a in ("score.evaluer", "aifp.analyser", "coh.analyser")
                if _SRC_AUDIT.find(a) < 0
                or "langue" not in _SRC_AUDIT[_SRC_AUDIT.find(a):
                                              _SRC_AUDIT.find(a) + 90]]
verifier("audit-doc : la langue de mesure atteint les trois mesures qui en "
         "dependent, pas seulement le scorecard",
         not _sans_langue, str(_sans_langue))

_EN_TICS = ("<!-- lint-style:langue=en -->\n\n"
            + "Moreover, the first result holds. Furthermore, the second "
              "result holds. Moreover, the third result holds. However, the "
              "fourth result holds. Moreover, the fifth result holds. "
              "Furthermore, the sixth result holds. Moreover, the seventh "
              "one holds. However, the eighth one holds.")
verifier("audit-doc : sur un texte anglais a tics, l'empreinte IA compte "
         "enfin les connecteurs anglais",
         audit_a.auditer(_EN_TICS)["scorecard"]["langue"] == "en"
         and audit_a.auditer(_EN_TICS)["empreinte_ia"]
         != audit_a.auditer(_EN_TICS, langue="fr")["empreinte_ia"],
         "%s / %s" % (audit_a.auditer(_EN_TICS)["empreinte_ia"],
                      audit_a.auditer(_EN_TICS, langue="fr")["empreinte_ia"]))

_avec_constats = [s for s in (audit_a.auditer(ANGLAIS)["empreinte_ia"],
                              audit_a.auditer(ANGLAIS)["coherence"],
                              audit_a.auditer(ANGLAIS)["tableaux"]) if s]
verifier("audit-doc : une section rendue par un script non cable est "
         "DECLAREE, pas maquillee",
         (not _avec_constats) or "not yet wired" in _audit_en,
         "constats non cables=%s" % _avec_constats)

verifier("audit-doc : la declaration ne pollue pas le rapport francais",
         "non encore cables" not in _audit_fr)

verifier("audit-doc : la sortie JSON reste francaise meme en demandant "
         "l'anglais",
         "\"verdict\": \"A reviser\"" in _sortie_de(
             [_CHEMIN_FR, "--format", "json", "--langue-affichage", "en"]),
         _sortie_de([_CHEMIN_FR, "--format", "json"])[:60])

verifier("cli : la sortie JSON de scorecard.py ignore --langue-affichage",
         _j(score_a.evaluer(ANGLAIS))
         == _j(score_a.evaluer(ANGLAIS, langue_affichage=None)))
