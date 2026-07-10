# Grille de revue adversariale

Référence du contrôle qualité. Huit dimensions, sévérité, verdict, carte preuve-affirmation. À charger pour toute révision structurée.

## Huit dimensions

Les cinq premières dimensions s'appliquent à tout écrit. Les trois dernières (6 à 8) sont des dimensions de revue qualitative, notées dans le rapport de revue au même titre que les cinq premières : elles ne touchent pas au calcul du scorecard mécanique de `scripts/scorecard.py`, qui reste sur ses cinq axes chiffrés (Style, Sources, Traçabilité, Terminologie et nombres, Lisibilité).

### 1. Contribution et pertinence

- Le document répond à la problématique du cadrage.
- Il démontre, il ne juxtapose pas.
- L'ordre des sections est nécessaire, pas interchangeable.

### 2. Clarté et fluidité

- Un paragraphe, un message, en première phrase.
- Progression connu-inconnu sans saut conceptuel.
- Transitions par relation explicite.
- Rythme des phrases varié.

### 3. Preuve et rigueur (contrainte dure)

- Chaque affirmation majeure étayée par une preuve datée et vérifiée.
- Aucune affirmation au statut "à sourcer" en version finale.
- Affirmations de l'introduction et de la conclusion soutenues par le corps.
- Observation distinguée de l'interprétation.
- URL et DOI vérifiés, sans paramètres de suivi.

### 4. Complétude et structure

- Structure standard du genre respectée.
- Sections obligatoires présentes (résumé, méthode, limites, bibliographie selon le genre).
- Figures et tableaux autonomes et lisibles.

### 5. Conformité au style maison

- Zéro tiret cadratin ou demi-cadratin.
- Pas de virgule d'Oxford.
- Guillemets et apostrophes droits, gras rare.
- Lexique banni absent.
- Pas de métadiscours, registre neutre.
- Faits précis, pas de vague.

### 6. Rigueur méthodologique

- La méthode choisie répond à la question posée, pas seulement disponible ou familière à l'auteur.
- Les biais connus de la méthode sont nommés et, si possible, mitigés (voir `biais-relecteur.md`, `sophismes-causalite.md`).
- Les statuts épistémiques (`sophismes-causalite.md`, section statuts) sont respectés : aucune affirmation n'est présentée comme plus établie que ce que la méthode permet réellement de conclure.

### 7. Portée et transférabilité

- Le domaine de validité de la conclusion est nommé explicitement (population, contexte, période).
- Aucune généralisation ne dépasse ce que l'échantillon, le cas ou le corpus permet (voir la généralisation hâtive, `sophismes-causalite.md`).
- Les conditions qui rendraient la conclusion transférable à un autre contexte sont précisées, sinon leur absence est admise.

### 8. Honnêteté des limites

- Les limites réelles du travail sont énoncées par l'auteur, pas seulement découvertes par le relecteur.
- Aucune limite connue n'est dissimulée sous une formulation vague.
- Une limite assumée est traitée comme un gage de rigueur, pas comme un aveu de faiblesse à minimiser dans la revue.

## Sévérité

- Critique : fausse une affirmation, source manquante ou inventée, violation dure du style. À corriger avant toute finalisation.
- Majeur : nuit à la clarté ou à la rigueur sans fausser un fait.
- Mineur : forme, confort de lecture.

## Carte preuve-affirmation

```
| Affirmation | Preuve (source datée) | Statut |
| --- | --- | --- |
```

Statut possible : étayé, à sourcer, à retirer. Aucune ligne "à sourcer" ne passe en version finale.

## Auto-revue cinq questions (académique)

Pour les genres scientifiques, répondre par écrit avant de finaliser, puis corriger les points non résolus.

1. Contribution claire et justifiée ?
2. Clarté : message en première phrase de chaque paragraphe ?
3. Force des preuves : soutiennent-elles les affirmations ?
4. Complétude : manque-t-il une comparaison ou une limite ?
5. Solidité de la méthode face à un évaluateur hostile ?

## Format de sortie imposé

```
Verdict : [Prêt / À réviser / À refondre]

Contrôles :
- Contribution : [Conforme / Non conforme] - [détail]
- Clarté et fluidité : [Conforme / Non conforme] - [détail]
- Preuve et rigueur : [Conforme / Non conforme] - [détail]
- Complétude : [Conforme / Non conforme] - [détail]
- Style maison : [Conforme / Non conforme] - [détail]
- Rigueur méthodologique : [Conforme / Non conforme] - [détail]
- Portée et transférabilité : [Conforme / Non conforme] - [détail]
- Honnêteté des limites : [Conforme / Non conforme] - [détail]

Constats classés par sévérité :
1. [Critique] [description] -> Correctif : [recommandation] (règle : [citée])
2. [Majeur] [description] -> Correctif : [recommandation] (règle : [citée])
3. [Mineur] [description] -> Correctif : [recommandation] (règle : [citée])

Ce qui fonctionne :
- [point fort]

Questions ouvertes :
- [question] -> Recommandation : [proposition]
```

Règles : chaque constat cite sa règle, chaque question ouverte porte une recommandation, lister aussi ce qui fonctionne. Un verdict "Prêt" est faux si un contrôle a été sauté en silence. Les trois dimensions ajoutées (6 à 8) sont notées comme les cinq premières, en lecture qualitative : aucune des deux séries de cinq et de trois dimensions ne remplace le calcul du scorecard, qui reste indépendant et mécanique.
