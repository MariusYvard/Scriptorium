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

Module importable : analyser(chemin) -> dict ; rapport_texte(rapport) -> str.
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


def verifier_integrite_binaire(chemin):
    """Lecture binaire directe, sans backend : en-tete %PDF-, marqueur
    %%EOF en fin de fichier, presence d'une table xref/startxref. Marche
    toujours, meme sans aucun backend PDF installe."""
    resultat = {"entete_pdf": None, "eof_present": None, "xref_present": None,
               "chiffre_signale": None, "erreur": None}
    try:
        with open(chemin, "rb") as f:
            donnees = f.read()
    except OSError as e:
        resultat["erreur"] = f"lecture binaire impossible : {e}"
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


def _compacter(liste, max_n=20):
    """Represente une liste d'entiers de facon lisible, tronquee si longue."""
    if len(liste) <= max_n:
        return ", ".join(str(i) for i in liste)
    reste = len(liste) - max_n
    return ", ".join(str(i) for i in liste[:max_n]) + f", ... (+{reste})"


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


def analyser(chemin):
    """Analyse complete d'un fichier PDF avant ancrage. Retourne un rapport
    dict : fichier, pages_total, pages_texte, taux_couverture,
    pages_sans_texte, pages_ancrables, pages_non_ancrables, verdict, binaire,
    info, avertissements, problemes."""
    rapport = {"fichier": os.path.basename(chemin), "pages_total": None,
              "pages_texte": None, "taux_couverture": None,
              "pages_sans_texte": [], "pages_ancrables": [], "pages_non_ancrables": [],
              "verdict": None, "binaire": {}, "info": [], "avertissements": [], "problemes": []}
    if not os.path.isfile(chemin):
        rapport["problemes"].append(f"Fichier introuvable : {chemin}")
        rapport["verdict"] = "lecture non fiable"
        return rapport
    if not chemin.lower().endswith(".pdf"):
        rapport["avertissements"].append("Extension non .pdf : ce preflight est concu pour un PDF.")

    binaire = verifier_integrite_binaire(chemin)
    rapport["binaire"] = binaire
    defectueux = False
    if binaire.get("erreur"):
        rapport["problemes"].append(binaire["erreur"])
        defectueux = True
    else:
        if not binaire["entete_pdf"]:
            rapport["problemes"].append(
                "En-tete %PDF- absent en tete de fichier : non reconnaissable comme PDF.")
            defectueux = True
        if not binaire["eof_present"]:
            rapport["problemes"].append(
                f"Marqueur %%EOF absent dans les {TAILLE_QUEUE_EOF} derniers octets : "
                "fichier tronque ou mal ferme.")
            defectueux = True
        if not binaire["xref_present"]:
            rapport["problemes"].append(
                "Table xref/startxref introuvable : structure PDF illisible.")
            defectueux = True
        if binaire["chiffre_signale"]:
            rapport["avertissements"].append(
                "Marqueur /Encrypt present : PDF chiffre ou protege. Extraction "
                "potentiellement partielle ou vide. Aucun contournement tente ici.")
    return _analyser_texte(chemin, rapport, defectueux)


