# Répondre aux relecteurs

Préparer une resoumission convaincante : une réponse courtoise et précise à chaque commentaire, et une version révisée dont les changements sont traçables. Le flux suit la publication scientifique.

## 1. Recueillir les entrées

Réunir les commentaires des relecteurs (numérotés par relecteur), la version soumise et la version révisée du manuscrit. Si la version révisée n'existe pas encore, la produire d'abord avec `produire` (genre) et `controler` (revue).

### Revue externe réelle (commentaires humains non structurés)

Un commentaire de relecteur réel arrive rarement pré-découpé : texte brut, PDF annoté ou liste informelle, qualité variable. Découper ces commentaires en items typés (majeur, mineur, éditorial, positif), chacun avec sa citation exacte, puis soumettre ce découpage à l'utilisateur pour confirmation avant de poursuivre : un mauvais découpage fausse toute la suite (un commentaire composé traité comme un seul point peut cacher deux demandes distinctes).

Une fois le découpage confirmé, appliquer un coaching en quatre couches à chaque item avant de rédiger la réponse.

1. Comprendre le souci réel du relecteur derrière sa formulation littérale.
2. Juger : l'utilisateur est-il d'accord avec le fond du commentaire, en désaccord ou partiellement d'accord ?
3. Formuler la réponse dans la lettre, selon le jugement retenu à l'étape précédente.
4. Évaluer le risque : quelles conséquences si ce point n'est pas traité comme le relecteur le souhaite (risque de refus ou point secondaire) ?

Ne jamais accepter tous les commentaires par défaut. Un relecteur réel peut se tromper, partir d'un biais de paradigme méthodologique (voir `references/biais-relecteur.md`) ou mal lire un passage. Le jugement de l'étape 2 reste une décision de l'utilisateur, pas une capitulation automatique.

## 2. Construire le journal des modifications

Comparer les deux versions pour objectiver les changements.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/diff-versions.py soumis.md revise.md
```

Le script liste les sections ajoutées, supprimées et modifiées, avec le nombre de mots changés. Ce journal alimente les renvois précis de la réponse.

## 3. Répondre point par point

Pour chaque commentaire, un triplet.

```
Commentaire R1.3 : [citation exacte du relecteur]
Réponse : [accord / accord partiel / désaccord argumenté, jamais un refus sec]
Modification : [section, paragraphe et nature du changement ou justification du maintien du texte d'origine]
```

Citer le commentaire mot pour mot. Une réponse n'est jamais un refus sec : même un désaccord se motive par une preuve ou un argument, jamais par un simple "non" ou une reformulation évasive. Quand un point est écarté, le justifier avec courtoisie et preuve. Remercier sobrement, sans flagornerie.

### Quatre statuts fermés par remarque

Un désaccord argumenté avec un relecteur est une issue légitime, distincte de l'échec. Fermer chaque remarque sur l'un de ces quatre statuts, avec l'obligation de preuve qui lui correspond.

- Résolu : le texte a été modifié en réponse directe au commentaire. Preuve exigée : localisation précise du changement (section, paragraphe).
- Limite assumée : le point est reconnu fondé mais non traité, la limite est déclarée explicitement dans le texte plutôt que corrigée. Preuve exigée : la phrase exacte du texte qui porte cette déclaration.
- Non résoluble : le commentaire dépasse ce que les données ou le format permettent (nouvelle expérience hors de portée, source introuvable). Preuve exigée : la raison factuelle de l'impossibilité, pas une esquive.
- Désaccord fondé sur preuve : l'utilisateur maintient sa position contre l'avis du relecteur, avec une justification étayée. Preuve exigée : la source ou l'argument précis qui soutient le maintien.

## 4. Registre des engagements

Chaque promesse contenue dans la réponse (une expérience supplémentaire, une clarification, une nouvelle citation, une restructuration) s'extrait individuellement dans un registre, indépendamment du triplet qui l'a formulée. Ne jamais fusionner deux engagements distincts pris dans une seule réponse composée.

| Engagement | Type | Preuve de réalisation attendue | Statut |
| --- | --- | --- | --- |
| [promesse extraite] | [expérience / clarification / citation / restructuration] | [ce qui doit apparaître dans la version révisée] | [tenu / partiel / non tenu / rejeté explicitement] |

Le statut se vérifie indépendamment de la réponse elle-même, en re-revue (section 7) : une promesse notée "tenue" sans localisation vérifiable dans le texte reste "non tenue" tant que le changement réel n'est pas retrouvé.

## 5. Produire la version en modifications suivies

Pour un livrable Word avec corrections visibles, passer par la compétence `livrer` (document) et le skill `docx` : insérer les changements en révisions suivies (ajouts et suppressions marqués) ou en commentaires, pour que le relecteur accepte ou refuse chaque modification. Garder une version propre en parallèle.

## 6. Contrôler

Repasser la version révisée par `controler` (revue) et le scorecard déterministe. Un changement demandé par un relecteur ne doit pas en casser un autre ni introduire un écart de style.

## 7. Re-revue et trajectoire de score

### Priorités et condition d'acceptation

Classer chaque remarque en P1, P2 ou P3. Tous les P1 doivent être au statut résolu pour recommander l'acceptation. Les P2 à 80% suffisent. Les P3 n'ont aucun effet sur la décision, ils restent informatifs.

### Vérification localisée

Pour chaque item P1, localiser le changement réel dans la version révisée plutôt que de se fier à la déclaration de l'auteur. Une affirmation vague ("corrigé", "pris en compte") sans localisation précise vaut invérifiable, pas résolu.

### Trajectoire de score

Comparer le scorecard de la version d'origine et celui de la version révisée, axe par axe.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scorecard.py soumis.md --format json > rapport-avant.json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scorecard.py revise.md --format json > rapport-apres.json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scorecard.py --trajectoire rapport-avant.json rapport-apres.json
```

Une régression de plus de 3 points sur un axe (un axe qui perd du terrain pendant que d'autres progressent) déclenche un point de contrôle, jamais un passage silencieux. Trois options s'offrent alors : accepter le compromis (le gain net justifie la perte localisée), réviser à nouveau en ciblant seulement l'axe régressé ou restaurer la version antérieure de la section concernée.

## Format de sortie

1. La lettre de réponse, point par point, par relecteur, avec le statut fermé de chaque remarque.
2. Le registre des engagements.
3. Le journal des modifications (sorties de `diff-versions.py`).
4. La trajectoire de score entre la version soumise et la version révisée.
5. La version révisée en modifications suivies, plus une version propre.

## Règles

1. Citer chaque commentaire mot pour mot avant d'y répondre.
2. Toute réponse renvoie à un changement précis et localisé ou à une justification étayée, jamais à un refus sec.
3. Aucune impasse : chaque commentaire reçoit une réponse et un statut fermé parmi les quatre définis.
4. Courtoisie sobre, jamais de flagornerie ni de polémique.
5. La version révisée respecte le style maison et passe le scorecard.
6. Un engagement pris dans la réponse se vérifie indépendamment en re-revue, une affirmation vague ne vaut pas preuve de réalisation.
7. Tous les P1 résolus pour recommander l'acceptation, les P2 à 80%, les P3 sans effet sur la décision.
8. Une régression de plus de 3 points sur un axe en re-revue est un point de contrôle obligatoire, jamais un passage silencieux.
9. Une revue externe réelle se découpe et se confirme avec l'utilisateur avant traitement, jamais acceptée en bloc par défaut.
