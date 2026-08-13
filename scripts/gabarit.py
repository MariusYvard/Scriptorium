#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gabarits de document imposes : inventorier, comparer, remplir.

Quatre familles de fichiers, lues avec la bibliotheque standard seule
(zipfile, xml.etree, lecture binaire), sans aucune dependance :

  texte OOXML     .docx .dotx   inventaire complet, comparaison, remplissage
  diapositives    .pptx .potx   inventaire complet, comparaison, remplissage
  texte ODF       .odt .odp     inventaire et comparaison
  page fixe       .pdf          inventaire et comparaison, en lecture seule

Trois actions :
  inventorier  lit un gabarit fourni par un tiers (ecole, laboratoire, revue,
               client) et ecrit sa structure dans un JSON declaratif.
  comparer     confronte un document produit a cet inventaire et rend un
               verdict ferme, avec les ecarts nommes un par un.
  remplir      injecte du contenu dans le gabarit lui-meme, dans ses styles ou
               ses dispositions existants, plutot que de generer un fichier
               neuf. Un gabarit porte des elements qu'une regeneration
               perdrait : filigrane, numerotation liee, masque de
               diapositive, theme de couleurs propre au modele.

Le remplissage n'existe que pour les formats ou l'ecriture est sure. Un PDF est
une page fixe deja composee : il s'inventorie et se compare, il ne se remplit
pas, et le script le refuse par un message nomme plutot que par un resultat
approximatif. Un ODF s'inventorie et se compare, son remplissage reste ouvert.

La comparaison se fait par identifiant stable (w:styleId en Word, nom de
disposition en PowerPoint, style:name en ODF), jamais par le libelle affiche :
une suite bureautique francisee renomme les libelles, pas les identifiants.

Usage :
  python3 gabarit.py inventorier GABARIT.docx|.pptx|.odt|.pdf [--out INV.json]
  python3 gabarit.py comparer INVENTAIRE.json DOCUMENT [--format text|json]
  python3 gabarit.py remplir INVENTAIRE.json CONTENU.md --out SORTIE
                     [--logo FICHIER --logo-largeur-cm N] [--disposition NOM]
  python3 gabarit.py formats

Code de sortie 1 sur erreur bloquante ou ecart majeur en comparaison.
"""
import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
RELS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"

# Un point vaut 12700 EMU, un pouce 914400 EMU, un centimetre 360000 EMU.
EMU_CM = 360000
# Word exprime les marges en vingtiemes de point (1 cm = 566,93 twips).
TWIP_CM = 567.0

NIVEAUX_TITRE = 6

# Espaces de noms des trois autres familles.
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
OFF = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
STY = "urn:oasis:names:tc:opendocument:xmlns:style:1.0"
TXT = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
FO = "urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"

# Famille de traitement par extension. La famille, pas l'extension, decide du
# code applique : un .dotx se lit comme un .docx, un .potx comme un .pptx.
FAMILLES = {
    "docx": "texte-ooxml", "dotx": "texte-ooxml", "docm": "texte-ooxml",
    "pptx": "diapositives-ooxml", "potx": "diapositives-ooxml",
    "pptm": "diapositives-ooxml",
    "odt": "texte-odf", "odp": "diapositives-odf", "ott": "texte-odf",
    "otp": "diapositives-odf",
    "pdf": "page-fixe",
}
REMPLISSABLES = ("texte-ooxml", "diapositives-ooxml")
MOTIF_NON_REMPLISSABLE = {
    "texte-odf": "le remplissage ODF n'est pas implemente ; l'inventaire et la "
                 "comparaison le sont",
    "diapositives-odf": "le remplissage ODF n'est pas implemente ; "
                        "l'inventaire et la comparaison le sont",
    "page-fixe": "un PDF est une page deja composee : il se compare, il ne se "
                 "remplit pas. Remplir le gabarit d'origine puis exporter",
}

EMU_POUCE = 914400


def _q(ns, tag):
    return "{%s}%s" % (ns, tag)


def detecter_format(chemin):
    """Format et famille d'un fichier, par son contenu puis par son extension.

    Le contenu prime : un fichier renomme .docx qui commence par %PDF- est un
    PDF, et le traiter comme un zip produirait une erreur obscure au lieu d'un
    constat clair. L'extension ne sert qu'a departager les familles zip entre
    elles, que leur magie commune ne distingue pas.
    """
    if not os.path.isfile(chemin):
        raise SystemExit("fichier introuvable : %s" % chemin)
    ext = os.path.splitext(chemin)[1].lower().lstrip(".")
    with open(chemin, "rb") as f:
        tete = f.read(8)
    if tete[:5] == b"%PDF-":
        return "pdf", "page-fixe"
    if tete[:2] != b"PK":
        raise SystemExit(
            "%s n'est ni un PDF ni une archive : format non reconnu"
            % os.path.basename(chemin))
    famille = FAMILLES.get(ext)
    if famille and famille != "page-fixe":
        return ext, famille
    # Extension absente ou trompeuse : la piece maitresse du zip tranche.
    with zipfile.ZipFile(chemin) as z:
        noms = set(z.namelist())
    if "word/document.xml" in noms:
        return "docx", "texte-ooxml"
    if "ppt/presentation.xml" in noms:
        return "pptx", "diapositives-ooxml"
    if "content.xml" in noms:
        mime = ""
        with zipfile.ZipFile(chemin) as z:
            if "mimetype" in noms:
                mime = z.read("mimetype").decode("ascii", "replace")
        return ("odp", "diapositives-odf") if "presentation" in mime \
            else ("odt", "texte-odf")
    raise SystemExit("%s est une archive, mais d'aucun format de document "
                     "reconnu" % os.path.basename(chemin))


def lire_parties(chemin, piece_attendue="word/document.xml"):
    """Toutes les entrees du zip en memoire. Un document bureautique est petit.

    piece_attendue nomme la partie sans laquelle le fichier n'est pas du format
    voulu. La passer a None accepte n'importe quelle archive, ce qui sert aux
    formats dont la piece maitresse varie.
    """
    if not os.path.isfile(chemin):
        raise SystemExit("fichier introuvable : %s" % chemin)
    try:
        with zipfile.ZipFile(chemin) as z:
            noms = z.namelist()
            if piece_attendue and piece_attendue not in noms:
                raise SystemExit(
                    "%s ne porte pas %s : format inattendu"
                    % (os.path.basename(chemin), piece_attendue))
            return {n: z.read(n) for n in noms}
    except zipfile.BadZipFile:
        raise SystemExit("%s n'est pas une archive lisible"
                         % os.path.basename(chemin))


def _racine(parties, nom):
    brut = parties.get(nom)
    if brut is None:
        return None
    try:
        return ET.fromstring(brut)
    except ET.ParseError:
        return None


def styles(parties):
    """Styles nommes du gabarit, par identifiant."""
    racine = _racine(parties, "word/styles.xml")
    if racine is None:
        return {}
    out = {}
    for st in racine.findall(_q(W, "style")):
        sid = st.get(_q(W, "styleId"))
        if not sid:
            continue
        nom = st.find(_q(W, "name"))
        base = st.find(_q(W, "basedOn"))
        suivant = st.find(_q(W, "next"))
        out[sid] = {
            "id": sid,
            "type": st.get(_q(W, "type")) or "paragraph",
            "nom": nom.get(_q(W, "val")) if nom is not None else sid,
            "base": base.get(_q(W, "val")) if base is not None else None,
            "suivant": suivant.get(_q(W, "val")) if suivant is not None else None,
            "defaut": st.get(_q(W, "default")) == "1",
        }
    return out


def hierarchie_titres(cat):
    """Associe un niveau de titre 1 a 6 a l'identifiant de style qui le porte.

    Word nomme ses styles integres Heading1 a Heading9 en interne quel que soit
    l'affichage. Un gabarit peut aussi definir ses propres styles de titre : la
    detection retombe alors sur le libelle (Titre 1, Heading 1, Niveau 1).
    """
    out = {}
    for niveau in range(1, NIVEAUX_TITRE + 1):
        candidat = None
        for sid, st in cat.items():
            if st["type"] != "paragraph":
                continue
            cle = sid.lower().replace(" ", "").replace("-", "")
            libelle = (st["nom"] or "").lower()
            if cle in ("heading%d" % niveau, "titre%d" % niveau):
                candidat = sid
                break
            if re.fullmatch(r"(heading|titre|niveau)\s*%d" % niveau, libelle):
                candidat = candidat or sid
        if candidat:
            out[str(niveau)] = candidat
    return out


def style_corps(cat):
    """Identifiant du style de paragraphe courant."""
    for sid, st in cat.items():
        if st["type"] == "paragraph" and st["defaut"]:
            return sid
    for attendu in ("Normal", "BodyText", "Corpsdetexte", "Standard"):
        if attendu in cat:
            return attendu
    for sid, st in cat.items():
        if st["type"] == "paragraph":
            return sid
    return None


def mise_en_page(parties):
    """Marges, dimensions et hauteurs d'en-tete et de pied, en centimetres."""
    racine = _racine(parties, "word/document.xml")
    if racine is None:
        return {}
    sect = None
    for el in racine.iter(_q(W, "sectPr")):
        sect = el
    if sect is None:
        return {}
    out = {}
    pg = sect.find(_q(W, "pgMar"))
    if pg is not None:
        for cle in ("top", "bottom", "left", "right", "header", "footer",
                    "gutter"):
            brut = pg.get(_q(W, cle))
            if brut is None:
                continue
            try:
                out[cle] = round(int(brut) / TWIP_CM, 2)
            except ValueError:
                continue
    sz = sect.find(_q(W, "pgSz"))
    if sz is not None:
        for cle, dest in (("w", "largeur"), ("h", "hauteur")):
            brut = sz.get(_q(W, cle))
            if brut:
                try:
                    out[dest] = round(int(brut) / TWIP_CM, 2)
                except ValueError:
                    pass
        out["orientation"] = sz.get(_q(W, "orient")) or "portrait"
    return out


