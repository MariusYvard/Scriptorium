#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recuperation et identification d'une figure tierce.

Chainon amont de check-droits.py : celui-ci dit ce que la licence permet,
celui-la dit de quelle figure on parle et d'ou le fichier vient. images.py
sort des images anonymes, que rien ne relie a "Figure 3" ni a sa legende ;
ce script pose ce lien, avec une confiance mesuree, et refuse de l'affirmer
quand la page est ambigue.

Trois questions, trois sous-commandes, plus une qui les enchaine.

  inventorier : apparier image, legende et page dans un PDF deja possede.
  localiser   : etat d'acces ouvert et adresse du PDF ouvert, par DOI.
  recuperer   : telecharger, et seulement depuis une localisation ouverte.
  chainer     : localiser, recuperer, inventorier, droits, entree de registre.

GARDE-FOU. Le script ne recupere un fichier que depuis une localisation
declaree en acces ouvert par l'index. Il ne contourne aucun controle
d'acces, ne presente aucun identifiant, ne tente aucune adresse devinee, et
refuse par un message nomme quand la source n'est pas ouverte. La garantie
est structurelle : recuperer() prend la fiche produite par localiser(), pas
une adresse libre, et lit l'adresse dedans. Un article sous abonnement se
demande a son editeur, il ne se contourne pas ; la procedure est dans
references/droits-figures.md.

L'appariement est une heuristique declaree comme telle. Une page qui porte
une image et une legende donne un appariement de confiance elevee ; trois
images et trois legendes donnent un appariement d'ordre, de confiance
moyenne ; des comptes qui divergent donnent une confiance faible. Sans
backend de texte, l'inventaire rend les images sans legende et le dit : il
n'invente pas de legende.

Reseau optionnel derriere --reseau. Consultatif par defaut, --strict rend un
code de sortie non nul.

Usage :
    python3 emprunts.py inventorier SOURCE.pdf [--out DIR] [--format text|json] [--strict]
    python3 emprunts.py localiser --doi 10.xxxx/yyyy [--reseau] [--format text|json] [--strict]
    python3 emprunts.py recuperer --doi 10.xxxx/yyyy --out FICHIER.pdf [--reseau] [--strict]
    python3 emprunts.py chainer --doi 10.xxxx/yyyy [--out DIR] [--source FICHIER.pdf]
                        [--figure N] [--modifications TEXTE] [--registre R.json]
                        [--reseau] [--format text|json] [--strict]

Langue d'affichage : chaque fonction qui compose une chaine lisible prend un
parametre langue_affichage optionnel. Sans lui, les chaines sont les chaines
francaises d'origine a l'octet pres, et ce sont elles que serialise
--format json. Etats, verdicts et niveaux de confiance restent des valeurs
machine francaises dans les deux langues : check-droits.py branche sur les
verdicts, et les evals les comparent litteralement.

Module importable : localiser, recuperer, reperer_legendes, apparier,
inventorier, entree_registre, voies_de_repli, chainer, rapport_texte.
"""
import argparse
import importlib.util
import json
import os
import re
import sys

TIMEOUT = 15
USER_AGENT = "Scriptorium/0.11 (recuperation de figure en acces ouvert)"

# Longueur maximale d'une legende retenue, en caracteres. Au-dela, le texte
# capte n'est plus une legende mais le corps de l'article.
LONGUEUR_LEGENDE = 300

# Nombre de lignes de continuation lues apres la ligne de legende.
LIGNES_CONTINUATION = 3

ETATS_LOCALISATION = ("acces ouvert confirme", "acces ouvert sans fichier",
                      "acces non ouvert", "localisation inconnue")

ETATS_RECUPERATION = ("recuperee", "refus source non ouverte",
                      "refus adresse absente", "refus localisation inconnue",
                      "echec reseau", "echec contenu non pdf")

NIVEAUX_CONFIANCE = ("elevee", "moyenne", "faible", "nulle")

VERDICTS_INVENTAIRE = ("inventaire apparie", "inventaire partiel",
                       "inventaire sans legende", "inventaire non apparie",
                       "extraction impossible")

VERDICTS_CHAINE = ("emprunt prepare", "autorisation a demander",
                   "licence a etablir", "source non ouverte",
                   "chaine incomplete")

# Espace de valeurs machine de chaque etape de la chaine. Sert a traduire le
# statut affiche sans redire ailleurs les tables deja posees ; un statut hors
# de l'espace de son etape retombe sur emprunts.statut_etape.
ETAPE_ESPACE = {
    "localiser": "emprunts.etat_localisation",
    "recuperer": "emprunts.etat_recuperation",
    "inventorier": "emprunts.verdict_inventaire",
    "droits": "droits.verdict",
}


def _charger(nom_fichier, nom_module):
    """Charge un script frere par chemin explicite, jamais via sys.path :
    inserer scripts/ dans sys.path a deja fait resoudre "import numbers" vers
    le numbers.py maison dans ce depot. Renvoie None si le fichier est
    absent, degradation propre plutot que plantage."""
    try:
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              nom_fichier)
        if not os.path.isfile(chemin):
            return None
        spec = importlib.util.spec_from_file_location(nom_module, chemin)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


_IMG = _charger("images.py", "images_mod")
_CHKP = _charger("check-presentation.py", "check_presentation_mod")
_DRT = _charger("check-droits.py", "check_droits_mod")

# check-droits.py charge deja verify-sources.py. Reprendre SON objet module
# plutot qu'en charger un second : les evals remplacent _requete_json en un
# seul endroit, et les deux scripts voient la meme simulation.
_VSRC = getattr(_DRT, "_VSRC", None) or _charger("verify-sources.py",
                                                 "verify_sources_mod")

_LIB = _charger("libelles.py", "scriptorium_libelles")


def _lib():
    """Couche de libelles, chargee comme les autres scripts freres."""
    return _LIB


# Limite, garde-fou et refus sont DERIVES de la couche de libelles plutot que
# redits ici : une seule table porte les deux langues, et les constantes
# gardent leur nom, qui est lu ailleurs.
LIMITE = _LIB.t("emprunts.limite", "fr")

GARDE_FOU = _LIB.t("emprunts.garde_fou", "fr")

REFUS_NON_OUVERT = _LIB.t("emprunts.refus_non_ouvert", "fr",
                          garde_fou=GARDE_FOU)

REFUS_ADRESSE_ABSENTE = _LIB.t("emprunts.refus_adresse_absente", "fr",
                               garde_fou=GARDE_FOU)

REFUS_LOCALISATION_INCONNUE = _LIB.t("emprunts.refus_localisation_inconnue",
                                     "fr", garde_fou=GARDE_FOU)


def _garde_fou(lib, la):
    return lib.t("emprunts.garde_fou", la)


def _refus(cle, lib, la):
    """Message de refus, dans la langue demandee, garde-fou inclus."""
    return lib.t(cle, la, garde_fou=_garde_fou(lib, la))


def _statut_lisible(nom_etape, statut, lib, la):
    """Libelle d'un statut d'etape. L'espace de valeurs suit l'etape ; un
    statut propre a l'enchainement retombe sur emprunts.statut_etape."""
    espace = ETAPE_ESPACE.get(nom_etape)
    if espace and statut in (lib.VALEURS.get(espace) or {}):
        return lib.valeur(espace, statut, la)
    return lib.valeur("emprunts.statut_etape", statut, la)


