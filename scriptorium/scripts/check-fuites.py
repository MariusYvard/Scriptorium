#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ce qu'un livrable trahit de son auteur, avant de l'envoyer.

Un document bureautique ne transporte pas que son texte. Il porte le nom de
qui l'a ecrit et de qui l'a modifie en dernier, celui de l'organisation, le
nombre de revisions, le temps d'edition cumule, parfois des commentaires et des
modifications suivies que personne n'a acceptees, parfois le chemin local d'un
fichier lie. Un PDF porte son dictionnaire Info et son XMP, et garde ses
versions anterieures quand il a ete modifie par mise a jour incrementale.

Ce script inspecte, il ne nettoie pas. Il dit ce que le fichier raconte pour
que l'auteur decide, plutot que d'effacer a sa place : supprimer une trace est
une decision editoriale, la reperer est une mesure.

Quatre familles lues avec la bibliotheque standard seule : texte OOXML
(.docx, .dotx, .docm), diapositives OOXML (.pptx, .potx, .pptm), ODF (.odt,
.ott, .odp, .otp) et PDF.

Chaque constat porte une confiance, parce qu'un champ rempli et un champ
present ne disent pas la meme chose :
  confirme    une valeur lisible identifie une personne, une organisation ou
              une machine.
  probable    une valeur existe et parait identifiante sans certitude.
  informatif  une structure est presente sans contenu lisible ici.
  douteux     le constat a de bonnes chances d'etre un faux positif, il est
              rapporte pour ne rien taire, pas pour etre corrige.

Usage :
  python3 check-fuites.py FICHIER [--format text|json] [--strict]
  python3 check-fuites.py FICHIER --auteur "Prenom Nom"
  python3 check-fuites.py FICHIER --langue-affichage en

Consultatif par defaut. Code de sortie 1 avec --strict des le premier constat
confirme.

Module importable : analyser(chemin, auteur=None, langue_affichage=None)
-> dict ; rapport_texte(r, langue_affichage=None) -> str. Sans
langue_affichage, le detail des constats est la chaine francaise d'origine a
l'octet pres : c'est elle que serialise --format json. Le verdict, le nom de
regle, la confiance et la categorie restent des valeurs machine francaises
dans les deux cas. Le fichier inspecte est un binaire bureautique, il ne
porte pas de pragme de langue : l'affichage part donc du francais.
"""
import argparse
import importlib.util
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
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


CP = "http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
DC = "http://purl.org/dc/elements/1.1/"
DCT = "http://purl.org/dc/terms/"
EP = ("http://schemas.openxmlformats.org/officeDocument/2006/"
      "extended-properties")
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
OFF = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
META = "urn:oasis:names:tc:opendocument:xmlns:meta:1.0"

CONFIRME, PROBABLE, INFORMATIF, DOUTEUX = (
    "confirme", "probable", "informatif", "douteux")
ORDRE_CONFIANCE = {CONFIRME: 0, PROBABLE: 1, INFORMATIF: 2, DOUTEUX: 3}

# Valeurs si courantes qu'elles n'identifient personne.
GENERIQUES = {"", "user", "utilisateur", "admin", "administrateur", "unknown",
              "inconnu", "author", "auteur", "windows user", "microsoft office",
              "libreoffice", "openoffice", "word", "writer"}


def _q(ns, tag):
    return "{%s}%s" % (ns, tag)


def _constat(regle, detail, confiance, valeur=None, quoi=None):
    return {"regle": regle, "detail": detail, "confiance": confiance,
            "valeur": valeur, "categorie": quoi or "identite"}


def _identifiante(valeur, auteur_declare=None):
    """Confiance d'une valeur de champ d'identite.

    Un nom vide ou generique ne trahit rien. Un nom egal a l'auteur declare du
    document ne fuit rien non plus : il est deja public sur la page de garde,
    le signaler serait un faux positif.
    """
    if valeur is None:
        return None
    v = valeur.strip()
    if not v or v.lower() in GENERIQUES:
        return None
    if auteur_declare and v.lower() == auteur_declare.strip().lower():
        return DOUTEUX
    # Deux mots capitalises, ou un point dans un identifiant, sentent le nom.
    if re.match(r"^[A-ZÀ-Ý][\w'-]+\s+[A-ZÀ-Ý][\w'-]+", v) or "." in v \
            or "@" in v:
        return CONFIRME
    return PROBABLE


def detecter_format(chemin, langue_affichage=None):
    """Format et famille, par le contenu d'abord, l'extension ensuite."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    if not os.path.isfile(chemin):
        raise SystemExit(lib.t("fuites.err_introuvable", la, chemin=chemin))
    with open(chemin, "rb") as f:
        tete = f.read(8)
    if tete[:5] == b"%PDF-":
        return "pdf", "page-fixe"
    if tete[:2] != b"PK":
        raise SystemExit(lib.t("fuites.err_format", la,
                               fichier=os.path.basename(chemin)))
    with zipfile.ZipFile(chemin) as z:
        noms = set(z.namelist())
    if "word/document.xml" in noms:
        return "docx", "texte-ooxml"
    if "ppt/presentation.xml" in noms:
        return "pptx", "diapositives-ooxml"
    if "content.xml" in noms:
        return "odf", "odf"
    raise SystemExit(lib.t("fuites.err_archive", la,
                           fichier=os.path.basename(chemin)))


