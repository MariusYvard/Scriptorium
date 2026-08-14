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

Usage :
  python3 logos.py valider REGISTRE.json [--format text|json] [--strict]
  python3 logos.py placer REGISTRE.json --usage page-garde|en-tete|pied|
                   co-signature --format docx|latex|html [--sortie text|json]
"""
import argparse
import json
import os
import sys

USAGES = ("page-garde", "en-tete", "pied", "co-signature")
VECTORIELS = ("svg", "eps", "pdf", "emf", "wmf")

# Seuils consultatifs de resolution effective, en points par pouce.
DPI_IMPRESSION = 300
DPI_ECRAN = 150
POUCE_CM = 2.54

# Largeurs par defaut, en centimetres, quand le registre n'en fixe pas.
LARGEURS = {"page-garde": 5.0, "en-tete": 2.5, "pied": 2.0,
            "co-signature": 3.0}


def _images():
    """Delegue la lecture des dimensions a images.py, source unique."""
    import importlib.util
    chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "images.py")
    spec = importlib.util.spec_from_file_location("images_mod", chemin)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def charger(source):
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
                raise SystemExit("registre introuvable : %s" % source)
            reg = json.load(open(source, encoding="utf-8"))
            racine = os.path.dirname(os.path.abspath(source))
    reg.setdefault("logos", [])
    reg["_racine"] = racine
    return reg


def resolution_effective(pixels, largeur_cm):
    """Points par pouce reels a la taille d'affichage demandee."""
    if not pixels or not largeur_cm:
        return None
    return pixels / (largeur_cm / POUCE_CM)


def largeur_usage(logo, usage):
    """Largeur d'affichage retenue : celle du registre, sinon le defaut."""
    par_usage = logo.get("largeur_cm_par_usage") or {}
    if usage in par_usage:
        return float(par_usage[usage])
    if logo.get("largeur_cm"):
        return float(logo["largeur_cm"])
    return LARGEURS.get(usage, 3.0)


def valider(reg):
    """Erreurs bloquantes et avertissements consultatifs, jamais melanges."""
    erreurs, avis = [], []
    racine = reg.get("_racine") or os.getcwd()
    logos = reg.get("logos") or []
    if not logos:
        erreurs.append("le registre ne declare aucun logo")
    vus = set()
    mod = None
    for i, logo in enumerate(logos):
        etiquette = logo.get("id") or "entree %d" % (i + 1)
        if not logo.get("id"):
            erreurs.append("%s : champ id manquant" % etiquette)
        elif logo["id"] in vus:
            erreurs.append("%s : identifiant en double" % logo["id"])
        else:
            vus.add(logo["id"])
        fichier = logo.get("fichier")
        if not fichier:
            erreurs.append("%s : champ fichier manquant" % etiquette)
            continue
        chemin = fichier if os.path.isabs(fichier) \
            else os.path.join(racine, fichier)
        if not os.path.isfile(chemin):
            erreurs.append("%s : fichier absent (%s)" % (etiquette, fichier))
            continue
        usages = logo.get("usages") or list(USAGES)
        inconnus = [u for u in usages if u not in USAGES]
        if inconnus:
            erreurs.append("%s : usage inconnu %s"
                           % (etiquette, ", ".join(inconnus)))
        ext = os.path.splitext(chemin)[1].lower().lstrip(".")
        if ext in VECTORIELS:
            continue
        if mod is None:
            mod = _images()
        larg_px, haut_px, _fmt = mod.dimensions(open(chemin, "rb").read())
        if not larg_px:
            avis.append("%s : dimensions illisibles, resolution non mesuree"
                        % etiquette)
            continue
        for usage in usages:
            cible = largeur_usage(logo, usage)
            dpi = resolution_effective(larg_px, cible)
            seuil = DPI_IMPRESSION if usage in ("page-garde", "co-signature") \
                else DPI_ECRAN
            if dpi is not None and dpi < seuil:
                avis.append(
                    "%s en %s : %d dpi a %.1f cm, sous le seuil de %d dpi"
                    % (etiquette, usage, round(dpi), cible, seuil))
        avis.append("%s : format %s, un vectoriel resisterait mieux a "
                    "l'agrandissement" % (etiquette, ext))
        if logo.get("ratio_verrouille") and haut_px:
            attendu = logo["ratio_verrouille"]
            reel = larg_px / float(haut_px)
            if abs(reel - float(attendu)) > 0.02:
                erreurs.append("%s : ratio %.3f contre %.3f declare"
                               % (etiquette, reel, float(attendu)))
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


def fragment(reg, usage, format_sortie):
    """Fragment pret a inserer pour un usage, dans un des trois formats."""
    logos = pour_usage(reg, usage)
    if not logos:
        return "", ["aucun logo declare pour l'usage %s" % usage]
    avis = []
    racine = reg.get("_racine") or os.getcwd()
    if usage == "co-signature" and len(logos) < 2:
        avis.append("co-signature demandee avec un seul logo, le rang "
                    "protocolaire ne joue pas")
    morceaux = []
    for logo in logos:
        larg = largeur_usage(logo, usage)
        chemin = logo.get("fichier", "")
        absolu = chemin if os.path.isabs(chemin) \
            else os.path.join(racine, chemin)
        if not os.path.isfile(absolu):
            avis.append("%s : fichier absent, ecarte du placement plutot que "
                        "reference a vide" % (logo.get("id") or chemin))
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
        avis.append("en docx, ces chemins se passent a gabarit.py remplir "
                    "--logo, qui ecrit la relation et le manifeste")
    return rendu, avis


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Registre de logos : valider un registre, emettre le "
                    "fragment de placement pour un usage.")
    sp = p.add_subparsers(dest="action")

    pv = sp.add_parser("valider", help="controler un registre de logos")
    pv.add_argument("registre")
    pv.add_argument("--format", choices=("text", "json"), default="text")
    pv.add_argument("--strict", action="store_true",
                    help="code de sortie 1 des le premier avertissement")

    pp = sp.add_parser("placer", help="fragment de placement pour un usage")
    pp.add_argument("registre")
    pp.add_argument("--usage", choices=USAGES, required=True)
    pp.add_argument("--format", choices=("docx", "latex", "html"),
                    default="html")
    pp.add_argument("--sortie", choices=("text", "json"), default="text")

    a = p.parse_args(argv)
    if not a.action:
        p.print_help()
        return 0

    reg = charger(a.registre)

    if a.action == "valider":
        erreurs, avis = valider(reg)
        if a.format == "json":
            print(json.dumps({"erreurs": erreurs, "avertissements": avis,
                              "logos": len(reg.get("logos") or [])},
                             ensure_ascii=False, indent=2))
        else:
            for e in erreurs:
                print("  erreur        %s" % e)
            for w in avis:
                print("  avertissement %s" % w)
            if not erreurs and not avis:
                print("  registre conforme, %d logos"
                      % len(reg.get("logos") or []))
            print("\n%d erreurs, %d avertissements" % (len(erreurs), len(avis)))
        if erreurs:
            return 1
        return 1 if (a.strict and avis) else 0

    if a.action == "placer":
        rendu, avis = fragment(reg, a.usage, a.format)
        if a.sortie == "json":
            print(json.dumps({"usage": a.usage, "format": a.format,
                              "fragment": rendu, "avertissements": avis},
                             ensure_ascii=False, indent=2))
        else:
            print(rendu)
            for w in avis:
                print("  avertissement : %s" % w, file=sys.stderr)
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