def _texte(el):
    return "".join(t.text or "" for t in el.iter(_q(W, "t"))).strip()


def entetes_et_pieds(parties):
    """Contenu texte et champs de chaque en-tete et pied declare."""
    out = []
    for nom in sorted(parties):
        base = os.path.basename(nom)
        if not (base.startswith("header") or base.startswith("footer")):
            continue
        if not nom.endswith(".xml"):
            continue
        racine = _racine(parties, nom)
        if racine is None:
            continue
        champs = []
        for fld in racine.iter(_q(W, "fldSimple")):
            instr = (fld.get(_q(W, "instr")) or "").strip()
            if instr:
                champs.append(instr.split()[0].upper())
        for instr in racine.iter(_q(W, "instrText")):
            brut = (instr.text or "").strip()
            if brut:
                champs.append(brut.split()[0].upper())
        out.append({
            "partie": nom,
            "role": "en-tete" if base.startswith("header") else "pied",
            "texte": _texte(racine)[:200],
            "champs": sorted(set(champs)),
            "images": len(list(racine.iter(_q(W, "drawing")))),
        })
    return out


def protection(parties):
    """Restriction d'edition declaree dans le gabarit, sans jamais la lever."""
    racine = _racine(parties, "word/settings.xml")
    if racine is None:
        return None
    prot = racine.find(_q(W, "documentProtection"))
    if prot is None:
        return None
    return {
        "edition": prot.get(_q(W, "edit")),
        "applique": prot.get(_q(W, "enforcement")) == "1",
        "mot_de_passe": prot.get(_q(W, "hash")) is not None,
    }


def styles_utilises(parties):
    """Identifiants de style effectivement appliques aux paragraphes."""
    racine = _racine(parties, "word/document.xml")
    if racine is None:
        return {}
    compte = {}
    for p in racine.iter(_q(W, "p")):
        pr = p.find(_q(W, "pPr"))
        sid = None
        if pr is not None:
            ps = pr.find(_q(W, "pStyle"))
            if ps is not None:
                sid = ps.get(_q(W, "val"))
        cle = sid or "(defaut)"
        compte[cle] = compte.get(cle, 0) + 1
    return compte


def polices(parties):
    """Polices nommees dans les styles et dans le theme de police par defaut."""
    trouvees = set()
    cibles = ["word/styles.xml"]
    # Le theme ne vit pas au meme endroit selon l'application : word/theme en
    # Word, ppt/theme en PowerPoint. Les parcourir tous evite de le redire.
    cibles += [n for n in parties if "/theme/" in n and n.endswith(".xml")]
    for nom in cibles:
        racine = _racine(parties, nom)
        if racine is None:
            continue
        for rf in racine.iter(_q(W, "rFonts")):
            for cle in ("ascii", "hAnsi", "cs"):
                val = rf.get(_q(W, cle))
                if val and not val.startswith("+"):
                    trouvees.add(val)
        for lat in racine.iter(_q(A, "latin")):
            val = lat.get("typeface")
            if val:
                trouvees.add(val)
    return sorted(trouvees)


def _compter_images(parties, nom):
    racine = _racine(parties, nom)
    if racine is None:
        return 0
    return len(list(racine.iter(_q(W, "drawing"))))


def _inventorier_docx(chemin, parties):
    cat = styles(parties)
    return {
        "styles": [cat[s] for s in sorted(cat)],
        "hierarchie_titres": hierarchie_titres(cat),
        "style_corps": style_corps(cat),
        "mise_en_page": mise_en_page(parties),
        "entetes_et_pieds": entetes_et_pieds(parties),
        "protection": protection(parties),
        "polices": polices(parties),
        "styles_utilises": styles_utilises(parties),
        "images_corps": _compter_images(parties, "word/document.xml"),
    }


def inventorier(chemin):
    """Structure declarative d'un gabarit, prete a servir de reference.

    Le format se detecte, il ne se declare pas. Les quatre familles rendent le
    meme squelette de cles, ce qui laisse la comparaison et l'affichage
    communs, chacune y ajoutant ce qui n'existe que chez elle : dispositions
    pour une presentation, formats de page pour un PDF.
    """
    fmt, famille = detecter_format(chemin)
    if famille == "page-fixe":
        socle = _inventorier_pdf(chemin)
    elif famille == "texte-ooxml":
        socle = _inventorier_docx(chemin, lire_parties(chemin))
    elif famille == "diapositives-ooxml":
        socle = _inventorier_pptx(
            chemin, lire_parties(chemin, "ppt/presentation.xml"))
    else:
        socle = _inventorier_odf(
            chemin, lire_parties(chemin, "content.xml"), famille)
    inv = dict(socle)
    inv["source"] = os.path.basename(chemin)
    inv["source_chemin"] = os.path.abspath(chemin)
    inv["format"] = fmt
    inv["famille"] = famille
    inv["remplissable"] = famille in REMPLISSABLES
    if not inv["remplissable"]:
        inv["motif_non_remplissable"] = MOTIF_NON_REMPLISSABLE.get(famille)
    inv["lacunes"] = lacunes_inventaire(inv)
    return inv


def lacunes_inventaire(inv):
    """Aveu de non-completude porte par l'inventaire lui-meme.

    Un inventaire lu par machine ne voit que ce qui est declaratif. Ce qui
    releve du code (macros), du rendu (polices reellement installees) ou d'une
    consigne ecrite ailleurs n'y figure pas et doit etre nomme comme absent.
    """
    famille = inv.get("famille", "texte-ooxml")
    manques = []
    if not inv.get("mise_en_page"):
        manques.append("aucune mise en page lisible dans le fichier")
    if famille in ("texte-ooxml", "texte-odf"):
        if not inv.get("hierarchie_titres"):
            manques.append("aucun style de titre reconnu, la hierarchie est a "
                           "declarer a la main")
        if not inv.get("entetes_et_pieds"):
            manques.append("aucun en-tete ni pied declare dans le gabarit")
    if famille == "diapositives-ooxml":
        if not inv.get("dispositions"):
            manques.append("aucune disposition lisible, le gabarit ne propose "
                           "pas de mise en page nommee")
        manques.append("la position et la taille exactes de chaque espace "
                       "reserve ne sont pas comparees, seule leur presence "
                       "l'est")
    if famille in ("texte-odf", "diapositives-odf"):
        manques.append("les styles automatiques nes d'une mise en forme "
                       "directe sont ignores, seuls les styles nommes du "
                       "document comptent comme regle")
    if famille == "page-fixe":
        manques.append("un PDF ne declare pas de marges : elles sont une "
                       "propriete du dessin, pas une donnee du fichier, et ne "
                       "sont donc pas inventoriees")
        manques.append("les objets ranges dans un flux compresse echappent a "
                       "la lecture binaire : un compte de pages absent se "
                       "declare plutot que de se deviner")
        if not inv.get("pages"):
            manques.append("nombre de pages illisible sur ce fichier")
    manques.append("les polices listees sont celles nommees dans le fichier, "
                   "leur presence sur la machine n'est pas verifiee")
    manques.append("une consigne de forme donnee hors du fichier (reglement "
                   "PDF, page web, courriel) n'est pas couverte par cet "
                   "inventaire")
    return manques


