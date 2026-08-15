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

Consultatif par defaut. Code de sortie 1 avec --strict des le premier constat
confirme.
"""
import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

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


def detecter_format(chemin):
    """Format et famille, par le contenu d'abord, l'extension ensuite."""
    if not os.path.isfile(chemin):
        raise SystemExit("fichier introuvable : %s" % chemin)
    with open(chemin, "rb") as f:
        tete = f.read(8)
    if tete[:5] == b"%PDF-":
        return "pdf", "page-fixe"
    if tete[:2] != b"PK":
        raise SystemExit(
            "%s n'est ni un PDF ni une archive : format non couvert"
            % os.path.basename(chemin))
    with zipfile.ZipFile(chemin) as z:
        noms = set(z.namelist())
    if "word/document.xml" in noms:
        return "docx", "texte-ooxml"
    if "ppt/presentation.xml" in noms:
        return "pptx", "diapositives-ooxml"
    if "content.xml" in noms:
        return "odf", "odf"
    raise SystemExit("%s est une archive d'un format non couvert"
                     % os.path.basename(chemin))


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


CHAMPS_CORE = [
    (DC, "creator", "auteur d'origine"),
    (CP, "lastModifiedBy", "derniere personne a avoir enregistre"),
    (DC, "title", "titre enregistre dans le fichier"),
    (DC, "subject", "sujet enregistre"),
    (DC, "description", "description enregistree"),
    (CP, "keywords", "mots-cles enregistres"),
    (CP, "category", "categorie enregistree"),
]

CHAMPS_APP = [
    ("Company", "organisation"),
    ("Manager", "responsable declare"),
    ("Application", "logiciel de production"),
    ("Template", "gabarit d'origine"),
]


def _fuites_ooxml(parties, auteur):
    """Proprietes de document, revisions et residus de travail OOXML."""
    constats = []
    core = _racine(parties, "docProps/core.xml")
    if core is not None:
        for ns, tag, libelle in CHAMPS_CORE:
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
                "propriete de document", libelle, conf, valeur))
        rev = core.find(_q(CP, "revision"))
        if rev is not None and (rev.text or "").strip().isdigit():
            n = int(rev.text.strip())
            if n > 1:
                constats.append(_constat(
                    "historique d'edition",
                    "le fichier declare %d enregistrements successifs" % n,
                    PROBABLE if n >= 10 else INFORMATIF, str(n), "historique"))

    app = _racine(parties, "docProps/app.xml")
    if app is not None:
        for tag, libelle in CHAMPS_APP:
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
                "propriete de document", libelle, conf, valeur))
        tt = app.find(_q(EP, "TotalTime"))
        if tt is not None and (tt.text or "").strip().isdigit():
            minutes = int(tt.text.strip())
            if minutes > 0:
                constats.append(_constat(
                    "historique d'edition",
                    "temps d'edition cumule declare : %d minutes" % minutes,
                    PROBABLE if minutes >= 60 else INFORMATIF,
                    str(minutes), "historique"))
    return constats


def _residus_docx(parties):
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
                "%d insertion(s) et %d suppression(s) non acceptees restent "
                "dans le document" % (ins, dele), CONFIRME,
                "%d/%d" % (ins, dele), "residu"))
        masque = len(list(doc.iter(_q(W, "vanish"))))
        if masque:
            constats.append(_constat(
                "texte masque",
                "%d passage(s) en texte masque, invisibles a l'ecran mais "
                "presents dans le fichier" % masque, PROBABLE, str(masque),
                "residu"))
    commentaires = _racine(parties, "word/comments.xml")
    if commentaires is not None:
        n = len(list(commentaires.iter(_q(W, "comment"))))
        auteurs = sorted({c.get(_q(W, "author")) or ""
                          for c in commentaires.iter(_q(W, "comment"))}
                         - {""})
        if n:
            constats.append(_constat(
                "commentaires",
                "%d commentaire(s) restent dans le document%s"
                % (n, (", de " + ", ".join(auteurs)) if auteurs else ""),
                CONFIRME, ", ".join(auteurs) or str(n), "residu"))
    if any(n.startswith("customXml/") for n in parties):
        constats.append(_constat(
            "donnees applicatives",
            "le fichier porte un dossier customXml, souvent laisse par un "
            "outil de gestion documentaire", INFORMATIF, None, "residu"))
    if "word/people.xml" in parties:
        gens = _racine(parties, "word/people.xml")
        noms = sorted({e.get(_q(W, "author")) or ""
                       for e in (gens.iter() if gens is not None else [])}
                      - {""})
        if noms:
            constats.append(_constat(
                "collaborateurs",
                "le fichier liste les personnes ayant contribue : %s"
                % ", ".join(noms), CONFIRME, ", ".join(noms), "residu"))
    return constats


def _residus_pptx(parties):
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
            "%d diapositive(s) portent des notes, visibles par qui ouvre le "
            "fichier" % avec_texte, CONFIRME, str(avec_texte), "residu"))
    coms = [n for n in parties if "comment" in n.lower()
            and n.startswith("ppt/") and n.endswith(".xml")]
    if coms:
        constats.append(_constat(
            "commentaires",
            "%d partie(s) de commentaires dans la presentation" % len(coms),
            PROBABLE, str(len(coms)), "residu"))
    return constats


# Un chemin local dans une relation trahit l'arborescence de la machine.
CHEMIN_LOCAL = re.compile(
    rb'Target="(file:///[^"]+|[A-Za-z]:[\\/][^"]+|\.\./[^"]*/Users/[^"]+)"')


def _chemins_locaux(parties):
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
                "chemin local",
                "un lien pointe vers un chemin de votre machine",
                CONFIRME, chemin, "chemin"))
    return constats[:10]


def _fuites_odf(parties, auteur):
    """Metadonnees ODF : meta.xml porte l'identite et les compteurs."""
    constats = []
    r = _racine(parties, "meta.xml")
    if r is None:
        return constats
    champs = [
        (META, "initial-creator", "auteur d'origine", True),
        (DC, "creator", "derniere personne a avoir enregistre", True),
        (META, "generator", "logiciel de production", False),
        (DC, "title", "titre enregistre dans le fichier", False),
        (DC, "subject", "sujet enregistre", False),
    ]
    for ns, tag, libelle, identite in champs:
        for el in r.iter(_q(ns, tag)):
            valeur = (el.text or "").strip()
            if not valeur:
                continue
            conf = (_identifiante(valeur, auteur) if identite
                    else INFORMATIF)
            if conf is None:
                continue
            constats.append(_constat(
                "propriete de document", libelle, conf, valeur))
            break
    for el in r.iter(_q(META, "editing-cycles")):
        v = (el.text or "").strip()
        if v.isdigit() and int(v) > 1:
            constats.append(_constat(
                "historique d'edition",
                "le fichier declare %s enregistrements successifs" % v,
                PROBABLE if int(v) >= 10 else INFORMATIF, v, "historique"))
        break
    for el in r.iter(_q(META, "editing-duration")):
        v = (el.text or "").strip()
        if v and v not in ("PT0S", "P0D"):
            constats.append(_constat(
                "historique d'edition",
                "duree d'edition cumulee declaree : %s" % v,
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
                "le document porte un registre de modifications suivies",
                CONFIRME, None, "residu"))
    return constats


