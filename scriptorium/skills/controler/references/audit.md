# Auditer un document existant

Évaluer un document déjà produit, pas seulement ceux que l'on rédige. Extraire le texte, puis lancer l'audit consolidé.

## 1. Extraire le texte

Selon le format.

- Markdown ou texte : lire directement.
- PDF : extraire le texte avec le skill `pdf` (ou l'outil `pdftotext` si disponible).
- Word : extraire le texte avec le skill `docx`.

Sauvegarder le texte extrait dans un fichier `.md` de travail. Conserver la structure (titres, tableaux) autant que possible, l'audit s'appuie dessus.

## 2. Lancer l'audit consolidé

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit-doc.py texte-extrait.md
```

Le rapport réunit le scorecard sur 100, les signaux d'empreinte IA, les redites et duplications, et l'audit des tableaux. Pour le détail d'un axe, lancer le script correspondant (`scorecard.py`, `traceability.py`, `numbers.py`, etc.).

## 3. Restituer

Présenter le scorecard avec le détail par axe, puis les constats complémentaires (empreinte IA, cohérence, tableaux), classés par priorité. Proposer les correctifs, sans réécrire le document sauf demande.

## Format de sortie

Le rapport d'audit consolidé (note sur 100, axes, signaux), plus une courte liste d'actions prioritaires. Si l'utilisateur le souhaite, enchaîner vers `controler` (revue) pour corriger.

## Règles

1. L'extraction préserve la structure (titres, tableaux, références) autant que possible.
2. L'audit ne modifie pas le document, il l'évalue.
3. Le scorecard est déterministe et reproductible, la note ne dépend pas de l'humeur du modèle.
4. Classer les constats par priorité, du critique au mineur.

## Inventaire des images

Au-delà du texte, recenser les images du document source pour ne rien perdre à la reprise :

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/images.py extract FICHIER --out images/
```

Le manifeste liste les images, leurs dimensions et les doublons. Signaler leur nombre dans l'audit. Pour une reprise, les replacer via `produire` (image) puis `livrer` (document).

## Audit de fuites (ce que le fichier trahit de son auteur)

Un document bureautique ne transporte pas que son texte. Il porte le nom de qui l'a écrit et de qui l'a enregistré en dernier, celui de l'organisation, le nombre d'enregistrements successifs, le temps d'édition cumulé, parfois des commentaires et des modifications suivies que personne n'a acceptées, parfois le chemin local d'un fichier lié. Un PDF porte son dictionnaire Info et son bloc XMP. Ces traces partent avec le fichier et s'ouvrent en trois gestes chez le destinataire, qui n'a pas eu à les chercher.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-fuites.py LIVRABLE.docx --auteur "Prenom Nom"
```

Quatre familles couvertes : texte OOXML, diapositives OOXML, ODF et PDF. Le rapport range les constats par catégorie (identité et organisation, résidus de travail, intégrité du fichier, historique d'édition, chemins locaux) et se ferme sur quatre verdicts : fuites confirmees, fuites probables, traces sans identite lisible, rien a signaler.

### Confiance graduée

Un champ rempli et un champ présent ne disent pas la même chose, donc chaque constat porte son niveau de preuve. `confirme` : une valeur lisible identifie une personne, une organisation ou une machine. `probable` : une valeur existe et paraît identifiante sans certitude. `informatif` : une structure est présente sans contenu lisible ici. `douteux` : le constat a de bonnes chances d'être un faux positif, rapporté pour ne rien taire plutôt que pour être corrigé. L'option `--auteur` sert cette graduation : le nom de l'auteur déclaré figure déjà sur la page de garde, un champ qui le porte redescend en `douteux` au lieu d'encombrer le rapport. Restituer les constats confirmés d'abord, avec la valeur exacte lue dans le fichier ; un rapport qui annonce des métadonnées sans les citer ne permet aucune décision.

### Le contrôle inspecte, il ne nettoie pas

Le script n'écrit jamais dans le fichier examiné. Supprimer une trace est une décision éditoriale : un nom d'organisation peut être exigé par le destinataire, un commentaire peut être volontaire, une modification suivie peut être le livrable lui-même. Effacer d'office trancherait à la place de l'auteur et rendrait le geste invisible, alors que le repérage laisse la décision documentée. Quand le nettoyage est décidé, il se fait dans l'application d'origine (inspecteur de document Word, export neuf pour un PDF), puis le contrôle se rejoue pour vérifier le résultat plutôt que de le supposer.

### Le piège de la mise à jour incrémentale d'un PDF

Un outil comme exiftool écrit dans un PDF de façon incrémentale : il ajoute un bloc en fin de fichier qui libère l'objet Info et le retire du trailer, mais les octets d'origine restent dans le fichier, verbatim et récupérables. La commande sort en succès, le lecteur n'affiche plus rien et le fichier grossit au lieu de maigrir, ce qui est le signe. Croire une métadonnée supprimée alors qu'elle reste lisible est pire que de la savoir présente, parce que la première croyance ferme la vérification. Le script compte les marqueurs `%%EOF` et les renvois `/Prev` vers une table xref antérieure, puis rend un constat confirmé quand les deux sont réunis. Un tel PDF n'est pas fautif en soi (une signature électronique procède ainsi), mais son état antérieur reste dans le fichier : pour un envoi sensible, réexporter un PDF neuf depuis la source plutôt que corriger l'existant.

### Ce que le contrôle ne voit pas

Le rapport nomme ses propres angles morts, à reprendre dans la restitution. Le contenu rédactionnel n'est pas jugé ici, seules les traces le sont. Les métadonnées des images incorporées ne sont pas ouvertes une par une (voir `images.py extract` puis `manifest`). Les macros et le code embarqué ne sont pas analysés. Un PDF chiffré n'est inspecté que par son enveloppe. Les objets rangés dans un flux compressé échappent à la lecture binaire, donc une absence de constat n'est pas une preuve d'absence.
