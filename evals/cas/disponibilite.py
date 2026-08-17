# -*- coding: utf-8 -*-
"""Cas d'eval du controle de disponibilite des donnees et du code.

Couvre le reperage de la section, la detection des six regimes, la
distinction entre "section absente" et "regime non identifie", la preuve
attendue de chaque regime (identifiant perenne, date d'embargo, licence de
code, detenteur d'un jeu de tiers), la confiance graduee et le verdict ferme.

Les cas negatifs comptent autant que les autres : une declaration correcte et
complete ne doit lever aucun constat, sinon le controle apprend a l'auteur a
ignorer ses rapports.
"""
import os as _os

disp = charger("check-disponibilite.py", "check_disponibilite")


def _regles(rapport):
    return {c["regle"] for c in rapport["constats"]}


def _confiance(rapport, regle):
    for c in rapport["constats"]:
        if c["regle"] == regle:
            return c["confiance"]
    return None


def _doc(titre, corps):
    return ("# Etude\n\n## Discussion\n\nTexte de discussion.\n\n## "
            + titre + "\n\n" + corps + "\n")


def _an(titre, corps):
    return disp.analyser(_doc(titre, corps))


# --- 1-3 : structure de la declaration ---

_rien = disp.analyser("# Etude\n\n## Discussion\n\nTexte sans declaration.\n")
_vide = _an("Data availability statement", "Sans objet.")
verifier("disponibilite : section absente et section titree sans declaration "
         "sont deux etats distincts",
         _rien["verdict"] == "declaration absente"
         and _regles(_rien) == {"section-absente"}
         and _vide["verdict"] == "declaration incoherente"
         and "section-vide" in _regles(_vide),
         str((_rien["verdict"], sorted(_regles(_vide)))))

_titres = ["Disponibilité des données", "Data and code availability",
           "Data sharing statement", "Accès aux données"]
_vus = [t for t in _titres
        if _an(t, "Les données sont déposées dans Zenodo sous l'identifiant "
                  "10.5281/zenodo.1.")["section"]["trouvee"]]
verifier("disponibilite : les intitules courants sont reconnus en francais "
         "et en anglais", _vus == _titres, str(_vus))

_bloc = disp.analyser("# Etude\n\n## Methode\n\nGabarit :\n\n```\n"
                      "## Disponibilité des données\n\nLes données sont "
                      "déposées dans Zenodo sous 10.5281/zenodo.1.\n```\n")
verifier("disponibilite : une declaration citee dans un bloc de code n'est "
         "pas la declaration du document",
         _bloc["verdict"] == "declaration absente", str(_bloc["verdict"]))

# --- 4 : regime introuvable, distinct de la section absente ---

_flou = _an("Disponibilité des données",
            "Les auteurs ont pris soin de documenter le travail réalisé "
            "pendant cette étude et restent attentifs aux suites qui lui "
            "seront données.")
verifier("disponibilite : une section sans regime ne se confond pas avec une "
         "section absente",
         _flou["verdict"] == "regime non identifie"
         and "regime-non-identifie" in _regles(_flou), str(_flou["verdict"]))

# --- 5-8 : l'ouverture annoncee se prouve par un identifiant perenne ---

_sans_id = _an("Disponibilité des données",
               "Les données qui soutiennent les résultats de cette étude "
               "sont publiquement accessibles sur le site web de notre "
               "laboratoire, à l'adresse https://labo.example.org/donnees.")
verifier("disponibilite : ouverture annoncee sans identifiant perenne est un "
         "constat confirme, une adresse web ne fixant rien",
         _confiance(_sans_id, "ouverture-sans-identifiant") == "confirme"
         and _sans_id["verdict"] == "declaration incoherente",
         str(sorted(_regles(_sans_id))))

_acc = _an("Disponibilité des données",
           "Les séquences sont déposées dans l'European Nucleotide Archive "
           "sous le numéro d'accession PRJEB12345, en accès ouvert.")
verifier("disponibilite : un numero d'accession vaut identifiant, l'absence "
         "de DOI restant informative",
         [i["type"] for i in _acc["identifiants"]] == ["accession"]
         and _confiance(_acc, "identifiant-sans-doi") == "informatif"
         and _acc["verdict"] == "declaration conforme",
         str(_acc["identifiants"]) + str(sorted(_regles(_acc))))

