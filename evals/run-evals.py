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
