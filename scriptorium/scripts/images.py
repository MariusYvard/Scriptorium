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

Usage :
    python3 images.py extract SOURCE --out DIR [--min-bytes N]
    python3 images.py manifest DIR
    python3 images.py catalogue DIR [--out FICHIER] [--largeur-cm N]
                      [--usage impression|ecran] [--format text|json]
    python3 images.py convertir FIGURE.svg --out FIGURE.png [--largeur-px N]
                      [--format text|json]

Importable : extract(source, outdir, min_bytes), extraire_office(path, outdir),
dimensions(data) -> (largeur, hauteur, format), construire(items, outdir, min_bytes),
resolution_effective(pixels, largeur_cm), seuil_dpi(usage),
cataloguer(dossier, largeur_cm, usage), convertir(source, sortie, largeur_px),
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


def cataloguer(dossier, largeur_cm=LARGEUR_INSERTION_CM, usage="impression",
               out=None, recursif=False):
    """Catalogue un dossier d'illustrations deja produites.

    Meme mecanique que l'extraction (dimensions lues dans l'en-tete, empreinte
    sha1, drapeaux) appliquee a des fichiers deja sur le disque : photos de
    dispositif, captures d'ecran, schemas faits ailleurs. Chaque entree recoit
    en plus la resolution effective a LARGEUR_CM et un verdict ferme pris dans
    VERDICTS. Ecrit le catalogue en JSON et le retourne.
    """
    if not os.path.isdir(dossier):
        raise SystemExit("dossier introuvable : %s" % dossier)
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
    notes = []
    if faibles:
        notes.append(
            "%d illustration(s) sous %d dpi a %.1f cm : reduire la largeur "
            "d'insertion (colonne largeur_cm_max), retrouver le fichier "
            "d'origine, ou refaire la prise de vue ou la capture."
            % (len(faibles), seuil, largeur_cm))
    if any("vecteur-a-convertir" in i["flags"] for i in illustrations):
        notes.append("Illustrations vectorielles presentes : la voie Word "
                     "passe par images.py convertir.")
    if any(i["verdict"] == "dimensions illisibles" for i in illustrations):
        notes.append("Dimensions illisibles sur au moins un fichier : format "
                     "non couvert par la lecture d'en-tete, mesurer autrement "
                     "plutot que supposer.")
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


def catalogue_texte(cat):
    """Liste des figures lisible : une ligne par illustration, puis les notes."""
    lignes = ["Catalogue : %s" % cat["dossier"],
              "Largeur d'insertion prevue : %.1f cm, usage %s, seuil %d dpi"
              % (cat["largeur_cm"], cat["usage"], cat["seuil_dpi"]),
              "%d illustration(s) unique(s), %d doublon(s), %d sous le seuil"
              % (cat["count"], cat["doublons"], cat["sous_le_seuil"]), ""]
    lignes.append("  %-3s %-28s %-8s %-12s %-7s %s"
                  % ("n", "fichier", "format", "dimensions", "dpi", "verdict"))
    for i in cat["illustrations"]:
        dims = ("%sx%s" % (i["largeur"], i["hauteur"])) if i["largeur"] else "-"
        dpi = str(i["dpi_effectif"]) if i["dpi_effectif"] else "-"
        suffixe = (" (doublon de %s)" % i["doublon_de"]) if i.get("doublon_de") else ""
        lignes.append("  %-3d %-28s %-8s %-12s %-7s %s%s"
                      % (i["index"], i["fichier"][:28], i["format"][:8], dims,
                         dpi, i["verdict"], suffixe))
    if cat["ignores"]:
        lignes.append("")
        for g in cat["ignores"]:
            lignes.append("  ignore : %s (%s)" % (g["fichier"], g["raison"]))
    if cat["notes"]:
        lignes.append("")
        for n in cat["notes"]:
            lignes.append("  note : %s" % n)
    return "\n".join(lignes)


