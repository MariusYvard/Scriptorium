# Playbook : rapport scientifique, mémoire et article IMRAD

Couvre le mémoire universitaire, le rapport de recherche et l'article scientifique original. Finalité : transférer une connaissance scientifique, valider un cursus, publier auprès de pairs. Critères clés : cohérence théorico-pratique, reproductibilité, validité interne, significativité.

## Langue

La langue du document se fixe au cadrage, avec le genre et le plan, et ne change plus ensuite. Un mémoire ou un article rédigé en anglais suit `produire` (style), référence `style-anglais.md` : les règles de forme calibrées sur le français y sont remplacées, non ajoutées, et le contrôle mécanique se lance avec `scripts/lint-style.py --langue en`. Deux points y pèsent plus que les autres pour ce genre : `significant` se réserve à la signification statistique, et la règle de temps ci-dessous est la convention anglaise, que le linter ne contrôle pas. La structure elle-même bouge : `genres-anglais.md`, chargé en plus de ce playbook pour un document anglais, donne les trois variantes d'IMRAD selon la revue visée (ICMJE, IEEE, Nature), les temps verbaux section par section, la forme et la place de l'abstract, les mots-clés puis les longueurs comptées en mots.

## A. Mémoire universitaire et rapport de recherche

Longueur idéale 30 à 60 pages pour un travail de fin d'études. Équilibre classique : un tiers de partie théorique, deux tiers de partie pratique (matériels, méthodes, analyses). Présentation : texte justifié, police classique (Arial ou Times, 10 à 12), interligne 1,25 ou 1,5.

Structure universelle :

1. Pages liminaires : page de garde (titre précis exprimant le maximum d'information), table des matières, listes des tableaux, figures et abréviations (chaque abréviation définie à sa première apparition).
2. Introduction : amener le sujet de façon progressive, exposer la problématique en interrogation simple et courte, annoncer le plan.
3. Partie théorique et méthodologique : asseoir les fondements conceptuels sur des sources reconnues. Placer le principe théorique en début de paragraphe, avant l'observation de terrain.
4. Résultats et discussion : présenter les données analysées, puis une interprétation critique. Tenir une position d'extériorité et de prudence. Masquer l'identité réelle des acteurs ou des lieux pour la confidentialité.
5. Conclusion : résumer les résultats, souligner les limites, ouvrir sur des perspectives.
6. Déclarations de fin de manuscrit : contribution, financement, usage de l'IA (`credit-divulgation.md`), puis disponibilité des données et du code (`disponibilite.md`).
7. Bibliographie : par ordre d'apparition ou alphabétique, selon la norme exigée (APA 7 ou Vancouver).

## B. Article scientifique original (IMRAD)

Rapport court (environ 20 pages) et dense. Précédé d'un résumé structuré (abstract) de 150 à 300 mots. Règle de temps : présent pour les connaissances acquises de la science, passé pour la méthode et les résultats propres de l'étude.

Chaque section a un rôle exclusif, pour éviter la redondance.

### Introduction

Justifier l'étude, passer en revue les données antérieures, expliciter l'objectif principal ou la question de recherche en toute fin de section. Entonnoir : du général documenté vers la question précise.

### Méthodes (Methods)

Détailler le protocole pour permettre la réplication exacte. Décrire obligatoirement : la population (critères d'inclusion et de non-inclusion), le lieu, l'intervention, le critère de jugement principal (unique et mesurable), le calcul de taille de l'échantillon, les méthodes statistiques. Au passé.

### Résultats (Results)

Présenter les observations de façon neutre : texte, graphiques, tableaux autonomes. Le tableau 1 est classiquement réservé aux caractéristiques démographiques et cliniques des participants. Pas d'interprétation ici, seulement les faits. Au passé.

### Discussion

Commencer par une première phrase clé qui répond à l'objectif principal formulé dans l'introduction. Évaluer ensuite forces et faiblesses méthodologiques, comparer à la littérature, conclure en adéquation stricte avec les résultats. Ne pas surinterpréter.

Paternité : l'ordre des co-auteurs suit la contribution scientifique réelle, le premier auteur est le contributeur principal (règles ICMJE).

### Déclarations (après la discussion, avant la bibliographie)

Quatre déclarations distinctes, jamais fondues en un paragraphe unique : contribution CRediT, financement, usage de l'IA (`credit-divulgation.md`), disponibilité des données et du code (`disponibilite.md`). La déclaration de disponibilité nomme son régime et porte la preuve que ce régime exige : identifiant pérenne pour un dépôt ouvert, date de levée pour un embargo, licence nommée pour du code, détenteur pour des données de tiers. Contrôle mécanique par `scripts/check-disponibilite.py`. Pour un essai clinique, l'ICMJE impose en plus des éléments précis, listés dans la référence.

## Guides de section (article)

- Abstract : version condensée de l'étude, un volet par section IMRAD, conclusion incluse. 150 à 300 mots.
- Introduction : finir sur l'objectif, jamais sur du contexte.
- Related work ou état de l'art : situer sans dénigrer, montrer le manque que l'étude comble.
- Method : assez précis pour répliquer, ni plus ni moins.
- Experiments ou résultats : chaque résultat répond à une question posée. Tableaux à encre minimale, lisibles.
- Conclusion : résumé, limites, perspectives, sans fait nouveau.

## Barre de qualité (auto-revue cinq dimensions)

Avant de finaliser, répondre par écrit aux cinq questions, puis corriger les points non résolus.

1. Contribution : l'apport est-il clair et justifié ?
2. Clarté d'écriture : chaque paragraphe a-t-il un message en première phrase ?
3. Force expérimentale : les résultats soutiennent-ils les affirmations ?
4. Complétude de l'évaluation : manque-t-il une comparaison ou une limite ?
5. Solidité de la méthode : le protocole résiste-t-il à un évaluateur hostile ?

Contrainte dure : toute affirmation de l'abstract et de l'introduction est vérifiée contre les preuves expérimentales. Une affirmation non soutenue est affaiblie ou retirée.

## Pièges à éviter

- Écrire la discussion comme un second résultat, sans recul critique.
- Surinterpréter une corrélation en causalité.
- Présenter un résultat sans la question qu'il adresse.
- Mélanger présent et passé hors de la règle de temps.
- Laisser une abréviation non définie à sa première apparition.

## Sources

- Recommendations for the Conduct, Reporting, Editing and Publication of Scholarly Work in Medical Journals (preparing a manuscript), ICMJE, 2026. https://www.icmje.org/recommendations/browse/manuscript-preparation/preparing-for-submission.html
- Writing a Scientific Paper, University of California Irvine Libraries, 2026. https://guides.lib.uci.edu/scientificwriting

## Publics et exemples

Genre central du chercheur, il sert aussi l'ingénieur pour un rapport d'essais ou une validation expérimentale. Exemples : un chercheur publie une étude IMRAD sur un protocole ; un ingénieur documente la qualification d'un matériau (méthode, résultats, incertitudes en unités SI).