# Prefixe de nom pose par les backends PyMuPDF et pypdf dans images.py :
# "p003-01.png" designe la troisieme page. pdfimages numerote les images sans
# dire la page ; dans ce cas la page reste inconnue et l'inventaire le dit.
PAGE_RE = re.compile(r"(?:^|[\\/])p(\d+)-")

# Reperage d'une legende en tete de ligne. Formes couvertes : "Figure 3.",
# "Fig. 3 tiret cadratin", "Figure 3:", "Tableau 2.", plus les formes
# anglaises Figure, Fig. et Table. Le separateur peut etre une ponctuation,
# une espace ou la fin de ligne, parce que les revues n'en fixent pas une
# seule ; le prix de cette tolerance est declare dans les limites.
LEGENDE_RE = re.compile(
    r"^[ \t>|]{0,4}(?P<mot>Figures?|Fig\.|Fig|Tableaux|Tableau|Tables?|Tab\.)"
    r"[ \t\u00a0]*(?P<num>\d{1,3}(?:[.\-]\d{1,3})?[a-dA-D]?)"
    r"(?P<sep>[.:\)\u2013\u2014-]|[ \t]|$)[ \t]*(?P<texte>.*)$")


# Signes qui separent le numero de figure de sa legende, retires en tete du
# texte capte : "Tableau 2 : Parametres" ne donne pas une legende qui
# commence par deux-points.
SIGNES_TETE = " \t.:)–—-"


def _famille(mot):
    """Famille d'un mot de legende : figure ou tableau."""
    base = mot.lower().rstrip(".")
    return "tableau" if base.startswith("tab") else "figure"


def reperer_legendes(texte):
    """Legendes reperees dans le texte d'une page.

    Retourne une liste de dicts : famille (figure ou tableau), numero,
    libelle, legende, ligne. Une ligne qui porte le numero sans texte donne
    une entree dont la legende vaut None : le numero est constate, la
    legende reste absente, elle n'est pas comblee.

    Deux occurrences du meme numero sur une page (un renvoi dans le corps
    puis la legende sous la figure) sont fusionnees, le texte le plus long
    l'emportant : c'est celui qui a des chances d'etre la vraie legende.
    """
    if not texte:
        return []
    lignes = texte.splitlines()
    trouvees = {}
    ordre = []
    for i, ligne in enumerate(lignes):
        m = LEGENDE_RE.match(ligne)
        if not m:
            continue
        famille = _famille(m.group("mot"))
        numero = m.group("num")
        # Le separateur peut etre suivi d'un second signe ("Tableau 2 : ..."),
        # que le groupe sep n'a pas absorbe. Il se retire ici plutot que de
        # rester colle en tete de legende.
        corps = (m.group("texte") or "").strip().lstrip(SIGNES_TETE).strip()
        j = i + 1
        while (j < len(lignes) and j - i <= LIGNES_CONTINUATION
               and len(corps) < LONGUEUR_LEGENDE):
            suite = lignes[j].strip()
            if not suite or LEGENDE_RE.match(lignes[j]):
                break
            corps = (corps + " " + suite).strip()
            j += 1
        corps = corps[:LONGUEUR_LEGENDE].strip() or None
        cle = (famille, numero)
        fiche = {"famille": famille, "numero": numero,
                 "libelle": "%s %s" % ("Tableau" if famille == "tableau"
                                       else "Figure", numero),
                 "legende": corps, "ligne": i + 1}
        if cle not in trouvees:
            trouvees[cle] = fiche
            ordre.append(cle)
        elif len(corps or "") > len(trouvees[cle]["legende"] or ""):
            trouvees[cle] = fiche
    return [trouvees[c] for c in ordre]


def page_de(origine):
    """Numero de page lu dans le nom pose par le backend d'extraction.

    PyMuPDF et pypdf nomment "p003-01.ext" : la page est dans le nom.
    pdfimages numerote les images sans dire la page, et la fonction rend
    alors None : la page est inconnue, elle n'est pas devinee.
    """
    m = PAGE_RE.search((origine or "").replace("\\", "/"))
    return int(m.group(1)) if m else None


def _confiance(n_images, n_legendes):
    """Niveau et valeur de confiance d'un appariement de page.

    Une page a une image et une legende ne laisse pas de place au doute : la
    legende est celle de l'image. Trois images et trois legendes se
    correspondent probablement dans l'ordre de lecture, sans garantie qu'un
    encart ou une figure pleine page ne rompe l'ordre. Des comptes qui
    divergent signent une page ou l'extraction et la mise en page ne
    racontent pas la meme chose : l'appariement d'ordre y reste possible,
    mais il ne se donne pas pour acquis.
    """
    if n_images == 1 and n_legendes == 1:
        return "elevee", 0.9
    if n_images == n_legendes:
        return "moyenne", 0.5
    return "faible", 0.25


def apparier(images, legendes_par_page, texte_disponible=True,
             backend_texte=None, langue_affichage=None):
    """Apparie des images extraites aux legendes de leur page.

    images : liste de fiches du manifeste d'images.py (cle "origine" pour la
    page, "fichier" pour le chemin relatif). legendes_par_page : dict page
    vers liste de legendes. Retourne (appariements, legendes_orphelines).

    Aucun appariement n'est affirme sans son niveau : la fiche porte
    toujours "niveau" et "confiance", et "legende" reste None quand rien ne
    permet de la nommer.
    """
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    appariements = []
    utilisees = set()
    par_page = {}
    for img in images:
        par_page.setdefault(page_de(img.get("origine")), []).append(img)
    for page in sorted(par_page, key=lambda p: (p is None, p)):
        lot = par_page[page]
        legendes = list(legendes_par_page.get(page) or []) if page else []
        if not texte_disponible:
            motif = lib.t("emprunts.a.sans_backend", la)
            legendes = []
        elif page is None:
            motif = lib.t("emprunts.a.page_inconnue", la,
                          backend=(backend_texte
                                   or lib.t("emprunts.a.backend_defaut", la)))
            legendes = []
        elif not legendes:
            motif = lib.t("emprunts.a.aucune_legende", la, page=page)
        else:
            motif = None
        appariements.extend(_apparier_page(page, lot, legendes, motif,
                                           utilisees, lib, la))
    orphelines = [dict(l, page=p) for p, lot in sorted(
        legendes_par_page.items(), key=lambda kv: kv[0])
        for l in lot if (p, l["famille"], l["numero"]) not in utilisees]
    return appariements, orphelines


