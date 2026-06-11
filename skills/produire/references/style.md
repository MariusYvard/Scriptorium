# Style maison (charte éditoriale)

Garantir une voix constante et des règles de forme respectées sur tout écrit. Le style maison par défaut applique des directives strictes (voir `references/directives-strictes.md`). Cette compétence sert à trois choses : appliquer ces directives, en extraire une charte à partir d'écrits existants, contrôler la conformité d'un texte.

## Mode 1 : appliquer le style

Charger `references/directives-strictes.md`. Réécrire ou rédiger le texte en appliquant chaque règle. Conserver le fond, ajuster la forme. Voir aussi `references/lexique-banni.md` pour les substitutions.

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

## Mode 3 : contrôler la conformité

Passer le texte au crible des directives. Produire la liste des écarts, classés par sévérité, chacun citant la règle enfreinte et proposant un correctif. Déléguer à l'agent `controle-qualite` pour un contrôle complet.

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

## Règles

1. Le style ajuste la forme, jamais le fond ni les faits.
2. Chaque écart relevé cite la règle enfreinte.
3. Omettre une section de charte sans donnée plutôt que d'y mettre un fragment vide.
4. Le style maison s'applique aussi aux textes produits par les autres compétences du plugin.
