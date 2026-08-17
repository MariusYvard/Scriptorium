# Schéma de sélection PRISMA

Tracer la sélection des sources d'une revue, pour la rendre reproductible.

## Étapes et comptes

1. Identification : nombre de références trouvées par source de recherche (bases, web, références croisées).
2. Doublons retirés : références identiques dédupliquées par DOI ou titre.
3. Sélection sur titre et résumé : retenues, écartées (avec motif).
4. Éligibilité sur texte intégral : retenues, écartées (avec motif).
5. Incluses : nombre final retenu pour la synthèse.

## Forme

```
Identifiées : N1
Doublons retirés : N2
Examinées (titre, résumé) : N3   dont écartées : N4 (motifs)
Évaluées (texte intégral) : N5   dont écartées : N6 (motifs)
Incluses dans la synthèse : N7
```

Chaque écart porte un motif (hors sujet, méthode insuffisante, doublon, langue).

## Rendu en figure

Le type `prisma` de `scripts/figures.py` rend ce schéma en SVG, avec les quatre étapes (identification, criblage, éligibilité, inclusion) et les exclusions sorties latéralement.

```
echo '{"identifiees":{"Bases de données":420,"Autres sources":15},"doublons":60,
"examinees":375,"ecartees_titre":[{"motif":"Hors sujet","n":150},{"motif":"Langue non couverte","n":50}],
"evaluees":175,"ecartees_texte":[{"motif":"Méthode insuffisante","n":90},{"motif":"Population différente","n":50}],
"incluses":35}' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/figures.py prisma --data - --audit --out prisma.svg --title "Sélection des études"
```

Lancer `--audit` avant de rendre. Il vérifie que les comptes bouclent aux trois jonctions : identifiées moins doublons égale examinées, examinées moins la somme des écarts au criblage égale évaluées, évaluées moins la somme des écarts en texte intégral égale incluses. Un schéma dont les comptes ne tombent pas juste est faux, quel que soit le soin de son rendu.

## Tableau de preuves

Une ligne par affirmation, une colonne d'attribution et un niveau de preuve.

```
| Affirmation | Sources | Niveau de preuve | Note |
| --- | --- | --- | --- |
| ... | [n], [m] | élevé / moyen / faible | concordance ou désaccord |
```
