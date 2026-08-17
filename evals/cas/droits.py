# -*- coding: utf-8 -*-
"""Cas d'eval des droits de reutilisation d'une figure tierce (check-droits.py).

Couvre la normalisation des familles de licence, le verdict ferme, la
distinction entre "licence inconnue" et "autorisation requise", la ligne
d'attribution dans ses trois formes, l'alternative du redessin depuis les
donnees et la validation du registre des figures empruntees.

Tous les cas tournent hors ligne : les reponses de Crossref et d'OpenAlex
sont simulees en remplacant _requete_json du module verify-sources charge par
check-droits.py, comme lecture-pdf.py simule les backends PDF. Un cas d'eval
qui dependrait du reseau ne mesurerait plus rien sur une machine hors ligne.
"""
import copy as _copy

drt = charger("check-droits.py", "check_droits")


def _avec_index(reponses):
    """Rend un executeur qui repond aux URL d'index par une table locale.

    reponses : fragment d'URL -> (code_http_ou_None, donnees_ou_None). Un
    fragment absent de la table rend (None, None), soit un index injoignable.
    """
    def faux(url, timeout=None):
        for fragment, valeur in reponses.items():
            if fragment in url:
                return valeur
        return (None, None)

    def executer(appel):
        sauve = drt._VSRC._requete_json
        drt._VSRC._requete_json = faux
        try:
            return appel()
        finally:
            drt._VSRC._requete_json = sauve
    return executer


def _crossref(licences):
    return (200, {"message": {"title": ["Un article"], "license": list(licences)}})


def _openalex(licence):
    loc = {"license": licence} if licence else {}
    return (200, {"title": "Un article",
                  "open_access": {"is_oa": bool(licence), "oa_status": "gold"},
                  "best_oa_location": loc, "primary_location": loc})


CC_BY_URL = "http://creativecommons.org/licenses/by/4.0/"
ELSEVIER_TDM = "https://www.elsevier.com/tdm/userlicense/1.0/"

# --- Cas 1-4 : chaque famille de licence tombe sur son verdict ---

_by = drt.normaliser_licence(CC_BY_URL)
_cc0 = drt.normaliser_licence("https://creativecommons.org/publicdomain/zero/1.0/")
_pd = drt.normaliser_licence("public-domain")
verifier("droits : famille ouverte (CC BY, CC0, domaine public) reutilisable "
         "avec attribution, version lue dans l'URL",
         all(drt.classer([f]) == "reutilisable avec attribution"
             for f in (_by, _cc0, _pd))
         and _by["nom"] == "CC BY 4.0" and _cc0["attribution_exigee"] is False,
         "%s %s" % (_by["nom"], [drt.classer([f]) for f in (_by, _cc0, _pd)]))

_sa = drt.normaliser_licence("cc-by-sa")
_nc = drt.normaliser_licence("https://creativecommons.org/licenses/by-nc/4.0/")
_nd = drt.normaliser_licence("https://openalex.org/licenses/cc-by-nd")
verifier("droits : SA, NC et ND sont reutilisables sous conditions, chacune "
         "avec la contrainte qui lui est propre",
         all(drt.classer([f]) == "reutilisable sous conditions"
             for f in (_sa, _nc, _nd))
         and _sa["partage_identique"] is True and _nc["commercial"] is False
         and _nd["adaptation"] is False,
         "%s" % [drt.classer([f]) for f in (_sa, _nc, _nd)])

_els = drt.normaliser_licence(ELSEVIER_TDM)
verifier("droits : une licence de fouille de textes n'est pas une permission "
         "de republication",
         _els["code"] == "tous-droits-reserves"
         and drt.classer([_els]) == "autorisation requise", str(_els["code"]))

_inconnue = drt.normaliser_licence("https://exemple.test/conditions-maison")
verifier("droits : une licence non reconnue reste inconnue, jamais interdite",
         _inconnue["reconnue"] is False
         and drt.classer([_inconnue]) == "licence inconnue", str(_inconnue))

# --- Cas 5-9 : resolution par DOI, index simules hors ligne ---

_r_ouvert = _avec_index({
    "api.crossref.org": _crossref([
        {"URL": CC_BY_URL, "content-version": "unspecified",
         "delay-in-days": 0, "start": {"date-time": "2007-03-21T00:00:00Z"}}]),
    "api.openalex.org": _openalex("cc-by")})(
        lambda: drt.resoudre_doi("10.1371/journal.pone.0000308", reseau=True))
