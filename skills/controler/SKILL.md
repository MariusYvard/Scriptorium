---
name: controler
description: >
  Éprouve, contrôle et corrige un écrit avant publication. Six sous-commandes. revue : revue adversariale et contrôle qualité (carte preuve-affirmation, sévérité, verdict, auto-revue cinq dimensions) "révise mon texte", "ce texte est-il prêt", "critique mon écrit". contredire : contradiction la plus forte d'une thèse, modèle de Toulmin, points de rupture "joue l'avocat du diable", "conteste ma thèse", "où est la faille". consensus : vote de trois agents ancré sur le scorecard, profils de discipline "revue par consensus", "double validation". humaniser : détecter et corriger l'empreinte d'un texte généré "ça sonne IA", "enlève les tics d'écriture". audit : noter un PDF ou Word existant (scorecard, contrôles) "audite ce document", "note ce rapport". relecteurs : réponse point par point aux relecteurs et version en modifications suivies. Sert le chercheur, l'ingénieur et l'analyste géopolitique.
metadata:
  version: "0.6.6"
---

# Contrôler (réviser, contredire, valider, humaniser, auditer)

Éprouve et corrige un écrit avant publication. Lire en lecteur sceptique, pas en auteur bienveillant : l'auteur connaît son texte de l'intérieur, le correcteur le découvre.

## Sous-commandes

Si une action est passée en argument (par exemple `audit`), suivre directement sa section. Sinon, déduire l'action de la demande. Charger le fichier de référence indiqué.

- revue : revue adversariale et contrôle qualité complet (cinq dimensions, sévérité, verdict). Charger `references/revue.md`.
- contredire : construire la contradiction la plus forte d'une thèse (modèle de Toulmin, points de rupture). Charger `references/contredire.md`.
- consensus : revue par vote de trois agents, ancrée sur le scorecard, calibrée par profil de discipline. Charger `references/consensus.md`.
- humaniser : détecter et corriger l'empreinte d'un texte généré. Charger `references/humaniser.md`.
- audit : auditer un document déjà rédigé (PDF, Word, Markdown), extraction puis scorecard. Charger `references/audit.md`.
- relecteurs : réponse point par point aux relecteurs et version en modifications suivies. Charger `references/relecteurs.md`.

## Contrôles déterministes d'abord

Avant toute lecture de fond, lancer les scripts sur le texte. Ils attrapent mécaniquement ce qu'un modèle juge mal et libèrent la revue pour le fond. Audit consolidé en une commande :

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit-doc.py FICHIER
```

Détail axe par axe : `lint-style.py`, `readability.py`, `verify-sources.py`, `traceability.py`, `terminology.py`, `numbers.py`, `scorecard.py`, `ai-fingerprint.py`, `coherence.py`, `tables.py audit`, `plan-check.py`. Traiter les constats critiques avant la revue de fond.

## Délégation

Pour un contrôle complet et structuré, déléguer à l'agent `controle-qualite` via l'outil Task. Pour une contradiction de la thèse centrale, déléguer à l'agent `contradicteur`. Pour la vérification factuelle, déléguer à l'agent `verificateur-faits`. L'action consensus fait voter ces agents ensemble.

## Trois publics

Les seuils de rigueur se calibrent par profil de discipline (action consensus) : sciences dures, sciences sociales, ingénierie, analyse géopolitique. Le scorecard et la grille de revue restent les mêmes, les seuils s'ajustent.

## Règles

1. La cohérence preuve-affirmation est une contrainte dure, pas une préférence.
2. Classer les constats par sévérité (critique, majeur, mineur), corriger les critiques avant toute finalisation.
3. Chaque constat cite sa règle. Chaque question ouverte porte une recommandation.
4. Verdict explicite et honnête. "Prêt" est faux si un contrôle a été sauté en silence.
