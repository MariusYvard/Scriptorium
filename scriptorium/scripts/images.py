#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extraction et inventaire d'images depuis un PDF ou un document Office.

Coeur deterministe (bibliotheque standard) : ouvre les fichiers Office comme
des ZIP et en sort les medias, lit les dimensions dans l'en-tete, deduplique
par empreinte, ecrit un manifeste JSON. Pour le PDF, essaie des backends
optionnels (PyMuPDF, pdfimages, pypdf) puis, a defaut, indique de passer par
le skill pdf. Aucune image n'est interpretee ici : l'alt et la legende sont
ecrits par le modele a l'etape de placement.

Catalogue un dossier d'illustrations deja produites (photos de dispositif,
captures d'ecran, schemas faits ailleurs) avec les memes mesures que
l'extraction : dimensions lues dans l'en-tete, empreinte, doublons, plus la
resolution effective a la largeur d'insertion prevue et un verdict par
illustration. Convertit aussi un SVG en PNG par backends optionnels en
cascade, sans qu'aucun devienne une dependance obligatoire.

Ce module porte le calcul de resolution effective pour tout le plugin :
logos.py le reprend ici plutot que d'en tenir une seconde copie.

Le manifeste d'extraction et le catalogue ECRITS sur le disque restent
francais : ce sont des donnees, relues plus tard par un autre outil ou une
autre session, et un fichier dont les notes changeraient de langue selon la
commande qui l'a produit ne se comparerait plus a lui-meme. Seule leur
restitution a l'ecran suit --langue-affichage, et les notes affichees sont
composees a partir des memes mesures que celles ecrites.

Usage :
    python3 images.py extract SOURCE --out DIR [--min-bytes N]
    python3 images.py manifest DIR
    python3 images.py catalogue DIR [--out FICHIER] [--largeur-cm N]
                      [--usage impression|ecran] [--format text|json]
                      [--langue-affichage fr|en]
    python3 images.py convertir FIGURE.svg --out FIGURE.png [--largeur-px N]
                      [--format text|json] [--langue-affichage fr|en]

Importable : extract(source, outdir, min_bytes), extraire_office(path, outdir),
dimensions(data) -> (largeur, hauteur, format), construire(items, outdir, min_bytes),
resolution_effective(pixels, largeur_cm), seuil_dpi(usage),
cataloguer(dossier, largeur_cm, usage),
catalogue_texte(cat, langue_affichage=None),
convertir(source, sortie, largeur_px, langue_affichage=None),
backends_svg_disponibles().
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import zipfile

_LIB = None


def _lib():
    """Charge libelles.py par son chemin, une seule fois : le module se lit
    par chemin, aucun sys.path n'est garanti."""
    global _LIB
    if _LIB is None:
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "libelles.py")
        spec = importlib.util.spec_from_file_location("scriptorium_libelles",
                                                      chemin)
        _LIB = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_LIB)
    return _LIB


OFFICE = (".docx", ".pptx", ".xlsx", ".docm", ".pptm", ".xlsm", ".odt", ".odp", ".ods")
RASTER = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff"}
VECTOR = {".emf", ".wmf", ".svg", ".eps"}

# Seuils consultatifs de resolution effective, en points par pouce. Source
# unique pour le plugin : un logo, une photo de dispositif et une capture
# d'ecran se mesurent avec la meme regle.
DPI_IMPRESSION = 300
DPI_ECRAN = 150
POUCE_CM = 2.54

# Largeur d'insertion par defaut, en centimetres : une figure sur toute la
# justification d'une page A4 a marges de 3 cm.
LARGEUR_INSERTION_CM = 15.0

# Verdicts fermes du catalogue : un fichier en recoit un et un seul.
VERDICTS = ("utilisable", "sous le seuil", "doublon", "dimensions illisibles",
            "vecteur, resolution sans objet", "hors perimetre")


def sha1(b):
    return hashlib.sha1(b).hexdigest()


def resolution_effective(pixels, largeur_cm):
    """Points par pouce reels a la taille d'insertion demandee.

    Une image de 1200 pixels de large inseree sur 5 cm rend 610 dpi, la meme
    inseree sur 15 cm en rend 203 : la resolution n'est pas une propriete du
    fichier, elle depend de la taille a laquelle il est pose sur la page.
    Renvoie None quand une des deux grandeurs manque, plutot qu'un zero qui
    passerait pour une mesure.
    """
    if not pixels or not largeur_cm:
        return None
    return pixels / (largeur_cm / POUCE_CM)


