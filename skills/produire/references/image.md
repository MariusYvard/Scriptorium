# Produire : image (extraire et replacer des images)

Récupérer les images d'un document source (PDF, Word, PowerPoint, Excel) et les préparer à un placement propre. La répartition est nette : le script `images.py` fait le mécanique, le modèle fait le jugement (alt, légende, tri, pertinence).

## 1. Extraction déterministe

Lancer le script. Il extrait les images, déduplique, lit les dimensions et écrit un manifeste.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/images.py extract SOURCE --out images/
```

- Word, PowerPoint, Excel et ODF : extraction directe des médias (zip), sans dépendance.
- PDF : le script essaie PyMuPDF, puis `pdfimages` (poppler), puis pypdf. Si aucun n'est présent, il l'indique. Extraire alors les images avec le skill `pdf`, puis reprendre à l'étape 2.

Le manifeste (`images/manifest.json`) donne pour chaque image : index, fichier, format, dimensions, octets, empreinte, ordre, doublons, drapeaux (espaceur 1x1, vecteur à convertir, dimensions inconnues).

## 2. Tri avant analyse

Lire le manifeste. Écarter les doublons et les micro-images, déjà séparés par le script. Pour une image vectorielle (EMF ou WMF, drapeau `vecteur-a-convertir`), la convertir en PNG avant de la regarder (LibreOffice ou Inkscape s'ils sont présents), sinon la décrire depuis son contexte et le signaler. Si la source contient beaucoup d'images, annoncer le volume et demander le périmètre (toutes, ou seulement les figures utiles).

## 3. Analyse par le modèle (alt et contexte)

Ouvrir chaque image retenue et l'examiner. Pour chacune, écrire :

- un `alt` factuel et concis qui décrit ce que montre l'image,
- une légende qui dit ce que la figure apporte, et sa source,
- la classe : informative (figure numérotée, légendée, sourcée) ou décorative (`alt` vide, pas de numéro),
- la transcription ou le résumé du texte porté par l'image, le cas échéant,
- un avis de pertinence et de placement (garder, où, ou écarter).

Ne jamais inventer un `alt`. Si une image est illisible, le dire. Consigner ces champs dans le manifeste enrichi (`images/manifest.enrichi.json`), produit une fois et réutilisé.

## 4. Passer au placement

Transmettre le manifeste enrichi à `livrer` (document). Le placement insère chaque image informative numérotée, légendée, sourcée, au ratio d'origine et cadrée par la charte. Voir `livrer`, section image.

## Règles

1. Le code extrait et mesure, le modèle décrit et trie. Ne pas demander au script de juger une image.
2. Pas d'alt inventé. Une image illisible est signalée, pas décrite au hasard.
3. Doublons et espaceurs écartés avant analyse.
4. Une image importée suit la même exigence qu'une figure : numérotée, titrée, sourcée, autonome.
