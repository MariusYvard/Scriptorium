#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gabarits de document imposes : inventorier, comparer, remplir.

Un .docx ou .dotx est un zip de fragments XML (OOXML, ECMA-376). Ce script les
lit avec la bibliotheque standard seule (zipfile, xml.etree), sans dependance.

Trois actions :
  inventorier  lit un gabarit fourni par un tiers (ecole, laboratoire, revue,
               client) et ecrit sa structure dans un JSON declaratif : styles
               nommes, hierarchie de titres, marges, en-tetes, pieds, champs.
  comparer     confronte un document produit a cet inventaire et rend un
               verdict ferme, avec les ecarts nommes un par un.
  remplir      injecte du contenu dans le gabarit lui-meme, dans ses styles
               existants, plutot que de generer un fichier neuf. Un gabarit
               porte des elements qu'une regeneration perdrait : filigrane,
               numerotation liee, theme de couleurs propre au modele.

La comparaison des styles se fait par identifiant (w:styleId), jamais par le
libelle affiche : un Word francise renomme les libelles, pas les identifiants.

Usage :
  python3 gabarit.py inventorier GABARIT.docx [--out INVENTAIRE.json]
  python3 gabarit.py comparer INVENTAIRE.json DOCUMENT.docx [--format text|json]
  python3 gabarit.py remplir INVENTAIRE.json CONTENU.md --out SORTIE.docx
                     [--logo FICHIER --logo-largeur-cm N]

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


def _q(ns, tag):
    return "{%s}%s" % (ns, tag)


def lire_parties(chemin):
    """Toutes les entrees du zip en memoire. Un docx est petit, la RAM suffit."""
    if not os.path.isfile(chemin):
        raise SystemExit("fichier introuvable : %s" % chemin)
    try:
        with zipfile.ZipFile(chemin) as z:
            noms = z.namelist()
            if "word/document.xml" not in noms:
                raise SystemExit(
                    "%s n'est pas un document Word (word/document.xml absent)"
                    % os.path.basename(chemin))
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
    for nom in ("word/styles.xml", "word/theme/theme1.xml"):
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


def inventorier(chemin):
    """Structure declarative d'un gabarit, prete a servir de reference."""
    parties = lire_parties(chemin)
    cat = styles(parties)
    inv = {
        "source": os.path.basename(chemin),
        "source_chemin": os.path.abspath(chemin),
        "format": os.path.splitext(chemin)[1].lower().lstrip("."),
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
    inv["lacunes"] = lacunes_inventaire(inv)
    return inv


def lacunes_inventaire(inv):
    """Aveu de non-completude porte par l'inventaire lui-meme.

    Un inventaire lu par machine ne voit que ce qui est declaratif. Ce qui
    releve du code (macros), du rendu (polices reellement installees) ou d'une
    consigne ecrite ailleurs n'y figure pas et doit etre nomme comme absent.
    """
    manques = []
    if not inv.get("hierarchie_titres"):
        manques.append("aucun style de titre reconnu, la hierarchie est a "
                       "declarer a la main")
    if not inv.get("entetes_et_pieds"):
        manques.append("aucun en-tete ni pied declare dans le gabarit")
    if not inv.get("mise_en_page"):
        manques.append("aucune section de mise en page lisible")
    manques.append("les polices listees sont celles nommees dans le fichier, "
                   "leur presence sur la machine n'est pas verifiee")
    manques.append("une consigne de forme donnee hors du fichier (PDF, page "
                   "web, courriel) n'est pas couverte par cet inventaire")
    return manques


def _ecart(gravite, regle, detail):
    return {"gravite": gravite, "regle": regle, "detail": detail}


def comparer(inv, chemin, tolerance_cm=0.1):
    """Confronte un document a l'inventaire d'un gabarit. Verdict ferme.

    Trois valeurs : conforme, ecarts mineurs, ecarts majeurs. Un style inconnu
    du gabarit ou une marge divergente sont majeurs (le rendu imprime change).
    Un style du gabarit jamais employe est mineur (le document est plus pauvre
    que le gabarit, il ne le viole pas).
    """
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

    attendue = inv.get("mise_en_page") or {}
    obtenue = mise_en_page(parties)
    for cle in ("top", "bottom", "left", "right", "largeur", "hauteur"):
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

    roles_attendus = {e["role"] for e in inv.get("entetes_et_pieds", [])}
    roles_obtenus = {e["role"] for e in entetes_et_pieds(parties)}
    for role in sorted(roles_attendus - roles_obtenus):
        ecarts.append(_ecart(
            "majeur", "en-tete ou pied manquant",
            "le gabarit declare un %s, le document n'en a pas" % role))

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
        "verdict": verdict,
        "majeurs": majeurs,
        "mineurs": mineurs,
        "ecarts": ecarts,
        "non_verifie": [
            "le contenu redactionnel n'est pas juge ici, seule la forme l'est",
            "un element de forme decrit hors du fichier gabarit echappe a "
            "cette comparaison",
        ],
    }


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
            source=None):
    """Injecte le contenu dans le gabarit lui-meme, styles existants compris.

    Le contenu s'ajoute a la fin du corps, avant la derniere section, plutot
    que de remplacer ce que le gabarit contient deja : une page de garde, un
    sommaire ou un filigrane du gabarit survivent a l'operation. Le nettoyage
    des paragraphes de remplissage reste un geste de l'auteur.
    """
    chemin = source or inv.get("source_chemin")
    if not chemin or not os.path.isfile(chemin):
        raise SystemExit(
            "gabarit source introuvable (%s) : passer --source" % chemin)
    prot = inv.get("protection") or {}
    if prot.get("applique"):
        raise SystemExit(
            "gabarit protege en edition (%s) : le remplissage s'arrete plutot "
            "que de produire un fichier douteux"
            % (prot.get("edition") or "restriction declaree"))

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


