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
RACINE = os.path.abspath(os.path.join(ICI, ".."))
PLUGIN = os.path.join(RACINE, "scriptorium")
SCRIPTS = os.path.join(PLUGIN, "scripts")
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
gab = charger("gabarit.py", "gabarit")
logo = charger("logos.py", "logos")


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
_gdir = os.path.join(PLUGIN, "skills", "produire", "references")
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
    _p = os.path.join(PLUGIN, "skills", _skill, "SKILL.md")
    _txt = open(_p, encoding="utf-8").read()
    _refs = set(_re.findall(r"`references/([a-z0-9-]+\.md)`", _txt))
    _manq = sorted(r for r in _refs
                   if not os.path.isfile(os.path.join(PLUGIN, "skills", _skill, "references", r)))
    verifier(f"routeur {_skill} : chaque reference citee existe", not _manq, f"manquantes={_manq}")

for _a in sorted(_glob.glob(os.path.join(PLUGIN, "agents", "*.md"))):
    _t = open(_a, encoding="utf-8").read()
    _fm = _t.split("---")[1] if _t.startswith("---") else ""
    verifier(f"agent {os.path.basename(_a)} : frontmatter name et description",
             "name:" in _fm and "description:" in _fm)

_perimes = []
for _f in (_glob.glob(os.path.join(PLUGIN, "agents", "*.md"))
           + _glob.glob(os.path.join(PLUGIN, "skills", "*", "references", "*.md"))
           + _glob.glob(os.path.join(PLUGIN, "skills", "*", "SKILL.md"))):
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
        _p = os.path.join(PLUGIN, "skills", _skill, "references", _n)
        if "## Sources" not in open(_p, encoding="utf-8").read():
            _sans.append(_n)
verifier("lint de prompt : chaque nouvelle reference sourcee porte sa section Sources",
         not _sans, f"sans={_sans}")

# --- v0.8.0 : recolte openscience (sources, evaluation, livraison) ---

chkp = charger("check-presentation.py", "check_presentation")

# Citations : validation de champs par type et tri stable
_bibv = (
    "@article{ok2024,\n author={Doe, Jane},\n title={T},\n journal={J},\n year={2024},\n note={p. 3}\n}\n"
    "@article{article_incomplet,\n title={Sans auteur ni annee},\n journal={J}\n}\n"
    "@book{livre_editeur,\n editor={Roe, Dan},\n title={L},\n publisher={P},\n year={2020}\n}\n"
    "@inproceedings{confmanquante,\n author={Poe, Al},\n title={C},\n year={2021}\n}\n"
    "@typeinconnu{bizarre,\n title={X}\n}\n")
_entv = cita.parser_bibtex(_bibv)
_rapv = cita.rapport_validation(_entv)
verifier("citations : champs manquants reperes par type",
         sorted(_rapv["incompletes"]) == ["article_incomplet", "confmanquante"],
         f"inc={_rapv['incompletes']}")
verifier("citations : type non reconnu signale, book a editeur accepte",
         _rapv["types_non_reconnus"] == ["bizarre"] and "livre_editeur" not in _rapv["incompletes"],
         f"types={_rapv['types_non_reconnus']}")
_bibt = ("@misc{b,\n title={B},\n year={2020}\n}\n@misc{a,\n title={A},\n year={2022}\n}\n"
         "@misc{c,\n title={C},\n year={2020}\n}\n")
_trie = cita.trier_entrees(cita.parser_bibtex(_bibt), "annee")
verifier("citations : tri par annee stable sur egalite",
         [e["_cle"] for e in _trie] == ["b", "c", "a"],
         f"ordre={[e['_cle'] for e in _trie]}")

# Verify-sources : paliers de domaine sans reseau
_dp2 = vsrc.analyser(
    "Sources : https://www.nature.com/articles/x https://arxiv.org/abs/2001.00001 "
    "https://medium.com/@x/y https://www.economie.gouv.fr/page https://site-inconnu-xyz.example/p")
_pal = {p["url"].split("/")[2]: p["palier"] for p in _dp2["paliers"]}
verifier("paliers : revue a comite et preprint distingues",
         _pal.get("www.nature.com") == "revue-a-comite" and _pal.get("arxiv.org") == "preprint",
         f"pal={_pal}")