def seuil_dpi(usage):
    """Seuil consultatif pour un usage : impression ou ecran."""
    return DPI_IMPRESSION if usage == "impression" else DPI_ECRAN


def dimensions(data):
    """Largeur, hauteur, format lus dans l'en-tete, ou (None, None, fmt|None)."""
    try:
        if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
            w, h = struct.unpack(">II", data[16:24])
            return w, h, "png"
        if data[:6] in (b"GIF87a", b"GIF89a"):
            w, h = struct.unpack("<HH", data[6:10])
            return w, h, "gif"
        if data[:2] == b"BM":
            w, h = struct.unpack("<ii", data[18:26])
            return abs(w), abs(h), "bmp"
        if data[:2] == b"\xff\xd8":
            i, n = 2, len(data)
            while i + 9 < n:
                if data[i] != 0xFF:
                    i += 1
                    continue
                m = data[i + 1]
                if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                    h, w = struct.unpack(">HH", data[i + 5:i + 9])
                    return w, h, "jpeg"
                if m == 0xD8 or m == 0xD9 or 0xD0 <= m <= 0xD7:
                    i += 2
                    continue
                seg = struct.unpack(">H", data[i + 2:i + 4])[0]
                i += 2 + seg
            return None, None, "jpeg"
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            fmt = data[12:16]
            if fmt == b"VP8X":
                w = 1 + (data[24] | data[25] << 8 | data[26] << 16)
                h = 1 + (data[27] | data[28] << 8 | data[29] << 16)
                return w, h, "webp"
            if fmt == b"VP8 ":
                w = struct.unpack("<H", data[26:28])[0] & 0x3FFF
                h = struct.unpack("<H", data[28:30])[0] & 0x3FFF
                return w, h, "webp"
            if fmt == b"VP8L":
                b1, b2, b3, b4 = data[21], data[22], data[23], data[24]
                w = 1 + (((b2 & 0x3F) << 8) | b1)
                h = 1 + (((b4 & 0x0F) << 10) | (b3 << 2) | ((b2 & 0xC0) >> 6))
                return w, h, "webp"
            return None, None, "webp"
    except Exception:
        return None, None, None
    return None, None, None


def _ext(name):
    return os.path.splitext(name)[1].lower()


def _classer(ext):
    """Famille d'un fichier d'apres son extension : vecteur, raster, autre."""
    if ext in VECTOR:
        return "vecteur"
    if ext in RASTER:
        return "raster"
    return "autre"


def extraire_office(path, outdir):
    """Medias d'un fichier Office ou ODF (zip). Retourne [(nom_origine, octets)]."""
    items = []
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            n = info.filename
            low = n.lower()
            if n.endswith("/"):
                continue
            if "/media/" in low or low.startswith("media/") or "/pictures/" in low:
                items.append((n, z.read(info)))

    def key(it):
        base = os.path.basename(it[0]).lower()
        m = re.search(r"(\d+)", base)
        return (int(m.group(1)) if m else 0, base)

    items.sort(key=key)
    return items


def _have(cmd):
    return shutil.which(cmd) is not None