def _apparier_page(page, images, legendes, motif, utilisees, lib, la):
    """Apparie les images et les legendes d'une seule page, dans l'ordre."""
    fiches = []
    niveau, valeur = _confiance(len(images), len(legendes))
    for rang, img in enumerate(images):
        legende = legendes[rang] if rang < len(legendes) else None
        if legende is None:
            fiche_niveau, fiche_valeur = "nulle", 0.0
            detail = motif or lib.t("emprunts.a.plus_d_images", la, page=page)
        else:
            fiche_niveau, fiche_valeur = niveau, valeur
            detail = _detail_appariement(fiche_niveau, page, len(images),
                                         len(legendes), lib, la)
            utilisees.add((page, legende["famille"], legende["numero"]))
        fiches.append({
            "fichier": img.get("fichier"), "index": img.get("index"),
            "page": page, "origine": img.get("origine"),
            "largeur": img.get("largeur"), "hauteur": img.get("hauteur"),
            "famille": (legende or {}).get("famille"),
            "numero": (legende or {}).get("numero"),
            "libelle": (legende or {}).get("libelle"),
            "legende": (legende or {}).get("legende"),
            "niveau": fiche_niveau, "confiance": fiche_valeur,
            "motif": detail,
            "images_sur_la_page": len(images),
            "legendes_sur_la_page": len(legendes)})
    return fiches


def _detail_appariement(niveau, page, n_images, n_legendes, lib, la):
    """Phrase qui dit ce que l'appariement vaut, sans le surjouer."""
    if niveau == "elevee":
        return lib.t("emprunts.a.direct", la, page=page)
    if niveau == "moyenne":
        return lib.t("emprunts.a.par_ordre", la, images=n_images,
                     legendes=n_legendes, page=page)
    return lib.t("emprunts.a.comptes_divergents", la, images=n_images,
                 legendes=n_legendes, page=page)


def _verdict_inventaire(manifeste, texte_disponible, appariements):
    """Verdict ferme de l'inventaire, sur cinq valeurs."""
    if manifeste is None or (not manifeste.get("images")
                             and not manifeste.get("backend")):
        return "extraction impossible"
    if not texte_disponible:
        return "inventaire non apparie"
    apparies = [a for a in appariements if a["niveau"] != "nulle"]
    if not apparies:
        return "inventaire sans legende"
    if all(a["niveau"] == "elevee" for a in appariements):
        return "inventaire apparie"
    return "inventaire partiel"


def inventorier(source, dossier=None, min_octets=1024, textes=None,
                langue_affichage=None):
    """Apparie image, legende et page dans un PDF ou un document Office.

    Les images sortent par images.py, le texte par la cascade de backends de
    check-presentation.py, deja partagee avec check-lecture-pdf.py. Passer
    textes (liste de chaines, une par page) court-circuite la cascade, ce qui
    sert aux evaluations hors ligne.

    Sans langue_affichage, motifs et notes sont les chaines francaises
    d'origine a l'octet pres : ce sont elles que serialise --format json.
    """
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    rapport = {"source": os.path.basename(source or ""), "dossier": dossier,
               "backend_images": None, "backend_texte": None,
               "pages_lues": None, "images": 0, "doublons": 0,
               "appariements": [], "legendes_sans_image": [],
               "verdict": "extraction impossible", "notes": [],
               "limite": lib.t("emprunts.limite", la)}
    if not source or not os.path.isfile(source):
        rapport["notes"].append(lib.t("emprunts.n.fichier_introuvable", la,
                                      source=source))
        return rapport
    if _IMG is None:
        rapport["notes"].append(lib.t("emprunts.n.images_absent", la))
        return rapport
    dossier = dossier or os.path.join(os.path.dirname(os.path.abspath(source)),
                                      "images-%s" % os.path.splitext(
                                          os.path.basename(source))[0])
    rapport["dossier"] = dossier
    manifeste = _IMG.extract(source, dossier, min_octets)
    rapport["backend_images"] = manifeste.get("backend")
    rapport["images"] = manifeste.get("count") or 0
    rapport["doublons"] = manifeste.get("doublons") or 0
    rapport["notes"].extend(manifeste.get("notes") or [])
    return _inventaire_texte(source, rapport, manifeste, textes, lib, la)


def _inventaire_texte(source, rapport, manifeste, textes, lib, la):
    """Seconde moitie de inventorier() : lecture du texte, reperage des
    legendes, appariement. Separee pour rester lisible."""
    backend_texte = None
    if textes is None and _CHKP is not None:
        textes, backend_texte = _CHKP.extraire_texte_pages(source)
    rapport["backend_texte"] = backend_texte
    texte_disponible = textes is not None
    if not texte_disponible:
        rapport["notes"].append(lib.t("emprunts.n.sans_backend_texte", la))
    else:
        rapport["pages_lues"] = len(textes)
    legendes_par_page = {}
    if texte_disponible:
        for numero, texte in enumerate(textes, 1):
            legendes = reperer_legendes(texte)
            if legendes:
                legendes_par_page[numero] = legendes
    uniques = [i for i in (manifeste.get("images") or [])
               if "doublon_de" not in i]
    appariements, orphelines = apparier(uniques, legendes_par_page,
                                        texte_disponible,
                                        manifeste.get("backend"), la)
    rapport["appariements"] = appariements
    rapport["legendes_sans_image"] = orphelines
    rapport["verdict"] = _verdict_inventaire(manifeste, texte_disponible,
                                             appariements)
    if orphelines:
        rapport["notes"].append(lib.t("emprunts.n.legendes_orphelines", la,
                                      n=len(orphelines)))
    doutes = [a for a in appariements if a["niveau"] in ("moyenne", "faible")]
    if doutes:
        rapport["notes"].append(lib.t("emprunts.n.appariements_douteux", la,
                                      n=len(doutes)))
    return rapport