TYPES_ESPACE = {
    "title": "titre", "ctrTitle": "titre centre", "subTitle": "sous-titre",
    "body": "corps", "obj": "objet", "tbl": "tableau", "chart": "graphique",
    "pic": "image", "media": "media", "dt": "date", "ftr": "pied",
    "hdr": "en-tete", "sldNum": "numero de diapositive",
}


def _rels_de(parties, partie):
    """Cible de chaque relation d'une partie, par identifiant."""
    dossier, base = os.path.split(partie)
    cle = "%s/_rels/%s.rels" % (dossier, base)
    racine = _racine(parties, cle)
    if racine is None:
        return {}
    out = {}
    for rel in racine:
        rid, cible = rel.get("Id"), rel.get("Target")
        if not rid or not cible:
            continue
        if cible.startswith("/"):
            out[rid] = cible.lstrip("/")
        else:
            out[rid] = os.path.normpath(
                os.path.join(dossier, cible)).replace("\\", "/")
    return out


def _espaces_reserves(racine):
    """Espaces reserves d'une disposition ou d'une diapositive.

    Un espace reserve se designe par son type et son index. Le type seul ne
    suffit pas : une disposition a deux zones de corps porte deux fois le type
    body, que seul l'index distingue. Un espace sans type declare vaut corps,
    convention de la norme.
    """
    out = []
    if racine is None:
        return out
    for ph in racine.iter(_q(P, "ph")):
        t = ph.get("type") or "body"
        out.append({"type": t, "libelle": TYPES_ESPACE.get(t, t),
                    "index": ph.get("idx")})
    return out


def _texte_p(racine):
    if racine is None:
        return ""
    return " ".join(t.text or "" for t in racine.iter(_q(A, "t"))).strip()


def dispositions(parties):
    """Dispositions du gabarit, par nom, avec leurs espaces reserves.

    Le nom d'une disposition (attribut name de cSld) est l'identifiant stable
    cote PowerPoint : c'est lui que porte une diapositive qui s'en reclame.
    """
    out = {}
    for nom in sorted(parties):
        if not (nom.startswith("ppt/slideLayouts/")
                and nom.endswith(".xml")):
            continue
        racine = _racine(parties, nom)
        if racine is None:
            continue
        csld = racine.find(_q(P, "cSld"))
        libelle = (csld.get("name") if csld is not None else None) \
            or os.path.basename(nom)
        out[libelle] = {
            "nom": libelle,
            "partie": nom,
            "type": racine.get("type"),
            "espaces": _espaces_reserves(racine),
        }
    return out


def taille_diapositive(parties):
    """Dimensions de la diapositive en centimetres, et orientation."""
    racine = _racine(parties, "ppt/presentation.xml")
    if racine is None:
        return {}
    sz = racine.find(_q(P, "sldSz"))
    if sz is None:
        return {}
    out = {}
    for cle, dest in (("cx", "largeur"), ("cy", "hauteur")):
        brut = sz.get(cle)
        if brut:
            try:
                out[dest] = round(int(brut) / EMU_CM, 2)
            except ValueError:
                pass
    if out.get("largeur") and out.get("hauteur"):
        out["orientation"] = "paysage" if out["largeur"] >= out["hauteur"] \
            else "portrait"
        out["ratio"] = round(out["largeur"] / out["hauteur"], 3)
    return out


def diapositives(parties):
    """Diapositives presentes, avec la disposition dont chacune se reclame."""
    cartes = dispositions(parties)
    par_partie = {d["partie"]: d["nom"] for d in cartes.values()}
    out = []
    for nom in sorted(parties):
        if not (nom.startswith("ppt/slides/") and nom.endswith(".xml")):
            continue
        racine = _racine(parties, nom)
        if racine is None:
            continue
        disposition = None
        for cible in _rels_de(parties, nom).values():
            if cible in par_partie:
                disposition = par_partie[cible]
                break
        out.append({
            "partie": nom,
            "disposition": disposition,
            "espaces": _espaces_reserves(racine),
            "titre": _texte_p(racine)[:120],
            "images": len(list(racine.iter(_q(P, "pic")))),
        })
    return out


def _inventorier_pptx(chemin, parties):
    cartes = dispositions(parties)
    slides = diapositives(parties)
    inv = {
        "hierarchie_titres": {},
        "style_corps": None,
        "styles": [],
        "dispositions": [cartes[k] for k in sorted(cartes)],
        "diapositives": slides,
        "dispositions_employees": sorted(
            {s["disposition"] for s in slides if s["disposition"]}),
        "mise_en_page": taille_diapositive(parties),
        "entetes_et_pieds": [],
        "protection": None,
        "polices": polices(parties),
        "styles_utilises": {},
        "images_corps": sum(s["images"] for s in slides),
    }
    return inv


def _inventorier_odf(chemin, parties, famille):
    """Inventaire ODF : styles nommes, page maitresse, dimensions.

    Un ODF porte ses styles dans deux parties (styles.xml pour les styles de
    document, content.xml pour les styles automatiques nes d'une mise en forme
    directe). Seuls les premiers sont un gabarit : un style automatique est le
    residu d'un formatage manuel, pas une regle que l'auteur doit suivre.
    """
    cat, titres, corps = {}, {}, None
    racine = _racine(parties, "styles.xml")
    if racine is not None:
        for st in racine.iter(_q(STY, "style")):
            nom = st.get(_q(STY, "name"))
            if not nom:
                continue
            cat[nom] = {
                "id": nom,
                "type": st.get(_q(STY, "family")) or "paragraph",
                "nom": st.get(_q(STY, "display-name")) or nom,
                "base": st.get(_q(STY, "parent-style-name")),
                "suivant": st.get(_q(STY, "next-style-name")),
                "defaut": False,
            }
        for niveau in range(1, NIVEAUX_TITRE + 1):
            for cle in ("Heading_20_%d" % niveau, "Heading %d" % niveau,
                        "Titre_20_%d" % niveau):
                if cle in cat:
                    titres[str(niveau)] = cle
                    break
        for cle in ("Standard", "Default_20_Paragraph_20_Style",
                    "Text_20_body"):
            if cle in cat:
                corps = cle
                break
    mep = {}
    if racine is not None:
        for pl in racine.iter(_q(STY, "page-layout-properties")):
            for attr, dest in (("page-width", "largeur"),
                               ("page-height", "hauteur"),
                               ("margin-top", "top"),
                               ("margin-bottom", "bottom"),
                               ("margin-left", "left"),
                               ("margin-right", "right")):
                brut = pl.get(_q(FO, attr))
                val = _longueur_odf(brut)
                if val is not None and dest not in mep:
                    mep[dest] = val
            break
    if mep.get("largeur") and mep.get("hauteur"):
        mep["orientation"] = "paysage" if mep["largeur"] > mep["hauteur"] \
            else "portrait"
    employes = {}
    contenu = _racine(parties, "content.xml")
    if contenu is not None:
        for el in contenu.iter():
            nom = el.get(_q(TXT, "style-name"))
            if nom:
                employes[nom] = employes.get(nom, 0) + 1
    return {
        "styles": [cat[s] for s in sorted(cat)],
        "hierarchie_titres": titres,
        "style_corps": corps,
        "mise_en_page": mep,
        "entetes_et_pieds": [],
        "protection": None,
        "polices": _polices_odf(racine),
        "styles_utilises": employes,
        "images_corps": len(list(contenu.iter(
            "{urn:oasis:names:tc:opendocument:xmlns:drawing:1.0}image")))
        if contenu is not None else 0,
    }


def _longueur_odf(brut):
    """Convertit une longueur ODF (2cm, 0.79in, 56.7pt, 20mm) en centimetres."""
    if not brut:
        return None
    m = re.match(r"^(-?[\d.]+)\s*(cm|mm|in|pt|pc)$", brut.strip())
    if not m:
        return None
    val = float(m.group(1))
    facteur = {"cm": 1.0, "mm": 0.1, "in": 2.54, "pt": 2.54 / 72.0,
               "pc": 2.54 / 6.0}[m.group(2)]
    return round(val * facteur, 2)


def _polices_odf(racine):
    if racine is None:
        return []
    trouvees = set()
    for el in racine.iter(_q(STY, "font-face")):
        nom = el.get(_q(STY, "name"))
        if nom:
            trouvees.add(nom)
    return sorted(trouvees)