CHAMPS_PDF = [
    (rb"/Author\s*\(([^)]{1,200})\)", "auteur declare", True),
    (rb"/Creator\s*\(([^)]{1,200})\)", "logiciel de creation", False),
    (rb"/Producer\s*\(([^)]{1,200})\)", "logiciel de production", False),
    (rb"/Title\s*\(([^)]{1,200})\)", "titre enregistre dans le fichier", False),
    (rb"/Keywords\s*\(([^)]{1,200})\)", "mots-cles enregistres", False),
    (rb"/Subject\s*\(([^)]{1,200})\)", "sujet enregistre", False),
]


def _fuites_pdf(chemin, auteur):
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

    for motif, libelle, identite in CHAMPS_PDF:
        m = re.search(motif, brut)
        if not m:
            continue
        valeur = m.group(1).decode("latin-1", "replace").strip()
        if not valeur:
            continue
        conf = _identifiante(valeur, auteur) if identite else INFORMATIF
        if conf is None:
            continue
        constats.append(_constat("propriete de document", libelle, conf,
                                 valeur))

    eof = len(re.findall(rb"%%EOF", brut))
    prev = len(re.findall(rb"/Prev\s+\d+", brut))
    if eof > 1 or prev:
        constats.append(_constat(
            "mise a jour incrementale",
            "le fichier porte %d marqueurs de fin et %d renvoi(s) vers une "
            "table anterieure : les versions precedentes du document restent "
            "dans le fichier et sont recuperables, y compris des metadonnees "
            "que l'on croirait supprimees" % (eof, prev),
            CONFIRME if (eof > 1 and prev) else PROBABLE,
            "%d %%EOF, %d /Prev" % (eof, prev), "integrite"))

    if re.search(rb"<x:xmpmeta", brut):
        auteurs_xmp = re.findall(rb"<dc:creator>.{0,300}?</dc:creator>", brut,
                                 re.S)
        constats.append(_constat(
            "metadonnees XMP",
            "le fichier porte un bloc XMP%s"
            % (", avec un champ d'auteur" if auteurs_xmp else ""),
            PROBABLE if auteurs_xmp else INFORMATIF, None))

    if b"/Encrypt" in brut:
        constats.append(_constat(
            "chiffrement",
            "le PDF est chiffre : son contenu n'a pas ete inspecte en detail",
            INFORMATIF, None, "integrite"))

    if re.search(rb"/Type\s*/EmbeddedFile", brut):
        constats.append(_constat(
            "fichier embarque",
            "le PDF embarque au moins un fichier joint, qui part avec lui",
            CONFIRME, None, "residu"))

    if re.search(rb"/Annots", brut) and re.search(rb"/Subtype\s*/Text", brut):
        constats.append(_constat(
            "commentaires",
            "le PDF porte des annotations de type note",
            PROBABLE, None, "residu"))
    return constats


