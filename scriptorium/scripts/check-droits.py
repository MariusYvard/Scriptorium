#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Controle des droits de reutilisation d'une figure tierce.

Citer la source regle l'honnetete intellectuelle, pas le droit de
reproduction : une figure est une oeuvre protegee independamment du texte de
l'article qui la porte. Ce script resout la licence declaree d'une source par
son DOI, la classe sur une echelle fermee, emet la ligne d'attribution
conforme, nomme l'alternative du redessin depuis les donnees, et valide le
registre des figures empruntees d'un document.

Le script rapporte ce qu'une licence declare. Il ne prononce pas la legalite
d'un usage : le contrat d'une revue, la politique d'un employeur ou le droit
applicable peuvent en decider autrement. Meme partage que check-fuites.py,
qui inspecte sans nettoyer.

Reseau optionnel derriere --reseau, en reutilisant les fonctions de requete
de verify-sources.py chargees par chemin (meme principe que gabarit.py qui
importe images.py). Un index qui ne repond pas produit une mesure omise et
declaree, jamais une valeur inventee. Point central : "licence inconnue" ne
se confond jamais avec "autorisation requise", comme "non mesurable" ne se
confond pas avec "lecture non fiable" dans check-lecture-pdf.py. Une absence
d'information n'est ni une interdiction, ni une permission.

Langue d'affichage : chaque fonction qui compose une chaine lisible prend un
parametre langue_affichage optionnel. Sans lui, les chaines sont les chaines
francaises d'origine a l'octet pres, et ce sont elles que serialise
--format json. Le verdict, l'etat d'autorisation, le nom de licence et
l'element manquant restent des valeurs machine francaises dans les deux
langues, comme le veut le partage pose par libelles.py. La ligne de credit
suit la langue d'affichage : elle se colle dans le document, et un document
anglais ne porte pas un credit francais.

Usage :
    python3 check-droits.py licence --doi 10.xxxx/yyyy [--reseau] [--format text|json] [--strict]
    python3 check-droits.py registre REGISTRE.json [--reseau] [--format text|json] [--strict]
    python3 check-droits.py credits REGISTRE.json [--sortie texte|html|latex]
    (les trois acceptent --langue-affichage fr|en)

