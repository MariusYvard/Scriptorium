# -*- coding: utf-8 -*-
"""Cas d'eval de la recuperation et de l'identification d'une figure tierce
(emprunts.py).

Couvre le reperage des legendes francaises et anglaises, l'appariement image
legende page et sa confiance graduee, la degradation sans backend de texte,
les etats fermes de localisation, les trois refus de recuperation, dont
celui d'une source non ouverte, et l'entree de registre que check-droits.py
valide.

Tous les cas tournent hors ligne. Les backends d'extraction d'images et de
texte sont simules comme lecture-pdf.py simule la cascade PDF, et les
reponses d'index comme droits.py simule Crossref et OpenAlex. Un cas d'eval
qui dependrait du reseau ou de l'outillage local ne mesurerait plus rien.
"""
import importlib.util
import os
import tempfile


def charger(nom_fichier, nom_module, dossier=SCRIPTS):
    spec = importlib.util.spec_from_file_location(
        nom_module, os.path.join(dossier, nom_fichier))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


emp = charger("emprunts.py", "emprunts")
drt = emp._DRT
genfix = charger("generer-pdf-emprunts.py", "generer_pdf_emprunts", FIXT)

# Fixture regeneree a chaque run : deterministe, sans dependance.
genfix.main(FIXT)
P_PDF = os.path.join(FIXT, "pdf-emprunts.pdf")

# Meme texte que les pages de la fixture, injecte a la place du backend.
TEXTES = ["Resultats de la campagne de mesure\n"
          "Figure 1. Courbe de charge du reseau mesuree sur douze mois",
          "Figure 2. Distribution des masses relevees au banc\n"
          "Figure 3. Detail du montage optique en configuration nominale",
          "Discussion generale sans aucune legende de figure sur cette page"]


def _img(index, page):
    return {"index": index, "fichier": "img-%03d.png" % index,
            "origine": "p%03d-%02d.png" % (page, index), "largeur": 800,
            "hauteur": 600, "octets": 4096, "flags": []}


def _manifeste(images, backend="pymupdf"):
    return {"source": "pdf-emprunts.pdf", "type": "pdf", "backend": backend,
            "count": len(images), "doublons": 0, "images": list(images),
            "skipped": [], "notes": []}


def _avec_backends(manifeste, textes):
    """Rend un executeur qui simule l'extraction d'images et de texte.

    textes a None simule l'absence totale de backend de texte, comme
    lecture-pdf.py le fait pour la cascade PDF : le resultat ne depend plus
    de ce qui est installe sur la machine.
    """
    def executer(appel):
        sauve = (emp._IMG.extract, emp._CHKP.extraire_texte_pages)
        emp._IMG.extract = lambda s, d, m=1024: dict(manifeste)
        emp._CHKP.extraire_texte_pages = lambda c: (
            (list(textes), "simule") if textes is not None else (None, None))
        try:
            return appel()
        finally:
            emp._IMG.extract, emp._CHKP.extraire_texte_pages = sauve
    return executer


def _avec_index(reponses):
    """Rend un executeur qui repond aux URL d'index par une table locale.

    Un fragment absent de la table rend (None, None), soit un index
    injoignable. emprunts.py et check-droits.py partagent le meme objet
    verify-sources, donc une seule substitution couvre les deux.
    """
    def faux(url, timeout=None):
        for fragment, valeur in reponses.items():
            if fragment in url:
                return valeur
        return (None, None)

    def executer(appel):
        sauve = emp._VSRC._requete_json
        emp._VSRC._requete_json = faux
        try:
            return appel()
        finally:
            emp._VSRC._requete_json = sauve
    return executer


CC_BY = "https://creativecommons.org/licenses/by/4.0/"
ND = "https://creativecommons.org/licenses/by-nd/4.0/"
TDM = "https://www.elsevier.com/tdm/userlicense/1.0/"
AUTEURS = [{"author": {"display_name": "Nguyen, T."}},
           {"author": {"display_name": "Roe, D."}}]


def _crossref(url_licence):
    licences = ([{"URL": url_licence, "content-version": "vor",
                  "start": {"date-time": "2023-01-01T00:00:00Z"}}]
                if url_licence else [])
    return (200, {"message": {"title": ["Charge du reseau"],
                              "license": licences}})