verifier("droits : un article sous CC BY est reutilisable, les deux index "
         "comptes consultes",
         _r_ouvert["verdict"] == "reutilisable avec attribution"
         and _r_ouvert["index"]["crossref"]["consulte"]
         and _r_ouvert["index"]["openalex"]["trouve"], str(_r_ouvert["verdict"]))

_r_abonnement = _avec_index({
    "api.crossref.org": _crossref([
        {"URL": ELSEVIER_TDM, "content-version": "tdm", "delay-in-days": 0,
         "start": {"date-time": "2011-03-01T00:00:00Z"}},
        {"URL": "https://www.elsevier.com/legal/tdmrep-license",
         "content-version": "tdm", "delay-in-days": 0, "start": {}}]),
    "api.openalex.org": _openalex(None)})(
        lambda: drt.resoudre_doi("10.1016/j.cell.2011.02.013", reseau=True))
verifier("droits : un tableau license rempli de conditions d'editeur donne "
         "autorisation requise",
         _r_abonnement["verdict"] == "autorisation requise",
         str(_r_abonnement["verdict"]))

_r_sans_licence = _avec_index({
    "api.crossref.org": _crossref([]),
    "api.openalex.org": _openalex(None)})(
        lambda: drt.resoudre_doi("10.9999/sans.licence", reseau=True))
verifier("droits : source trouvee sans licence declaree reste licence "
         "inconnue, jamais autorisation requise",
         _r_sans_licence["verdict"] == "licence inconnue"
         and "absence d'information" in _r_sans_licence["detail"],
         str(_r_sans_licence["detail"]))

_r_muet = _avec_index({})(
    lambda: drt.resoudre_doi("10.9999/injoignable", reseau=True))
verifier("droits : aucun index joignable donne une mesure omise et declaree, "
         "pas une interdiction",
         _r_muet["verdict"] == "licence inconnue"
         and "omise" in _r_muet["detail"]
         and not _r_muet["index"]["crossref"]["consulte"], str(_r_muet["detail"]))

_r_hors_reseau = drt.resoudre_doi("10.1371/journal.pone.0000308")
verifier("droits : sans --reseau, aucun index n'est consulte et rien n'est "
         "suppose",
         _r_hors_reseau["verdict"] == "licence inconnue"
         and _r_hors_reseau["index"] == {}, str(_r_hors_reseau["detail"]))

# --- Cas 10-12 : ligne d'attribution et alternative du redessin ---

FIGURE = {"id": "fig-3", "libelle": "Figure 3",
          "titre": "Courbe de charge du reseau",
          "auteur": "Nguyen, T. et Roe, D.", "source": "Energy Policy",
          "doi": "10.1016/j.enpol.2023.113600", "licence": CC_BY_URL,
          "modifications": "recadree, legende retraduite"}

_att = drt.ligne_attribution(FIGURE)
verifier("droits : la ligne d'attribution porte titre, auteur, source, "
         "licence, DOI et modifications, dans les trois formes",
         all(x in _att["texte"] for x in (
             "Courbe de charge du reseau", "Nguyen, T. et Roe, D.",
             "Energy Policy", "CC BY 4.0",
             "https://doi.org/10.1016/j.enpol.2023.113600", "Figure modifiée"))
         and not _att["manques"]
         and "<a href=\"https://doi.org/10.1016/j.enpol.2023.113600\">" in _att["html"]
         and _att["latex"].startswith("\\caption[")
         and "\\href{" in _att["latex"], _att["texte"])

_att_creux = drt.ligne_attribution({"id": "fig-9", "source": "Revue X"})
verifier("droits : un element absent est declare manquant, jamais invente",
         sorted(_att_creux["manques"]) == ["auteur", "licence", "titre"]
         and "À COMPLÉTER" in _att_creux["texte"], str(_att_creux["manques"]))

verifier("droits : le redessin depuis les donnees est propose quand la "
         "reproduction n'est pas acquise, et jamais quand elle l'est",
         drt.alternative_redessin("autorisation requise", "Nguyen")["types_figures"]
         == ["courbe", "nuage", "histogramme", "boite", "flux", "prisma"]
         and drt.alternative_redessin("licence inconnue", "Nguyen")["mention"]
         == "D'après les données de Nguyen"
         and drt.alternative_redessin("reutilisable avec attribution") is None
         and drt.alternative_redessin("reutilisable sous conditions") is None)