Module importable : normaliser_licence, classer, resoudre_doi,
ligne_attribution, alternative_redessin, valider_registre, section_credits,
analyser, rapport_texte.
"""
import argparse
import importlib.util
import json
import os
import sys

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


INDEX_TIMEOUT = 8

VERDICTS = ("reutilisable avec attribution", "reutilisable sous conditions",
            "autorisation requise", "licence inconnue")
RANG_VERDICT = {v: i for i, v in enumerate(VERDICTS)}

VERDICTS_REGISTRE = ("registre invalide", "autorisations a obtenir",
                     "licences a etablir", "credits complets")

ETATS_AUTORISATION = ("non demandee", "demandee", "obtenue", "refusee")

TYPES_FIGURES_DONNEES = ("courbe", "nuage", "histogramme", "boite", "flux",
                         "prisma")

LIMITE = _lib().t("droits.limite", "fr")

# Familles de licence, table locale sans reseau. Chaque entree dit ce que la
# licence declare permettre, jamais ce que le droit autorise dans un cas
# donne. Un ND ferme toute adaptation, donc tout recadrage ; un SA impose sa
# licence au document derive ; un NC ferme l'usage commercial.
#
# "conditions" porte des CLES de libelle, pas des phrases : la condition
# imprimee se compose au moment ou la fiche est produite, dans la langue
# d'affichage demandee. "nom" reste le libelle francais, c'est lui que porte
# la sortie JSON ; sa traduction passe par la table VALEURS, indexee par le
# code de la famille.
FAMILLES = {
    "cc0": {
        "nom": "CC0", "commercial": True, "adaptation": True,
        "partage_identique": False, "attribution_exigee": False,
        "verdict": "reutilisable avec attribution",
        "conditions": ["droits.c.attribution_non_exigee"]},
    "domaine-public": {
        "nom": "Domaine public", "commercial": True, "adaptation": True,
        "partage_identique": False, "attribution_exigee": False,
        "verdict": "reutilisable avec attribution",
        "conditions": ["droits.c.attribution_non_exigee"]},
    "cc-by": {
        "nom": "CC BY", "commercial": True, "adaptation": True,
        "partage_identique": False, "attribution_exigee": True,
        "verdict": "reutilisable avec attribution",
        "conditions": ["droits.c.attribution_complete",
                       "droits.c.mention_modifications"]},
    "cc-by-sa": {
        "nom": "CC BY-SA", "commercial": True, "adaptation": True,
        "partage_identique": True, "attribution_exigee": True,
        "verdict": "reutilisable sous conditions",
        "conditions": ["droits.c.partage_identique",
                       "droits.c.destination_contrainte"]},
    "cc-by-nc": {
        "nom": "CC BY-NC", "commercial": False, "adaptation": True,
        "partage_identique": False, "attribution_exigee": True,
        "verdict": "reutilisable sous conditions",
        "conditions": ["droits.c.commercial_ferme_exemples"]},
    "cc-by-nc-sa": {
        "nom": "CC BY-NC-SA", "commercial": False, "adaptation": True,
        "partage_identique": True, "attribution_exigee": True,
        "verdict": "reutilisable sous conditions",
        "conditions": ["droits.c.commercial_ferme",
                       "droits.c.partage_identique"]},
    "cc-by-nd": {
        "nom": "CC BY-ND", "commercial": True, "adaptation": False,
        "partage_identique": False, "attribution_exigee": True,
        "verdict": "reutilisable sous conditions",
        "conditions": ["droits.c.aucune_adaptation_legende",
                       "droits.c.figure_entiere"]},
    "cc-by-nc-nd": {
        "nom": "CC BY-NC-ND", "commercial": False, "adaptation": False,
        "partage_identique": False, "attribution_exigee": True,
        "verdict": "reutilisable sous conditions",
        "conditions": ["droits.c.commercial_ferme",
                       "droits.c.aucune_adaptation"]},
    "tous-droits-reserves": {
        "nom": "Tous droits réservés", "commercial": False,
        "adaptation": False, "partage_identique": False,
        "attribution_exigee": True,
        "verdict": "autorisation requise",
        "conditions": ["droits.c.demande_ecrite",
                       "droits.c.fouille_pas_republication"]},
}

# Chemins Creative Commons rencontres dans une URL de licence Crossref.
_CC_CHEMINS = {"by": "cc-by", "by-sa": "cc-by-sa", "by-nd": "cc-by-nd",
               "by-nc": "cc-by-nc", "by-nc-sa": "cc-by-nc-sa",
               "by-nc-nd": "cc-by-nc-nd"}

# Slugs servis par OpenAlex dans best_oa_location.license et license_id.
# Verifie le 2026-08-17 sur une reponse reelle de l'API : la valeur y est
# "cc-by" et license_id vaut "https://openalex.org/licenses/cc-by".
_SLUGS = {"cc-by": "cc-by", "cc-by-sa": "cc-by-sa", "cc-by-nd": "cc-by-nd",
          "cc-by-nc": "cc-by-nc", "cc-by-nc-sa": "cc-by-nc-sa",
          "cc-by-nc-nd": "cc-by-nc-nd", "cc0": "cc0",
          "public-domain": "domaine-public", "pd": "domaine-public"}

# Conditions d'editeur rencontrees dans le tableau license de Crossref.
# Aucune n'est une permission de republication : une licence de fouille de
# textes couvre l'exploration automatisee, pas la reproduction d'une figure
# dans un autre document. Verifie le 2026-08-17 sur 10.1016/j.cell.2011.02.013,
# dont les trois entrees license pointent toutes vers des conditions Elsevier
# (content-version tdm deux fois, vor une fois) sans aucune licence ouverte.
# Un tableau license rempli ne vaut donc pas licence de reutilisation.
TERMES_EDITEUR = (
    ("elsevier.com/tdm", "Elsevier, licence de fouille de textes et de données"),
    ("elsevier.com/legal/tdmrep", "Elsevier, licence de fouille de textes et de données"),
    ("elsevier.com/open-access/userlicense", "Elsevier, licence utilisateur"),
    ("springernature.com/gp/researchers/text-and-data-mining",
     "Springer Nature, fouille de textes et de données"),
    ("springer.com/tdm", "Springer, fouille de textes et de données"),
    ("onlinelibrary.wiley.com/termsandconditions", "Wiley, conditions générales"),
    ("wiley.com/terms-and-conditions", "Wiley, conditions générales"),
    ("pubs.acs.org/page/policy", "ACS, politique de droits"),
    ("ieee.org/publications/rights", "IEEE, politique de droits"),
    ("publishing.aip.org/resources/researchers/rights-and-permissions",
     "AIP, droits et permissions"),
    ("rsc.org/journals-books-databases/journal-authors-reviewers/licences-copyright-permissions",
     "RSC, licences et permissions"),
)

_MENTIONS_RESERVEES = ("tous droits reserves", "tous droits réservés",
                       "all rights reserved", "copyright", "proprietary")


def _charger_verify_sources():
    """Charge verify-sources.py par chemin, comme check-lecture-pdf.py charge
    check-presentation.py, pour reutiliser ses fonctions de requete plutot que
    de les redire. Renvoie None si le fichier est absent : degradation propre,
    jamais un plantage."""
    try:
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "verify-sources.py")
        if not os.path.isfile(chemin):
            return None
        spec = importlib.util.spec_from_file_location("verify_sources_mod", chemin)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


# Charge une seule fois au niveau module : les evals remplacent
# _VSRC._requete_json pour simuler les reponses d'index hors ligne.
_VSRC = _charger_verify_sources()


def _lire_code(bas):
    """Reconnait un code de licence dans un slug OpenAlex ou une URL Crossref.

    Retourne (code, version, nom_editeur). Une valeur non reconnue rend
    (None, None, None) : une licence illisible n'est pas une licence qui
    interdit, elle reste une absence d'information.
    """
    for fragment, nom in TERMES_EDITEUR:
        if fragment in bas:
            return "tous-droits-reserves", None, nom
    if "creativecommons.org/publicdomain/zero" in bas:
        return "cc0", "1.0", None
    if "creativecommons.org/publicdomain/mark" in bas:
        return "domaine-public", "1.0", None
    if "creativecommons.org/licenses/" in bas:
        reste = bas.split("creativecommons.org/licenses/", 1)[1]
        morceaux = [m for m in reste.strip("/").split("/") if m]
        chemin = morceaux[0] if morceaux else ""
        version = morceaux[1] if len(morceaux) > 1 else None
        code = _CC_CHEMINS.get(chemin)
        if code:
            return code, version, None
        return None, None, None
    if bas in _SLUGS:
        return _SLUGS[bas], None, None
    dernier = bas.rstrip("/").split("/")[-1]
    if dernier in _SLUGS:
        return _SLUGS[dernier], None, None
    for mention in _MENTIONS_RESERVEES:
        if mention in bas:
            return "tous-droits-reserves", None, None
    return None, None, None


def normaliser_licence(valeur, version_contenu=None, date_application=None,
                       origine=None, langue_affichage=None):
    """Normalise une valeur de licence (slug OpenAlex ou URL Crossref) en une
    fiche fermee. Une valeur non reconnue est declaree telle quelle, avec
    reconnue=False et le verdict "licence inconnue".

    Sans langue_affichage, les conditions sont les phrases francaises
    d'origine a l'octet pres. La cle privee "_editeur" retient la condition
    d'editeur reconnue, s'il y en a une : elle sert a traduire le nom
    affiche, et _sans_prive la retire de la sortie JSON."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    fiche = {"brut": valeur, "code": None, "nom": None, "version": None,
             "url": None, "reconnue": False, "commercial": None,
             "adaptation": None, "partage_identique": None,
             "attribution_exigee": None, "conditions": [],
             "verdict": "licence inconnue", "version_contenu": version_contenu,
             "date_application": date_application, "origine": origine,
             "_editeur": None}
    if not valeur or not isinstance(valeur, str):
        return fiche
    v = valeur.strip()
    bas = v.lower()
    if bas.startswith("http"):
        fiche["url"] = v
    code, version, nom_editeur = _lire_code(bas)
    if code is None:
        return fiche
    famille = FAMILLES[code]
    fiche.update({"code": code, "version": version, "reconnue": True,
                  "commercial": famille["commercial"],
                  "adaptation": famille["adaptation"],
                  "partage_identique": famille["partage_identique"],
                  "attribution_exigee": famille["attribution_exigee"],
                  "conditions": [lib.t(c, la) for c in famille["conditions"]],
                  "verdict": famille["verdict"], "_editeur": nom_editeur})
    nom = nom_editeur or famille["nom"]
    fiche["nom"] = "%s %s" % (nom, version) if version and not nom_editeur else nom
    return fiche