verifier("paliers : suffixe gouv.fr institutionnel et inconnu non classe",
         _pal.get("www.economie.gouv.fr") == "institutionnel"
         and _pal.get("site-inconnu-xyz.example") == "non-classe", f"pal={_pal}")

# Reporting-standards : garde structurelle (URL sans utm, compte chiffre ou non confirme)
_rs = open(os.path.join(PLUGIN, "skills", "produire", "references",
                        "reporting-standards.md"), encoding="utf-8").read()
_lignes_std = [l for l in _rs.splitlines()
               if _re.match(r"^\| (CONSORT|STROBE|SPIRIT|STARD|TRIPOD|ARRIVE|CARE|SQUIRE|CHEERS|SRQR) ", l)]
verifier("reporting-standards : les 10 standards tabules",
         len(_lignes_std) >= 10, f"n={len(_lignes_std)}")
verifier("reporting-standards : au moins 10 URL primaires en Sources, aucune URL de suivi",
         _rs.count("https://") >= 10 and "utm_" not in _rs)
_std_sans_compte = [l.split("|")[1].strip() for l in _lignes_std
                    if not (_re.search(r"\d", l) or _re.search(r"non confirm", l, _re.I))]
verifier("reporting-standards : chaque rangee porte un compte ou la mention non confirme",
         not _std_sans_compte, f"sans={_std_sans_compte}")

# Scorecard : barres ASCII, forces et faiblesses, poids, seuil de type, arret anticipe
_scr = score.evaluer(lire("style-mauvais.md"))
_txt = score.rapport_texte(_scr)
verifier("scorecard : barre ASCII presente dans le rapport",
         "#" in _txt and any(len(seg) >= 10 for seg in _re.findall(r"#+", _txt)))
verifier("scorecard : forces et faiblesses nommees",
         "Force" in _txt and "Faiblesse" in _txt)
_scp2 = score.evaluer(lire("style-propre.md"),
                      poids={"Style": 0.75, "Sources": 0.75, "Tracabilite": 0.75,
                             "Terminologie et nombres": 0.75, "Lisibilite": 0.75})
verifier("scorecard : poids renormalises, total borne a 100",
         0 <= _scp2["total"] <= 100, f"total={_scp2['total']}")
_scs = score.evaluer(lire("style-mauvais.md"), seuil_type="publication")
verifier("scorecard : seuil de type publication non atteint sur texte fautif",
         _scs["seuil_type"]["atteint"] is False, f"st={_scs['seuil_type']}")
_tja = {"axes": {"Style": {"score": 18}, "Sources": {"score": 15}}, "total": 80, "verdict": "x"}
_tjb = {"axes": {"Style": {"score": 19}, "Sources": {"score": 16}}, "total": 82, "verdict": "x"}
_tj2 = score.trajectoire(_tja, _tjb)
verifier("trajectoire : arret anticipe signale sous +3 sans regression",
         _tj2.get("arret_anticipe") is True, f"tj={_tj2.get('arret_anticipe')}")

# Figures : TAM-SAM-SOM
_ts_ok = {"tam": {"libelle": "Marche total", "valeur": "80"},
          "sam": {"libelle": "Accessible", "valeur": "30"},
          "som": {"libelle": "Atteignable", "valeur": "5"}}
_svg_ts = figs.tam_sam_som(_ts_ok)
verifier("figures : tam-sam-som genere 3 cercles etiquetes",
         _svg_ts.count("<circle") >= 3 and "Marche total" in _svg_ts)
_av_ts = figs.auditer("tam-sam-som", {"tam": {"libelle": "T", "valeur": "10"},
                                      "sam": {"libelle": "S", "valeur": "50"},
                                      "som": {"libelle": "O", "valeur": "5"}})
verifier("figures : audit tam-sam-som attrape l'ordre inverse",
         any("TAM" in a and "SAM" in a for a in _av_ts), f"avis={_av_ts}")

# Theme : preambule LaTeX, palette nommee, avertissement dichromate
_th = theme.charger({"encre": "#16314E", "fond": "#FFFFFF", "accent": "#C8102E"})
_ltx = theme.latex(_th)
verifier("theme : preambule latex avec definecolor et police",
         "\\definecolor" in _ltx and ("setmainfont" in _ltx or "newfontfamily" in _ltx))
