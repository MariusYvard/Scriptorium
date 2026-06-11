# Scriptorium

[![evals](https://github.com/MariusYvard/Scriptorium/actions/workflows/evals.yml/badge.svg)](https://github.com/MariusYvard/Scriptorium/actions/workflows/evals.yml)

Atelier de rédaction de haut niveau pour le chercheur, l'ingénieur et l'analyste géopolitique. Le plugin transforme une demande floue en document rigoureux, structuré et sourcé, en appliquant une méthodologie d'ingénierie textuelle, des garde-fous déterministes et un style maison à directives strictes.

Version 0.6.0.

## Installation

Télécharger le fichier `.plugin` depuis la page des releases, puis l'installer.

- Cowork : ouvrir `scriptorium-0.6.0.plugin` et accepter l'installation.
- Claude Code : `/plugin marketplace add MariusYvard/Scriptorium`, puis installer le plugin `scriptorium`.

Quatre compétences à sous-commandes apparaissent sous le préfixe `scriptorium:` (atelier, produire, controler, livrer). Les scripts déterministes et le harnais d'évaluation tournent en Python sans dépendance (`python3 evals/run-evals.py`).

## Quatre compétences, des sous-commandes

| Compétence | Sous-commandes | Rôle |
| --- | --- | --- |
| `atelier` | piloter, cadrer, projet | Point d'entrée : orchestration de A à Z, cadrage du sujet, mémoire de projet entre sessions |
| `produire` | genre, sourcer, revue-litterature, figure, tableau, equation, style, charte | Produit le contenu et fixe la forme : rédaction des six genres, sources, figures, tableaux, équations, style maison, charte graphique |
| `controler` | revue, contredire, consensus, humaniser, audit, relecteurs | Éprouve un écrit : revue adversariale, contradiction, vote de consensus, empreinte IA, audit d'un document existant, réponse aux relecteurs |
| `livrer` | document, decliner | Met en forme (Word, PDF, HTML) et décline par canal (deck, résumé, abstract, post, communiqué) |

Chaque sous-commande charge à la demande son fichier dans `references/`, le contexte reste léger. Décrire la cible suffit, la bonne compétence et la bonne action se déclenchent ; on peut aussi nommer l'action (par exemple `produire figure`).

## Trois publics

- Chercheur : rapport scientifique IMRAD, article, revue de littérature, normes APA 7 ou Vancouver.
- Ingénieur : long rapport technique, étude de cas, rapport d'essais, équations et unités SI.
- Analyste géopolitique : analyse stratégique (PESTEL, jeu d'acteurs Mactor, 5 forces de Porter), prospective (signaux faibles, scénarios contrastés).

La méthode et le style maison ne changent pas, seuls le genre et les exemples s'adaptent au domaine.

## Genres couverts

1. Rapport scientifique et mémoire universitaire (structure IMRAD, normes APA 7 ou Vancouver).
2. Article (blog, tribune, vulgarisation, article scientifique original).
3. Long rapport professionnel et décisionnel (constat, diagnostic, recommandations budgétées).
4. Analyse stratégique (SWOT, PESTEL, 5 forces de Porter, BCG, McKinsey 7S, Mactor, Ansoff).
5. Rapport de prospective (signaux faibles, scénarios contrastés, méthode Horizons Canada).
6. Étude de cas d'affaires (contexte, problématique MECE, démarche, bénéfices mesurés).

## Formats de sortie

Le format natif de travail est le Markdown. La finalisation (`livrer` action document) produit :

- Word (.docx) via le skill `docx`.
- PDF via le skill `pdf`.
- HTML autonome dont le CSS dérive de la charte graphique (couleurs, polices, accent, rayon), figures SVG embarquées, feuille d'impression. Le HTML offre la plus grande marge de mise en forme et sert de source pour un PDF fidèle à la charte.
- Présentation (.pptx) via le skill `pptx` pour une soutenance ou un deck.

Les figures sortent en SVG (PNG possible via cairosvg), les tableaux en Markdown, les équations en PDF via LaTeX.

## Agents délégués

Le travail lourd est confié à cinq agents lancés via l'outil Task.

1. `redacteur` (sonnet) : rédaction long-format multi-contraintes.
2. `controle-qualite` (haiku) : validation structurée, pré-passe déterministe puis jugement du fond.
3. `synthese-sources` (sonnet) : recherche, pondération, triangulation, score de confiance.
4. `contradicteur` (sonnet) : contre-thèse la plus forte, points de rupture, verdict.
5. `verificateur-faits` (sonnet) : vérification factuelle des affirmations contre les sources, verdict.

## Garde-fous déterministes

Dix-sept scripts en Python pur (bibliothèque standard) déplacent la rigueur du jugement du modèle vers un contrôle mécanique et reproductible. Voir `scripts/README.md`. Une porte d'intégration continue éditoriale (`tools/check.py`) verrouille un document contre un seuil de scorecard, voir `docs/CI.md`.

- `scripts/lint-style.py` : détecte les écarts au style maison.
- `scripts/verify-sources.py` : nettoie les URL, repère les doublons, contrôle les DOI.
- `scripts/readability.py` : chiffre le rythme (longueur de phrase, écart-type, indice LIX, densité lexicale, taux de passif).
- `scripts/figures.py` : génère les figures stratégiques (option `--theme`) et porte un audit critique.
- `scripts/theme.py` : charge et valide une charte graphique, contrôle le contraste WCAG, émet le CSS du HTML (`--format css`).
- `scripts/traceability.py` : références orphelines ou pendantes, appels de figures et tableaux.
- `scripts/terminology.py` : glossaire des sigles, sigles non définis, variantes orthographiques.
- `scripts/numbers.py` : pourcentages impossibles, partitions qui ne somment pas, séparateur décimal mixte.
- `scripts/citations.py` : BibTeX vers APA 7 ou Vancouver, déduplication par DOI.
- `scripts/diff-versions.py` : journal des écarts entre deux versions.
- `scripts/scorecard.py` : note déterministe de 0 à 100 sur cinq axes, calcul montré.
- `scripts/ai-fingerprint.py` : marqueurs d'empreinte IA (rythme, ouvertures, connecteurs, cadence ternaire).
- `scripts/coherence.py` : paragraphes quasi dupliqués, redites, promesses à vérifier.
- `scripts/tables.py` : génère un tableau depuis CSV ou JSON, audite les tableaux d'un document.
- `scripts/plan-check.py` : conformité du document au plan validé.
- `scripts/project.py` : mémoire de projet (projet.json).
- `scripts/audit-doc.py` : audit consolidé (scorecard, empreinte IA, cohérence, tableaux).

Un hook (`hooks/hooks.json`) lance le linter après chaque écriture de document et bloque la finalisation tant qu'un écart critique subsiste. Sur Windows, remplacer `python3` par `python` dans le hook si nécessaire.

## Harnais d'évaluation

`evals/run-evals.py` relie des cas piégés à des attentes précises et vérifie que les garde-fous attrapent ce qu'ils doivent. Lancer avant toute release :

```
python3 evals/run-evals.py
```

## Principe directeur

Tout écrit suit le triptyque annonce, développement, synthèse, progresse selon la logique connu-inconnu, et n'avance aucune affirmation majeure sans preuve cartographiée. Le style maison par défaut applique des règles strictes : registre encyclopédique et neutre, zéro tiret cadratin, pas de virgule d'Oxford, lexique promotionnel banni, faits précis ou rien, sources vérifiées sans paramètres de suivi.

## Usage

Décrire la cible suffit. Par exemple : "Rédige une analyse stratégique de 20 pages sur le marché X pour mon comité de direction." La compétence `atelier` (piloter) enchaîne le cadrage, le sourcing, la rédaction, la révision et la mise en forme. Pour garder la main étape par étape, appeler une action précise : `atelier` (cadrer), puis `produire` (sourcer), puis `produire` (genre), puis `controler` (revue), puis `livrer` (document).

## Sources et connecteurs

Le plugin fonctionne en autonomie et utilise la recherche web. Les connecteurs (gestionnaire de références, base de connaissances) sont optionnels, voir `CONNECTORS.md`.

## Personnalisation

Le style maison vit dans `skills/produire/references/directives-strictes.md`. Le linter applique les mêmes règles. La compétence `produire` (style) peut régénérer une charte à partir de vos écrits.

## Release

Voir `docs/RELEASE.md` pour la procédure versionnée.