def _inventorier_pdf(chemin):
    """Inventaire d'un PDF, en lecture binaire directe, sans aucun moteur.

    Un PDF ne declare pas de styles nommes ni de marges : sa mise en page est
    deja composee. Ce qui reste verifiable est le cadre : format et orientation
    des pages, nombre de pages, polices nommees, chiffrement. Les marges d'un
    PDF ne sont pas une donnee du fichier, elles sont une propriete du dessin :
    l'inventaire ne les invente pas.

    La lecture par expression reguliere sur les octets ignore les objets ranges
    dans un flux compresse, frequents depuis PDF 1.5. Le compte de pages tombe
    alors a zero et l'inventaire le declare, plutot que de rendre un chiffre
    faux.
    """
    with open(chemin, "rb") as f:
        brut = f.read()
    version = None
    m = re.match(rb"%PDF-(\d\.\d)", brut[:16])
    if m:
        version = m.group(1).decode("ascii")

    pages = len(re.findall(rb"/Type\s*/Page[^s]", brut))
    compte_declare = None
    for m in re.finditer(rb"/Type\s*/Pages\b.{0,200}?/Count\s+(\d+)", brut,
                         re.S):
        compte_declare = int(m.group(1))
    if compte_declare:
        pages = max(pages, compte_declare)

    formats = {}
    for m in re.finditer(
            rb"/MediaBox\s*\[\s*(-?[\d.]+)\s+(-?[\d.]+)\s+"
            rb"(-?[\d.]+)\s+(-?[\d.]+)\s*\]", brut):
        x0, y0, x1, y1 = (float(g) for g in m.groups())
        # Un point PDF vaut 1/72 de pouce, soit 2,54/72 centimetres.
        larg = round(abs(x1 - x0) * 2.54 / 72.0, 2)
        haut = round(abs(y1 - y0) * 2.54 / 72.0, 2)
        formats[(larg, haut)] = formats.get((larg, haut), 0) + 1

    principal = {}
    if formats:
        (larg, haut), _n = max(formats.items(), key=lambda kv: kv[1])
        principal = {
            "largeur": larg, "hauteur": haut,
            "orientation": "paysage" if larg > haut else "portrait",
            "format_nomme": _format_nomme(larg, haut),
        }

    polices_pdf = sorted({
        m.group(1).decode("latin-1")
        for m in re.finditer(rb"/BaseFont\s*/([#\w+.-]+)", brut)})
    # Un nom de police incorpore porte un prefixe de six lettres et un plus.
    polices_nettes = sorted({
        p[7:] if re.match(r"^[A-Z]{6}\+", p) else p for p in polices_pdf})
    incorporees = [p for p in polices_pdf if re.match(r"^[A-Z]{6}\+", p)]

    return {
        "styles": [],
        "hierarchie_titres": {},
        "style_corps": None,
        "mise_en_page": principal,
        "pages": pages or None,
        "formats_de_page": [
            {"largeur": k[0], "hauteur": k[1], "pages": v}
            for k, v in sorted(formats.items())],
        "version_pdf": version,
        "chiffre": b"/Encrypt" in brut,
        "entetes_et_pieds": [],
        "protection": ({"edition": "chiffrement PDF", "applique": True,
                        "mot_de_passe": True} if b"/Encrypt" in brut else None),
        "polices": polices_nettes,
        "polices_incorporees": len(incorporees),
        "styles_utilises": {},
        "images_corps": len(re.findall(rb"/Subtype\s*/Image", brut)),
    }


FORMATS_NOMMES = {
    "A4": (21.0, 29.7), "A3": (29.7, 42.0), "A5": (14.85, 21.0),
    "A0": (84.1, 118.9), "A1": (59.4, 84.1), "A2": (42.0, 59.4),
    "Letter": (21.59, 27.94), "Legal": (21.59, 35.56),
}


def _format_nomme(largeur, hauteur, tolerance=0.3):
    """Nom normalise d'un format de page, ou None. L'orientation ne compte pas."""
    for nom, (l, h) in FORMATS_NOMMES.items():
        for a, b in ((l, h), (h, l)):
            if abs(largeur - a) <= tolerance and abs(hauteur - b) <= tolerance:
                return nom
    return None


def _ecart(gravite, regle, detail):
    return {"gravite": gravite, "regle": regle, "detail": detail}


def comparer(inv, chemin, tolerance_cm=0.1):
    """Confronte un document a l'inventaire d'un gabarit. Verdict ferme.

    Trois valeurs : conforme, ecarts mineurs, ecarts majeurs. Un style inconnu
    du gabarit ou une marge divergente sont majeurs (le rendu impose change).
    Un style structurant du gabarit jamais employe est mineur, un style
    seulement propose et non employe est informatif.

    Comparer un document a un gabarit d'une autre famille n'a pas de sens et
    s'arrete par un message nomme : les mesures ne portent pas sur les memes
    objets, et un verdict rendu malgre tout serait faux sans le dire.
    """
    fmt, famille = detecter_format(chemin)
    attendue = inv.get("famille", "texte-ooxml")
    if famille != attendue:
        raise SystemExit(
            "le gabarit est de famille %s et le document de famille %s : "
            "comparaison sans objet" % (attendue, famille))
    if famille == "diapositives-ooxml":
        return _comparer_pptx(inv, chemin, tolerance_cm)
    if famille == "page-fixe":
        return _comparer_pdf(inv, chemin, tolerance_cm)
    if famille in ("texte-odf", "diapositives-odf"):
        return _comparer_odf(inv, chemin, tolerance_cm)
    return _comparer_docx(inv, chemin, tolerance_cm)


def _envelopper(chemin, inv, ecarts, non_verifie):
    """Compte les gravites, rend le verdict ferme, emballe le rapport.

    Seuls majeur et mineur pesent sur le verdict. Le niveau info existe pour
    dire quelque chose de vrai sans le compter comme un manquement : un gabarit
    propose toujours plus qu'un document n'emploie.
    """
    majeurs = sum(1 for e in ecarts if e["gravite"] == "majeur")
    mineurs = sum(1 for e in ecarts if e["gravite"] == "mineur")
    if majeurs:
        verdict = "ecarts majeurs"
    elif mineurs:
        verdict = "ecarts mineurs"
    else:
        verdict = "conforme"
    return {
        "document": os.path.basename(chemin),
        "gabarit": inv.get("source"),
        "famille": inv.get("famille"),
        "verdict": verdict,
        "majeurs": majeurs,
        "mineurs": mineurs,
        "ecarts": ecarts,
        "non_verifie": non_verifie,
    }


def _ecarts_mise_en_page(attendue, obtenue, tolerance_cm, cles):
    ecarts = []
    for cle in cles:
        if cle not in attendue:
            continue
        if cle not in obtenue:
            ecarts.append(_ecart(
                "majeur", "mise en page absente",
                "la mesure %s du gabarit (%s cm) n'est pas declaree dans le "
                "document" % (cle, attendue[cle])))
            continue
        if abs(attendue[cle] - obtenue[cle]) > tolerance_cm:
            ecarts.append(_ecart(
                "majeur", "mise en page divergente",
                "%s : gabarit %s cm, document %s cm"
                % (cle, attendue[cle], obtenue[cle])))
    if attendue.get("orientation") and obtenue.get("orientation") \
            and attendue["orientation"] != obtenue["orientation"]:
        ecarts.append(_ecart(
            "majeur", "orientation divergente",
            "gabarit %s, document %s"
            % (attendue["orientation"], obtenue["orientation"])))
    return ecarts


