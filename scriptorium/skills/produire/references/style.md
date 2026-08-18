# Style maison (charte éditoriale)

Garantir une voix constante et des règles de forme respectées sur tout écrit. Le style maison par défaut applique des directives strictes (voir `references/directives-strictes.md`). Cette compétence sert à quatre choses : appliquer ces directives, en extraire une charte à partir d'écrits existants, contrôler la conformité d'un texte, calibrer un profil de style personnel mesurable.

## Mode 1 : appliquer le style

Charger `references/directives-strictes.md`. Réécrire ou rédiger le texte en appliquant chaque règle. Conserver le fond, ajuster la forme. Voir aussi `references/lexique-banni.md` pour les substitutions.

Document en anglais : charger `references/style-anglais.md` en plus, et avant de rédiger. Cette référence dit ce qui se transpose du style maison, ce qui change (la virgule sérielle est recommandée en anglais par Chicago, l'APA et la MLA ; le tiret cadratin y est une ponctuation légitime) et les règles propres à l'écriture scientifique anglaise. Le contrôle mécanique correspondant est `scripts/lint-style.py --langue en` ; `scripts/scorecard.py --langue en` porte la même langue dans toute la notation (traçabilité, nombres, lisibilité, empreinte IA, cohérence), pas seulement dans le linter. Appelé sans langue, chaque script retombe sur le pragme du document puis sur le français, et noter un texte anglais avec les règles françaises rend des constats faux. Détail script par script dans `references/langue.md`.

Boucle d'application : produire, vérifier, expliquer.

1. Produire le texte conforme.
2. Vérifier chaque règle (typographie, lexique, ponctuation, registre).
3. Expliquer brièvement les ajustements faits, pour que l'utilisateur garde la main.

## Mode 2 : générer une charte

Quand l'utilisateur veut formaliser sa voix à partir de ses écrits, suivre le schéma de `references/charte-template.md`.

1. Réunir les écrits sources fournis.
2. Repérer les régularités les plus constantes (tournures, registre, longueur de phrase, lexique récurrent).
3. Synthétiser une table "Nous écrivons / Nous n'écrivons pas", chaque ligne appuyée sur un exemple tiré des sources.
4. Distinguer la voix (personnalité, valeurs, constantes) du ton (registre, énergie, technicité, qui varie selon le contexte).
5. Affecter un score de confiance par section : élevé si trois sources concordent et qu'une source explicite l'établit, moyen ou faible sinon.
6. Lister les questions ouvertes, chacune avec une recommandation.
7. Sauvegarder la charte pour les sessions suivantes.

Cette charte couvre la voix et le ton. Pour un profil quantifié utilisé comme garde à la rédaction, voir Mode 4.

## Mode 3 : contrôler la conformité

Passer le texte au crible des directives. Produire la liste des écarts, classés par sévérité, chacun citant la règle enfreinte et proposant un correctif. Déléguer à l'agent `controle-qualite` pour un contrôle complet.

## Mode 4 : calibrer un style personnel (six dimensions)

Apprendre le style mesurable d'un auteur à partir d'échantillons qu'il fournit, pour guider la rédaction sans jamais prendre le pas sur une norme plus forte que lui. Ce mode complète le mode 2 : la charte décrit la voix et le lexique, le profil ici mesure six dimensions concrètes de la phrase et du paragraphe.

### Constituer le profil

Réunir au moins trois échantillons fournis par l'utilisateur. Un seul texte ne distingue pas une habitude d'un accident d'écriture, trois textes ou plus commencent à faire une régularité. Plus il y a d'échantillons, plus le profil est fiable, sans seuil haut fixe.

Mesurer six dimensions, chacune décrite par une régularité observée dans les échantillons, jamais par une préférence supposée.

| Dimension | Ce qui est observé |
| --- | --- |
| Longueur de phrase | Moyenne de mots par phrase et écart entre la plus courte et la plus longue |
| Longueur de paragraphe | Nombre de phrases par paragraphe, uniforme ou variable |
| Transitions | Connecteurs récurrents, façon de lier une idée à la suivante |
| Intégration des citations | Citation fondue dans la phrase ou détachée en retrait, fréquence de la citation directe |
| Densité de modificateurs | Fréquence des adjectifs et adverbes par phrase |
| Registre par section | Écart de formalité entre une introduction, un corps de texte et une conclusion |

Consigner le profil dans le format de sortie (voir plus bas), avec un exemple tiré des échantillons pour chaque dimension. Omettre une dimension sans donnée observable plutôt que d'y mettre un exemple forcé.

### Hiérarchie d'application

Le profil personnel est une garde souple, pas une règle dure : il s'applique en dernier, jamais en premier. Ordre strict du plus fort au plus faible.

1. Style maison (`references/directives-strictes.md`). Non négociable, voir Mode 1.
2. Convention de la discipline visée (voir `references/profils-discipline.md`) : norme de citation, structure attendue, registre du champ.
3. Convention du support visé, quand elle existe (une revue, un commanditaire, un gabarit imposé) : règles propres à ce canal précis.
4. Style personnel calibré. Appliqué seulement là où les trois niveaux précédents laissent un choix libre.

Un conflit entre deux niveaux se tranche toujours en faveur du niveau le plus haut, jamais par compromis entre les deux. Journaliser chaque conflit rencontré (quelle dimension du profil, quelle règle plus forte l'a emporté) et le signaler à l'utilisateur une seule fois par document plutôt qu'à chaque occurrence : un rappel répété à chaque paragraphe noierait le signal utile dans le bruit.

## Niveau de strictness

Lire si l'utilisateur a fixé un niveau (strict, équilibré, souple). Par défaut, strict : appliquer toutes les directives sans exception. En cas de conflit entre une règle de style et une exigence de la revue ou du commanditaire, signaler le conflit, trancher pour la contrainte la plus forte (la plus récente ou la plus officielle), expliquer le compromis.

## Les directives strictes par défaut

Résumé, détail dans `references/directives-strictes.md`.

- Registre encyclopédique, neutre, factuel, zéro promotion.
- Entrée directe en matière, pas de métadiscours.
- Pas de remplissage sur l'héritage, l'impact ou le futur.
- Lexique banni : pivotal, crucial, emblématique, façonner le paysage, témoigne de, souligne, reflète, au-delà de, riche tapisserie, incontournable. Verbes simples (est, sont) plutôt que "se présente comme".
- Ponctuation : zéro tiret cadratin ou demi-cadratin, parenthèses ou virgules à la place. Pas de virgule d'Oxford (A, B et C). Guillemets et apostrophes droits. Gras rare.
- Forme : briser la règle de trois (varier un, deux ou quatre éléments). Pas de liste du type titre en gras puis description.
- Rigueur : fait précis ou rien. Sources avec URL ou DOI vérifiés, sans paramètres de suivi.

## Format de sortie

- Mode appliquer : le texte conforme, plus une note courte des ajustements.
- Mode générer : la charte selon `charte-template.md`, avec scores de confiance et questions ouvertes.
- Mode contrôler : la liste des écarts classés par sévérité, chacun citant sa règle, plus un verdict de conformité.
- Mode calibrer : le profil sur six dimensions, chacune avec l'exemple qui l'illustre, plus la liste des conflits rencontrés pendant la rédaction et le niveau de la hiérarchie qui a tranché chacun.

## Règles

1. Le style ajuste la forme, jamais le fond ni les faits.
2. Chaque écart relevé cite la règle enfreinte.
3. Omettre une section de charte sans donnée plutôt que d'y mettre un fragment vide.
4. Le style maison s'applique aussi aux textes produits par les autres compétences du plugin.
5. La hiérarchie discipline, support puis style personnel ne s'inverse jamais, quel que soit le nombre d'échantillons fournis. Le style maison la domine toutes les deux.
6. La langue du document se fixe au cadrage et ne change plus. En anglais, `references/style-anglais.md` remplace les règles de forme calibrées sur le français ; les directives de fond (registre, rigueur, sources) sont inchangées. `references/langue.md` détaille jusqu'où va ce bilinguisme dans les scripts déterministes.
