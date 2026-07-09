# Revue par consensus et profils de discipline

Réduire les angles morts d'une révision en passe unique : faire évaluer le document par plusieurs agents indépendants, agréger leurs verdicts et caler les normes sur la discipline visée.

## 1. Calibrer le profil de discipline

Charger `references/profils-discipline.md`. Le profil fixe la norme de citation, la structure attendue et la pondération des sources pour le champ visé (sciences dures, sciences humaines, droit, gestion, médecine). Si un fichier `profil.json` existe dans le dossier de travail, l'utiliser. Sinon, demander la discipline une fois, puis appliquer son profil.

## 2. Précontrat de notation en aveugle

Avant que chaque voix ne lise le document, appliquer le contrat de notation préenregistré : voir `references/contrat-notation.md`. Chaque agent (`controle-qualite`, `contradicteur`, `verificateur-faits`) reçoit le contrat (dimensions, conditions d'échec avec sévérité et quantificateur, procédure de mesure), le paraphrase et s'engage sur un plan de notation avant de recevoir le texte. Cette phase aveugle précède l'appel de la section suivante, elle ne s'y substitue pas.

## 3. Lancer la revue à trois voix

Déléguer en parallèle, via l'outil Task, à trois agents indépendants.

- `controle-qualite` : conformité au style maison, rigueur, structure. Pré-passe déterministe comprise.
- `contradicteur` : contre-thèse la plus forte, points de rupture.
- `verificateur-faits` : vérification des affirmations factuelles contre les sources.

Chaque agent rend un verdict (Prêt, À réviser ou À refondre) accompagné d'une confiance de 1 à 5 sur sa recommandation, selon la grille de `references/contrat-notation.md` et `references/lettre-decision.md`.

### Anti-ancrage entre les voix

Chaque voix vote sans jamais voir le verdict, la confiance ou le motif des autres. La délégation en parallèle par l'outil Task assure déjà cette séparation par construction, mais la règle reste explicite pour ne pas se perdre si l'exécution devient un jour séquentielle : le premier verdict rendu n'est jamais montré aux voix qui rendent le leur ensuite. La synthèse (section 5) ne révèle les trois votes qu'une fois les trois rendus, jamais un par un au fil de l'eau. Montrer le premier verdict avant les deux autres en ferait une ancre, même sans intention de biaiser le résultat.

## 4. Ancrer sur le scorecard déterministe

Calculer la note objective du document.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scorecard.py FICHIER --format json
```

Le scorecard sert d'ancre commune et de départage. Un document que les agents jugent prêt mais que le scorecard place sous 70 n'est pas prêt. La sortie JSON expose aussi une décision éditoriale à quatre valeurs et un plancher par axe (option `--plancher N`, champ `decision_editoriale`) : un axe sous le plancher plafonne cette décision indépendamment du total, voir la logique montrée dans `scorecard.py` et le détail dans `_cablage-lot2.md`.

## 5. Agréger le verdict

Règle de consensus sur trois voix.

- Prêt seulement si au moins deux agents disent Prêt, qu'aucun ne signale de point critique non résolu et que le scorecard atteint le seuil du profil (souvent 85).
- À refondre si au moins deux agents disent À refondre, ou si le scorecard tombe sous 70.
- À réviser sinon.

### Agrégation mécanique par quantificateur

Chaque condition d'échec du contrat de notation porte un quantificateur fixé avant la lecture (voir `references/contrat-notation.md`) : au moins un, majorité ou tous. Appliquer ce quantificateur tel quel, jamais un autre choisi après coup pour obtenir le résultat voulu.

### Précédence de sévérité

Quand plusieurs conditions se déclenchent en même temps, la plus sévère tranche : critique avant majeur, majeur avant mineur. Une égalité de sévérité se résout par l'ordre d'apparition dans le contrat. Voir `controler/references/severite.md` pour la définition unique de ces niveaux.

### Plancher par dimension

Une dimension effondrée (sous le plancher, champ `decision_editoriale` de `scorecard.py`) peut bloquer le verdict de consensus même si la moyenne des trois voix serait favorable. Ne jamais laisser une bonne moyenne masquer une dimension qui s'effondre seule.

### Interdit ferme

Ne jamais lisser deux dimensions contradictoires en une moyenne. Si `controle-qualite` et `contradicteur` jugent différemment la même dimension pour des raisons distinctes et fondées, rapporter les deux scores tels quels dans le verdict de consensus, jamais en un chiffre unique qui efface le désaccord.

Surfacer les désaccords entre agents, ils signalent les zones à trancher. Un consensus mou qui efface un signal critique est un échec.

## 6. Vérification croisée par un second modèle (optionnelle)

Pour un document à enjeu élevé, une vérification supplémentaire peut porter sur un échantillon des affirmations ou des citations, pas sur leur ensemble, confiée à une configuration de modèle distincte de celle qui a produit le premier contrôle. Cette option reste facultative pour trois raisons.

- Elle ne remplace jamais les trois voix de la section 3, elle les complète sur échantillon.
- Elle se dégrade gracieusement si aucune seconde configuration de modèle n'est disponible dans l'environnement courant : le consensus à trois voix reste valide seul, l'absence de vérification croisée se note comme non réalisée plutôt que de bloquer la revue.
- Une divergence entre la vérification croisée et le consensus initial se signale telle quelle, elle ne se moyenne jamais avec les votes déjà rendus : un désaccord entre deux mécanismes de contrôle est un signal à trancher en lecture humaine, pas un chiffre à lisser.

## Format de sortie

```
Profil de discipline : [champ] (norme [APA/Vancouver/...], structure [...])

Votes :
- controle-qualite : [verdict] - confiance [1-5] - [motif clé]
- contradicteur : [verdict] - confiance [1-5] - [faille principale]
- verificateur-faits : [verdict] - confiance [1-5] - [affirmation à étayer]

Dissidence : [aucune / une dimension : laquelle, par quelle voix] (deux dissidences simultanées -> un nouveau cycle, voir contrat-notation.md)

Scorecard : [note]/100 | Décision éditoriale : [accepter/révision mineure/révision majeure/refus] (plancher [N]/20)

Vérification croisée : [non réalisée / réalisée sur échantillon de N éléments, convergente / divergente sur tel point]

Verdict de consensus : [Prêt / À réviser / À refondre]
Désaccords à trancher : [...]
Actions prioritaires : [...]
```

## Règles

1. Trois voix indépendantes, jamais une seule passe déguisée en consensus.
2. Le scorecard déterministe départage et ancre les verdicts qualitatifs.
3. Un point critique signalé par un seul agent suffit à retenir le verdict Prêt.
4. Surfacer les désaccords, ne pas les moyenner.
5. Le profil de discipline cale la norme, il ne relâche pas la rigueur.
6. Le contrat de notation se préenregistre en aveugle avant la lecture, jamais après.
7. Une dimension sous le plancher bloque malgré une bonne moyenne. Deux dimensions contradictoires se rapportent telles quelles, jamais lissées.
8. Aucune voix ne voit le verdict d'une autre avant que les trois soient rendus. Une vérification croisée par un second modèle, si elle a lieu, reste un signal supplémentaire sur échantillon, jamais moyenné avec les trois voix.