def _rendre_inventaire(inv):
    lignes = ["Gabarit : %s" % inv["source"], ""]
    lignes.append("Styles declares : %d" % len(inv["styles"]))
    if inv["hierarchie_titres"]:
        paires = ", ".join("%s=%s" % (n, s)
                           for n, s in sorted(inv["hierarchie_titres"].items()))
        lignes.append("Titres : %s" % paires)
    else:
        lignes.append("Titres : aucun style de titre reconnu")
    lignes.append("Corps : %s" % (inv["style_corps"] or "non identifie"))
    mep = inv["mise_en_page"]
    if mep:
        lignes.append(
            "Page : %s x %s cm, %s, marges h%s b%s g%s d%s"
            % (mep.get("largeur", "?"), mep.get("hauteur", "?"),
               mep.get("orientation", "portrait"), mep.get("top", "?"),
               mep.get("bottom", "?"), mep.get("left", "?"),
               mep.get("right", "?")))
    for e in inv["entetes_et_pieds"]:
        champs = (", champs " + "+".join(e["champs"])) if e["champs"] else ""
        lignes.append("%s : %s%s" % (e["role"], e["texte"] or "(vide)", champs))
    if inv["polices"]:
        lignes.append("Polices nommees : %s" % ", ".join(inv["polices"]))
    if inv["protection"]:
        lignes.append("Protection : %s%s"
                      % (inv["protection"].get("edition"),
                         " (appliquee)" if inv["protection"].get("applique")
                         else ""))
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
    pr.add_argument("--format", choices=("text", "json"), default="text")

    a = p.parse_args(argv)
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
                      logo_largeur_cm=a.logo_largeur_cm, source=a.source)
        if a.format == "json":
            print(json.dumps(rap, ensure_ascii=False, indent=2))
        else:
            print("%d paragraphes injectes dans %s"
                  % (rap["paragraphes"], rap["sortie"]))
            if rap["logo"]:
                print("Logo : %s, %s cm de large"
                      % (rap["logo"]["fichier"], rap["logo"]["largeur_cm"]))
            for av in rap["avertissements"]:
                print("  avertissement : %s" % av)
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