def _nom_licence(fiche, lib, la):
    """Nom affiche d'une licence, dans la langue demandee.

    Le nom porte par la fiche est le libelle francais, valeur machine du
    JSON. La traduction s'appuie sur le CODE de famille (ou sur la condition
    d'editeur reconnue), jamais sur le nom lui-meme, pour que la version lue
    dans l'URL se recolle a l'identique."""
    if fiche.get("_editeur"):
        return lib.valeur("droits.editeur", fiche["_editeur"], la)
    if not fiche.get("code"):
        return fiche.get("nom") or fiche.get("brut")
    nom = lib.valeur("droits.licence", fiche["code"], la)
    return "%s %s" % (nom, fiche["version"]) if fiche.get("version") else nom


def classer(fiches):
    """Verdict ferme a partir des licences declarees pour une meme source.

    La plus permissive des licences reconnues l'emporte : une revue hybride
    declare souvent ses conditions de fouille de textes a cote de la licence
    ouverte de l'article. Aucune licence reconnue rend "licence inconnue",
    jamais "autorisation requise" : ne pas savoir n'est pas se voir interdire.
    """
    reconnues = [f for f in fiches if f.get("reconnue")]
    if not reconnues:
        return "licence inconnue"
    return min((f["verdict"] for f in reconnues), key=lambda v: RANG_VERDICT[v])


def licence_crossref(doi, timeout=INDEX_TIMEOUT, langue_affichage=None):
    """Licences declarees par Crossref pour un DOI.

    Crossref porte un tableau "license" dont chaque entree donne une URL
    (cle "URL", en capitales), une date d'application ("start"), un delai
    ("delay-in-days") et la version de contenu visee ("content-version" :
    vor, am, tdm, unspecified). Structure verifiee le 2026-08-17 sur
    10.1371/journal.pone.0000308 et sur 10.1016/j.cell.2011.02.013.
    """
    vide = {"consulte": False, "trouve": False, "licences": [], "titre": None}
    if _VSRC is None:
        return dict(vide, motif="verify-sources.py introuvable")
    code, data = _VSRC._requete_json("https://api.crossref.org/works/%s" % doi,
                                     timeout)
    if code is None:
        return dict(vide)
    if code == 404:
        return dict(vide, consulte=True)
    message = (data or {}).get("message") or {}
    fiches = []
    for entree in message.get("license") or []:
        if not isinstance(entree, dict):
            continue
        fiches.append(normaliser_licence(
            entree.get("URL"),
            version_contenu=entree.get("content-version"),
            date_application=((entree.get("start") or {}).get("date-time")),
            origine="crossref", langue_affichage=langue_affichage))
    titres = message.get("title") or []
    return {"consulte": True, "trouve": True, "licences": fiches,
            "titre": titres[0] if titres else None}


def licence_openalex(doi, timeout=INDEX_TIMEOUT, api_key=None,
                     langue_affichage=None):
    """Licence de la meilleure localisation ouverte declaree par OpenAlex.

    OpenAlex expose l'acces ouvert dans "open_access" (is_oa, oa_status) et
    la licence par localisation dans "best_oa_location" et
    "primary_location" (cles "license", slug type cc-by, et "license_id",
    URL type https://openalex.org/licenses/cc-by). Structure verifiee le
    2026-08-17 sur 10.1371/journal.pone.0000308.

    Une cle API est acceptee (constat de verify-sources.py du 2026-07-08 sur
    l'authentification OpenAlex). Sans cle, la requete est tentee quand meme
    et un refus degrade en index non consulte, jamais en echec de la source.
    """
    vide = {"consulte": False, "trouve": False, "licences": [], "titre": None,
            "acces_ouvert": None}
    if _VSRC is None:
        return dict(vide, motif="verify-sources.py introuvable")
    url = ("https://api.openalex.org/works/https://doi.org/%s"
           "?select=id,doi,title,open_access,best_oa_location,primary_location"
           % doi)
    if api_key:
        url += "&api_key=%s" % api_key
    code, data = _VSRC._requete_json(url, timeout)
    if code is None:
        return dict(vide)
    if code == 404:
        return dict(vide, consulte=True)
    data = data or {}
    fiches = []
    for cle in ("best_oa_location", "primary_location"):
        loc = data.get(cle) or {}
        valeur = loc.get("license") or loc.get("license_id")
        if valeur:
            fiches.append(normaliser_licence(
                valeur, origine="openalex/%s" % cle,
                langue_affichage=langue_affichage))
    acces = data.get("open_access") or {}
    return {"consulte": True, "trouve": True, "licences": fiches,
            "titre": data.get("title"),
            "acces_ouvert": {"est_ouvert": acces.get("is_oa"),
                             "statut": acces.get("oa_status")} if acces else None}