def _parties(chemin):
    with zipfile.ZipFile(chemin) as z:
        return {n: z.read(n) for n in z.namelist()}


def _racine(parties, nom):
    brut = parties.get(nom)
    if brut is None:
        return None
    try:
        return ET.fromstring(brut)
    except ET.ParseError:
        return None


# Le troisieme element de chaque champ est une CLE de libelle, pas un
# libelle : le detail imprime se compose au moment du constat, dans la langue
# d'affichage demandee.
CHAMPS_CORE = [
    (DC, "creator", "fuites.d.auteur_origine"),
    (CP, "lastModifiedBy", "fuites.d.dernier_enregistrement"),
    (DC, "title", "fuites.d.titre"),
    (DC, "subject", "fuites.d.sujet"),
    (DC, "description", "fuites.d.description"),
    (CP, "keywords", "fuites.d.mots_cles"),
    (CP, "category", "fuites.d.categorie"),
]

CHAMPS_APP = [
    ("Company", "fuites.d.organisation"),
    ("Manager", "fuites.d.responsable"),
    ("Application", "fuites.d.logiciel_production"),
    ("Template", "fuites.d.gabarit"),
]


def _fuites_ooxml(parties, auteur, lib, la):
    """Proprietes de document, revisions et residus de travail OOXML."""
    constats = []
    core = _racine(parties, "docProps/core.xml")
    if core is not None:
        for ns, tag, cle in CHAMPS_CORE:
            el = core.find(_q(ns, tag))
            if el is None or not (el.text or "").strip():
                continue
            valeur = el.text.strip()
            if tag in ("creator", "lastModifiedBy"):
                conf = _identifiante(valeur, auteur)
                if conf is None:
                    continue
            else:
                conf = PROBABLE if len(valeur) > 3 else INFORMATIF
            constats.append(_constat(
                "propriete de document", lib.t(cle, la), conf, valeur))
        rev = core.find(_q(CP, "revision"))
        if rev is not None and (rev.text or "").strip().isdigit():
            n = int(rev.text.strip())
            if n > 1:
                constats.append(_constat(
                    "historique d'edition",
                    lib.t("fuites.d.enregistrements", la, n=n),
                    PROBABLE if n >= 10 else INFORMATIF, str(n), "historique"))

    app = _racine(parties, "docProps/app.xml")
    if app is not None:
        for tag, cle in CHAMPS_APP:
            el = app.find(_q(EP, tag))
            if el is None or not (el.text or "").strip():
                continue
            valeur = el.text.strip()
            conf = (_identifiante(valeur, auteur) if tag in ("Company",
                                                             "Manager")
                    else INFORMATIF)
            if conf is None:
                continue
            constats.append(_constat(
                "propriete de document", lib.t(cle, la), conf, valeur))
        tt = app.find(_q(EP, "TotalTime"))
        if tt is not None and (tt.text or "").strip().isdigit():
            minutes = int(tt.text.strip())
            if minutes > 0:
                constats.append(_constat(
                    "historique d'edition",
                    lib.t("fuites.d.temps_edition", la, n=minutes),
                    PROBABLE if minutes >= 60 else INFORMATIF,
                    str(minutes), "historique"))
    return constats


