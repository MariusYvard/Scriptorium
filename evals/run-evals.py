#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Harnais d'évaluation de Scriptorium.

Vérifie que les garde-fous déterministes attrapent bien ce qu'ils doivent et
laissent passer ce qui est conforme. Chaque cas de test relie une fixture à des
attentes précises. Le harnais protège contre les régressions : si une règle du
linter ou du vérificateur change, un cas échoue.

Usage : python3 run-evals.py
Code de sortie 0 si tous les cas passent, 1 sinon.
"""
import importlib.util
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(ICI, "..", "scripts")
FIXT = os.path.join(ICI, "fixtures")


def charger(nom_fichier, nom_module):
    spec = importlib.util.spec_from_file_location(
        nom_module, os.path.join(SCRIPTS, nom_fichier))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lint = charger("lint-style.py", "lint_style")
vsrc = charger("verify-sources.py", "verify_sources")
read = charger("readability.py", "readability")
figs = charger("figures.py", "figures")
theme = charger("theme.py", "theme_mod")
trac = charger("traceability.py", "traceability")
term = charger("terminology.py", "terminology")
nums = charger("numbers.py", "numbers")
score = charger("scorecard.py", "scorecard")
cita = charger("citations.py", "citations")
diffv = charger("diff-versions.py", "diff_versions")
aifp = charger("ai-fingerprint.py", "ai_fingerprint")
coh = charger("coherence.py", "coherence")
tab = charger("tables.py", "tables")
planc = charger("plan-check.py", "plan_check")
proj = charger("project.py", "project")
auditd = charger("audit-doc.py", "audit_doc")
imgs = charger("images.py", "images")


def lire(nom):
    return open(os.path.join(FIXT, nom), encoding="utf-8").read()


RESULTATS = []


def verifier(nom, condition, detail=""):
    RESULTATS.append((nom, bool(condition), detail))


# Cas 1 : le linter attrape les critiques du document fautif
constats = lint.lint_text(lire("style-mauvais.md"))
regles_crit = {c["regle"] for c in constats if c["severite"] == "critique"}
verifier("lint attrape le tiret cadratin", "tiret-cadratin" in regles_crit)
verifier("lint attrape les guillemets courbes", "typographie-courbe" in regles_crit)
verifier("lint attrape le lexique promo", "lexique-promo" in regles_crit)
verifier("lint attrape les parametres de suivi", "url-suivi" in regles_crit)
verifier("lint signale la virgule d'Oxford (majeur)",
         any(c["regle"] == "virgule-oxford" for c in constats))
verifier("lint compte au moins 4 critiques",
         sum(1 for c in constats if c["severite"] == "critique") >= 4,
         f"critiques={sum(1 for c in constats if c['severite']=='critique')}")

# Cas 2 : le document propre ne declenche aucun critique
constats_ok = lint.lint_text(lire("style-propre.md"))
verifier("document propre : zero critique",
         not any(c["severite"] == "critique" for c in constats_ok),
         f"critiques={[c['regle'] for c in constats_ok if c['severite']=='critique']}")

# Cas 3 : le verificateur de sources nettoie et deduplique
d = vsrc.analyser(lire("sources-sales.md"))
verifier("verify : au moins 2 URL a nettoyer", len(d["urls_a_nettoyer"]) >= 2,
         f"a_nettoyer={len(d['urls_a_nettoyer'])}")
verifier("verify : au moins 1 doublon detecte", len(d["doublons"]) >= 1,
         f"doublons={len(d['doublons'])}")
verifier("verify : aucun parametre utm dans les URL propres",
         all("utm_" not in u for u in d["urls"]))

# Cas 4 : la lisibilite produit des metriques coherentes
m = read.mesurer(lire("style-propre.md"))
verifier("readability : indice LIX calcule", m["indice_lix"] > 0)
verifier("readability : au moins une phrase comptee", m["phrases"] >= 1)

# Cas 5 : l'audit de figure repere une case vide et une valeur hors bornes
av_swot = figs.auditer("swot", {"forces": ["a"], "faiblesses": ["b"], "opportunites": ["c"]})
verifier("audit figure : case menaces vide signalee",
         any("menaces" in a for a in av_swot))
av_bcg = figs.auditer("bcg", {"items": [{"nom": "X", "croissance": 50, "part": 140}]})
verifier("audit figure : valeur BCG hors bornes signalee",
         any("hors de 0-100" in a for a in av_bcg))


# Cas 6 : la charte graphique valide passe, le faible contraste et le hex invalide sont signales
err_ok, warn_ok = theme.valider(theme.charger({"encre": "#16314E", "fond": "#FFFFFF"}))
verifier("theme : charte correcte sans erreur", not err_ok)
err_ko, warn_ko = theme.valider(theme.charger({"encre": "#8A8A8A", "fond": "#9C9C9C"}))
verifier("theme : faible contraste signale", any("Contraste" in w for w in warn_ko))
err_bad, _ = theme.valider(theme.charger({"accent": "zz"}))
verifier("theme : couleur mal formee = erreur", any("accent" in e for e in err_bad))


dt = trac.analyser("Voir [1] et [4].\n\n## References\n1. A.\n")
verifier("tracabilite : citation pendante", 4 in dt["citations_pendantes"])
dtm = term.analyser("La methode HACCP est utilisee partout.")
verifier("terminologie : sigle non defini", "HACCP" in dtm["sigles_non_definis"])
dn = nums.analyser("Un taux de 120 % apparait.")
verifier("nombres : pourcentage impossible", bool(dn["pourcentages_impossibles"]))
sc = score.evaluer("# T\n\nLe rapport sert la decision. Les donnees datent de 2025 et montrent une hausse de 12 pour cent, portee par les grands comptes. La tendance tient sur trois exercices consecutifs. La source est https://exemple.fr/x")
verifier("scorecard : texte propre bien note", sc["total"] >= 80, f"total={sc['total']}")
sc2 = score.evaluer("Ce projet est crucial et incontournable [4]. La methode HACCP. Un taux de 120 % et 40 %, 35 % et 20 %. Valeurs 1,5 et 2.5.")
verifier("scorecard : texte fautif mal note", sc2["total"] < 70, f"total={sc2['total']}")
bib1 = "@article{k,\n author={Doe, Jane},\n title={T},\n year={2024},\n doi={10.1/x}\n}\n"
bib2 = "@book{k2,\n title={Autre},\n doi={10.1/x},\n year={2023}\n}\n"
ent = cita.parser_bibtex(bib1)
verifier("citations : bibtex parse une entree", len(ent) == 1)
uniq, dbl = cita.dedupe(ent + cita.parser_bibtex(bib2))
verifier("citations : dedupe par DOI", len(uniq) == 1 and dbl == ["k2"])
df = diffv.comparer("# A\nun deux\n", "# A\nun deux trois\n\n# B\nnouveau\n")
verifier("diff : section ajoutee", "B" in df["sections_ajoutees"])


aif = aifp.analyser("De plus, le un. De plus, le deux. De plus, le trois. De plus, le quatre. De plus, le cinq. De plus, le six. De plus, le sept. De plus, le huit.")
verifier("empreinte IA : tics detectes", len(aif["signaux"]) >= 2, f"sig={len(aif['signaux'])}")
cohd = coh.analyser("Le chiffre progresse de douze pour cent porte par la demande des grands comptes a l export.\n\nAutre paragraphe distinct ici present.\n\nLe chiffre progresse de douze pour cent porte par la demande des grands comptes a l export.")
verifier("coherence : paragraphe duplique", bool(cohd["paragraphes_dupliques"]))
tb = tab.auditer("| A | B |\n| --- | --- |\n| 1 |  |\n")
verifier("tables : cellule vide detectee", bool(tb["problemes"]))
verifier("tables : generer disponible", callable(tab.generer))
pc = planc.analyser({"sections": ["Introduction", "Conclusion"]}, "# Introduction\nx\n")
verifier("plan : section manquante", "Conclusion" in pc["sections_manquantes"])
sk = proj.charger("/tmp/inexistant_scriptorium_xyz.json")
verifier("project : squelette par defaut", "genre" in sk)
ad = auditd.auditer("# T\n\nUn texte court de test pour l audit consolide, avec une source https://x.fr et rien d autre.")
verifier("audit-doc : scorecard present", "total" in ad["scorecard"])


cssout = theme.css(theme.charger({"accent": "#C8102E"}))
verifier("theme : css derive de la charte (accent + impression)",
         "--accent: #C8102E" in cssout and "@media print" in cssout)


import tempfile as _tmp, zipfile as _zip
_png = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                     "1f15c4890000000d49444154789c6200010000050001"
                     "0d0a2db40000000049454e44ae426082")
_d = _tmp.mkdtemp(prefix="scriptorium_img_")
_docx = os.path.join(_d, "t.docx")
with _zip.ZipFile(_docx, "w") as _z:
    _z.writestr("word/document.xml", "<x/>")
    _z.writestr("word/media/image1.png", _png)
    _z.writestr("word/media/image2.png", _png)
_mi = imgs.extract(_docx, os.path.join(_d, "out"), 0)
verifier("images : office 1 unique + 1 doublon", _mi["count"] == 1 and _mi["doublons"] == 1, f"c={_mi['count']} d={_mi['doublons']}")
verifier("images : dimensions PNG 1x1 lues", any(i.get("largeur") == 1 and i.get("hauteur") == 1 for i in _mi["images"]))
verifier("images : manifest ecrit", os.path.isfile(os.path.join(_d, "out", "manifest.json")))
verifier("images : pdf sans backend renvoie une note", bool(imgs.extract(os.path.join(_d, "vide.pdf"), os.path.join(_d, "o2"))["notes"]))


import glob as _glob
_gdir = os.path.join(ICI, "..", "skills", "produire", "references")
_genres = _glob.glob(os.path.join(_gdir, "genre-*.md"))
verifier("genres : au moins 24 playbooks", len(_genres) >= 24, f"n={len(_genres)}")
_sans_src = sorted(os.path.basename(f) for f in _genres if "## Sources" not in open(f, encoding="utf-8").read())
verifier("genres : chaque playbook porte une section Sources", not _sans_src, f"sans={_sans_src}")


# --- v0.7.0 : integrite des sources, comite de revue, atelier ---

ctmp = charger("check-temporel.py", "check_temporel")
import re as _re
import json as _json

# Ancres de citation (fixture a double usage)
_bib = _re.search(r"```bibtex\n(.*?)```", lire("citations-sans-ancre.md"), _re.S).group(1)
_ent = cita.parser_bibtex(_bib)
_ra = cita.rapport_ancrage(_ent)
verifier("citations : la fixture d'ancrage porte 3 entrees", len(_ent) == 3, f"n={len(_ent)}")
verifier("citations : l'entree sans ancre est seule reperee",
         _ra["sans_ancre"] == ["orphan2024"], f"sans={_ra['sans_ancre']}")
for _s in ("apa", "vancouver", "chicago", "mla", "ieee"):
    verifier(f"citations : format {_s} rend chaque entree",
             all(cita.FORMATS[_s](e) for e in _ent))

# Tags de lacune normalises (fixture a double usage)
_dt = trac.analyser(lire("lacunes-tagguees.md"))
verifier("traceability : 2 tags LACUNE MATERIELLE comptes",
         _dt["tags_lacune_materielle"] == 2, f"n={_dt['tags_lacune_materielle']}")
verifier("traceability : 1 tag PREUVE FAIBLE compte",
         _dt["tags_preuve_faible"] == 1, f"n={_dt['tags_preuve_faible']}")
verifier("traceability : la variante mal casse est signalee",
         len(_dt["tags_variantes_mal_formees"]) == 1, f"v={_dt['tags_variantes_mal_formees']}")

# Verification temporelle
_ct = ctmp.analyser("Le lancement a eu lieu en 2099.")
verifier("temporel : futur presente comme passe detecte",
         any(c["type"] == "futur-au-passe" for c in _ct["constats"]))
_ct2 = ctmp.analyser("La reforme de 2022 a permis la croissance de 2018.")
verifier("temporel : inversion causale detectee",
         any(c["type"] == "inversion-causale" for c in _ct2["constats"]))
_ct3 = ctmp.analyser("L'etude de 2020 precede la synthese publiee en 2024.")
verifier("temporel : chronologie saine sans faux positif",
         not any(c["type"] in ("futur-au-passe", "inversion-causale") for c in _ct3["constats"]),
         f"constats={[c['type'] for c in _ct3['constats']]}")

# Scorecard : plancher par axe et decision editoriale
_scp = score.evaluer(lire("style-mauvais.md"))
verifier("scorecard : decision editoriale rendue", "decision_editoriale" in _scp)
verifier("scorecard : un axe effondre plafonne la decision a refus",
         _scp["decision_editoriale"]["decision"] == "refus"
         and "Style" in _scp["decision_editoriale"]["axes_effondres"],
         f"decision={_scp['decision_editoriale']}")

# Trajectoire entre deux revues (fixtures a double usage)
_tj = score.trajectoire(_json.loads(lire("rapport-regression-avant.json")),
                        _json.loads(lire("rapport-regression-apres.json")))
verifier("trajectoire : regression d'axe detectee sous -3",
         "Style" in _tj["regressions"], f"reg={_tj['regressions']}")
verifier("trajectoire : delta total negatif rapporte",
         _tj["delta_total"] < 0, f"delta={_tj['delta_total']}")

# Journal de projet : hash, transitions, reprise unique
_dp = proj.charger("/tmp/inexistant_scriptorium_v070.json")
verifier("project : hash de continuite deterministe sur 12 hexadecimaux",
         proj._hash_continuite(_dp.get("journal", [])) == proj._hash_continuite(_dp.get("journal", []))
         and len(proj._hash_continuite([])) == 12)
proj.changer_etat(_dp, "cadrage", "en_cours")
try:
    proj.changer_etat(_dp, "redaction", "termine")
    _illegale = False
except ValueError:
    _illegale = True
verifier("project : transition illegale refusee", _illegale)
proj.poser_frontiere(_dp, "fin de cadrage")
_hf = _dp["journal"][-1]["hash"]
proj.reprendre(_dp, _hf)
try:
    proj.reprendre(_dp, _hf)
    _double = False
except ValueError:
    _double = True
verifier("project : double reprise du meme hash refusee", _double)

# Friction des outrepassements (3 crans)
_ok1 = True
try:
    proj.valider_justification(1, None)
except ValueError:
    _ok1 = False
verifier("friction : cran 1 passe sans justification", _ok1)
try:
    proj.valider_justification(2, "")
    _cran2 = False
except ValueError:
    _cran2 = True
verifier("friction : cran 2 exige une justification", _cran2)
try:
    proj.valider_justification(3, "trop court")
    _cran3 = False
except ValueError:
    _cran3 = True
verifier("friction : cran 3 exige 100 caracteres", _cran3)

# Lint de prompt : les fichiers du plugin comme donnees
for _skill in ("atelier", "produire", "controler", "livrer"):
    _p = os.path.join(ICI, "..", "skills", _skill, "SKILL.md")
    _txt = open(_p, encoding="utf-8").read()
    _refs = set(_re.findall(r"`references/([a-z0-9-]+\.md)`", _txt))
    _manq = sorted(r for r in _refs
                   if not os.path.isfile(os.path.join(ICI, "..", "skills", _skill, "references", r)))
    verifier(f"routeur {_skill} : chaque reference citee existe", not _manq, f"manquantes={_manq}")

for _a in sorted(_glob.glob(os.path.join(ICI, "..", "agents", "*.md"))):
    _t = open(_a, encoding="utf-8").read()
    _fm = _t.split("---")[1] if _t.startswith("---") else ""
    verifier(f"agent {os.path.basename(_a)} : frontmatter name et description",
             "name:" in _fm and "description:" in _fm)

_perimes = []
for _f in (_glob.glob(os.path.join(ICI, "..", "agents", "*.md"))
           + _glob.glob(os.path.join(ICI, "..", "skills", "*", "references", "*.md"))
           + _glob.glob(os.path.join(ICI, "..", "skills", "*", "SKILL.md"))):
    _t = open(_f, encoding="utf-8").read()
    for _old in ("skills/rediger/", "skills/reviser/", "skills/style-maison/"):
        if _old in _t:
            _perimes.append((os.path.basename(_f), _old))
verifier("lint de prompt : aucun chemin de competence perime", not _perimes, f"{_perimes}")

_avec_sources = [
    ("produire", ("integrite-sources.md", "hierarchie-preuve.md", "corpus-utilisateur.md",
                  "discipline-synthese.md", "credit-divulgation.md", "veille.md")),
    ("controler", ("contrat-notation.md", "lettre-decision.md", "biais-relecteur.md",
                   "sante-dialogue.md", "sophismes-causalite.md", "plagiat.md")),
    ("atelier", ("cadre-finer.md", "boite-socratique.md")),
]
_sans = []
for _skill, _fichiers in _avec_sources:
    for _n in _fichiers:
        _p = os.path.join(ICI, "..", "skills", _skill, "references", _n)
        if "## Sources" not in open(_p, encoding="utf-8").read():
            _sans.append(_n)
verifier("lint de prompt : chaque nouvelle reference sourcee porte sa section Sources",
         not _sans, f"sans={_sans}")

def main():
    passes = sum(1 for _, ok, _ in RESULTATS if ok)
    total = len(RESULTATS)
    for nom, ok, detail in RESULTATS:
        marque = "PASS" if ok else "ECHEC"
        suffixe = f"  [{detail}]" if (detail and not ok) else ""
        print(f"  {marque}  {nom}{suffixe}")
    print(f"\n{passes}/{total} cas reussis.")
    return 0 if passes == total else 1


if __name__ == "__main__":
    sys.exit(main())
