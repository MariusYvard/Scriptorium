---
name: atelier
description: >
  Point d'entrée d'un projet d'écrit : orchestration de bout en bout, cadrage du sujet et mémoire de projet entre sessions. Trois sous-commandes. piloter : produire un document complet de A à Z (cadrage, sourcing, rédaction, révision, finalisation) quand l'utilisateur dit "produis un rapport complet", "rédige de A à Z", "prends en charge tout l'écrit". cadrer : délimiter le sujet, formuler la problématique en question fermée, choisir le genre, bâtir le plan quand il dit "cadre mon rapport", "par où commencer", "quel plan", "formule ma problématique". projet : sauvegarder ou recharger le contexte (brief, charte, glossaire, sources, plan) quand il dit "charge mon projet", "reprends le projet", "où en étais-je". Sert le chercheur, l'ingénieur et l'analyste géopolitique.
metadata:
  version: "0.6.4"
---

# Atelier (piloter, cadrer, projet)

Point d'entrée d'un projet d'écrit. Cette compétence cadre le sujet, garde le contexte entre les sessions et orchestre la production complète. Elle ne réécrit pas la méthode de chaque étape, elle route vers la bonne action et tient la cohérence d'ensemble.

## Sous-commandes

Si une action est passée en argument (par exemple `cadrer`), suivre directement sa section. Sinon, déduire l'action de la demande. Charger le fichier de référence indiqué, et lui seul, pour ne pas saturer le contexte.

- piloter : produire un document de A à Z. Charger `references/piloter.md`. Enchaîne cadrage, sourcing, rédaction, révision et finalisation en s'appuyant sur `produire`, `controler` et `livrer`.
- cadrer : délimiter le sujet, formuler la problématique, choisir le genre, bâtir le plan. Charger `references/cadrer.md`.
- projet : sauvegarder ou recharger le contexte du projet (`projet.json`). Charger `references/projet.md`.

## Trois publics

Le plugin sert le chercheur (rapport scientifique, article, revue de littérature), l'ingénieur (long rapport technique, étude de cas, équations) et l'analyste géopolitique (analyse stratégique, prospective). Le genre retenu au cadrage oriente la chaîne, la méthode et le style maison ne changent pas.

## Router vers une seule action

Si la demande ne porte que sur une étape ("trouve des sources", "révise ce brouillon"), ne pas lancer tout le pipeline : charger directement la compétence concernée (`produire`, `controler`, `livrer`). L'action piloter sert quand l'utilisateur veut un livrable abouti à partir d'un sujet.

## Mémoire de projet

Au démarrage, si `projet.json` existe dans le dossier de travail, le recharger (action projet) pour reprendre le genre, la problématique, la charte et le plan sans les redemander. Sinon, l'initialiser au cadrage.

## Règles

1. Respecter le style maison par défaut (voir `produire`, action style) sur tout le document.
2. Ne jamais inventer une source ni un chiffre. Une affirmation sans preuve est affaiblie ou retirée.
3. Garder la terminologie stable d'un bout à l'autre.
4. Tenir le périmètre validé au cadrage. Toute donnée hors démonstration part en encadré ou en annexe.
5. Échouer bruyamment : si une étape n'aboutit pas, le dire et nommer ce qui bloque, plutôt que de livrer un document incomplet présenté comme terminé.
