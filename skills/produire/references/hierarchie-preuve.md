# Hiérarchie de preuve et fiche de notation

Classer une source par son niveau de preuve avant de s'appuyer dessus, puis noter sa qualité propre indépendamment de son niveau. Un rapport de niveau moyen mais rigoureux vaut mieux qu'une source de haut niveau mal exécutée. Complète `references/ponderation-sources.md` (fiabilité et récence) par un classement plus fin, adapté au domaine du document.

## 1. Sept niveaux de preuve

Du plus fort au plus faible, indépendamment du domaine.

1. Synthèse de sources primaires convergentes (revue systématique, méta-analyse, agrégation officielle de données primaires).
2. Étude ou donnée primaire à méthode robuste et vérifiable (protocole expérimental contrôlé, statistique officielle avec méthodologie publiée).
3. Étude ou donnée primaire sans groupe de comparaison, ou observationnelle à grande échelle.
4. Rapport d'une institution reconnue, étude de cas documentée avec méthode déclarée, donnée secondaire officielle.
5. Publication évaluée par les pairs de portée limitée (échantillon restreint, résultat isolé) ou prépublication à méthode transparente et vérifiable.
6. Source professionnelle sérieuse non évaluée par les pairs (rapport sectoriel avec méthode déclarée, presse spécialisée qui cite ses sources).
7. Opinion d'expert non étayée par une méthode déclarée, ou source secondaire sans méthode.

Une source de niveau 6 ou 7 ne porte jamais seule une affirmation centrale. Voir la règle de triangulation de `references/ponderation-sources.md`.

## 2. Fiche de notation (six critères, note A à F)

Pour chaque source retenue, noter six critères indépendamment, puis une note globale.

| Critère | A | C | F |
| --- | --- | --- | --- |
| Niveau de preuve | Niveau 1 ou 2 | Niveau 4 ou 5 | Niveau 7 |
| Validation | Évaluation par les pairs ou équivalent institutionnel constaté | Relecture éditoriale sans évaluation par les pairs | Aucune validation identifiable |
| Méthodologie | Protocole explicite et reproductible | Méthode partiellement déclarée | Méthode absente ou non vérifiable |
| Couverture | Échantillon ou périmètre représentatif du sujet | Échantillon restreint mais déclaré | Périmètre non précisé |
| Actualité | Dans la fenêtre de fraîcheur du domaine (voir `ponderation-sources.md`) | En limite de fenêtre | Périmée sans être une référence stable |
| Conflits d'intérêt | Absence constatée ou déclaration complète | Conflit déclaré et documenté | Conflit non déclaré mais probable |

La note globale est la plus basse des six, pas une moyenne : un excellent niveau de preuve ne compense pas une méthodologie opaque.

### Recommandation d'usage par note

- A ou B : preuve principale d'une affirmation centrale, sans réserve.
- C ou D : utilisable avec réserve explicite dans le texte (« selon une étude à échantillon restreint », par exemple).
- F : à ne pas utiliser comme preuve. Une source de note F peut rester citée pour la critiquer ou documenter une position, jamais pour l'étayer.

## 3. Ajustement par domaine

Le niveau 1 n'a pas le même contenu concret partout. Le standard courant attendu varie aussi.

| Domaine | Standard le plus haut atteignable en pratique | Niveau courant réaliste |
| --- | --- | --- |
| Sciences expérimentales et médecine | Niveau 1 (méta-analyse, essai contrôlé) | Niveaux 1 à 3 |
| Sciences sociales et gestion | Niveau 2 à 3, la randomisation étant rarement praticable | Niveaux 3 à 5 |
| Droit et politique publique | Le texte de loi ou la décision de la juridiction la plus haute jouent le rôle du niveau 1 | Niveaux 4 à 6, l'avis d'expert motivé étant recevable |
| Technologie et ingénierie | Niveau 3 (benchmark reproductible), la revue par les pairs prenant souvent du retard sur la pratique | Niveaux 3 à 6, rapport industriel inclus |
| Lettres et sciences humaines | Épistémologie différente, la convergence de sources primaires vaut le niveau 1 | Niveaux 4 à 6 |

Cette table ajuste la lecture, elle ne remplace pas la fiche de notation individuelle de chaque source.

## 4. Logique GRADE générale

Principe applicable hors de la médecine : partir d'un niveau de confiance déterminé par le type de preuve, puis l'ajuster explicitement à la hausse ou à la baisse, plutôt que de fixer une note figée par nature de source.

Point de départ : confiance élevée pour une preuve de niveau 1 ou 2, confiance faible pour une preuve de niveau 3 ou en dessous.

Facteurs de baisse (chacun peut faire descendre la confiance d'un cran) : risque de biais dans la méthode, incohérence entre sources censées converger, indirection (la preuve répond à une question voisine, pas à la question posée), imprécision (intervalle ou marge d'erreur large), biais de publication suspecté (seules les études favorables semblent visibles).

Facteurs de hausse : effet de grande ampleur, gradient dose-réponse observé (l'effet croît avec l'exposition), facteurs de confusion plausibles qui iraient pourtant à l'encontre du résultat observé.

La confiance ajustée qui en résulte alimente le score de confiance déjà produit par l'agent `synthese-sources` : un fait de niveau 3 avec tous les facteurs de baisse absents peut justifier une confiance supérieure à un fait de niveau 2 miné par une forte incohérence.

## 5. Indice mécanique de palier de domaine

`scripts/verify-sources.py` classe automatiquement, sans réseau, le domaine de chaque URL d'un document dans l'un de cinq paliers : revue à comité de lecture, preprint, institutionnel, encyclopédie, presse-blog (table locale d'une vingtaine de domaines connus ; un domaine absent de la table est classé non-classe, jamais rangé par défaut dans une catégorie qu'il ne mérite pas forcément).

Cet indice alimente le critère Validation de la fiche de notation (section 2) : une URL de revue à comité de lecture pointe vers une évaluation par les pairs généralement constatée, un billet de blog n'en pointe aucune. Il ne s'y substitue jamais. Une revue à comité de lecture peut publier un article à méthodologie faible (note F malgré un palier de revue à comité de lecture) et un blog peut relayer fidèlement une donnée primaire correctement attribuée (note qui peut rester acceptable malgré un palier presse-blog). Le palier oriente la lecture en premier passage, la fiche de notation individuelle des six critères tranche.

## Sources

- The GRADE Working Group. https://www.gradeworkinggroup.org/ (consultée le 2026-07-08)
- Guyatt, G. H., Oxman, A. D., Vist, G. E., Kunz, R., Falck-Ytter, Y., Alonso-Coello, P. et Schünemann, H. J. (2008). GRADE: an emerging consensus on rating quality of evidence and strength of recommendations. BMJ, 336, 924-926. https://doi.org/10.1136/bmj.39489.470347.AD