def _residus_docx(parties, lib, la):
    """Ce qui reste du travail : revisions, commentaires, texte masque.

    Une modification suivie non acceptee affiche a un tiers ce que l'auteur a
    hesite a ecrire. Un commentaire oublie nomme son auteur et sa remarque.
    Les deux partent avec le fichier et se voient a l'ouverture.
    """
    constats = []
    doc = _racine(parties, "word/document.xml")
    if doc is not None:
        ins = len(list(doc.iter(_q(W, "ins"))))
        dele = len(list(doc.iter(_q(W, "del"))))
        if ins or dele:
            constats.append(_constat(
                "modifications suivies",
                lib.t("fuites.d.modifications_suivies", la, insertions=ins,
                      suppressions=dele), CONFIRME,
                "%d/%d" % (ins, dele), "residu"))
        masque = len(list(doc.iter(_q(W, "vanish"))))
        if masque:
            constats.append(_constat(
                "texte masque",
                lib.t("fuites.d.texte_masque", la, n=masque),
                PROBABLE, str(masque), "residu"))
    commentaires = _racine(parties, "word/comments.xml")
    if commentaires is not None:
        n = len(list(commentaires.iter(_q(W, "comment"))))
        auteurs = sorted({c.get(_q(W, "author")) or ""
                          for c in commentaires.iter(_q(W, "comment"))}
                         - {""})
        if n:
            constats.append(_constat(
                "commentaires",
                lib.t("fuites.d.commentaires_docx", la, n=n,
                      auteurs=lib.t("fuites.d.commentaires_auteurs", la,
                                    auteurs=", ".join(auteurs))
                      if auteurs else ""),
                CONFIRME, ", ".join(auteurs) or str(n), "residu"))
    if any(n.startswith("customXml/") for n in parties):
        constats.append(_constat(
            "donnees applicatives", lib.t("fuites.d.custom_xml", la),
            INFORMATIF, None, "residu"))
    if "word/people.xml" in parties:
        gens = _racine(parties, "word/people.xml")
        noms = sorted({e.get(_q(W, "author")) or ""
                       for e in (gens.iter() if gens is not None else [])}
                      - {""})
        if noms:
            constats.append(_constat(
                "collaborateurs",
                lib.t("fuites.d.collaborateurs", la, noms=", ".join(noms)),
                CONFIRME, ", ".join(noms), "residu"))
    return constats


def _residus_pptx(parties, lib, la):
    """Notes du presentateur et commentaires d'une presentation."""
    constats = []
    notes = [n for n in parties if n.startswith("ppt/notesSlides/")
             and n.endswith(".xml")]
    avec_texte = 0
    for n in notes:
        r = _racine(parties, n)
        if r is None:
            continue
        txt = "".join(t.text or "" for t in r.iter(
            "{http://schemas.openxmlformats.org/drawingml/2006/main}t")).strip()
        if txt:
            avec_texte += 1
    if avec_texte:
        constats.append(_constat(
            "notes du presentateur",
            lib.t("fuites.d.notes_presentateur", la, n=avec_texte),
            CONFIRME, str(avec_texte), "residu"))
    coms = [n for n in parties if "comment" in n.lower()
            and n.startswith("ppt/") and n.endswith(".xml")]
    if coms:
        constats.append(_constat(
            "commentaires",
            lib.t("fuites.d.commentaires_pptx", la, n=len(coms)),
            PROBABLE, str(len(coms)), "residu"))
    return constats


# Un chemin local dans une relation trahit l'arborescence de la machine.
CHEMIN_LOCAL = re.compile(
    rb'Target="(file:///[^"]+|[A-Za-z]:[\\/][^"]+|\.\./[^"]*/Users/[^"]+)"')