# --- Cas 13-18 : registre des figures empruntees et section de credits ---


def _registre(*figures):
    return {"document": "Memoire de stage",
            "figures": [_copy.deepcopy(f) for f in figures]}


FIG_LIBRE = dict(FIGURE, modifications=None)
FIG_REVUE = {"id": "fig-5", "libelle": "Figure 5", "titre": "Schema du banc",
             "auteur": "Poe, A.", "source": "Journal of Testing",
             "doi": "10.1016/j.test.2020.01", "licence": ELSEVIER_TDM,
             "autorisation": {"etat": "obtenue", "date": "2026-08-01",
                              "reference": "RightsLink 5012345"}}

_rap_ok = drt.analyser(_registre(FIG_LIBRE, FIG_REVUE))
verifier("droits : un registre complet, autorisation obtenue comprise, rend "
         "credits complets sans erreur",
         _rap_ok["verdict"] == "credits complets" and not _rap_ok["erreurs"],
         "%s %s" % (_rap_ok["verdict"], _rap_ok["erreurs"]))

_rap_attente = drt.analyser(_registre(
    dict(FIG_REVUE, autorisation={"etat": "demandee"})))
_rap_muet = drt.analyser(_registre({"id": "fig-1", "titre": "T",
                                    "auteur": "A", "source": "S"}))
verifier("droits : autorisation en attente et licence absente donnent deux "
         "verdicts de registre distincts",
         _rap_attente["verdict"] == "autorisations a obtenir"
         and _rap_muet["verdict"] == "licences a etablir"
         and _rap_muet["figures"][0]["alternative"] is not None,
         "%s / %s" % (_rap_attente["verdict"], _rap_muet["verdict"]))

_erreurs = {
    "identifiant duplique": drt.valider_registre(
        _registre(FIG_LIBRE, FIG_LIBRE))[0],
    "source absente": drt.valider_registre(
        _registre({"id": "fig-2", "licence": CC_BY_URL}))[0],
    "verdict hors liste": drt.valider_registre(
        _registre(dict(FIG_LIBRE, verdict="reutilisable a volonte")))[0],
    "verdict contredit par la licence": drt.valider_registre(
        _registre(dict(FIG_LIBRE, verdict="autorisation requise")))[0],
    "recadrage sous licence ND": drt.valider_registre(
        _registre(dict(FIG_LIBRE, licence="cc-by-nd",
                       modifications="recadree")))[0],
    "registre sans figure": drt.valider_registre({"figures": []})[0],
}
_sans_erreur = sorted(k for k, v in _erreurs.items() if not v)
verifier("droits : les six formes de registre invalide sont refusees",
         not _sans_erreur, "acceptees a tort=%s" % _sans_erreur)
verifier("droits : chaque refus nomme sa cause plutot qu'un compte anonyme",
         "dupliqué" in " ".join(_erreurs["identifiant duplique"])
         and "incompatible" in " ".join(_erreurs["verdict contredit par la licence"])
         and "interdit toute adaptation" in " ".join(_erreurs["recadrage sous licence ND"]),
         str(_erreurs["recadrage sous licence ND"]))

_rap_refus = drt.analyser(_registre(
    dict(FIG_REVUE, autorisation={"etat": "refusee"})))
verifier("droits : une autorisation refusee invalide le registre et renvoie "
         "vers le redessin",
         _rap_refus["verdict"] == "registre invalide"
         and any("refusée" in e for e in _rap_refus["erreurs"]),
         str(_rap_refus["erreurs"]))

_reg_credits = _registre(FIG_LIBRE, FIG_REVUE)
drt.valider_registre(_reg_credits)
verifier("droits : la section de credits liste chaque figure empruntee, en "
         "texte, en HTML et en LaTeX",
         drt.section_credits(_reg_credits).startswith("## Crédits des figures")
         and "Figure 3" in drt.section_credits(_reg_credits)
         and "<section class=\"credits-figures\">"
         in drt.section_credits(_reg_credits, "html")
         and "\\section*{Crédits des figures}"
         in drt.section_credits(_reg_credits, "latex"))

verifier("droits : le rapport porte lui-meme sa limite, comme check-fuites "
         "dit qu'il inspecte sans nettoyer",
         "ne prononce pas la légalité" in drt.rapport_texte(_rap_ok)
         and "ne prononce pas la légalité" in drt.rapport_licence_texte(_r_muet))
