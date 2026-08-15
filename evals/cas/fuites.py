"""Cas d'eval de l'audit de fuites (check-fuites.py) et des invisibles.

Couvre les proprietes de document, les residus de travail (modifications
suivies, commentaires, texte masque), les chemins locaux, la detection de mise
a jour incrementale d'un PDF, la graduation de confiance, et les caracteres
invisibles du linter avec leurs faux positifs a ne pas lever.
"""
import importlib.util as _iu
import os

fui = charger("check-fuites.py", "check_fuites")
lint_f = charger("lint-style.py", "lint_style_fuites")

# Le harnais injecte charger(nom, module) qui lit dans scripts/ : le
# generateur vit dans les fixtures, il se charge par chemin explicite.
_spec = _iu.spec_from_file_location(
    "generer_fuites", os.path.join(FIXT, "generer-fuites.py"))
genf = _iu.module_from_spec(_spec)
_spec.loader.exec_module(genf)
genf.main(FIXT)

F_DOCX = os.path.join(FIXT, "fuites-docx.docx")
F_NET = os.path.join(FIXT, "fuites-docx-net.docx")
F_PDF = os.path.join(FIXT, "fuites-pdf.pdf")
F_INC = os.path.join(FIXT, "fuites-pdf-incremental.pdf")

r = fui.analyser(F_DOCX)
verifier("fuites : le verdict se ferme sur un constat confirme",
         r["verdict"] == "fuites confirmees", f"v={r['verdict']}")
_regles = {c["regle"] for c in r["constats"]}
verifier("fuites : auteur et derniere personne a enregistrer sont relevés",
         sum(1 for c in r["constats"]
             if c["regle"] == "propriete de document"
             and c["confiance"] == "confirme") >= 2, f"r={_regles}")
verifier("fuites : les modifications suivies non acceptees sont confirmees",
         any(c["regle"] == "modifications suivies"
             and c["confiance"] == "confirme" for c in r["constats"]))
verifier("fuites : un commentaire oublie nomme son auteur",
         any(c["regle"] == "commentaires" and "Claire Dumas" in (c["valeur"] or "")
             for c in r["constats"]), f"c={_regles}")
verifier("fuites : le texte masque est signale sans etre affirme",
         any(c["regle"] == "texte masque" and c["confiance"] == "probable"
             for c in r["constats"]))
verifier("fuites : un chemin local est une fuite confirmee",
         any(c["regle"] == "chemin local" and "prenom.nom" in (c["valeur"] or "")
             for c in r["constats"]))
verifier("fuites : l'historique d'edition est rapporte a part de l'identite",
         any(c["categorie"] == "historique" for c in r["constats"]))

# Graduation : un champ qui porte l'auteur declare du document ne fuit rien.
_sans = fui.analyser(F_PDF)
_avec = fui.analyser(F_PDF, auteur="Prenom Nom")
verifier("fuites : l'auteur declare passe de confirme a douteux",
         any(c["confiance"] == "confirme" for c in _sans["constats"])
         and not any(c["confiance"] == "confirme" for c in _avec["constats"]),
         f"sans={_sans['comptes']} avec={_avec['comptes']}")

_net = fui.analyser(F_NET)
verifier("fuites : un document sans identite ne leve aucun confirme",
         _net["comptes"]["confirme"] == 0, f"n={_net['comptes']}")
verifier("fuites : un champ generique n'est pas compte comme une identite",
         all("Word" not in (c["valeur"] or "") or c["confiance"] == "informatif"
             for c in _net["constats"]))

# Le piege exiftool : l'edition incrementale laisse l'ancien etat lisible.
_inc = fui.analyser(F_INC)
verifier("fuites : une mise a jour incrementale de PDF est detectee",
         any(c["regle"] == "mise a jour incrementale"
             and c["confiance"] == "confirme" for c in _inc["constats"]),
         f"c={[x['regle'] for x in _inc['constats']]}")
verifier("fuites : le PDF simple ne declenche pas le constat incremental",
         not any(c["regle"] == "mise a jour incrementale"
                 for c in _sans["constats"]))
verifier("fuites : le fichier incremental est plus gros que l'original",
         os.path.getsize(F_INC) > os.path.getsize(F_PDF))
verifier("fuites : le rapport nomme ce qu'il ne verifie pas",
         len(_inc["non_verifie"]) >= 3 and isinstance(
             fui.rapport_texte(_inc), str))
try:
    fui.analyser(os.path.join(FIXT, "style-propre.md"))
    _refus = False
except SystemExit:
    _refus = True
verifier("fuites : un format non couvert s'arrete par un message nomme",
         _refus)

# Caracteres invisibles du linter : ce qui doit etre attrape.
_pieges = [
    ("largeur nulle", "Un texte avec​une espace nulle.",
     "caractere-invisible"),
    ("trait conditionnel", "Un mot cou­pe.", "caractere-invisible"),
    ("controle bidi", "Un texte ‮suspect‬ ici.", "controle-bidi"),
    ("caractere de tag", "Un texte \U000e0041 marque.", "caractere-tag"),
    ("zone privee", "Un glyphe  maison.", "zone-privee"),
    ("espace exotique", "Une espace  fine.", "espace-exotique"),
    ("liant entre lettres latines", "Un mot bi‌zarre.", "liant-inutile"),
]
for _nom, _txt, _regle in _pieges:
    _c = {x["regle"] for x in lint_f.lint_text(_txt)}
    verifier("invisibles : %s attrape" % _nom, _regle in _c, f"vu={_c}")

# Ce qui ne doit surtout PAS etre attrape : les liants portent du sens dans
# les emoji composes et dans les ecritures qui les emploient.
_REGLES_INV = {"caractere-invisible", "controle-bidi", "caractere-tag",
               "zone-privee", "espace-exotique", "liant-inutile"}
_propres = [
    ("famille emoji", "Une famille \U0001f468‍\U0001f469‍\U0001f467."),
    ("drapeau", "Le drapeau \U0001f1eb\U0001f1f7 francais."),
    ("liant en ecriture arabe", "Texte ل‌ا arabe."),
    ("insecable ordinaire", "Page 12 correcte."),
    ("prose francaise nette", "Une phrase parfaitement ordinaire et lisible."),
]
for _nom, _txt in _propres:
    _c = {x["regle"] for x in lint_f.lint_text(_txt)} & _REGLES_INV
    verifier("invisibles : %s ne leve aucun constat" % _nom, not _c,
             f"vu={_c}")
