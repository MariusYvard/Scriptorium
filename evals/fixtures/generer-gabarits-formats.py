# -*- coding: utf-8 -*-
"""Regenere les fixtures de gabarit pour PowerPoint, ODF et PDF.

Complement de generer-gabarit.py, qui couvre le seul Word. Meme principe : les
archives et le PDF sont des binaires, leur contenu exact reste lisible et
modifiable ici plutot que d'etre livre en bloc opaque.

Usage : python3 generer-gabarits-formats.py [DOSSIER]
"""
import os
import sys
import zipfile

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = ("http://schemas.openxmlformats.org/officeDocument/2006/relationships")
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
RELS = "http://schemas.openxmlformats.org/package/2006/relationships"

# 25,4 x 19,05 cm, le format 4:3 classique, en EMU.
LARG, HAUT = 9144000, 6858000

PPT_CT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
<Override PartName="/ppt/slideLayouts/slideLayout2.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
</Types>"""

PPT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="%s">
<Relationship Id="rId1" Type="%s/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>""" % (RELS, R)

PRES_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="%s">
<Relationship Id="rId1" Type="%s/slideMaster" Target="slideMasters/slideMaster1.xml"/>
<Relationship Id="rId2" Type="%s/theme" Target="theme/theme1.xml"/>
</Relationships>""" % (RELS, R, R)

MASTER_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="%s">
<Relationship Id="rId1" Type="%s/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
<Relationship Id="rId2" Type="%s/slideLayout" Target="../slideLayouts/slideLayout2.xml"/>
<Relationship Id="rId3" Type="%s/theme" Target="../theme/theme1.xml"/>
</Relationships>""" % (RELS, R, R, R)

LAYOUT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="%s">
<Relationship Id="rId1" Type="%s/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>""" % (RELS, R)


def _entete(balise):
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<%s xmlns:a="%s" xmlns:r="%s" xmlns:p="%s">' % (balise, A, R, P))


def _placeholder(ident, nom, type_ph, idx=None):
    attr_idx = ' idx="%s"' % idx if idx else ""
    return ('<p:sp><p:nvSpPr><p:cNvPr id="%d" name="%s"/>'
            '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
            '<p:nvPr><p:ph type="%s"%s/></p:nvPr></p:nvSpPr>'
            '<p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>'
            '</p:sp>' % (ident, nom, type_ph, attr_idx))


def layout(nom, type_layout, formes):
    corps = ('<p:cSld name="%s"><p:spTree>'
             '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/>'
             '</p:nvGrpSpPr><p:grpSpPr/>%s</p:spTree></p:cSld>'
             % (nom, formes))
    return (_entete('p:sldLayout type="%s"' % type_layout) + corps
            + '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>'
              '</p:sldLayout>')


def master():
    corps = ('<p:cSld><p:spTree>'
             '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/>'
             '</p:nvGrpSpPr><p:grpSpPr/>%s</p:spTree></p:cSld>'
             % (_placeholder(2, "Titre du masque", "title")))
    liste = ('<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/>'
             '<p:sldLayoutId id="2147483650" r:id="rId2"/></p:sldLayoutIdLst>')
    carte = ('<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" '
             'accent1="accent1" accent2="accent2" accent3="accent3" '
             'accent4="accent4" accent5="accent5" accent6="accent6" '
             'hlink="hlink" folHlink="folHlink"/>')
    return (_entete("p:sldMaster") + corps + carte + liste + "</p:sldMaster>")


def presentation():
    return (_entete("p:presentation")
            + '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/>'
              '</p:sldMasterIdLst>'
            + '<p:sldSz cx="%d" cy="%d"/><p:notesSz cx="%d" cy="%d"/>'
              % (LARG, HAUT, HAUT, LARG)
            + "</p:presentation>")


def theme():
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<a:theme xmlns:a="%s" name="Theme ecole">'
            '<a:themeElements><a:fontScheme name="Ecole">'
            '<a:majorFont><a:latin typeface="Calibri Light"/></a:majorFont>'
            '<a:minorFont><a:latin typeface="Calibri"/></a:minorFont>'
            '</a:fontScheme></a:themeElements></a:theme>' % A)