def resoudre_doi(doi, reseau=False, timeout=INDEX_TIMEOUT,
                 api_key_openalex=None, langue_affichage=None):
    """Resout la licence declaree d'une source par son DOI.

    Sans --reseau, aucun index n'est consulte et le verdict reste "licence
    inconnue" avec son motif. Avec --reseau, Crossref et OpenAlex sont
    interroges ; un index qui ne repond pas sort du calcul et le dit. Trois
    situations restent distinctes : aucun index joignable, index joignable
    sans licence declaree, licence declaree et lue. Aucune ne produit
    "autorisation requise" par defaut.
    """
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    rapport = {"doi": doi, "reseau": bool(reseau), "index": {}, "licences": [],
               "verdict": "licence inconnue", "detail": "", "titre": None,
               "acces_ouvert": None, "conditions": [],
               "limite": lib.t("droits.limite", la)}
    if not reseau:
        rapport["detail"] = lib.t("droits.d.reseau_desactive", la)
        rapport["alternative"] = alternative_redessin(
            rapport["verdict"], langue_affichage=la)
        return rapport

    cr = licence_crossref(doi, timeout, langue_affichage=la)
    oa = licence_openalex(doi, timeout, api_key_openalex, langue_affichage=la)
    rapport["index"] = {
        "crossref": {"consulte": cr["consulte"], "trouve": cr["trouve"],
                     "licences": len(cr["licences"])},
        "openalex": {"consulte": oa["consulte"], "trouve": oa["trouve"],
                     "licences": len(oa["licences"])}}
    rapport["titre"] = cr.get("titre") or oa.get("titre")
    rapport["acces_ouvert"] = oa.get("acces_ouvert")
    fiches = list(cr["licences"]) + list(oa["licences"])
    rapport["licences"] = fiches
    rapport["verdict"] = classer(fiches)

    consultes = [n for n, r in (("Crossref", cr), ("OpenAlex", oa))
                 if r["consulte"]]
    trouves = [n for n, r in (("Crossref", cr), ("OpenAlex", oa))
               if r["consulte"] and r["trouve"]]
    reconnues = [f for f in fiches if f["reconnue"]]
    if reconnues:
        retenue = min(reconnues, key=lambda f: RANG_VERDICT[f["verdict"]])
        rapport["conditions"] = list(retenue["conditions"])
        rapport["licence_retenue"] = retenue
        rapport["detail"] = lib.t(
            "droits.d.licence_declaree", la,
            licence=_nom_licence(retenue, lib, la),
            index=", ".join(trouves) or lib.t("droits.d.index_generique", la))
    elif fiches:
        rapport["detail"] = lib.t("droits.d.aucune_reconnue", la,
                                  n=len(fiches))
    elif trouves:
        rapport["detail"] = lib.t("droits.d.aucune_declaree", la,
                                  index=", ".join(trouves))
    elif consultes:
        rapport["detail"] = lib.t("droits.d.doi_non_trouve", la,
                                  index=", ".join(consultes))
    else:
        rapport["detail"] = lib.t("droits.d.aucun_index", la)
    rapport["alternative"] = alternative_redessin(rapport["verdict"],
                                                  langue_affichage=la)
    return rapport


def alternative_redessin(verdict, auteur=None, type_figure=None,
                         langue_affichage=None):
    """Nomme la voie qui evite la question du droit de reproduction.

    Les donnees ne sont pas protegeables, leur mise en forme l'est. Refaire
    la figure a partir des valeurs publiees, avec le rendu du document et la
    mention "d'apres les donnees de X", ne reproduit aucune oeuvre. Proposee
    quand le verdict est "autorisation requise" ou "licence inconnue", nulle
    sinon : une figure deja reutilisable n'a pas besoin d'etre refaite.
    """
    if verdict not in ("autorisation requise", "licence inconnue"):
        return None
    if type_figure and type_figure not in TYPES_FIGURES_DONNEES:
        type_figure = None
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    return {
        "voie": lib.t("droits.alt.voie", la),
        "mention": lib.t("droits.alt.mention", la,
                         auteur=auteur or lib.t("droits.alt.auteur_inconnu",
                                                la)),
        # Les types de figure et la commande sont des valeurs machine : le
        # nom du type est celui qu'attend figures.py, il ne se traduit pas.
        "types_figures": list(TYPES_FIGURES_DONNEES),
        "commande": ("python3 figures.py %s --data donnees.json --out figure.svg"
                     % (type_figure or "courbe")),
        "note": lib.t("droits.alt.note", la),
    }


def _echapper_html(s):
    """Echappement minimal, sans dependance ni import de module homonyme."""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _echapper_latex(s):
    """Echappement des caracteres actifs de LaTeX dans un texte courant."""
    sortie = str(s).replace("\\", "\\textbackslash{}")
    for c in ("&", "%", "$", "#", "_", "{", "}"):
        sortie = sortie.replace(c, "\\" + c)
    return sortie.replace("~", "\\textasciitilde{}").replace("^", "\\textasciicircum{}")


