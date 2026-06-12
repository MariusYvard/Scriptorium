---
name: produire
description: >
  Produit le contenu d'un document et fixe ses règles d'écriture. Huit sous-commandes. genre : rédiger ou réécrire un texte de haut niveau dans l'un des onze genres (rapport scientifique IMRAD, article, long rapport, analyse stratégique, prospective, étude de cas, note de politique publique, note juridique, cahier des charges, cas clinique, présentation) "rédige un rapport", "écris l'introduction". sourcer : trouver, pondérer et vérifier des sources et des citations "trouve des sources", "vérifie ce fait". revue-litterature : synthèse multi-sources, PRISMA. figure : schéma SVG (SWOT, PESTEL, BCG, chaîne de valeur). tableau : générer ou auditer un tableau. equation : LaTeX, unités SI. style : style maison, charte éditoriale. charte : identité visuelle. image : extraire et replacer les images d'un PDF, Word ou PowerPoint "récupère les images de ce PDF". Sert le chercheur, l'ingénieur, l'analyste géopolitique, le juriste, le soignant, le consultant, le communicant et l'étudiant.
metadata:
  version: "0.6.1"
---

# Produire (rédiger, sourcer, illustrer, styler)

Produit le contenu d'un document et fixe sa forme. Le genre détermine la structure, la méthodologie transverse détermine la mécanique de chaque paragraphe, le style maison et la charte graphique fixent l'apparence.

## Sous-commandes

Si une action est passée en argument (par exemple `figure`), suivre directement sa section. Sinon, déduire l'action de la demande. Charger le fichier de référence indiqué, et lui seul.

- genre : rédiger ou réécrire un texte. Charger `references/redaction.md` (moteur unifié), puis le playbook du genre voulu dans `references/genre-*.md`, et `references/methodologie-transverse.md` pour la mécanique commune.
- sourcer : trouver, pondérer et vérifier les sources, formater les citations, bâtir la carte preuve-affirmation. Charger `references/sourcer.md`.
- revue-litterature : synthétiser plusieurs sources en une revue unique (tableau de preuves, schéma PRISMA). Charger `references/revue-litterature.md`.
- figure : générer un schéma stratégique en SVG. Charger `references/figure.md`.
- tableau : générer un tableau autonome ou auditer les tableaux d'un document. Charger `references/tableau.md`.
- equation : poser des équations en LaTeX, contrôler unités SI et chiffres significatifs. Charger `references/equation.md`.
- style : générer, appliquer ou faire respecter la charte éditoriale. Charger `references/style.md`.
- charte : définir, appliquer ou valider une identité visuelle sur le texte et les figures. Charger `references/charte.md`.
- image : extraire les images d'un PDF ou d'un document Office (Word, PowerPoint, Excel), les cataloguer et les préparer au placement. Charger `references/image.md`.

## Genres et publics

Onze genres couvrent huit publics. Le chercheur écrit un rapport scientifique (IMRAD), un article ou une revue de littérature. L'ingénieur écrit un long rapport, une étude de cas, un cahier des charges ou une spécification, souvent avec équations et tableaux. L'analyste géopolitique écrit une analyse stratégique (PESTEL, jeu d'acteurs Mactor) ou une note de politique publique. Le juriste écrit une note ou une consultation (méthode IRAC). Le professionnel de santé écrit un cas clinique ou un protocole (CONSORT, PRISMA, STROBE). Le consultant et le dirigeant écrivent un long rapport décisionnel ou une étude de cas. Le communicant écrit un article ou un livre blanc. L'étudiant écrit un mémoire ou une présentation. Charger le playbook du genre dans `references/genre-*.md`. La méthode et le style maison ne changent pas, seuls la structure du genre et les exemples s'adaptent.

## Préalables

Rédiger sans plan ni preuve produit du remplissage. Si le plan n'est pas posé, lancer d'abord `atelier` (cadrer). Si les preuves ne sont pas réunies, lancer d'abord l'action sourcer.

## Délégation

Pour un document de plus de cinq pages ou à sections denses, déléguer la rédaction à l'agent `redacteur` via l'outil Task, section par section. Lui transmettre le plan, les preuves, le playbook de genre et le style maison. L'agent retourne le texte, il n'écrit pas de fichier.

## Scripts déterministes

Les actions s'appuient sur le dossier `scripts/` : `figures.py` pour figure, `tables.py` pour tableau, `citations.py` et `verify-sources.py` pour sourcer, `theme.py` pour charte, `images.py` pour image, `lint-style.py` et `readability.py` pour style. Voir `scripts/README.md`.

## Règles

1. Garder la terminologie stable. Définir un terme à sa première occurrence.
2. Ne pas écrire un paragraphe que les preuves ne soutiennent pas. Affaiblir ou retirer.
3. Respecter le périmètre validé au cadrage.
4. Traiter figures et tableaux comme du contenu, pas de la décoration. Un tableau est autonome et lisible.
5. À la fin d'une passe de rédaction, enchaîner vers `controler` (revue).