_thp = theme.charger({"encre": "#111111", "fond": "#FFFFFF", "palette": "okabe-ito"})
verifier("theme : palette okabe-ito injectee",
         any(c.upper() in ("#E69F00", "#56B4E9") for c in _thp.get("palette", [])),
         f"pal={_thp.get('palette')}")
_errd, _warnd = theme.valider(theme.charger(
    {"encre": "#111111", "fond": "#FFFFFF", "palette": ["#CC3333", "#33CC33"]}))
verifier("theme : paire rouge-vert signalee au dichromate",
         any("dichromate" in w for w in _warnd), f"warn={_warnd}")

# Check-presentation : degradation propre sans backend
_sauve = (chkp.extraire_texte_pages, chkp.rendre_pages_basses_res, chkp.compter_pages_et_taille)
chkp.extraire_texte_pages = lambda chemin: (None, "aucun backend")
chkp.rendre_pages_basses_res = lambda chemin, dpi=60: (None, "aucun backend")
chkp.compter_pages_et_taille = lambda chemin: (None, 0, "aucun backend")
_rapp = chkp.analyser("/tmp/deck_inexistant_scriptorium.pdf", duree=15)
chkp.extraire_texte_pages, chkp.rendre_pages_basses_res, chkp.compter_pages_et_taille = _sauve
verifier("check-presentation : degradation declaree, rien d'invente",
         any("saut" in str(x).lower() or "aucun backend" in str(x).lower()
             for x in (_rapp.get("notes") or [])) or _rapp.get("pages") is None,
         f"rapport={_rapp.get('notes')}")


# Gabarit : inventaire, comparaison, remplissage
_gab_src = os.path.join(FIXT, "gabarit-ecole.docx")
_inv = gab.inventorier(_gab_src)
verifier("gabarit : styles nommes lus dans le zip",
         len(_inv["styles"]) >= 5, f"n={len(_inv['styles'])}")
verifier("gabarit : hierarchie de titres reconstituee par identifiant",
         _inv["hierarchie_titres"].get("1") == "Heading1"
         and _inv["style_corps"] == "Normal",
         f"h={_inv['hierarchie_titres']} corps={_inv['style_corps']}")
verifier("gabarit : marges lues en centimetres",
         abs(_inv["mise_en_page"].get("left", 0) - 3.0) < 0.05,
         f"mep={_inv['mise_en_page']}")
verifier("gabarit : en-tete et pied reperes avec leurs champs",
         {e["role"] for e in _inv["entetes_et_pieds"]} == {"en-tete", "pied"}
         and any("PAGE" in e["champs"] for e in _inv["entetes_et_pieds"]),
         f"ep={_inv['entetes_et_pieds']}")
verifier("gabarit : l'inventaire declare ses propres lacunes",
         len(_inv["lacunes"]) >= 2, f"lac={_inv['lacunes']}")

_cmp_ok = gab.comparer(_inv, _gab_src)
verifier("gabarit : un document conforme rend le verdict conforme",
         _cmp_ok["verdict"] == "conforme" and _cmp_ok["majeurs"] == 0,
         f"v={_cmp_ok['verdict']}")
verifier("gabarit : un style declare mais non employe reste informatif",
         any(e["gravite"] == "info" for e in _cmp_ok["ecarts"]),
         f"ec={_cmp_ok['ecarts']}")
_cmp_ko = gab.comparer(_inv, os.path.join(FIXT, "document-devie.docx"))
verifier("gabarit : style hors gabarit et marge divergente sont majeurs",
         _cmp_ko["verdict"] == "ecarts majeurs" and _cmp_ko["majeurs"] == 2,
         f"v={_cmp_ko['verdict']} m={_cmp_ko['majeurs']}")
verifier("gabarit : l'ecart nomme le style fautif, pas un compte anonyme",
         any("StyleInconnu" in e["detail"] for e in _cmp_ko["ecarts"]),
         f"ec={_cmp_ko['ecarts']}")