def _comparer_pptx(inv, chemin, tolerance_cm=0.1):
    """Comparaison d'une presentation : dispositions, taille, espaces.

    L'identifiant stable est le nom de la disposition. Une diapositive qui se
    reclame d'une disposition absente du gabarit casse le modele, une
    diapositive sans disposition identifiable est un cas a regarder, une
    disposition proposee et jamais employee est normale.
    """
    parties = lire_parties(chemin, "ppt/presentation.xml")
    connues = {d["nom"] for d in inv.get("dispositions", [])}
    slides = diapositives(parties)
    ecarts = []

    for s in slides:
        if s["disposition"] is None:
            ecarts.append(_ecart(
                "mineur", "disposition non identifiable",
                "%s ne se reclame d'aucune disposition lisible"
                % os.path.basename(s["partie"])))
        elif s["disposition"] not in connues:
            ecarts.append(_ecart(
                "majeur", "disposition hors gabarit",
                "%s emploie la disposition %s, absente du gabarit"
                % (os.path.basename(s["partie"]), s["disposition"])))

    employees = {s["disposition"] for s in slides if s["disposition"]}
    for nom in sorted(connues - employees):
        ecarts.append(_ecart(
            "info", "disposition jamais employee",
            "le gabarit propose la disposition %s, aucune diapositive ne "
            "l'emploie" % nom))

    if not slides:
        ecarts.append(_ecart("mineur", "presentation vide",
                             "le document ne porte aucune diapositive"))

    ecarts += _ecarts_mise_en_page(
        inv.get("mise_en_page") or {}, taille_diapositive(parties),
        tolerance_cm, ("largeur", "hauteur"))

    # Espaces reserves d'une disposition non repris par la diapositive qui s'en
    # reclame : le modele prevoyait une zone que la diapositive laisse de cote.
    par_nom = {d["nom"]: d for d in inv.get("dispositions", [])}
    for s in slides:
        modele = par_nom.get(s["disposition"])
        if not modele:
            continue
        attendus = {e["type"] for e in modele["espaces"]}
        presents = {e["type"] for e in s["espaces"]}
        manquants = sorted(a for a in attendus - presents
                           if a in ("title", "ctrTitle", "body", "subTitle"))
        if manquants:
            ecarts.append(_ecart(
                "mineur", "espace reserve non repris",
                "%s laisse vides les zones %s prevues par %s"
                % (os.path.basename(s["partie"]),
                   ", ".join(TYPES_ESPACE.get(m, m) for m in manquants),
                   s["disposition"])))

    return _envelopper(chemin, inv, ecarts, [
        "le contenu redactionnel n'est pas juge ici, seule la forme l'est",
        "la position et la taille des espaces reserves ne sont pas mesurees",
        "le masque de diapositive et le theme ne sont pas compares",
    ])


def _comparer_pdf(inv, chemin, tolerance_cm=0.1):
    """Comparaison d'un PDF : format de page, orientation, pages, polices.

    Un PDF ne porte ni styles ni marges declarees : la comparaison se limite au
    cadre. Ce qui n'est pas mesurable est nomme dans non_verifie plutot que
    passe sous silence, pour qu'un verdict conforme ne se lise pas comme une
    conformite totale.
    """
    obtenu = _inventorier_pdf(chemin)
    ecarts = []
    ecarts += _ecarts_mise_en_page(
        inv.get("mise_en_page") or {}, obtenu.get("mise_en_page") or {},
        max(tolerance_cm, 0.2), ("largeur", "hauteur"))

    attendu_nom = (inv.get("mise_en_page") or {}).get("format_nomme")
    obtenu_nom = (obtenu.get("mise_en_page") or {}).get("format_nomme")
    if attendu_nom and obtenu_nom and attendu_nom != obtenu_nom:
        ecarts.append(_ecart("majeur", "format de page divergent",
                             "gabarit %s, document %s"
                             % (attendu_nom, obtenu_nom)))

    if len(obtenu.get("formats_de_page") or []) > 1:
        ecarts.append(_ecart(
            "mineur", "formats de page melanges",
            "le document mele %d formats de page differents"
            % len(obtenu["formats_de_page"])))

    limite = inv.get("pages_max")
    if limite and obtenu.get("pages") and obtenu["pages"] > limite:
        ecarts.append(_ecart(
            "majeur", "limite de pages depassee",
            "%d pages pour une limite de %d" % (obtenu["pages"], limite)))

    if obtenu.get("chiffre"):
        ecarts.append(_ecart(
            "mineur", "document chiffre",
            "le PDF est chiffre : son contenu n'a pas ete inspecte"))

    if obtenu.get("polices") and not obtenu.get("polices_incorporees"):
        ecarts.append(_ecart(
            "mineur", "aucune police incorporee",
            "aucun nom de police ne porte de prefixe de sous-ensemble : le "
            "rendu depend des polices installees chez le lecteur"))

    if obtenu.get("pages") is None:
        ecarts.append(_ecart(
            "info", "pagination illisible",
            "le compte de pages n'a pas pu se lire en binaire, probablement "
            "un flux d'objets compresse"))

    return _envelopper(chemin, inv, ecarts, [
        "les marges d'un PDF ne sont pas une donnee du fichier et ne se "
        "comparent pas",
        "le respect des styles de titre ne survit pas a l'export PDF",
        "l'integrite de lecture du texte se controle avec check-lecture-pdf.py",
    ])


def _comparer_odf(inv, chemin, tolerance_cm=0.1):
    """Comparaison ODF : styles nommes employes, dimensions, marges."""
    fmt, famille = detecter_format(chemin)
    obtenu = _inventorier_odf(chemin, lire_parties(chemin, "content.xml"),
                              famille)
    connus = {s["id"] for s in inv.get("styles", [])}
    # Un style automatique (P1, T2, Table1) est le residu d'une mise en forme
    # directe, jamais une regle du gabarit : le signaler comme hors gabarit
    # noierait le rapport sous des faux positifs.
    automatique = re.compile(r"^(P|T|Table|Sect|fr|gr|N)\d+$")
    ecarts = []
    for sid, n in sorted(obtenu.get("styles_utilises", {}).items()):
        if sid in connus or automatique.match(sid):
            continue
        ecarts.append(_ecart(
            "majeur", "style hors gabarit",
            "le style %s est applique %d fois et n'existe pas dans le gabarit"
            % (sid, n)))

    corps = inv.get("style_corps")
    titre1 = inv.get("hierarchie_titres", {}).get("1")
    for sid in (corps, titre1):
        if sid and sid not in obtenu.get("styles_utilises", {}):
            ecarts.append(_ecart(
                "mineur", "style du gabarit jamais employe",
                "le style %s est prevu par le gabarit et n'apparait pas"
                % sid))

    ecarts += _ecarts_mise_en_page(
        inv.get("mise_en_page") or {}, obtenu.get("mise_en_page") or {},
        tolerance_cm, ("top", "bottom", "left", "right", "largeur", "hauteur"))

    return _envelopper(chemin, inv, ecarts, [
        "le contenu redactionnel n'est pas juge ici, seule la forme l'est",
        "les styles automatiques nes d'une mise en forme directe sont ignores",
    ])


def _comparer_docx(inv, chemin, tolerance_cm=0.1):
    parties = lire_parties(chemin)
    connus = {s["id"] for s in inv.get("styles", [])}
    employes = styles_utilises(parties)
    ecarts = []

    inconnus = sorted(s for s in employes if s not in connus and s != "(defaut)")
    for sid in inconnus:
        ecarts.append(_ecart(
            "majeur", "style hors gabarit",
            "le style %s est applique %d fois et n'existe pas dans le gabarit"
            % (sid, employes[sid])))

    prevus = set(inv.get("hierarchie_titres", {}).values())
    corps = inv.get("style_corps")
    if corps:
        prevus.add(corps)
    # Un gabarit declare toujours plus de styles qu'un document n'en emploie.
    # Seuls le style de corps et le titre de premier niveau font exception :
    # un document qui ne les emploie jamais n'habite pas son gabarit.
    structurants = {corps, inv.get("hierarchie_titres", {}).get("1")}
    inutilises = sorted(s for s in prevus if s and s not in employes)
    for sid in inutilises:
        ecarts.append(_ecart(
            "mineur" if sid in structurants else "info",
            "style du gabarit jamais employe",
            "le style %s est prevu par le gabarit et n'apparait pas" % sid))

    ecarts += _ecarts_mise_en_page(
        inv.get("mise_en_page") or {}, mise_en_page(parties), tolerance_cm,
        ("top", "bottom", "left", "right", "largeur", "hauteur"))

    roles_attendus = {e["role"] for e in inv.get("entetes_et_pieds", [])}
    roles_obtenus = {e["role"] for e in entetes_et_pieds(parties)}
    for role in sorted(roles_attendus - roles_obtenus):
        ecarts.append(_ecart(
            "majeur", "en-tete ou pied manquant",
            "le gabarit declare un %s, le document n'en a pas" % role))

    return _envelopper(chemin, inv, ecarts, [
        "le contenu redactionnel n'est pas juge ici, seule la forme l'est",
        "un element de forme decrit hors du fichier gabarit echappe a cette "
        "comparaison",
    ])