def ecrire_pptx(chemin, avec_diapositive=False, disposition_inconnue=False,
                largeur=LARG, hauteur=HAUT):
    """Gabarit de presentation a deux dispositions nommees.

    avec_diapositive ajoute une diapositive qui se reclame de la disposition
    Titre et contenu. disposition_inconnue la fait pointer vers une disposition
    absente du gabarit, ce que la comparaison doit attraper.
    """
    l1 = layout("Diapositive de titre", "title",
                _placeholder(2, "Titre", "ctrTitle")
                + _placeholder(3, "Sous-titre", "subTitle", "1"))
    l2 = layout("Titre et contenu", "obj",
                _placeholder(2, "Titre", "title")
                + _placeholder(3, "Contenu", "body", "1"))
    pres = presentation().replace('cx="%d" cy="%d"' % (LARG, HAUT),
                                  'cx="%d" cy="%d"' % (largeur, hauteur), 1)
    with zipfile.ZipFile(chemin, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _ct_pptx(avec_diapositive))
        z.writestr("_rels/.rels", PPT_RELS)
        z.writestr("ppt/presentation.xml",
                   _pres_avec_slide(pres) if avec_diapositive else pres)
        z.writestr("ppt/_rels/presentation.xml.rels",
                   _pres_rels(avec_diapositive))
        z.writestr("ppt/slideMasters/slideMaster1.xml", master())
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", MASTER_RELS)
        z.writestr("ppt/slideLayouts/slideLayout1.xml", l1)
        z.writestr("ppt/slideLayouts/slideLayout2.xml", l2)
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", LAYOUT_RELS)
        z.writestr("ppt/slideLayouts/_rels/slideLayout2.xml.rels", LAYOUT_RELS)
        z.writestr("ppt/theme/theme1.xml", theme())
        if avec_diapositive:
            z.writestr("ppt/slides/slide1.xml", _slide())
            cible = "slideLayout9.xml" if disposition_inconnue \
                else "slideLayout2.xml"
            z.writestr("ppt/slides/_rels/slide1.xml.rels",
                       '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                       '<Relationships xmlns="%s"><Relationship Id="rId1" '
                       'Type="%s/slideLayout" Target="../slideLayouts/%s"/>'
                       '</Relationships>' % (RELS, R, cible))
    return chemin


def _ct_pptx(avec_diapositive):
    ct = PPT_CT
    if avec_diapositive:
        ct = ct.replace(
            "</Types>",
            '<Override PartName="/ppt/slides/slide1.xml" ContentType='
            '"application/vnd.openxmlformats-officedocument.presentationml.'
            'slide+xml"/></Types>')
    return ct


def _pres_rels(avec_diapositive):
    if not avec_diapositive:
        return PRES_RELS
    return PRES_RELS.replace(
        "</Relationships>",
        '<Relationship Id="rId3" Type="%s/slide" Target="slides/slide1.xml"/>'
        "</Relationships>" % R)


def _pres_avec_slide(pres):
    return pres.replace(
        "</p:sldMasterIdLst>",
        '</p:sldMasterIdLst><p:sldIdLst><p:sldId id="256" r:id="rId3"/>'
        "</p:sldIdLst>")


def _slide():
    corps = ('<p:cSld><p:spTree>'
             '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/>'
             '</p:nvGrpSpPr><p:grpSpPr/>'
             '<p:sp><p:nvSpPr><p:cNvPr id="2" name="Titre"/>'
             '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
             '<p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr><p:spPr/>'
             '<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r>'
             '<a:t>Diapositive du gabarit</a:t></a:r></a:p></p:txBody>'
             '</p:sp></p:spTree></p:cSld>')
    return (_entete("p:sld") + corps
            + '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>')


OFF = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
STY = "urn:oasis:names:tc:opendocument:xmlns:style:1.0"
TXT = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
FO = "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"

ODT_MIME = "application/vnd.oasis.opendocument.text"

ODT_MANIFEST = """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.3">
<manifest:file-entry manifest:full-path="/" manifest:media-type="%s"/>
<manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
<manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
</manifest:manifest>""" % ODT_MIME


def odt_styles(marge_gauche="3cm"):
    styles = "".join(
        '<style:style style:name="%s" style:family="paragraph" '
        'style:display-name="%s"/>' % (sid, nom)
        for sid, nom in (("Standard", "Standard"),
                         ("Heading_20_1", "Heading 1"),
                         ("Heading_20_2", "Heading 2"),
                         ("Text_20_body", "Text body")))
    police = ('<style:font-face style:name="Liberation Serif" '
              'svg:font-family="Liberation Serif" '
              'xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:'
              'svg-compatible:1.0"/>')
    page = ('<style:page-layout style:name="Mpm1">'
            '<style:page-layout-properties fo:page-width="21.001cm" '
            'fo:page-height="29.7cm" fo:margin-top="2.5cm" '
            'fo:margin-bottom="2.5cm" fo:margin-left="%s" '
            'fo:margin-right="2cm"/></style:page-layout>' % marge_gauche)
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<office:document-styles xmlns:office="%s" xmlns:style="%s" '
            'xmlns:fo="%s" office:version="1.3">'
            '<office:font-face-decls>%s</office:font-face-decls>'
            '<office:styles>%s</office:styles>'
            '<office:automatic-styles>%s</office:automatic-styles>'
            "</office:document-styles>" % (OFF, STY, FO, police, styles, page))