_frag, _av_titre = gab.contenu_en_paragraphes("# Titre\n\nTexte.\n\n#### Trop bas\n", _inv)
verifier("gabarit : un niveau de titre absent retombe sur le corps, avec avis",
         any("niveau de titre 4" in a for a in _av_titre)
         and 'w:val="Heading1"' in _frag[0], f"av={_av_titre}")

import tempfile as _tf
_sortie = os.path.join(_tf.mkdtemp(), "rempli.docx")
_rap = gab.remplir(_inv, "# Introduction\n\nUn paragraphe.\n", _sortie,
                   logo=os.path.join(FIXT, "logo-ecole.png"),
                   logo_largeur_cm=5.0)
import zipfile as _zf
with _zf.ZipFile(_sortie) as _z:
    _noms = _z.namelist()
    _doc = _z.read("word/document.xml").decode("utf-8")
    _rels = _z.read("word/_rels/document.xml.rels").decode("utf-8")
    _ct = _z.read("[Content_Types].xml").decode("utf-8")
verifier("gabarit : le remplissage injecte avant la derniere section",
         _doc.index("Introduction") < _doc.index("<w:sectPr"))
verifier("gabarit : les prefixes OOXML survivent au remplissage",
         "ns0:" not in _doc and _doc.count("<w:p>") > 0)
verifier("gabarit : le logo arrive avec sa relation et son type declare",
         any("word/media/" in n for n in _noms)
         and "relationships/image" in _rels and 'Extension="png"' in _ct)
verifier("gabarit : la hauteur du logo suit le ratio du fichier",
         abs(_rap["logo"]["hauteur_cm"] - 5.0 * 400 / 1200) < 0.05,
         f"logo={_rap['logo']}")
verifier("gabarit : le document rempli reste conforme a son gabarit",
         gab.comparer(_inv, _sortie)["verdict"] == "conforme")

_inv_protege = dict(_inv, protection={"edition": "readOnly", "applique": True})
try:
    gab.remplir(_inv_protege, "# X\n", _sortie)
    _arret = False
except SystemExit:
    _arret = True
verifier("gabarit : un gabarit protege arrete le remplissage", _arret)

# Logos : registre, resolution effective, ordre protocolaire, placement
_reg = {"_racine": FIXT, "logos": [
    {"id": "ecole", "fichier": "logo-ecole.png", "rang": 1,
     "usages": ["page-garde", "en-tete"], "respiration": 0.3},
    {"id": "labo", "fichier": "logo-basse-def.png", "rang": 2,
     "usages": ["page-garde", "co-signature"]},
    {"id": "fantome", "fichier": "absent.png", "usages": ["page-garde"]},
]}
_err_l, _av_l = logo.valider(_reg)
verifier("logos : un fichier absent est une erreur, pas un avertissement",
         any("fantome" in e for e in _err_l)
         and not any("fantome" in a for a in _av_l), f"err={_err_l}")
verifier("logos : une resolution insuffisante reste consultative",
         any("dpi" in a and "labo" in a for a in _av_l), f"av={_av_l}")
verifier("logos : la resolution effective se calcule en pouces",
         abs(logo.resolution_effective(1200, 5.0) - 1200 / (5.0 / 2.54)) < 0.5)
verifier("logos : l'ordre protocolaire suit le rang, pas l'alphabet",
         [x["id"] for x in logo.pour_usage(_reg, "page-garde")][:2]
         == ["ecole", "labo"])
_html, _av_h = logo.fragment(_reg, "page-garde", "html")
verifier("logos : un logo sans fichier est ecarte du placement",
         "absent.png" not in _html and any("fantome" in a for a in _av_h),
         f"html={_html}")
_tex, _ = logo.fragment(_reg, "page-garde", "latex")
verifier("logos : le fragment latex contraint la largeur",
         "includegraphics[width=" in _tex and "cm]" in _tex, f"tex={_tex}")
_err_vide, _ = logo.valider({"_racine": FIXT, "logos": []})
verifier("logos : un registre vide est une erreur declaree",
         any("aucun logo" in e for e in _err_vide))

# Scorecard : un axe dont la precondition ne tient pas sort du calcul
_court = score.evaluer("Un texte tres court. Il tient en deux phrases propres.")
verifier("scorecard : lisibilite non evaluee sous le seuil de mots",
         _court["axes"]["Lisibilite"].get("non_evalue") is True
         and _court["axes"]["Lisibilite"]["score"] is None,
         f"ax={_court['axes']['Lisibilite']}")