def extraire_pdf(path, outdir):
    """Essaie les backends PDF. Retourne ([(nom, octets)], backend) ou ([], None)."""
    try:
        import fitz
        out, doc = [], __import__("fitz").open(path)
        for pi in range(len(doc)):
            for ii, img in enumerate(doc.get_page_images(pi)):
                d = doc.extract_image(img[0])
                out.append((f"p{pi + 1:03d}-{ii + 1:02d}.{d['ext']}", d["image"]))
        return out, "pymupdf"
    except ImportError:
        pass
    except Exception:
        pass
    if _have("pdfimages"):
        try:
            os.makedirs(outdir, exist_ok=True)
            pref = os.path.join(outdir, "_pdfimg")
            subprocess.run(["pdfimages", "-all", path, pref], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            out = []
            for fn in sorted(os.listdir(outdir)):
                if fn.startswith("_pdfimg"):
                    p = os.path.join(outdir, fn)
                    with open(p, "rb") as f:
                        out.append((fn, f.read()))
                    os.remove(p)
            return out, "pdfimages"
        except Exception:
            pass
    try:
        from pypdf import PdfReader
        out = []
        for pi, page in enumerate(PdfReader(path).pages):
            for ii, im in enumerate(page.images):
                out.append((f"p{pi + 1:03d}-{ii + 1:02d}-{im.name}", im.data))
        return out, "pypdf"
    except ImportError:
        pass
    except Exception:
        pass
    return [], None


def construire(items, outdir, min_bytes=1024):
    """Ecrit les images uniques, deduplique, mesure. Retourne (images, skipped)."""
    os.makedirs(outdir, exist_ok=True)
    seen, images, skipped, idx = {}, [], [], 0
    for order, (origine, data) in enumerate(items, 1):
        ext = _ext(origine) or ".bin"
        h = sha1(data)
        if h in seen:
            images.append({"index": seen[h]["index"], "doublon_de": seen[h]["fichier"],
                           "ordre": order, "octets": len(data), "sha1": h, "origine": origine})
            continue
        kind = _classer(ext)
        if len(data) < min_bytes and kind != "vecteur":
            skipped.append({"origine": origine, "octets": len(data), "raison": "micro-image"})
            continue
        idx += 1
        fichier = f"img-{idx:03d}{ext}"
        with open(os.path.join(outdir, fichier), "wb") as f:
            f.write(data)
        w = ht = None
        fmt = ext.lstrip(".")
        flags = []
        if kind == "raster":
            w, ht, det = dimensions(data)
            if det:
                fmt = det
            if w == 1 and ht == 1:
                flags.append("espaceur-1x1")
            if w is None:
                flags.append("dimensions-inconnues")
        elif kind == "vecteur":
            flags.append("vecteur-a-convertir")
        rec = {"index": idx, "fichier": fichier, "format": fmt, "type": kind,
               "largeur": w, "hauteur": ht, "octets": len(data), "sha1": h,
               "ordre": order, "origine": origine, "flags": flags}
        seen[h] = rec
        images.append(rec)
    return images, skipped


def extract(source, outdir, min_bytes=1024):
    ext = _ext(source)
    backend = "office-zip"
    if ext in OFFICE:
        items = extraire_office(source, outdir)
    elif ext == ".pdf":
        items, backend = extraire_pdf(source, outdir)
        if backend is None:
            return {"source": os.path.basename(source), "type": "pdf", "backend": None,
                    "count": 0, "doublons": 0, "images": [], "skipped": [],
                    "notes": ["Aucun backend PDF (PyMuPDF, pdfimages, pypdf). "
                              "Extraire les images avec le skill pdf."]}
    else:
        return {"source": os.path.basename(source), "type": ext.lstrip("."), "backend": None,
                "count": 0, "doublons": 0, "images": [], "skipped": [],
                "notes": [f"Format non gere : {ext}. Gerer .docx .pptx .xlsx .pdf et ODF."]}
    images, skipped = construire(items, outdir, min_bytes)
    uniques = [i for i in images if "doublon_de" not in i]
    notes = []
    if any("vecteur-a-convertir" in i.get("flags", []) for i in uniques):
        notes.append("Images vectorielles (EMF/WMF) presentes : convertir avant analyse.")
    manifest = {"source": os.path.basename(source), "type": ext.lstrip("."), "backend": backend,
                "count": len(uniques), "doublons": sum(1 for i in images if "doublon_de" in i),
                "images": images, "skipped": skipped, "notes": notes}
    with open(os.path.join(outdir, "manifest.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return manifest


def _notes_catalogue(faibles, seuil, largeur_cm, illustrations, la):
    """Notes du catalogue, source unique pour le fichier ecrit et pour
    l'ecran.

    Le fichier les recoit en francais (la="fr"), l'ecran dans la langue
    demandee : une seule fonction, donc le francais du fichier et celui du
    rapport ne peuvent pas diverger."""
    lib = _lib()
    notes = []
    if faibles:
        notes.append(lib.t("images.n.sous_seuil", la, n=len(faibles),
                           seuil=seuil, largeur=largeur_cm))
    if any("vecteur-a-convertir" in i["flags"] for i in illustrations):
        notes.append(lib.t("images.n.vecteur", la))
    if any(i["verdict"] == "dimensions illisibles" for i in illustrations):
        notes.append(lib.t("images.n.illisible", la))
    return notes


def cataloguer(dossier, largeur_cm=LARGEUR_INSERTION_CM, usage="impression",
               out=None, recursif=False, langue_affichage=None):
    """Catalogue un dossier d'illustrations deja produites.

    Meme mecanique que l'extraction (dimensions lues dans l'en-tete, empreinte
    sha1, drapeaux) appliquee a des fichiers deja sur le disque : photos de
    dispositif, captures d'ecran, schemas faits ailleurs. Chaque entree recoit
    en plus la resolution effective a LARGEUR_CM et un verdict ferme pris dans
    VERDICTS. Ecrit le catalogue en JSON et le retourne.

    Le catalogue ecrit est en FRANCAIS quoi qu'il arrive, verdicts, motifs
    d'exclusion et notes compris : c'est un fichier de donnees, relu plus tard
    par une autre commande. langue_affichage ne sert qu'au message d'arret
    quand le dossier n'existe pas, la seule chaine de cette fonction qui parte
    a l'ecran plutot que sur le disque.
    """
    if not os.path.isdir(dossier):
        lib = _lib()
        raise SystemExit(lib.t("images.err_dossier",
                               lib.resoudre_affichage(langue_affichage),
                               dossier=dossier))
    seuil = seuil_dpi(usage)
    chemins = []
    if recursif:
        for base, _sous, noms in os.walk(dossier):
            chemins.extend(os.path.join(base, n) for n in sorted(noms))
    else:
        chemins = [os.path.join(dossier, n) for n in sorted(os.listdir(dossier))]
    vus, illustrations, ignores, idx = {}, [], [], 0
    for chemin in chemins:
        if not os.path.isfile(chemin):
            continue
        nom = os.path.relpath(chemin, dossier).replace("\\", "/")
        if os.path.basename(nom) in ("manifest.json", "catalogue.json"):
            continue
        try:
            with open(chemin, "rb") as f:
                data = f.read()
        except OSError:
            ignores.append({"fichier": nom, "raison": "fichier illisible"})
            continue
        ext = _ext(chemin)
        kind = _classer(ext)
        idx += 1
        rec = {"index": idx, "fichier": nom,
               "format": ext.lstrip(".") or "sans-extension", "type": kind,
               "largeur": None, "hauteur": None, "octets": len(data),
               "sha1": sha1(data), "largeur_cm": largeur_cm,
               "dpi_effectif": None, "flags": [], "verdict": None}
        if rec["sha1"] in vus:
            rec["doublon_de"] = vus[rec["sha1"]]
            rec["verdict"] = "doublon"
            illustrations.append(rec)
            continue
        vus[rec["sha1"]] = nom
        if kind == "autre":
            rec["flags"].append("format-non-image")
            rec["verdict"] = "hors perimetre"
            illustrations.append(rec)
            continue
        if kind == "vecteur":
            rec["flags"].append("vecteur-a-convertir")
            rec["verdict"] = "vecteur, resolution sans objet"
            illustrations.append(rec)
            continue
        larg, haut, det = dimensions(data)
        if det:
            rec["format"] = det
        rec["largeur"], rec["hauteur"] = larg, haut
        if larg == 1 and haut == 1:
            rec["flags"].append("espaceur-1x1")
        if not larg:
            rec["flags"].append("dimensions-inconnues")
            rec["verdict"] = "dimensions illisibles"
            illustrations.append(rec)
            continue
        dpi = resolution_effective(larg, largeur_cm)
        rec["dpi_effectif"] = round(dpi)
        rec["largeur_cm_max"] = round(larg / (seuil / POUCE_CM), 2)
        rec["verdict"] = "sous le seuil" if dpi < seuil else "utilisable"
        illustrations.append(rec)
    uniques = [i for i in illustrations if "doublon_de" not in i]
    faibles = [i for i in illustrations if i["verdict"] == "sous le seuil"]
    notes = _notes_catalogue(faibles, seuil, largeur_cm, illustrations, "fr")
    catalogue = {
        "dossier": os.path.abspath(dossier), "usage": usage,
        "largeur_cm": largeur_cm, "seuil_dpi": seuil,
        "count": len(uniques),
        "doublons": sum(1 for i in illustrations if "doublon_de" in i),
        "sous_le_seuil": len(faibles), "illustrations": illustrations,
        "ignores": ignores, "notes": notes,
    }
    cible = out or os.path.join(dossier, "catalogue.json")
    with open(cible, "w", encoding="utf-8", newline="\n") as f:
        json.dump(catalogue, f, ensure_ascii=False, indent=2)
    catalogue["fichier_catalogue"] = cible
    return catalogue


def catalogue_texte(cat, langue_affichage=None):
    """Liste des figures lisible : une ligne par illustration, puis les notes.

    Le verdict, l'usage et le motif d'exclusion sont des valeurs machine : le
    catalogue les porte en francais, ils sont traduits ici a l'affichage
    seulement. Les notes sont RECOMPOSEES a partir des mesures du catalogue
    plutot que recopiees de sa cle notes, sans quoi un catalogue francais
    relu en anglais rendrait un rapport moitie traduit."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    faibles = [i for i in cat["illustrations"]
               if i["verdict"] == "sous le seuil"]
    lignes = [lib.t("images.cat.titre", la, dossier=cat["dossier"]),
              lib.t("images.cat.largeur", la, largeur=cat["largeur_cm"],
                    usage=lib.valeur("images.usage", cat["usage"], la),
                    seuil=cat["seuil_dpi"]),
              lib.t("images.cat.comptes", la, uniques=cat["count"],
                    doublons=cat["doublons"], faibles=cat["sous_le_seuil"]),
              ""]
    lignes.append("  %-3s %-28s %-8s %-12s %-7s %s"
                  % (lib.t("images.cat.col_n", la),
                     lib.t("images.cat.col_fichier", la),
                     lib.t("images.cat.col_format", la),
                     lib.t("images.cat.col_dimensions", la),
                     lib.t("images.cat.col_dpi", la),
                     lib.t("images.cat.col_verdict", la)))
    for i in cat["illustrations"]:
        dims = ("%sx%s" % (i["largeur"], i["hauteur"])) if i["largeur"] else "-"
        dpi = str(i["dpi_effectif"]) if i["dpi_effectif"] else "-"
        suffixe = (lib.t("images.cat.doublon_de", la,
                         fichier=i["doublon_de"])
                   if i.get("doublon_de") else "")
        lignes.append("  %-3d %-28s %-8s %-12s %-7s %s%s"
                      % (i["index"], i["fichier"][:28], i["format"][:8], dims,
                         dpi, lib.valeur("images.verdict", i["verdict"], la),
                         suffixe))
    if cat["ignores"]:
        lignes.append("")
        for g in cat["ignores"]:
            lignes.append("  " + lib.t(
                "images.cat.ignore", la, fichier=g["fichier"],
                raison=lib.valeur("images.raison_ignore", g["raison"], la)))
    notes = _notes_catalogue(faibles, cat["seuil_dpi"], cat["largeur_cm"],
                             cat["illustrations"], la)
    if notes:
        lignes.append("")
        for n in notes:
            lignes.append("  " + lib.t("images.cat.note", la, note=n))
    return "\n".join(lignes)


# --- Conversion SVG vers PNG, backends optionnels en cascade ---------------
#
# Meme discipline que check-presentation.py : plusieurs backends essayes dans
# l'ordre de preference, aucun obligatoire, et si aucun n'est present la
# commande le declare au lieu d'ecrire un fichier douteux. Un echec de backend
# et une absence de backend sont deux statuts distincts, pour qu'un dossier
# sans outil ne passe pas pour un SVG fautif.

BACKENDS_SVG = ("rsvg-convert", "inkscape", "cairosvg", "magick", "convert")

# La marche a suivre pour installer un backend vit dans libelles.py, sous la
# cle images.conv.installation : elle est lue par un humain, dans sa langue.


def _est_imagemagick(cmd):
    """Vrai si CMD est bien ImageMagick.

    La presence sur le PATH ne suffit pas : sous Windows, convert.exe est
    l'utilitaire systeme de conversion FAT vers NTFS, homonyme sans rapport,
    present sur toute installation. L'appeler pour convertir un SVG echoue de
    facon opaque, donc l'identite se verifie avant usage.
    """
    if not _have(cmd):
        return False
    try:
        r = subprocess.run([cmd, "-version"], capture_output=True, text=True,
                           timeout=20)
        return "ImageMagick" in ((r.stdout or "") + (r.stderr or ""))
    except Exception:
        return False


def _a_cairosvg():
    try:
        return importlib.util.find_spec("cairosvg") is not None
    except (ImportError, ValueError):
        return False


def backends_svg_disponibles():
    """Backends de conversion reellement utilisables, dans l'ordre de preference."""
    dispo = []
    for cmd in ("rsvg-convert", "inkscape"):
        if _have(cmd):
            dispo.append(cmd)
    if _a_cairosvg():
        dispo.append("cairosvg")
    for cmd in ("magick", "convert"):
        if _est_imagemagick(cmd):
            dispo.append(cmd)
    return dispo


def _lancer(cmd, args, sortie):
    """Lance un backend externe. Vrai si la sortie existe et n'est pas vide."""
    try:
        subprocess.run([cmd] + args, check=True, capture_output=True, timeout=120)
    except Exception:
        return False
    return os.path.isfile(sortie) and os.path.getsize(sortie) > 0


def convertir(source, sortie, largeur_px=None, langue_affichage=None):
    """Convertit un SVG en PNG par le premier backend disponible.

    Retourne un rapport dict : source, sortie, backend, statut, notes. Le
    statut est ferme : converti, source-absente, source-non-svg,
    aucun-backend, echec-backend. C'est une valeur machine, elle reste la
    chaine francaise dans les deux langues. Aucun backend n'est une
    dependance du plugin, l'absence de tous se declare plutot que de se
    traduire en erreur de fichier.

    Sans langue_affichage, les notes sont les chaines francaises d'origine a
    l'octet pres : ce sont elles que serialise --format json. Ce rapport
    n'est jamais ecrit sur le disque, il peut donc suivre la langue demandee
    sans qu'aucune donnee relue plus tard n'en depende.
    """
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    rapport = {"source": source, "sortie": sortie, "backend": None,
               "statut": None, "notes": [],
               "backends_disponibles": backends_svg_disponibles()}
    if not os.path.isfile(source):
        rapport["statut"] = "source-absente"
        rapport["notes"].append(lib.t("images.conv.source_absente", la,
                                      source=source))
        return rapport
    if _ext(source) != ".svg":
        rapport["statut"] = "source-non-svg"
        rapport["notes"].append(lib.t(
            "images.conv.source_non_svg", la,
            ext=_ext(source) or lib.t("images.conv.sans_extension", la)))
        return rapport
    if not rapport["backends_disponibles"]:
        rapport["statut"] = "aucun-backend"
        rapport["notes"].append(lib.t("images.conv.aucun_backend_note", la,
                                      backends=", ".join(BACKENDS_SVG)))
        rapport["notes"].append(lib.t("images.conv.installation", la))
        rapport["notes"].append(lib.t("images.conv.repli", la))
        return rapport
    dossier = os.path.dirname(os.path.abspath(sortie))
    if dossier:
        os.makedirs(dossier, exist_ok=True)
    for backend in rapport["backends_disponibles"]:
        if backend == "rsvg-convert":
            args = ["-f", "png", "-o", sortie]
            if largeur_px:
                args += ["-w", str(int(largeur_px))]
            ok = _lancer("rsvg-convert", args + [source], sortie)
        elif backend == "inkscape":
            args = ["--export-type=png", "--export-filename=%s" % sortie]
            if largeur_px:
                args.append("--export-width=%d" % int(largeur_px))
            ok = _lancer("inkscape", args + [source], sortie)
        elif backend == "cairosvg":
            try:
                import cairosvg
                cairosvg.svg2png(url=source, write_to=sortie,
                                 output_width=int(largeur_px) if largeur_px else None)
                ok = os.path.isfile(sortie) and os.path.getsize(sortie) > 0
            except Exception:
                ok = False
        else:
            args = ["-background", "none"]
            if largeur_px:
                args += ["-resize", "%d" % int(largeur_px)]
            ok = _lancer(backend, args + [source, sortie], sortie)
        if ok:
            rapport["backend"] = backend
            rapport["statut"] = "converti"
            larg, haut, _f = dimensions(open(sortie, "rb").read())
            rapport["largeur"], rapport["hauteur"] = larg, haut
            return rapport
        rapport["notes"].append(lib.t("images.conv.backend_echec", la,
                                      backend=backend))
    rapport["statut"] = "echec-backend"
    rapport["notes"].append(lib.t("images.conv.echec_tous", la))
    return rapport


def main(argv=None):
    p = argparse.ArgumentParser(description="Extraction d'images (PDF, Office).")
    sub = p.add_subparsers(dest="cmd", required=True)
    pe = sub.add_parser("extract")
    pe.add_argument("source")
    pe.add_argument("--out", required=True)
    pe.add_argument("--min-bytes", type=int, default=1024)
    pm = sub.add_parser("manifest")
    pm.add_argument("dir")
    # Option commune aux deux sous-commandes qui rendent un rapport texte :
    # posee sur un parent, elle s'ecrit apres la sous-commande comme dans les
    # dix-sept scripts deja cables.
    commun = argparse.ArgumentParser(add_help=False)
    commun.add_argument("--langue-affichage", choices=("fr", "en"),
                        default=None,
                        help="langue des libelles du rapport texte (defaut "
                             "fr : un dossier d'images ne porte pas de "
                             "pragme de langue). Le catalogue ecrit sur le "
                             "disque et la sortie JSON restent francais")
    pc = sub.add_parser("catalogue", parents=[commun])
    pc.add_argument("dir")
    pc.add_argument("--out")
    pc.add_argument("--largeur-cm", type=float, default=LARGEUR_INSERTION_CM,
                    dest="largeur_cm")
    pc.add_argument("--usage", choices=("impression", "ecran"),
                    default="impression")
    pc.add_argument("--recursif", action="store_true")
    pc.add_argument("--format", choices=("text", "json"), default="text")
    pc.add_argument("--strict", action="store_true",
                    help="code de sortie 1 si une illustration est sous le seuil")
    pv = sub.add_parser("convertir", parents=[commun])
    pv.add_argument("source")
    pv.add_argument("--out", required=True)
    pv.add_argument("--largeur-px", type=int, dest="largeur_px")
    pv.add_argument("--format", choices=("text", "json"), default="text")
    a = p.parse_args(argv)
    lib = _lib()
    la = lib.resoudre_affichage(getattr(a, "langue_affichage", None))
    if a.cmd == "catalogue":
        cat = cataloguer(a.dir, a.largeur_cm, a.usage, a.out, a.recursif, la)
        # Le JSON ne se traduit pas : c'est le catalogue ecrit sur le disque.
        print(json.dumps(cat, ensure_ascii=False, indent=2)
              if a.format == "json" else catalogue_texte(cat, la))
        return 1 if (a.strict and cat["sous_le_seuil"]) else 0
    if a.cmd == "convertir":
        if a.format == "json":
            # Le JSON ne se traduit pas : les evals et le jeu d'or le lisent.
            rap = convertir(a.source, a.out, a.largeur_px)
            print(json.dumps(rap, ensure_ascii=False, indent=2))
        else:
            rap = convertir(a.source, a.out, a.largeur_px, la)
            print(lib.t("images.conv.ligne", la,
                        statut=lib.valeur("images.statut_conversion",
                                          rap["statut"], la),
                        backend=rap["backend"]
                        or lib.t("images.conv.aucun_backend", la)))
            for n in rap["notes"]:
                print("  %s" % n)
        if rap["statut"] == "converti":
            return 0
        return 3 if rap["statut"] == "aucun-backend" else 1
    if a.cmd == "extract":
        m = extract(a.source, a.out, a.min_bytes)
        resume = {k: m[k] for k in ("source", "type", "backend", "count", "doublons", "notes")}
        print(json.dumps(resume, ensure_ascii=False, indent=2))
        return 0
    mp = os.path.join(a.dir, "manifest.json")
    if not os.path.isfile(mp):
        print(lib.t("images.pas_de_manifest", la), file=sys.stderr)
        return 2
    print(open(mp, encoding="utf-8").read())
    return 0


if __name__ == "__main__":
    sys.exit(main())