# --- Conversion SVG vers PNG, backends optionnels en cascade ---------------
#
# Meme discipline que check-presentation.py : plusieurs backends essayes dans
# l'ordre de preference, aucun obligatoire, et si aucun n'est present la
# commande le declare au lieu d'ecrire un fichier douteux. Un echec de backend
# et une absence de backend sont deux statuts distincts, pour qu'un dossier
# sans outil ne passe pas pour un SVG fautif.

BACKENDS_SVG = ("rsvg-convert", "inkscape", "cairosvg", "magick", "convert")

INSTALLATION_SVG = (
    "Installer l'un de ces backends : librsvg (commande rsvg-convert, "
    "paquet librsvg2-bin sous Debian, librsvg sous Homebrew), Inkscape "
    "(inkscape.org), le module Python cairosvg (pip install cairosvg), ou "
    "ImageMagick (imagemagick.org, commande magick).")


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


def convertir(source, sortie, largeur_px=None):
    """Convertit un SVG en PNG par le premier backend disponible.

    Retourne un rapport dict : source, sortie, backend, statut, notes. Le
    statut est ferme : converti, source-absente, source-non-svg,
    aucun-backend, echec-backend. Aucun backend n'est une dependance du
    plugin, l'absence de tous se declare plutot que de se traduire en erreur
    de fichier.
    """
    rapport = {"source": source, "sortie": sortie, "backend": None,
               "statut": None, "notes": [],
               "backends_disponibles": backends_svg_disponibles()}
    if not os.path.isfile(source):
        rapport["statut"] = "source-absente"
        rapport["notes"].append("Fichier source introuvable : %s" % source)
        return rapport
    if _ext(source) != ".svg":
        rapport["statut"] = "source-non-svg"
        rapport["notes"].append(
            "Source attendue en .svg, recue en %s." % (_ext(source) or "sans extension"))
        return rapport
    if not rapport["backends_disponibles"]:
        rapport["statut"] = "aucun-backend"
        rapport["notes"].append(
            "Aucun backend de conversion SVG present (essayes dans l'ordre : "
            "%s). Le fichier source n'est pas en cause." % ", ".join(BACKENDS_SVG))
        rapport["notes"].append(INSTALLATION_SVG)
        rapport["notes"].append(
            "Sans backend, garder le SVG pour les voies HTML, LaTeX et PDF, "
            "qui l'affichent, et signaler la figure manquante dans la voie Word.")
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
        rapport["notes"].append("Backend %s essaye sans succes." % backend)
    rapport["statut"] = "echec-backend"
    rapport["notes"].append(
        "Tous les backends presents ont echoue : le SVG lui-meme est en cause "
        "(syntaxe, police absente, reference externe).")
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
    pc = sub.add_parser("catalogue")
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
    pv = sub.add_parser("convertir")
    pv.add_argument("source")
    pv.add_argument("--out", required=True)
    pv.add_argument("--largeur-px", type=int, dest="largeur_px")
    pv.add_argument("--format", choices=("text", "json"), default="text")
    a = p.parse_args(argv)
    if a.cmd == "catalogue":
        cat = cataloguer(a.dir, a.largeur_cm, a.usage, a.out, a.recursif)
        print(json.dumps(cat, ensure_ascii=False, indent=2)
              if a.format == "json" else catalogue_texte(cat))
        return 1 if (a.strict and cat["sous_le_seuil"]) else 0
    if a.cmd == "convertir":
        rap = convertir(a.source, a.out, a.largeur_px)
        if a.format == "json":
            print(json.dumps(rap, ensure_ascii=False, indent=2))
        else:
            print("%s : %s" % (rap["statut"], rap["backend"] or "aucun backend"))
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
        print("Pas de manifest.json dans ce dossier.", file=sys.stderr)
        return 2
    print(open(mp, encoding="utf-8").read())
    return 0


if __name__ == "__main__":
    sys.exit(main())
