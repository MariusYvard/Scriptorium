---
name: tableaux
description: >
  Génère des tableaux autonomes à partir d'un CSV ou d'un JSON et audite les tableaux d'un document (cellules vides, colonne numérique sans unité, ligne Total incohérente). À utiliser quand l'utilisateur demande "fais un tableau", "génère un tableau", "tableau à partir de ces données", "audite mes tableaux", "vérifie ce tableau" ou veut présenter des données en tableau.
metadata:
  version: "0.1.0"
---

# Tableaux (génération et audit)

Traiter le tableau comme du contenu, comme la figure. Un tableau est autonome : titre, en-têtes avec unités, source, aucune cellule vide.

## 1. Générer un tableau

À partir d'un CSV ou d'un JSON.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tables.py gen donnees.csv --caption "Titre du tableau" --source "Source datée"
```

Le JSON accepte une liste d'objets, ou la forme `{"columns": [...], "rows": [[...]]}`. Mettre l'unité dans l'en-tête de chaque colonne numérique (par exemple `Ventes (k€)`). Le titre et la source rendent le tableau autonome.

## 2. Auditer les tableaux d'un document

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tables.py audit document.md
```

L'audit signale les cellules vides, les colonnes numériques sans unité dans l'en-tête, et les lignes Total dont la somme ne correspond pas aux composantes. Corriger avant d'insérer.

## 3. Insérer

Numéroter le tableau, lui donner un titre et citer sa source. Le tableau 1 d'un article scientifique présente classiquement les caractéristiques de la population. Renvoyer au tableau dans le texte (« voir tableau 2 »). La traçabilité (`traceability.py`) vérifie que chaque tableau défini est appelé.

## Format de sortie

Le tableau en Markdown (convertible pour Word), ou le rapport d'audit des tableaux existants, avec les corrections proposées.

## Règles

1. Une unité dans l'en-tête de chaque colonne numérique.
2. Aucune cellule vide, un tiret explicite pour une donnée absente.
3. Une ligne Total cohérente avec ses composantes.
4. Titre et source sur chaque tableau, il est autonome.
5. Préférer un tableau à un camembert quand les valeurs comptent plus que les proportions.