verifier("scorecard : l'axe non evalue porte son motif chiffre",
         "mots" in (_court["axes"]["Lisibilite"].get("motif") or ""),
         f"motif={_court['axes']['Lisibilite'].get('motif')}")
verifier("scorecard : le total se renormalise sur les axes mesures",
         _court["total"] == 100, f"total={_court['total']}")
verifier("scorecard : un axe non evalue n'entre pas dans forces et faiblesses",
         "Lisibilite" not in _court["forces_faiblesses"]["meilleurs_axes"]
         and "Lisibilite" not in _court["forces_faiblesses"]["pires_axes"])
verifier("scorecard : le rapport texte nomme l'axe hors calcul",
         "non evalue, hors calcul" in score.rapport_texte(_court))
_long = ("Le dispositif observe repose sur une mesure repetee et datee. "
         "Les auteurs decrivent un protocole en trois etapes, chacune "
         "documentee par un releve horodate et par une photographie. "
         "La variance mesuree reste faible sur l'ensemble des series. ") * 8
_lg = score.evaluer(_long)
verifier("scorecard : au dela du seuil, la lisibilite reprend une note",
         _lg["axes"]["Lisibilite"]["score"] is not None
         and not _lg["axes"]["Lisibilite"].get("non_evalue"))
_tr_ne = score.trajectoire(_court, _lg)
verifier("scorecard : un axe non mesure d'un cote ne fabrique pas de delta",
         "Lisibilite" in _tr_ne["axes_non_mesures"]
         and all(d["axe"] != "Lisibilite" for d in _tr_ne["deltas"]),
         f"tr={_tr_ne['axes_non_mesures']}")

# Verify-sources : statut de retractation, lu hors ligne sur reponse simulee
_msg_retracte = {"title": ["Un article"], "updated-by": [
    {"type": "retraction", "DOI": "10.1000/avis",
     "updated": {"date-time": "2025-03-04T00:00:00Z"}}]}
_ret = vsrc._retractation_crossref(_msg_retracte)
verifier("verify-sources : une retractation declaree par Crossref est lue",
         _ret and _ret["statut"] == "retracte"
         and _ret["avis_doi"] == "10.1000/avis", f"ret={_ret}")
_msg_avis = {"title": ["Retraction notice"], "update-to": [
    {"type": "retraction", "DOI": "10.1000/article", "updated": {}}]}
_ret2 = vsrc._retractation_crossref(_msg_avis)
verifier("verify-sources : l'avis de retractation ne se confond pas avec "
         "l'article retracte",
         _ret2 and _ret2["statut"] == "avis de retractation", f"ret={_ret2}")
_msg_correction = {"title": ["Un article"], "updated-by": [
    {"type": "correction", "DOI": "10.1000/erratum", "updated": {}}]}
verifier("verify-sources : une simple correction n'est pas une retractation",
         vsrc._retractation_crossref(_msg_correction) is None)
verifier("verify-sources : sans declaration, le statut reste absent, pas sain",
         vsrc._retractation_crossref({"title": ["Un article"]}) is None)


# Gabarit multi-format : detection, presentations, ODF, PDF
_fmt_attendus = {
    "gabarit-ecole.docx": ("docx", "texte-ooxml"),
    "gabarit-deck.pptx": ("pptx", "diapositives-ooxml"),
    "gabarit-labo.odt": ("odt", "texte-odf"),
    "gabarit-rendu.pdf": ("pdf", "page-fixe"),
}
for _f, _attendu in sorted(_fmt_attendus.items()):
    verifier("gabarit : %s reconnu comme %s" % (_f, _attendu[1]),
             gab.detecter_format(os.path.join(FIXT, _f)) == _attendu,
             f"vu={gab.detecter_format(os.path.join(FIXT, _f))}")

_invp = gab.inventorier(os.path.join(FIXT, "gabarit-deck.pptx"))
verifier("gabarit pptx : dispositions lues par leur nom",
         {d["nom"] for d in _invp["dispositions"]}
         == {"Diapositive de titre", "Titre et contenu"},
         f"d={[d['nom'] for d in _invp['dispositions']]}")
