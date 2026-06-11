---
name: charte-graphique
description: >
  Définit, applique ou valide une charte graphique (identité visuelle) sur tout un document, texte et figures comprises : couleurs, polices, accent, filigrane, rayon. Contrôle le contraste WCAG pour refuser une charte illisible. À utiliser quand l'utilisateur demande "applique ma charte graphique", "respecte la charte", "utilise les couleurs de la marque", "mets l'identité visuelle", "thème des figures", "police de la marque" ou fournit des couleurs, une police ou un logo à suivre.
metadata:
  version: "0.1.0"
---

# Charte graphique (identité visuelle)

Faire suivre une identité visuelle donnée sur l'ensemble d'un document. La charte fixe les couleurs, les polices, l'accent, un filigrane et le rayon des angles. Elle s'applique aux figures par le générateur et aux documents par la mise en forme, de façon cohérente d'un bout à l'autre.

La charte est un fichier JSON. Format complet dans `references/charte-graphique-format.md`, exemple dans `assets/charte-graphique.exemple.json`.

## Mode 1 : définir la charte

Construire le JSON à partir de ce que fournit l'utilisateur.

- Couleurs données directement : les placer dans `couleurs` (encre, trait, fond, accent, palette de quatre fonds).
- Charte fournie dans un document de marque (PDF, page, capture) : en extraire les codes hexadécimaux, la police et le logo, puis remplir le JSON.
- Rien de précis : partir de l'exemple et proposer, en signalant que ce sont des valeurs par défaut.

Enregistrer la charte sous `charte-graphique.json` dans le dossier de travail. Les compétences `schematiser` et `finaliser` la trouvent là par convention.

## Mode 2 : appliquer la charte

Valider d'abord, puis appliquer.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/theme.py charte-graphique.json
```

- Figures : passer la charte au générateur.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/figures.py TYPE --theme charte-graphique.json --out figure.svg --title "Titre"
```

Toutes les couleurs, la police, le filet d'accent sous le titre et le filigrane suivent la charte.

- Documents : la compétence `finaliser` lit la charte et applique la police des titres, la couleur d'encre et l'accent aux titres, filets, légendes et liens. Le corps reste lisible (la charte ne change pas le fond du texte courant).

Appliquer la même charte à toutes les figures et à la mise en forme, pour une cohérence visuelle complète.

## Mode 3 : valider la charte

Avant tout usage, contrôler la charte.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/theme.py charte-graphique.json
```

Le script signale une couleur mal formée (erreur) et un contraste insuffisant entre l'encre et le fond, ou l'encre et un fond de palette (avertissement sous 4,5:1). Une charte en erreur n'est pas utilisée telle quelle. Un avertissement de contraste se corrige en assombrissant l'encre ou en éclaircissant le fond.

## Convention de dossier

Si `charte-graphique.json` existe dans le dossier de travail, l'utiliser par défaut pour toutes les figures et la mise en forme, sans le redemander. Sinon, travailler avec la charte sobre par défaut, et proposer d'en définir une.

## Format de sortie

- Mode définir : le fichier `charte-graphique.json`, plus un résumé des choix (couleurs, police, accent).
- Mode appliquer : les figures thémées et le document mis en forme à la charte.
- Mode valider : le rapport du script (erreurs, avertissements de contraste) avec la correction proposée.

## Ce que la charte couvre

Couleurs, polices, graisse des titres, accent, fond, rayon, filigrane texte. Un logo en image s'insère séparément dans le document. Les illustrations sur mesure et les grilles complexes restent un travail manuel que la charte cadre sans l'automatiser.

## Règles

1. Valider la charte avant de l'appliquer. Une charte en erreur n'est pas utilisée.
2. Un avertissement de contraste se corrige, il ne s'ignore pas.
3. La même charte sur toutes les figures et la mise en forme. Pas de figure hors charte dans un document à charte.
4. La charte fixe la forme visuelle, jamais le fond ni les faits.
5. Le style maison éditorial (voir `style-maison`) reste appliqué en plus de la charte graphique : l'un règle les mots, l'autre l'image.
