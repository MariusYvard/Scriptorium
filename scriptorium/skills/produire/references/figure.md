# Schématiser (figures stratégiques, figures de données et regard critique)

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

TYPE, figures stratégiques (à cases, sans axes) : `swot`, `bcg`, `ansoff`, `pestel`, `chaine-valeur`, `tam-sam-som`.

TYPE, figures de données (à axes gradués) : `courbe`, `nuage`, `histogramme`, `boite`, `flux`, `prisma`.

La distinction commande la vérification. Une figure stratégique range des éléments dans des cases : elle n'a pas d'axes, le point 1 de l'étape 4 ne s'y applique pas. Une figure de données porte deux axes gradués dont chacun reçoit un titre et son unité, déclarés dans les données (`{"titre": "Durée", "unite": "h"}`). Le type `prisma` rend le schéma de sélection des études d'une revue, sur le même moteur que `flux`.

Le SVG est portable et les voies HTML, LaTeX et PDF l'affichent tel quel. La voie Word demande un PNG, un .docx n'affichant pas un SVG de façon fiable.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/images.py convertir figure.svg --out figure.png --largeur-px 1800
```

La commande essaie les backends présents dans l'ordre `rsvg-convert`, `inkscape`, `cairosvg`, ImageMagick. Aucun n'est une dépendance du plugin. Si aucun n'est installé, elle sort en code 3 avec le statut `aucun-backend`, nomme ce qu'il faut installer et dit que le fichier source n'est pas en cause : ne pas lire cette sortie comme un SVG défectueux et ne jamais fabriquer un PNG de remplacement. Garder alors le SVG pour les autres voies et signaler la figure manquante dans la voie Word.

Dimensionner `--largeur-px` d'après la largeur d'insertion prévue : 300 dpi sur 15 cm demandent 1772 pixels (voir `image.md`, étape 1 bis, pour le contrôle de résolution appliqué au PNG obtenu).

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

## Encodage redondant

Jamais la couleur seule pour porter un sens. Chaque distinction que la couleur code (catégorie, statut, zone) porte au moins un second signal parmi la forme (rond, carré, triangle), le motif (plein, hachuré, pointillé), la position (regroupement spatial, ordre) ou le libellé direct sur l'élément plutôt que dans une légende éloignée. Un daltonien, une impression en niveaux de gris ou une projection dégradée doivent laisser la figure lisible.

Deux vérifications rapides suffisent : d'abord, retirer mentalement la couleur (ou imprimer un aperçu en niveaux de gris) : la figure garde-t-elle son sens ? Ensuite, si la charte fournit une palette manuelle plutôt qu'une palette nommée daltonisme-sûre (`okabe-ito` ou `wong`, voir `produire`, action charte), passer `theme.py` sur la charte : il signale en avertissement les paires de couleurs trop proches en vision dichromate (approximation déterministe, jamais une certitude clinique). Un avertissement de ce type se corrige par un second canal (forme, motif, libellé), pas seulement en changeant la teinte.

## Grille de raffinement notée

Quand une figure mérite plus qu'un regard ponctuel (figure centrale d'un rapport, figure destinée à un support de communication externe), noter le rendu sur cinq critères pondérés, chacun de 0 à 10.

| Critère | Poids | Ce qu'il vérifie |
| --- | --- | --- |
| Lisibilité | 0,25 | Taille de texte, contraste, encombrement à la taille d'insertion réelle |
| Exactitude | 0,25 | Concordance entre la figure et les données ou le texte qu'elle illustre |
| Hiérarchie | 0,20 | L'élément principal se voit en premier, le secondaire ne rivalise pas |
| Cohérence charte | 0,15 | Couleurs, police et filet d'accent alignés sur la charte graphique du document |
| Légendes | 0,15 | Titre, axes, unités, source et légende complets et autonomes |

Le score pondéré se compare à un seuil selon l'usage de la figure, pas un seuil unique universel.

- Brouillon interne : 6,5 sur 10.
- Rapport ou document remis : 8,0 sur 10.
- Support de communication externe (poster, présentation à diffusion large) : 8,5 sur 10.

Sous le seuil, corriger et renoter. Arrêt anticipé : si deux itérations successives ne font pas progresser le score pondéré, arbitrer avec l'utilisateur plutôt que de poursuivre une boucle sans gain (viser une figure différente, accepter le score atteint pour ce brouillon ou revoir les données sources elles-mêmes).

## Format de sortie

Le fichier SVG (ou PNG), le rapport d'audit déterministe, la vérification visuelle du rendu (étape 4), la note de regard critique qualitatif sur les cinq points de l'étape 5 et le score pondéré de la grille de raffinement si la figure en a fait l'objet. Si la figure illustre une affirmation, vérifier que la donnée de la figure correspond à la carte preuve-affirmation.

## Règles

1. Pas de figure à case vide ni à échelle faussée.
2. Chaque figure est autonome : titre, axes, unités, source.
3. La couleur n'est jamais le seul porteur de sens, un second canal (forme, motif, position, libellé) double toujours l'information.
4. Une figure, un message. Résumer ce qui déborde.
5. La donnée d'une figure est sourcée comme une affirmation du texte.
6. Toute figure qui échoue la vérification visuelle du rendu est refaite, jamais livrée avec une réserve.
7. Sous le seuil de la grille de raffinement pour l'usage visé, corriger avant livraison ; après deux itérations sans gain, arbitrer plutôt que boucler.
