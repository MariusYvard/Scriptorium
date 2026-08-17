# Catalogue des figures et grille de regard critique

Types de figures produits par `scripts/figures.py`, formats de données et grille de lecture critique.

## Formats de données

### SWOT
```
{"forces":["..."],"faiblesses":["..."],"opportunites":["..."],"menaces":["..."]}
```
Quatre cases équilibrées. Chaque entrée courte et factuelle.

### Matrice BCG
```
{"items":[{"nom":"Domaine A","croissance":0-100,"part":0-100,"taille":8-40}]}
```
croissance : taux de croissance du marché (100 en haut). part : part de marché relative (100 à gauche). taille : poids du domaine, rayon de la bulle.

### Matrice d'Ansoff
```
{"penetration":["..."],"extension_produit":["..."],"extension_marche":["..."],"diversification":["..."]}
```
Axes : produit actuel ou nouveau, marché actuel ou nouveau.

### PESTEL
```
{"politique":["..."],"economique":["..."],"social":["..."],"technologique":["..."],"environnemental":["..."],"legal":["..."]}
```
Six dimensions du macro-environnement.

### Chaîne de valeur (Porter)
```
{"soutien":["..."],"principales":["..."]}
```
Activités de soutien au-dessus, activités principales en dessous, marge à droite.

## Formats de données des figures de données

Les cinq figures ci-dessus rangent des éléments dans des cases et n'ont pas d'axes. Les six suivantes portent des grandeurs mesurées, donc des axes gradués. Chaque axe se déclare par `{"titre": "...", "unite": "..."}`. Une grandeur sans unité le dit (`"unite": "sans unité"`) plutôt que d'omettre la clé.

Les séries se distinguent par la couleur et par un second canal (forme du marqueur, style de trait). Les couleurs viennent de la palette de la charte, filtrées sur leur contraste avec le fond ; les palettes nommées `okabe-ito` et `wong` sont daltonisme-sûres.

### Courbe
```
{"axe_x":{"titre":"Durée","unite":"h"},"axe_y":{"titre":"Concentration","unite":"mg/L"},
 "depart_zero":true,
 "series":[{"nom":"Témoin","points":[[0,1.2],[2,3.4]],"marqueurs":true,"erreurs":[0.2,0.3]}]}
```
Une série x/y au minimum, six au plus avant que l'audit ne signale la surcharge. `erreurs` donne la demi-hauteur de la barre d'erreur de chaque point, dans l'ordre des points (un nombre unique s'applique à tous). `marqueurs` vaut vrai par défaut. `depart_zero` force l'origine des ordonnées à zéro.

### Nuage de points
```
{"axe_x":{"titre":"Masse","unite":"kg"},"axe_y":{"titre":"Rendement","unite":"%"},
 "series":[{"nom":"Lot A","points":[[1,12],[2,15]],"ajustement":true}]}
```
`ajustement` ajoute une droite des moindres carrés, tracée en pointillés et annoncée comme ajustement dans la légende. Elle n'est pas une donnée mesurée.

### Histogramme
```
{"axe_x":{"titre":"Classe d'âge"},"axe_y":{"titre":"Effectif","unite":"individus"},
 "barres":[{"categorie":"18-24","valeur":42,"erreur":4}],"couleur_par_barre":false}
```
Barres verticales, une par catégorie ou par classe. L'axe des ordonnées part toujours de zéro. `erreur` est facultative. `valeurs_affichees` (vrai par défaut) écrit la valeur au-dessus de chaque barre jusqu'à quatorze barres.

### Boîtes à moustaches
```
{"axe_x":{"titre":"Groupe"},"axe_y":{"titre":"Durée de séjour","unite":"jours"},
 "groupes":[{"nom":"Témoin","valeurs":[3,4,5,6,7,20]},
            {"nom":"Traité","min":2,"q1":3,"mediane":4,"q3":6,"max":9,"aberrants":[14]}]}
```
Deux entrées possibles par groupe. Des valeurs brutes donnent les quartiles et les points aberrants par la règle de 1,5 écart interquartile. Les cinq nombres peuvent aussi être fournis tels quels.

