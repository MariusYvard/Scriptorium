<p align="center">
  <img src="docs/banner.svg" alt="Scriptorium" width="100%">
</p>

<p align="center">
  <a href="https://github.com/MariusYvard/Scriptorium/actions/workflows/evals.yml"><img src="https://github.com/MariusYvard/Scriptorium/actions/workflows/evals.yml/badge.svg" alt="evals"></a>
  <a href="https://github.com/MariusYvard/Scriptorium/releases"><img src="https://github.com/MariusYvard/Scriptorium/actions/workflows/release.yml/badge.svg" alt="release"></a>
  <img src="https://img.shields.io/badge/version-0.7.0-1f6feb" alt="version 0.7.0">
  <img src="https://img.shields.io/badge/licence-MIT-3da639" alt="licence MIT">
  <img src="https://img.shields.io/badge/python-stdlib%20pur-3776ab" alt="python stdlib pur">
  <img src="https://img.shields.io/badge/genres-25%20sourc%C3%A9s-8957e5" alt="25 genres sourcés">
</p>

<p align="center"><b>Décrivez la cible. Scriptorium cadre, source, rédige, révise et met en forme un document rigoureux, sous le contrôle de garde-fous déterministes.</b></p>

Scriptorium est un plugin Claude (Cowork et Claude Code) qui transforme une demande de rédaction en document fini. Il applique une méthodologie d'ingénierie textuelle, déplace la rigueur vérifiable du jugement du modèle vers dix-neuf scripts déterministes, et impose un style maison à directives strictes. Quatre compétences couvrent le cycle de vie complet, du cadrage à la livraison, sur vingt-cinq genres adossés chacun à des sources faisant autorité.

## Comment ça marche

```mermaid
flowchart LR
  A["<b>atelier</b><br/>piloter · cadrer · projet"] --> P["<b>produire</b><br/>genre · sourcer · veille · figure · tableau<br/>equation · style · charte · image"]
  P --> C["<b>controler</b><br/>revue · contredire · consensus<br/>humaniser · audit · relecteurs"]
  C --> L["<b>livrer</b><br/>document · decliner"]
  L --> O(["Word · PDF · HTML · PowerPoint"])
```

Deux moteurs travaillent ensemble. Le modèle tranche le jugement : rédiger, classer, résumer, décrire une image, formuler une contre-thèse. Le code tranche le mécanique et le reproductible : détecter un tiret cadratin, nettoyer une URL, trianguler un DOI contre trois index, noter un document sur cent, suivre la trajectoire d'une note entre deux revues. Une affirmation majeure sans preuve cartographiée est affaiblie ou retirée, c'est une contrainte dure et non une préférence.

## Installation