def _auteur_openalex(data):
    """Auteur principal declare par OpenAlex, forme courte pour un credit."""
    noms = []
    for a in (data.get("authorships") or [])[:2]:
        nom = ((a or {}).get("author") or {}).get("display_name")
        if nom:
            noms.append(nom)
    if not noms:
        return None
    if len(data.get("authorships") or []) > 2:
        return "%s et al." % noms[0]
    return " et ".join(noms)


def localiser(doi, reseau=False, timeout=TIMEOUT, api_key=None,
              langue_affichage=None):
    """Etat d'acces ouvert et adresse du PDF ouvert d'une source, par DOI.

    Une seule source d'autorite ici : OpenAlex, qui porte open_access
    (is_oa, oa_status) et best_oa_location (pdf_url, landing_page_url,
    license, version). Etat ferme sur quatre valeurs. Sans --reseau, ou
    quand l'index ne repond pas, l'etat reste "localisation inconnue" :
    une mesure omise, jamais une valeur supposee.
    """
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    fiche = {"doi": doi, "reseau": bool(reseau),
             "etat": "localisation inconnue", "est_ouvert": None,
             "statut_oa": None, "licence_declaree": None, "url_pdf": None,
             "url_page": None, "version": None, "revue": None, "titre": None,
             "auteur": None, "index_consulte": False, "detail": "",
             "garde_fou": _garde_fou(lib, la),
             "limite": lib.t("emprunts.limite", la)}
    if not reseau:
        fiche["detail"] = lib.t("emprunts.l.reseau_desactive", la)
        return fiche
    if _VSRC is None:
        fiche["detail"] = lib.t("emprunts.l.vsrc_absent", la)
        return fiche
    url = ("https://api.openalex.org/works/https://doi.org/%s?select=id,doi,"
           "title,open_access,best_oa_location,primary_location,authorships"
           % doi)
    if api_key:
        url += "&api_key=%s" % api_key
    code, data = _VSRC._requete_json(url, timeout)
    if code is None:
        fiche["detail"] = lib.t("emprunts.l.injoignable", la)
        return fiche
    fiche["index_consulte"] = True
    if code == 404 or not data:
        fiche["detail"] = lib.t("emprunts.l.doi_non_trouve", la)
        return fiche
    return _lire_localisation(fiche, data, lib, la)


def _lire_localisation(fiche, data, lib, la):
    """Lit la reponse d'OpenAlex et ferme l'etat sur ETATS_LOCALISATION."""
    acces = data.get("open_access") or {}
    meilleure = data.get("best_oa_location") or {}
    primaire = data.get("primary_location") or {}
    fiche["titre"] = data.get("title")
    fiche["auteur"] = _auteur_openalex(data)
    fiche["est_ouvert"] = acces.get("is_oa")
    fiche["statut_oa"] = acces.get("oa_status")
    fiche["licence_declaree"] = (meilleure.get("license")
                                 or meilleure.get("license_id")
                                 or primaire.get("license"))
    fiche["version"] = meilleure.get("version")
    fiche["url_pdf"] = meilleure.get("pdf_url")
    fiche["url_page"] = meilleure.get("landing_page_url")
    revue = meilleure.get("source") or primaire.get("source") or {}
    fiche["revue"] = revue.get("display_name") if isinstance(revue, dict) else None
    statut = fiche["statut_oa"] or lib.t("emprunts.l.statut_non_precise", la)
    if fiche["est_ouvert"] and fiche["url_pdf"]:
        fiche["etat"] = "acces ouvert confirme"
        fiche["detail"] = lib.t("emprunts.l.ouvert_avec_pdf", la,
                                statut=statut)
    elif fiche["est_ouvert"]:
        fiche["etat"] = "acces ouvert sans fichier"
        fiche["detail"] = lib.t("emprunts.l.ouvert_sans_pdf", la,
                                statut=statut)
    elif fiche["est_ouvert"] is False:
        fiche["etat"] = "acces non ouvert"
        fiche["detail"] = lib.t("emprunts.l.non_ouvert", la, statut=statut)
    else:
        fiche["detail"] = lib.t("emprunts.l.indetermine", la)
    return fiche


def _telecharger(url, timeout):
    """GET simple, sans identifiant ni cookie. Retourne (octets, erreur).

    Aucun en-tete d'authentification n'est construit ici, et aucun n'est lu
    dans l'environnement : le script n'a pas de moyen de se presenter comme
    un abonne, par construction.
    """
    import urllib.request
    try:
        requete = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT, "Accept": "application/pdf"})
        with urllib.request.urlopen(requete, timeout=timeout) as reponse:
            return reponse.read(), None
    except Exception as e:
        return None, "%s" % type(e).__name__


def recuperer(localisation, cible, timeout=TIMEOUT, langue_affichage=None):
    """Recupere le fichier d'une source, et seulement si elle est ouverte.

    La fonction prend la fiche produite par localiser(), pas une adresse
    libre : l'adresse tentee est celle que l'index a publiee, et il n'existe
    pas de chemin de code qui en essaie une autre. Un etat autre que
    "acces ouvert confirme" produit un refus nomme, chemin de premiere
    classe, avec la conduite a tenir.
    """
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    rapport = {"etat": None, "url": None, "fichier": None, "octets": 0,
               "message": "", "garde_fou": _garde_fou(lib, la)}
    etat = (localisation or {}).get("etat")
    if etat == "acces non ouvert":
        rapport["etat"] = "refus source non ouverte"
        rapport["message"] = _refus("emprunts.refus_non_ouvert", lib, la)
        return rapport
    if etat == "acces ouvert sans fichier":
        rapport["etat"] = "refus adresse absente"
        rapport["message"] = _refus("emprunts.refus_adresse_absente", lib, la)
        return rapport
    if etat != "acces ouvert confirme":
        rapport["etat"] = "refus localisation inconnue"
        rapport["message"] = _refus("emprunts.refus_localisation_inconnue",
                                    lib, la)
        return rapport
    return _recuperer_ouvert(localisation, cible, timeout, rapport, lib, la)


