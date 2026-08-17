---
name: controler
description: >
  Éprouve, contrôle et corrige un écrit avant publication. Six sous-commandes. revue : revue adversariale et contrôle qualité (carte preuve-affirmation, sévérité, verdict, lettre de décision) "révise mon texte", "ce texte est-il prêt", "critique mon écrit". contredire : contradiction la plus forte d'une thèse, modèle de Toulmin, discipline de concession, points de rupture "joue l'avocat du diable", "conteste ma thèse", "où est la faille". consensus : vote de trois agents sur contrat de notation préenregistré, comparaison par paires, ancré sur le scorecard, profils de discipline "revue par consensus", "double validation". humaniser : détecter et corriger l'empreinte d'un texte généré "ça sonne IA", "enlève les tics d'écriture". audit : noter un PDF, un Word ou un deck existant (scorecard, contrôles, originalité), vérifier la conformité à un gabarit imposé, contrôler ce que le fichier trahit de son auteur avant envoi et la déclaration de disponibilité des données avant soumission "audite ce document", "note ce rapport", "est-ce que ça respecte le modèle imposé", "qu'est-ce que ce fichier dit de moi". relecteurs : réponse point par point, registre d'engagements, re-revue avec trajectoire de score. Sert le chercheur, l'ingénieur et l'analyste géopolitique.
metadata:
  version: "0.12.0"
---

# Contrôler (réviser, contredire, valider, humaniser, auditer)

Éprouve et corrige un écrit avant publication. Lire en lecteur sceptique, pas en auteur bienveillant : l'auteur connaît son texte de l'intérieur, le correcteur le découvre.

## Sous-commandes

Si une action est passée en argument (par exemple `audit`), suivre directement sa section. Sinon, déduire l'action de la demande. Charger le fichier de référence indiqué.

- revue : revue adversariale et contrôle qualité complet (huit dimensions, sévérité, verdict). Charger `references/revue.md`. Pour une revue à fort enjeu, charger aussi `references/biais-relecteur.md` (biais, lentilles, calibration de sévérité) et `references/sophismes-causalite.md` (sophismes, biais du chercheur, causalité, statuts épistémiques).
- contredire : construire la contradiction la plus forte d'une thèse (modèle de Toulmin, discipline de concession, points de rupture). Charger `references/contredire.md`.
- consensus : revue par vote de trois agents, chacun engagé sur un contrat de notation préenregistré avant lecture (`references/contrat-notation.md`), ancrée sur le scorecard, calibrée par profil de discipline. Pour départager deux versions, comparaison par paires anti-biais de position. Charger `references/consensus.md`.
- humaniser : détecter et corriger l'empreinte d'un texte généré. Charger `references/humaniser.md`.
- audit : auditer un document déjà rédigé (PDF, Word, Markdown), extraction puis scorecard ; un deck exporté en PDF s'audite avec `scripts/check-presentation.py`. Quand un gabarit est imposé, la conformité de forme se contrôle en plus du fond : `python3 scripts/gabarit.py comparer gabarit-inventaire.json DOCUMENT.docx` rend un verdict fermé et liste les écarts. Avant tout envoi hors de l'organisation, contrôler ce que le fichier trahit de son auteur : `python3 scripts/check-fuites.py LIVRABLE.docx --auteur "Prenom Nom"` inventorie propriétés de document, résidus de travail, chemins locaux et, pour un PDF, les états antérieurs laissés par une mise à jour incrémentale. Avant soumission d'un manuscrit qui promet des données ou du code, contrôler la déclaration de disponibilité : `python3 scripts/check-disponibilite.py MANUSCRIT.md` rend un verdict fermé sur cinq valeurs et signale un régime déclaré sans la preuve qu'il exige. Charger `references/audit.md`. Pour un contrôle d'originalité, charger aussi `references/plagiat.md`.
- relecteurs : réponse point par point aux relecteurs, registre d'engagements, re-revue et version en modifications suivies. Charger `references/relecteurs.md`.

## Contrôles déterministes d'abord

Avant toute lecture de fond, lancer les scripts sur le texte. Ils attrapent mécaniquement ce qu'un modèle juge mal et libèrent la revue pour le fond. Audit consolidé en une commande :

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit-doc.py FICHIER
```

Détail axe par axe : `lint-style.py`, `readability.py`, `verify-sources.py`, `traceability.py`, `terminology.py`, `numbers.py`, `scorecard.py` (plancher par axe, poids optionnels, seuil par type de document, trajectoire entre deux revues), `ai-fingerprint.py`, `coherence.py`, `check-temporel.py` (défaillances chronologiques), `check-presentation.py` (deck PDF), `gabarit.py comparer` (conformité à un gabarit imposé), `check-fuites.py` (ce qu'un livrable trahit de son auteur avant envoi), `check-disponibilite.py` (déclaration de disponibilité des données et du code avant soumission), `tables.py audit`, `plan-check.py`. Traiter les constats critiques avant la revue de fond.

## Références transverses

`references/severite.md` fixe la définition unique de critique, majeur, mineur et signal, les seuils numériques partagés, les seuils par type de document (brouillon, rapport, publication) et le taux d'égalité comme signal de grille : les autres références y renvoient plutôt que de redéfinir localement. `references/sante-dialogue.md` (auto-contrôle anti-complaisance) s'applique à tout échange qui dépasse cinq tours. `references/lettre-decision.md` structure la décision finale d'une revue ou d'un consensus à fort enjeu.

## Délégation

Pour un contrôle complet et structuré, déléguer à l'agent `controle-qualite` via l'outil Task. Pour une contradiction de la thèse centrale, déléguer à l'agent `contradicteur`. Pour la vérification factuelle, déléguer à l'agent `verificateur-faits`. L'action consensus fait voter ces agents ensemble, sans qu'aucun ne voie le verdict des autres avant d'avoir rendu le sien.

## Trois publics

Les seuils de rigueur se calibrent par profil de discipline (action consensus) : sciences dures, sciences sociales, ingénierie, analyse géopolitique. Le scorecard et la grille de revue restent les mêmes, les seuils s'ajustent.

## Règles

1. La cohérence preuve-affirmation est une contrainte dure, pas une préférence.
2. Classer les constats par sévérité (voir `references/severite.md`), corriger les critiques avant toute finalisation.
3. Chaque constat cite sa règle. Chaque question ouverte porte une recommandation.
4. Verdict explicite et honnête. "Prêt" est faux si un contrôle a été sauté en silence.