def analyser(chemin, auteur=None):
    """Inventaire de ce que le fichier trahit. N'ecrit jamais, ne nettoie pas."""
    fmt, famille = detecter_format(chemin)
    constats = []
    if famille == "page-fixe":
        constats += _fuites_pdf(chemin, auteur)
    else:
        parties = _parties(chemin)
        if famille == "odf":
            constats += _fuites_odf(parties, auteur)
        else:
            constats += _fuites_ooxml(parties, auteur)
            constats += (_residus_docx(parties) if famille == "texte-ooxml"
                         else _residus_pptx(parties))
        constats += _chemins_locaux(parties)

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
        "non_verifie": _non_verifie(famille),
    }


def _non_verifie(famille):
    """Ce que ce controle ne regarde pas, dit plutot que taise.

    Un rapport qui ne nomme pas ses angles morts se lit comme un quitus.
    """
    commun = [
        "le contenu redactionnel n'est pas juge ici, seules les traces le sont",
        "les metadonnees des images incorporees ne sont pas ouvertes une par "
        "une (voir images.py extract puis manifest)",
    ]
    if famille == "page-fixe":
        return commun + [
            "un PDF chiffre n'est pas inspecte au dela de son enveloppe",
            "les objets ranges dans un flux compresse echappent a la lecture "
            "binaire : l'absence de constat n'est pas une preuve d'absence",
        ]
    return commun + [
        "les macros et le code embarque ne sont pas analyses",
        "un champ efface par l'application mais conserve dans une partie non "
        "standard peut echapper a ce controle",
    ]


LIBELLE_CONFIANCE = {
    CONFIRME: "CONFIRME ",
    PROBABLE: "probable ",
    INFORMATIF: "informatif",
    DOUTEUX: "douteux   ",
}


def rapport_texte(r):
    lignes = ["%s : %s" % (r["fichier"], r["verdict"]), ""]
    if not r["constats"]:
        lignes.append("  aucune trace lisible dans les parties inspectees")
    par_categorie = {}
    for c in r["constats"]:
        par_categorie.setdefault(c["categorie"], []).append(c)
    titres = {"identite": "Identite et organisation",
              "historique": "Historique d'edition",
              "residu": "Residus de travail",
              "chemin": "Chemins locaux",
              "integrite": "Integrite du fichier"}
    for cat in ("identite", "residu", "integrite", "historique", "chemin"):
        groupe = par_categorie.get(cat)
        if not groupe:
            continue
        lignes.append("  %s" % titres[cat])
        for c in groupe:
            valeur = (" -> %s" % c["valeur"]) if c["valeur"] else ""
            lignes.append("    [%s] %s : %s%s"
                          % (LIBELLE_CONFIANCE[c["confiance"]], c["regle"],
                             c["detail"], valeur))
        lignes.append("")
    lignes.append("  %d confirme(s), %d probable(s), %d informatif(s), "
                  "%d douteux" % (r["comptes"][CONFIRME], r["comptes"][PROBABLE],
                                  r["comptes"][INFORMATIF],
                                  r["comptes"][DOUTEUX]))
    lignes.append("")
    lignes.append("Ce controle inspecte, il ne nettoie pas : retirer une trace")
    lignes.append("est une decision de l'auteur, la reperer est une mesure.")
    lignes.append("")
    lignes.append("Non verifie ici :")
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
    a = p.parse_args(argv)

    r = analyser(a.fichier, a.auteur)
    if a.format == "json":
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(rapport_texte(r))
    return 1 if (a.strict and r["comptes"][CONFIRME]) else 0


if __name__ == "__main__":
    sys.exit(main())