def _openalex(is_oa, slug=None, pdf_url=None, revue="Energy Policy"):
    loc = None
    if is_oa:
        loc = {"license": slug, "version": "publishedVersion",
               "landing_page_url": "https://depot.example/oa/article",
               "source": {"display_name": revue}}
        if pdf_url:
            loc["pdf_url"] = pdf_url
    return (200, {"title": "Charge du reseau", "authorships": list(AUTEURS),
                  "open_access": {"is_oa": bool(is_oa),
                                  "oa_status": "gold" if is_oa else "closed"},
                  "best_oa_location": loc,
                  "primary_location": {"license": slug,
                                       "source": {"display_name": revue}}})


PDF_OUVERT = "https://depot.example/oa/article.pdf"
DOI = "10.1016/j.enpol.2023.113600"


# --- Cas 1-4 : reperage des legendes ---

_fr = emp.reperer_legendes("Figure 3. Courbe de charge du reseau\n"
                           "\nTableau 2 : Parametres du banc")
verifier("emprunts : legendes francaises reperees avec leur famille, leur "
         "numero et leur texte nettoye du separateur",
         [(l["famille"], l["numero"], l["legende"]) for l in _fr]
         == [("figure", "3", "Courbe de charge du reseau"),
             ("tableau", "2", "Parametres du banc")], str(_fr))

_en = emp.reperer_legendes(
    "Fig. 3 — Load curve of the grid\n\nTable 4 Mass distribution\n"
    "\nFigure 5: Optical setup")
verifier("emprunts : formes anglaises reconnues, Table rangee en tableau",
         [(l["famille"], l["numero"]) for l in _en]
         == [("figure", "3"), ("tableau", "4"), ("figure", "5")]
         and _en[0]["legende"] == "Load curve of the grid", str(_en))

_renvoi = emp.reperer_legendes(
    "Le montage est decrit plus haut, voir la Figure 7 dans le texte.\n"
    "\nFigure 8")
verifier("emprunts : un renvoi en cours de ligne n'est pas pris pour une "
         "legende, et un numero seul ne fait pas naitre une legende",
         [l["numero"] for l in _renvoi] == ["8"]
         and _renvoi[0]["legende"] is None, str(_renvoi))

_double = emp.reperer_legendes(
    "Figure 2 est commentee ici\n\nFigure 2. Distribution des masses "
    "relevees au banc de mesure")
verifier("emprunts : deux occurrences du meme numero fusionnent sur le texte "
         "le plus long",
         len(_double) == 1
         and _double[0]["legende"].startswith("Distribution des masses"),
         str(_double))

# --- Cas 5-8 : appariement et confiance ---

_a1, _o1 = emp.apparier([_img(1, 1)], {1: emp.reperer_legendes(
    "Figure 1. Courbe de charge")}, True, "pymupdf")
verifier("emprunts : une image et une legende sur la page donnent un "
         "appariement de confiance elevee",
         _a1[0]["niveau"] == "elevee" and _a1[0]["confiance"] == 0.9
         and _a1[0]["libelle"] == "Figure 1" and not _o1, str(_a1))

_a2, _o2 = emp.apparier([_img(1, 2), _img(2, 2)], {2: emp.reperer_legendes(
    "Figure 2. Deux\nFigure 3. Trois")}, True, "pymupdf")
verifier("emprunts : une page a deux images et deux legendes abaisse la "
         "confiance et dit que l'appariement reste a verifier",
         all(a["niveau"] == "moyenne" and a["confiance"] == 0.5 for a in _a2)
         and [a["libelle"] for a in _a2] == ["Figure 2", "Figure 3"]
         and "à vérifier" in _a2[0]["motif"], str(_a2))

_a3, _o3 = emp.apparier([_img(1, 2), _img(2, 2), _img(3, 2)],
                        {2: emp.reperer_legendes("Figure 2. Deux")},
                        True, "pymupdf")
verifier("emprunts : des comptes qui divergent donnent une confiance faible, "
         "et les images en trop restent sans legende plutot que d'en recevoir "
         "une au hasard",
         [a["niveau"] for a in _a3] == ["faible", "nulle", "nulle"]
         and _a3[1]["legende"] is None, str([a["niveau"] for a in _a3]))

_a4, _o4 = emp.apparier([_img(1, 2)], {2: emp.reperer_legendes(
    "Figure 2. Deux\nFigure 3. Trois")}, True, "pymupdf")
verifier("emprunts : une legende sans image extraite est declaree plutot "
         "qu'ignoree",
         [l["libelle"] for l in _o4] == ["Figure 3"], str(_o4))


# --- Cas 9-12 : inventaire d'un PDF, backends simules ---

