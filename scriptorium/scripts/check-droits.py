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

Usage :
    python3 check-droits.py licence --doi 10.xxxx/yyyy [--reseau] [--format text|json] [--strict]
    python3 check-droits.py registre REGISTRE.json [--reseau] [--format text|json] [--strict]
    python3 check-droits.py credits REGISTRE.json [--sortie texte|html|latex]

Module importable : normaliser_licence, classer, resoudre_doi,
ligne_attribution, alternative_redessin, valider_registre, section_credits,
analyser, rapport_texte.
"""
import argparse
import importlib.util
import json
import os
import sys

INDEX_TIMEOUT = 8

VERDICTS = ("reutilisable avec attribution", "reutilisable sous conditions",
            "autorisation requise", "licence inconnue")
RANG_VERDICT = {v: i for i, v in enumerate(VERDICTS)}

VERDICTS_REGISTRE = ("registre invalide", "autorisations a obtenir",
                     "licences a etablir", "credits complets")

ETATS_AUTORISATION = ("non demandee", "demandee", "obtenue", "refusee")

TYPES_FIGURES_DONNEES = ("courbe", "nuage", "histogramme", "boite", "flux",
                         "prisma")

LIMITE = ("Ce rapport dit ce que la licence déclare, il ne prononce pas la "
          "légalité d'un usage. Le contrat signé avec une revue, la politique "
          "d'un employeur ou le droit applicable peuvent en décider autrement.")

# Familles de licence, table locale sans reseau. Chaque entree dit ce que la
# licence declare permettre, jamais ce que le droit autorise dans un cas
# donne. Un ND ferme toute adaptation, donc tout recadrage ; un SA impose sa
# licence au document derive ; un NC ferme l'usage commercial.
FAMILLES = {
    "cc0": {
        "nom": "CC0", "commercial": True, "adaptation": True,
        "partage_identique": False, "attribution_exigee": False,
        "verdict": "reutilisable avec attribution",
        "conditions": ["Attribution non exigée par la licence, conservée par "
                       "honnêteté de sourçage."]},
    "domaine-public": {
        "nom": "Domaine public", "commercial": True, "adaptation": True,
        "partage_identique": False, "attribution_exigee": False,
        "verdict": "reutilisable avec attribution",
        "conditions": ["Attribution non exigée par la licence, conservée par "
                       "honnêteté de sourçage."]},
    "cc-by": {
        "nom": "CC BY", "commercial": True, "adaptation": True,
        "partage_identique": False, "attribution_exigee": True,
        "verdict": "reutilisable avec attribution",
        "conditions": ["Attribution complète : titre, auteur, source, licence.",
                       "Mention des modifications si la figure est retouchée."]},
    "cc-by-sa": {
        "nom": "CC BY-SA", "commercial": True, "adaptation": True,
        "partage_identique": True, "attribution_exigee": True,
        "verdict": "reutilisable sous conditions",
        "conditions": ["Le document dérivé se diffuse sous la même licence.",
                       "Vérifier que la destination accepte cette contrainte."]},
    "cc-by-nc": {
        "nom": "CC BY-NC", "commercial": False, "adaptation": True,
        "partage_identique": False, "attribution_exigee": True,
        "verdict": "reutilisable sous conditions",
        "conditions": ["Usage commercial fermé (livre vendu, rapport facturé, "
                       "support de formation payante)."]},
    "cc-by-nc-sa": {
        "nom": "CC BY-NC-SA", "commercial": False, "adaptation": True,
        "partage_identique": True, "attribution_exigee": True,
        "verdict": "reutilisable sous conditions",
        "conditions": ["Usage commercial fermé.",
                       "Le document dérivé se diffuse sous la même licence."]},
    "cc-by-nd": {
        "nom": "CC BY-ND", "commercial": True, "adaptation": False,
        "partage_identique": False, "attribution_exigee": True,
        "verdict": "reutilisable sous conditions",
        "conditions": ["Aucune adaptation : ni recadrage, ni retouche, ni "
                       "traduction de la légende incrustée.",
                       "La figure se reproduit entière ou pas du tout."]},
    "cc-by-nc-nd": {
        "nom": "CC BY-NC-ND", "commercial": False, "adaptation": False,
        "partage_identique": False, "attribution_exigee": True,
        "verdict": "reutilisable sous conditions",
        "conditions": ["Usage commercial fermé.",
                       "Aucune adaptation : ni recadrage, ni retouche."]},
    "tous-droits-reserves": {
        "nom": "Tous droits réservés", "commercial": False,
        "adaptation": False, "partage_identique": False,
        "attribution_exigee": True,
        "verdict": "autorisation requise",
        "conditions": ["Demande écrite à l'éditeur avant toute reproduction.",
                       "Une licence de fouille de textes ne couvre pas la "
                       "republication d'une figure."]},
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
                       origine=None):
    """Normalise une valeur de licence (slug OpenAlex ou URL Crossref) en une
    fiche fermee. Une valeur non reconnue est declaree telle quelle, avec
    reconnue=False et le verdict "licence inconnue"."""
    fiche = {"brut": valeur, "code": None, "nom": None, "version": None,
             "url": None, "reconnue": False, "commercial": None,
             "adaptation": None, "partage_identique": None,
             "attribution_exigee": None, "conditions": [],
             "verdict": "licence inconnue", "version_contenu": version_contenu,
             "date_application": date_application, "origine": origine}
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
                  "conditions": list(famille["conditions"]),
                  "verdict": famille["verdict"]})
    nom = nom_editeur or famille["nom"]
    fiche["nom"] = "%s %s" % (nom, version) if version and not nom_editeur else nom
    return fiche


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


def licence_crossref(doi, timeout=INDEX_TIMEOUT):
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
            origine="crossref"))
    titres = message.get("title") or []
    return {"consulte": True, "trouve": True, "licences": fiches,
            "titre": titres[0] if titres else None}


def licence_openalex(doi, timeout=INDEX_TIMEOUT, api_key=None):
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
            fiches.append(normaliser_licence(valeur, origine="openalex/%s" % cle))
    acces = data.get("open_access") or {}
    return {"consulte": True, "trouve": True, "licences": fiches,
            "titre": data.get("title"),
            "acces_ouvert": {"est_ouvert": acces.get("is_oa"),
                             "statut": acces.get("oa_status")} if acces else None}


def resoudre_doi(doi, reseau=False, timeout=INDEX_TIMEOUT,
                 api_key_openalex=None):
    """Resout la licence declaree d'une source par son DOI.

    Sans --reseau, aucun index n'est consulte et le verdict reste "licence
    inconnue" avec son motif. Avec --reseau, Crossref et OpenAlex sont
    interroges ; un index qui ne repond pas sort du calcul et le dit. Trois
    situations restent distinctes : aucun index joignable, index joignable
    sans licence declaree, licence declaree et lue. Aucune ne produit
    "autorisation requise" par defaut.
    """
    rapport = {"doi": doi, "reseau": bool(reseau), "index": {}, "licences": [],
               "verdict": "licence inconnue", "detail": "", "titre": None,
               "acces_ouvert": None, "conditions": [], "limite": LIMITE}
    if not reseau:
        rapport["detail"] = ("--reseau désactivé : aucune licence consultée. "
                             "Renseigner la licence à la main dans le registre.")
        rapport["alternative"] = alternative_redessin(rapport["verdict"])
        return rapport

    cr = licence_crossref(doi, timeout)
    oa = licence_openalex(doi, timeout, api_key_openalex)
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
        rapport["detail"] = ("licence %s déclarée par %s"
                             % (retenue["nom"], ", ".join(trouves) or "un index"))
    elif fiches:
        rapport["detail"] = ("%d licence(s) déclarée(s) mais aucune reconnue "
                             "par la table locale : lire les conditions à la "
                             "source avant de reproduire." % len(fiches))
    elif trouves:
        rapport["detail"] = ("source trouvée par %s, aucune licence déclarée : "
                             "absence d'information, ni interdiction ni "
                             "permission." % ", ".join(trouves))
    elif consultes:
        rapport["detail"] = ("DOI non trouvé par %s : la licence reste "
                             "inconnue." % ", ".join(consultes))
    else:
        rapport["detail"] = ("aucun index joignable (réseau indisponible) : "
                             "mesure omise, jamais remplacée par une valeur "
                             "supposée.")
    rapport["alternative"] = alternative_redessin(rapport["verdict"])
    return rapport


def alternative_redessin(verdict, auteur=None, type_figure=None):
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
    return {
        "voie": "redessin depuis les données publiées",
        "mention": "D'après les données de %s" % (auteur or "l'auteur de la source"),
        "types_figures": list(TYPES_FIGURES_DONNEES),
        "commande": ("python3 figures.py %s --data donnees.json --out figure.svg"
                     % (type_figure or "courbe")),
        "note": ("Relever les valeurs publiées (texte, tableau, données "
                 "supplémentaires), puis tracer avec la charte du document. "
                 "Ne pas décalquer le rendu d'origine, qui est la partie "
                 "protégée. Voir references/figures-catalogue.md."),
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


def ligne_attribution(figure, licence=None):
    """Ligne de crédit prête à coller, dans les trois formes utiles.

    Une licence Creative Commons demande le titre, l'auteur, la source et la
    licence, plus la mention des modifications quand la figure a ete recadree
    ou redessinee. Les elements absents ne sont pas inventes : ils sont listes
    dans "manques" et le gabarit porte alors une marque visible.
    """
    fiche = licence or normaliser_licence(figure.get("licence"))
    libelle = figure.get("libelle") or figure.get("id") or "Figure"
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
    marque = "[À COMPLÉTER : %s]"
    titre_a = titre or marque % "titre"
    auteur_a = auteur or marque % "auteur"
    source_a = source or marque % "source"
    licence_a = nom_licence or marque % "licence"
    modifs = figure.get("modifications")
    phrase_modif = ("Figure modifiée (%s)." % modifs if modifs
                    else "Figure reproduite sans modification.")

    source_txt = "%s (%s)" % (source_a, lien) if lien else source_a
    texte = ('%s : "%s", %s, %s, sous licence %s. %s'
             % (libelle, titre_a, auteur_a, source_txt, licence_a, phrase_modif))

    lien_h = ('<a href="%s">%s</a>' % (_echapper_html(lien),
                                       _echapper_html(source_a))
              if lien else _echapper_html(source_a))
    licence_h = ('<a href="%s">%s</a>' % (_echapper_html(fiche["url"]),
                                          _echapper_html(licence_a))
                 if fiche.get("url") else _echapper_html(licence_a))
    html = ('<p class="credit-figure">%s : &quot;%s&quot;, %s, %s, sous licence '
            '%s. %s</p>'
            % (_echapper_html(libelle), _echapper_html(titre_a),
               _echapper_html(auteur_a), lien_h, licence_h,
               _echapper_html(phrase_modif)))

    lien_l = ("\\href{%s}{%s}" % (lien, _echapper_latex(source_a)) if lien
              else _echapper_latex(source_a))
    corps_l = ("%s. %s, %s, sous licence %s. %s"
               % (_echapper_latex(titre_a), _echapper_latex(auteur_a), lien_l,
                  _echapper_latex(licence_a), _echapper_latex(phrase_modif)))
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


def valider_registre(registre):
    """Valide le registre. Retourne (erreurs, avertissements).

    Une erreur rend le registre inexploitable pour produire la section de
    credits : identifiant absent ou duplique, source absente, verdict hors
    liste fermee, verdict declare que la licence declaree contredit,
    modification declaree sous une licence qui interdit toute adaptation,
    autorisation refusee sur une figure conservee.
    """
    erreurs, avertissements = [], []
    if not isinstance(registre, dict):
        return ["Le registre n'est pas un objet JSON."], []
    figures = registre.get("figures")
    if not isinstance(figures, list) or not figures:
        return ["Clé \"figures\" absente, vide ou mal formée."], []
    vus = set()
    for i, fig in enumerate(figures, 1):
        if not isinstance(fig, dict):
            erreurs.append("Entrée %d : ce n'est pas un objet." % i)
            continue
        ident = fig.get("id")
        rang = ident or "entrée %d" % i
        if not ident:
            erreurs.append("Entrée %d : clé \"id\" absente." % i)
        elif ident in vus:
            erreurs.append("Figure %s : identifiant dupliqué." % ident)
        else:
            vus.add(ident)
        if not fig.get("source"):
            erreurs.append("Figure %s : clé \"source\" absente, la ligne de "
                           "crédit ne peut pas être écrite." % rang)
        if not fig.get("titre"):
            avertissements.append("Figure %s : titre absent, la ligne de "
                                  "crédit restera incomplète." % rang)
        if not fig.get("auteur"):
            avertissements.append("Figure %s : auteur absent, la ligne de "
                                  "crédit restera incomplète." % rang)
        if not fig.get("doi") and not fig.get("url"):
            avertissements.append("Figure %s : ni DOI ni URL, la source n'est "
                                  "pas résoluble par un lecteur." % rang)
        _valider_verdict(fig, rang, erreurs, avertissements)
    return erreurs, avertissements


def _valider_verdict(fig, rang, erreurs, avertissements):
    """Controle le verdict declare, la licence declaree et l'etat de la
    demande d'autorisation d'une entree du registre."""
    fiche = normaliser_licence(fig.get("licence"))
    declare = fig.get("verdict")
    if declare is not None and declare not in VERDICTS:
        erreurs.append("Figure %s : verdict \"%s\" hors de la liste fermée "
                       "(%s)." % (rang, declare, ", ".join(VERDICTS)))
        declare = None
    calcule = classer([fiche])
    if declare and fiche["reconnue"] and declare != calcule:
        erreurs.append("Figure %s : verdict déclaré \"%s\" incompatible avec "
                       "la licence déclarée %s, qui donne \"%s\"."
                       % (rang, declare, fiche["nom"], calcule))
    effectif = declare or calcule
    if fig.get("licence") and not fiche["reconnue"]:
        avertissements.append("Figure %s : licence \"%s\" non reconnue par la "
                              "table locale, conditions à lire à la source."
                              % (rang, fig.get("licence")))
    if fiche["reconnue"] and fiche["adaptation"] is False and fig.get("modifications"):
        erreurs.append("Figure %s : modification déclarée (%s) sous une licence "
                       "%s, qui interdit toute adaptation, donc tout recadrage."
                       % (rang, fig.get("modifications"), fiche["nom"]))

    autorisation = fig.get("autorisation")
    etat = None
    if autorisation is not None:
        if not isinstance(autorisation, dict):
            erreurs.append("Figure %s : clé \"autorisation\" mal formée." % rang)
        else:
            etat = autorisation.get("etat")
            if etat is not None and etat not in ETATS_AUTORISATION:
                erreurs.append("Figure %s : état d'autorisation \"%s\" hors de "
                               "la liste fermée (%s)."
                               % (rang, etat, ", ".join(ETATS_AUTORISATION)))
                etat = None
    if etat == "refusee":
        erreurs.append("Figure %s : autorisation refusée, la figure ne peut "
                       "pas être reproduite. La retirer ou la redessiner "
                       "depuis les données." % rang)
    elif effectif == "autorisation requise" and etat != "obtenue":
        avertissements.append("Figure %s : autorisation requise, état \"%s\". "
                              "Obtenir l'accord écrit de l'éditeur avant "
                              "diffusion." % (rang, etat or "non renseigné"))
    elif effectif == "licence inconnue":
        avertissements.append("Figure %s : licence inconnue. Une absence "
                              "d'information n'est pas une permission : "
                              "établir la licence ou redessiner depuis les "
                              "données." % rang)
    fig["_fiche"] = fiche
    fig["_verdict_effectif"] = effectif
    fig["_etat_autorisation"] = etat


def section_credits(registre, sortie="texte"):
    """Section de crédits des figures empruntées, prête à coller.

    Un document de quarante pages qui emprunte huit figures porte la liste de
    ses crédits, comme il porte sa bibliographie. Une figure dont la
    reproduction n'est pas acquise reste dans la liste, avec son état : la
    section sert aussi de tableau de bord avant diffusion.
    """
    figures = (registre.get("figures") or []) if isinstance(registre, dict) else []
    lignes = []
    for fig in figures:
        if not isinstance(fig, dict):
            continue
        fiche = fig.get("_fiche") or normaliser_licence(fig.get("licence"))
        att = ligne_attribution(fig, fiche)
        lignes.append(att["html"] if sortie == "html"
                      else att["latex_credit"] if sortie == "latex"
                      else att["texte"])
    if sortie == "html":
        return ("<section class=\"credits-figures\">\n<h2>Crédits des figures"
                "</h2>\n%s\n</section>" % "\n".join(lignes))
    if sortie == "latex":
        return ("\\section*{Crédits des figures}\n\\begin{itemize}\n%s\n"
                "\\end{itemize}" % "\n".join("\\item %s" % l for l in lignes))
    return "## Crédits des figures\n\n%s" % "\n\n".join(lignes)


def analyser(source, reseau=False, timeout=INDEX_TIMEOUT,
             api_key_openalex=None):
    """Valide un registre de figures empruntées et rend le rapport complet.

    Avec --reseau, une figure qui porte un DOI sans licence déclarée voit sa
    licence résolue auprès des index, puis validée comme les autres. Sans
    réseau, rien n'est supposé : la licence absente reste inconnue.
    """
    registre = charger_registre(source) if isinstance(source, str) else source
    rapport = {"fichier": registre.get("_chemin") if isinstance(registre, dict) else None,
               "reseau": bool(reseau), "figures": [], "erreurs": [],
               "avertissements": [], "verdict": "registre invalide",
               "limite": LIMITE}
    figures = (registre.get("figures") or []) if isinstance(registre, dict) else []
    if reseau:
        for fig in figures:
            if isinstance(fig, dict) and fig.get("doi") and not fig.get("licence"):
                res = resoudre_doi(fig["doi"], True, timeout, api_key_openalex)
                fig["_resolution"] = {"verdict": res["verdict"],
                                      "detail": res["detail"]}
                retenue = res.get("licence_retenue")
                if retenue:
                    fig["licence"] = retenue["brut"]
    erreurs, avertissements = valider_registre(registre)
    rapport["erreurs"] = erreurs
    rapport["avertissements"] = avertissements
    return _fermer_rapport(rapport, figures, erreurs)


def _fermer_rapport(rapport, figures, erreurs):
    """Assemble la fiche de chaque figure et ferme le verdict du registre sur
    quatre valeurs. Une erreur de validation prime : un registre qu'on ne
    peut pas lire ne rend pas un verdict de droits."""
    a_obtenir = a_etablir = False
    for fig in figures:
        if not isinstance(fig, dict):
            continue
        fiche = fig.get("_fiche") or normaliser_licence(fig.get("licence"))
        verdict = fig.get("_verdict_effectif") or classer([fiche])
        etat = fig.get("_etat_autorisation")
        if verdict == "autorisation requise" and etat != "obtenue":
            a_obtenir = True
        if verdict == "licence inconnue":
            a_etablir = True
        rapport["figures"].append({
            "id": fig.get("id"), "libelle": fig.get("libelle"),
            "source": fig.get("source"), "doi": fig.get("doi"),
            "licence": fiche.get("nom") or fig.get("licence"),
            "licence_reconnue": fiche.get("reconnue"),
            "verdict": verdict, "conditions": fiche.get("conditions") or [],
            "autorisation": etat,
            "modifications": fig.get("modifications"),
            "resolution": fig.get("_resolution"),
            "attribution": ligne_attribution(fig, fiche),
            "alternative": alternative_redessin(verdict, fig.get("auteur")),
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


def rapport_licence_texte(res):
    """Rendu texte de la resolution de licence d'un DOI."""
    out = ["Droits de réutilisation : %s" % res["doi"]]
    out.append("  Verdict : %s" % res["verdict"].upper())
    out.append("  Motif : %s" % res["detail"])
    if res.get("titre"):
        out.append("  Titre : %s" % res["titre"])
    if res.get("acces_ouvert"):
        ao = res["acces_ouvert"]
        out.append("  Accès ouvert : %s (statut %s)"
                   % (ao.get("est_ouvert"), ao.get("statut")))
    if res.get("index"):
        for nom, r in sorted(res["index"].items()):
            out.append("  Index %s : consulté=%s trouvé=%s licences=%d"
                       % (nom, r["consulte"], r["trouve"], r["licences"]))
    if res.get("licences"):
        out.append("Licences déclarées :")
        for f in res["licences"]:
            out.append("  [%s] %s (%s)"
                       % ("reconnue" if f["reconnue"] else "non reconnue",
                          f.get("nom") or f.get("brut"), f.get("origine")))
    if res.get("conditions"):
        out.append("Conditions :")
        out += ["  - %s" % c for c in res["conditions"]]
    if res.get("alternative"):
        alt = res["alternative"]
        out.append("Alternative sans emprunt : %s" % alt["voie"])
        out.append("  Mention : %s" % alt["mention"])
        out.append("  Types de figures de données : %s"
                   % ", ".join(alt["types_figures"]))
        out.append("  %s" % alt["commande"])
    out.append("Limite : %s" % res.get("limite", LIMITE))
    return "\n".join(out)