def _chemins_locaux(parties, lib, la):
    constats = []
    vus = set()
    for nom, brut in parties.items():
        if not nom.endswith(".rels"):
            continue
        for m in CHEMIN_LOCAL.finditer(brut):
            chemin = m.group(1).decode("utf-8", "replace")
            if chemin in vus:
                continue
            vus.add(chemin)
            constats.append(_constat(
                "chemin local", lib.t("fuites.d.chemin_local", la),
                CONFIRME, chemin, "chemin"))
    return constats[:10]


def _fuites_odf(parties, auteur, lib, la):
    """Metadonnees ODF : meta.xml porte l'identite et les compteurs."""
    constats = []
    r = _racine(parties, "meta.xml")
    if r is None:
        return constats
    champs = [
        (META, "initial-creator", "fuites.d.auteur_origine", True),
        (DC, "creator", "fuites.d.dernier_enregistrement", True),
        (META, "generator", "fuites.d.logiciel_production", False),
        (DC, "title", "fuites.d.titre", False),
        (DC, "subject", "fuites.d.sujet", False),
    ]
    for ns, tag, cle, identite in champs:
        for el in r.iter(_q(ns, tag)):
            valeur = (el.text or "").strip()
            if not valeur:
                continue
            conf = (_identifiante(valeur, auteur) if identite
                    else INFORMATIF)
            if conf is None:
                continue
            constats.append(_constat(
                "propriete de document", lib.t(cle, la), conf, valeur))
            break
    for el in r.iter(_q(META, "editing-cycles")):
        v = (el.text or "").strip()
        if v.isdigit() and int(v) > 1:
            constats.append(_constat(
                "historique d'edition",
                lib.t("fuites.d.enregistrements", la, n=v),
                PROBABLE if int(v) >= 10 else INFORMATIF, v, "historique"))
        break
    for el in r.iter(_q(META, "editing-duration")):
        v = (el.text or "").strip()
        if v and v not in ("PT0S", "P0D"):
            constats.append(_constat(
                "historique d'edition",
                lib.t("fuites.d.duree_edition", la, duree=v),
                INFORMATIF, v, "historique"))
        break
    # Un ODF garde ses modifications suivies dans content.xml.
    contenu = _racine(parties, "content.xml")
    if contenu is not None:
        tracked = len(list(contenu.iter(
            "{urn:oasis:names:tc:opendocument:xmlns:text:1.0}"
            "tracked-changes")))
        if tracked:
            constats.append(_constat(
                "modifications suivies",
                lib.t("fuites.d.registre_suivi", la),
                CONFIRME, None, "residu"))
    return constats


CHAMPS_PDF = [
    (rb"/Author\s*\(([^)]{1,200})\)", "fuites.d.auteur_declare", True),
    (rb"/Creator\s*\(([^)]{1,200})\)", "fuites.d.logiciel_creation", False),
    (rb"/Producer\s*\(([^)]{1,200})\)", "fuites.d.logiciel_production", False),
    (rb"/Title\s*\(([^)]{1,200})\)", "fuites.d.titre", False),
    (rb"/Keywords\s*\(([^)]{1,200})\)", "fuites.d.mots_cles", False),
    (rb"/Subject\s*\(([^)]{1,200})\)", "fuites.d.sujet", False),
]


