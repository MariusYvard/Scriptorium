# Produire : image (extraire, cataloguer et replacer des images)

Récupérer les images d'un document source (PDF, Word, PowerPoint, Excel) ou reprendre un dossier d'illustrations déjà produites, puis les préparer à un placement propre. La répartition est nette : le script `images.py` fait le mécanique, le modèle fait le jugement (alt, légende, tri, pertinence).

Deux entrées possibles. Les images sont enfermées dans un document existant : commencer à l'étape 1. L'auteur arrive avec un dossier de fichiers en vrac (photos de dispositif, captures d'écran, schémas faits ailleurs) : commencer à l'étape 1 bis, puis reprendre à l'étape 3.

## 1. Extraction déterministe

Lancer le script. Il extrait les images, déduplique, lit les dimensions et écrit un manifeste.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/images.py extract SOURCE --out images/
```

- Word, PowerPoint, Excel et ODF : extraction directe des médias (zip), sans dépendance.
- PDF : le script essaie PyMuPDF, puis `pdfimages` (poppler), puis pypdf. Si aucun n'est présent, il l'indique. Extraire alors les images avec le skill `pdf`, puis reprendre à l'étape 2.

Le manifeste (`images/manifest.json`) donne pour chaque image : index, fichier, format, dimensions, octets, empreinte, ordre, doublons, drapeaux (espaceur 1x1, vecteur à convertir, dimensions inconnues).

## 1 bis. Catalogue d'un dossier d'illustrations déjà produites

Quand les illustrations existent déjà comme fichiers, il n'y a rien à extraire mais tout à mesurer. Le catalogue applique les mêmes mesures que l'extraction et rend la liste des figures exploitable par l'auteur.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/images.py catalogue illustrations/ --largeur-cm 15
```

`--largeur-cm` déclare en centimètres la largeur d'insertion prévue dans le document et commande tout le reste : une image de 1772 pixels de large rend 300 dpi sur 15 cm et 180 dpi sur 25 cm. La résolution n'est pas une propriété du fichier, elle dépend de la taille à laquelle il est posé sur la page. `--usage impression` applique le seuil de 300 dpi, `--usage ecran` celui de 150 dpi. Une figure destinée à une demi-largeur se catalogue à sa propre largeur, en relançant la commande.

Le catalogue (`illustrations/catalogue.json`) donne par illustration : nom de fichier, format lu dans l'en-tête, type, dimensions en pixels, poids, empreinte, doublon éventuel avec le fichier dont il est la copie, résolution effective à la largeur demandée, largeur maximale qui tiendrait encore le seuil, drapeaux et un verdict.

Six verdicts, exclusifs.

| Verdict | Ce qu'il commande |
| --- | --- |
| `utilisable` | Insérer à la largeur prévue, rien à faire |
| `sous le seuil` | Réduire la largeur d'insertion à `largeur_cm_max`, retrouver le fichier d'origine ou refaire la prise de vue |
| `doublon` | Écarter, la même image est déjà cataloguée sous un autre nom |
| `dimensions illisibles` | Format non couvert par la lecture d'en-tête : mesurer autrement, jamais supposer |
| `vecteur, resolution sans objet` | Un vectoriel n'a pas de résolution, il s'agrandit sans perte (voir étape 2) |
| `hors perimetre` | Le fichier n'est pas une image, il sort du catalogue sans devenir une alerte |

Un verdict `sous le seuil` ne se contourne pas en agrandissant le fichier dans un éditeur : un agrandissement invente des pixels, il ne restitue pas de détail. Les deux vraies réponses sont une insertion plus petite ou un fichier source de meilleure définition.

## 1 ter. Apparier figure, légende et page

Les images sorties de l'étape 1 sont anonymes : rien ne relie `img-003.png` à "Figure 3" ni à sa légende. `emprunts.py inventorier` pose ce lien. Il extrait les images, lit le texte page par page, repère les légendes en tête de ligne (`Figure 3.`, `Fig. 3`, `Figure 3:`, `Tableau 2.`, plus les formes anglaises `Figure`, `Fig.` et `Table`), puis apparie chaque image aux légendes de sa page.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/emprunts.py inventorier SOURCE.pdf --out images/
```

L'appariement lit une mise en page, pas une figure. Chaque fiche porte donc son niveau de confiance. Un appariement douteux n'est jamais présenté comme certain.

| Niveau | Ce qui l'a produit | Ce qu'il commande |
| --- | --- | --- |
| `elevee` | Une image et une légende sur la page | Utiliser le numéro et la légende tels quels |
| `moyenne` | Comptes égaux pour plus d'une image, appariement par ordre de lecture | Vérifier la page avant de citer le numéro |
| `faible` | Les comptes d'images et de légendes divergent | Vérifier la page, l'ordre a de bonnes chances d'être rompu |
| `nulle` | Aucune légende disponible pour cette image | Nommer la figure à la main, le libellé reste vide |

Cinq verdicts d'inventaire : `inventaire apparie`, `inventaire partiel`, `inventaire sans legende`, `inventaire non apparie`, `extraction impossible`. Sans backend de texte, l'inventaire rend les images sans légende et le déclare, il n'invente aucune légende. Les légendes repérées sans image extraite sont listées à part : la figure est alors probablement vectorielle, tracée dans la page plutôt que posée comme image. Elle se récupère alors par une capture de la zone.

## 2. Tri avant analyse

Lire le manifeste ou le catalogue. Écarter les doublons et les micro-images, déjà séparés par le script. Pour une image vectorielle (EMF ou WMF, drapeau `vecteur-a-convertir`), la convertir en PNG avant de la regarder, sinon la décrire depuis son contexte et le signaler. Un SVG se convertit avec `images.py convertir` (voir `figure.md`, étape 3). Si la source contient beaucoup d'images, annoncer le volume et demander le périmètre (toutes, ou seulement les figures utiles).

## 2 bis. Contrôle des droits avant réutilisation

Une image tirée d'un document tiers est une oeuvre protégée indépendamment du texte qui la porte. Citer la source règle le sourçage, pas le droit de reproduction. Résoudre la licence avant d'investir dans l'analyse et le placement.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-droits.py licence --doi 10.xxxx/yyyy --reseau
```

Quatre verdicts fermés : `reutilisable avec attribution`, `reutilisable sous conditions`, `autorisation requise`, `licence inconnue`. Le dernier ne se confond pas avec le troisième : une absence d'information n'est ni une interdiction, ni une permission. Sur `autorisation requise` ou `licence inconnue`, deux voies restent ouvertes : demande écrite à l'éditeur, redessin de la figure depuis les données publiées avec la mention "d'après les données de X". Les figures empruntées se consignent dans un registre qui valide les crédits et produit la section correspondante. Familles de licences, procédure d'autorisation et forme du registre dans `references/droits-figures.md`.

## 2 ter. La chaîne complète pour une figure tierce

Quand la figure vient d'une publication identifiée par un DOI, les quatre gestes s'enchaînent en une commande : localiser la version en accès ouvert, récupérer le fichier si la source est ouverte, apparier les images à leurs légendes, résoudre les droits et écrire l'entrée du registre.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/emprunts.py chainer --doi 10.xxxx/yyyy --figure 3 \
  --out emprunts/ --registre registre-figures.json --reseau
```

Le PDF déjà possédé se passe en `--source FICHIER.pdf`, ce qui saute la récupération. Un recadrage se déclare en `--modifications "recadrée"` : la mention entre dans la ligne de crédit. `check-droits.py` refuse ensuite le registre si la licence interdit toute adaptation.

Le script ne récupère un fichier que depuis une localisation déclarée en accès ouvert par l'index. Il ne contourne aucun contrôle d'accès, ne présente aucun identifiant et ne tente aucune adresse devinée. Un article sous abonnement se demande à son éditeur, il ne se contourne pas : le refus renvoie vers la procédure de `references/droits-figures.md`. Trois refus distincts, à ne pas confondre : `refus source non ouverte` (l'index déclare la source fermée), `refus adresse absente` (source ouverte mais aucune adresse publiée, ouvrir la page de dépôt à la main), `refus localisation inconnue` (l'état d'accès n'est pas établi, ce qui ne vaut pas permission).

Cinq verdicts de chaîne : `emprunt prepare`, `autorisation a demander`, `licence a etablir`, `source non ouverte`, `chaine incomplete`. Sur les deux du milieu, le rapport nomme les deux voies ouvertes : la demande écrite à l'éditeur avec ses cinq étapes ou le redessin depuis les données publiées avec les types de `figures.py` (`courbe`, `nuage`, `histogramme`, `boite`, `flux`, `prisma`).

## 2 quater. Citer la figure retenue

L'entrée écrite au registre porte la source, le DOI, le numéro de figure, la légende d'origine, la licence, le verdict, la mention des modifications et le chemin du fichier récupéré. La ligne de crédit s'en tire ensuite, en texte, en HTML ou en LaTeX.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-droits.py registre registre-figures.json --strict
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-droits.py credits registre-figures.json --sortie latex
```

Un élément absent de l'entrée reste absent et sort marqué "À COMPLÉTER" dans la ligne de crédit. Le combler au jugé produirait un crédit faux, ce qui est pire qu'un crédit incomplet.

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
5. La résolution se contrôle à la largeur d'insertion réelle, jamais sur le seul nombre de pixels du fichier.
6. Une illustration sous le seuil se corrige par une insertion plus petite ou un fichier de meilleure définition, jamais par un agrandissement logiciel.
7. Une image tirée d'une publication tierce passe le contrôle des droits avant l'analyse. Son crédit porte titre, auteur, source, licence et mention des modifications.
8. Un numéro de figure ne se cite que si l'appariement le donne en confiance `elevee`. Aux niveaux `moyenne` et `faible`, ouvrir la page et vérifier avant d'écrire "Figure 3".
9. Un fichier ne se récupère que depuis une localisation déclarée en accès ouvert. Aucun contrôle d'accès n'est contourné, aucune adresse n'est devinée : une source fermée passe par la demande d'autorisation.