verifier("gabarit pptx : espaces reserves types par disposition",
         any(e["type"] == "body" for d in _invp["dispositions"]
             for e in d["espaces"]))
verifier("gabarit pptx : taille de diapositive et ratio",
         _invp["mise_en_page"]["ratio"] == 1.333
         and _invp["mise_en_page"]["orientation"] == "paysage",
         f"mep={_invp['mise_en_page']}")
verifier("gabarit pptx : polices lues dans le theme de la presentation",
         "Calibri" in _invp["polices"], f"p={_invp['polices']}")
_cmp_deck = gab.comparer(_invp, os.path.join(FIXT, "deck-conforme.pptx"))
verifier("gabarit pptx : un deck conforme ne leve aucun majeur",
         _cmp_deck["majeurs"] == 0, f"v={_cmp_deck['verdict']}")
_cmp_devie = gab.comparer(_invp, os.path.join(FIXT, "deck-devie.pptx"))
verifier("gabarit pptx : une taille de diapositive divergente est majeure",
         any(e["regle"] == "mise en page divergente"
             for e in _cmp_devie["ecarts"]), f"e={_cmp_devie['ecarts']}")
verifier("gabarit pptx : une disposition non resolue est signalee",
         any(e["regle"] == "disposition non identifiable"
             for e in _cmp_devie["ecarts"]))
# Inventaire ampute : la disposition employee par le deck n'y figure plus.
_inv_ampute = dict(_invp, dispositions=[
    d for d in _invp["dispositions"] if d["nom"] != "Titre et contenu"])
_cmp_hors = gab.comparer(_inv_ampute, os.path.join(FIXT, "deck-conforme.pptx"))
verifier("gabarit pptx : une disposition hors gabarit est majeure",
         any(e["regle"] == "disposition hors gabarit"
             for e in _cmp_hors["ecarts"]), f"e={_cmp_hors['ecarts']}")

_sortie_deck = os.path.join(_tf.mkdtemp(), "deck.pptx")
_rap_deck = gab.remplir(
    _invp, "# Contexte\n\n- Un point\n- Un autre\n\n# Methode\n\nTexte.\n",
    _sortie_deck)
verifier("gabarit pptx : un titre de niveau 1 ouvre une diapositive",
         _rap_deck["diapositives"] == 2, f"r={_rap_deck}")
verifier("gabarit pptx : la disposition d'accueil porte titre et corps",
         _rap_deck["disposition"] == "Titre et contenu")
with _zf.ZipFile(_sortie_deck) as _z:
    _noms_d = _z.namelist()
    _pres = _z.read("ppt/presentation.xml").decode("utf-8")
    _s1 = _z.read("ppt/slides/slide1.xml").decode("utf-8")
    _ctd = _z.read("[Content_Types].xml").decode("utf-8")
verifier("gabarit pptx : chaque diapositive arrive avec ses quatre ecritures",
         _pres.count("<p:sldId ") == 2
         and _ctd.count("presentationml.slide+xml") == 2
         and "ppt/slides/_rels/slide1.xml.rels" in _noms_d)
verifier("gabarit pptx : les prefixes OOXML survivent au remplissage",
         "ns0:" not in _s1 and "Contexte" in _s1 and "Un point" in _s1)
verifier("gabarit pptx : le deck produit reste conforme a son gabarit",
         gab.comparer(_invp, _sortie_deck)["majeurs"] == 0)
try:
    gab.remplir(_invp, "# X\n", _sortie_deck, disposition="Inexistante")
    _refus_dispo = False
except SystemExit:
    _refus_dispo = True
verifier("gabarit pptx : une disposition demandee et absente arrete le "
         "remplissage", _refus_dispo)

_invo = gab.inventorier(os.path.join(FIXT, "gabarit-labo.odt"))
verifier("gabarit odt : styles nommes et hierarchie de titres lus",
         _invo["hierarchie_titres"].get("1") == "Heading_20_1"
         and _invo["style_corps"] == "Standard",
         f"h={_invo['hierarchie_titres']} c={_invo['style_corps']}")
