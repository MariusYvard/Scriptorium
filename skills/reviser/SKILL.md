---
name: reviser
description: >
  Soumet un écrit à une revue adversariale et à un contrôle qualité structuré : carte preuve-affirmation, reverse outlining, auto-revue en cinq dimensions, conformité au style maison, constats classés par sévérité et verdict. À utiliser quand l'utilisateur demande "révise mon texte", "relis ce rapport", "revue adversariale", "vérifie les sources", "ce texte est-il prêt", "critique mon écrit" ou avant de finaliser un document.
metadata:
  version: "0.1.0"
---

# Réviser (revue adversariale et contrôle qualité)

Lire le document en lecteur sceptique, pas en auteur bienveillant. L'auteur connaît son texte de l'intérieur, le correcteur le découvre. La révision sert à combler cet écart et à résoudre chaque risque de rejet avant la version finale.

## Quand déléguer

Pour un contrôle complet et structuré, déléguer à l'agent `controle-qualite` via l'outil Task. Il retourne une liste de contrôle, des constats classés par sévérité et un verdict, chaque constat citant sa règle. Pour une relecture ciblée (un seul axe, une seule section), traiter directement.

## Cinq axes de revue

Examiner le document selon cinq dimensions, chacune avec ses sous-points.

### 1. Contribution et pertinence

Le document répond-il à la problématique posée au cadrage ? Apporte-t-il quelque chose, ou juxtapose-t-il des connaissances ? L'ordre des sections est-il démonstratif, ou pourrait-il s'inverser sans perte ?

### 2. Clarté et fluidité

Chaque paragraphe porte-t-il un seul message, énoncé en première phrase ? La progression connu-inconnu tient-elle, sans saut conceptuel ? Les transitions relient-elles les idées par une relation explicite ? Le rythme des phrases varie-t-il ?

### 3. Preuve et rigueur

Chaque affirmation majeure est-elle étayée par une preuve datée et vérifiée ? La carte preuve-affirmation ne laisse-t-elle aucune affirmation au statut "à sourcer" ? Les affirmations de l'introduction et de la conclusion sont-elles toutes soutenues par le corps ? C'est une contrainte dure : une affirmation non étayée est affaiblie ou retirée.

### 4. Complétude et structure

La structure standard du genre est-elle respectée ? Les sections obligatoires sont-elles présentes (résumé, méthode, limites, bibliographie selon le genre) ? Les figures et tableaux sont-ils autonomes et lisibles ?

### 5. Conformité au style maison

Le texte respecte-t-il les directives strictes ? Vérifier point par point : zéro tiret cadratin, pas de virgule d'Oxford, guillemets et apostrophes droits, lexique banni absent, pas de métadiscours, faits précis, URL sans paramètres de suivi. Voir `references/grille-revue.md`.

## Controles deterministes (avant la lecture)

Avant la lecture humaine, lancer les trois scripts sur le texte. Ils attrapent mecaniquement ce qu'un modele juge mal, et liberent la revue pour le fond.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lint-style.py FICHIER
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/readability.py FICHIER
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify-sources.py FICHIER
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/traceability.py FICHIER
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/terminology.py FICHIER
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/numbers.py FICHIER
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scorecard.py FICHIER
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ai-fingerprint.py FICHIER
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/coherence.py FICHIER
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/tables.py audit FICHIER
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/plan-check.py plan.json FICHIER
```

Pour un audit consolidé en une commande, lancer `audit-doc.py FICHIER` (scorecard, empreinte IA, cohérence, tableaux).

Le linter signale les ecarts de style par severite (code de sortie 1 si un constat critique subsiste). Les metriques chiffrent le rythme (longueur de phrase, ecart-type, indice LIX). Le verificateur nettoie les URL et repere doublons et DOI douteux. La traçabilité contrôle les références orphelines ou pendantes et les appels de figures, la terminologie le glossaire et les sigles, les nombres les pourcentages et les unités. Le scorecard agrège le tout en une note sur 100 (départ 20 par axe, pénalités fixes, calcul montré). Traiter les constats critiques avant la revue de fond. L'empreinte IA mesure les tics d'écriture générée, la cohérence repère les redites et duplications, l'audit de tableaux et la conformité au plan ferment les dernières boucles. Pour une validation à fort enjeu, lancer la compétence `consensus` (vote de trois agents ancré sur le scorecard).

## Revue adversariale

Après les cinq axes, jouer le rôle d'un évaluateur hostile. Lister les questions à plus haut risque de rejet : la preuve la plus faible, l'affirmation la plus exposée, la limite passée sous silence. Résoudre chaque question, ou l'adresser explicitement dans le texte (une limite assumée vaut mieux qu'une faille dissimulée). Pour une contradiction structurée de la thèse centrale, déléguer à l'agent `contradicteur` (modèle de Toulmin, points de rupture par gravité).

## Format de sortie

Reprendre la grille de `references/grille-revue.md`. Structure imposée :

```
Verdict : [Prêt / À réviser / À refondre]

Contrôles :
- Contribution : [Conforme / Non conforme] - [détail]
- Clarté et fluidité : [Conforme / Non conforme] - [détail]
- Preuve et rigueur : [Conforme / Non conforme] - [détail]
- Complétude : [Conforme / Non conforme] - [détail]
- Style maison : [Conforme / Non conforme] - [détail]

Constats classés par sévérité :
1. [Critique] [description] -> Correctif : [recommandation]
2. [Majeur] [description] -> Correctif : [recommandation]
3. [Mineur] [description] -> Correctif : [recommandation]

Ce qui fonctionne :
- [point fort 1]
- [point fort 2]

Questions ouvertes :
- [question] -> Recommandation : [proposition]
```

Tout constat cite la règle ou le critère qu'il invoque. Aucune impasse : chaque question ouverte porte une recommandation. Lister aussi ce qui fonctionne, une critique qui ne voit que les défauts perd en crédibilité.

## Hygiène de relecture

Conseiller, quand c'est possible, de laisser reposer le document avant la dernière passe, ou de le soumettre à un tiers non spécialiste. Une démonstration qui emporte l'adhésion d'un lecteur non averti dès la première lecture est une démonstration solide.

## Règles

1. La cohérence preuve-affirmation est une contrainte dure, pas une préférence.
2. Classer les constats par sévérité (critique, majeur, mineur), corriger les critiques avant toute finalisation.
3. Chaque constat cite sa règle. Chaque question ouverte porte une recommandation.
4. Verdict explicite et honnête. "Prêt" est faux si un contrôle a été sauté en silence.
