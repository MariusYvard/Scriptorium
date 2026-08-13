# -*- coding: utf-8 -*-
"""Regenere les fixtures binaires de gabarit.py et logos.py.

Les fixtures .docx et .png de ce dossier sont des archives et des images
binaires. Ce generateur existe pour qu'elles ne soient pas des blocs opaques :
leur contenu exact reste lisible et modifiable ici, sans dependance.

Usage : python3 generer-gabarit.py [DOSSIER]
"""
import os
import struct
import sys
import zipfile
import zlib

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
R = ('xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/'
     'relationships"')

CT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>
<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""

DOCRELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer1.xml"/>
</Relationships>"""

HEADER = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<w:hdr %s><w:p><w:r><w:t>Ecole nationale, promotion 2026</w:t>'
          '</w:r></w:p></w:hdr>' % W)

FOOTER = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<w:ftr %s><w:p><w:fldSimple w:instr="PAGE \\* MERGEFORMAT">'
          '<w:r><w:t>1</w:t></w:r></w:fldSimple></w:p></w:ftr>' % W)


def styles_xml():
    """Cinq styles : le corps par defaut, trois titres, un style propre."""
    defs = [
        ("Normal", "Normal", ' w:default="1"'),
        ("Heading1", "heading 1", ""),
        ("Heading2", "heading 2", ""),
        ("Heading3", "heading 3", ""),
        ("TitrePageGarde", "Titre page de garde", ""),
    ]
    corps = "".join(
        '<w:style w:type="paragraph"%s w:styleId="%s"><w:name w:val="%s"/>'
        '<w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/></w:rPr>'
        '</w:style>' % (d, sid, nom) for sid, nom, d in defs)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:styles %s>%s</w:styles>' % (W, corps))


def document_xml(marge_gauche=1701, styles_utilises=("Heading1", "Normal")):
    """Marges en vingtiemes de point : 1701 twips valent 3,0 cm."""
    ps = "".join(
        '<w:p><w:pPr><w:pStyle w:val="%s"/></w:pPr><w:r>'
        '<w:t>Texte de gabarit</w:t></w:r></w:p>' % s
        for s in styles_utilises)
    sect = ('<w:sectPr><w:headerReference w:type="default" r:id="rId2"/>'
            '<w:footerReference w:type="default" r:id="rId3"/>'
            '<w:pgSz w:w="11906" w:h="16838"/>'
            '<w:pgMar w:top="1417" w:right="1701" w:bottom="1417" '
            'w:left="%d" w:header="708" w:footer="708"/></w:sectPr>'
            % marge_gauche)
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document %s %s><w:body>%s%s</w:body></w:document>'
            % (W, R, ps, sect))


def ecrire_docx(chemin, marge_gauche=1701,
                styles_utilises=("Heading1", "Normal")):
    with zipfile.ZipFile(chemin, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CT)
        z.writestr("_rels/.rels", RELS)
        z.writestr("word/_rels/document.xml.rels", DOCRELS)
        z.writestr("word/document.xml",
                   document_xml(marge_gauche, styles_utilises))
        z.writestr("word/styles.xml", styles_xml())
        z.writestr("word/header1.xml", HEADER)
        z.writestr("word/footer1.xml", FOOTER)
    return chemin


def ecrire_png(chemin, largeur=1200, hauteur=400):
    """PNG uni minimal, ecrit a la main avec zlib de la bibliotheque standard."""
    def bloc(typ, data):
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF))
    brut = b"".join(b"\x00" + b"\x20\x40\x60" * largeur
                    for _ in range(hauteur))
    out = (b"\x89PNG\r\n\x1a\n"
           + bloc(b"IHDR", struct.pack(">IIBBBBB", largeur, hauteur, 8, 2,
                                       0, 0, 0))
           + bloc(b"IDAT", zlib.compress(brut, 9))
           + bloc(b"IEND", b""))
    with open(chemin, "wb") as f:
        f.write(out)
    return chemin


def main(dest):
    if not os.path.isdir(dest):
        os.makedirs(dest)
    ecrire_docx(os.path.join(dest, "gabarit-ecole.docx"))
    # Document delibrement devie : marge gauche a 3,88 cm et style inconnu.
    ecrire_docx(os.path.join(dest, "document-devie.docx"), marge_gauche=2200,
                styles_utilises=("Heading1", "StyleInconnu"))
    ecrire_png(os.path.join(dest, "logo-ecole.png"))
    ecrire_png(os.path.join(dest, "logo-basse-def.png"), 90, 30)
    print("fixtures ecrites dans %s" % dest)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1
                  else os.path.dirname(os.path.abspath(__file__))))
