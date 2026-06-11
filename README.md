# Scriptorium

[![evals](https://github.com/MariusYvard/Scriptorium/actions/workflows/evals.yml/badge.svg)](https://github.com/MariusYvard/Scriptorium/actions/workflows/evals.yml)

Atelier de rédaction de haut niveau pour six genres d'écrits professionnels, académiques et stratégiques. Le plugin transforme une demande floue en document rigoureux, structuré et sourcé, en appliquant une méthodologie d'ingénierie textuelle, des garde-fous déterministes et un style maison à directives strictes.

Version 0.5.0.

## Installation

Télécharger le fichier `.plugin` depuis la page des releases, puis l'installer.

- Cowork : ouvrir `scriptorium-0.5.0.plugin` et accepter l'installation.
- Claude Code : `/plugin marketplace add MariusYvard/Scriptorium`, puis installer le plugin `scriptorium` depuis ce marketplace.

Les compétences apparaissent ensuite sous le préfixe `scriptorium:` (atelier, cadrer, rediger, reviser, sourcer, finaliser et les autres). Les scripts déterministes et le harnais d'évaluation tournent en Python sans dépendance (`python3 evals/run-evals.py`).

## Genres couverts

1. Rapport scientifique et mémoire universitaire (structure IMRAD, normes APA 7 ou Vancouver).
2. Article (blog, tribune, vulgarisation, article scientifique original).
3. Long rapport professionnel et décisionnel (constat, diagnostic, recommandations budgétées).
4. Analyse stratégique (SWOT, PESTEL, 5 forces de Porter, BCG, McKinsey 7S, Mactor, Ansoff).
5. Rapport de prospective (signaux faibles, scénarios contrastés, méthode Horizons Canada).
6. Étude de cas d'affaires (contexte, problématique MECE, démarche, bénéfices mesurés).

## Compétences

| Compétence | Rôle |
| --- | --- |
| `atelier` | Pilote le pipeline complet de A à Z (cadrage, sourcing, rédaction, révision, finalisation) |
| `cadrer` | Cadre le sujet, applique les cinq filtres de délimitation, formule la problématique, bâtit le plan |
| `sourcer` | Trouve, pondère et vérifie les sources, formate les citations, construit la carte preuve-affirmation |
| `rediger` | Moteur de rédaction unifié qui charge le playbook du genre et applique le style maison |
| `reviser` | Revue adversariale et contrôle qualité (preuve-affirmation, sévérité, verdict, auto-revue 5 dimensions) |
| `style-maison` | Génère, applique ou fait respecter la charte éditoriale |
| `finaliser` | Met en forme le livrable (Word ou PDF) selon les conventions du genre |
| `schematiser` | Génère des figures stratégiques en SVG et porte un regard critique avant insertion |
| `contredire` | Éprouve une thèse par la contradiction la plus forte (modèle de Toulmin) |
| `charte-graphique` | Définit, applique et valide une identité visuelle (couleurs, polices, accent) sur le texte et les figures |
| `equations` | Équations LaTeX, unités SI, chiffres significatifs, export PDF |
| `repondre-relecteurs` | Réponse point par point aux relecteurs et version en modifications suivies |
| `decliner` | Décline un document validé en présentation, résumé, abstract, post, communiqué |
| `consensus` | Revue par vote de trois agents, ancrée sur le scorecard, profils de discipline |
| `memoire-projet` | Conserve et recharge le contexte du projet (brief, charte, glossaire, sources, profil, plan) |
| `auditer-existant` | Audite un PDF ou un Word existant : extraction puis scorecard et contrôles |
| `tableaux` | Génère des tableaux autonomes et audite les tableaux existants |
| `revue-litterature` | Synthèse multi-documents, tableau de preuves dédupliqué, schéma PRISMA |
| `humaniser` | Détecte et corrige l'empreinte d'un texte généré |

## Agents délégués

Le travail lourd est confié à cinq agents lancés via l'outil Task.

1. `redacteur` (sonnet) : rédaction long-format multi-contraintes.
2. `controle-qualite` (haiku) : validation structurée, pré-passe déterministe puis jugement du fond.
3. `synthese-sources` (sonnet) : recherche, pondération, triangulation, score de confiance.
4. `contradicteur` (sonnet) : contre-thèse la plus forte, points de rupture, verdict.
5. `verificateur-faits` (sonnet) : vérification factuelle des affirmations contre les sources, verdict.

## Garde-fous déterministes

Dix-sept scripts en Python pur (bibliothèque standard) déplacent la rigueur du jugement du modèle vers un contrôle mécanique et reproductible. Voir `scripts/README.md`. Une porte d'intégration continue éditoriale (`tools/check.py`) verrouille un document contre un seuil de scorecard, voir `docs/CI.md`.

- `scripts/lint-style.py` : détecte les écarts au style maison (tiret cadratin, typographie courbe, lexique banni, paramètres de suivi, virgule d'Oxford, métadiscours, pronom « on »).
- `scripts/verify-sources.py` : nettoie les URL, repère les doublons, contrôle les DOI.
- `scripts/readability.py` : chiffre le rythme (longueur de phrase, écart-type, indice LIX, densité lexicale, taux de passif).
- `scripts/figures.py` : génère les figures stratégiques (option `--theme` pour la charte graphique) et porte un audit critique déterministe.
- `scripts/theme.py` : charge et valide une charte graphique, contrôle le contraste WCAG.
- `scripts/traceability.py` : références orphelines ou pendantes, appels de figures et tableaux.
- `scripts/terminology.py` : glossaire des sigles, sigles non définis, variantes orthographiques.
- `scripts/numbers.py` : pourcentages impossibles, partitions qui ne somment pas, séparateur décimal mixte.
- `scripts/citations.py` : BibTeX vers APA 7 ou Vancouver, déduplication par DOI, résolution DOI optionnelle.
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

Décrire la cible suffit. Par exemple : « Rédige une analyse stratégique de 20 pages sur le marché X pour mon comité de direction. » La compétence `atelier` enchaîne le cadrage, le sourcing, la rédaction, la révision et la mise en forme. Pour garder la main étape par étape, appeler directement `cadrer`, puis `sourcer`, puis `rediger`, puis `reviser`, puis `finaliser`.

## Sources et connecteurs

Le plugin fonctionne en autonomie et utilise la recherche web. Les connecteurs (gestionnaire de références, base de connaissances) sont optionnels, voir `CONNECTORS.md`.

## Personnalisation

Le style maison vit dans `skills/style-maison/references/directives-strictes.md`. Le linter applique les mêmes règles. La compétence `style-maison` peut régénérer une charte à partir de vos écrits.

## Release

Voir `docs/RELEASE.md` pour la procédure versionnée.