def _recuperer_ouvert(localisation, cible, timeout, rapport, lib, la):
    """Telechargement effectif, atteint seulement depuis une localisation
    declaree ouverte. Un contenu qui n'est pas un PDF n'est pas ecrit : une
    page d'interstitiel enregistree sous un nom en .pdf ferait passer un mur
    d'acces pour un article."""
    url = localisation.get("url_pdf")
    rapport["url"] = url
    donnees, erreur = _telecharger(url, timeout)
    if donnees is None:
        rapport["etat"] = "echec reseau"
        rapport["message"] = lib.t("emprunts.r.injoignable", la,
                                   erreur=erreur)
        return rapport
    if not donnees[:1024].lstrip().startswith(b"%PDF-"):
        rapport["etat"] = "echec contenu non pdf"
        rapport["message"] = lib.t("emprunts.r.pas_un_pdf", la)
        return rapport
    dossier = os.path.dirname(os.path.abspath(cible))
    if dossier:
        os.makedirs(dossier, exist_ok=True)
    with open(cible, "wb") as f:
        f.write(donnees)
    rapport.update({"etat": "recuperee", "fichier": cible,
                    "octets": len(donnees),
                    "message": lib.t("emprunts.r.recuperee", la)})
    return rapport


def entree_registre(doi, localisation=None, droits=None, appariement=None,
                    fichier=None, modifications=None, identifiant=None,
                    langue_affichage=None):
    """Entree du registre des figures empruntees, au format que
    check-droits.py valide.

    Les cles sont celles de ce registre (id, libelle, titre, auteur, source,
    doi, url, licence, verdict, modifications, autorisation), plus le chemin
    du fichier recupere et la tracabilite de l'appariement. La licence
    inscrite est celle que check-droits.py a retenue, pour que le verdict
    declare ne contredise jamais la licence declaree. Un element absent
    reste absent : check-droits.py le signalera comme manquant plutot que
    de le voir comble ici.
    """
    localisation = localisation or {}
    droits = droits or {}
    appariement = appariement or {}
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    numero = appariement.get("numero")
    libelle = appariement.get("libelle") or (
        lib.t("emprunts.e.libelle_defaut", la, numero=numero)
        if numero else None)
    retenue = droits.get("licence_retenue") or {}
    verdict = droits.get("verdict")
    entree = {
        "id": identifiant or ("fig-%s" % numero if numero else "fig-1"),
        "libelle": libelle,
        "titre": appariement.get("legende"),
        "legende_origine": appariement.get("legende"),
        "auteur": localisation.get("auteur"),
        "source": localisation.get("revue") or localisation.get("titre"),
        "doi": doi,
        "url": localisation.get("url_page") or (
            "https://doi.org/%s" % doi if doi else None),
        "licence": retenue.get("brut") or localisation.get("licence_declaree"),
        "verdict": (verdict if verdict in getattr(_DRT, "VERDICTS", ())
                    else None),
        "modifications": modifications,
        "fichier": fichier,
        "page": appariement.get("page"),
        "confiance_appariement": appariement.get("niveau"),
    }
    if verdict == "autorisation requise":
        entree["autorisation"] = {"etat": "non demandee"}
    return entree


def voies_de_repli(verdict, doi=None, auteur=None, langue_affichage=None):
    """Les deux voies ouvertes quand la reproduction n'est pas acquise.

    Demander l'autorisation a l'editeur, ou refaire la figure a partir des
    donnees publiees. Nulle quand la reproduction est deja acquise : une
    figure reutilisable n'a pas besoin d'etre refaite. Meme discours que
    check-droits.py, dont l'alternative de redessin est reprise telle
    quelle plutot que redite.
    """
    if verdict not in ("autorisation requise", "licence inconnue"):
        return None
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    demande = {
        "voie": lib.t("emprunts.v.demande", la),
        "etapes": [
            lib.t("emprunts.v.etape_titulaire", la),
            lib.t("emprunts.v.etape_figure", la,
                  doi=doi or lib.t("emprunts.v.doi_defaut", la)),
            lib.t("emprunts.v.etape_usage", la),
            lib.t("emprunts.v.etape_reponse", la),
        ],
        "reference": "references/droits-figures.md",
    }
    redessin = (_DRT.alternative_redessin(verdict, auteur,
                                          langue_affichage=la)
                if _DRT else None)
    return {"autorisation": demande, "redessin": redessin}


def _etape(rapport, nom, statut, detail):
    rapport["etapes"].append({"etape": nom, "statut": statut,
                              "detail": detail})


def _verdict_chaine(recuperation, droits_verdict, inventaire_verdict):
    """Verdict ferme de la chaine, sur cinq valeurs. Le refus d'une source
    non ouverte prime : c'est le fait le plus lourd du rapport."""
    if recuperation and recuperation.get("etat") == "refus source non ouverte":
        return "source non ouverte"
    if droits_verdict == "autorisation requise":
        return "autorisation a demander"
    if droits_verdict == "licence inconnue":
        return "licence a etablir"
    if inventaire_verdict in ("inventaire apparie", "inventaire partiel"):
        return "emprunt prepare"
    return "chaine incomplete"


def chainer(doi, dossier=None, reseau=False, source=None, figure=None,
            modifications=None, registre=None, timeout=TIMEOUT,
            api_key=None, textes=None, langue_affichage=None):
    """Enchaine localisation, recuperation, inventaire, droits et registre.

    source : chemin d'un PDF deja possede, qui court-circuite la
    recuperation. figure : numero de figure a retenir, sinon toutes les
    images appariees entrent au registre. registre : chemin d'un registre a
    creer ou a completer.
    """
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    dossier = dossier or os.path.join(os.getcwd(), "emprunts")
    rapport = {"doi": doi, "reseau": bool(reseau), "dossier": dossier,
               "etapes": [], "localisation": None, "recuperation": None,
               "inventaire": None, "droits": None, "entrees": [],
               "erreurs_registre": [], "avertissements_registre": [],
               "voies": None, "registre": None,
               "verdict": "chaine incomplete",
               "garde_fou": _garde_fou(lib, la),
               "limite": lib.t("emprunts.limite", la)}
    localisation = localiser(doi, reseau, timeout, api_key,
                             langue_affichage=la)
    rapport["localisation"] = localisation
    _etape(rapport, "localiser", localisation["etat"], localisation["detail"])
    fichier = source
    if source:
        _etape(rapport, "recuperer", "source locale fournie",
               lib.t("emprunts.c.source_locale", la))
    else:
        cible = os.path.join(dossier, "%s.pdf"
                             % re.sub(r"[^A-Za-z0-9]+", "-", doi or "source"))
        recuperation = recuperer(localisation, cible, timeout,
                                 langue_affichage=la)
        rapport["recuperation"] = recuperation
        _etape(rapport, "recuperer", recuperation["etat"],
               recuperation["message"])
        fichier = recuperation.get("fichier")
    return _chainer_suite(rapport, doi, dossier, reseau, fichier, figure,
                          modifications, registre, timeout, api_key, textes,
                          lib, la)


