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

## Audit déterministe

Lancer `figures.py TYPE --data - --audit` avant de rendre. Il relève : cases vides, surcharge (plus de 7 éléments), déséquilibre fort entre cases, éléments trop longs, points BCG sans nom ou hors bornes 0-100, plus de 10 bulles.

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