def _fuites_pdf(chemin, auteur, lib, la):
    """Dictionnaire Info, XMP, et surtout l'etat incremental du fichier.

    Le piege : un outil de nettoyage de metadonnees comme exiftool ecrit dans
    un PDF de facon INCREMENTALE. Il ajoute un bloc de mise a jour qui libere
    l'objet Info et le retire du trailer, mais les octets d'origine restent
    dans le fichier, verbatim et recuperables. La commande sort en succes, le
    lecteur n'affiche plus rien, et le fichier GROSSIT au lieu de maigrir :
    c'est le signe. Croire une metadonnee supprimee alors qu'elle est encore
    lisible ferme la verification, ce qui est pire que de la savoir presente.

    Un PDF a mise a jour incrementale porte plusieurs %%EOF et une chaine de
    tables xref reliees par /Prev. C'est parfaitement legitime en soi (une
    signature electronique procede ainsi), mais cela veut dire que l'etat
    anterieur du document est toujours dans le fichier.
    """
    constats = []
    with open(chemin, "rb") as f:
        brut = f.read()

    for motif, cle, identite in CHAMPS_PDF:
        m = re.search(motif, brut)
        if not m:
            continue
        valeur = m.group(1).decode("latin-1", "replace").strip()
        if not valeur:
            continue
        conf = _identifiante(valeur, auteur) if identite else INFORMATIF
        if conf is None:
            continue
        constats.append(_constat("propriete de document", lib.t(cle, la),
                                 conf, valeur))

    eof = len(re.findall(rb"%%EOF", brut))
    prev = len(re.findall(rb"/Prev\s+\d+", brut))
    if eof > 1 or prev:
        constats.append(_constat(
            "mise a jour incrementale",
            lib.t("fuites.d.incremental", la, eof=eof, prev=prev),
            CONFIRME if (eof > 1 and prev) else PROBABLE,
            "%d %%EOF, %d /Prev" % (eof, prev), "integrite"))

    if re.search(rb"<x:xmpmeta", brut):
        auteurs_xmp = re.findall(rb"<dc:creator>.{0,300}?</dc:creator>", brut,
                                 re.S)
        constats.append(_constat(
            "metadonnees XMP",
            lib.t("fuites.d.xmp", la,
                  auteur=lib.t("fuites.d.xmp_auteur", la)
                  if auteurs_xmp else ""),
            PROBABLE if auteurs_xmp else INFORMATIF, None))

    if b"/Encrypt" in brut:
        constats.append(_constat(
            "chiffrement", lib.t("fuites.d.chiffrement", la),
            INFORMATIF, None, "integrite"))

    if re.search(rb"/Type\s*/EmbeddedFile", brut):
        constats.append(_constat(
            "fichier embarque", lib.t("fuites.d.fichier_embarque", la),
            CONFIRME, None, "residu"))

    if re.search(rb"/Annots", brut) and re.search(rb"/Subtype\s*/Text", brut):
        constats.append(_constat(
            "commentaires", lib.t("fuites.d.annotations", la),
            PROBABLE, None, "residu"))
    return constats


