---
name: schematiser
description: >
  Génère des figures stratégiques en SVG (SWOT, matrice BCG, matrice d'Ansoff, PESTEL, chaîne de valeur), porte un regard critique sur chaque figure et l'insère titrée et sourcée. À utiliser quand l'utilisateur demande "génère le schéma", "fais un SWOT", "matrice BCG", "matrice d'Ansoff", "diagramme PESTEL", "chaîne de valeur", "schématise", "une figure pour" ou veut illustrer une analyse.
metadata:
  version: "0.1.0"
---

# Schématiser (figures stratégiques et regard critique)

Produire des figures sobres, justes et autonomes, puis les passer au crible avant insertion. Une figure est du contenu, pas de la décoration. Elle se comprend sans le texte.

## 1. Préparer les données

Structurer le contenu de la figure en JSON, selon le type. Voir `references/figures-catalogue.md` pour les formats exacts. Exemple SWOT :

```
{"forces":[...],"faiblesses":[...],"opportunites":[...],"menaces":[...]}
```

Chaque entrée est courte (moins de 90 caractères) et factuelle. Une case de figure se lit d'un coup d'oeil, pas en paragraphe.

## 2. Porter le regard critique déterministe

Avant de produire le SVG, lancer l'audit. Il relève les défauts structurels : cases vides, surcharge, déséquilibre, valeurs hors bornes, points non étiquetés.

```
echo 'DONNEES_JSON' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/figures.py TYPE --data - --audit
```

Corriger les défauts signalés avant de rendre la figure. Une case vide ou une échelle faussée discrédite la figure entière.

## 3. Produire le SVG

```
echo 'DONNEES_JSON' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/figures.py TYPE --data - --out figure.svg --title "Titre"
```

TYPE : `swot`, `bcg`, `ansoff`, `pestel`, `chaine-valeur`. Le SVG est portable. Pour l'insérer dans un document Word, le convertir en PNG avec l'outil disponible.

Si une charte graphique existe (`charte-graphique.json` dans le dossier de travail, voir la compétence `charte-graphique`), l'ajouter avec `--theme charte-graphique.json`. La figure suit alors l'identité visuelle : couleurs, police, filet d'accent, filigrane. Toutes les figures d'un même document partagent la charte.

## 4. Appliquer le regard critique qualitatif

L'audit déterministe ne voit pas tout. Compléter par une lecture humaine, à l'oeil, sur cinq points.

1. Honnêteté des échelles : les axes partent-ils de zéro, les tailles de bulles sont-elles proportionnelles, une échelle tronquée exagère-t-elle un écart ?
2. Autonomie : la figure se comprend-elle sans le texte ? Titre clair, axes nommés, unités présentes, source citée.
3. Justesse du placement : dans une matrice, chaque élément est-il dans le bon quadrant au regard de ses valeurs réelles ?
4. Sens porté par autre chose que la couleur : un daltonien lit-il la figure ? La couleur ne doit pas être le seul code.
5. Sobriété : la figure dit-elle une chose, sans surcharge ni ornement inutile. Si une case déborde, résumer.

Voir la liste complète dans `references/figures-catalogue.md`.

## 5. Insérer

Numéroter la figure, lui donner un titre et citer sa source. La placer près du passage qu'elle illustre. Renvoyer à elle dans le texte (« voir figure 2 »).

## Format de sortie

Le fichier SVG (ou PNG), le rapport d'audit déterministe, et la note de regard critique qualitatif sur les cinq points. Si la figure illustre une affirmation, vérifier que la donnée de la figure correspond à la carte preuve-affirmation.

## Règles

1. Pas de figure à case vide ni à échelle faussée.
2. Chaque figure est autonome : titre, axes, unités, source.
3. La couleur n'est jamais le seul porteur de sens.
4. Une figure, un message. Résumer ce qui déborde.
5. La donnée d'une figure est sourcée comme une affirmation du texte.