_doi_faux = _an("Disponibilité des données",
                "Les données sont déposées dans Zenodo, doi: 10.52/zenodo, "
                "sous licence CC BY 4.0 et accessibles en accès ouvert.")
verifier("disponibilite : un DOI mal forme est cite et compte comme une "
         "absence d'identifiant",
         "doi-mal-forme" in _regles(_doi_faux)
         and "ouverture-sans-identifiant" in _regles(_doi_faux)
         and any(c["extrait"] == "10.52/zenodo" for c in _doi_faux["constats"]),
         str([(c["regle"], c["extrait"]) for c in _doi_faux["constats"]]))

_doi_bon = _an("Disponibilité des données",
               "Les données sont déposées dans Zenodo, "
               "doi:10.5281/zenodo.1234567, en accès ouvert sous licence "
               "CC BY 4.0.")
verifier("disponibilite negatif : un DOI bien forme ne devient pas un DOI "
         "mal forme",
         "doi-mal-forme" not in _regles(_doi_bon)
         and _doi_bon["verdict"] == "declaration conforme",
         str(sorted(_regles(_doi_bon))))

# --- 9-10 : embargo ---

_emb = _an("Disponibilité des données",
           "Les données sont déposées dans Dryad et restent sous embargo "
           "pendant la durée de la procédure en cours.")
verifier("disponibilite : un embargo sans date de levee est un constat "
         "confirme, la date etant ce qui le distingue d'un refus",
         _confiance(_emb, "embargo-sans-date") == "confirme",
         str(sorted(_regles(_emb))))

_emb_ok = _an("Disponibilité des données",
              "Les données sont déposées dans Dryad sous l'identifiant "
              "10.5061/dryad.abc123 et restent sous embargo jusqu'au "
              "2027-06-30, date fixée par le dépôt de brevet en cours.")
verifier("disponibilite negatif : un embargo date ne leve aucun constat "
         "confirme ni probable",
         _emb_ok["comptes"]["confirme"] == 0
         and _emb_ok["comptes"]["probable"] == 0,
         str(sorted(_regles(_emb_ok))))

# --- 11-13 : "sur demande", la formule la moins suivie d'effet ---

_dem = _an("Disponibilité des données",
           "Les données qui soutiennent les résultats de cette étude sont "
           "disponibles sur demande.")
verifier("disponibilite : une demande sans conditions nomme ce qui manque",
         _confiance(_dem, "demande-sans-conditions") == "probable"
         and "durée" in [c["detail"] for c in _dem["constats"]
                         if c["regle"] == "demande-sans-conditions"][0],
         str(sorted(_regles(_dem))))

_dem_ok = _an("Disponibilité des données",
              "Les données sont conservées par l'établissement et "
              "communiquées par l'auteur correspondant sur demande motivée, "
              "pour toute réanalyse méthodologique, après signature d'un "
              "accord de partage, pendant cinq ans à compter de la "
              "publication.")
verifier("disponibilite negatif : une demande qui porte contact, criteres et "
         "duree ne leve aucun constat",
         _dem_ok["constats"] == []
         and _dem_ok["verdict"] == "declaration conforme",
         str(sorted(_regles(_dem_ok))))

_mixte = _an("Disponibilité des données et du code",
             "Les données sont déposées dans Zenodo sous l'identifiant "
             "10.5281/zenodo.1234567, sous licence CC BY 4.0. Les "
             "enregistrements bruts restent disponibles sur demande.")
verifier("disponibilite : a cote d'un depot identifie, la demande secondaire "
         "se degrade en douteux, la combinaison de regimes reste informative "
         "et le verdict ne se degrade pas",
         _confiance(_mixte, "demande-sans-conditions") == "douteux"
         and _confiance(_mixte, "regimes-multiples") == "informatif"
         and _mixte["verdict"] == "declaration conforme",
         str([(c["regle"], c["confiance"]) for c in _mixte["constats"]]))

# --- 14-15 : code, licence et version figee ---

_code = _an("Disponibilité du code",
            "Le code d'analyse est publiquement accessible dans le dépôt "
            "https://github.com/exemple/projet, identifiant "
            "10.5281/zenodo.42.")
verifier("disponibilite : du code sans licence est confirme, un depot de "
         "developpement sans version figee reste probable",
         _confiance(_code, "code-sans-licence") == "confirme"
         and _confiance(_code, "code-sans-version-figee") == "probable",
         str([(c["regle"], c["confiance"]) for c in _code["constats"]]))