def ligne_attribution(figure, licence=None, langue_affichage=None):
    """Ligne de crédit prête à coller, dans les trois formes utiles.

    Une licence Creative Commons demande le titre, l'auteur, la source et la
    licence, plus la mention des modifications quand la figure a ete recadree
    ou redessinee. Les elements absents ne sont pas inventes : ils sont listes
    dans "manques" et le gabarit porte alors une marque visible.

    La ligne suit la langue d'affichage, parce qu'elle se colle dans le
    document : un document anglais ne porte pas un credit francais. La liste
    "manques", elle, reste en valeurs machine francaises.
    """
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    fiche = licence or normaliser_licence(figure.get("licence"),
                                          langue_affichage=la)
    libelle = (figure.get("libelle") or figure.get("id")
               or lib.t("droits.attr.figure_defaut", la))
    titre = figure.get("titre")
    auteur = figure.get("auteur")
    source = figure.get("source")
    doi = figure.get("doi")
    lien = figure.get("url") or ("https://doi.org/%s" % doi if doi else None)
    nom_licence = fiche.get("nom") or (figure.get("licence")
                                       if isinstance(figure.get("licence"), str)
                                       else None)
    manques = [nom for nom, val in (("titre", titre), ("auteur", auteur),
                                    ("source", source),
                                    ("licence", nom_licence)) if not val]
    if nom_licence and fiche.get("reconnue"):
        nom_licence = _nom_licence(fiche, lib, la)

    def marque(element):
        return lib.t("droits.attr.marque", la,
                     element=lib.valeur("droits.element", element, la))

    titre_a = titre or marque("titre")
    auteur_a = auteur or marque("auteur")
    source_a = source or marque("source")
    licence_a = nom_licence or marque("licence")
    modifs = figure.get("modifications")
    phrase_modif = (lib.t("droits.attr.modifiee", la, modifications=modifs)
                    if modifs else lib.t("droits.attr.sans_modification", la))

    source_txt = (lib.t("droits.attr.source_lien", la, source=source_a,
                        lien=lien) if lien else source_a)
    texte = lib.t("droits.attr.texte", la, libelle=libelle, titre=titre_a,
                  auteur=auteur_a, source=source_txt, licence=licence_a,
                  modification=phrase_modif)

    lien_h = ('<a href="%s">%s</a>' % (_echapper_html(lien),
                                       _echapper_html(source_a))
              if lien else _echapper_html(source_a))
    licence_h = ('<a href="%s">%s</a>' % (_echapper_html(fiche["url"]),
                                          _echapper_html(licence_a))
                 if fiche.get("url") else _echapper_html(licence_a))
    html = lib.t("droits.attr.html", la, libelle=_echapper_html(libelle),
                 titre=_echapper_html(titre_a),
                 auteur=_echapper_html(auteur_a), source=lien_h,
                 licence=licence_h,
                 modification=_echapper_html(phrase_modif))

    lien_l = ("\\href{%s}{%s}" % (lien, _echapper_latex(source_a)) if lien
              else _echapper_latex(source_a))
    corps_l = lib.t("droits.attr.latex_corps", la,
                    titre=_echapper_latex(titre_a),
                    auteur=_echapper_latex(auteur_a), source=lien_l,
                    licence=_echapper_latex(licence_a),
                    modification=_echapper_latex(phrase_modif))
    latex = "\\caption[%s]{%s}" % (_echapper_latex(titre_a), corps_l)
    return {"texte": texte, "html": html, "latex": latex,
            "latex_credit": "%s : %s" % (_echapper_latex(libelle), corps_l),
            "manques": manques, "modifications_declarees": bool(modifs)}


def charger_registre(chemin):
    """Lit le registre des figures empruntees. Meme forme declarative que
    assets/registre-logos.exemple.json : un objet, une liste d'entrees, une
    entree par figure."""
    with open(chemin, encoding="utf-8") as f:
        registre = json.load(f)
    if isinstance(registre, dict):
        registre = dict(registre)
        registre["_chemin"] = chemin
    return registre


def valider_registre(registre, langue_affichage=None):
    """Valide le registre. Retourne (erreurs, avertissements).

    Une erreur rend le registre inexploitable pour produire la section de
    credits : identifiant absent ou duplique, source absente, verdict hors
    liste fermee, verdict declare que la licence declaree contredit,
    modification declaree sous une licence qui interdit toute adaptation,
    autorisation refusee sur une figure conservee.
    """
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    erreurs, avertissements = [], []
    if not isinstance(registre, dict):
        return [lib.t("droits.v.pas_un_objet", la)], []
    figures = registre.get("figures")
    if not isinstance(figures, list) or not figures:
        return [lib.t("droits.v.figures_absentes", la)], []
    vus = set()
    for i, fig in enumerate(figures, 1):
        if not isinstance(fig, dict):
            erreurs.append(lib.t("droits.v.entree_pas_objet", la, rang=i))
            continue
        ident = fig.get("id")
        rang = ident or lib.t("droits.v.rang", la, rang=i)
        if not ident:
            erreurs.append(lib.t("droits.v.id_absent", la, rang=i))
        elif ident in vus:
            erreurs.append(lib.t("droits.v.id_duplique", la, rang=ident))
        else:
            vus.add(ident)
        if not fig.get("source"):
            erreurs.append(lib.t("droits.v.source_absente", la, rang=rang))
        if not fig.get("titre"):
            avertissements.append(lib.t("droits.v.titre_absent", la,
                                        rang=rang))
        if not fig.get("auteur"):
            avertissements.append(lib.t("droits.v.auteur_absent", la,
                                        rang=rang))
        if not fig.get("doi") and not fig.get("url"):
            avertissements.append(lib.t("droits.v.sans_lien", la, rang=rang))
        _valider_verdict(fig, rang, erreurs, avertissements, lib, la)
    return erreurs, avertissements


