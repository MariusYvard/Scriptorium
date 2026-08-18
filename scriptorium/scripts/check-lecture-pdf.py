#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Preflight d'integrite de lecture PDF, a lancer avant tout ancrage de
citation dans une source PDF.

Un ancrage ("p. 12") suppose que le texte de cette page a ete reellement lu.
Ce script le verifie plutot que de le supposer : nombre de pages dont du
texte a ete extrait, taux de couverture, pages sans texte (scan sans OCR),
pages a l'encodage suspect (mojibake), fichier tronque ou malforme (verifie
en lecture binaire directe, sans backend, donc toujours disponible), et PDF
chiffre ou protege (declare, jamais contourne).

Reutilise la cascade de backends PDF de check-presentation.py (pypdf, puis
pdftotext) plutot que de la redire : voir _charger_check_presentation()
ci-dessous, meme principe que gabarit.py qui importe images.py par chemin
pour ne pas dupliquer la lecture de dimensions. Aucun backend n'est une
dependance obligatoire ; son absence degrade proprement vers le verdict
"non mesurable", jamais confondu avec "lecture non fiable" (voir
_calculer_verdict).

Verdict ferme sur quatre valeurs : lecture fiable, lecture partielle,
lecture non fiable, non mesurable.

Usage :
    python3 check-lecture-pdf.py FICHIER.pdf [--format text|json] [--strict]
                                             [--langue-affichage fr|en]

Module importable : analyser(chemin, langue_affichage=None) -> dict ;
rapport_texte(rapport, langue_affichage=None) -> str. Sans langue_affichage,
les constats sont les chaines francaises d'origine a l'octet pres : ce sont
elles que serialise --format json. Le fichier analyse est un PDF, il ne porte
pas de pragme de langue : l'affichage part donc du francais, et seule
l'option le change.
"""
import argparse
import importlib.util
import json
import os
import re
import sys

SEUIL_REMPLACEMENT = 0.02  # part de U+FFFD dans une page qui la marque suspecte
LONGUEUR_MOT_SUSPECT = 20  # longueur minimale d'un mot sans voyelle pour le signaler
TAILLE_QUEUE_EOF = 2048  # octets lus en fin de fichier pour chercher %%EOF

MOJIBAKE_RE = re.compile(r"Ã[\x82-\x9F\xA0-\xBF]")
VOYELLE_RE = re.compile(r"[aeiouyAEIOUYàâäéèêëïîôöùûüÀÂÄÉÈÊËÏÎÔÖÙÛÜ]")
MOT_LONG_RE = re.compile(r"[A-Za-zÀ-ÿ]{%d,}" % LONGUEUR_MOT_SUSPECT)

VERDICTS = ("lecture fiable", "lecture partielle", "lecture non fiable", "non mesurable")


def _charger_check_presentation():
    """Charge check-presentation.py par chemin (comme gabarit.py charge
    images.py), pour reutiliser sa cascade de backends PDF sans la redire.
    Renvoie None si le fichier est absent : degradation propre, jamais un
    plantage."""
    try:
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "check-presentation.py")
        if not os.path.isfile(chemin):
            return None
        spec = importlib.util.spec_from_file_location("check_presentation_mod", chemin)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except Exception:
        return None


# Charge une seule fois au niveau module : les evals monkeypatchent les
# fonctions de _CHKP pour simuler l'absence de backend, comme run-evals.py
# le fait deja pour check-presentation.py lui-meme (voir _evals_pdf.py).
_CHKP = _charger_check_presentation()

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


def verifier_integrite_binaire(chemin, langue_affichage=None):
    """Lecture binaire directe, sans backend : en-tete %PDF-, marqueur
    %%EOF en fin de fichier, presence d'une table xref/startxref. Marche
    toujours, meme sans aucun backend PDF installe."""
    resultat = {"entete_pdf": None, "eof_present": None, "xref_present": None,
               "chiffre_signale": None, "erreur": None}
    try:
        with open(chemin, "rb") as f:
            donnees = f.read()
    except OSError as e:
        lib = _lib()
        resultat["erreur"] = lib.t(
            "lecture.m.erreur_binaire",
            lib.resoudre_affichage(langue_affichage), erreur=e)
        return resultat
    resultat["entete_pdf"] = donnees[:1024].lstrip().startswith(b"%PDF-")
    queue = donnees[-TAILLE_QUEUE_EOF:] if len(donnees) > TAILLE_QUEUE_EOF else donnees
    resultat["eof_present"] = b"%%EOF" in queue
    resultat["xref_present"] = b"startxref" in donnees or b"xref" in donnees
    resultat["chiffre_signale"] = b"/Encrypt" in donnees
    return resultat


def _texte_suspect(texte):
    """True si le texte d'une page semble a l'encodage casse : trop de
    caracteres de remplacement U+FFFD, sequences repetees typiques d'un
    UTF-8 relu en Latin-1 (mojibake), ou un mot tres long sans une seule
    voyelle. Heuristique approximative et deterministe : elle signale un
    doute, elle ne diagnostique pas la cause exacte."""
    n = len(texte)
    if n == 0:
        return False
    caractere_remplacement = "�"  # U+FFFD, ecrit en echappement pour eviter tout probleme cp1252
    if (texte.count(caractere_remplacement) / n) > SEUIL_REMPLACEMENT:
        return True
    if len(MOJIBAKE_RE.findall(texte)) >= 3:
        return True
    for mot in MOT_LONG_RE.findall(texte):
        if not VOYELLE_RE.search(mot):
            return True
    return False


def _compacter(liste, max_n=20, langue_affichage=None):
    """Represente une liste d'entiers de facon lisible, tronquee si longue."""
    if len(liste) <= max_n:
        return ", ".join(str(i) for i in liste)
    lib = _lib()
    return (", ".join(str(i) for i in liste[:max_n])
            + lib.t("lecture.reste", lib.resoudre_affichage(langue_affichage),
                    reste=len(liste) - max_n))