def _chainer_suite(rapport, doi, dossier, reseau, fichier, figure,
                   modifications, registre, timeout, api_key, textes,
                   lib, la):
    """Seconde moitie de chainer() : inventaire, droits, registre, voies."""
    inventaire = None
    if fichier:
        inventaire = inventorier(fichier, os.path.join(dossier, "images"),
                                 textes=textes, langue_affichage=la)
        rapport["inventaire"] = inventaire
        _etape(rapport, "inventorier", inventaire["verdict"],
               lib.t("emprunts.c.inventaire_fait", la,
                     images=inventaire["images"],
                     appariements=len(inventaire["appariements"])))
    else:
        _etape(rapport, "inventorier", "non exécutée",
               lib.t("emprunts.c.sans_fichier", la))
    droits = (_DRT.resoudre_doi(doi, reseau, timeout, api_key,
                                langue_affichage=la) if _DRT else {})
    rapport["droits"] = droits
    _etape(rapport, "droits", droits.get("verdict") or "indisponible",
           droits.get("detail") or lib.t("emprunts.c.droits_absent", la))
    rapport["entrees"] = _construire_entrees(
        doi, rapport["localisation"], droits, inventaire, figure,
        modifications, fichier, la)
    if rapport["entrees"] and _DRT:
        enveloppe = {"figures": rapport["entrees"]}
        erreurs, avertissements = _DRT.valider_registre(enveloppe, la)
        rapport["erreurs_registre"] = erreurs
        rapport["avertissements_registre"] = avertissements
        rapport["entrees"] = _DRT._sans_prive(enveloppe)["figures"]
        _etape(rapport, "registre",
               "invalide" if erreurs else "valide",
               lib.t("emprunts.c.registre", la,
                     entrees=len(rapport["entrees"]), erreurs=len(erreurs),
                     avertissements=len(avertissements)))
        if registre:
            rapport["registre"] = ecrire_registre(registre,
                                                  rapport["entrees"])
    rapport["voies"] = voies_de_repli(
        droits.get("verdict"), doi,
        (rapport["localisation"] or {}).get("auteur"), la)
    rapport["verdict"] = _verdict_chaine(
        rapport["recuperation"], droits.get("verdict"),
        (inventaire or {}).get("verdict"))
    return rapport


def _construire_entrees(doi, localisation, droits, inventaire, figure,
                        modifications, fichier, la=None):
    """Une entree de registre par image appariee retenue.

    Sans appariement exploitable, une entree unique est produite quand meme,
    avec ses trous : le registre sert aussi de tableau de bord de ce qui
    reste a etablir, et une figure non identifiee ne disparait pas du
    compte.
    """
    appariements = [a for a in ((inventaire or {}).get("appariements") or [])
                    if a.get("numero")]
    if figure is not None:
        appariements = [a for a in appariements
                        if str(a.get("numero")) == str(figure)]
    if not appariements:
        return [entree_registre(doi, localisation, droits, None, fichier,
                                modifications, langue_affichage=la)]
    entrees = []
    for a in appariements:
        chemin = a.get("fichier")
        if chemin and (inventaire or {}).get("dossier"):
            chemin = os.path.join(inventaire["dossier"], chemin)
        entrees.append(entree_registre(doi, localisation, droits, a,
                                       chemin or fichier, modifications,
                                       langue_affichage=la))
    return entrees


def ecrire_registre(chemin, entrees):
    """Ecrit ou complete le registre des figures empruntees.

    Une entree de meme identifiant remplace la precedente, les autres sont
    conservees : un registre se complete figure par figure au fil du
    document, il ne se reecrit pas a chaque appel.
    """
    registre = {"figures": []}
    if os.path.isfile(chemin):
        try:
            with open(chemin, encoding="utf-8") as f:
                charge = json.load(f)
            if isinstance(charge, dict):
                registre = charge
                registre.setdefault("figures", [])
        except (OSError, ValueError):
            registre = {"figures": []}
    par_id = {f.get("id"): i for i, f in enumerate(registre["figures"])
              if isinstance(f, dict)}
    for entree in entrees:
        if entree.get("id") in par_id:
            registre["figures"][par_id[entree["id"]]] = entree
        else:
            par_id[entree.get("id")] = len(registre["figures"])
            registre["figures"].append(entree)
    dossier = os.path.dirname(os.path.abspath(chemin))
    if dossier:
        os.makedirs(dossier, exist_ok=True)
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        json.dump(_sans_prive(registre), f, ensure_ascii=False, indent=2)
    return chemin


def _sans_prive(objet):
    """Retire les cles de travail prefixees d'un tiret bas avant toute
    sortie, comme le fait check-droits.py : le JSON ne montre que le
    contrat public."""
    if _DRT is not None:
        return _DRT._sans_prive(objet)
    if isinstance(objet, dict):
        return {k: _sans_prive(v) for k, v in objet.items()
                if not str(k).startswith("_")}
    if isinstance(objet, list):
        return [_sans_prive(x) for x in objet]
    return objet