def _echapper(txt):
    return (txt.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _paragraphe(texte, style):
    """Fragment de paragraphe OOXML, ecrit a la main.

    L'ecriture directe evite un aller-retour par ElementTree, qui renommerait
    les prefixes w: et r: en ns0: et ns1: sur toute la partie serialisee. Le
    fichier resterait valide, le diff deviendrait illisible.
    """
    pr = ""
    if style:
        pr = '<w:pPr><w:pStyle w:val="%s"/></w:pPr>' % _echapper(style)
    if not texte:
        return "<w:p>%s</w:p>" % pr
    return ('<w:p>%s<w:r><w:t xml:space="preserve">%s</w:t></w:r></w:p>'
            % (pr, _echapper(texte)))


def contenu_en_paragraphes(markdown, inv):
    """Traduit un Markdown simple en paragraphes styles du gabarit.

    Les titres # a ###### prennent le style de titre du niveau correspondant
    quand le gabarit en declare un. Un niveau sans style declare retombe sur le
    style de corps, avec un avertissement plutot qu'une invention de style.
    """
    titres = inv.get("hierarchie_titres", {})
    corps = inv.get("style_corps")
    fragments, avis = [], []
    bloc = []

    def vider():
        if bloc:
            fragments.append(_paragraphe(" ".join(bloc), corps))
            bloc.clear()

    for ligne in markdown.splitlines():
        nue = ligne.strip()
        if not nue:
            vider()
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", nue)
        if m:
            vider()
            niveau = str(len(m.group(1)))
            style = titres.get(niveau)
            if not style:
                style = corps
                avis.append("niveau de titre %s absent du gabarit, rendu en "
                            "style de corps" % niveau)
            fragments.append(_paragraphe(m.group(2), style))
            continue
        bloc.append(nue)
    vider()
    return fragments, sorted(set(avis))


def _prochain_rid(rels_xml):
    ids = [int(n) for n in re.findall(rb'Id="rId(\d+)"', rels_xml)]
    return "rId%d" % (max(ids) + 1 if ids else 1)


def _declarer_extension(ct_xml, ext):
    """Ajoute un Default de type MIME au manifeste s'il manque."""
    ext = ext.lower().lstrip(".")
    if b'Extension="%s"' % ext.encode() in ct_xml:
        return ct_xml
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "gif": "image/gif", "bmp": "image/bmp", "svg": "image/svg+xml",
            "emf": "image/x-emf", "wmf": "image/x-wmf",
            "tif": "image/tiff", "tiff": "image/tiff"}.get(ext)
    if not mime:
        return ct_xml
    ajout = b'<Default Extension="%s" ContentType="%s"/>' % (
        ext.encode(), mime.encode())
    m = re.search(rb"<Types[^>]*>", ct_xml)
    if not m:
        return ct_xml
    return ct_xml[:m.end()] + ajout + ct_xml[m.end():]


def _drawing(rid, largeur_emu, hauteur_emu, nom, ident):
    """Image inline, fragment ecrit a la main pour ne rien reserialiser."""
    return (
        '<w:p><w:r><w:drawing>'
        '<wp:inline distT="0" distB="0" distL="0" distR="0" '
        'xmlns:wp="%s">'
        '<wp:extent cx="%d" cy="%d"/>'
        '<wp:docPr id="%d" name="%s" descr="%s"/>'
        '<a:graphic xmlns:a="%s"><a:graphicData uri="%s">'
        '<pic:pic xmlns:pic="%s">'
        '<pic:nvPicPr><pic:cNvPr id="%d" name="%s"/><pic:cNvPicPr/></pic:nvPicPr>'
        '<pic:blipFill><a:blip xmlns:r="%s" r:embed="%s"/>'
        '<a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/>'
        '<a:ext cx="%d" cy="%d"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic></wp:inline>'
        '</w:drawing></w:r></w:p>'
        % (WP, largeur_emu, hauteur_emu, ident, _echapper(nom),
           _echapper(nom), A, PIC, PIC, ident, _echapper(nom), R, rid,
           largeur_emu, hauteur_emu))


def inserer_image(parties, chemin_image, largeur_cm=4.0, hauteur_cm=None,
                  ident=1000):
    """Ajoute une image au corps et rend le fragment de paragraphe a inserer.

    Trois ecritures : le binaire dans word/media, la relation dans le fichier
    de relations du document, l'extension dans le manifeste de types. Aucune
    partie n'est reserialisee, chaque ajout est une insertion ciblee.
    """
    if not os.path.isfile(chemin_image):
        raise SystemExit("image introuvable : %s" % chemin_image)
    donnees = open(chemin_image, "rb").read()
    ext = os.path.splitext(chemin_image)[1].lower().lstrip(".") or "png"
    base = "image_scriptorium_%d.%s" % (ident, ext)
    parties["word/media/%s" % base] = donnees

    cle_rels = "word/_rels/document.xml.rels"
    rels = parties.get(cle_rels)
    if rels is None:
        rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="%s"></Relationships>' % RELS).encode()
    rid = _prochain_rid(rels)
    ajout = ('<Relationship Id="%s" Type="http://schemas.openxmlformats.org/'
             'officeDocument/2006/relationships/image" Target="media/%s"/>'
             % (rid, base)).encode()
    parties[cle_rels] = rels.replace(b"</Relationships>",
                                     ajout + b"</Relationships>", 1)

    ct = parties.get("[Content_Types].xml")
    if ct is not None:
        parties["[Content_Types].xml"] = _declarer_extension(ct, ext)

    dims = dimensions_image(donnees)
    if hauteur_cm is None:
        if dims[0] and dims[1]:
            hauteur_cm = largeur_cm * dims[1] / float(dims[0])
        else:
            hauteur_cm = largeur_cm
    frag = _drawing(rid, int(largeur_cm * EMU_CM), int(hauteur_cm * EMU_CM),
                    os.path.basename(chemin_image), ident)
    return frag, {"fichier": os.path.basename(chemin_image),
                  "pixels": dims, "largeur_cm": round(largeur_cm, 2),
                  "hauteur_cm": round(hauteur_cm, 2)}


def dimensions_image(donnees):
    """Dimensions en pixels, deleguees a images.py pour ne pas les redire."""
    try:
        import importlib.util
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "images.py")
        spec = importlib.util.spec_from_file_location("images_mod", chemin)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        larg, haut, _fmt = mod.dimensions(donnees)
        return (larg, haut)
    except Exception:
        return (None, None)


def ecrire_docx(parties, sortie):
    """Reecrit le zip complet, entrees inchangees comprises."""
    dossier = os.path.dirname(os.path.abspath(sortie))
    if dossier and not os.path.isdir(dossier):
        os.makedirs(dossier)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    tmp.close()
    with zipfile.ZipFile(tmp.name, "w", zipfile.ZIP_DEFLATED) as z:
        for nom in parties:
            z.writestr(nom, parties[nom])
    shutil.move(tmp.name, sortie)
    return sortie


def remplir(inv, markdown, sortie, logo=None, logo_largeur_cm=4.0,
            source=None, disposition=None):
    """Injecte le contenu dans le gabarit lui-meme, sans le recreer.

    Le remplissage ne vaut que pour les familles ou l'ecriture est sure. Pour
    les autres, le refus est explicite et porte son motif : mieux vaut un arret
    nomme qu'un fichier approximatif que l'auteur croirait conforme.
    """
    chemin = source or inv.get("source_chemin")
    if not chemin or not os.path.isfile(chemin):
        raise SystemExit(
            "gabarit source introuvable (%s) : passer --source" % chemin)
    famille = inv.get("famille", "texte-ooxml")
    if famille not in REMPLISSABLES:
        raise SystemExit(
            "remplissage impossible pour un gabarit %s : %s"
            % (famille, MOTIF_NON_REMPLISSABLE.get(famille, "format non ecrit")))
    prot = inv.get("protection") or {}
    if prot.get("applique"):
        raise SystemExit(
            "gabarit protege en edition (%s) : le remplissage s'arrete plutot "
            "que de produire un fichier douteux"
            % (prot.get("edition") or "restriction declaree"))
    if famille == "diapositives-ooxml":
        return _remplir_pptx(inv, markdown, sortie, chemin, disposition,
                             logo, logo_largeur_cm)
    return _remplir_docx(inv, markdown, sortie, chemin, logo, logo_largeur_cm)


def _remplir_docx(inv, markdown, sortie, chemin, logo=None,
                  logo_largeur_cm=4.0):
    """Le contenu s'ajoute a la fin du corps, avant la derniere section.

    Rien n'est remplace : une page de garde, un sommaire ou un filigrane du
    gabarit survivent a l'operation. Le nettoyage des paragraphes de
    remplissage du modele reste un geste de l'auteur.
    """
    parties = lire_parties(chemin)
    doc = parties["word/document.xml"]
    fragments, avis = contenu_en_paragraphes(markdown, inv)
    rapport = {"sortie": sortie, "paragraphes": len(fragments),
               "avertissements": avis, "logo": None}

    if logo:
        frag_logo, meta = inserer_image(parties, logo, logo_largeur_cm)
        doc = parties["word/document.xml"]
        fragments.insert(0, frag_logo)
        rapport["logo"] = meta

    bloc = "".join(fragments).encode("utf-8")
    m = re.search(rb"<w:sectPr[ >]", doc)
    if m:
        doc = doc[:m.start()] + bloc + doc[m.start():]
    elif b"</w:body>" in doc:
        doc = doc.replace(b"</w:body>", bloc + b"</w:body>", 1)
    else:
        raise SystemExit("corps du document illisible, remplissage annule")
    parties["word/document.xml"] = doc
    ecrire_docx(parties, sortie)
    return rapport