def _valider_verdict(fig, rang, erreurs, avertissements, lib, la):
    """Controle le verdict declare, la licence declaree et l'etat de la
    demande d'autorisation d'une entree du registre."""
    fiche = normaliser_licence(fig.get("licence"), langue_affichage=la)
    declare = fig.get("verdict")
    if declare is not None and declare not in VERDICTS:
        erreurs.append(lib.t(
            "droits.v.verdict_hors_liste", la, rang=rang, verdict=declare,
            liste=", ".join(lib.valeur("droits.verdict", v, la)
                            for v in VERDICTS)))
        declare = None
    calcule = classer([fiche])
    if declare and fiche["reconnue"] and declare != calcule:
        erreurs.append(lib.t(
            "droits.v.verdict_incompatible", la, rang=rang,
            declare=lib.valeur("droits.verdict", declare, la),
            licence=_nom_licence(fiche, lib, la),
            calcule=lib.valeur("droits.verdict", calcule, la)))
    effectif = declare or calcule
    if fig.get("licence") and not fiche["reconnue"]:
        avertissements.append(lib.t("droits.v.licence_non_reconnue", la,
                                    rang=rang, licence=fig.get("licence")))
    if fiche["reconnue"] and fiche["adaptation"] is False and fig.get("modifications"):
        erreurs.append(lib.t(
            "droits.v.modification_interdite", la, rang=rang,
            modifications=fig.get("modifications"),
            licence=_nom_licence(fiche, lib, la)))

    autorisation = fig.get("autorisation")
    etat = None
    if autorisation is not None:
        if not isinstance(autorisation, dict):
            erreurs.append(lib.t("droits.v.autorisation_mal_formee", la,
                                 rang=rang))
        else:
            etat = autorisation.get("etat")
            if etat is not None and etat not in ETATS_AUTORISATION:
                erreurs.append(lib.t(
                    "droits.v.etat_hors_liste", la, rang=rang, etat=etat,
                    liste=", ".join(lib.valeur("droits.autorisation", e, la)
                                    for e in ETATS_AUTORISATION)))
                etat = None
    if etat == "refusee":
        erreurs.append(lib.t("droits.v.autorisation_refusee", la, rang=rang))
    elif effectif == "autorisation requise" and etat != "obtenue":
        avertissements.append(lib.t(
            "droits.v.autorisation_requise", la, rang=rang,
            etat=(lib.valeur("droits.autorisation", etat, la) if etat
                  else lib.t("droits.v.etat_non_renseigne", la))))
    elif effectif == "licence inconnue":
        avertissements.append(lib.t("droits.v.licence_inconnue", la,
                                    rang=rang))
    fig["_fiche"] = fiche
    fig["_verdict_effectif"] = effectif
    fig["_etat_autorisation"] = etat


def section_credits(registre, sortie="texte", langue_affichage=None):
    """Section de crédits des figures empruntées, prête à coller.

    Un document de quarante pages qui emprunte huit figures porte la liste de
    ses crédits, comme il porte sa bibliographie. Une figure dont la
    reproduction n'est pas acquise reste dans la liste, avec son état : la
    section sert aussi de tableau de bord avant diffusion.
    """
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    figures = (registre.get("figures") or []) if isinstance(registre, dict) else []
    lignes = []
    for fig in figures:
        if not isinstance(fig, dict):
            continue
        fiche = fig.get("_fiche") or normaliser_licence(fig.get("licence"),
                                                        langue_affichage=la)
        att = ligne_attribution(fig, fiche, la)
        lignes.append(att["html"] if sortie == "html"
                      else att["latex_credit"] if sortie == "latex"
                      else att["texte"])
    if sortie == "html":
        return ("<section class=\"credits-figures\">\n<h2>%s"
                "</h2>\n%s\n</section>"
                % (lib.t("droits.credits.titre_html", la), "\n".join(lignes)))
    if sortie == "latex":
        return ("\\section*{%s}\n\\begin{itemize}\n%s\n\\end{itemize}"
                % (lib.t("droits.credits.titre_latex", la),
                   "\n".join("\\item %s" % l for l in lignes)))
    return "%s\n\n%s" % (lib.t("droits.credits.titre_md", la),
                         "\n\n".join(lignes))


def analyser(source, reseau=False, timeout=INDEX_TIMEOUT,
             api_key_openalex=None, langue_affichage=None):
    """Valide un registre de figures empruntées et rend le rapport complet.

    Avec --reseau, une figure qui porte un DOI sans licence déclarée voit sa
    licence résolue auprès des index, puis validée comme les autres. Sans
    réseau, rien n'est supposé : la licence absente reste inconnue.

    Sans langue_affichage, chaque chaine lisible du rapport est la chaine
    francaise d'origine a l'octet pres : ce sont elles que serialise
    --format json.
    """
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    registre = charger_registre(source) if isinstance(source, str) else source
    rapport = {"fichier": registre.get("_chemin") if isinstance(registre, dict) else None,
               "reseau": bool(reseau), "figures": [], "erreurs": [],
               "avertissements": [], "verdict": "registre invalide",
               "limite": lib.t("droits.limite", la)}
    figures = (registre.get("figures") or []) if isinstance(registre, dict) else []
    if reseau:
        for fig in figures:
            if isinstance(fig, dict) and fig.get("doi") and not fig.get("licence"):
                res = resoudre_doi(fig["doi"], True, timeout,
                                   api_key_openalex, langue_affichage=la)
                fig["_resolution"] = {"verdict": res["verdict"],
                                      "detail": res["detail"]}
                retenue = res.get("licence_retenue")
                if retenue:
                    fig["licence"] = retenue["brut"]
    erreurs, avertissements = valider_registre(registre, la)
    rapport["erreurs"] = erreurs
    rapport["avertissements"] = avertissements
    return _fermer_rapport(rapport, figures, erreurs, lib, la)


