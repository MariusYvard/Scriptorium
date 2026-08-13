# Contredire (dialectique et red-team)

Éprouver une thèse en construisant la meilleure version de son opposé. Une démonstration qui n'a pas affronté sa contradiction la plus forte n'est pas solide, elle n'a pas encore été testée. Cette compétence sert avant la rédaction (pour blinder le plan) et après (pour trouver la faille).

## Quand déléguer

Pour une contradiction complète et structurée, déléguer à l'agent `contradicteur` via l'outil Task. Pour une objection ponctuelle, traiter directement.

## 1. Isoler la thèse

Formuler en une phrase la thèse centrale à éprouver. Si le texte en porte plusieurs, traiter la principale d'abord. Une thèse floue ne peut pas être contredite utilement, la resserrer.

## 2. Construire la contre-thèse par le modèle de Toulmin

Décomposer l'argument adverse le plus fort, pas un homme de paille.

- Affirmation : ce que la contre-thèse soutient.
- Données : les faits sur lesquels elle s'appuie.
- Garantie : le principe qui relie les données à l'affirmation.
- Fondement : ce qui soutient la garantie.
- Réfutation : les conditions où la thèse de départ tomberait.

Construire la version la plus défendable de l'opposition (steelman), celle qu'un partisan compétent avancerait.

## 3. Viser les points de rupture

Chercher là où la thèse cède le plus vite.

- La preuve la plus faible : quelle affirmation tient sur la source la plus fragile ?
- L'objection non traitée : quelle question le texte évite-t-il ?
- Le saut logique : où passe-t-on d'une corrélation à une causalité, d'un cas au général ? Voir `references/sophismes-causalite.md` pour le catalogue des sophismes qui structurent souvent ce saut et les critères de Bradford Hill pour une affirmation causale précise.
- L'angle mort : quel acteur, quel coût, quel scénario le texte ignore-t-il ?

## 4. Discipline de concession

Quand l'auteur ou un autre agent conteste un point de rupture, noter la réfutation reçue de 1 à 5 avant de décider de céder ou non.

- 5 : preuve nouvelle qui démonte le constat. Concéder.
- 4 : réponse solide avec une réserve mineure. Concéder, en formulant la réserve.
- 3 : l'auteur répète sa position sans preuve nouvelle. Tenir, en précisant ce qui reste non traité.
- 2 : contre-attaque qui déplace le débat sans répondre au point. Ne pas céder, signaler le hors-sujet.
- 1 : affirmation sans preuve à l'appui. Ne pas céder, l'attaque initiale tient d'autant plus.

Règles fermes : concession seulement à 4 ou 5. Jamais deux concessions consécutives, le seuil suivant remonte à 5 strict après une première concession. Pause obligatoire si plus de la moitié des points de rupture d'un même cycle ont été concédés : le déclarer explicitement à l'utilisateur avant de continuer, plutôt que de conclure en silence que la thèse tient.

### Seuil de concession moyenne

Calculer la moyenne des notes de réfutation attribuées sur l'ensemble d'une passe de contradiction. Une moyenne au-dessus de 3,5 sur 5 signale une contradiction trop tendre : un contradicteur qui concède beaucoup a cherché l'accord plutôt que la faille. Rejouer la passe en durcissant, en reprenant la preuve la plus faible identifiée à l'étape 3, jamais en haussant le ton.

## 5. Verrouillage de cadrage

Au bout de plusieurs tours de réfutation sur les mêmes points, une thèse qui résiste point par point peut pourtant reposer sur une prémisse commune aux deux camps, jamais interrogée. Après trois tours ou plus sur le même point de rupture, interroger explicitement cette prémisse implicite plutôt que de continuer à discuter ses conséquences. Question type : les deux positions supposent X, qu'est-ce qui montre que X tient réellement ?

## 6. Sévérité DA-CRITIQUE

Au-dessus de la gravité "grave" de la section 3, une sévérité DA-CRITIQUE s'applique à un homme de paille structurel : la thèse entière attaque une position que personne ne défend réellement, pas un excès ponctuel isolé. Cette sévérité n'appelle pas une retouche locale mais un recadrage : nommer la position réellement défendue par un partisan compétent et reprendre l'analyse sur cette base plutôt que de corriger le détail.

## 7. Restituer

Présenter la contradiction de façon utilisable, pas pour démolir mais pour renforcer.

```
Thèse éprouvée : [une phrase]

Contre-thèse la plus forte (Toulmin) :
- Affirmation : ...
- Données : ...
- Garantie : ...
- Réfutation : conditions où la thèse de départ tombe : ...

Points de rupture, par gravité (grave / moyen / DA-CRITIQUE si homme de paille structurel) :
1. [grave] [faille] -> Parade : [renforcer, nuancer ou concéder]
2. [moyen] [faille] -> Parade : ...

Concessions (si contestation reçue) :
- [point] -> réfutation notée [1-5] -> [concédé / tenu]

Verrouillage de cadrage : [prémisse interrogée / non détecté]

Verdict : la thèse tient / tient sous conditions / doit être nuancée / doit être recadrée (DA-CRITIQUE).
```

## 8. Boucler avec la rédaction

Reverser le résultat dans le texte. Une bonne thèse adresse explicitement sa contradiction la plus forte. Une limite assumée vaut mieux qu'une faille dissimulée. Pour les genres concernés (analyse stratégique, prospective, article de point de vue), intégrer une section qui présente les perspectives opposées.

## Règles

1. Toujours construire l'opposition la plus forte, jamais un homme de paille.
2. Nommer la parade pour chaque faille, sans impasse.
3. Distinguer la faille fatale (la thèse tombe) de la faille réparable (la thèse se nuance).
4. La contradiction sert à renforcer, pas à paralyser. Conclure par un verdict.
5. Concession seulement à 4 ou 5 sur 5, jamais deux concessions consécutives, pause déclarée si plus de la moitié des points cède.
6. Un homme de paille structurel (DA-CRITIQUE) exige un recadrage de la thèse, pas une retouche.