def contenu_en_diapositives(markdown):
    """Decoupe un Markdown en diapositives : un titre de niveau 1 ou 2 en ouvre
    une, les lignes suivantes en forment le corps. Le texte avant le premier
    titre forme une diapositive sans titre plutot que d'etre perdu."""
    slides, courante = [], None
    for ligne in markdown.splitlines():
        nue = ligne.strip()
        m = re.match(r"^(#{1,2})\s+(.*)$", nue)
        if m:
            if courante:
                slides.append(courante)
            courante = {"titre": m.group(2), "corps": []}
            continue
        if not nue:
            continue
        if courante is None:
            courante = {"titre": None, "corps": []}
        courante["corps"].append(re.sub(r"^[-*]\s+", "", nue))
    if courante:
        slides.append(courante)
    return slides


def _choisir_disposition(inv, demandee):
    """Disposition d'accueil : celle demandee, sinon la premiere qui porte a la
    fois un titre et un corps, sinon la premiere declaree."""
    cartes = inv.get("dispositions") or []
    if not cartes:
        raise SystemExit("le gabarit ne declare aucune disposition")
    if demandee:
        for d in cartes:
            if d["nom"] == demandee:
                return d, None
        noms = ", ".join(d["nom"] for d in cartes)
        raise SystemExit("disposition %s absente du gabarit. Disponibles : %s"
                         % (demandee, noms))
    for d in cartes:
        types = {e["type"] for e in d["espaces"]}
        if types & {"title", "ctrTitle"} and "body" in types:
            return d, None
    return cartes[0], ("aucune disposition ne porte a la fois un titre et un "
                       "corps, la premiere declaree (%s) est employee"
                       % cartes[0]["nom"])


def _forme_texte(ident, nom, type_ph, index, lignes, largeur, hauteur,
                 decalage_y):
    """Forme de texte rattachee a un espace reserve de la disposition.

    La position et la taille viennent de l'espace reserve, pas d'un placement
    calcule ici : c'est ce qui fait qu'une diapositive produite ressemble au
    modele au lieu de le contredire.
    """
    idx = ' idx="%s"' % index if index else ""
    paras = "".join(
        '<a:p><a:r><a:rPr lang="fr-FR" dirty="0"/><a:t>%s</a:t></a:r></a:p>'
        % _echapper(l) for l in lignes) or "<a:p/>"
    return (
        '<p:sp><p:nvSpPr>'
        '<p:cNvPr id="%d" name="%s"/>'
        '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
        '<p:nvPr><p:ph type="%s"%s/></p:nvPr>'
        '</p:nvSpPr>'
        '<p:spPr><a:xfrm><a:off x="%d" y="%d"/><a:ext cx="%d" cy="%d"/>'
        '</a:xfrm></p:spPr>'
        '<p:txBody><a:bodyPr/><a:lstStyle/>%s</p:txBody></p:sp>'
        % (ident, _echapper(nom), type_ph, idx, int(0.08 * largeur),
           int(decalage_y), int(0.84 * largeur), int(hauteur), paras))


def _diapositive_xml(titre, corps, espaces, largeur_emu, hauteur_emu):
    """Diapositive complete, ecrite a la main, sans reserialisation."""
    formes, ident = [], 2
    types = {e["type"]: e for e in espaces}
    type_titre = "ctrTitle" if "ctrTitle" in types and "title" not in types \
        else "title"
    if titre:
        e = types.get(type_titre) or {}
        formes.append(_forme_texte(ident, "Titre", type_titre, e.get("index"),
                                   [titre], largeur_emu, 0.18 * hauteur_emu,
                                   0.08 * hauteur_emu))
        ident += 1
    if corps:
        e = types.get("body") or types.get("subTitle") or {}
        type_corps = "body" if "body" in types else (
            "subTitle" if "subTitle" in types else "body")
        formes.append(_forme_texte(ident, "Corps", type_corps, e.get("index"),
                                   corps, largeur_emu, 0.58 * hauteur_emu,
                                   0.30 * hauteur_emu))
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<p:sld xmlns:a="%s" xmlns:r="%s" xmlns:p="%s">'
        '<p:cSld><p:spTree>'
        '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/>'
        '</p:nvGrpSpPr>'
        '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
        '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
        '%s</p:spTree></p:cSld>'
        '<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'
        % (A, R, P, "".join(formes))).encode("utf-8")


def _remplir_pptx(inv, markdown, sortie, chemin, disposition=None,
                  logo=None, logo_largeur_cm=4.0):
    """Ajoute des diapositives au gabarit, dans une de ses dispositions.

    Quatre ecritures par diapositive : la partie elle-meme, ses relations vers
    la disposition, la declaration de type dans le manifeste, l'entree dans la
    liste de la presentation. En oublier une donne un fichier que PowerPoint
    refuse d'ouvrir ou ouvre en perdant la diapositive.
    """
    parties = lire_parties(chemin, "ppt/presentation.xml")
    modele, avis_disposition = _choisir_disposition(inv, disposition)
    slides = contenu_en_diapositives(markdown)
    avis = [avis_disposition] if avis_disposition else []
    if not slides:
        raise SystemExit("le contenu ne produit aucune diapositive")

    mep = inv.get("mise_en_page") or {}
    largeur = int((mep.get("largeur") or 25.4) * EMU_CM)
    hauteur = int((mep.get("hauteur") or 19.05) * EMU_CM)

    existants = [int(m.group(1)) for n in parties
                 for m in [re.match(r"ppt/slides/slide(\d+)\.xml$", n)] if m]
    depart = max(existants) + 1 if existants else 1

    pres = parties["ppt/presentation.xml"]
    rels_pres = parties.get("ppt/_rels/presentation.xml.rels", b"")
    ct = parties.get("[Content_Types].xml", b"")
    ids_existants = [int(m.group(1))
                     for m in re.finditer(rb'<p:sldId id="(\d+)"', pres)]
    prochain_id = max(ids_existants) + 1 if ids_existants else 256
    nouveaux = []

    for i, s in enumerate(slides):
        nom_partie = "ppt/slides/slide%d.xml" % (depart + i)
        parties[nom_partie] = _diapositive_xml(
            s["titre"], s["corps"], modele["espaces"], largeur, hauteur)
        parties["ppt/slides/_rels/slide%d.xml.rels" % (depart + i)] = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="%s"><Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/'
            'relationships/slideLayout" Target="../%s"/></Relationships>'
            % (RELS, modele["partie"].replace("ppt/", ""))).encode("utf-8")
        rid = _prochain_rid(rels_pres)
        rels_pres = rels_pres.replace(
            b"</Relationships>",
            ('<Relationship Id="%s" Type="http://schemas.openxmlformats.org/'
             'officeDocument/2006/relationships/slide" Target="slides/'
             'slide%d.xml"/>' % (rid, depart + i)).encode("utf-8")
            + b"</Relationships>", 1)
        ct = ct.replace(
            b"</Types>",
            ('<Override PartName="/%s" ContentType="application/vnd.'
             'openxmlformats-officedocument.presentationml.slide+xml"/>'
             % nom_partie).encode("utf-8") + b"</Types>", 1)
        nouveaux.append(b'<p:sldId id="%d" r:id="%s"/>'
                        % (prochain_id, rid.encode("ascii")))
        prochain_id += 1

    bloc = b"".join(nouveaux)
    if b"</p:sldIdLst>" in pres:
        pres = pres.replace(b"</p:sldIdLst>", bloc + b"</p:sldIdLst>", 1)
    else:
        m = re.search(rb"<p:sldMasterIdLst.*?</p:sldMasterIdLst>", pres, re.S)
        if not m:
            raise SystemExit("presentation.xml illisible, remplissage annule")
        pres = (pres[:m.end()] + b"<p:sldIdLst>" + bloc + b"</p:sldIdLst>"
                + pres[m.end():])

    parties["ppt/presentation.xml"] = pres
    parties["ppt/_rels/presentation.xml.rels"] = rels_pres
    parties["[Content_Types].xml"] = ct

    rapport = {"sortie": sortie, "diapositives": len(slides),
               "disposition": modele["nom"], "avertissements": avis,
               "logo": None}
    if logo:
        avis.append("le placement d'un logo en diapositive suit le masque du "
                    "gabarit : le poser par diapositive le dupliquerait")
    ecrire_docx(parties, sortie)
    return rapport