_code_flou = _an("Disponibilité du code",
                 "Le code d'analyse est archivé dans Zenodo sous "
                 "l'identifiant 10.5281/zenodo.42, version v1.2.0, et "
                 "diffusé sous licence libre.")
verifier("disponibilite : une licence evoquee sans etre nommee reste "
         "probable, jamais confirmee",
         _confiance(_code_flou, "licence-non-nommee") == "probable"
         and "code-sans-licence" not in _regles(_code_flou),
         str(sorted(_regles(_code_flou))))

# --- 16-19 : restriction, tiers, absence de donnee nouvelle ---

_restr = _an("Disponibilité des données",
             "Les données ne peuvent pas être partagées et ne sont pas "
             "publiques. Une demande peut être adressée à l'établissement.")
_tiers = _an("Disponibilité des données",
             "Les données sont des données de tiers, utilisées sous licence "
             "pour cette étude. Les auteurs ne sont pas autorisés à les "
             "rediffuser.")
verifier("disponibilite : une restriction sans motif et des donnees de tiers "
         "sans detenteur sont deux constats probables distincts",
         _confiance(_restr, "restriction-sans-motif") == "probable"
         and _confiance(_tiers, "tiers-sans-detenteur") == "probable",
         str((sorted(_regles(_restr)), sorted(_regles(_tiers)))))

_restr_ok = _an("Disponibilité des données",
                "Les données ne peuvent pas être partagées : elles portent "
                "des données à caractère personnel couvertes par le "
                "consentement des participants. Le dictionnaire des "
                "variables est déposé dans Zenodo sous l'identifiant "
                "10.5281/zenodo.999, sous licence CC0.")
verifier("disponibilite negatif : une restriction motivee avec son jeu "
         "substitut ne leve aucun constat confirme ni probable",
         _restr_ok["comptes"]["confirme"] == 0
         and _restr_ok["comptes"]["probable"] == 0,
         str([(c["regle"], c["confiance"]) for c in _restr_ok["constats"]]))

_aucune = _an("Disponibilité des données",
              "Cette étude n'a produit aucune donnée nouvelle. Les données "
              "analysées sont celles de la cohorte publiée, accessibles sous "
              "10.1000/exemple.")
verifier("disponibilite negatif : l'absence de donnee nouvelle est un regime "
         "valide, sans constat",
         _aucune["regimes"] == ["aucune-donnee"]
         and _aucune["constats"] == []
         and _aucune["verdict"] == "declaration conforme",
         str(_aucune["regimes"]) + str(sorted(_regles(_aucune))))

_contra = _an("Disponibilité des données",
              "Cette étude n'a produit aucune donnée nouvelle. Les données "
              "mesurées sont déposées dans Zenodo sous l'identifiant "
              "10.5281/zenodo.5, sous licence CC BY.")
verifier("disponibilite : declarer l'absence de donnee et un depot dans le "
         "meme corps est une contradiction confirmee",
         _confiance(_contra, "regimes-contradictoires") == "confirme"
         and _contra["verdict"] == "declaration incoherente",
         str(sorted(_regles(_contra))))

# --- 20 : contrat de sortie et cablage de la reference ---

_ref = _os.path.join(RACINE, "scriptorium", "skills", "produire", "references",
                     "disponibilite.md")
_txt_ref = open(_ref, encoding="utf-8").read().casefold()
_texte_dem = disp.rapport_texte(_dem_ok)
verifier("disponibilite : verdicts fermes, angles morts declares, six "
         "regimes documentes dans la reference",
         all(r["verdict"] in disp.VERDICTS
             for r in (_rien, _vide, _flou, _sans_id, _emb, _dem_ok, _mixte,
                       _contra, _aucune))
         and len(_dem_ok["non_verifie"]) >= 4
         and "DECLARATION CONFORME" in _texte_dem
         and "Non vérifié ici" in _texte_dem
         and "## sources" in _txt_ref and "utm_" not in _txt_ref
         and all(disp.LIBELLE_REGIME[r].casefold() in _txt_ref
                 for r in disp.REGIMES),
         str([r for r in disp.REGIMES
              if disp.LIBELLE_REGIME[r].casefold() not in _txt_ref]))
