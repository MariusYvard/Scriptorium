#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Registre de logos : valider, placer.

Une charte graphique fixe des couleurs et des polices. Un logo obeit a d'autres
regles, propres a l'organisation qui le possede : zone de respiration, taille
minimale, usages autorises, rang protocolaire en co-signature. Ces regles
vivent dans un fichier separe, registre-logos.json, reference par la charte.

Deux actions :
  valider  controle le format du registre, l'existence des fichiers, la
           resolution effective de chaque logo pour l'usage qu'il declare, le
           contraste de son fond, et signale un format matriciel la ou un
           vectoriel serait preferable.
  placer   emet le fragment pret a inserer pour un usage donne, en docx, LaTeX
           ou HTML, largeur contrainte selon les regles du registre.

Aucune verification n'est bloquante a ce stade sauf une erreur de format ou un
fichier absent : une resolution basse est un avertissement, pas un refus.

Le calcul de resolution effective et ses seuils vivent dans images.py, qui les
porte pour toute illustration du plugin. Ce module les reprend sous les memes
noms (resolution_effective, DPI_IMPRESSION, DPI_ECRAN, POUCE_CM) sans en tenir
une seconde copie.

Le fragment de placement est un LIVRABLE : il part dans le document et ne
depend d'aucune langue d'affichage. Seuls les erreurs, les avertissements et
le rapport texte suivent --langue-affichage. Sans l'option ils restent en
francais : un registre de logos est un fichier de configuration, il ne porte
pas de langue.

Usage :
  python3 logos.py valider REGISTRE.json [--format text|json] [--strict]
                   [--langue-affichage fr|en]
  python3 logos.py placer REGISTRE.json --usage page-garde|en-tete|pied|
                   co-signature --format docx|latex|html [--sortie text|json]
                   [--langue-affichage fr|en]

Module importable : charger(source) -> dict ;
valider(reg, langue_affichage=None) -> (erreurs, avertissements) ;
pour_usage(reg, usage) -> list ;
fragment(reg, usage, format_sortie, langue_affichage=None) -> (str, avis).
Sans langue_affichage, erreurs et avertissements sont les chaines francaises
d'origine a l'octet pres : ce sont elles que serialise --format json.
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


USAGES = ("page-garde", "en-tete", "pied", "co-signature")
VECTORIELS = ("svg", "eps", "pdf", "emf", "wmf")

# Largeurs par defaut, en centimetres, quand le registre n'en fixe pas.
LARGEURS = {"page-garde": 5.0, "en-tete": 2.5, "pied": 2.0,
            "co-signature": 3.0}


def _charger_images():
    """Charge images.py par chemin, une seule fois au niveau module.

    Meme idiome que gabarit.py et check-lecture-pdf.py : le plugin n'est pas
    un paquet importable, ses scripts se chargent par chemin depuis le
    dossier voisin.
    """
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "images.py")
    spec = importlib.util.spec_from_file_location("images_mod", chemin)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_IMG = _charger_images()

# Seuils et calcul de resolution effective : images.py les porte pour tout le
# plugin (une photo de dispositif se mesure comme un logo), ils sont repris
# ici sous les memes noms plutot que redits.
DPI_IMPRESSION = _IMG.DPI_IMPRESSION
DPI_ECRAN = _IMG.DPI_ECRAN
POUCE_CM = _IMG.POUCE_CM
resolution_effective = _IMG.resolution_effective


def _images():
    """Module images.py deja charge, source unique de la lecture de dimensions."""
    return _IMG


def charger(source, langue_affichage=None):
    """Lit un registre depuis un chemin, un objet dejà charge ou l'entree."""
    if isinstance(source, dict):
        reg = source
        racine = os.getcwd()
    else:
        if source == "-":
            reg = json.load(sys.stdin)
            racine = os.getcwd()
        else:
            if not os.path.isfile(source):
                lib = _lib()
                raise SystemExit(lib.t(
                    "logos.err_registre",
                    lib.resoudre_affichage(langue_affichage), chemin=source))
            reg = json.load(open(source, encoding="utf-8"))
            racine = os.path.dirname(os.path.abspath(source))
    reg.setdefault("logos", [])
    reg["_racine"] = racine
    return reg


def largeur_usage(logo, usage):
    """Largeur d'affichage retenue : celle du registre, sinon le defaut."""
    par_usage = logo.get("largeur_cm_par_usage") or {}
    if usage in par_usage:
        return float(par_usage[usage])
    if logo.get("largeur_cm"):
        return float(logo["largeur_cm"])
    return LARGEURS.get(usage, 3.0)


