#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Détection déterministe de défaillances chronologiques pour Scriptorium.

Repère cinq incohérences temporelles propres à un texte rédigé avec l'aide
d'un modèle de langage : une date future présentée comme passée, une version
logicielle ou normative citée avant sa date de sortie connue (glossaire
--versions optionnel), une cause datée après son effet dans la même phrase,
un langage à péremption non ancré à une date ou une version ("le plus
récent", "actuellement"), et une chaîne de dates incohérente dans une
référence bibliographique (preprint daté après sa version publiée).

Principe : mesure avant politique. Le script ne bloque jamais par défaut,
il liste des constats à vérifier par un humain. --strict fait passer le
code de sortie à 1 dès qu'un constat existe, quelle que soit sa sévérité.

Portee de langue, verifiee constat par constat plutot que supposee. Quatre
des cinq detections lisent des mots et dependent donc de la langue : la
date future se reconnait a un marqueur de temps passe (verbes francais),
l'inversion causale a un connecteur causal (« grace a », « a permis »), le
langage a peremption a un deictique (« a ce jour », « le plus recent »), et
la chaine de dates a un marqueur de version publiee. Chacune a son jeu de
motifs par langue. Deux briques restent communes et le sont declarees ici :
la version citee avant sa sortie ne lit que le glossaire fourni et des
annees a quatre chiffres, et le reperage de la section bibliographie
delegue a traceability.py, dont le motif de titre couvre deja les deux
langues (References, Bibliographie, Bibliography). Le motif de mois, lui,
sert a taire le langage a peremption dans une phrase deja datee : il est
propre a chaque langue, faute de quoi « the latest, as of March 2024 »
leverait un constat en anglais alors que la phrase porte sa date.

Usage :
    python3 check-temporel.py FICHIER [--format text|json] [--strict]
    python3 check-temporel.py FICHIER --versions glossaire.json
    python3 check-temporel.py FICHIER --date-reference 2026-07-08
    python3 check-temporel.py FICHIER --langue en
    cat doc.md | python3 check-temporel.py -

Format du glossaire de versions (JSON, optionnel), nom vers date ISO :
    {"GPT-4": "2023-03-14", "Python 3.12": "2023-10-02"}

Codes de sortie :
    0  toujours, sauf --strict avec au moins un constat
    1  --strict et au moins un constat
    2  erreur d'usage (fichier ou glossaire illisible, date invalide)

Le module est importable : analyser(texte, langue=None) -> dict avec clé
"constats".

Limite assumée : la détection du marqueur de temps verbal passé et de la
causalité repose sur des listes de motifs curées, pas sur une analyse
grammaticale complète. Le script peut manquer des cas et en signaler à
tort. Chaque constat reste à vérifier, jamais à appliquer aveuglément.
"""
import argparse
import datetime
import importlib.util
import json
import os
import re
import sys

SIGNAL, AVERTISSEMENT = "signal", "avertissement"

ICI = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("traceability_ct",
                                                os.path.join(ICI, "traceability.py"))
_trac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_trac)

SENT_RE = re.compile(r'[^.!?…]+[.!?…]+', re.S)
HEAD_LIGNE_RE = re.compile(r'^\s{0,3}#{1,6}[^\n]*\n+')
ANNEE_RE = re.compile(r'\b(19|20)\d{2}\b')
MOIS = ("janvier|f[ée]vrier|mars|avril|mai|juin|juillet|"
        "ao[uû]t|septembre|octobre|novembre|d[ée]cembre")
DATE_MOIS_RE = re.compile(rf'\b(\d{{1,2}}\s+)?({MOIS})\s+((19|20)\d{{2}})\b', re.I)

MARQUEUR_PASSE_RE = re.compile(
    r"\b(a eu lieu|a permis|a montr[ée]|a r[ée]v[ée]l[ée]|a [ée]t[ée]|ont [ée]t[ée]|"
    r"s'est d[ée]roul[ée]?e?|s'est tenue?|s'est produite?|[ée]tait|furent|fut|avait|"
    r"a organis[ée]|a lanc[ée]|a publi[ée]|a annonc[ée]|s'est achev[ée]e?)\b", re.I)

# connecteur -> position de la date-cause par rapport au connecteur
CONNECTEURS_CAUSAUX = {
    "grâce à": "apres", "grace a": "apres",
    "à la suite de": "apres", "a la suite de": "apres",
    "en raison de": "apres",
    "suite à": "apres", "suite a": "apres",
    "a permis": "avant",
}
CONNECTEUR_RE = re.compile(
    "|".join(re.escape(c) for c in sorted(CONNECTEURS_CAUSAUX, key=len, reverse=True)), re.I)

PEREMPTION_RE = re.compile(
    r"\b(le plus r[ée]cent|la plus r[ée]cente|[àa] ce jour|actuellement|"
    r"pour l'instant|d[ée]sormais|de nos jours|jusqu'[àa] pr[ée]sent)\b", re.I)

PREPRINT_MARK_RE = re.compile(r"\b(preprint|arxiv|pr[ée]publication|working paper)\b", re.I)
PUBLIE_MARK_RE = re.compile(r"\b(in proc\.|actes de|version revue|version publi[ée]e|"
                             r"journal|revue|conf[ée]rence)\b", re.I)

# --- Motifs anglais ---------------------------------------------------------
#
# Transposition mesure par mesure des quatre motifs qui lisent des mots. Le
# marqueur de preprint ci-dessus est deja commun aux deux langues (preprint,
# arxiv, working paper) et n'est pas redouble ; seul le marqueur de version
# publiee l'est, ses formes francaises ne reconnaissant pas « proceedings »
# ni « in press », et « conf[ée]rence » ne reconnaissant pas « conference ».
MOIS_EN = ("january|february|march|april|may|june|july|august|september|"
           "october|november|december|jan|feb|mar|apr|jun|jul|aug|sept|sep|"
           "oct|nov|dec")
DATE_MOIS_EN_RE = re.compile(
    rf'\b(\d{{1,2}}\s+)?({MOIS_EN})\.?\s+(\d{{1,2}},?\s+)?((19|20)\d{{2}})\b', re.I)

MARQUEUR_PASSE_EN_RE = re.compile(
    r"\b(took place|was held|were held|was published|were published|"
    r"was announced|was launched|was released|was completed|was signed|"
    r"has shown|have shown|has been|have been|had been|was|were|had|"
    r"occurred|ended|began|started|reported|demonstrated|revealed)\b", re.I)

CONNECTEURS_CAUSAUX_EN = {
    "thanks to": "apres", "following": "apres", "as a result of": "apres",
    "because of": "apres", "owing to": "apres", "due to": "apres",
    "in the wake of": "apres",
    "led to": "avant", "enabled": "avant", "made possible": "avant",
    "resulted in": "avant", "paved the way for": "avant",
}
CONNECTEUR_EN_RE = re.compile(
    "|".join(re.escape(c) for c in
             sorted(CONNECTEURS_CAUSAUX_EN, key=len, reverse=True)), re.I)

PEREMPTION_EN_RE = re.compile(
    r"\b(the (?:most recent|latest|newest)|to date|currently|at present|"
    r"at the time of writing|recently|in recent years|nowadays|"
    r"(?:so|thus) far|up to now|until now|state[- ]of[- ]the[- ]art)\b", re.I)

PUBLIE_MARK_EN_RE = re.compile(
    r"\b(in proc\.|proceedings|published version|revised version|"
    r"in press|journal|conference|symposium)\b", re.I)


LANGUES = ("fr", "en")

_LINT = None


def _lint():
    """Charge lint-style.py par son chemin, une seule fois.

    Le nom du fichier porte un tiret, il n'est pas importable tel quel. La
    resolution de langue y est definie et documentee : elle est lue ici,
    jamais recopiee, sinon deux scripts pourraient trancher differemment la
    langue du meme document.
    """
    global _LINT
    if _LINT is None:
        spec = importlib.util.spec_from_file_location(
            "lint_style_ct", os.path.join(ICI, "lint-style.py"))
        _LINT = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_LINT)
    return _LINT


def resoudre_langue(texte, langue=None):
    """Tranche la langue d'analyse, par delegation a lint-style.py.

    Meme ordre de priorite que le linter : option explicite, puis auto, puis
    pragme du document, puis francais. Un code hors fr, en et auto est rendu
    tel quel ; les motifs retombent alors sur le francais.
    """
    if langue is not None and langue not in LANGUES and langue != "auto":
        return langue
    return _lint().resoudre_langue(texte, langue)


def _jeu(langue):
    """Jeu de motifs de la langue. Hors anglais, le jeu francais, defaut."""
    if langue == "en":
        return {"passe": MARQUEUR_PASSE_EN_RE, "date_mois": DATE_MOIS_EN_RE,
                "causaux": CONNECTEURS_CAUSAUX_EN, "causal": CONNECTEUR_EN_RE,
                "peremption": PEREMPTION_EN_RE, "publie": PUBLIE_MARK_EN_RE}
    return {"passe": MARQUEUR_PASSE_RE, "date_mois": DATE_MOIS_RE,
            "causaux": CONNECTEURS_CAUSAUX, "causal": CONNECTEUR_RE,
            "peremption": PEREMPTION_RE, "publie": PUBLIE_MARK_RE}


def _ligne_de(texte, offset):
    return texte.count("\n", 0, offset) + 1


def _phrase_affichee(phrase):
    """Nettoyage d'affichage seul : retire un titre Markdown en tête (le
    découpage en phrases ne s'arrête pas aux sauts de ligne), tronque à
    160 caractères. N'affecte jamais la détection, seulement l'extrait montré."""
    return HEAD_LIGNE_RE.sub("", phrase).strip()[:160]


def _annee_proche(segment, position):
    """Année à 4 chiffres la plus proche d'une position dans un segment.
    Retourne l'année (int) ou None si aucune trouvée."""
    meilleure, dist_min = None, None
    for m in ANNEE_RE.finditer(segment):
        centre = (m.start() + m.end()) / 2
        dist = abs(centre - position)
        if dist_min is None or dist < dist_min:
            dist_min, meilleure = dist, int(m.group(0))
    return meilleure


def _annee_apres_position(segment, position):
    """Premiere annee a 4 chiffres dont le debut se trouve a ou apres
    `position` dans `segment` (lecture gauche a droite). None si aucune."""
    for m in ANNEE_RE.finditer(segment):
        if m.start() >= position:
            return int(m.group(0))
    return None


def _detecter_futur_au_passe(texte, date_reference, jeu):
    constats = []
    for m in SENT_RE.finditer(texte):
        phrase = m.group(0)
        annees = [int(a.group(0)) for a in ANNEE_RE.finditer(phrase)]
        if not annees or max(annees) <= date_reference.year:
            continue
        if not jeu["passe"].search(phrase):
            continue
        constats.append({
            "type": "futur-au-passe",
            "severite": AVERTISSEMENT,
            "ligne": _ligne_de(texte, m.start()),
            "message": (f"Année {max(annees)} postérieure à la référence "
                        f"({date_reference.year}) associée à un marqueur de passé dans la "
                        f"même phrase : vérifier si le fait est déjà survenu."),
            "extrait": _phrase_affichee(phrase),
        })
    return constats


def _detecter_versions_anterieures(texte, versions):
    constats = []
    if not versions:
        return constats
    for nom, date_connue in versions.items():
        try:
            annee_connue = int(str(date_connue)[:4])
        except (ValueError, TypeError):
            continue
        for m in re.finditer(re.escape(nom), texte):
            deb = texte.rfind(".", 0, m.start()) + 1
            fin = texte.find(".", m.end())
            fin = fin if fin != -1 else len(texte)
            phrase = texte[deb:fin]
            annees = [int(a.group(0)) for a in ANNEE_RE.finditer(phrase)]
            if any(a < annee_connue for a in annees):
                constats.append({
                    "type": "version-anterieure",
                    "severite": AVERTISSEMENT,
                    "ligne": _ligne_de(texte, m.start()),
                    "message": (f"« {nom} » mentionné avec une année antérieure à sa date "
                                f"connue ({date_connue})."),
                    "extrait": _phrase_affichee(phrase),
                })
    return constats


def _detecter_inversions_causales(texte, jeu):
    constats = []
    for m in SENT_RE.finditer(texte):
        phrase = m.group(0)
        cm = jeu["causal"].search(phrase)
        if not cm:
            continue
        sens = jeu["causaux"].get(cm.group(0).lower())
        if sens is None:
            continue
        avant, apres = phrase[:cm.start()], phrase[cm.end():]
        annee_avant = _annee_proche(avant, len(avant))
        annee_apres = _annee_proche(apres, 0)
        if annee_avant is None or annee_apres is None:
            continue
        annee_cause, annee_effet = ((annee_apres, annee_avant) if sens == "apres"
                                     else (annee_avant, annee_apres))
        if annee_cause > annee_effet:
            constats.append({
                "type": "inversion-causale",
                "severite": AVERTISSEMENT,
                "ligne": _ligne_de(texte, m.start()),
                "message": (f"Connecteur causal « {cm.group(0)} » : la date associée à la "
                            f"cause ({annee_cause}) suit celle de l'effet ({annee_effet}) "
                            f"au lieu de la précéder."),
                "extrait": _phrase_affichee(phrase),
            })
    return constats


def _detecter_langage_peremption(texte, jeu):
    constats = []
    for m in SENT_RE.finditer(texte):
        phrase = m.group(0)
        if ANNEE_RE.search(phrase) or jeu["date_mois"].search(phrase):
            continue
        for pm in jeu["peremption"].finditer(phrase):
            constats.append({
                "type": "langage-peremption",
                "severite": SIGNAL,
                "ligne": _ligne_de(texte, m.start() + pm.start()),
                "message": f"« {pm.group(0)} » non ancré à une date ou une version dans la phrase.",
                "extrait": _phrase_affichee(phrase),
            })
    return constats


def _detecter_chaines_incoherentes(texte, jeu):
    """Cherche, ligne par ligne dans la section bibliographie, un marqueur de
    preprint et un marqueur de version publiee tous deux presents, chacun
    associe a la premiere annee qui le suit dans la ligne (ordre de lecture)."""
    constats = []
    _, biblio = _trac.separer_biblio(texte)
    if not biblio:
        return constats
    debut_biblio = len(texte) - len(biblio)
    offset = 0
    for brute in biblio.splitlines(keepends=True):
        ligne = brute.rstrip("\n")
        pm = PREPRINT_MARK_RE.search(ligne)
        um = jeu["publie"].search(ligne)
        if pm and um:
            annee_preprint = _annee_apres_position(ligne, pm.end())
            annee_publie = _annee_apres_position(ligne, um.end())
            if (annee_preprint is not None and annee_publie is not None
                    and annee_preprint > annee_publie):
                constats.append({
                    "type": "chaine-incoherente",
                    "severite": AVERTISSEMENT,
                    "ligne": _ligne_de(texte, debut_biblio + offset),
                    "message": (f"Référence : le preprint ({annee_preprint}) est daté après "
                                f"la version publiée ({annee_publie})."),
                    "extrait": ligne.strip()[:160],
                })
        offset += len(brute)
    return constats


def analyser(texte, date_reference=None, versions=None, langue=None):
    if date_reference is None:
        date_reference = datetime.date.today()
    langue = resoudre_langue(texte, langue)
    jeu = _jeu(langue)
    constats = []
    constats += _detecter_futur_au_passe(texte, date_reference, jeu)
    constats += _detecter_versions_anterieures(texte, versions)
    constats += _detecter_inversions_causales(texte, jeu)
    constats += _detecter_langage_peremption(texte, jeu)
    constats += _detecter_chaines_incoherentes(texte, jeu)
    constats.sort(key=lambda c: (c["ligne"], c["type"]))
    return {"constats": constats, "langue": langue}


def compter(constats):
    n = {SIGNAL: 0, AVERTISSEMENT: 0}
    for c in constats:
        n[c["severite"]] += 1
    return n


def rapport_texte(d, chemin):
    constats = d["constats"]
    n = compter(constats)
    out = [f"Vérification temporelle : {chemin or '(stdin)'}"]
    out.append(f"  signaux={n[SIGNAL]}  avertissements={n[AVERTISSEMENT]}")
    if not constats:
        out.append("  Aucune défaillance chronologique détectée.")
        return "\n".join(out)
    type_courant = None
    for c in constats:
        if c["type"] != type_courant:
            type_courant = c["type"]
            out.append(f"\n[{type_courant}]")
        out.append(f"  L{c['ligne']} ({c['severite']}) {c['message']}\n      « {c['extrait']} »")
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(description="Vérification temporelle déterministe Scriptorium.")
    p.add_argument("fichier", help="chemin du fichier, ou - pour stdin")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--strict", action="store_true",
                   help="code de sortie 1 si au moins un constat (jamais bloquant sans ce drapeau)")
    p.add_argument("--versions", help="glossaire JSON optionnel {nom_version: date_ISO}")
    p.add_argument("--date-reference", help="date de référence AAAA-MM-JJ (défaut : aujourd'hui)")
    p.add_argument("--langue", choices=["fr", "en", "auto"], default=None,
                   help="langue d'analyse. Sans l'option : le pragme "
                        "lint-style:langue du document, sinon fr. "
                        "auto lance la détection heuristique")
    a = p.parse_args(argv)
    try:
        texte = sys.stdin.read() if a.fichier == "-" else open(a.fichier, encoding="utf-8").read()
    except OSError as e:
        print(f"Erreur de lecture : {e}", file=sys.stderr)
        return 2
    versions = None
    if a.versions:
        try:
            with open(a.versions, encoding="utf-8") as f:
                versions = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            print(f"Erreur de lecture du glossaire de versions : {e}", file=sys.stderr)
            return 2
    date_reference = datetime.date.today()
    if a.date_reference:
        try:
            date_reference = datetime.datetime.strptime(a.date_reference, "%Y-%m-%d").date()
        except ValueError as e:
            print(f"Date de référence invalide : {e}", file=sys.stderr)
            return 2
    chemin = None if a.fichier == "-" else a.fichier
    d = analyser(texte, date_reference=date_reference, versions=versions,
                 langue=a.langue)
    if a.format == "json":
        print(json.dumps({"fichier": chemin, "compte": compter(d["constats"]), **d},
                          ensure_ascii=False, indent=2))
    else:
        print(rapport_texte(d, chemin))
    if a.strict and d["constats"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