def rapport_inventaire_texte(rap, langue_affichage=None):
    """Rendu texte de l'inventaire. Voir inventorier() pour la structure.
    Motifs et notes ont ete composes dans la langue d'affichage par
    inventorier() : ils sont repris tels quels."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    aucun = lib.t("emprunts.inv.aucun_backend", la)
    out = [lib.t("emprunts.inv.titre", la, source=rap.get("source") or "?")]
    out.append("  " + lib.t("emprunts.inv.verdict", la, verdict=lib.valeur(
        "emprunts.verdict_inventaire", rap["verdict"], la).upper()))
    out.append("  " + lib.t("emprunts.inv.images", la, uniques=rap["images"],
                            doublons=rap["doublons"],
                            backend=rap["backend_images"] or aucun))
    out.append("  " + lib.t(
        "emprunts.inv.texte", la,
        pages=rap["pages_lues"] if rap["pages_lues"] is not None else "0",
        backend=rap["backend_texte"] or aucun))
    for a in rap["appariements"]:
        out.append("")
        out.append("  " + lib.t(
            "emprunts.inv.appariement", la,
            niveau=lib.valeur("emprunts.confiance", a["niveau"], la).upper(),
            libelle=(a.get("libelle")
                     or lib.t("emprunts.inv.non_identifiee", la))))
        out.append("    " + lib.t(
            "emprunts.inv.fichier", la, fichier=a.get("fichier"),
            page=(a.get("page") if a.get("page")
                  else lib.t("emprunts.inv.page_inconnue", la))))
        out.append("    " + lib.t(
            "emprunts.inv.legende", la,
            legende=(a["legende"] if a.get("legende")
                     else lib.t("emprunts.inv.legende_absente", la))))
        out.append("    " + lib.t("emprunts.inv.confiance", la,
                                  valeur="%.2f" % a["confiance"],
                                  motif=a["motif"]))
    for l in rap["legendes_sans_image"]:
        out.append("")
        out.append("  " + lib.t(
            "emprunts.inv.sans_image", la, libelle=l["libelle"],
            page=l.get("page"),
            legende=(l.get("legende")
                     or lib.t("emprunts.inv.legende_vide", la))))
    out.append("")
    out.append(lib.t("emprunts.inv.notes" if rap["notes"]
                     else "emprunts.inv.notes_aucune", la))
    out += ["  - %s" % n for n in rap["notes"]]
    out.append(lib.t("emprunts.limite_ligne", la,
                     limite=rap.get("limite") or lib.t("emprunts.limite", la)))
    return "\n".join(out)


def rapport_localisation_texte(fiche, langue_affichage=None):
    """Rendu texte de la localisation d'une source par son DOI."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    out = [lib.t("emprunts.loc.titre", la, doi=fiche["doi"])]
    out.append("  " + lib.t("emprunts.loc.etat", la, etat=lib.valeur(
        "emprunts.etat_localisation", fiche["etat"], la).upper()))
    out.append("  " + lib.t("emprunts.loc.motif", la, motif=fiche["detail"]))
    out.append("  " + lib.t("emprunts.loc.index", la, reponse=lib.t(
        "emprunts.loc.oui" if fiche["index_consulte"]
        else "emprunts.loc.non", la)))
    if fiche.get("titre"):
        out.append("  " + lib.t("emprunts.loc.titre_source", la,
                                titre=fiche["titre"]))
    if fiche.get("revue"):
        out.append("  " + lib.t("emprunts.loc.revue", la,
                                revue=fiche["revue"]))
    if fiche.get("auteur"):
        out.append("  " + lib.t("emprunts.loc.auteur", la,
                                auteur=fiche["auteur"]))
    out.append("  " + lib.t(
        "emprunts.loc.acces", la, ouvert=fiche["est_ouvert"],
        statut=(fiche["statut_oa"]
                or lib.t("emprunts.loc.statut_non_declare", la))))
    if fiche.get("licence_declaree"):
        out.append("  " + lib.t("emprunts.loc.licence", la,
                                licence=fiche["licence_declaree"]))
    if fiche.get("url_pdf"):
        out.append("  " + lib.t("emprunts.loc.pdf", la, url=fiche["url_pdf"]))
    if fiche.get("url_page"):
        out.append("  " + lib.t("emprunts.loc.page", la,
                                url=fiche["url_page"]))
    out.append(lib.t("emprunts.garde_fou_ligne", la,
                     garde_fou=fiche.get("garde_fou") or _garde_fou(lib, la)))
    return "\n".join(out)


def rapport_recuperation_texte(rap, langue_affichage=None):
    """Rendu texte d'une recuperation, refus compris. Le message de refus a
    ete compose dans la langue d'affichage par recuperer() : il est repris
    tel quel, entier, sans etre resume."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    out = [lib.t("emprunts.rec.titre", la, etat=lib.valeur(
        "emprunts.etat_recuperation", rap["etat"], la).upper())]
    if rap.get("url"):
        out.append("  " + lib.t("emprunts.rec.adresse", la, url=rap["url"]))
    if rap.get("fichier"):
        out.append("  " + lib.t("emprunts.rec.fichier", la,
                                fichier=rap["fichier"], octets=rap["octets"]))
    out.append("  %s" % rap["message"])
    return "\n".join(out)


def rapport_texte(rap, langue_affichage=None):
    """Rendu texte de la chaine complete. Voir chainer()."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    out = [lib.t("emprunts.ch.titre", la, doi=rap.get("doi") or "?")]
    out.append("  " + lib.t("emprunts.ch.verdict", la, verdict=lib.valeur(
        "emprunts.verdict_chaine", rap["verdict"], la).upper()))
    for e in rap["etapes"]:
        out.append("  %-12s %-28s %s"
                   % (e["etape"],
                      _statut_lisible(e["etape"], e["statut"], lib, la),
                      e["detail"]))
    for entree in rap["entrees"]:
        out.append("")
        out.append("  " + lib.t("emprunts.ch.entree", la,
                                id=entree.get("id")))
        a_etablir = lib.t("emprunts.ch.a_etablir", la)
        out.append("    " + lib.t("emprunts.ch.libelle", la,
                                  libelle=entree.get("libelle") or a_etablir))
        out.append("    " + lib.t(
            "emprunts.ch.legende_origine", la,
            legende=(entree.get("legende_origine")
                     or lib.t("emprunts.ch.absente", la))))
        out.append("    " + lib.t("emprunts.ch.source", la,
                                  source=entree.get("source") or a_etablir))
        out.append("    " + lib.t(
            "emprunts.ch.licence", la,
            licence=(entree.get("licence")
                     or lib.t("emprunts.ch.licence_inconnue", la))))
        out.append("    " + lib.t(
            "emprunts.ch.verdict_entree", la,
            verdict=(lib.valeur("droits.verdict", entree["verdict"], la)
                     if entree.get("verdict")
                     else lib.t("emprunts.ch.indetermine", la))))
        if entree.get("modifications"):
            out.append("    " + lib.t("emprunts.ch.modifications", la,
                                      modifications=entree["modifications"]))
        out.append("    " + lib.t(
            "emprunts.ch.fichier", la,
            fichier=(entree.get("fichier")
                     or lib.t("emprunts.ch.aucun_fichier", la))))
        out.append("    " + lib.t(
            "emprunts.ch.confiance", la,
            confiance=lib.valeur("emprunts.confiance",
                                 entree.get("confiance_appariement")
                                 or "nulle", la)))
    if rap["erreurs_registre"]:
        out.append("")
        out.append(lib.t("emprunts.ch.erreurs_registre", la))
        out += ["  - %s" % e for e in rap["erreurs_registre"]]
    if rap["avertissements_registre"]:
        out.append(lib.t("emprunts.ch.avertissements_registre", la))
        out += ["  - %s" % a for a in rap["avertissements_registre"]]
    if rap.get("registre"):
        out.append(lib.t("emprunts.ch.registre_ecrit", la,
                         chemin=rap["registre"]))
    out += _voies_texte(rap.get("voies"), lib, la)
    out.append("")
    out.append(lib.t("emprunts.garde_fou_ligne", la,
                     garde_fou=rap.get("garde_fou") or _garde_fou(lib, la)))
    out.append(lib.t("emprunts.limite_ligne", la,
                     limite=rap.get("limite") or lib.t("emprunts.limite", la)))
    return "\n".join(out)


