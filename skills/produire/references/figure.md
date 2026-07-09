# Schématiser (figures stratégiques et regard critique)

Produire des figures sobres, justes et autonomes, puis les passer au crible avant insertion. Une figure est du contenu, pas de la décoration. Elle se comprend sans le texte.

## 1. Préparer les données

Structurer le contenu de la figure en JSON, selon le type. Voir `references/figures-catalogue.md` pour les formats exacts. Exemple SWOT :

```
{"forces":[...],"faiblesses":[...],"opportunites":[...],"menaces":[...]}
```

Chaque entrée est courte (moins de 90 caractères) et factuelle. Une case de figure se lit d'un coup d'oeil, pas en paragraphe.

## 2. Porter le regard critique déterministe

Avant de produire le SVG, lancer l'audit. Il relève les défauts structurels : cases vides, surcharge, déséquilibre, valeurs hors bornes, points non étiquetés.

```
echo 'DONNEES_JSON' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/figures.py TYPE --data - --audit
```

Corriger les défauts signalés avant de rendre la figure. Une case vide ou une échelle faussée discrédite la figure entière.

## 3. Produire le SVG

```
echo 'DONNEES_JSON' | python3 ${CLAUDE_PLUGIN_ROOT}/scripts/figures.py TYPE --data - --out figure.svg --title "Titre"
```

TYPE : `swot`, `bcg`, `ansoff`, `pestel`, `chaine-valeur`. Le SVG est portable. Pour l'insérer dans un document Word, le convertir en PNG avec l'outil disponible.

Si une charte graphique existe (`charte-graphique.json` dans le dossier de travail, voir la compétence `produire` (charte)), l'ajouter avec `--theme charte-graphique.json`. La figure suit alors l'identité visuelle : couleurs, police, filet d'accent, filigrane. Toutes les figures d'un même document partagent la charte.

## 4. Vérifier le rendu visuellement

Avant toute livraison, ouvrir le fichier de figure produit (le SVG ou son export PNG) et l'examiner, comme `produire` (image) le fait déjà pour les images extraites d'un document existant. L'audit déterministe de l'étape 2 ne voit que les données, jamais le rendu final : cette étape regarde l'objet réellement livré.

Vérifier cinq points sur le rendu ouvert.

1. Chaque axe porte un titre et son unité, pas seulement une échelle de chiffres nus.
2. La légende est complète : tout élément codé par couleur, forme ou motif y figure.
3. Le texte reste lisible à la taille réelle d'insertion, pas seulement agrandi à l'écran pendant la production.
4. La figure correspond au passage du texte qui la cite : mêmes valeurs, même conclusion, aucun écart entre ce que dit le texte et ce que montre la figure.
5. Le contraste entre le texte, les éléments graphiques et le fond reste suffisant à la lecture.

Toute figure qui échoue un seul de ces points est refaite avant livraison, jamais livrée avec une réserve mentionnée en passant.

## 5. Appliquer le regard critique qualitatif

L'audit déterministe ne voit pas tout. Compléter par une lecture humaine, à l'oeil, sur cinq points.

1. Honnêteté des échelles : les axes partent-ils de zéro, les tailles de bulles sont-elles proportionnelles, une échelle tronquée exagère-t-elle un écart ?
2. Autonomie : la figure se comprend-elle sans le texte ? Titre clair, axes nommés, unités présentes, source citée.
3. Justesse du placement : dans une matrice, chaque élément est-il dans le bon quadrant au regard de ses valeurs réelles ?
4. Sens porté par autre chose que la couleur : un daltonien lit-il la figure ? La couleur ne doit pas être le seul code.
5. Sobriété : la figure dit-elle une chose, sans surcharge ni ornement inutile. Si une case déborde, résumer.

Voir la liste complète dans `references/figures-catalogue.md`.

## 6. Insérer

Numéroter la figure, lui donner un titre et citer sa source. La placer près du passage qu'elle illustre. Renvoyer à elle dans le texte (« voir figure 2 »).

## Format de sortie

Le fichier SVG (ou PNG), le rapport d'audit déterministe, la vérification visuelle du rendu (étape 4) et la note de regard critique qualitatif sur les cinq points de l'étape 5. Si la figure illustre une affirmation, vérifier que la donnée de la figure correspond à la carte preuve-affirmation.

## Règles

1. Pas de figure à case vide ni à échelle faussée.
2. Chaque figure est autonome : titre, axes, unités, source.
3. La couleur n'est jamais le seul porteur de sens.
4. Une figure, un message. Résumer ce qui déborde.
5. La donnée d'une figure est sourcée comme une affirmation du texte.
6. Toute figure qui échoue la vérification visuelle du rendu est refaite, jamais livrée avec une réserve.