def odt_content(styles_employes=("Heading_20_1", "Standard")):
    corps = "".join('<text:p text:style-name="%s">Texte de gabarit</text:p>'
                    % s for s in styles_employes)
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<office:document-content xmlns:office="%s" xmlns:text="%s" '
            'office:version="1.3"><office:body><office:text>%s'
            "</office:text></office:body></office:document-content>"
            % (OFF, TXT, corps))


def ecrire_odt(chemin, marge_gauche="3cm",
               styles_employes=("Heading_20_1", "Standard")):
    """Le mimetype doit etre la premiere entree du zip et rester non compresse,
    exigence de la norme ODF que les lecteurs verifient."""
    with zipfile.ZipFile(chemin, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(zipfile.ZipInfo("mimetype"), ODT_MIME,
                   compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/manifest.xml", ODT_MANIFEST)
        z.writestr("styles.xml", odt_styles(marge_gauche))
        z.writestr("content.xml", odt_content(styles_employes))
    return chemin


def ecrire_pdf(chemin, pages=2, largeur_pt=595, hauteur_pt=842,
               police="Helvetica"):
    """PDF minimal a table xref exacte, ecrit octet par octet.

    Les decalages de la table doivent pointer le debut reel de chaque objet :
    ils se calculent pendant l'ecriture, jamais a l'avance.
    """
    objets = []
    kids = " ".join("%d 0 R" % (4 + 2 * i) for i in range(pages))
    objets.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objets.append(("<< /Type /Pages /Kids [%s] /Count %d >>"
                   % (kids, pages)).encode("ascii"))
    objets.append(("<< /Type /Font /Subtype /Type1 /BaseFont /%s >>"
                   % police).encode("ascii"))
    for i in range(pages):
        flux = ("BT /F1 12 Tf 72 %d Td (Page %d du gabarit impose) Tj ET"
                % (hauteur_pt - 100, i + 1)).encode("ascii")
        objets.append((
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %d %d] "
            "/Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>"
            % (largeur_pt, hauteur_pt, 5 + 2 * i)).encode("ascii"))
        objets.append(b"<< /Length %d >>\nstream\n" % len(flux)
                      + flux + b"\nendstream")

    sortie = bytearray(b"%PDF-1.4\n")
    decalages = []
    for i, corps in enumerate(objets, start=1):
        decalages.append(len(sortie))
        sortie += b"%d 0 obj\n" % i + corps + b"\nendobj\n"

    debut_xref = len(sortie)
    sortie += b"xref\n0 %d\n" % (len(objets) + 1)
    sortie += b"0000000000 65535 f \n"
    for d in decalages:
        sortie += b"%010d 00000 n \n" % d
    sortie += (b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
               % (len(objets) + 1, debut_xref))
    with open(chemin, "wb") as f:
        f.write(bytes(sortie))
    return chemin


def main(dest):
    if not os.path.isdir(dest):
        os.makedirs(dest)
    j = lambda n: os.path.join(dest, n)
    ecrire_pptx(j("gabarit-deck.pptx"))
    ecrire_pptx(j("deck-conforme.pptx"), avec_diapositive=True)
    ecrire_pptx(j("deck-devie.pptx"), avec_diapositive=True,
                disposition_inconnue=True, largeur=12192000, hauteur=6858000)
    ecrire_odt(j("gabarit-labo.odt"))
    ecrire_odt(j("document-odt-devie.odt"), marge_gauche="4cm",
               styles_employes=("Heading_20_1", "StyleMaison"))
    ecrire_pdf(j("gabarit-rendu.pdf"))
    ecrire_pdf(j("rendu-devie.pdf"), pages=3, largeur_pt=612, hauteur_pt=792)
    print("fixtures multi-format ecrites dans %s" % dest)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1
                  else os.path.dirname(os.path.abspath(__file__))))