def _fermer_rapport(rapport, figures, erreurs, lib, la):
    """Assemble la fiche de chaque figure et ferme le verdict du registre sur
    quatre valeurs. Une erreur de validation prime : un registre qu'on ne
    peut pas lire ne rend pas un verdict de droits."""
    a_obtenir = a_etablir = False
    for fig in figures:
        if not isinstance(fig, dict):
            continue
        fiche = fig.get("_fiche") or normaliser_licence(fig.get("licence"),
                                                        langue_affichage=la)
        verdict = fig.get("_verdict_effectif") or classer([fiche])
        etat = fig.get("_etat_autorisation")
        if verdict == "autorisation requise" and etat != "obtenue":
            a_obtenir = True
        if verdict == "licence inconnue":
            a_etablir = True
        rapport["figures"].append({
            "id": fig.get("id"), "libelle": fig.get("libelle"),
            "source": fig.get("source"), "doi": fig.get("doi"),
            # En francais, _nom_licence rend exactement fiche["nom"] : la
            # sortie JSON ne bouge pas, seul l'affichage anglais change.
            "licence": (_nom_licence(fiche, lib, la) if fiche.get("nom")
                        else fig.get("licence")),
            "licence_reconnue": fiche.get("reconnue"),
            "verdict": verdict, "conditions": fiche.get("conditions") or [],
            "autorisation": etat,
            "modifications": fig.get("modifications"),
            "resolution": fig.get("_resolution"),
            "attribution": ligne_attribution(fig, fiche, la),
            "alternative": alternative_redessin(verdict, fig.get("auteur"),
                                                langue_affichage=la),
        })
    if erreurs:
        rapport["verdict"] = "registre invalide"
    elif a_obtenir:
        rapport["verdict"] = "autorisations a obtenir"
    elif a_etablir:
        rapport["verdict"] = "licences a etablir"
    else:
        rapport["verdict"] = "credits complets"
    return rapport


def rapport_licence_texte(res, langue_affichage=None):
    """Rendu texte de la resolution de licence d'un DOI. Le motif, les
    conditions et l'alternative ont ete composes dans la langue d'affichage
    par resoudre_doi() : ils sont repris tels quels."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    out = [lib.t("droits.lic.titre", la, doi=res["doi"])]
    out.append("  " + lib.t("droits.lic.verdict", la, verdict=lib.valeur(
        "droits.verdict", res["verdict"], la).upper()))
    out.append("  " + lib.t("droits.lic.motif", la, motif=res["detail"]))
    if res.get("titre"):
        out.append("  " + lib.t("droits.lic.titre_source", la,
                                titre=res["titre"]))
    if res.get("acces_ouvert"):
        ao = res["acces_ouvert"]
        out.append("  " + lib.t("droits.lic.acces_ouvert", la,
                                ouvert=ao.get("est_ouvert"),
                                statut=ao.get("statut")))
    if res.get("index"):
        for nom, r in sorted(res["index"].items()):
            out.append("  " + lib.t("droits.lic.index", la, nom=nom,
                                    consulte=r["consulte"], trouve=r["trouve"],
                                    licences=r["licences"]))
    if res.get("licences"):
        out.append(lib.t("droits.lic.licences", la))
        for f in res["licences"]:
            out.append("  " + lib.t(
                "droits.lic.licence_ligne", la,
                etat=lib.t("droits.lic.reconnue" if f["reconnue"]
                           else "droits.lic.non_reconnue", la),
                nom=_nom_licence(f, lib, la) or f.get("brut"),
                origine=f.get("origine")))
    if res.get("conditions"):
        out.append(lib.t("droits.lic.conditions", la))
        out += ["  - %s" % c for c in res["conditions"]]
    if res.get("alternative"):
        alt = res["alternative"]
        out.append(lib.t("droits.lic.alternative", la, voie=alt["voie"]))
        out.append("  " + lib.t("droits.lic.mention", la,
                                mention=alt["mention"]))
        out.append("  " + lib.t("droits.lic.types_figures", la,
                                types=", ".join(alt["types_figures"])))
        out.append("  %s" % alt["commande"])
    out.append(lib.t("droits.lic.limite", la,
                     limite=res.get("limite") or lib.t("droits.limite", la)))
    return "\n".join(out)


def rapport_texte(rapport, langue_affichage=None):
    """Rendu texte du rapport de registre. Voir analyser() pour la structure.
    Erreurs, avertissements, conditions et credits ont ete composes dans la
    langue d'affichage par analyser() : ils sont repris tels quels."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    out = [lib.t("droits.reg.titre", la,
                 fichier=(rapport.get("fichier")
                          or lib.t("droits.reg.en_memoire", la)))]
    out.append("  " + lib.t("droits.reg.verdict", la, verdict=lib.valeur(
        "droits.verdict_registre", rapport["verdict"], la).upper()))
    out.append("  " + lib.t("droits.reg.figures", la,
                            n=len(rapport["figures"])))
    for f in rapport["figures"]:
        out.append("")
        out.append("  " + lib.t(
            "droits.reg.figure", la,
            verdict=lib.valeur("droits.verdict", f["verdict"], la).upper(),
            id=f.get("id") or "?"))
        out.append("    " + lib.t(
            "droits.reg.source", la,
            source=(f.get("source")
                    or lib.t("droits.reg.source_absente", la))))
        if f.get("licence"):
            out.append("    " + lib.t(
                "droits.reg.licence", la, licence=f["licence"],
                etat=lib.t("droits.lic.reconnue" if f.get("licence_reconnue")
                           else "droits.lic.non_reconnue", la)))
        if f.get("autorisation"):
            out.append("    " + lib.t("droits.reg.autorisation", la,
                                      etat=lib.valeur("droits.autorisation",
                                                      f["autorisation"], la)))
        if f.get("resolution"):
            out.append("    " + lib.t("droits.reg.resolution", la,
                                      detail=f["resolution"]["detail"]))
        for c in f.get("conditions") or []:
            out.append("    " + lib.t("droits.reg.condition", la, condition=c))
        out.append("    " + lib.t("droits.reg.credit", la,
                                  credit=f["attribution"]["texte"]))
        if f["attribution"]["manques"]:
            out.append("    " + lib.t(
                "droits.reg.manques", la,
                elements=", ".join(lib.valeur("droits.element", m, la)
                                   for m in f["attribution"]["manques"])))
        if f.get("alternative"):
            out.append("    " + lib.t(
                "droits.reg.alternative", la, voie=f["alternative"]["voie"],
                mention=f["alternative"]["mention"],
                types=", ".join(f["alternative"]["types_figures"])))
    out.append("")
    out.append(lib.t("droits.reg.erreurs" if rapport["erreurs"]
                     else "droits.reg.erreurs_aucune", la))
    out += ["  - %s" % e for e in rapport["erreurs"]]
    out.append(lib.t("droits.reg.avertissements" if rapport["avertissements"]
                     else "droits.reg.avertissements_aucun", la))
    out += ["  - %s" % a for a in rapport["avertissements"]]
    out.append("")
    out.append(lib.t("droits.lic.limite", la,
                     limite=rapport.get("limite")
                     or lib.t("droits.limite", la)))
    return "\n".join(out)