def _analyser_texte(chemin, rapport, defectueux):
    """Deuxieme moitie de analyser() : mesure de la couverture de texte via
    la cascade de check-presentation.py. Separee pour rester lisible."""
    chkp = _CHKP
    if chkp is None:
        rapport["problemes"].append(
            "check-presentation.py introuvable : cascade de backends PDF indisponible.")
        rapport["verdict"] = _calculer_verdict(None, None, defectueux, True)
        return rapport

    n_pages, _dims, backend_pages = chkp.compter_pages_et_taille(chemin)
    rapport["pages_total"] = n_pages
    if backend_pages:
        rapport["info"].append(f"Pages : {n_pages} (source : {backend_pages}).")
    else:
        rapport["avertissements"].append(
            "Nombre de pages indetermine : aucun backend disponible pour le compter.")

    textes, backend_texte = chkp.extraire_texte_pages(chemin)
    if textes is None:
        rapport["avertissements"].append(
            "Texte non extrait : aucun backend disponible (pypdf ou pdftotext). "
            "Couverture non mesurable, ancrage a refuser par prudence.")
        rapport["verdict"] = _calculer_verdict(n_pages, None, defectueux, True)
        return rapport

    rapport["info"].append(f"Texte extrait via {backend_texte} sur {len(textes)} page(s).")
    if n_pages is not None and n_pages != len(textes):
        rapport["avertissements"].append(
            f"Comptage de pages ({n_pages}, {backend_pages}) et extraction de texte "
            f"({len(textes)}, {backend_texte}) divergent.")
    if rapport["pages_total"] is None:
        rapport["pages_total"] = len(textes)

    return _classer_pages(rapport, textes, defectueux)


def _classer_pages(rapport, textes, defectueux):
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
        rapport["problemes"].append(
            f"Pages sans texte extrait, ancrage refuse : {_compacter(sans_texte)}.")
    if cassees:
        rapport["problemes"].append(
            "Pages a l'encodage suspect (mojibake ou caracteres de remplacement), "
            f"ancrage refuse : {_compacter(cassees)}.")
    if textes and len(sans_texte) == len(textes):
        if rapport["binaire"].get("chiffre_signale"):
            rapport["problemes"].append(
                "Aucune page ne rend de texte, et le PDF est signale chiffre/protege : "
                "l'extraction vide vient probablement de la protection, pas d'un scan sans OCR.")
        else:
            rapport["problemes"].append(
                "Aucune page ne rend de texte alors que le fichier a des pages : "
                "probable PDF scanne sans OCR.")

    n_pages_final = rapport["pages_total"] if rapport["pages_total"] is not None else len(textes)
    rapport["verdict"] = _calculer_verdict(n_pages_final, taux, defectueux, False)
    return rapport


def rapport_texte(rapport):
    """Rendu texte lisible du rapport. Voir analyser() pour la structure."""
    out = [f"Preflight d'integrite de lecture PDF : {rapport['fichier']}"]
    out.append(f"  Verdict : {rapport['verdict'].upper()}")
    if rapport.get("pages_total") is not None:
        out.append(f"  Pages : {rapport['pages_total']} au total, "
                   f"{rapport.get('pages_texte')} avec texte extrait.")
    if rapport.get("taux_couverture") is not None:
        out.append(f"  Taux de couverture texte (pages ancrables) : "
                   f"{rapport['taux_couverture'] * 100:.1f} %")
    if rapport.get("pages_ancrables"):
        out.append(f"  Pages ancrables : {_compacter(rapport['pages_ancrables'])}")
    if rapport.get("pages_non_ancrables"):
        out.append(f"  Pages NON ancrables (ancrage a refuser) : "
                   f"{_compacter(rapport['pages_non_ancrables'])}")
    out.append("Information :" if rapport["info"] else "Information : aucune")
    for i in rapport["info"]:
        out.append(f"  - {i}")
    out.append("Avertissements :" if rapport["avertissements"] else "Avertissements : aucun")
    for a in rapport["avertissements"]:
        out.append(f"  - {a}")
    out.append("Problemes :" if rapport["problemes"] else "Problemes : aucun")
    for e in rapport["problemes"]:
        out.append(f"  - {e}")
    return "\n".join(out)


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Preflight d'integrite de lecture PDF, avant tout ancrage de citation.")
    p.add_argument("fichier")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--strict", action="store_true",
                   help="code de sortie 1 si un avertissement ou un probleme est releve")
    a = p.parse_args(argv)
    rapport = analyser(a.fichier)
    if a.format == "json":
        print(json.dumps(rapport, ensure_ascii=False, indent=2))
    else:
        print(rapport_texte(rapport))
    if a.strict and (rapport["avertissements"] or rapport["problemes"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