_inv_ok = _avec_backends(_manifeste([_img(1, 1)]), TEXTES)(
    lambda: emp.inventorier(P_PDF, tempfile.mkdtemp(prefix="emp_")))
verifier("emprunts : un inventaire dont chaque image tombe sur sa legende "
         "rend le verdict inventaire apparie",
         _inv_ok["verdict"] == "inventaire apparie"
         and _inv_ok["appariements"][0]["legende"].startswith("Courbe de charge")
         and _inv_ok["appariements"][0]["page"] == 1,
         "%s %s" % (_inv_ok["verdict"], _inv_ok["appariements"]))

_inv_part = _avec_backends(
    _manifeste([_img(1, 1), _img(2, 2), _img(3, 2), _img(4, 3)]), TEXTES)(
        lambda: emp.inventorier(P_PDF, tempfile.mkdtemp(prefix="emp_")))
verifier("emprunts : une image sur une page sans legende suffit a faire "
         "tomber l'inventaire en partiel, avec sa note de verification",
         _inv_part["verdict"] == "inventaire partiel"
         and _inv_part["appariements"][-1]["niveau"] == "nulle"
         and any("confiance moyenne ou faible" in n
                 for n in _inv_part["notes"]),
         "%s %s" % (_inv_part["verdict"], _inv_part["notes"]))

_inv_muet = _avec_backends(_manifeste([_img(1, 1)]), None)(
    lambda: emp.inventorier(P_PDF, tempfile.mkdtemp(prefix="emp_")))
verifier("emprunts : sans backend de texte, l'inventaire rend les images "
         "sans legende et le declare, il n'en invente aucune",
         _inv_muet["verdict"] == "inventaire non apparie"
         and _inv_muet["appariements"][0]["legende"] is None
         and _inv_muet["appariements"][0]["libelle"] is None
         and any("aucune légende n'est inventée" in n
                 for n in _inv_muet["notes"]),
         "%s %s" % (_inv_muet["verdict"], _inv_muet["notes"]))

_inv_absent = emp.inventorier(os.path.join(FIXT, "inexistant_emprunts_xyz.pdf"))
verifier("emprunts : un fichier introuvable donne extraction impossible avec "
         "son motif, jamais un inventaire vide presente comme complet",
         _inv_absent["verdict"] == "extraction impossible"
         and any("introuvable" in n for n in _inv_absent["notes"]),
         str(_inv_absent["notes"]))


# --- Cas 13-15 : localisation en acces ouvert, etats fermes ---

_loc_ouvert = _avec_index({"api.openalex.org": _openalex(
    True, "cc-by", PDF_OUVERT)})(lambda: emp.localiser(DOI, reseau=True))
verifier("emprunts : une source ouverte rend l'adresse du PDF, le statut "
         "d'acces ouvert et la licence declaree",
         _loc_ouvert["etat"] == "acces ouvert confirme"
         and _loc_ouvert["url_pdf"] == PDF_OUVERT
         and _loc_ouvert["est_ouvert"] is True
         and _loc_ouvert["statut_oa"] == "gold"
         and _loc_ouvert["licence_declaree"] == "cc-by"
         and _loc_ouvert["auteur"] == "Nguyen, T. et Roe, D.",
         str(_loc_ouvert["etat"]))

_loc_ferme = _avec_index({"api.openalex.org": _openalex(False, TDM)})(
    lambda: emp.localiser(DOI, reseau=True))
_loc_sans_fichier = _avec_index({"api.openalex.org": _openalex(True, "cc-by")})(
    lambda: emp.localiser(DOI, reseau=True))
verifier("emprunts : source fermee et source ouverte sans adresse publiee "
         "sont deux etats distincts",
         _loc_ferme["etat"] == "acces non ouvert"
         and _loc_sans_fichier["etat"] == "acces ouvert sans fichier"
         and _loc_sans_fichier["url_pdf"] is None,
         "%s / %s" % (_loc_ferme["etat"], _loc_sans_fichier["etat"]))

_loc_hors = emp.localiser(DOI)
_loc_muet = _avec_index({})(lambda: emp.localiser(DOI, reseau=True))
verifier("emprunts : sans reseau et index injoignable restent inconnus pour "
         "des motifs distincts, et aucun ne vaut source fermee",
         _loc_hors["etat"] == _loc_muet["etat"] == "localisation inconnue"
         and _loc_hors["index_consulte"] is False
         and "désactivé" in _loc_hors["detail"]
         and "injoignable" in _loc_muet["detail"]
         and _loc_muet["est_ouvert"] is None,
         "%s / %s" % (_loc_hors["detail"], _loc_muet["detail"]))