def _voies_texte(voies, lib, la):
    """Les deux voies de repli, en texte, quand elles existent."""
    if not voies:
        return []
    out = ["", lib.t("emprunts.v.entete", la)]
    out.append("  " + lib.t("emprunts.v.voie_1", la,
                            voie=voies["autorisation"]["voie"],
                            reference=voies["autorisation"]["reference"]))
    out += ["     - %s" % e for e in voies["autorisation"]["etapes"]]
    red = voies.get("redessin")
    if red:
        out.append("  " + lib.t("emprunts.v.voie_2", la, voie=red["voie"]))
        out.append("     " + lib.t("emprunts.v.mention", la,
                                   mention=red["mention"]))
        out.append("     " + lib.t("emprunts.v.types", la,
                                   types=", ".join(red["types_figures"])))
        out.append("     %s" % red["commande"])
    return out


def main(argv=None):
    # Une console Windows en page de code heritee ne sait pas encoder tout ce
    # qu'un index renvoie (titre en japonais, tiret long, guillemet courbe).
    # Sans garde, l'impression leve UnicodeEncodeError et la commande echoue
    # alors que la mesure est juste : le caractere se degrade, jamais le
    # resultat. Rien n'est reconfigure quand la sortie est deja detournee.
    for _flux in (sys.stdout, sys.stderr):
        try:
            _flux.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass
    p = argparse.ArgumentParser(
        description="Récupération et identification d'une figure tierce : "
                    "appariement image-légende-page, localisation en accès "
                    "ouvert, chaînage vers les droits. Consultatif par défaut.",
        epilog=GARDE_FOU)
    sp = p.add_subparsers(dest="action", required=True)

    pi = sp.add_parser("inventorier",
                       help="apparier image, légende et page dans un document")
    pi.add_argument("source")
    pi.add_argument("--out", help="dossier des images extraites")
    pi.add_argument("--min-bytes", type=int, default=1024, dest="min_bytes")
    pi.add_argument("--format", choices=["text", "json"], default="text")
    pi.add_argument("--strict", action="store_true",
                    help="code de sortie 1 si un appariement n'est pas sûr")

    pl = sp.add_parser("localiser",
                       help="état d'accès ouvert et adresse du PDF, par DOI")
    pl.add_argument("--doi", required=True)
    pl.add_argument("--reseau", action="store_true",
                    help="interroger OpenAlex (désactivé par défaut)")
    pl.add_argument("--openalex-cle")
    pl.add_argument("--format", choices=["text", "json"], default="text")
    pl.add_argument("--strict", action="store_true")

    pr = sp.add_parser("recuperer",
                       help="télécharger, et seulement depuis une "
                            "localisation déclarée ouverte")
    pr.add_argument("--doi", required=True)
    pr.add_argument("--out", required=True)
    pr.add_argument("--reseau", action="store_true")
    pr.add_argument("--openalex-cle")
    pr.add_argument("--format", choices=["text", "json"], default="text")
    pr.add_argument("--strict", action="store_true")

    pc = sp.add_parser("chainer",
                       help="localiser, récupérer, inventorier, droits, "
                            "entrée de registre")
    pc.add_argument("--doi", required=True)
    pc.add_argument("--out", help="dossier de travail")
    pc.add_argument("--source", help="PDF déjà possédé, aucun téléchargement")
    pc.add_argument("--figure", help="numéro de figure à retenir")
    pc.add_argument("--modifications",
                    help="modifications apportées à la figure (recadrage)")
    pc.add_argument("--registre", help="registre à créer ou à compléter")
    pc.add_argument("--reseau", action="store_true")
    pc.add_argument("--openalex-cle")
    pc.add_argument("--format", choices=["text", "json"], default="text")
    pc.add_argument("--strict", action="store_true")

    for sous in (pi, pl, pr, pc):
        sous.add_argument("--langue-affichage", choices=["fr", "en"],
                          default=None,
                          help="langue des libellés du rapport texte (défaut "
                               "fr : ni un PDF ni un DOI ne portent de pragme "
                               "de langue). La sortie JSON reste française "
                               "quoi qu'il arrive")
    return _executer(p.parse_args(argv))


def _sortir(rapport, format_, texte):
    """Ecrit le rapport dans le format demande."""
    if format_ == "json":
        print(json.dumps(_sans_prive(rapport), ensure_ascii=False, indent=2))
    else:
        print(texte)


def _executer(a):
    """Execute l'action demandee et rend le code de sortie.

    Le mode JSON ne recoit jamais de langue d'affichage : les evals et le jeu
    d'or lisent ce JSON, il reste francais quoi qu'il arrive."""
    la = (None if a.format == "json"
          else _lib().resoudre_affichage(a.langue_affichage))
    cle = getattr(a, "openalex_cle", None) or os.environ.get("OPENALEX_API_KEY")
    if a.action == "inventorier":
        rap = inventorier(a.source, a.out, a.min_bytes, langue_affichage=la)
        _sortir(rap, a.format, rapport_inventaire_texte(rap, la))
        return 1 if (a.strict and rap["verdict"] != "inventaire apparie") else 0
    if a.action == "localiser":
        fiche = localiser(a.doi, a.reseau, api_key=cle, langue_affichage=la)
        _sortir(fiche, a.format, rapport_localisation_texte(fiche, la))
        return 1 if (a.strict
                     and fiche["etat"] != "acces ouvert confirme") else 0
    if a.action == "recuperer":
        fiche = localiser(a.doi, a.reseau, api_key=cle, langue_affichage=la)
        rap = recuperer(fiche, a.out, langue_affichage=la)
        rap["localisation"] = fiche
        _sortir(rap, a.format,
                "%s\n%s" % (rapport_localisation_texte(fiche, la),
                            rapport_recuperation_texte(rap, la)))
        return 1 if (a.strict and rap["etat"] != "recuperee") else 0
    rap = chainer(a.doi, a.out, a.reseau, a.source, a.figure,
                  a.modifications, a.registre, api_key=cle,
                  langue_affichage=la)
    _sortir(rap, a.format, rapport_texte(rap, la))
    return 1 if (a.strict and rap["verdict"] != "emprunt prepare") else 0


if __name__ == "__main__":
    sys.exit(main())
