#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prepare et controle la compilation reelle des gabarits LaTeX.

Les gabarits scriptorium/assets/gabarit-rapport.tex et gabarit-poster.tex
n'avaient jamais ete compiles : seul l'equilibre de leurs environnements
avait ete verifie par script. Ce module fabrique un dossier de compilation
autonome, pour que .github/workflows/gabarits-latex.yml les passe dans un
vrai xelatex, en image TeX Live, et echoue si la compilation echoue.

Ce que "preparer" fabrique dans le dossier de destination :
  - gabarit-rapport.tex et gabarit-poster.tex, bloc CHARTE remplace par la
    sortie reelle de theme.py --format latex. Le mecanisme d'injection est
    documente en tete des deux gabarits et n'avait jamais ete execute contre
    un compilateur ; il l'est ici, avec la charte d'exemple du depot.
  - pilote-figure.tex : le gabarit de rapport dont les deux exemples de
    figure, laisses en commentaire, sont decommentes VERBATIM, suivis de
    renvois \\ref et \\pageref. Verbatim est le point : le pilote compile
    l'exemple tel qu'il est ecrit dans le gabarit, jamais une reecriture qui
    pourrait compiler la ou l'exemple echouerait.
  - figures/*.png : les images que ces exemples incluent. Une figure sans
    image a inclure ne prouve pas \\includegraphics. Les PNG sont ecrits ici
    (zlib et struct, bibliotheque standard) plutot que commites.

"controler" relit ce que la compilation a laisse : PDF non vides, table des
figures et liste des tableaux reellement remplies depuis les \\caption,
aucun renvoi non resolu. Un latexmk qui rend 0 ne prouve pas a lui seul que
\\listoffigures s'est rempli.

Usage :
    python3 tools/ci-latex.py preparer --dest DOSSIER [--charte FICHIER]
    python3 tools/ci-latex.py controler --dest DOSSIER

Module importable : injecter_charte(texte, bloc) -> str ;
extraire_figures(texte) -> [str] ; png(largeur, hauteur) -> bytes ;
pilote(texte_rapport, figures) -> str.
Bibliotheque standard uniquement, aucun compilateur invoque ici.
"""
import argparse
import importlib.util
import os
import re
import struct
import sys
import zlib

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.abspath(os.path.join(ICI, ".."))
ASSETS = os.path.join(RACINE, "scriptorium", "assets")
SCRIPTS = os.path.join(RACINE, "scriptorium", "scripts")
CHARTE_DEFAUT = os.path.join(ASSETS, "charte-graphique.exemple.json")

GABARITS = ("gabarit-rapport.tex", "gabarit-poster.tex")

MARQUE_DEBUT = ">>> DEBUT BLOC CHARTE"
MARQUE_FIN = "<<< FIN BLOC CHARTE"

# Ancre d'insertion du bloc de figures dans le pilote : juste avant l'encadre
# de resultat, la ou le gabarit place lui-meme son exemple commente.
ANCRE_PILOTE = "\\begin{resultat}[Constat principal]"

# Images attendues par les exemples de figure du gabarit, sans extension dans
# le .tex (xelatex choisit le format disponible) et rangees sous figures/,
# premier dossier de \graphicspath.
IMAGES = {"courbe-mesures": (640, 400), "vue-avant": (480, 360),
          "vue-apres": (480, 360)}

_DEBUT_FIG = re.compile(r"^%\s*\\begin\{figure\}")
_FIN_FIG = re.compile(r"^%\s*\\end\{figure\}")


def _mod(fichier, nom):
    spec = importlib.util.spec_from_file_location(
        nom, os.path.join(SCRIPTS, fichier))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def injecter_charte(texte, bloc):
    """Remplace le contenu situe entre les deux marqueurs CHARTE d'un gabarit
    par BLOC. Les lignes de marqueur restent en place, pour que le gabarit
    produit reste injectable une seconde fois.

    Leve ValueError si un marqueur manque ou apparait plus d'une fois : un
    gabarit dont le mecanisme d'injection a ete casse doit se signaler, pas
    ressortir intact et silencieux.
    """
    lignes = texte.splitlines()
    debuts = [i for i, l in enumerate(lignes) if MARQUE_DEBUT in l]
    fins = [i for i, l in enumerate(lignes) if MARQUE_FIN in l]
    if len(debuts) != 1 or len(fins) != 1:
        raise ValueError(
            "marqueurs CHARTE attendus une fois chacun (vu debut=%d, fin=%d)"
            % (len(debuts), len(fins)))
    if fins[0] <= debuts[0]:
        raise ValueError("marqueur de fin CHARTE avant le marqueur de debut")
    return "\n".join(lignes[:debuts[0] + 1] + bloc.splitlines()
                     + lignes[fins[0]:]) + "\n"


def _decommenter(ligne):
    depouillee = ligne.lstrip()
    if not depouillee.startswith("%"):
        return ligne
    depouillee = depouillee[1:]
    return depouillee[1:] if depouillee.startswith(" ") else depouillee


def extraire_figures(texte):
    """Retourne les environnements figure laisses en commentaire dans un
    gabarit, decommentes verbatim, dans l'ordre du fichier.

    Les \\begin{subfigure} imbriques ne ferment pas l'environnement : seule
    une ligne \\end{figure} le fait.
    """
    trouvees, courant = [], None
    for ligne in texte.splitlines():
        if courant is None:
            if _DEBUT_FIG.match(ligne):
                courant = [_decommenter(ligne)]
            continue
        courant.append(_decommenter(ligne))
        if _FIN_FIG.match(ligne):
            trouvees.append("\n".join(courant))
            courant = None
    if courant is not None:
        raise ValueError("environnement figure commente non ferme")
    return trouvees


# Renvois ajoutes au pilote. Le gabarit documente \ref, \pageref et le renvoi
# a une sous-figure en commentaire ; le pilote les exerce pour de vrai, sinon
# rien ne prouve que les etiquettes posees se resolvent.
RENVOIS = r"""
La dispersion se lit sur la figure~\ref{fig:mesures}, page~\pageref{fig:mesures}.
L'etat du dispositif avant et apres intervention est donne par la
figure~\ref{fig:vues}, dont la vue posterieure porte le renvoi~\ref{fig:vues-apres} ;
les series correspondantes figurent au tableau~\ref{tab:exemple},
page~\pageref{tab:exemple}.
"""


def pilote(texte_rapport, figures):
    """Insere les exemples de figure decommentes, puis les renvois, juste
    avant l'encadre de resultat du gabarit de rapport."""
    if not figures:
        raise ValueError(
            "aucun exemple de figure commente trouve dans le gabarit de rapport")
    if texte_rapport.count(ANCRE_PILOTE) != 1:
        raise ValueError("ancre d'insertion absente ou ambigue : %s" % ANCRE_PILOTE)
    bloc = "\n\n".join(figures) + "\n" + RENVOIS + "\n"
    return texte_rapport.replace(ANCRE_PILOTE, bloc + ANCRE_PILOTE)


def png(largeur=640, hauteur=400):
    """PNG RGB valide, ecrit a la main (zlib et struct).

    Ecrit plutot que commite : le depot n'a pas besoin d'un binaire de plus,
    et une image generee ne peut pas deriver de ce que le test croit inclure.
    """
    if largeur < 1 or hauteur < 1:
        raise ValueError("dimensions PNG strictement positives attendues")
    dx = max(largeur - 1, 1)
    dy = max(hauteur - 1, 1)
    lignes = []
    for y in range(hauteur):
        ligne = bytearray([0])  # octet de filtre : aucun
        vert = (y * 255) // dy
        for x in range(largeur):
            ligne += bytes(((x * 255) // dx, vert, 128))
        lignes.append(bytes(ligne))

    def bloc(typ, donnees):
        return (struct.pack(">I", len(donnees)) + typ + donnees
                + struct.pack(">I", zlib.crc32(typ + donnees) & 0xFFFFFFFF))

    entete = struct.pack(">IIBBBBB", largeur, hauteur, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + bloc(b"IHDR", entete)
            + bloc(b"IDAT", zlib.compress(b"".join(lignes), 9))
            + bloc(b"IEND", b""))


def preparer(dest, charte=None):
    """Ecrit dans DEST les deux gabarits chartes, le pilote et ses images.

    La charte est injectee par theme.latex() execute ICI, donc dans
    l'environnement qui compilera : sa resolution de police par fc-list voit
    les polices reellement installees et retombe sur Latin Modern si la
    police demandee est absente. Preparer sur une machine et compiler sur une
    autre annulerait cette garantie.
    """
    theme = _mod("theme.py", "theme_mod")
    t = theme.charger(charte or CHARTE_DEFAUT)
    erreurs, _ = theme.valider(t)
    if erreurs:
        raise ValueError("charte invalide : " + " ; ".join(erreurs))
    bloc = theme.latex(t)

    os.makedirs(os.path.join(dest, "figures"), exist_ok=True)
    ecrits, sources = [], {}
    for nom in GABARITS:
        with open(os.path.join(ASSETS, nom), encoding="utf-8") as f:
            sources[nom] = f.read()
        chemin = os.path.join(dest, nom)
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(injecter_charte(sources[nom], bloc))
        ecrits.append(chemin)

    figures = extraire_figures(sources["gabarit-rapport.tex"])
    chemin_pilote = os.path.join(dest, "pilote-figure.tex")
    with open(chemin_pilote, "w", encoding="utf-8") as f:
        f.write(pilote(injecter_charte(sources["gabarit-rapport.tex"], bloc),
                       figures))
    ecrits.append(chemin_pilote)

    for nom, (largeur, hauteur) in sorted(IMAGES.items()):
        chemin = os.path.join(dest, "figures", nom + ".png")
        with open(chemin, "wb") as f:
            f.write(png(largeur, hauteur))
        ecrits.append(chemin)

    return {"dest": dest, "fichiers": ecrits,
            "figures_extraites": len(figures),
            "bloc_charte": bloc.splitlines()}


DOCUMENTS = ("gabarit-rapport", "gabarit-poster", "pilote-figure")


def _lire(chemin):
    try:
        with open(chemin, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def controler(dest):
    """Relit ce que la compilation a laisse. Un latexmk qui rend 0 ne prouve
    pas que \\listoffigures s'est rempli ni qu'un \\ref s'est resolu."""
    constats = []

    def dire(nom, ok, detail=""):
        constats.append({"controle": nom, "ok": bool(ok), "detail": detail})

    for base in DOCUMENTS:
        pdf = os.path.join(dest, base + ".pdf")
        existe = os.path.isfile(pdf)
        taille = os.path.getsize(pdf) if existe else 0
        entete = b""
        if existe:
            with open(pdf, "rb") as f:
                entete = f.read(5)
        dire("%s : PDF produit, en-tete PDF, non vide" % base,
             existe and entete == b"%PDF-" and taille > 10000,
             "existe=%s entete=%r octets=%d" % (existe, entete, taille))

    lof = _lire(os.path.join(dest, "pilote-figure.lof"))
    n_fig = lof.count("\\contentsline {figure}")
    dire("pilote : table des figures remplie depuis les \\caption",
         n_fig >= 2, "entrees figure=%d (2 attendues)" % n_fig)

    lot = _lire(os.path.join(dest, "pilote-figure.lot"))
    n_tab = lot.count("\\contentsline {table}")
    dire("pilote : liste des tableaux remplie", n_tab >= 1,
         "entrees table=%d" % n_tab)

    log = _lire(os.path.join(dest, "pilote-figure.log"))
    dire("pilote : aucun renvoi non resolu",
         bool(log) and "There were undefined references" not in log,
         "journal lu=%s" % bool(log))
    absentes = [n for n in sorted(IMAGES) if (n + ".png") not in log]
    dire("pilote : chaque image incluse apparait dans le journal",
         not absentes, "absentes du journal : %s" % ", ".join(absentes))

    return constats


def controler_texte(constats):
    lignes = []
    for c in constats:
        marque = "OK" if c["ok"] else "ECHEC"
        suffixe = "  %s" % c["detail"] if (c["detail"] and not c["ok"]) else ""
        lignes.append("  [%s] %s%s" % (marque, c["controle"], suffixe))
    rates = sum(1 for c in constats if not c["ok"])
    lignes.append("")
    lignes.append("%d/%d controles passes." % (len(constats) - rates, len(constats)))
    return "\n".join(lignes)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="ci-latex.py",
        description="Prepare et controle la compilation reelle des gabarits LaTeX.")
    sous = ap.add_subparsers(dest="commande", required=True)

    p_p = sous.add_parser("preparer", help="ecrit gabarits chartes, pilote et images")
    p_p.add_argument("--dest", required=True, help="dossier de compilation")
    p_p.add_argument("--charte", default=None,
                     help="charte graphique JSON (defaut : la charte d'exemple du depot)")

    p_c = sous.add_parser("controler", help="relit les sorties de compilation")
    p_c.add_argument("--dest", required=True, help="dossier de compilation")

    a = ap.parse_args(argv)

    if a.commande == "preparer":
        try:
            r = preparer(a.dest, a.charte)
        except (OSError, ValueError) as e:
            print("Preparation impossible : %s" % e, file=sys.stderr)
            return 1
        print("Prepare dans %s : %d exemple(s) de figure extrait(s) du gabarit."
              % (r["dest"], r["figures_extraites"]))
        for ligne in r["bloc_charte"]:
            print("  charte| %s" % ligne)
        for f in r["fichiers"]:
            print("  ecrit  %s" % os.path.relpath(f, a.dest))
        return 0

    constats = controler(a.dest)
    print(controler_texte(constats))
    return 0 if all(c["ok"] for c in constats) else 1


if __name__ == "__main__":
    sys.exit(main())