def rapport_texte(rapport):
    """Rendu texte du rapport de registre. Voir analyser() pour la structure."""
    out = ["Registre des figures empruntées : %s"
           % (rapport.get("fichier") or "(en mémoire)")]
    out.append("  Verdict : %s" % rapport["verdict"].upper())
    out.append("  Figures : %d" % len(rapport["figures"]))
    for f in rapport["figures"]:
        out.append("")
        out.append("  [%s] %s" % (f["verdict"].upper(), f.get("id") or "?"))
        out.append("    Source : %s" % (f.get("source") or "absente"))
        if f.get("licence"):
            out.append("    Licence : %s (%s)"
                       % (f["licence"],
                          "reconnue" if f.get("licence_reconnue") else "non reconnue"))
        if f.get("autorisation"):
            out.append("    Autorisation : %s" % f["autorisation"])
        if f.get("resolution"):
            out.append("    Résolution réseau : %s" % f["resolution"]["detail"])
        for c in f.get("conditions") or []:
            out.append("    Condition : %s" % c)
        out.append("    Crédit : %s" % f["attribution"]["texte"])
        if f["attribution"]["manques"]:
            out.append("    Éléments manquants : %s"
                       % ", ".join(f["attribution"]["manques"]))
        if f.get("alternative"):
            out.append("    Alternative : %s, mention \"%s\", figures %s"
                       % (f["alternative"]["voie"], f["alternative"]["mention"],
                          ", ".join(f["alternative"]["types_figures"])))
    out.append("")
    out.append("Erreurs :" if rapport["erreurs"] else "Erreurs : aucune")
    out += ["  - %s" % e for e in rapport["erreurs"]]
    out.append("Avertissements :" if rapport["avertissements"]
               else "Avertissements : aucun")
    out += ["  - %s" % a for a in rapport["avertissements"]]
    out.append("")
    out.append("Limite : %s" % rapport.get("limite", LIMITE))
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
    return _executer(p.parse_args(argv))


def _executer(a):
    """Execute l'action demandee et rend le code de sortie."""
    cle = getattr(a, "openalex_cle", None) or os.environ.get("OPENALEX_API_KEY")
    if a.action == "licence":
        res = resoudre_doi(a.doi, a.reseau, api_key_openalex=cle)
        if a.format == "json":
            print(json.dumps(_sans_prive(res), ensure_ascii=False, indent=2))
        else:
            print(rapport_licence_texte(res))
        if a.strict and res["verdict"] in ("autorisation requise",
                                           "licence inconnue"):
            return 1
        return 0
    try:
        registre = charger_registre(a.fichier)
    except (OSError, ValueError) as e:
        print("Erreur de lecture du registre : %s" % e, file=sys.stderr)
        return 2
    if a.action == "credits":
        valider_registre(registre)
        print(section_credits(registre, a.sortie))
        return 0
    rapport = analyser(registre, a.reseau, api_key_openalex=cle)
    if a.format == "json":
        print(json.dumps(_sans_prive(rapport), ensure_ascii=False, indent=2))
    else:
        print(rapport_texte(rapport))
    if a.strict and rapport["verdict"] != "credits complets":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
