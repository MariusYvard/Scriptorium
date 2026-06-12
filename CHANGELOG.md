# Changelog

Toutes les évolutions notables de Scriptorium sont consignées ici.
Format : [Keep a Changelog](https://keepachangelog.com) ; versionnage [SemVer](https://semver.org).

---

## [Unreleased]

<!-- Les changements à venir s'ajoutent ici avant la prochaine version. -->

---

## [0.6.1] - 2026-06-12

Cinq genres et cinq publics, README visuel, automatisation de release.

### Added
- Cinq genres : note de politique publique (policy brief), note et consultation juridique (méthode IRAC), cahier des charges et spécification technique, cas clinique et protocole de recherche (CONSORT, PRISMA, STROBE), présentation (soutenance et pitch). Onze genres au total.
- Cinq publics : juriste, professionnel de santé, consultant et dirigeant, communicant et marketing, étudiant. Huit publics au total, avec leurs profils de discipline.
- README refondu : bannière SVG adaptative (thème clair ou sombre), badges, diagramme Mermaid du fonctionnement, exemple concret, tableau des garde-fous déterministes.
- Automatisation de release : workflow `.github/workflows/release.yml` (un tag `vX.Y.Z` vérifie que le tag correspond à `plugin.json` et `marketplace.json` et qu'une section CHANGELOG existe, lance les evals, construit `scriptorium-X.Y.Z.plugin` et publie la Release avec ses notes et l'artefact) et ce `CHANGELOG.md`.

### Changed
- Description et section publics de `produire` ouvertes aux onze genres et huit publics.
- Conventions de mise en forme ajoutées pour les cinq nouveaux genres ; profils de discipline étendus (communication et marketing, présentation et soutenance, travail étudiant).

---

## [0.6.0] - 2026-06-11

Simplification de l'usage, sortie HTML et extraction d'images. Plugin ouvert au chercheur, à l'ingénieur et à l'analyste géopolitique.

### Changed
- Dix-neuf compétences ramenées à quatre à sous-commandes : `atelier` (piloter, cadrer, projet), `produire` (genre, sourcer, revue-litterature, figure, tableau, equation, style, charte, image), `controler` (revue, contredire, consensus, humaniser, audit, relecteurs), `livrer` (document, decliner). Chaque ancienne compétence devient une sous-commande chargée à la demande depuis `references/`, les routeurs `SKILL.md` restent légers.
- Descriptions et exemples ouverts aux trois publics. Profil de discipline analyse géopolitique ajouté à la sous-commande consensus.

### Added
- Sortie HTML autonome pilotée par la charte graphique : `scripts/theme.py --format css` (jetons `:root`, propriétés logiques, mesure fluide, focus visible, feuille d'impression) et une section HTML dans `livrer` (document) alignée sur des standards d'HTML propre (sémantique, jetons, WCAG 2.2). Le HTML sert de source pour un PDF fidèle.
- Extraction et placement d'images : `scripts/images.py` (Office .docx/.pptx/.xlsx et ODF via `zipfile` en pur stdlib ; PDF via PyMuPDF, pdfimages ou pypdf, sinon repli sur le skill pdf ; déduplication par empreinte, lecture des dimensions, signalement EMF/WMF, manifeste JSON) et la sous-commande `produire` (image), où le modèle rédige l'alt et la légende, le script ne juge rien.
- `evals/run-evals.py` porté à 37 cas (theme css, extraction d'images).

---

## [0.5.0] - 2026-06-11

### Added
- Persistance, cohérence d'ensemble et intégration continue éditoriale : mémoire de projet (`project.py`), conformité au plan (`plan-check.py`), empreinte IA (`ai-fingerprint.py`), cohérence interne (`coherence.py`), génération et audit de tableaux (`tables.py`), audit consolidé (`audit-doc.py`), porte d'intégration continue (`tools/check.py`). Compétences memoire-projet, auditer-existant, tableaux, revue-litterature, humaniser. evals 32 cas.

---

## [0.4.0] - 2026-06-11

### Added
- Colonne déterministe étendue : scorecard 0-100 (`scorecard.py`), traçabilité (`traceability.py`), terminologie (`terminology.py`), intégrité numérique (`numbers.py`), citations BibTeX (`citations.py`), diff de versions (`diff-versions.py`). Compétences equations, repondre-relecteurs, decliner, consensus. Agent verificateur-faits. evals 25 cas.

---

## [0.3.0] - 2026-06-11

### Added
- Charte graphique appliquée au texte et aux figures : `scripts/theme.py` (contrôle de contraste WCAG), `figures.py --theme`, compétence charte-graphique, exemple `assets/charte-graphique.exemple.json`. evals 17 cas.

---

## [0.2.0] - 2026-06-10

### Added
- Scripts déterministes (style, sources, lisibilité, figures), hook d'application, compétences finaliser, schematiser, contredire, agent contradicteur, harnais d'évaluation, maturité de distribution.

---

## [0.1.0] - 2026-06-10

### Added
- Six compétences (atelier, cadrer, sourcer, rediger, reviser, style-maison), trois agents, playbooks de genre, boîtes à outils stratégie et prospective, style maison à directives strictes.
