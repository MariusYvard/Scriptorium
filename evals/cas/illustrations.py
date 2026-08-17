# -*- coding: utf-8 -*-
"""Cas d'eval de la chaine des illustrations.

Trois garde-fous y sont eprouves ensemble. Le catalogue d'un dossier
d'illustrations deja produites (mesure, doublon par empreinte, verdict de
resolution a la largeur d'insertion prevue), la conversion SVG vers PNG a
backends optionnels (une absence de backend ne doit jamais passer pour un
fichier fautif) et le contrat de passation vers le redacteur (glossaire et
objets numerotes transportes explicitement).

Les cas negatifs comptent autant que les positifs : une illustration
suffisamment definie, une illustration juste au seuil et un fichier
vectoriel ne doivent declencher aucun signalement.
"""
import json
import os
import shutil
import struct
import tempfile

imgs = charger("images.py", "images")
logo = charger("logos.py", "logos")
proj = charger("project.py", "project")


def png(largeur, hauteur):
    """PNG minimal : en-tete IHDR aux dimensions voulues, sans donnee d'image.

    Le catalogue lit les dimensions dans l'en-tete, jamais les pixels : un
    IHDR suffit a eprouver la mesure, et les octets varient avec les
    dimensions donc l'empreinte distingue deux fichiers differents.
    """
    ihdr = b"IHDR" + struct.pack(">II", largeur, hauteur) + b"\x08\x06\x00\x00\x00"
    return (b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + ihdr
            + b"\x00\x00\x00\x00" + b"\x00\x00\x00\x00IEND\xaeB`\x82")


SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50">'
       '<rect width="100" height="50" fill="#16314E"/></svg>')

DOSSIER = tempfile.mkdtemp(prefix="scriptorium_illus_")


def poser(nom, contenu):
    chemin = os.path.join(DOSSIER, nom)
    mode = "wb" if isinstance(contenu, bytes) else "w"
    with open(chemin, mode) as f:
        f.write(contenu)
    return chemin


# Dossier en vrac : photo de dispositif nette (2400 px), capture d'ecran
# juste au-dessus du seuil (1772 px a 15 cm rendent 300 dpi), schema
# vectoriel, note de travail, capture trop faible (600 px), et le doublon
# exact de la photo nette.
poser("photo-banc.png", png(2400, 1600))
poser("capture-interface.png", png(1772, 900))
poser("schema-principe.svg", SVG)
poser("notes-prise-de-vue.txt", "releve du 12 mars")
poser("capture-oscillo.png", png(600, 400))
# Le doublon porte un nom qui passe apres l'original dans l'ordre du dossier :
# le catalogue retient le premier rencontre et rattache les suivants a lui.
poser("z-photo-banc-doublon.png", png(2400, 1600))

CAT = imgs.cataloguer(DOSSIER, largeur_cm=15.0, usage="impression")


def entree(nom, catalogue=None):
    for i in (catalogue or CAT)["illustrations"]:
        if i["fichier"] == nom:
            return i
    return {}


# --- Catalogue d'un dossier d'illustrations deja produites -----------------

verifier("catalogue : le dossier en vrac est inventorie en entier",
         len(CAT["illustrations"]) == 6, f"n={len(CAT['illustrations'])}")

verifier("catalogue : les dimensions sont lues dans l'en-tete du fichier",
         entree("photo-banc.png")["largeur"] == 2400
         and entree("photo-banc.png")["hauteur"] == 1600,
         str(entree("photo-banc.png")))

verifier("catalogue : le manifeste ecrit tient la liste des figures",
         os.path.isfile(os.path.join(DOSSIER, "catalogue.json"))
         and all(set(("fichier", "format", "sha1", "verdict", "dpi_effectif"))
                 <= set(i) for i in json.load(
                     open(os.path.join(DOSSIER, "catalogue.json"),
                          encoding="utf-8"))["illustrations"]))

# --- Doublon par empreinte -------------------------------------------------

verifier("catalogue : le doublon exact est reconnu par son empreinte et ne "
         "gonfle pas le compte",
         entree("z-photo-banc-doublon.png")["verdict"] == "doublon"
         and entree("z-photo-banc-doublon.png")["doublon_de"] == "photo-banc.png"
         and CAT["count"] == 5 and CAT["doublons"] == 1,
         f"{entree('z-photo-banc-doublon.png')} count={CAT['count']}")

# --- Seuil d'impression : ce qui est attrape -------------------------------

verifier("catalogue : la capture sous-definie est attrapee, avec la largeur "
         "maximale qui tiendrait",
         entree("capture-oscillo.png")["verdict"] == "sous le seuil"
         and entree("capture-oscillo.png")["dpi_effectif"] < 300
         and abs(entree("capture-oscillo.png")["largeur_cm_max"] - 5.08) < 0.02
         and CAT["sous_le_seuil"] == 1,
         str(entree("capture-oscillo.png")))

# --- Seuil d'impression : ce qui ne doit rien declencher -------------------

verifier("catalogue : la photo nette n'est pas signalee",
         entree("photo-banc.png")["verdict"] == "utilisable",
         str(entree("photo-banc.png")))

verifier("catalogue : une illustration juste au seuil n'est pas signalee",
         entree("capture-interface.png")["verdict"] == "utilisable"
         and entree("capture-interface.png")["dpi_effectif"] >= 300,
         str(entree("capture-interface.png")))

