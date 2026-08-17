# Conventions de mise en forme par genre

Spécifications appliquées à l'étape de finalisation. Le fond est déjà validé, seule la forme s'ajoute.

## Rapport scientifique et mémoire

- Page de garde : titre précis exprimant le maximum d'information, auteur, institution, date, encadrant.
- Pages liminaires : sommaire paginé, liste des tableaux, liste des figures, liste des abréviations (chaque sigle défini à sa première occurrence dans le texte).
- Corps : texte justifié, police classique (Times ou Arial) en 11 ou 12, interligne 1,5, marges 2,5 cm, pagination en pied de page.
- Titres hiérarchisés et numérotés (1, 1.1, 1.1.1).
- Figures et tableaux numérotés, titrés, sourcés. Tableau 1 réservé aux caractéristiques de la population pour un article.
- Bibliographie : APA 7 ou Vancouver, une seule norme, par ordre alphabétique ou d'apparition selon la norme.
- Annexes numérotées, appelées depuis le texte.

## Article

- Titre, chapô (deux à trois phrases qui posent l'enjeu), intertitres.
- Pas de page de garde lourde.
- Références en fin, liens nettoyés des paramètres de suivi.
- Mise en page aérée, paragraphes courts.

## Long rapport professionnel

- Page de garde, résumé analytique en tête (une à cinq pages, autonome).
- Sommaire paginé, en-têtes et pieds de page (titre du rapport, pagination).
- Encadrés pour les chiffres clés et les décisions.
- Annexes numérotées pour les données détaillées.

## Analyse stratégique

- Synthèse en tête (forces du diagnostic, choix retenu).
- Figures intégrées (SWOT, PESTEL, BCG, Ansoff) numérotées et sourcées, produites par `produire` (figure).
- Plan opérationnel en tableau, chaque axe avec son indicateur.

## Rapport de prospective

- Cadre, système étudié, horizon temporel en tête.
- Cartographie systémique en figure.
- Scénarios présentés en sections parallèles, chacun titré.
- Implications pour la décision présente en clôture.

## Étude de cas d'affaires

- Format court (2 à 4 pages), mise en page dense mais lisible.
- Encadrés de chiffres clés (avant, après, gain).
- Verbatims mis en exergue, attribués.
- Logo et contexte client en tête si la diffusion le permet.

## Note de politique publique

- Résumé exécutif en tête, recommandation comprise, une page maximum.
- Tableau comparatif des options (coût, délai, impact, risque).
- Encadrés pour les chiffres clés, sources officielles datées en notes.

## Note et consultation juridique

- Exposé des faits, puis plan IRAC (question, règle, application, conclusion).
- Citations juridiques normalisées (article et code, décision avec juridiction et date).
- Conclusion mise en exergue.

## Cahier des charges et spécification

- Exigences numérotées en tableau (identifiant, énoncé, priorité, critère d'acceptation).
- Périmètre inclus et exclu en tête, glossaire des sigles.
- Annexes pour interfaces et schémas.

## Cas clinique et protocole

- Données anonymisées, valeurs avec unités SI et dates.
- Norme Vancouver, ligne directrice citée (CONSORT, PRISMA, STROBE).
- Figures et tableaux de résultats numérotés.

## Présentation

- Sortie PowerPoint (skill pptx) ou HTML, une idée par diapositive, titre assertif.
- Charte graphique appliquée, contraste élevé pour la projection.
- Dernière diapositive : conclusion ou appel à l'action.

## Demande de financement et proposition de recherche

- Plan calé sur la grille de l'appel, limites de pages strictement respectées.
- Objectifs sur une page, budget et chronogramme en annexe.

## Dissertation et commentaire

- Introduction (termes, problématique, annonce du plan), parties à transitions, conclusion.
- Pas de page de garde lourde pour une copie d'examen.

## Business plan

- Résumé opérationnel d'une à deux pages en tête, prévisions financières en tableaux, pièces en annexe.

## Proposition commerciale et réponse à appel d'offres

- Plan miroir du règlement de consultation, réponse point par point, références et moyens en annexe.

## Étude de marché

- Synthèse des résultats en tête, tableaux de segmentation et de concurrence, méthode en annexe.

## Documentation technique

- Un document par mode (tutoriel, guide, référence, explication), sommaire, exemples de code en blocs.

## Rapport d'incident et post-mortem

- Résumé (impact, durée) en tête, chronologie horodatée, tableau des actions de suivi assignées.

## Note d'analyse financière

- Bandeau d'en-tête (recommandation, cours, objectif), tableaux de valorisation, sources datées et avertissement.

## Rapport d'évaluation

- Résumé exécutif, une section par critère du CAD, recommandations numérotées reliées aux constats.

## Livre blanc

- Couverture, sommaire, mise en page aérée, figures sourcées, entreprise mentionnée en fin de document.

## Discours et allocution

- Texte pour l'oral : phrases courtes, repères de respiration, durée estimée, pas de jargon non explicité.

## Conclusions et mémoire contentieux

- Parties attendues (questions, faits, discussion, dispositif), intertitres argumentatifs, demandes en clôture.

## Rédaction de contrat

- Préambule, définitions, articles numérotés, clauses énumérées, annexes ; "doit" pour les obligations.

## Listes de figures et de tableaux

Les pages liminaires d'un rapport scientifique ou d'un mémoire comprennent une liste des figures et une liste des tableaux. Elles ne se produisent pas de la même façon selon la voie de sortie.

- LaTeX : `\listoffigures` et `\listoftables`, placés après `\tableofcontents` dans `assets/gabarit-rapport.tex`. Les deux listes se remplissent seules à partir des `\caption`, à la deuxième passe de compilation. Une figure sans `\caption` n'y figure pas.
- HTML : aucune génération automatique. La liste se construit à la main, en `<nav>` de liens vers les `id` posés sur chaque `<figure>` et chaque `<table>`, avec le numéro et la légende repris à l'identique du `<figcaption>` et du `<caption>`. La feuille produite par `theme.py --format css` met en forme figures et légendes, elle ne fabrique aucune liste.
- Word : aucune génération par le plugin. Deux options. La liste s'écrit comme un paragraphe de renvois numérotés à l'insertion du document. Ou elle se délègue au champ natif "Table des illustrations" de Word, qui exige que chaque légende ait été posée avec le style de légende de Word et se met à jour dans l'application, pas depuis le skill `docx`.
- PDF : hérite de la voie qui l'a produit, LaTeX ou conversion du HTML.

Avant de générer les listes, vérifier la numérotation sur le Markdown source : `traceability.py` signale un numéro en double, un numéro sauté, une suite qui ne commence pas à 1 et un objet jamais appelé depuis le texte. Une liste de figures construite sur une numérotation fautive reproduit la faute.

## Constantes de forme

- Style maison respecté jusque dans les légendes et les notes.
- Une seule norme bibliographique par document.
- Figures et tableaux autonomes : titre, axes, unités, source.
- Numérotation continue par type d'objet, commençant à 1, sans trou ni doublon, chaque objet appelé depuis le texte.
- Pagination, sommaire à jour, abréviations définies.
