# Discipline de synthèse (anti-patterns et lacunes)

Synthétiser n'est pas résumer. Trois défauts nommés pour les repérer, une matrice pour mesurer la convergence entre sources, une typologie pour classer ce qui manque plutôt que de le passer sous silence. Complète `produire` (revue-litterature) et l'agent `synthese-sources`.

## 1. Trois anti-patterns nommés

### Résumé séquentiel

Mauvais : « La source A montre que le marché croît de 8 %. La source B montre que la satisfaction client augmente. La source C montre que les coûts baissent. » Trois faits juxtaposés, aucun lien entre eux.

Bon : « La croissance du marché (source A) coïncide avec la baisse des coûts d'entrée (source C) sur la même période, ce qui explique en partie la hausse de satisfaction client relevée par la source B : de nouveaux entrants moins chers élargissent l'offre. » Le lien causal ou structurel entre les faits est explicite, pas seulement leur juxtaposition.

### Cherry-picking

Mauvais : citer une étude favorable à la thèse défendue en ignorant trois études contraires disponibles dans le même corpus.

Bon : présenter la source favorable et les sources contraires ensemble, avec leurs niveaux de preuve respectifs (`references/hierarchie-preuve.md`), puis conclure sur l'état réel de la convergence, pas sur la position qui arrangeait le plus le propos initial.

### Contradiction non résolue

Mauvais : mentionner que deux sources se contredisent sans aller plus loin, en laissant le lecteur trancher seul.

Bon : comparer les niveaux de preuve des deux sources, examiner si la différence de contexte ou de méthode explique l'écart, puis trancher explicitement entre réconciliable (la différence s'explique) et irréconciliable (les sources restent en désaccord réel, à signaler comme tel).

## 2. Matrice source x thème

Une ligne par source, une colonne par thème, une cellule qui indique si la source soutient, contredit ou ne traite pas le thème.

```
| Source | Thème 1 | Thème 2 | Thème 3 |
| --- | --- | --- | --- |
| [1] | soutient | ne traite pas | contredit |
| [2] | soutient | soutient | ne traite pas |
| [3] | contredit | soutient | soutient |
```

### Seuils de convergence

- Fort : trois sources ou plus de niveau de preuve élevé (niveaux 1 à 3, voir `hierarchie-preuve.md`) convergent sur le thème.
- Modéré : deux sources concordantes, ou une source de niveau élevé appuyée par un indice secondaire cohérent.
- Faible : une source unique, ou des sources de niveau 5 et en dessous seulement.
- Contesté : des sources de niveau de preuve comparable se contredisent sans qu'un facteur de contexte explique l'écart.
- Lacune : zéro source ne traite le thème alors qu'il fait partie du périmètre annoncé.

## 3. Typologie des lacunes (cinq types)

1. Lacune empirique : aucune source n'a mesuré ce phénomène précis, même indirectement.
2. Lacune méthodologique : le phénomène est mesuré, mais avec des méthodes trop hétérogènes ou trop faibles pour trancher.
3. Lacune théorique : les faits sont établis, mais aucun cadre explicatif convaincant ne relie la cause à l'effet observé.
4. Lacune temporelle : les données disponibles sont anciennes par rapport à la vitesse d'évolution du champ (voir la fenêtre de fraîcheur dans `ponderation-sources.md`).
5. Lacune géographique : le phénomène est établi dans un contexte donné, sans réplication ailleurs.

Chaque lacune identifiée se signale avec le tag normalisé `[LACUNE MATERIELLE]` si elle affecte une affirmation centrale du document, ou se documente simplement dans la section des limites sinon. Voir `scripts/traceability.py` pour le comptage automatique de ces tags.

## Sources

- Page, M. J. et al. (2021). The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. BMJ, 372, n71. https://doi.org/10.1136/bmj.n71
