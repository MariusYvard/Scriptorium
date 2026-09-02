# Revue de littérature (synthèse multi-documents)

Fondre un corpus de sources en une analyse unique, traçable et dédupliquée. Chaque fait reste attribué à sa source.

## 1. Réunir et déduplier le corpus

Rassembler les sources (articles, rapports, références BibTeX). Dédupliquer par DOI et par titre.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/citations.py corpus.bib --dedupe
```

Tracer le schéma de sélection de type PRISMA : nombre de références identifiées, écartées (doublons, hors sujet), retenues. Voir `references/prisma.md`.

## 2. Extraire les faits par source

Pour chaque source retenue, déléguer à l'agent `synthese-sources` l'extraction des faits, chiffres et conclusions, chacun daté et attribué. Pondérer par fiabilité et récence (voir `produire` (sourcer)). Pour une revue de littérature scientifique, chercher et évaluer les sources d'abord avec `references/veille-academique.md` (arXiv, impact par citation, chaîne de version) avant l'extraction.

## 3. Construire le tableau de preuves

Une ligne par fait, une colonne d'attribution. Plusieurs sources qui concordent renforcent le fait, une source isolée reste une hypothèse.

```
| Affirmation | Sources | Niveau de preuve | Note |
| --- | --- | --- | --- |
| ... | [3], [7] | élevé | concordance |
```

Pour une matrice source x thème avec des seuils de convergence explicites (fort, modéré, faible, contesté, lacune), voir `references/discipline-synthese.md`.

Le standard de compte rendu qu'une source incluse aurait dû suivre dépend de son devis (essai randomisé, étude observationnelle, cas clinique, modèle prédictif...) : voir `references/reporting-standards.md` pour vérifier si la source le respecte avant de la créditer d'un niveau de preuve élevé.

## 4. Synthétiser par thème

Organiser par thème, pas par source. Chaque thème regroupe les faits convergents, signale les désaccords entre sources, et conclut sur l'état des connaissances. Ne pas juxtaposer des résumés d'articles, c'est une synthèse, pas une liste.

Éviter les trois anti-patterns nommés dans `references/discipline-synthese.md`, chacun avec un exemple bon et mauvais : le résumé séquentiel, le cherry-picking, la contradiction non résolue laissée sans arbitrage. Typer chaque manque identifié selon les cinq catégories de lacune du même fichier (empirique, méthodologique, théorique, temporelle, géographique) plutôt que de le mentionner vaguement.

## Format de sortie

1. Le schéma de sélection PRISMA (identifiées, écartées, retenues).
2. Le tableau de preuves dédupliqué, attribué.
3. La synthèse thématique, avec les zones de désaccord et les lacunes typées.
4. La bibliographie formatée (voir `produire` (sourcer)).

## Règles

1. Chaque fait est attribué à sa source.
2. Dédupliquer avant de synthétiser, tracer la sélection.
3. Organiser par thème, jamais par source.
4. Signaler les désaccords entre sources plutôt que de les lisser.
5. Une affirmation tenue par une source unique reste une hypothèse.