def valider(reg, langue_affichage=None):
    """Erreurs bloquantes et avertissements consultatifs, jamais melanges.

    Sans langue_affichage, les deux listes sont les chaines francaises
    d'origine a l'octet pres : ce sont elles que serialise --format json.
    Les identifiants de logo, les noms d'usage et les extensions sont des
    valeurs du registre, ils sont repris tels quels dans les deux langues."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    erreurs, avis = [], []
    racine = reg.get("_racine") or os.getcwd()
    logos = reg.get("logos") or []
    if not logos:
        erreurs.append(lib.t("logos.e.aucun_logo", la))
    vus = set()
    mod = None
    for i, logo in enumerate(logos):
        etiquette = logo.get("id") or lib.t("logos.etiquette_entree", la,
                                            n=i + 1)
        if not logo.get("id"):
            erreurs.append(lib.t("logos.e.id_manquant", la,
                                 etiquette=etiquette))
        elif logo["id"] in vus:
            erreurs.append(lib.t("logos.e.id_double", la,
                                 etiquette=logo["id"]))
        else:
            vus.add(logo["id"])
        fichier = logo.get("fichier")
        if not fichier:
            erreurs.append(lib.t("logos.e.fichier_manquant", la,
                                 etiquette=etiquette))
            continue
        chemin = fichier if os.path.isabs(fichier) \
            else os.path.join(racine, fichier)
        if not os.path.isfile(chemin):
            erreurs.append(lib.t("logos.e.fichier_absent", la,
                                 etiquette=etiquette, fichier=fichier))
            continue
        usages = logo.get("usages") or list(USAGES)
        inconnus = [u for u in usages if u not in USAGES]
        if inconnus:
            erreurs.append(lib.t("logos.e.usage_inconnu", la,
                                 etiquette=etiquette,
                                 usages=", ".join(inconnus)))
        ext = os.path.splitext(chemin)[1].lower().lstrip(".")
        if ext in VECTORIELS:
            continue
        if mod is None:
            mod = _images()
        larg_px, haut_px, _fmt = mod.dimensions(open(chemin, "rb").read())
        if not larg_px:
            avis.append(lib.t("logos.a.dimensions", la, etiquette=etiquette))
            continue
        for usage in usages:
            cible = largeur_usage(logo, usage)
            dpi = resolution_effective(larg_px, cible)
            seuil = DPI_IMPRESSION if usage in ("page-garde", "co-signature") \
                else DPI_ECRAN
            if dpi is not None and dpi < seuil:
                avis.append(lib.t("logos.a.sous_seuil", la,
                                  etiquette=etiquette, usage=usage,
                                  dpi=round(dpi), cible=cible, seuil=seuil))
        avis.append(lib.t("logos.a.matriciel", la, etiquette=etiquette,
                          ext=ext))
        if logo.get("ratio_verrouille") and haut_px:
            attendu = logo["ratio_verrouille"]
            reel = larg_px / float(haut_px)
            if abs(reel - float(attendu)) > 0.02:
                erreurs.append(lib.t("logos.e.ratio", la, etiquette=etiquette,
                                     reel=reel, attendu=float(attendu)))
    return erreurs, avis


def pour_usage(reg, usage):
    """Logos autorises pour un usage, dans l'ordre protocolaire declare.

    Un rang absent vaut le dernier rang plutot qu'un rang devine. L'ordre entre
    deux logos de meme rang suit l'ordre du fichier, jamais l'alphabet, qui
    ferait passer une tutelle devant une autre sans raison.
    """
    retenus = []
    for i, logo in enumerate(reg.get("logos") or []):
        usages = logo.get("usages") or list(USAGES)
        if usage in usages:
            rang = logo.get("rang")
            retenus.append((rang if isinstance(rang, int) else 10 ** 6, i, logo))
    retenus.sort(key=lambda t: (t[0], t[1]))
    return [t[2] for t in retenus]


def fragment(reg, usage, format_sortie, langue_affichage=None):
    """Fragment pret a inserer pour un usage, dans un des trois formats.

    Le fragment lui-meme est un livrable : il ne depend d'aucune langue
    d'affichage. Seuls les avis rendus a cote en dependent, et sans
    langue_affichage ils restent les chaines francaises d'origine."""
    lib = _lib()
    la = lib.resoudre_affichage(langue_affichage)
    logos = pour_usage(reg, usage)
    if not logos:
        return "", [lib.t("logos.a.aucun_pour_usage", la, usage=usage)]
    avis = []
    racine = reg.get("_racine") or os.getcwd()
    if usage == "co-signature" and len(logos) < 2:
        avis.append(lib.t("logos.a.cosignature_seul", la))
    morceaux = []
    for logo in logos:
        larg = largeur_usage(logo, usage)
        chemin = logo.get("fichier", "")
        absolu = chemin if os.path.isabs(chemin) \
            else os.path.join(racine, chemin)
        if not os.path.isfile(absolu):
            avis.append(lib.t("logos.a.ecarte", la,
                              etiquette=logo.get("id") or chemin))
            continue
        alt = logo.get("alt") or logo.get("id") or "logo"
        respiration = float(logo.get("respiration", 0.25))
        if format_sortie == "latex":
            morceaux.append("\\includegraphics[width=%.2fcm]{%s}"
                            % (larg, chemin.replace("\\", "/")))
        elif format_sortie == "html":
            morceaux.append(
                '<img src="%s" alt="%s" style="width:%.2fcm;'
                'margin:%.2fcm">' % (chemin.replace("\\", "/"), alt, larg,
                                     respiration * larg))
        else:
            morceaux.append(absolu)
    if format_sortie == "latex":
        colle = "\\hspace{%.2fcm}" % (0.5 * float(
            logos[0].get("respiration", 0.25)) * largeur_usage(logos[0], usage))
        rendu = colle.join(morceaux)
    elif format_sortie == "html":
        rendu = ('<div class="logos logos-%s">%s</div>'
                 % (usage, "".join(morceaux)))
    else:
        rendu = "\n".join(morceaux)
        avis.append(lib.t("logos.a.docx", la))
    return rendu, avis


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Registre de logos : valider un registre, emettre le "
                    "fragment de placement pour un usage.")
    sp = p.add_subparsers(dest="action")

    # Option commune aux deux sous-commandes : posee sur un parent, elle
    # s'ecrit apres la sous-commande comme dans les dix-sept scripts deja
    # cables, pas avant elle.
    commun = argparse.ArgumentParser(add_help=False)
    commun.add_argument("--langue-affichage", choices=("fr", "en"),
                        default=None,
                        help="langue des erreurs, des avertissements et du "
                             "rapport texte (defaut fr : un registre de "
                             "logos est un fichier de configuration, il ne "
                             "porte pas de langue). Le fragment de placement "
                             "et la sortie JSON n'en dependent pas")

    pv = sp.add_parser("valider", help="controler un registre de logos",
                       parents=[commun])
    pv.add_argument("registre")
    pv.add_argument("--format", choices=("text", "json"), default="text")
    pv.add_argument("--strict", action="store_true",
                    help="code de sortie 1 des le premier avertissement")

    pp = sp.add_parser("placer", help="fragment de placement pour un usage",
                       parents=[commun])
    pp.add_argument("registre")
    pp.add_argument("--usage", choices=USAGES, required=True)
    pp.add_argument("--format", choices=("docx", "latex", "html"),
                    default="html")
    pp.add_argument("--sortie", choices=("text", "json"), default="text")

    a = p.parse_args(argv)
    if not a.action:
        p.print_help()
        return 0

    lib = _lib()
    la = lib.resoudre_affichage(a.langue_affichage)
    reg = charger(a.registre, la)

    if a.action == "valider":
        if a.format == "json":
            # Le JSON ne se traduit pas : les evals et le jeu d'or le lisent.
            erreurs, avis = valider(reg)
            print(json.dumps({"erreurs": erreurs, "avertissements": avis,
                              "logos": len(reg.get("logos") or [])},
                             ensure_ascii=False, indent=2))
        else:
            erreurs, avis = valider(reg, la)
            for e in erreurs:
                print("  " + lib.t("logos.ligne_erreur", la, message=e))
            for w in avis:
                print("  " + lib.t("logos.ligne_avertissement", la,
                                   message=w))
            if not erreurs and not avis:
                print("  " + lib.t("logos.conforme", la,
                                   n=len(reg.get("logos") or [])))
            print("\n" + lib.t("logos.comptes", la, erreurs=len(erreurs),
                               avis=len(avis)))
        if erreurs:
            return 1
        return 1 if (a.strict and avis) else 0

    if a.action == "placer":
        if a.sortie == "json":
            # Le JSON ne se traduit pas : les evals et le jeu d'or le lisent.
            rendu, avis = fragment(reg, a.usage, a.format)
            print(json.dumps({"usage": a.usage, "format": a.format,
                              "fragment": rendu, "avertissements": avis},
                             ensure_ascii=False, indent=2))
        else:
            rendu, avis = fragment(reg, a.usage, a.format, la)
            print(rendu)
            for w in avis:
                print("  " + lib.t("logos.avertissement", la, message=w),
                      file=sys.stderr)
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
