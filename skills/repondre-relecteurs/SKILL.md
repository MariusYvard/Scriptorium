---
name: repondre-relecteurs
description: >
  Produit une réponse point par point aux relecteurs et une version révisée en modifications suivies, à partir des commentaires reçus et de deux versions du manuscrit. À utiliser quand l'utilisateur demande "réponse aux relecteurs", "response to reviewers", "répondre aux commentaires", "révisions suivies", "lettre de révision", "journal des modifications" ou prépare une resoumission.
metadata:
  version: "0.1.0"
---

# Répondre aux relecteurs

Préparer une resoumission convaincante : une réponse courtoise et précise à chaque commentaire, et une version révisée dont les changements sont traçables. Le flux suit la publication scientifique.

## 1. Recueillir les entrées

Réunir les commentaires des relecteurs (numérotés par relecteur), la version soumise et la version révisée du manuscrit. Si la version révisée n'existe pas encore, la produire d'abord avec `rediger` et `reviser`.

## 2. Construire le journal des modifications

Comparer les deux versions pour objectiver les changements.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/diff-versions.py soumis.md revise.md
```

Le script liste les sections ajoutées, supprimées et modifiées, avec le nombre de mots changés. Ce journal alimente les renvois précis de la réponse.

## 3. Répondre point par point

Pour chaque commentaire, un bloc.

```
Commentaire R1.3 : [citation exacte du relecteur]
Réponse : [ce qui a été modifié, ou la justification si le point est écarté]
Modification : [section, paragraphe, et nature du changement]
```

Citer le commentaire mot pour mot. Indiquer le changement réel et son emplacement. Quand un point est écarté, le justifier avec courtoisie et preuve, sans esquive. Remercier sobrement, sans flagornerie.

## 4. Produire la version en modifications suivies

Pour un livrable Word avec corrections visibles, passer par la compétence `finaliser` et le skill `docx` : insérer les changements en révisions suivies (ajouts et suppressions marqués) ou en commentaires, pour que le relecteur accepte ou refuse chaque modification. Garder une version propre en parallèle.

## 5. Contrôler

Repasser la version révisée par `reviser` et le scorecard déterministe. Un changement demandé par un relecteur ne doit pas en casser un autre ni introduire un écart de style.

## Format de sortie

1. La lettre de réponse, point par point, par relecteur.
2. Le journal des modifications (sorties de `diff-versions.py`).
3. La version révisée en modifications suivies, plus une version propre.

## Règles

1. Citer chaque commentaire mot pour mot avant d'y répondre.
2. Toute réponse renvoie à un changement précis et localisé, ou à une justification étayée.
3. Aucune impasse : chaque commentaire reçoit une réponse.
4. Courtoisie sobre, jamais de flagornerie ni de polémique.
5. La version révisée respecte le style maison et passe le scorecard.
