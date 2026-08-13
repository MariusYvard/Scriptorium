# -*- coding: utf-8 -*-
"""Cas d'eval du preflight d'integrite de lecture PDF (check-lecture-pdf.py).

Couvre les verdicts de lecture (fiable, non fiable, non mesurable), la
detection de pages sans texte, la degradation propre sans backend, la
detection de texte suspect et le cas d'un PDF chiffre ou introuvable.
"""
import importlib.util
import os
import sys
import tempfile


def charger(nom_fichier, nom_module, dossier=SCRIPTS):
    spec = importlib.util.spec_from_file_location(nom_module, os.path.join(dossier, nom_fichier))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


clp = charger("check-lecture-pdf.py", "check_lecture_pdf")
genpdf = charger("generer-pdf.py", "generer_pdf", FIXT)

# Garde contre le masquage d'un module standard par un fichier de scripts/.
# Aucun script du depot n'insere plus scripts/ dans sys.path, ce qui faisait
# resoudre "import numbers" (dont depend decimal) vers le numbers.py maison.
# Le controle reste ici : il coute une ligne et il echouerait bruyamment si la
# pratique revenait, au lieu de laisser un import casse se cacher.
_std = sys.modules.get("numbers")
if _std is not None and not hasattr(_std, "Number"):
    raise SystemExit(
        "le module standard numbers est masque par scripts/numbers.py : un "
        "script du depot a insere scripts/ dans sys.path")

# Fixtures regenerees a chaque run : deterministes, sans dependance.
genpdf.main(FIXT)
P_NORMAL = os.path.join(FIXT, "pdf-normal.pdf")
P_VIDE = os.path.join(FIXT, "pdf-sans-texte.pdf")
P_TRONQUE = os.path.join(FIXT, "pdf-tronque.pdf")


# Cas 1-3 : PDF normal, texte extractible, ancrage possible
r_normal = clp.analyser(P_NORMAL)
verifier("pdf normal : verdict lecture fiable",
         r_normal["verdict"] == "lecture fiable", f"verdict={r_normal['verdict']}")
verifier("pdf normal : page 1 ancrable",
         r_normal["pages_ancrables"] == [1] and r_normal["pages_non_ancrables"] == [],
         f"ancrables={r_normal['pages_ancrables']} non_ancrables={r_normal['pages_non_ancrables']}")
verifier("pdf normal : taux de couverture a 100%",
         r_normal["taux_couverture"] == 1.0, f"taux={r_normal['taux_couverture']}")

# Cas 4-5 : PDF sans texte (scan sans OCR), ancrage refuse
r_vide = clp.analyser(P_VIDE)
verifier("pdf sans texte : page sans texte refusee a l'ancrage",
         r_vide["pages_sans_texte"] == [1] and r_vide["pages_ancrables"] == [],
         f"sans_texte={r_vide['pages_sans_texte']} ancrables={r_vide['pages_ancrables']}")
verifier("pdf sans texte : scan sans OCR signale",
         any("scanne sans ocr" in p.lower() for p in r_vide["problemes"]),
         f"problemes={r_vide['problemes']}")

# Cas 6-7 : PDF tronque, attrape en lecture binaire directe (sans backend requis)
r_tronque = clp.analyser(P_TRONQUE)
verifier("pdf tronque : eof absent detecte",
         r_tronque["binaire"]["eof_present"] is False,
         f"binaire={r_tronque['binaire']}")
verifier("pdf tronque : verdict lecture non fiable",
         r_tronque["verdict"] == "lecture non fiable", f"verdict={r_tronque['verdict']}")


# Cas 8 : absence totale de backend -> non mesurable, JAMAIS non fiable
# (technique de monkeypatch identique a evals/run-evals.py pour check-presentation.py)
_sauve = (clp._CHKP.extraire_texte_pages, clp._CHKP.compter_pages_et_taille)
clp._CHKP.extraire_texte_pages = lambda chemin: (None, None)
clp._CHKP.compter_pages_et_taille = lambda chemin: (None, None, None)
r_sans_backend = clp.analyser(P_NORMAL)
clp._CHKP.extraire_texte_pages, clp._CHKP.compter_pages_et_taille = _sauve
verifier("absence de backend : verdict non mesurable, jamais non fiable",
         r_sans_backend["verdict"] == "non mesurable", f"verdict={r_sans_backend['verdict']}")
verifier("absence de backend : ne se confond pas avec un defaut du document",
         r_sans_backend["verdict"] != "lecture non fiable")

# Cas 9 : fichier introuvable
r_absent = clp.analyser(os.path.join(FIXT, "inexistant_scriptorium_xyz.pdf"))
verifier("fichier introuvable : verdict lecture non fiable, probleme explicite",
         r_absent["verdict"] == "lecture non fiable"
         and any("introuvable" in p for p in r_absent["problemes"]),
         f"rapport={r_absent}")

# Cas 10-12 : detection de texte suspect (encodage casse)
verifier("texte suspect : ratio eleve de caracteres de remplacement",
         clp._texte_suspect("�" * 30 + "texte normal ici"))
verifier("texte suspect : mot tres long sans une seule voyelle",
         clp._texte_suspect("Preambule normal puis " + "bcdfghjklmnpqrstvwxz" * 2))
verifier("texte suspect : texte francais normal non signale",
         not clp._texte_suspect(
             "Ceci est un texte francais tout a fait normal et lisible, "
             "avec des phrases completes et des mots courants."))


# Cas 13 : PDF chiffre/protege signale, sans tentative de contournement
with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
    tf.write(b"%PDF-1.4\n1 0 obj\n<< /Encrypt 2 0 R >>\nendobj\n%%EOF")
    p_chiffre = tf.name
try:
    bin_chiffre = clp.verifier_integrite_binaire(p_chiffre)
    verifier("integrite binaire : /Encrypt detecte et declare",
             bin_chiffre["chiffre_signale"] is True, f"binaire={bin_chiffre}")
finally:
    os.remove(p_chiffre)

# Cas 14 : rapport_texte() est une chaine exploitable, verdict lisible
texte_rapport = clp.rapport_texte(r_normal)
verifier("rapport_texte : chaine contenant le verdict en majuscules",
         isinstance(texte_rapport, str) and "LECTURE FIABLE" in texte_rapport,
         texte_rapport[:80])

# Cas 15 : pages_ancrables et pages_non_ancrables partitionnent les pages, sans recouvrement
recouvrement = set(r_vide["pages_ancrables"]) & set(r_vide["pages_non_ancrables"])
verifier("pages ancrables et non ancrables : aucun recouvrement",
         not recouvrement, f"recouvrement={recouvrement}")
