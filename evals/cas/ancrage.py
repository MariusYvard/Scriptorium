# -*- coding: utf-8 -*-
"""Cas d'eval de l'ancrage de citation a trois couches (couches 2 et 3).

Couvre la qualification des types d'ancre (citation, page, structure,
horodatage, defauts nommes) et l'audit de fidelite entre une affirmation
du texte et l'annotation bibtex qui la soutient.
"""

cita = charger("citations.py", "citations")

Q = '"'  # guillemet droit, evite les soucis d'echappement ci-dessous

# --- Couche 2 : types d'ancre reconnus ---

verifier("couche2 : citation exacte reconnue",
         cita.qualifier_ancre(Q + "la reforme a reduit le chomage local" + Q)["type"] == "citation")

verifier("couche2 : page simple reconnue",
         cita.qualifier_ancre("p. 12")["type"] == "page")

verifier("couche2 : plage de pages reconnue",
         cita.qualifier_ancre("pp. 12-15")["type"] == "page")

verifier("couche2 : localisation structurelle reconnue (section)",
         cita.qualifier_ancre("section 3.2")["type"] == "structure")

verifier("couche2 : localisation structurelle reconnue (annexe)",
         cita.qualifier_ancre("annexe B")["type"] == "structure")

verifier("couche2 : horodatage reconnu",
         cita.qualifier_ancre("12:34")["type"] == "horodatage")

verifier("couche2 : ancre absente",
         cita.qualifier_ancre("")["type"] == "aucune")

# --- Couche 2 : formes malformees attrapees comme defaut nomme ---

r_page0 = cita.qualifier_ancre("p. 0")
verifier("couche2 : page nulle est un defaut, pas une ancre valide",
         r_page0["type"] == "defaut" and r_page0["defaut"] == "page_invalide", str(r_page0))

r_inv = cita.qualifier_ancre("pp. 20-12")
verifier("couche2 : plage inversee est un defaut",
         r_inv["type"] == "defaut" and r_inv["defaut"] == "plage_inversee", str(r_inv))

longue = Q + " ".join(["mot"] * 30) + Q
r_longue = cita.qualifier_ancre(longue)
verifier("couche2 : citation de plus de 25 mots est un defaut (emprunt, pas une ancre)",
         r_longue["type"] == "defaut" and r_longue["defaut"] == "citation_trop_longue",
         str(r_longue))

r_nf = cita.qualifier_ancre(Q + "citation jamais refermee")
verifier("couche2 : guillemets non fermes sont un defaut",
         r_nf["type"] == "defaut" and r_nf["defaut"] == "guillemets_non_fermes", str(r_nf))

# --- Couche 3 : signaux mecaniques ---

bib_force = """@article{etude2024,
  author = {Nguyen, Thi},
  title = {Effet observe sur un echantillon restreint},
  journal = {Revue X},
  year = {2024},
  annote = {"dans cet echantillon, l'effet suggere une amelioration"}
}
"""
ent_force = cita.parser_bibtex(bib_force)
doc_force = "Cette etude demontre que l'effet est toujours present. [etude2024]"
rap_force = cita.auditer_fidelite(doc_force, ent_force)
verifier("couche3 : montee en force detectee (ancre prudente, affirmation forte)",
         len(rap_force) == 1
         and any(s["signal"] == "montee_en_force" for s in rap_force[0]["signaux"]),
         str(rap_force))

bib_chiffre = """@article{chiffres2023,
  author = {Martin, Paul},
  title = {Mesure d'un taux},
  journal = {Revue Y},
  year = {2023},
  annote = {"le taux observe est de 3,2 points sur cet echantillon"}
}
"""
ent_chiffre = cita.parser_bibtex(bib_chiffre)
doc_chiffre = "Le taux a atteint 12 points en 2025 selon cette mesure. [chiffres2023]"
rap_chiffre = cita.auditer_fidelite(doc_chiffre, ent_chiffre)
verifier("couche3 : chiffre orphelin detecte (nombre absent de l'ancre)",
         len(rap_chiffre) == 1
         and any(s["signal"] == "chiffre_orphelin" for s in rap_chiffre[0]["signaux"]),
         str(rap_chiffre))

bib_general = """@article{general2022,
  author = {Dupont, Marie},
  title = {Resultat localise},
  journal = {Revue Z},
  year = {2022},
  annote = {"chez les patients de cet echantillon, le traitement fonctionne"}
}
"""
ent_general = cita.parser_bibtex(bib_general)
doc_general = "Ce traitement fonctionne systematiquement, dans tous les cas. [general2022]"
rap_general = cita.auditer_fidelite(doc_general, ent_general)
verifier("couche3 : generalisation retiree detectee (portee de l'ancre non reprise)",
         len(rap_general) == 1
         and any(s["signal"] == "generalisation_retiree" for s in rap_general[0]["signaux"]),
         str(rap_general))

# --- Couche 3 : cas negatifs (aucun signal ne doit se declencher a tort) ---

bib_ok = """@article{fidele2024,
  author = {Petit, Anne},
  title = {Resultat fidelement rapporte},
  journal = {Revue A},
  year = {2024},
  annote = {"dans cet echantillon, le taux atteint 3,2 points"}
}
"""
ent_ok = cita.parser_bibtex(bib_ok)
doc_ok = ("Dans cet echantillon, le taux atteint 3,2 points selon cette mesure. "
          "[fidele2024]")
rap_ok = cita.auditer_fidelite(doc_ok, ent_ok)
verifier("couche3 negatif : affirmation fidele ne declenche aucun signal",
         len(rap_ok) == 1 and rap_ok[0]["signaux"] == [], str(rap_ok))

r_page_ok = cita.qualifier_ancre("pp. 12-15")
verifier("couche2 negatif : ancre correcte (plage valide) ne devient pas un defaut",
         r_page_ok["type"] == "page" and "defaut" not in r_page_ok, str(r_page_ok))