def _calculer_verdict(pages_total, taux_couverture, defectueux, chkp_absent):
    """Verdict ferme sur quatre valeurs. Un defaut binaire constate (fichier
    tronque, entete absente, xref illisible) est une preuve independante du
    backend : il l'emporte toujours. Un document sans aucune page est un
    defaut constate, pas une absence de mesure. Sans backend et sans defaut
    constate, le verdict est "non mesurable", jamais "lecture non fiable" :
    l'absence d'outil n'est pas un defaut du document."""
    if defectueux:
        return "lecture non fiable"
    if pages_total == 0:
        return "lecture non fiable"
    if chkp_absent or taux_couverture is None:
        return "non mesurable"
    if taux_couverture >= 0.999:
        return "lecture fiable"
    if taux_couverture <= 0.0:
        return "lecture non fiable"
    return "lecture partielle"


def analyser(chemin, langue_affichage=None):
    """Analyse complete d'un fichier PDF avant ancrage. Retourne un rapport
    dict : fichier, pages_total, pages_texte, taux_couverture,
    pages_sans_texte, pages_ancrables, pages_non_ancrables, verdict, binaire,
    info, avertissements, problemes.

    Sans langue_affichage, les trois listes de constats portent les chaines
    francaises d'origine a l'octet pres : ce sont elles que serialise le mode
    --format json. Le verdict, lui, reste une valeur machine francaise dans
    les deux cas."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    rapport = {"fichier": os.path.basename(chemin), "pages_total": None,
              "pages_texte": None, "taux_couverture": None,
              "pages_sans_texte": [], "pages_ancrables": [], "pages_non_ancrables": [],
              "verdict": None, "binaire": {}, "info": [], "avertissements": [], "problemes": []}
    if not os.path.isfile(chemin):
        rapport["problemes"].append(lib.t("lecture.m.fichier_introuvable", la,
                                          chemin=chemin))
        rapport["verdict"] = "lecture non fiable"
        return rapport
    if not chemin.lower().endswith(".pdf"):
        rapport["avertissements"].append(lib.t("lecture.m.extension", la))

    binaire = verifier_integrite_binaire(chemin, la)
    rapport["binaire"] = binaire
    defectueux = False
    if binaire.get("erreur"):
        rapport["problemes"].append(binaire["erreur"])
        defectueux = True
    else:
        if not binaire["entete_pdf"]:
            rapport["problemes"].append(lib.t("lecture.m.entete_absent", la))
            defectueux = True
        if not binaire["eof_present"]:
            rapport["problemes"].append(lib.t("lecture.m.eof_absent", la,
                                              n=TAILLE_QUEUE_EOF))
            defectueux = True
        if not binaire["xref_present"]:
            rapport["problemes"].append(lib.t("lecture.m.xref_absent", la))
            defectueux = True
        if binaire["chiffre_signale"]:
            rapport["avertissements"].append(lib.t("lecture.m.chiffre", la))
    return _analyser_texte(chemin, rapport, defectueux, lib, la)


def _analyser_texte(chemin, rapport, defectueux, lib, la):
    """Deuxieme moitie de analyser() : mesure de la couverture de texte via
    la cascade de check-presentation.py. Separee pour rester lisible."""
    chkp = _CHKP
    if chkp is None:
        rapport["problemes"].append(lib.t("lecture.m.chkp_absent", la))
        rapport["verdict"] = _calculer_verdict(None, None, defectueux, True)
        return rapport

    n_pages, _dims, backend_pages = chkp.compter_pages_et_taille(chemin)
    rapport["pages_total"] = n_pages
    if backend_pages:
        rapport["info"].append(lib.t("lecture.m.pages_source", la, n=n_pages,
                                     backend=backend_pages))
    else:
        rapport["avertissements"].append(
            lib.t("lecture.m.pages_indeterminees", la))

    textes, backend_texte = chkp.extraire_texte_pages(chemin)
    if textes is None:
        rapport["avertissements"].append(
            lib.t("lecture.m.texte_non_extrait", la))
        rapport["verdict"] = _calculer_verdict(n_pages, None, defectueux, True)
        return rapport

    rapport["info"].append(lib.t("lecture.m.texte_extrait", la,
                                 backend=backend_texte, n=len(textes)))
    if n_pages is not None and n_pages != len(textes):
        rapport["avertissements"].append(lib.t(
            "lecture.m.divergence", la, pages=n_pages,
            backend_pages=backend_pages, textes=len(textes),
            backend_texte=backend_texte))
    if rapport["pages_total"] is None:
        rapport["pages_total"] = len(textes)

    return _classer_pages(rapport, textes, defectueux, lib, la)


def _classer_pages(rapport, textes, defectueux, lib, la):
    """Classe chaque page : sans texte (refus d'ancrage), encodage suspect
    (refus d'ancrage), ou ancrable. Calcule le taux de couverture et le
    verdict final."""
    ancrables, non_ancrables, sans_texte, cassees = [], [], [], []
    for i, txt in enumerate(textes, 1):
        vide = not txt or not txt.strip()
        if vide:
            sans_texte.append(i)
            non_ancrables.append(i)
            continue
        if _texte_suspect(txt):
            cassees.append(i)
            non_ancrables.append(i)
            continue
        ancrables.append(i)

    rapport["pages_texte"] = len(textes) - len(sans_texte)
    rapport["pages_sans_texte"] = sans_texte
    rapport["pages_ancrables"] = ancrables
    rapport["pages_non_ancrables"] = non_ancrables
    taux = round(len(ancrables) / len(textes), 3) if textes else None
    rapport["taux_couverture"] = taux

    if sans_texte:
        rapport["problemes"].append(lib.t(
            "lecture.m.pages_sans_texte", la,
            pages=_compacter(sans_texte, langue_affichage=la)))
    if cassees:
        rapport["problemes"].append(lib.t(
            "lecture.m.pages_cassees", la,
            pages=_compacter(cassees, langue_affichage=la)))
    if textes and len(sans_texte) == len(textes):
        if rapport["binaire"].get("chiffre_signale"):
            rapport["problemes"].append(
                lib.t("lecture.m.aucun_texte_chiffre", la))
        else:
            rapport["problemes"].append(lib.t("lecture.m.aucun_texte", la))

    n_pages_final = rapport["pages_total"] if rapport["pages_total"] is not None else len(textes)
    rapport["verdict"] = _calculer_verdict(n_pages_final, taux, defectueux, False)
    return rapport


def rapport_texte(rapport, langue_affichage=None):
    """Rendu texte lisible du rapport. Voir analyser() pour la structure. Les
    constats portes par rapport ont ete composes dans la langue d'affichage
    par analyser() : ils sont repris tels quels."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    out = [lib.t("lecture.titre", la, fichier=rapport["fichier"])]
    out.append("  " + lib.t("lecture.verdict", la, verdict=lib.valeur(
        "lecture.verdict", rapport["verdict"], la).upper()))
    if rapport.get("pages_total") is not None:
        out.append("  " + lib.t("lecture.pages", la,
                                total=rapport["pages_total"],
                                avec_texte=rapport.get("pages_texte")))
    if rapport.get("taux_couverture") is not None:
        out.append("  " + lib.t(
            "lecture.taux", la,
            taux="%.1f" % (rapport["taux_couverture"] * 100)))
    if rapport.get("pages_ancrables"):
        out.append("  " + lib.t("lecture.ancrables", la, pages=_compacter(
            rapport["pages_ancrables"], langue_affichage=la)))
    if rapport.get("pages_non_ancrables"):
        out.append("  " + lib.t("lecture.non_ancrables", la, pages=_compacter(
            rapport["pages_non_ancrables"], langue_affichage=la)))
    for cle, cle_vide, entrees in (
            ("lecture.info", "lecture.info_aucune", rapport["info"]),
            ("lecture.avertissements", "lecture.avertissements_aucun",
             rapport["avertissements"]),
            ("lecture.problemes", "lecture.problemes_aucun",
             rapport["problemes"])):
        out.append(lib.t(cle if entrees else cle_vide, la))
        out += ["  - %s" % x for x in entrees]
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Preflight d'integrite de lecture PDF, avant tout ancrage de citation.")
    p.add_argument("fichier")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--strict", action="store_true",
                   help="code de sortie 1 si un avertissement ou un probleme est releve")
    p.add_argument("--langue-affichage", choices=["fr", "en"], default=None,
                   help="langue des libelles du rapport texte (defaut fr : un "
                        "PDF ne porte pas de pragme de langue). La sortie JSON "
                        "reste francaise quoi qu'il arrive")
    a = p.parse_args(argv)
    if a.format == "json":
        # Le JSON ne se traduit pas : les evals et le jeu d'or le lisent.
        rapport = analyser(a.fichier)
        print(json.dumps(rapport, ensure_ascii=False, indent=2))
    else:
        la = _lib().resoudre_affichage(a.langue_affichage)
        rapport = analyser(a.fichier, la)
        print(rapport_texte(rapport, la))
    if a.strict and (rapport["avertissements"] or rapport["problemes"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
