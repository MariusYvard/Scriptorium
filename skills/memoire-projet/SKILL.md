---
name: memoire-projet
description: >
  Conserve et recharge le contexte d'un projet d'écrit entre les sessions : brief de cadrage, charte, glossaire, bibliothèque de sources, profil de discipline et plan, dans un fichier projet.json. À utiliser quand l'utilisateur demande "charge mon projet", "reprends le projet", "où en étais-je", "sauvegarde le contexte", "mémoire de projet" ou recommence un document déjà cadré.
metadata:
  version: "0.1.0"
---

# Mémoire de projet

Éviter de repartir de zéro. Un fichier `projet.json` dans le dossier de travail conserve ce qui définit le projet, rechargé au début de chaque session.

## 1. Initialiser

Au lancement d'un nouveau document, créer la mémoire de projet.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py init
```

Le squelette contient : titre, genre, problématique, brief, chemin de la charte, chemin du profil de discipline, chemin du plan, glossaire, sources, notes.

## 2. Remplir au fil du cadrage

Quand `cadrer` fixe le genre, la problématique et le plan, les enregistrer. Quand `sourcer` réunit des références, les ajouter. Quand `style-maison` ou `charte-graphique` produisent une charte, en noter le chemin.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py set genre '"analyse-strategique"'
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py set problematique '"..."'
```

## 3. Recharger au début de session

Si `projet.json` existe, le lire pour retrouver le contexte sans le redemander.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py show
```

Reprendre le genre, la problématique, la charte, le profil et le plan tels quels. La session continue le travail au lieu de le redécouvrir.

## 4. Synchroniser avec Dream (optionnel)

Si la mémoire Dream est disponible, y stocker les décisions de cadrage et la charte comme événements, pour une persistance au delà du dossier de travail. Cette synchronisation est optionnelle, `projet.json` reste la source dans le dossier.

## Format de sortie

L'état du projet rechargé (genre, problématique, charte, profil, plan, nombre de sources) et la confirmation de ce qui a été repris.

## Règles

1. `projet.json` est la source dans le dossier de travail.
2. Ne pas redemander ce que la mémoire de projet contient déjà.
3. Tenir la mémoire à jour à chaque étape (cadrage, sourcing, charte).
4. Ne jamais stocker de secret ni de token dans `projet.json`.