verifier("catalogue : ni le vectoriel ni le fichier non-image ne deviennent "
         "des alertes de resolution",
         entree("schema-principe.svg")["verdict"] == "vecteur, resolution sans objet"
         and entree("schema-principe.svg")["dpi_effectif"] is None
         and entree("notes-prise-de-vue.txt")["verdict"] == "hors perimetre"
         and all(i["verdict"] in imgs.VERDICTS for i in CAT["illustrations"]),
         str(entree("schema-principe.svg")))

# La meme capture devient insuffisante sur une double page : le verdict tient
# a la largeur d'insertion prevue, pas au seul fichier.
CAT_LARGE = imgs.cataloguer(DOSSIER, largeur_cm=25.0, usage="impression",
                            out=os.path.join(DOSSIER, "catalogue-large.json"))
verifier("catalogue : le verdict suit la largeur d'insertion, pas le fichier "
         "seul",
         entree("capture-interface.png", CAT_LARGE)["verdict"] == "sous le seuil",
         str(entree("capture-interface.png", CAT_LARGE)))

# logos.py charge son propre exemplaire de images.py par chemin, distinct de
# celui du harnais : l'identite des objets ne dit donc rien. Ce qui compte est
# que le code execute vienne bien du fichier images.py, seule copie du calcul.
verifier("resolution : logos.py mesure avec le code de images.py, pas une "
         "seconde copie",
         os.path.basename(logo.resolution_effective.__code__.co_filename)
         == "images.py"
         and logo.DPI_IMPRESSION == imgs.DPI_IMPRESSION
         and logo.resolution_effective(1200, 5.0)
         == imgs.resolution_effective(1200, 5.0),
         logo.resolution_effective.__code__.co_filename)

# --- Conversion SVG vers PNG : degradation propre --------------------------

_svg = poser("figure-a-convertir.svg", SVG)
_sortie = os.path.join(DOSSIER, "figure-a-convertir.png")

_vrais_backends = imgs.backends_svg_disponibles
imgs.backends_svg_disponibles = lambda: []
RAP_SANS = imgs.convertir(_svg, _sortie)
RAP_ABSENT = imgs.convertir(os.path.join(DOSSIER, "jamais-ecrit.svg"), _sortie)
imgs.backends_svg_disponibles = _vrais_backends

verifier("conversion : sans backend, le statut est nomme et aucun PNG douteux "
         "n'est ecrit",
         RAP_SANS["statut"] == "aucun-backend" and not os.path.isfile(_sortie),
         str(RAP_SANS["statut"]))

verifier("conversion : sans backend, le fichier source n'est pas mis en cause "
         "et l'installation est expliquee",
         any("source n'est pas en cause" in n for n in RAP_SANS["notes"])
         and any("cairosvg" in n and "rsvg" in n for n in RAP_SANS["notes"]),
         str(RAP_SANS["notes"]))

verifier("conversion : une source absente ne se confond pas avec une absence "
         "de backend",
         RAP_ABSENT["statut"] == "source-absente", str(RAP_ABSENT["statut"]))

verifier("conversion : convert.exe de Windows n'est jamais pris pour "
         "ImageMagick",
         "convert" not in imgs.backends_svg_disponibles()
         or imgs._est_imagemagick("convert"))

# --- Passation vers le redacteur : glossaire et objets numerotes -----------

PROJ = proj.charger(os.path.join(DOSSIER, "projet-inexistant.json"))
PROJ["genre"] = "memoire-recherche"
PROJ["glossaire"] = {"banc d'essai": "montage instrumente decrit en 2.1",
                     "taux de conversion": "rapport molaire, jamais massique"}
proj.enregistrer_objet(PROJ, "figure", 1, "Schema du banc d'essai")
proj.enregistrer_objet(PROJ, "figure", 2, "Courbe de conversion")
proj.enregistrer_objet(PROJ, "tableau", 1, "Conditions operatoires")

PASS = proj.passation_redacteur(PROJ)

verifier("passation : le glossaire voyage entier vers le redacteur, jusque "
         "dans le texte a coller dans son prompt",
         PASS["glossaire"] == PROJ["glossaire"]
         and "banc d'essai" in proj.passation_texte(PASS),
         str(PASS["glossaire"]))

verifier("passation : la liste des figures et tableaux voyage avec le "
         "prochain numero libre par type",
         len(PASS["objets_numerotes"]) == 3
         and PASS["prochains_numeros"]["figure"] == 3
         and PASS["prochains_numeros"]["tableau"] == 2
         and PASS["prochains_numeros"]["equation"] == 1
         and "figure 2" in proj.passation_texte(PASS),
         str(PASS["prochains_numeros"]))

try:
    proj.enregistrer_objet(PROJ, "figure", 2, "Une autre figure")
    _conflit = False
except ValueError:
    _conflit = True
verifier("passation : un numero deja pris par un autre objet est refuse",
         _conflit)

# Compatibilite de lecture : un projet.json ecrit avant ce champ se lit sans
# erreur et la passation part quand meme, vide plutot qu'absente.
_ancien = os.path.join(DOSSIER, "projet-ancien.json")
with open(_ancien, "w", encoding="utf-8") as f:
    json.dump({"titre": "Ancien projet", "genre": "rapport-technique",
               "sources": []}, f)
_relu = proj.charger(_ancien)
verifier("passation : un projet.json sans le champ se lit sans casser",
         _relu["objets_numerotes"] == []
         and proj.passation_redacteur(_relu)["prochains_numeros"]["figure"] == 1,
         str(_relu.get("objets_numerotes")))

shutil.rmtree(DOSSIER, ignore_errors=True)