verifier("gabarit odt : longueurs converties en centimetres",
         _invo["mise_en_page"]["left"] == 3.0
         and _invo["mise_en_page"]["hauteur"] == 29.7,
         f"mep={_invo['mise_en_page']}")
verifier("gabarit odt : longueur en pouces et en millimetres converties",
         gab._longueur_odf("1in") == 2.54 and gab._longueur_odf("20mm") == 2.0)
_cmp_odt = gab.comparer(_invo, os.path.join(FIXT, "document-odt-devie.odt"))
verifier("gabarit odt : style hors gabarit et marge divergente sont majeurs",
         _cmp_odt["majeurs"] == 2, f"v={_cmp_odt}")
verifier("gabarit odt : un style automatique n'est pas compte hors gabarit",
         not any("P1" in e["detail"] for e in _cmp_odt["ecarts"]))

_invpdf = gab.inventorier(os.path.join(FIXT, "gabarit-rendu.pdf"))
verifier("gabarit pdf : pages, format nomme et version lus en binaire",
         _invpdf["pages"] == 2
         and _invpdf["mise_en_page"]["format_nomme"] == "A4"
         and _invpdf["version_pdf"] == "1.4", f"inv={_invpdf['mise_en_page']}")
verifier("gabarit pdf : les marges ne sont pas inventees",
         "left" not in (_invpdf["mise_en_page"] or {})
         and any("marges" in m for m in _invpdf["lacunes"]))
_cmp_pdf = gab.comparer(_invpdf, os.path.join(FIXT, "rendu-devie.pdf"))
verifier("gabarit pdf : un format de page divergent est majeur",
         any(e["regle"] == "format de page divergent"
             for e in _cmp_pdf["ecarts"]), f"e={_cmp_pdf['ecarts']}")
verifier("gabarit pdf : une police non incorporee reste un mineur",
         any(e["regle"] == "aucune police incorporee"
             and e["gravite"] == "mineur" for e in _cmp_pdf["ecarts"]))
_invpdf_limite = dict(_invpdf, pages_max=2)
verifier("gabarit pdf : une limite de pages depassee est majeure",
         any(e["regle"] == "limite de pages depassee" for e in gab.comparer(
             _invpdf_limite, os.path.join(FIXT, "rendu-devie.pdf"))["ecarts"]))

for _inv_nr, _nom_nr in ((_invo, "odt"), (_invpdf, "pdf")):
    verifier("gabarit %s : le remplissage est refuse avec son motif" % _nom_nr,
             _inv_nr["remplissable"] is False
             and bool(_inv_nr.get("motif_non_remplissable")))
try:
    gab.remplir(_invpdf, "# X\n", os.path.join(_tf.mkdtemp(), "x.pdf"))
    _refus_pdf = False
except SystemExit:
    _refus_pdf = True
verifier("gabarit pdf : remplir un PDF s'arrete plutot que d'approximer",
         _refus_pdf)
try:
    gab.comparer(_invp, os.path.join(FIXT, "gabarit-ecole.docx"))
    _refus_croise = False
except SystemExit:
    _refus_croise = True
verifier("gabarit : comparer deux familles differentes est refuse",
         _refus_croise)


# Modules de cas ranges dans evals/cas/. Le harnais grossit par fichier plutot
# que par lignes ajoutees a celui-ci : chaque module recoit verifier et les
# aides communes, et n'a ni chargement ni resume propres.
def _charger_modules_de_cas():
    dossier = os.path.join(ICI, "cas")
    if not os.path.isdir(dossier):
        return []
    charges = []
    espace_commun = {
        "verifier": verifier, "charger": charger, "lire": lire,
        "ICI": ICI, "SCRIPTS": SCRIPTS, "FIXT": FIXT, "RACINE": RACINE,
    }
    for nom in sorted(os.listdir(dossier)):
        if not nom.endswith(".py") or nom.startswith("_"):
            continue
        chemin = os.path.join(dossier, nom)
        espace = dict(espace_commun)
        espace["__file__"] = chemin
        with open(chemin, encoding="utf-8") as f:
            code = compile(f.read(), chemin, "exec")
        exec(code, espace)
        charges.append(nom)
    return charges


MODULES_DE_CAS = _charger_modules_de_cas()


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
