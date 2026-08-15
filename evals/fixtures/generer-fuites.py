# -*- coding: utf-8 -*-
"""Fixtures de check-fuites.py : documents qui trahissent, et documents nets.

Meme principe que les autres generateurs du dossier : les binaires restent
lisibles et modifiables ici plutot que livres en bloc opaque.

Usage : python3 generer-fuites.py [DOSSIER]
"""
import os
import sys
import zipfile

CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC = "http://purl.org/dc/elements/1.1/"
DCT = "http://purl.org/dc/terms/"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
EP = ("http://schemas.openxmlformats.org/officeDocument/2006/"
      "extended-properties")
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
RELS = "http://schemas.openxmlformats.org/package/2006/relationships"

CT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""

RACINE_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="%s">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>""" % RELS


def core_xml(createur, dernier, revision, titre=None):
    t = ("<dc:title>%s</dc:title>" % titre) if titre else ""
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="%s" xmlns:dc="%s" xmlns:dcterms="%s" '
            'xmlns:xsi="%s">%s<dc:creator>%s</dc:creator>'
            '<cp:lastModifiedBy>%s</cp:lastModifiedBy>'
            '<cp:revision>%s</cp:revision></cp:coreProperties>'
            % (CP, DC, DCT, XSI, t, createur, dernier, revision))


def app_xml(societe, minutes):
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Properties xmlns="%s"><Application>Microsoft Office Word'
            '</Application><Company>%s</Company><TotalTime>%d</TotalTime>'
            '</Properties>' % (EP, societe, minutes))


def document_xml(avec_revisions=False, avec_masque=False):
    corps = '<w:p><w:r><w:t>Texte ordinaire.</w:t></w:r></w:p>'
    if avec_revisions:
        corps += ('<w:p><w:ins w:id="1" w:author="Relecteur"><w:r>'
                  '<w:t>ajout non accepte</w:t></w:r></w:ins>'
                  '<w:del w:id="2" w:author="Relecteur"><w:r><w:delText>'
                  'coupe non accepte</w:delText></w:r></w:del></w:p>')
    if avec_masque:
        corps += ('<w:p><w:r><w:rPr><w:vanish/></w:rPr>'
                  '<w:t>note interne masquee</w:t></w:r></w:p>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="%s"><w:body>%s'
            '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/></w:sectPr>'
            '</w:body></w:document>' % (W, corps))


COMMENTS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:comments xmlns:w="%s">'
            '<w:comment w:id="1" w:author="Claire Dumas" w:initials="CD">'
            '<w:p><w:r><w:t>a revoir avant envoi</w:t></w:r></w:p>'
            '</w:comment></w:comments>' % W)

DOC_RELS_LOCAL = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                  '<Relationships xmlns="%s"><Relationship Id="rId9" '
                  'Type="http://schemas.openxmlformats.org/officeDocument/'
                  '2006/relationships/hyperlink" '
                  'Target="file:///C:/Users/prenom.nom/Documents/notes.xlsx" '
                  'TargetMode="External"/></Relationships>' % RELS)


def ecrire_docx(chemin, createur="Prenom Nom", dernier="autre.personne",
                societe="Cabinet Exemple", revision="17", minutes=245,
                revisions=False, commentaires=False, masque=False,
                lien_local=False):
    with zipfile.ZipFile(chemin, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CT)
        z.writestr("_rels/.rels", RACINE_RELS)
        z.writestr("word/document.xml", document_xml(revisions, masque))
        z.writestr("docProps/core.xml",
                   core_xml(createur, dernier, revision, "Rapport interne"))
        z.writestr("docProps/app.xml", app_xml(societe, minutes))
        if commentaires:
            z.writestr("word/comments.xml", COMMENTS)
        if lien_local:
            z.writestr("word/_rels/document.xml.rels", DOC_RELS_LOCAL)
    return chemin


def ecrire_docx_net(chemin):
    """Document sans rien a signaler : champs vides ou generiques."""
    with zipfile.ZipFile(chemin, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CT)
        z.writestr("_rels/.rels", RACINE_RELS)
        z.writestr("word/document.xml", document_xml())
        z.writestr("docProps/core.xml", core_xml("", "", "1"))
        z.writestr("docProps/app.xml", app_xml("", 0))
    return chemin


def _pdf_base(auteur="Prenom Nom", producteur="Scriptorium Test"):
    """PDF minimal a table xref exacte, avec un dictionnaire Info rempli."""
    objets = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        b"/Contents 4 0 R >>",
        b"<< /Length 44 >>\nstream\nBT /F1 12 Tf 72 742 Td (Rapport) Tj ET"
        b"\nendstream",
        ("<< /Author (%s) /Producer (%s) /Title (Rapport interne) >>"
         % (auteur, producteur)).encode("latin-1"),
    ]
    sortie = bytearray(b"%PDF-1.4\n")
    decalages = []
    for i, corps in enumerate(objets, start=1):
        decalages.append(len(sortie))
        sortie += b"%d 0 obj\n" % i + corps + b"\nendobj\n"
    debut = len(sortie)
    sortie += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objets) + 1)
    for d in decalages:
        sortie += b"%010d 00000 n \n" % d
    sortie += (b"trailer\n<< /Size %d /Root 1 0 R /Info 5 0 R >>\n"
               b"startxref\n%d\n%%%%EOF\n" % (len(objets) + 1, debut))
    return bytes(sortie), debut


def ecrire_pdf(chemin, auteur="Prenom Nom"):
    brut, _ = _pdf_base(auteur)
    with open(chemin, "wb") as f:
        f.write(brut)
    return chemin


def ecrire_pdf_incremental(chemin, auteur="Prenom Nom"):
    """PDF dont on a cru retirer les metadonnees, a la maniere d'exiftool.

    L'edition est INCREMENTALE : le trailer neuf ne reference plus /Info, mais
    l'objet d'origine et ses octets restent dans le fichier, recuperables. Le
    fichier a GROSSI au lieu de maigrir, ce qui est le signe. C'est exactement
    le piege que check-fuites.py doit relever.
    """
    base, premier_xref = _pdf_base(auteur)
    ajout = bytearray(base)
    # Objet 5 (Info) libere, puis nouvelle table qui renvoie vers l'ancienne.
    depart = len(ajout)
    ajout += b"5 0 obj\n<< >>\nendobj\n"
    debut = len(ajout)
    ajout += b"xref\n0 1\n0000000000 65535 f \n5 1\n"
    ajout += b"%010d 00000 n \n" % depart
    ajout += (b"trailer\n<< /Size 6 /Root 1 0 R /Prev %d >>\n"
              b"startxref\n%d\n%%%%EOF\n" % (premier_xref, debut))
    with open(chemin, "wb") as f:
        f.write(bytes(ajout))
    return chemin


def main(dest):
    if not os.path.isdir(dest):
        os.makedirs(dest)
    j = lambda n: os.path.join(dest, n)
    ecrire_docx(j("fuites-docx.docx"), revisions=True, commentaires=True,
                masque=True, lien_local=True)
    ecrire_docx_net(j("fuites-docx-net.docx"))
    ecrire_pdf(j("fuites-pdf.pdf"))
    ecrire_pdf_incremental(j("fuites-pdf-incremental.pdf"))
    print("fixtures de fuites ecrites dans %s" % dest)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1
                  else os.path.dirname(os.path.abspath(__file__))))
