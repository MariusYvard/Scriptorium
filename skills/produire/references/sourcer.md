# Sourcer (recherche et citations)

Réunir des preuves vérifiées et les relier aux affirmations du document. La règle est simple : fait précis et sourcé, ou rien. Une affirmation sans preuve est affaiblie ou retirée, jamais maquillée en certitude.

## Quand déléguer

Pour une recherche large (plusieurs thèmes, dizaines de sources, synthèse comparative), déléguer à l'agent `synthese-sources` via l'outil Task. Pour vérifier un fait isolé ou formater quelques références, traiter directement.

## 1. Cibler la recherche

Partir de la commande de preuve issue du cadrage : chaque sous-partie a un message et une preuve attendue. Lister les faits, chiffres et références à trouver. Hiérarchiser : d'abord les affirmations centrales de l'introduction et de la conclusion, qui supportent le plus de poids.

## 2. Chercher

Utiliser la recherche web pour les faits du monde présent (chiffres, dates, acteurs en poste, prix, état d'une loi). Ne jamais répondre de mémoire sur un fait susceptible d'avoir changé. Si une base de connaissances ou un gestionnaire de références est connecté, l'interroger aussi, sans en dépendre.

## 3. Pondérer les sources

Classer chaque source par fiabilité, puis par récence. Voir `references/ponderation-sources.md` pour la grille complète. Résumé des poids de fiabilité :

- Source autoritaire (publication évaluée par les pairs, texte officiel, donnée primaire) : 1,0.
- Source opérationnelle (institution reconnue, rapport sérieux) : 0,8.
- Source contextuelle ou secondaire : 0,3 à 0,6.
- Source périmée ou invérifiable : exclue.

Facteur de récence : une donnée de moins de six mois prime, une donnée de plus de deux ans est traitée avec prudence sauf si elle reste la référence officielle.

## 4. Trianguler

Ne pas asseoir une affirmation centrale sur une source unique. Corroborer par recoupement : plusieurs sources, plusieurs méthodes, plusieurs périodes. Une donnée tirée d'un seul rapport est une hypothèse, pas une conclusion. Étiqueter le niveau de preuve : élevé (plusieurs sources concordantes), moyen (indice sérieux), faible (signal précoce).

## 5. Extraire et attribuer

Pour chaque source retenue, extraire le fait, le chiffre exact ou la citation, avec son attribution complète. Distinguer l'observation de l'interprétation : une citation est une preuve, pas un constat. Le constat est l'interprétation qu'en tire l'auteur.

## 6. Construire la carte preuve-affirmation

Relier chaque affirmation majeure à sa preuve dans un tableau de contrôle. C'est l'outil central de la rigueur, repris à la révision.

```
| Affirmation | Preuve (source datée) | Statut |
| --- | --- | --- |
| Le marché croît de 12 % par an | Rapport X 2025, p. 14 | étayé |
| L'adoption dépasse 60 % | aucune source fiable | à sourcer ou retirer |
```

## 7. Formater les citations

Appliquer la norme demandée (APA 7 ou Vancouver pour l'académique, notes ou références numérotées sinon). Voir `references/formats-citation.md`. Nettoyer chaque URL : retirer les paramètres de suivi (utm_ et autres). Vérifier que chaque lien et chaque DOI résout bien vers la ressource citée.

## Vérification déterministe

Avant de livrer la bibliographie, la passer au script de vérification. Il retire les paramètres de suivi, repère les doublons et contrôle la syntaxe des DOI.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify-sources.py FICHIER
```

La résolution réseau des liens est optionnelle (`--check-links`). Corriger les URL signalées avant de formater la bibliographie.

Pour une bibliographie au format BibTeX, employer le moteur de citations : il formate en APA 7 ou Vancouver, déduplique par DOI, et peut récupérer une référence depuis son DOI (réseau, optionnel).

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/citations.py refs.bib --to apa --dedupe
```

## Format de sortie

1. Liste des sources retenues, classées par fiabilité, avec date et poids.
2. Faits extraits, attribués, étiquetés par niveau de preuve.
3. Carte preuve-affirmation.
4. Bibliographie formatée selon la norme.
5. Zones de preuve manquante, signalées pour décision (sourcer autrement, affaiblir ou retirer l'affirmation).

## Règles

1. Fait précis ou rien. Pas d'affirmation vague pour combler un trou.
2. URL et DOI vérifiés à 100 %, sans paramètres de suivi.
3. Jamais de source inventée ni de citation approximative attribuée à une personne réelle.
4. Trianguler toute affirmation centrale avant de l'avancer.
5. Distinguer observation et interprétation à chaque extraction.