# --- Cas 16-17 : refus de recuperation, chemin de premiere classe ---

_cible = os.path.join(tempfile.mkdtemp(prefix="emp_refus_"), "interdit.pdf")
_refus = emp.recuperer(_loc_ferme, _cible)
verifier("emprunts : une source non ouverte est refusee par un message qui "
         "nomme le garde-fou et renvoie vers la demande a l'editeur, sans "
         "qu'aucun fichier soit ecrit",
         _refus["etat"] == "refus source non ouverte"
         and "n'est pas déclarée en accès ouvert" in _refus["message"]
         and "ne contourne aucun contrôle d'accès" in _refus["message"]
         and "droits-figures.md" in _refus["message"]
         and _refus["fichier"] is None
         and not os.path.exists(_cible), _refus["message"][:120])

_refus_adresse = emp.recuperer(_loc_sans_fichier, _cible)
_refus_inconnu = emp.recuperer(_loc_muet, _cible)
verifier("emprunts : les trois refus ne se confondent pas, et aucun ne "
         "propose d'essayer une adresse devinee",
         _refus_adresse["etat"] == "refus adresse absente"
         and _refus_inconnu["etat"] == "refus localisation inconnue"
         and "ni une interdiction, ni une permission"
         in _refus_inconnu["message"]
         and "adresse supposée" in _refus_adresse["message"]
         and not os.path.exists(_cible),
         "%s / %s" % (_refus_adresse["etat"], _refus_inconnu["etat"]))


# --- Cas 18-20 : entree de registre et chainage vers les droits ---

_appariement = _inv_ok["appariements"][0]
_droits_by = _avec_index({"api.crossref.org": _crossref(CC_BY),
                          "api.openalex.org": _openalex(True, "cc-by",
                                                        PDF_OUVERT)})(
    lambda: drt.resoudre_doi(DOI, reseau=True))
_entree = emp.entree_registre(DOI, _loc_ouvert, _droits_by, _appariement,
                              fichier="emprunts/images/img-001.png")
_err, _av = drt.valider_registre({"figures": [dict(_entree)]})
verifier("emprunts : l'entree produite porte source, DOI, numero de figure, "
         "legende d'origine, licence, verdict et fichier, et le validateur "
         "de check-droits.py l'accepte sans erreur ni avertissement",
         not _err and not _av and _entree["id"] == "fig-1"
         and _entree["libelle"] == "Figure 1"
         and _entree["legende_origine"].startswith("Courbe de charge")
         and _entree["source"] == "Energy Policy"
         and _entree["verdict"] == "reutilisable avec attribution"
         and _entree["fichier"].endswith("img-001.png"),
         "%s %s %s" % (_err, _av, _entree))

_droits_nd = _avec_index({"api.crossref.org": _crossref(ND),
                          "api.openalex.org": _openalex(True, "cc-by-nd",
                                                        PDF_OUVERT)})(
    lambda: drt.resoudre_doi(DOI, reseau=True))
_entree_nd = emp.entree_registre(DOI, _loc_ouvert, _droits_nd, _appariement,
                                 modifications="recadrée")
_err_nd, _ = drt.valider_registre({"figures": [dict(_entree_nd)]})
verifier("emprunts : un recadrage declare sous une licence sans droit "
         "d'adaptation est refuse par le validateur, pas dissimule",
         any("interdit toute adaptation" in e for e in _err_nd), str(_err_nd))

_chaine = _avec_index({"api.crossref.org": _crossref(TDM),
                       "api.openalex.org": _openalex(False, TDM)})(
    lambda: emp.chainer(DOI, os.path.join(tempfile.mkdtemp(prefix="emp_"), "t"),
                        reseau=True))
_voies = _chaine.get("voies") or {}
verifier("emprunts : sur une source fermee la chaine s'arrete au refus, le "
         "dit dans son verdict et propose les deux voies, demande a "
         "l'editeur et redessin depuis les donnees publiees",
         _chaine["verdict"] == "source non ouverte"
         and _chaine["recuperation"]["etat"] == "refus source non ouverte"
         and "éditeur" in _voies["autorisation"]["voie"]
         and _voies["redessin"]["types_figures"]
         == ["courbe", "nuage", "histogramme", "boite", "flux", "prisma"]
         and "ne prononce pas" not in _chaine["garde_fou"],
         "%s %s" % (_chaine["verdict"], sorted(_voies)))
