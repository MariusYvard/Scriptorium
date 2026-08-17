# -*- coding: utf-8 -*-
"""Regenere les fixtures PDF de emprunts.py.

Meme principe que generer-pdf.py, dont l'ecriture de PDF minimal est reprise
par import de chemin plutot que recopiee : le contenu exact des fixtures
reste lisible et modifiable ici, sans dependance.

Ecrit un PDF de trois pages qui porte des legendes de figure dans son texte :
une legende seule en page 1, deux legendes en page 2, aucune en page 3. Les
evaluations simulent les backends d'extraction, mais le fichier reste un PDF
valide sur le disque, pour que les chemins qui verifient l'existence et
l'en-tete du fichier travaillent sur un vrai fichier.

Usage : python3 generer-pdf-emprunts.py [DOSSIER]
"""
import importlib.util
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))


def _charger_generateur():
    spec = importlib.util.spec_from_file_location(
        "generer_pdf_base", os.path.join(ICI, "generer-pdf.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PAGES = [
    ["Resultats de la campagne de mesure",
     "Figure 1. Courbe de charge du reseau mesuree sur douze mois"],
    ["Figure 2. Distribution des masses relevees au banc",
     "Figure 3. Detail du montage optique en configuration nominale"],
    ["Discussion generale sans aucune legende de figure sur cette page"],
]


def _flux_page(lignes):
    """Contenu d'une page : une ligne de texte par legende ou paragraphe."""
    morceaux = ["BT /F1 12 Tf 72 720 Td 14 TL"]
    for i, ligne in enumerate(lignes):
        propre = ligne.replace("(", "").replace(")", "")
        morceaux.append("%s(%s) Tj" % ("T* " if i else "", propre))
    morceaux.append("ET")
    return " ".join(morceaux).encode("ascii")


def construire(nb_pages):
    """Dictionnaire d'objets d'un PDF de nb_pages pages, textes de PAGES."""
    premier_page = 3
    premier_flux = premier_page + nb_pages
    police = premier_flux + nb_pages
    kids = " ".join("%d 0 R" % (premier_page + i) for i in range(nb_pages))
    objets = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: ("<< /Type /Pages /Kids [%s] /Count %d >>"
            % (kids, nb_pages)).encode("ascii"),
        police: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    }
    return objets, premier_page, premier_flux, police


def main(dest=ICI):
    base = _charger_generateur()
    if not os.path.isdir(dest):
        os.makedirs(dest)
    nb = len(PAGES)
    objets, premier_page, premier_flux, police = construire(nb)
    for i, lignes in enumerate(PAGES):
        objets[premier_page + i] = (
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            "/Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>"
            % (police, premier_flux + i)).encode("ascii")
        objets[premier_flux + i] = base._obj_stream(_flux_page(lignes))
    chemin = os.path.join(dest, "pdf-emprunts.pdf")
    base.ecrire_pdf(chemin, objets)
    print("fixture ecrite : %s (%d pages)" % (chemin, nb))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ICI))
