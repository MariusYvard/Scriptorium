# Changelog

Toutes les évolutions notables de Scriptorium sont consignées ici.
Format : [Keep a Changelog](https://keepachangelog.com) ; versionnage [SemVer](https://semver.org).

---

## [Unreleased]

<!-- Les changements à venir s'ajoutent ici avant la prochaine version. -->

---

## [0.7.0] - 2026-07-09

Intégrité des sources, comité de revue durci, journal de projet. Quarante-sept mécanismes réimplémentés à neuf depuis l'étude du plugin academic-research-skills (idées seulement, licence CC BY-NC 4.0 respectée, standards cités depuis leurs sources primaires).

### Added
- Intégrité des sources : triangulation multi-index en option réseau (Crossref, OpenAlex, Semantic Scholar, similarité de titre 0,70) avec verdicts gradués par référence (vérifié, plausible, invérifiable, fabriqué) et signaux de contamination ; taxonomie des citations fabriquées ; ancre par citation dans le BibTeX (citation exacte ou localisation, `--exiger-ancres`) ; tags de lacune normalisés `[LACUNE MATERIELLE]` et `[PREUVE FAIBLE]` comptés par traceability.py ; nouveau script check-temporel.py (cinq défaillances chronologiques, consultatif par défaut) ; hiérarchie de preuve à sept niveaux et fiche source A-F ; logique GRADE générale ; chronologie des sources et garde anti-anachronisme ; corpus utilisateur pré-criblé (BibTeX, Zotero) avec traçabilité inclus/exclus. Références : integrite-sources.md, hierarchie-preuve.md, corpus-utilisateur.md, discipline-synthese.md.
- Comité de revue : contrat de notation préenregistré en aveugle pour le consensus (contrat-notation.md), anti-ancrage entre les voix et vérification croisée optionnelle par un second modèle ; discipline de concession du contradicteur (réfutations notées 1-5, jamais deux concessions consécutives, sévérité DA-CRITIQUE, détection du verrouillage de cadrage) ; plancher par axe et décision éditoriale à quatre valeurs dans scorecard.py, mode trajectoire entre deux revues (régression sous -3 = point de contrôle) ; lettre de décision (lettre-decision.md) ; biais et lentilles du relecteur (biais-relecteur.md) ; santé du dialogue anti-complaisance (sante-dialogue.md) ; 28 sophismes en six familles, critères de Bradford Hill et statuts épistémiques (sophismes-causalite.md) ; protocole d'originalité et d'auto-plagiat (plagiat.md) ; statuts fermés par remarque de relecteur dont la limite assumée, registre d'engagements, revue externe réelle (relecteurs.md étendu).
- Atelier : cadre FINER (cadre-finer.md) et boîte socratique (boite-socratique.md) au cadrage ; aiguilleur des demandes (aiguilleur.md) ; douze chemins de défaillance avec récupération (chemins-defaillance.md) ; registre des modes sur le spectre fidélité-originalité (registre-modes.md) ; schémas de passation entre sous-commandes (passations.md) ; renforcement aux transitions et bilan de fin de mission avec auto-audit dans piloter.
- Journal de projet : project.py passe en journal append-only horodaté (frontières à hash de continuité SHA-256, reprise par hash à usage unique, décision en attente reposée, états d'étapes à transitions vérifiées, versions d'artefacts strictement croissantes, tableau de bord `status`, bloc de reproductibilité honnête). Compatibilité de lecture des projet.json antérieurs conservée.
- Production : calibration d'un style personnel sur échantillons, subordonnée au style maison (style.md, mode 4) ; formats Chicago, MLA et IEEE et bascule entre formats dans citations.py ; déclarations CRediT, financement et usage de l'IA avec politiques d'éditeurs vérifiées et datées (credit-divulgation.md) ; résumé bilingue FR/EN aligné (decliner.md) ; vérification visuelle du rendu des figures (figure.md) ; nouvelle sous-commande produire veille (veille.md : requêtes par plateforme, digest, rétractations via le jeu de données Retraction Watch chez Crossref) ; contrat rédacteur-évaluateur par mission (contrat-mission.md, exemple JSON dans assets/).
- Outillage : friction à trois crans sur les passages outre de tools/check.py, journalisés et non supprimables ; glossaire transverse de sévérité (severite.md) ; principes de conception documentés (docs/CONCEPTION.md : mesure avant politique, dégradation gracieuse, jamais de moyenne qui masque un désaccord) ; contrôle de fraîcheur des sources normatives documenté (docs/CI.md) ; quatre fixtures d'evals à double usage (test et exemple de référence) ; harnais étendu d'une trentaine de cas dont un lint de prompt (références citées existantes, frontmatters d'agents, chemins périmés, sections Sources).

### Changed
- Les agents contradicteur, controle-qualite, verificateur-faits et synthese-sources intègrent les nouvelles grilles (concession, lentilles, verdicts gradués, statuts épistémiques, hiérarchie de preuve). Les routeurs des quatre compétences référencent les nouvelles sous-commandes et références transverses.

### Fixed
- Chemins périmés hérités de la réorganisation 0.6.0 dans les agents redacteur (skills/rediger/) et controle-qualite (skills/reviser/, skills/style-maison/), désormais couverts par un cas d'eval dédié.
- Virgules d'Oxford résiduelles dans consensus.md et contredire.md.

---
## [0.6.7] - 2026-06-12

Pitch : ancrage dans une valeur fondamentale et soin de la clôture.

### Added
- genre-pitch.md gagne deux principes. L'ancrage du projet dans une valeur fondamentale universelle (application concrète du recadrage moral, avec un garde-fou éthique contre la valeur plaquée sans preuve). Et le soin de l'ouverture et de la clôture, adossé à l'effet de position sérielle (Murdock, 1962) et à la règle du pic et de la fin (Kahneman et al., 1993). Deux sources primaires ajoutées.

---

## [0.6.6] - 2026-06-12

Scission du genre présentation en deux playbooks distincts.

### Changed
- Le genre présentation est scindé en deux. Présentation et soutenance (genre-presentation.md) est allégé et centré sur la conception de diapositives, le non-verbal, l'interactivité et le trac. Pitch commercial et levée de fonds (genre-pitch.md) regroupe les cadres narratifs, la règle 10/20/30, le traitement des objections, l'humour, les études de cas et le renvoi au module pitch-narratif. Vingt-cinq genres au total.

### Added
- references/genre-pitch.md. Le pitch renvoie au genre présentation pour la délivrance non verbale commune, afin d'éviter la redite.

---

## [0.6.5] - 2026-06-12

Module narratif et cadrage de valeur pour le pitch.

### Added
- references/pitch-narratif.md, boîte à outils rattachée au genre présentation : paradigme narratif (Fisher), sparkline (Duarte) et lecture du keynote iPhone, structures comparées (Freytag, sept points, SCR de Minto et McKinsey, étude de cas), cadrage de valeur (Lakoff, fondations morales de Haidt et recadrage moral de Feinberg et Willer, épisodique contre thématique de FrameWorks, ancrage de Tversky et Kahneman), approche dramaturgique du pitch et éthique du cadrage (rhétorique invitationnelle de Foss et Griffin). Dix-huit sources vérifiées.

### Changed
- Recadrages de rigueur : la base limbique du Golden Circle est présentée comme une vulgarisation et non une neuroscience établie ; la règle dite des neuf minutes est corrigée en règle des dix minutes (Medina, via Gallo) ; les fondations morales sont données avec exactitude (cinq canoniques, la liberté restant une candidate) ; la recherche sur les émotions faciales est située sur des pitchs de financement participatif.

---

## [0.6.4] - 2026-06-12

Volet humour ajouté au playbook pitch, traité comme un levier à risque.

### Added
- Section Humour du genre présentation : mécanique d'écriture (formule attitude-sujet-prémisse-chute, règle de trois, mot-clé en fin de phrase), autodérision et empathie de situation. Traitement rigoureux des risques : downside asymétrique (Bitterly, Brooks et Schweitzer, 2017), biais de genre (Evans et al., Journal of Applied Psychology, 2019), rire contraint sous asymétrie de pouvoir (Harvard Business Review, 2025). Sources ajoutées (Aaker et Bagdonas, Nihill, Klaff, Kerr).

---

## [0.6.3] - 2026-06-12

Playbook pitch enrichi et sourcé.

### Changed
- Le genre présentation devient un playbook de pitch complet (soutenance, vente, levée de fonds) : cadres narratifs (cascade, Golden Circle de Sinek, Show and Tell de Roam), règle 10/20/30 de Kawasaki et répartition temporelle, conception des diapositives, délivrance non verbale (kinésique, proxémique, paraverbal), règle 7-38-55 de Mehrabian recadrée pour en éviter la surinterprétation, interactivité et brise-glaces calibrés par taille d'auditoire, régulation du trac, traitement des objections, études de cas (SécurClés, YouTube, Airbnb).

### Added
- Sources d'autorité sur la persuasion orale : Kawasaki (10/20/30), Sinek (Golden Circle), Mehrabian (7-38-55 et sa portée réelle), Ekman (micro-expressions), Roam (Show and Tell), Bpifrance et CCI.

---

## [0.6.2] - 2026-06-12

Treize genres et six publics supplémentaires, chaque genre adossé à des sources faisant autorité.

### Added
- Treize genres sourcés : demande de financement et proposition de recherche, dissertation et commentaire, business plan, proposition commerciale et réponse à appel d'offres, étude de marché, documentation technique (Diátaxis), rapport d'incident et post-mortem, note d'analyse financière, rapport d'évaluation (critères OCDE/CAD), livre blanc, discours et allocution, conclusions et mémoire contentieux, rédaction de contrat. Vingt-quatre genres au total.
- Six publics : analyste financier, entrepreneur, enseignant, chef de projet, agent public, journaliste. Quatorze publics au total.
- Section Sources dans chaque playbook, adossée à des standards et guides vérifiés (ICMJE, PRISMA 2020, IEEE/ISO/IEC 29148, INCOSE, Google SRE, CFA Institute, OCDE/CAD, IRAC, CARE, CONSORT, STROBE, Diátaxis, entre autres). Profils de discipline portés à quinze, avec leurs sources normatives.
- Conventions de mise en forme pour les treize nouveaux genres.

### Changed
- Description et section publics de produire ouvertes aux vingt-quatre genres et quatorze publics.
- evals portés à 39 cas (présence d'une section Sources dans chaque playbook).

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