def _rendre_inventaire(inv):
    famille = inv.get("famille", "texte-ooxml")
    lignes = ["Gabarit : %s (%s, famille %s)"
              % (inv["source"], inv.get("format", "?"), famille), ""]
    mep = inv["mise_en_page"]

    if famille == "diapositives-ooxml":
        lignes.append("Dispositions declarees : %d"
                      % len(inv.get("dispositions") or []))
        for d in inv.get("dispositions") or []:
            zones = ", ".join(sorted({e["libelle"] for e in d["espaces"]}))
            lignes.append("  %-28s %s" % (d["nom"], zones or "aucune zone"))
        lignes.append("Diapositives : %d" % len(inv.get("diapositives") or []))
        if inv.get("dispositions_employees"):
            lignes.append("Dispositions employees : %s"
                          % ", ".join(inv["dispositions_employees"]))
        if mep:
            lignes.append("Diapositive : %s x %s cm, %s, ratio %s"
                          % (mep.get("largeur", "?"), mep.get("hauteur", "?"),
                             mep.get("orientation", "?"), mep.get("ratio", "?")))
    elif famille == "page-fixe":
        lignes.append("Version PDF : %s" % (inv.get("version_pdf") or "?"))
        lignes.append("Pages : %s" % (inv.get("pages") or "illisible"))
        if mep:
            lignes.append("Page : %s x %s cm, %s%s"
                          % (mep.get("largeur", "?"), mep.get("hauteur", "?"),
                             mep.get("orientation", "?"),
                             ", format %s" % mep["format_nomme"]
                             if mep.get("format_nomme") else ""))
        for f in inv.get("formats_de_page") or []:
            lignes.append("  %s x %s cm sur %d page(s)"
                          % (f["largeur"], f["hauteur"], f["pages"]))
        lignes.append("Polices incorporees : %d sur %d nommees"
                      % (inv.get("polices_incorporees", 0),
                         len(inv.get("polices") or [])))
        if inv.get("chiffre"):
            lignes.append("Chiffrement : present, contenu non inspecte")
    else:
        lignes.append("Styles declares : %d" % len(inv["styles"]))
        if inv["hierarchie_titres"]:
            paires = ", ".join(
                "%s=%s" % (n, s)
                for n, s in sorted(inv["hierarchie_titres"].items()))
            lignes.append("Titres : %s" % paires)
        else:
            lignes.append("Titres : aucun style de titre reconnu")
        lignes.append("Corps : %s" % (inv["style_corps"] or "non identifie"))
        if mep:
            lignes.append(
                "Page : %s x %s cm, %s, marges h%s b%s g%s d%s"
                % (mep.get("largeur", "?"), mep.get("hauteur", "?"),
                   mep.get("orientation", "portrait"), mep.get("top", "?"),
                   mep.get("bottom", "?"), mep.get("left", "?"),
                   mep.get("right", "?")))
        for e in inv["entetes_et_pieds"]:
            champs = (", champs " + "+".join(e["champs"])) if e["champs"] else ""
            lignes.append("%s : %s%s"
                          % (e["role"], e["texte"] or "(vide)", champs))

    if inv["polices"]:
        lignes.append("Polices nommees : %s" % ", ".join(inv["polices"][:12]))
    if inv["protection"]:
        lignes.append("Protection : %s%s"
                      % (inv["protection"].get("edition"),
                         " (appliquee)" if inv["protection"].get("applique")
                         else ""))
    if not inv.get("remplissable"):
        lignes.append("Remplissage : impossible, %s"
                      % inv.get("motif_non_remplissable", "format non ecrit"))
    lignes.append("")
    lignes.append("Ce que cet inventaire ne couvre pas :")
    for m in inv["lacunes"]:
        lignes.append("  - %s" % m)
    return "\n".join(lignes)


def _rendre_comparaison(rap):
    lignes = ["%s contre %s" % (rap["document"], rap["gabarit"]), ""]
    for e in rap["ecarts"]:
        lignes.append("  [%s] %s : %s"
                      % (e["gravite"], e["regle"], e["detail"]))
    if not rap["ecarts"]:
        lignes.append("  aucun ecart de forme releve")
    lignes.append("")
    lignes.append("Verdict : %s (%d majeurs, %d mineurs)"
                  % (rap["verdict"], rap["majeurs"], rap["mineurs"]))
    lignes.append("")
    lignes.append("Non verifie ici :")
    for m in rap["non_verifie"]:
        lignes.append("  - %s" % m)
    return "\n".join(lignes)


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Gabarits de document imposes : inventorier, comparer, "
                    "remplir.")
    sp = p.add_subparsers(dest="action")

    pi = sp.add_parser("inventorier", help="lire la structure d'un gabarit")
    pi.add_argument("gabarit")
    pi.add_argument("--out", help="fichier JSON de sortie")
    pi.add_argument("--format", choices=("text", "json"), default="text")

    pc = sp.add_parser("comparer", help="confronter un document a un gabarit")
    pc.add_argument("inventaire")
    pc.add_argument("document")
    pc.add_argument("--format", choices=("text", "json"), default="text")
    pc.add_argument("--strict", action="store_true",
                    help="code de sortie 1 des le premier ecart mineur")

    pr = sp.add_parser("remplir", help="injecter du contenu dans le gabarit")
    pr.add_argument("inventaire")
    pr.add_argument("contenu")
    pr.add_argument("--out", required=True)
    pr.add_argument("--source", help="gabarit source si deplace depuis "
                                     "l'inventaire")
    pr.add_argument("--logo")
    pr.add_argument("--logo-largeur-cm", type=float, default=4.0)
    pr.add_argument("--disposition",
                    help="nom de la disposition d'accueil (presentations)")
    pr.add_argument("--format", choices=("text", "json"), default="text")

    sp.add_parser("formats", help="formats reconnus et ce que chacun permet")

    a = p.parse_args(argv)
    if getattr(a, "action", None) == "formats":
        print("Formats reconnus par gabarit.py\n")
        for famille in ("texte-ooxml", "diapositives-ooxml", "texte-odf",
                        "diapositives-odf", "page-fixe"):
            exts = sorted(e for e, f in FAMILLES.items() if f == famille)
            actions = "inventorier, comparer"
            if famille in REMPLISSABLES:
                actions += ", remplir"
            print("  %-20s %-22s %s" % (famille, ".".join([""] + exts).strip("."),
                                        actions))
            motif = MOTIF_NON_REMPLISSABLE.get(famille)
            if motif:
                print("  %-20s %s" % ("", motif))
        return 0
    if not a.action:
        p.print_help()
        return 0

    if a.action == "inventorier":
        inv = inventorier(a.gabarit)
        if a.out:
            with open(a.out, "w", encoding="utf-8") as f:
                json.dump(inv, f, ensure_ascii=False, indent=2)
        if a.format == "json":
            print(json.dumps(inv, ensure_ascii=False, indent=2))
        else:
            print(_rendre_inventaire(inv))
            if a.out:
                print("\nInventaire ecrit dans %s" % a.out)
        return 0

    inv = json.load(open(a.inventaire, encoding="utf-8"))

    if a.action == "comparer":
        rap = comparer(inv, a.document)
        if a.format == "json":
            print(json.dumps(rap, ensure_ascii=False, indent=2))
        else:
            print(_rendre_comparaison(rap))
        if rap["majeurs"]:
            return 1
        return 1 if (a.strict and rap["mineurs"]) else 0

    if a.action == "remplir":
        markdown = open(a.contenu, encoding="utf-8").read()
        rap = remplir(inv, markdown, a.out, logo=a.logo,
                      logo_largeur_cm=a.logo_largeur_cm, source=a.source,
                      disposition=a.disposition)
        if a.format == "json":
            print(json.dumps(rap, ensure_ascii=False, indent=2))
        else:
            if "diapositives" in rap:
                print("%d diapositives ajoutees dans %s, disposition %s"
                      % (rap["diapositives"], rap["sortie"],
                         rap["disposition"]))
            else:
                print("%d paragraphes injectes dans %s"
                      % (rap["paragraphes"], rap["sortie"]))
            if rap.get("logo"):
                print("Logo : %s, %s cm de large"
                      % (rap["logo"]["fichier"], rap["logo"]["largeur_cm"]))
            for av in rap["avertissements"]:
                print("  avertissement : %s" % av)
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
