# Contrat de mission (générateur-évaluateur)

Fixer par écrit, avant que quiconque n'écrive ou ne lise le document, ce qui vaudra acceptation et ce qui vaudra échec. Un contrat par mission d'écriture à enjeu réel (un rapport, une analyse, un mémoire), pas un rituel pour un court texte interne. Le contrat sépare deux rôles qui ne voient jamais le matériau avant de s'être engagés sur leurs propres termes : celui qui rédige, celui qui évalue.

## 1. Structure du contrat

Un contrat de mission est un objet JSON avec quatre parties. Voir `assets/contrat-mission.exemple.json` pour un contrat complet.

- `dimensions` : ce qui est noté, chaque dimension listée et décrite séparément. Jamais un seul score global qui les fond.
- `conditions_echec` : chacune avec un identifiant court, une sévérité (voir `controler/references/severite.md`), un quantificateur d'agrégation et une action précise si elle se déclenche.
- `verdict_reserve` : l'identifiant réservé au verdict global (section 3).
- `agregation` : la règle qui mappe les conditions déclenchées vers une décision (accepter, réviser, refuser).

## 2. Dimensions notées individuellement

Chaque dimension du contrat porte sa propre appréciation, jamais moyennée avec les autres. Une dimension qui s'effondre reste visible telle quelle dans le rapport final, même si les autres dimensions sont bonnes. Ce principe reprend celui du barème à plancher (`controler/references/consensus.md`) et l'applique au niveau de la mission entière, pas seulement au vote des trois voix.

## 3. Identifiant réservé au verdict global

Le contrat réserve un identifiant unique, `VERDICT`, qui ne désigne jamais une condition d'échec ordinaire. Il porte la décision finale une fois toutes les conditions vérifiées : accepté, à réviser ou refusé, selon la règle `agregation` du contrat. Aucune condition d'échec du contrat ne réutilise cet identifiant, pour qu'un lecteur qui grep le rapport final distingue sans ambiguïté un constat ordinaire du verdict qui les résume.

## 4. Pré-engagement en aveugle

Deux engagements distincts, chacun avant d'avoir vu ce qu'il n'est pas encore censé voir.

### Côté rédacteur

Avant d'écrire un mot du document, le rédacteur reçoit uniquement le contrat, pas encore le matériau source ni le brief détaillé, seulement ce qui est nécessaire pour comprendre les critères. Il paraphrase chaque dimension et chaque condition d'échec avec ses propres mots, puis déclare un plan de rédaction bref (comment il compte satisfaire chaque dimension, quelle section couvre quelle condition). Cet engagement est daté et conservé tel quel à côté du document final, pour qu'un écart entre l'intention déclarée et le résultat saute aux yeux plutôt que de rester invisible.

### Côté évaluateur

Reprend le mécanisme déjà décrit dans `controler/references/contrat-notation.md` : phase aveugle avant lecture, plan de notation engagé avant le texte, interdits fermes (moyenne qui masque un désaccord, adoucissement après coup, score de substitution). Ce fichier ne redéfinit pas ce mécanisme, il l'invoque tel quel pour la mission complète.

## 5. Flux complet

1. Le contrat est rédigé et validé : dimensions, conditions d'échec avec sévérité et action, `VERDICT` réservé, règle d'agrégation.
2. Le rédacteur reçoit le contrat seul, paraphrase, s'engage sur un plan de rédaction.
3. Le rédacteur écrit le document.
4. L'évaluateur reçoit le contrat seul, pas le document, paraphrase, s'engage sur un plan de notation (voir `contrat-notation.md`).
5. L'évaluateur lit le document, note chaque dimension, vérifie chaque condition d'échec, calcule `VERDICT` selon la règle d'agrégation.
6. Le verdict et le détail par dimension et par condition sont restitués ensemble, jamais un chiffre unique qui les remplace.

## Format de sortie

Le contrat JSON complet, les deux engagements horodatés (rédacteur, évaluateur) et le verdict final avec le détail par dimension et par condition d'échec déclenchée ou non.

## Règles

1. Une dimension notée individuellement ne se fond jamais dans un score global qui masquerait sa faiblesse.
2. `VERDICT` est réservé au verdict global, jamais réutilisé par une condition d'échec ordinaire.
3. Le rédacteur s'engage avant d'écrire, l'évaluateur avant de lire. Ni l'un ni l'autre ne voit le matériau avant son engagement.
4. Voir `controler/references/contrat-notation.md` pour le détail de la phase aveugle côté évaluateur, ce fichier ne la redéfinit pas.