### Diagramme de flux
```
{"niveaux":[{"titre":"Identification",
             "boites":[{"libelle":"Références trouvées","effectif":435,
                        "sous":["Bases : 420","Autres : 15"],
                        "exclusions":[{"libelle":"Doublons retirés","effectif":60}]}]}]}
```
Boîtes reliées par des flèches, rangées par niveau. Chaque boîte porte son effectif entre parenthèses. Les exclusions sortent latéralement à droite. `sous` ajoute des lignes de détail sous le libellé.

### PRISMA
```
{"identifiees":{"Bases de données":420,"Autres sources":15},"doublons":60,"examinees":375,
 "ecartees_titre":[{"motif":"Hors sujet","n":150},{"motif":"Langue non couverte","n":50}],
 "evaluees":175,
 "ecartees_texte":[{"motif":"Méthode insuffisante","n":90},{"motif":"Population différente","n":50}],
 "incluses":35}
```
Sélection des études d'une revue, sur le moteur du diagramme de flux avec la structure de `references/prisma.md`. `identifiees` accepte aussi un entier unique. Les comptes doivent boucler : identifiées moins doublons égale examinées, examinées moins la somme des écarts au criblage égale évaluées, évaluées moins la somme des écarts en texte intégral égale incluses.

## Audit déterministe

Lancer `figures.py TYPE --data - --audit` avant de rendre. Il relève : cases vides, surcharge (plus de 7 éléments), déséquilibre fort entre cases, éléments trop longs, points BCG sans nom ou hors bornes 0-100, plus de 10 bulles.

Sur les figures de données il relève : série vide ou absente, axe sans titre, axe sans unité, série sans nom (ses points ne sont pas étiquetables en légende), plus de six séries, barres d'erreur en nombre différent des points, catégorie ou groupe en doublon, catégorie sans libellé, valeur non numérique, échelle des ordonnées tronquée sur un histogramme, groupe dépourvu des cinq nombres, ordre min, Q1, médiane, Q3, max non respecté, boîte de flux sans effectif, écart PRISMA sans motif et comptes PRISMA qui ne bouclent pas à l'une des trois jonctions.

L'échelle tronquée et les comptes PRISMA qui ne bouclent pas sont des fautes d'honnêteté, pas des fautes de goût : une base non nulle exagère l'écart entre barres, un PRISMA dont les comptes ne tombent pas juste est faux.

## Grille de regard critique qualitatif

L'audit ne voit pas tout. Lire la figure à l'oeil sur ces points.

1. Honnêteté des échelles. Les axes partent de zéro. Les tailles sont proportionnelles. Une échelle tronquée exagère un écart, la proscrire sauf mention explicite.
2. Autonomie. Titre clair, axes nommés, unités présentes, source citée. La figure se comprend sans le texte.
3. Justesse du placement. Dans une matrice, chaque élément occupe le quadrant que ses valeurs réelles imposent. Vérifier deux ou trois placements à la main.
4. Sens hors couleur. La figure reste lisible en niveaux de gris. La couleur ne porte jamais seule l'information, doubler par une étiquette ou une position.
5. Sobriété. Une figure, un message. Pas d'ornement, pas de troisième dimension décorative, pas de surcharge. Si une case déborde, résumer.
6. Cohérence avec le texte. La donnée de la figure correspond à la carte preuve-affirmation et au chiffre cité dans le corps.
7. Source et date. La figure porte sa source et la date de la donnée, comme une affirmation du texte.

## Défauts fréquents à éviter

- La case vide qui fait paraître l'analyse incomplète.
- Le camembert à douze parts illisible (préférer un tableau ou une barre).
- L'échelle tronquée qui dramatise un écart mineur.
- La couleur seule comme code, illisible pour un daltonien.
- La bulle dont la surface ne reflète pas la grandeur représentée.
- La figure sans titre ni source, non autonome.
