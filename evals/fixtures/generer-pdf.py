# -*- coding: utf-8 -*-
"""Regenere les fixtures PDF de check-lecture-pdf.py.

Sur le modele de generer-gabarit.py : les fixtures binaires ne sont pas des
blocs opaques, leur contenu exact reste lisible et modifiable ici, sans
dependance. Ecrit trois PDF minimaux a la main (en-tete, objets, xref,
trailer, %%EOF) : un a texte extractible normal, un sans texte (page vide,
simule un scan sans OCR), un tronque (sans %%EOF, xref ni trailer).

Usage : python3 generer-pdf.py [DOSSIER]
"""
import os
import sys

OBJ1 = b"<< /Type /Catalog /Pages 2 0 R >>"
OBJ2 = b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>"
OBJ3 = (b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>")
OBJ5 = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

TEXTE_NORMAL = b"BT /F1 12 Tf 72 700 Td (Bonjour, ceci est un texte normal et lisible.) Tj ET"
TEXTE_VIDE = b"q Q"


def _obj_stream(contenu):
    """Corps d'un objet flux : dictionnaire /Length puis stream/endstream."""
    return f"<< /Length {len(contenu)} >>\nstream\n".encode("ascii") + contenu + b"\nendstream"


def ecrire_pdf(chemin, objets, root_num=1, tronquer=False):
    """Ecrit un PDF minimal valide a partir d'un dict {numero: corps_octets}.

    Si tronquer est vrai, le fichier s'arrete juste apres le dernier objet,
    sans table xref, sans trailer et sans %%EOF : simule un fichier coupe
    en cours d'ecriture ou de transfert.
    """
    buf = bytearray()
    buf += b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets = {}
    for num in sorted(objets):
        offsets[num] = len(buf)
        buf += f"{num} 0 obj\n".encode("ascii")
        buf += objets[num]
        buf += b"\nendobj\n"
    if tronquer:
        with open(chemin, "wb") as f:
            f.write(bytes(buf))
        return chemin
    xref_offset = len(buf)
    n = max(objets) + 1
    buf += f"xref\n0 {n}\n".encode("ascii")
    buf += b"0000000000 65535 f \n"
    for num in range(1, n):
        off = offsets.get(num, 0)
        buf += f"{off:010d} 00000 n \n".encode("ascii")
    buf += (f"trailer\n<< /Size {n} /Root {root_num} 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF").encode("ascii")
    with open(chemin, "wb") as f:
        f.write(bytes(buf))
    return chemin


def _verifier_avec_backend(chemin):
    """Ouvre le PDF ecrit avec pypdf s'il est installe. Backend optionnel :
    son absence est declaree et sautee, jamais une erreur du generateur."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return "pypdf absent, verification sautee"
    try:
        r = PdfReader(chemin)
        n = len(r.pages)
        texte = r.pages[0].extract_text() or ""
        return f"pypdf : {n} page(s), texte page 1 = {len(texte)} caractere(s)"
    except Exception as e:
        return f"pypdf : erreur a l'ouverture ({e})"


def main(dest):
    if not os.path.isdir(dest):
        os.makedirs(dest)
    p_normal = os.path.join(dest, "pdf-normal.pdf")
    p_vide = os.path.join(dest, "pdf-sans-texte.pdf")
    p_tronque = os.path.join(dest, "pdf-tronque.pdf")

    ecrire_pdf(p_normal, {1: OBJ1, 2: OBJ2, 3: OBJ3, 4: _obj_stream(TEXTE_NORMAL), 5: OBJ5})
    ecrire_pdf(p_vide, {1: OBJ1, 2: OBJ2, 3: OBJ3, 4: _obj_stream(TEXTE_VIDE), 5: OBJ5})
    ecrire_pdf(p_tronque, {1: OBJ1, 2: OBJ2, 3: OBJ3, 4: _obj_stream(TEXTE_NORMAL), 5: OBJ5},
              tronquer=True)

    print("fixtures ecrites dans %s" % dest)
    print("  pdf-normal.pdf :", _verifier_avec_backend(p_normal))
    print("  pdf-sans-texte.pdf :", _verifier_avec_backend(p_vide))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1
                  else os.path.dirname(os.path.abspath(__file__))))
