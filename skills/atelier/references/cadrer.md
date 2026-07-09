# Cadrer (cadrage et plan)

Transformer une intention floue en périmètre fermé et en plan démonstratif. Le cadrage évite l'éparpillement et la structure en liste d'épicerie, où les sections pourraient s'inverser sans perte de sens. Aucune rédaction ne commence avant que le genre, la problématique et le plan soient validés.

## 1. Établir le brief

Recueillir les paramètres du commanditaire, de façon conversationnelle, sans dérouler toute la liste d'un coup. Poser d'abord les questions qui changent le livrable.

Paramètres à fixer :

- Problème déclencheur et contexte (pourquoi cet écrit, maintenant).
- Public destinataire et son niveau d'expertise (un comité de direction, un jury, des pairs, un client).
- Décision que l'écrit doit éclairer (la question "ce document sert à décider quoi ?" recadre tout le reste).
- Contraintes de volume, de format et de délai.
- Sources déjà disponibles et sources à produire.

Consigner ces paramètres dans un brief court. Le relire à l'utilisateur en une phrase de synthèse avant de continuer.

## 2. Appliquer les cinq filtres de délimitation

Restreindre le sujet large en un objet traitable. Passer le sujet par cinq filtres et écarter tout ce qui n'y survit pas.

1. Sous-thème : restreindre à un aspect précis (la pomme biologique, pas l'agriculture biologique entière).
2. Géographie ou secteur : fixer un espace cohérent, éviter les généralisations.
3. Variables : isoler les facteurs clés étudiés, sans se disperser dans les corrélations secondaires.
4. Temps : poser des bornes chronologiques justifiées.
5. Catégorie étudiée : préciser le public cible, le type d'acteurs ou de clients concernés.

## 3. Formuler la problématique

Transformer le sujet filtré en une question fermée qui pose une tension réelle. Une bonne problématique appelle une démonstration, pas une description. Tester la formulation : si la réponse tient en un fait connu, la question est trop faible. Si elle ouvre un débat ou un arbitrage, elle tient.

Si le sujet reste flou après le brief et les cinq filtres, ou si l'utilisateur demande explicitement à être guidé plutôt que de répondre à une liste de questions, charger `boite-socratique.md` pour un dialogue guidé (contrôle de préparation, cristallisation de la thèse en trois couches, extraction incrémentale d'acquis) avant de revenir formuler la problématique ici.

## 4. Qualifier le sujet (cadre FINER)

Avant de choisir le genre et d'investir dans un plan, noter le sujet sur les cinq critères du cadre FINER (faisable, intéressant, novateur, éthique, pertinent). Voir `cadre-finer.md` pour la définition de chaque critère, ses paliers et le seuil d'engagement. Sous le seuil, resserrer le sujet, changer d'angle ou renoncer avant de continuer, plutôt que de découvrir l'infaisabilité en plein sourcing ou en pleine rédaction.

## 5. Choisir le genre

Apparier la cible au bon genre, qui fixe la structure standard et les normes attendues. Consulter au besoin `methodologie-transverse.md` et la matrice comparative des genres dans le playbook concerné de `rediger/references/`.

- Connaissances scientifiques à transférer, jury ou pairs : rapport scientifique ou mémoire (IMRAD).
- Étude originale courte et dense pour publication : article scientifique (IMRAD plus abstract structuré).
- Aide à la décision managériale, parties prenantes : long rapport professionnel.
- Alignement des ressources sur l'environnement concurrentiel : analyse stratégique.
- Anticipation de ruptures à long terme : rapport de prospective.
- Preuve d'usage commercial sur un projet clos : étude de cas d'affaires.

## 6. Bâtir le plan

Concevoir le plan comme une démonstration qui résout la problématique, pas comme une juxtaposition de connaissances. Partir de la structure standard du genre, puis y placer le fil conducteur propre au sujet.

Produire un plan à deux niveaux : titres de parties, puis message unique de chaque sous-partie en une phrase. Pour chaque sous-partie, noter la preuve attendue. Marquer les zones où la preuve manque, elles deviennent la commande de l'étape sourcing.

Délimiter explicitement le hors-périmètre. Lister ce que le document ne traitera pas, avec une raison courte. Cette section hors-sujet protège le document de la dérive.

## 7. Test de cohérence du plan

Avant de valider, vérifier que chaque sous-partie sert la problématique. Si l'ordre des sections peut s'inverser sans perte de sens, le plan est une liste, pas une démonstration. Le retravailler jusqu'à ce que chaque section appelle la suivante.

## Format de sortie

1. Brief de cadrage (cinq à huit lignes).
2. Problématique en une question fermée.
3. Qualification FINER (cinq notes et moyenne, voir `cadre-finer.md`).
4. Genre retenu et justification en une phrase.
5. Plan à deux niveaux avec, sous chaque sous-partie, la preuve attendue et le statut (disponible ou à sourcer).
6. Section hors-périmètre.
7. Liste des questions ouvertes, chacune accompagnée d'une recommandation.

Enregistrer le plan validé dans `plan.json` (genre, problématique, liste des sections) pour le contrôle de conformité ultérieur via `scripts/plan-check.py`, et l'inscrire dans la mémoire de projet (`scripts/project.py set plan`).

## Règles

1. Ne pas dérouler toutes les questions du brief d'un coup. Avancer comme deux praticiens devant un tableau, pas comme un formulaire.
2. Préférer un périmètre étroit et profond à un périmètre large et superficiel.
3. Toute question ouverte porte une recommandation. Jamais d'impasse.
4. Respecter le style maison dans le plan comme dans le document.
