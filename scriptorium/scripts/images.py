#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extraction et inventaire d'images depuis un PDF ou un document Office.

Coeur deterministe (bibliotheque standard) : ouvre les fichiers Office comme
des ZIP et en sort les medias, lit les dimensions dans l'en-tete, deduplique
par empreinte, ecrit un manifeste JSON. Pour le PDF, essaie des backends
optionnels (PyMuPDF, pdfimages, pypdf) puis, a defaut, indique de passer par
le skill pdf. Aucune image n'est interpretee ici : l'alt et la legende sont
ecrits par le modele a l'etape de placement.

Usage :
    python3 images.py extract SOURCE --out DIR [--min-bytes N]
    python3 images.py manifest DIR

Importable : extract(source, outdir, min_bytes), extraire_office(path, outdir),
dimensions(data) -> (largeur, hauteur, format), construire(items, outdir, min_bytes).
"""
import argparse
import hashlib
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


def sha1(b):
    return hashlib.sha1(b).hexdigest()


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
        kind = "vecteur" if ext in VECTOR else ("raster" if ext in RASTER else "autre")
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


def main(argv=None):
    p = argparse.ArgumentParser(description="Extraction d'images (PDF, Office).")
    sub = p.add_subparsers(dest="cmd", required=True)
    pe = sub.add_parser("extract")
    pe.add_argument("source")
    pe.add_argument("--out", required=True)
    pe.add_argument("--min-bytes", type=int, default=1024)
    pm = sub.add_parser("manifest")
    pm.add_argument("dir")
    a = p.parse_args(argv)
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
