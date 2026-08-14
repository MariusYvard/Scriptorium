# Charte graphique (identité visuelle)

Faire suivre une identité visuelle donnée sur l'ensemble d'un document. La charte fixe les couleurs, les polices, l'accent, un filigrane et le rayon des angles. Elle s'applique aux figures par le générateur et aux documents par la mise en forme, de façon cohérente d'un bout à l'autre.

La charte est un fichier JSON. Format complet dans `references/charte-graphique-format.md`, exemple dans `assets/charte-graphique.exemple.json`.

## Mode 1 : définir la charte

Construire le JSON à partir de ce que fournit l'utilisateur.

- Couleurs données directement : les placer dans `couleurs` (encre, trait, fond, accent, palette de quatre fonds).
- Charte fournie dans un document de marque (PDF, page, capture) : en extraire les codes hexadécimaux, la police et le logo, puis remplir le JSON.
- Rien de précis : partir de l'exemple et proposer, en signalant que ce sont des valeurs par défaut.

Enregistrer la charte sous `charte-graphique.json` dans le dossier de travail. Les compétences `produire` (figure) et `livrer` (document) la trouvent là par convention.

## Palettes daltonisme-sûres

Plutôt qu'une palette de fonds choisie à la main, `couleurs.palette` accepte le nom d'une palette daltonisme-sûre intégrée :

```json
{"couleurs": {"palette": "okabe-ito"}}
```

Deux palettes sont disponibles. `okabe-ito` (huit teintes dont le noir, Okabe et Ito, 2008) et `wong` (les sept teintes chromatiques de la même famille, sans le noir, reprises par Wong dans Nature Methods en 2011). Les deux sont conçues pour rester distinguables en vision dichromate (le type de daltonisme le plus courant).

Si la palette est fournie à la main plutôt que par un de ces deux noms, `theme.py` (voir plus bas) signale en avertissement les paires de couleurs trop proches en vision dichromate, par une approximation déterministe documentée dans le script. Ce n'est jamais une erreur bloquante : c'est un signal à traiter en ajoutant un second canal (voir encodage redondant ci-dessous), pas nécessairement en changeant la couleur.

## Mode 2 : appliquer la charte

Valider d'abord, puis appliquer.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/theme.py charte-graphique.json
```

- Figures : passer la charte au générateur.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/figures.py TYPE --theme charte-graphique.json --out figure.svg --title "Titre"
```

Toutes les couleurs, la police, le filet d'accent sous le titre et le filigrane suivent la charte.

- Documents HTML : la compétence `livrer` (document) lit la charte et applique la police des titres, la couleur d'encre et l'accent aux titres, filets, légendes et liens. Le corps reste lisible (la charte ne change pas le fond du texte courant).

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/theme.py charte-graphique.json --format css
```

- Documents LaTeX : le même principe s'applique au gabarit `assets/gabarit-rapport.tex` et à son équivalent poster `assets/gabarit-poster.tex`, par un préambule de couleurs et polices à coller tel quel (voir `livrer`, action document, section sortie LaTeX).

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/theme.py charte-graphique.json --format latex
```

Appliquer la même charte à toutes les figures et à la mise en forme, pour une cohérence visuelle complète.

## Mode 3 : valider la charte

Avant tout usage, contrôler la charte.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/theme.py charte-graphique.json
```

Le script signale une couleur mal formée (erreur), un contraste insuffisant entre l'encre et le fond ou l'encre et un fond de palette (avertissement sous 4,5:1), et, pour une palette fournie à la main, les paires de couleurs trop proches en vision dichromate (avertissement). Une charte en erreur n'est pas utilisée telle quelle. Un avertissement de contraste se corrige en assombrissant l'encre ou en éclaircissant le fond ; un avertissement de vision dichromate se corrige en ajoutant un second canal ou, si la teinte elle-même doit changer, en adoptant une des deux palettes nommées.

## Convention de dossier

Si `charte-graphique.json` existe dans le dossier de travail, l'utiliser par défaut pour toutes les figures et la mise en forme, sans le redemander. Sinon, travailler avec la charte sobre par défaut, et proposer d'en définir une.

## Format de sortie

- Mode définir : le fichier `charte-graphique.json`, plus un résumé des choix (couleurs, police, accent).
- Mode appliquer : les figures thémées et le document mis en forme à la charte (HTML ou LaTeX selon le canal).
- Mode valider : le rapport du script (erreurs, avertissements de contraste et de vision dichromate) avec la correction proposée.

## Ce que la charte couvre

Couleurs (une palette nommée daltonisme-sûre ou une liste choisie à la main), polices, graisse des titres, accent, fond, rayon, filigrane texte. Un logo en image s'insère séparément dans le document. Les illustrations sur mesure et les grilles complexes restent un travail manuel que la charte cadre sans l'automatiser.

## Encodage redondant

Règle de charte, pas seulement de figure isolée : dans tout document sous cette charte, une distinction (catégorie, statut, priorité) ne repose jamais sur la seule couleur. Un second canal l'accompagne toujours : forme, motif, position ou libellé direct. Cette règle s'applique aux figures produites par `produire` (figure) comme aux tableaux et aux encadrés sémantiques d'un document mis en forme. Voir `produire`, action figure, section encodage redondant, pour la vérification pratique.

## Règles

1. Valider la charte avant de l'appliquer. Une charte en erreur n'est pas utilisée.
2. Un avertissement de contraste se corrige, il ne s'ignore pas.
3. La même charte sur toutes les figures et la mise en forme. Pas de figure hors charte dans un document à charte.
4. La charte fixe la forme visuelle, jamais le fond ni les faits.
5. Le style maison éditorial (voir `produire` (style)) reste appliqué en plus de la charte graphique : l'un règle les mots, l'autre l'image.
6. Une palette manuelle qui signale un avertissement de vision dichromate se corrige par un second canal ou par l'adoption d'une palette nommée, jamais en ignorant l'avertissement.
