---
name: produire
description: >
  Produit le contenu d'un document et fixe ses règles d'écriture. Neuf sous-commandes. genre : rédiger ou réécrire un texte de haut niveau parmi vingt-cinq genres sourcés (académique, professionnel, stratégique, commercial, juridique, technique, financier, public, médical, communication) "rédige un rapport", "écris l'introduction". sourcer : trouver, pondérer, trianguler et vérifier sources et citations "trouve des sources", "vérifie ce fait". revue-litterature : synthèse multi-sources, PRISMA. veille : surveillance documentaire, rétractations "mets en place une veille". figure : schéma SVG (SWOT, PESTEL, BCG). tableau : générer ou auditer un tableau. equation : LaTeX, unités SI. style : style maison, charte éditoriale, calibrage d'un style personnel. charte : identité visuelle. image : extraire et replacer les images d'un PDF, Word ou PowerPoint. Sert le chercheur, l'ingénieur, l'analyste géopolitique, le juriste, le soignant, le financier, le consultant, le communicant, l'étudiant et l'agent public.
metadata:
  version: "0.7.0"
---

# Produire (rédiger, sourcer, illustrer, styler)

Produit le contenu d'un document et fixe sa forme. Le genre détermine la structure, la méthodologie transverse détermine la mécanique de chaque paragraphe, le style maison et la charte graphique fixent l'apparence.

## Sous-commandes

Si une action est passée en argument (par exemple `figure`), suivre directement sa section. Sinon, déduire l'action de la demande. Charger le fichier de référence indiqué, et lui seul.

- genre : rédiger ou réécrire un texte. Charger `references/redaction.md` (moteur unifié), puis le playbook du genre voulu dans `references/genre-*.md`, et `references/methodologie-transverse.md` pour la mécanique commune.
- sourcer : trouver, pondérer et vérifier les sources, formater les citations, bâtir la carte preuve-affirmation. Charger `references/sourcer.md`. Il renvoie vers `references/integrite-sources.md` (triangulation, citations fabriquées), `references/hierarchie-preuve.md` (niveaux de preuve, fiche A-F) et `references/corpus-utilisateur.md` (bibliothèque fournie) selon le besoin.
- revue-litterature : synthétiser plusieurs sources en une revue unique (tableau de preuves, schéma PRISMA, discipline de synthèse). Charger `references/revue-litterature.md`.
- veille : mettre en place une surveillance documentaire périodique sur un sujet (requêtes arXiv, PubMed, Google Scholar, digest, contrôle des rétractations). Charger `references/veille.md`.
- figure : générer un schéma stratégique en SVG et vérifier son rendu avant livraison. Charger `references/figure.md`.
- tableau : générer un tableau autonome ou auditer les tableaux d'un document. Charger `references/tableau.md`.
- equation : poser des équations en LaTeX, contrôler unités SI et chiffres significatifs. Charger `references/equation.md`.
- style : générer, appliquer ou faire respecter la charte éditoriale, calibrer un style personnel sur des échantillons fournis. Charger `references/style.md`.
- charte : définir, appliquer ou valider une identité visuelle sur le texte et les figures. Charger `references/charte.md`.
- image : extraire les images d'un PDF ou d'un document Office (Word, PowerPoint, Excel), les cataloguer et les préparer au placement. Charger `references/image.md`.

## Genres et publics

Vingt-cinq genres couvrent quatorze publics, et chaque playbook (`references/genre-*.md`) porte ses sources.

- Académique et recherche : rapport scientifique (IMRAD), article, revue de littérature, demande de financement, dissertation, pour le chercheur, l'enseignant et l'étudiant.
- Entreprise et conseil : long rapport, analyse stratégique, prospective, étude de cas, business plan, étude de marché, proposition commerciale, pitch, pour le consultant, le dirigeant et l'entrepreneur.
- Technique : cahier des charges, documentation technique, rapport d'incident et post-mortem, pour l'ingénieur, le développeur et le chef de projet.
- Finance : note d'analyse financière et mémo d'investissement, pour l'analyste financier.
- Public et droit : note de politique publique, rapport d'évaluation, note juridique, conclusions contentieuses, contrat, pour l'analyste géopolitique, l'agent public, le juriste et l'avocat.
- Santé : cas clinique et protocole, pour le professionnel de santé.
- Communication : livre blanc, discours, présentation, pour le communicant et l'orateur.

La méthode et le style maison ne changent pas, seuls la structure du genre et les exemples s'adaptent.

## Références transverses

`references/credit-divulgation.md` (déclaration de contribution CRediT, financement, usage de l'IA) se charge quand le document part vers une publication qui l'exige. `references/contrat-mission.md` (contrat rédacteur-évaluateur, critères d'acceptation posés avant d'écrire) se charge pour une mission à exigences formelles. `references/discipline-synthese.md` (anti-patterns, matrice source x thème) sert toute synthèse multi-sources.

## Préalables

Rédiger sans plan ni preuve produit du remplissage. Si le plan n'est pas posé, lancer d'abord `atelier` (cadrer). Si les preuves ne sont pas réunies, lancer d'abord l'action sourcer.

## Délégation

Pour un document de plus de cinq pages ou à sections denses, déléguer la rédaction à l'agent `redacteur` via l'outil Task, section par section. Lui transmettre le plan, les preuves, le playbook de genre et le style maison. L'agent retourne le texte, il n'écrit pas de fichier.

## Scripts déterministes

Les actions s'appuient sur le dossier `scripts/` : `figures.py` pour figure, `tables.py` pour tableau, `citations.py` (cinq formats, ancres par citation) et `verify-sources.py` (triangulation en option) pour sourcer, `theme.py` pour charte, `images.py` pour image, `lint-style.py` et `readability.py` pour style. Voir `scripts/README.md`.

## Règles

1. Garder la terminologie stable. Définir un terme à sa première occurrence.
2. Ne pas écrire un paragraphe que les preuves ne soutiennent pas. Affaiblir ou retirer.
3. Respecter le périmètre validé au cadrage.
4. Traiter figures et tableaux comme du contenu, pas de la décoration. Un tableau est autonome et lisible.
5. À la fin d'une passe de rédaction, enchaîner vers `controler` (revue).