def analyser(chemin, auteur=None, langue_affichage=None):
    """Inventaire de ce que le fichier trahit. N'ecrit jamais, ne nettoie pas.

    Sans langue_affichage, le detail de chaque constat et la liste des angles
    morts sont les chaines francaises d'origine a l'octet pres : ce sont
    elles que serialise le mode --format json."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    fmt, famille = detecter_format(chemin, la)
    constats = []
    if famille == "page-fixe":
        constats += _fuites_pdf(chemin, auteur, lib, la)
    else:
        parties = _parties(chemin)
        if famille == "odf":
            constats += _fuites_odf(parties, auteur, lib, la)
        else:
            constats += _fuites_ooxml(parties, auteur, lib, la)
            constats += (_residus_docx(parties, lib, la)
                         if famille == "texte-ooxml"
                         else _residus_pptx(parties, lib, la))
        constats += _chemins_locaux(parties, lib, la)

    constats.sort(key=lambda c: (ORDRE_CONFIANCE[c["confiance"]], c["regle"]))
    comptes = {niveau: sum(1 for c in constats if c["confiance"] == niveau)
               for niveau in (CONFIRME, PROBABLE, INFORMATIF, DOUTEUX)}
    if comptes[CONFIRME]:
        verdict = "fuites confirmees"
    elif comptes[PROBABLE]:
        verdict = "fuites probables"
    elif comptes[INFORMATIF]:
        verdict = "traces sans identite lisible"
    else:
        verdict = "rien a signaler"

    return {
        "fichier": os.path.basename(chemin),
        "format": fmt,
        "famille": famille,
        "verdict": verdict,
        "comptes": comptes,
        "constats": constats,
        "non_verifie": _non_verifie(famille, lib, la),
    }


def _non_verifie(famille, lib, la):
    """Ce que ce controle ne regarde pas, dit plutot que taise.

    Un rapport qui ne nomme pas ses angles morts se lit comme un quitus.
    """
    commun = [lib.t("fuites.nv.contenu", la), lib.t("fuites.nv.images", la)]
    if famille == "page-fixe":
        return commun + [lib.t("fuites.nv.pdf_chiffre", la),
                         lib.t("fuites.nv.flux_compresse", la)]
    return commun + [lib.t("fuites.nv.macros", la),
                     lib.t("fuites.nv.champ_non_standard", la)]


# Categories de constat, dans l'ordre ou le rapport les presente. La cle est
# la valeur machine portee par le constat, elle ne change pas de langue ; la
# valeur est la cle du libelle de son titre.
CATEGORIES = (
    ("identite", "fuites.cat.identite"),
    ("residu", "fuites.cat.residu"),
    ("integrite", "fuites.cat.integrite"),
    ("historique", "fuites.cat.historique"),
    ("chemin", "fuites.cat.chemin"),
)


def rapport_texte(r, langue_affichage=None):
    """Rendu texte. Le detail de chaque constat a ete compose dans la langue
    d'affichage par analyser() : il est repris tel quel. La confiance, le nom
    de regle et le verdict sont des valeurs machine, traduites ici par la
    table VALEURS et jamais dans les donnees."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    lignes = [lib.t("fuites.entete", la, fichier=r["fichier"],
                    verdict=lib.valeur("fuites.verdict", r["verdict"], la)),
              ""]
    if not r["constats"]:
        lignes.append("  " + lib.t("fuites.aucune_trace", la))
    par_categorie = {}
    for c in r["constats"]:
        par_categorie.setdefault(c["categorie"], []).append(c)
    for cat, cle_titre in CATEGORIES:
        groupe = par_categorie.get(cat)
        if not groupe:
            continue
        lignes.append("  " + lib.t(cle_titre, la))
        for c in groupe:
            valeur = (lib.t("fuites.valeur", la, valeur=c["valeur"])
                      if c["valeur"] else "")
            lignes.append("    " + lib.t(
                "fuites.constat", la,
                confiance=lib.valeur("fuites.confiance", c["confiance"], la),
                regle=lib.valeur("fuites.regle", c["regle"], la),
                detail=c["detail"], valeur=valeur))
        lignes.append("")
    lignes.append("  " + lib.t(
        "fuites.comptes", la, confirmes=r["comptes"][CONFIRME],
        probables=r["comptes"][PROBABLE], informatifs=r["comptes"][INFORMATIF],
        douteux=r["comptes"][DOUTEUX]))
    lignes.append("")
    lignes.append(lib.t("fuites.partage", la))
    lignes.append("")
    lignes.append(lib.t("fuites.non_verifie", la))
    for m in r["non_verifie"]:
        lignes.append("  - %s" % m)
    return "\n".join(lignes)


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Inventaire de ce qu'un livrable trahit de son auteur "
                    "avant envoi : proprietes de document, residus de "
                    "travail, chemins locaux, integrite du fichier.")
    p.add_argument("fichier")
    p.add_argument("--auteur",
                   help="auteur declare du document ; un champ qui porte ce "
                        "nom n'est pas compte comme une fuite")
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--strict", action="store_true",
                   help="code de sortie 1 des le premier constat confirme")
    p.add_argument("--langue-affichage", choices=("fr", "en"), default=None,
                   help="langue des libelles du rapport texte (defaut fr : un "
                        "binaire bureautique ne porte pas de pragme de "
                        "langue). La sortie JSON reste francaise quoi qu'il "
                        "arrive")
    a = p.parse_args(argv)

    if a.format == "json":
        # Le JSON ne se traduit pas : les evals et le jeu d'or le lisent.
        r = analyser(a.fichier, a.auteur)
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        la = _lib().resoudre_affichage(a.langue_affichage)
        r = analyser(a.fichier, a.auteur, la)
        print(rapport_texte(r, la))
    return 1 if (a.strict and r["comptes"][CONFIRME]) else 0


if __name__ == "__main__":
    sys.exit(main())