def _sans_prive(objet):
    """Retire les cles de travail prefixees d'un tiret bas avant la sortie
    JSON, qui ne doit exposer que le contrat public."""
    if isinstance(objet, dict):
        return {k: _sans_prive(v) for k, v in objet.items()
                if not str(k).startswith("_")}
    if isinstance(objet, list):
        return [_sans_prive(x) for x in objet]
    return objet


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
        description="Droits de réutilisation d'une figure tierce : licence "
                    "déclarée, verdict fermé, ligne d'attribution, registre "
                    "des figures empruntées. Consultatif par défaut.",
        epilog=LIMITE)
    sp = p.add_subparsers(dest="action", required=True)

    pl = sp.add_parser("licence", help="résoudre la licence d'une source par son DOI")
    pl.add_argument("--doi", required=True)
    pl.add_argument("--reseau", action="store_true",
                    help="interroger Crossref et OpenAlex (désactivé par défaut)")
    pl.add_argument("--openalex-cle",
                    help="clé API OpenAlex (défaut : variable OPENALEX_API_KEY)")
    pl.add_argument("--format", choices=["text", "json"], default="text")
    pl.add_argument("--strict", action="store_true",
                    help="code de sortie 1 si la reproduction n'est pas acquise")

    pr = sp.add_parser("registre", help="valider un registre de figures empruntées")
    pr.add_argument("fichier")
    pr.add_argument("--reseau", action="store_true")
    pr.add_argument("--openalex-cle")
    pr.add_argument("--format", choices=["text", "json"], default="text")
    pr.add_argument("--strict", action="store_true",
                    help="code de sortie 1 si le registre porte une erreur ou "
                         "si une figure n'est pas libre de reproduction")

    pc = sp.add_parser("credits", help="émettre la section de crédits du document")
    pc.add_argument("fichier")
    pc.add_argument("--sortie", choices=["texte", "html", "latex"], default="texte")

    for sous in (pl, pr, pc):
        sous.add_argument("--langue-affichage", choices=["fr", "en"],
                          default=None,
                          help="langue des libellés du rapport et de la ligne "
                               "de crédit (défaut fr : un registre JSON ne "
                               "porte pas de pragme de langue). La sortie "
                               "JSON reste française quoi qu'il arrive")
    return _executer(p.parse_args(argv))


def _executer(a):
    """Execute l'action demandee et rend le code de sortie."""
    lib = _lib()
    la = lib.resoudre_affichage(getattr(a, "langue_affichage", None))
    cle = getattr(a, "openalex_cle", None) or os.environ.get("OPENALEX_API_KEY")
    if a.action == "licence":
        if a.format == "json":
            # Le JSON ne se traduit pas : les evals et le jeu d'or le lisent.
            res = resoudre_doi(a.doi, a.reseau, api_key_openalex=cle)
            print(json.dumps(_sans_prive(res), ensure_ascii=False, indent=2))
        else:
            res = resoudre_doi(a.doi, a.reseau, api_key_openalex=cle,
                               langue_affichage=la)
            print(rapport_licence_texte(res, la))
        if a.strict and res["verdict"] in ("autorisation requise",
                                           "licence inconnue"):
            return 1
        return 0
    try:
        registre = charger_registre(a.fichier)
    except (OSError, ValueError) as e:
        print(lib.t("droits.err_registre", la, erreur=e), file=sys.stderr)
        return 2
    if a.action == "credits":
        valider_registre(registre, la)
        print(section_credits(registre, a.sortie, la))
        return 0
    if a.format == "json":
        # Le JSON ne se traduit pas : les evals et le jeu d'or le lisent.
        rapport = analyser(registre, a.reseau, api_key_openalex=cle)
        print(json.dumps(_sans_prive(rapport), ensure_ascii=False, indent=2))
    else:
        rapport = analyser(registre, a.reseau, api_key_openalex=cle,
                           langue_affichage=la)
        print(rapport_texte(rapport, la))
    if a.strict and rapport["verdict"] != "credits complets":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