Télécharger `scriptorium-0.7.0.plugin` depuis la [page des releases](https://github.com/MariusYvard/Scriptorium/releases), puis l'installer.

- Cowork : ouvrir le fichier `.plugin` et accepter l'installation.
- Claude Code : `/plugin marketplace add MariusYvard/Scriptorium`, puis installer le plugin `scriptorium`.

Les compétences apparaissent sous le préfixe `scriptorium:`. Les scripts et le harnais d'évaluation tournent en Python sans dépendance (`python3 evals/run-evals.py`).

## Les quatre compétences

| Compétence | Sous-commandes | Rôle |
| --- | --- | --- |
| `atelier` | piloter · cadrer · projet | Point d'entrée. Orchestre la production de A à Z avec bilan de fin de mission, cadre et qualifie le sujet (cadre FINER, dialogue socratique), tient le journal de projet entre les sessions (frontières, reprise par hash, tableau de bord). |
| `produire` | genre · sourcer · revue-litterature · veille · figure · tableau · equation · style · charte · image | Produit le contenu et fixe la forme. Rédige les vingt-cinq genres, trouve, pondère et triangule les sources, met en place une veille documentaire, génère figures et tableaux, pose les équations, applique style et charte, extrait les images d'un document source. |
| `controler` | revue · contredire · consensus · humaniser · audit · relecteurs | Éprouve un écrit. Revue adversariale, contradiction disciplinée (Toulmin, seuil de concession), consensus sur contrat de notation préenregistré, détection d'empreinte IA, audit d'un document existant avec contrôle d'originalité, réponse aux relecteurs avec registre d'engagements et trajectoire de score. |
| `livrer` | document · decliner | Met en forme le livrable (Word, PDF, HTML) et le décline par canal (présentation, résumé, résumé bilingue FR/EN, abstract, post, communiqué). |

Chaque sous-commande charge à la demande son fichier de référence, le contexte reste léger. Décrire la cible suffit à déclencher la bonne action ; il est aussi possible de nommer l'action, par exemple `produire figure`.

## En une demande

> « Rédige une analyse stratégique de 20 pages sur le marché X pour mon comité de direction, avec un SWOT et un PESTEL. »

`atelier` enchaîne le cadrage (problématique fermée, plan validé), le sourcing (sources pondérées, carte preuve-affirmation), la rédaction déléguée section par section à l'agent `redacteur`, les figures SWOT et PESTEL produites en SVG, la revue adversariale, puis la mise en forme à la charte. Trois points de contrôle reviennent vers vous : le périmètre, la suffisance des preuves, le verdict de révision.

## Garde-fous déterministes

Dix-neuf scripts en Python pur déplacent la rigueur du jugement du modèle vers un contrôle mécanique et reproductible. Une porte d'intégration continue (`tools/check.py`) verrouille un document contre un seuil de note, et passer outre exige une justification à friction croissante, journalisée.

| Script | Ce qu'il attrape |
| --- | --- |
| `lint-style.py` | Tiret cadratin, typographie courbe, lexique promotionnel, virgule d'Oxford, métadiscours, paramètres de suivi. |
| `verify-sources.py` | URL à nettoyer, doublons, DOI douteux ; en option réseau, triangulation Crossref, OpenAlex et Semantic Scholar avec verdicts gradués et signaux de contamination. |
| `citations.py` | Cinq formats de bibliographie (APA 7, Vancouver, Chicago, MLA, IEEE), bascule entre formats, ancres par citation (citation exacte ou localisation), dédoublonnage par DOI. |
| `check-temporel.py` | Futur présenté comme passé, inversion causale, version anachronique, langage à péremption, chaîne de dates incohérente. |
| `scorecard.py` | Note déterministe de 0 à 100 sur cinq axes, calcul montré, plancher par axe, décision éditoriale, trajectoire entre deux revues. |
| `traceability.py` | Références orphelines ou pendantes, appels de figures et de tableaux, tags de lacune normalisés. |
| `ai-fingerprint.py` | Rythme uniforme, ouvertures répétées, cadence ternaire, connecteurs suremployés. |
| `numbers.py` | Pourcentages impossibles, partitions qui ne somment pas, séparateur décimal mixte. |
| `project.py` | Journal de mission append-only, frontières à hash de continuité, reprise unique, états d'étapes, versions d'artefacts, tableau de bord. |
| `theme.py` | Validation de charte, contraste WCAG, émission du CSS du HTML. |
| `images.py` | Extraction d'images (Office, PDF), déduplication, dimensions, manifeste. |

Le catalogue complet est dans [`scripts/README.md`](scripts/README.md). Un hook lance le linter après chaque écriture et bloque la finalisation tant qu'un écart critique subsiste.

## Intégrité des sources

La vérification d'une source va plus loin que l'existence d'une URL. La triangulation multi-index rend un verdict gradué par référence (vérifié, plausible, invérifiable, fabriqué), une taxonomie des citations fabriquées sert de grille de lecture, chaque citation porte une ancre vérifiable (citation exacte ou localisation précise), les affirmations causales datées passent un contrôle chronologique, et les lacunes s'affichent en tags normalisés (`[LACUNE MATERIELLE]`, `[PREUVE FAIBLE]`) comptés par le linter. Une hiérarchie de preuve à sept niveaux et une fiche de notation A-F pondèrent chaque source, et une bibliothèque personnelle fournie (BibTeX, Zotero) est pré-criblée aux mêmes critères que les sources externes, sans écarter quoi que ce soit en silence.

## Comité de revue

Le consensus fait voter trois agents qui s'engagent chacun, avant de lire le document, sur un contrat de notation préenregistré : dimensions d'acceptation, conditions d'échec, procédure de mesure. Aucune moyenne ne masque un désaccord, aucun verdict n'est montré aux voix qui n'ont pas encore voté, et un axe effondré plafonne la décision malgré un bon total. Le contradicteur note chaque réfutation reçue de 1 à 5 et ne concède qu'à 4 ou plus, jamais deux fois de suite. La re-revue suit la trajectoire de score axe par axe et toute régression marquée déclenche un point de contrôle. La réponse aux relecteurs porte quatre statuts fermés par remarque, dont la limite assumée (un désaccord argumenté est une issue légitime), et un registre d'engagements vérifiés indépendamment.

## Vingt-cinq genres sourcés

Chaque genre est adossé à des sources faisant autorité, citées dans son playbook (`skills/produire/references/genre-*.md`).

- Académique et recherche : rapport scientifique et mémoire (IMRAD), article, revue de littérature (PRISMA), demande de financement et proposition de recherche, dissertation et commentaire.
- Entreprise et conseil : long rapport décisionnel, analyse stratégique (SWOT, PESTEL, 5 forces, Mactor), prospective, étude de cas, business plan, étude de marché, proposition commerciale et réponse à appel d'offres.
- Technique : cahier des charges et spécification (IEEE 29148), documentation technique (Diátaxis), rapport d'incident et post-mortem.
- Finance : note d'analyse financière et mémo d'investissement.
- Public et droit : note de politique publique, rapport d'évaluation (critères OCDE/CAD), note et consultation juridique (IRAC), conclusions et mémoire contentieux, rédaction de contrat.
- Santé : cas clinique et protocole de recherche (CARE, CONSORT, STROBE, PRISMA).
- Communication : livre blanc, discours et allocution, présentation (soutenance), pitch (commercial et levée de fonds).

## Quatorze publics

| Public | Genres de prédilection |
| --- | --- |
| Chercheur | Rapport scientifique IMRAD, article, revue de littérature, demande de financement. |
| Ingénieur | Cahier des charges, documentation technique, post-mortem, étude de cas. |
| Analyste géopolitique | Analyse stratégique (Mactor, PESTEL), prospective, note de politique publique. |
| Juriste | Note et consultation juridique (IRAC), conclusions contentieuses, contrat. |
| Professionnel de santé | Cas clinique, protocole de recherche (CARE, CONSORT, STROBE). |
| Consultant et dirigeant | Long rapport décisionnel, analyse stratégique, business plan. |
| Communicant et marketing | Livre blanc, article, présentation, étude de marché. |
| Étudiant | Dissertation et commentaire, mémoire, présentation de soutenance. |
| Analyste financier | Note d'analyse financière, mémo d'investissement. |
| Entrepreneur | Business plan, étude de marché, proposition commerciale, pitch. |
| Enseignant | Support de cours, dissertation, présentation. |
| Chef de projet | Cahier des charges, proposition commerciale, rapport d'évaluation. |
| Agent public | Note de politique publique, rapport d'évaluation. |
| Journaliste | Article, enquête, tribune. |

La méthode et le style maison ne changent pas, seuls le genre et les exemples s'adaptent au domaine. Les profils de discipline (voir `controler` consensus) calibrent la norme de citation et le seuil d'exigence.

## Formats de sortie

Le format de travail est le Markdown. La finalisation produit un document Word (`.docx`), un PDF, un HTML autonome dont le CSS dérive de la charte graphique (jetons, focus visible, feuille d'impression, source idéale pour un PDF fidèle), ou une présentation PowerPoint. Les figures sortent en SVG, les tableaux en Markdown, les équations en PDF via LaTeX, et les images d'un document source sont extraites puis replacées, numérotées et à la charte. Un document destiné à une publication peut porter ses déclarations de contribution (CRediT), de financement et d'usage de l'IA selon la politique du support visé.

## Style maison

Le style par défaut applique des directives strictes : registre encyclopédique et neutre, zéro tiret cadratin, pas de virgule d'Oxford, guillemets et apostrophes droits, lexique promotionnel banni, faits précis ou rien, sources vérifiées sans paramètres de suivi. Il vit dans [`skills/produire/references/directives-strictes.md`](skills/produire/references/directives-strictes.md) et le linter applique les mêmes règles. La compétence `produire` (style) peut régénérer une charte à partir de vos écrits, ou calibrer un style personnel sur des échantillons fournis, toujours subordonné au style maison et aux conventions de la discipline.

## Agents délégués

Le travail lourd est confié à cinq agents lancés via l'outil Task : `redacteur` (rédaction long-format), `controle-qualite` (validation structurée, trois lentilles, biais de relecteur auto-appliqués), `synthese-sources` (recherche, hiérarchie de preuve, chronologie), `contradicteur` (contre-thèse, discipline de concession), `verificateur-faits` (vérification factuelle à verdicts gradués, statuts épistémiques). Sur un échange long, chaque agent garde un auto-contrôle de santé du dialogue contre la complaisance.

## Évaluations et release

`evals/run-evals.py` relie des cas piégés à des attentes précises et vérifie que les garde-fous attrapent ce qu'ils doivent : règles du linter, verdicts des scripts, mais aussi la cohérence du plugin lui-même (chaque référence citée par un routeur existe, chaque agent porte son frontmatter, aucun chemin périmé, chaque playbook et chaque nouvelle référence porte sa section Sources). La publication est automatisée : un tag `vX.Y.Z` déclenche la vérification des versions, les evals, la construction du `.plugin` et la création de la Release. Voir [`docs/RELEASE.md`](docs/RELEASE.md) et [`CHANGELOG.md`](CHANGELOG.md).

## Inspirations

Les principes de conception du plugin sont documentés dans [`docs/CONCEPTION.md`](docs/CONCEPTION.md). Une partie des mécanismes d'intégrité et de revue de la version 0.7.0 réimplémente à neuf, en français et dans l'architecture de Scriptorium, des idées observées dans le plugin [academic-research-skills](https://github.com/Imbad0202/academic-research-skills) de Cheng-I Wu (CC BY-NC 4.0) : aucun texte n'en est repris, et les standards cités (PRISMA, CRediT, GRADE, Bradford Hill) le sont depuis leurs sources primaires.

## Licence

MIT. Voir [`LICENSE`](LICENSE).
