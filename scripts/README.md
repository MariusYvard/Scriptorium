# Scripts déterministes de Scriptorium

Dix-huit outils en Python pur (bibliothèque standard, aucune dépendance). Ils déplacent la rigueur du jugement du modèle vers un contrôle mécanique et reproductible. Les compétences `controler`, `produire` et `livrer` les appellent, et le hook les exécute après chaque écriture de document.

Sur Windows, remplacer `python3` par `python` si nécessaire.

## lint-style.py

Détecte les écarts au style maison sans jugement de modèle : tiret cadratin, typographie courbe, lexique promotionnel banni, paramètres de suivi dans les URL, virgule d'Oxford, métadiscours, pronom « on », quantificateurs vagues, verbes tics.

```
python3 lint-style.py FICHIER [--format text|json] [--strict] [--quiet]
cat doc.md | python3 lint-style.py -
```

Code de sortie 1 si un constat critique est présent (ou majeur avec `--strict`). Pragmas dans le document : une ligne contenant `lint-style:ignore` est sautée, un fichier contenant `lint-style:ignore-file` dans ses cinq premières lignes est ignoré.

## verify-sources.py

Extrait les URL et les DOI, retire les paramètres de suivi, repère les doublons, contrôle la syntaxe des DOI. La résolution réseau est optionnelle.

```
python3 verify-sources.py FICHIER [--format text|json] [--check-links]
```

`--check-links` est désactivé par défaut. Code de sortie 1 si une URL est à nettoyer, un doublon existe, un DOI est douteux ou (avec `--check-links`) un lien ne résout pas.

## readability.py

Métriques de lisibilité françaises : longueur de phrase moyenne et écart-type, part de phrases longues et courtes, longueur de paragraphe, densité lexicale, approximation du taux de passif, indice LIX. Transforme la règle « varier le rythme » en mesure.

```
python3 readability.py FICHIER [--format text|json]
```

## theme.py

Charge et valide une charte graphique (couleurs, polices, accent, palette), contrôle le contraste WCAG entre l'encre et les fonds. Une couleur mal formée est une erreur, un contraste sous 4,5:1 un avertissement.

```
python3 theme.py charte.json [--format text|json|css]
```

## figures.py

Génère des figures stratégiques en SVG (sans dépendance) et porte un regard critique déterministe sur la figure avant insertion.

```
python3 figures.py TYPE --out fichier.svg [--data data.json|-] [--title "Titre"]
python3 figures.py TYPE --data - --audit < data.json
```

TYPE : `swot`, `bcg`, `ansoff`, `pestel`, `chaine-valeur`. L'option `--audit` liste les défauts structurels (cases vides, surcharge, déséquilibre, valeurs hors bornes, points non étiquetés) sans écrire de fichier.

Formats de données attendus :

- swot : `{"forces":[...],"faiblesses":[...],"opportunites":[...],"menaces":[...]}`
- bcg : `{"items":[{"nom":"...","croissance":0-100,"part":0-100,"taille":8-40}]}`
- ansoff : `{"penetration":[...],"extension_produit":[...],"extension_marche":[...],"diversification":[...]}`
- pestel : `{"politique":[...],"economique":[...],"social":[...],"technologique":[...],"environnemental":[...],"legal":[...]}`
- chaine-valeur : `{"soutien":[...],"principales":[...]}`

## traceability.py

Boucle la traçabilité : références citées mais absentes de la bibliographie, références listées mais jamais citées, figures et tableaux définis mais non appelés, appels à un objet inexistant.

```
python3 traceability.py FICHIER [--format text|json]
```

## terminology.py

Construit le glossaire des sigles, signale un sigle non défini ou employé avant sa définition, et les variantes orthographiques d'un même terme.

```
python3 terminology.py FICHIER [--format text|json]
```

## numbers.py

Signale les pourcentages supérieurs à 100, les partitions de pourcentages qui ne somment pas à cent, et un séparateur décimal mixte.

```
python3 numbers.py FICHIER [--format text|json]
```

## citations.py

Lit du BibTeX, formate en APA 7 ou Vancouver, déduplique par DOI. La récupération d'une référence depuis un DOI (Crossref) est réseau et optionnelle.

```
python3 citations.py FICHIER.bib --to apa|vancouver [--dedupe]
python3 citations.py --doi 10.xxxx/yyyy
```

## diff-versions.py

Journal des écarts entre deux versions : sections ajoutées, supprimées, modifiées, avec le compte de mots changés.

```
python3 diff-versions.py ANCIEN.md NOUVEAU.md [--format text|json]
```

## scorecard.py

Agrège les sorties des scripts en une note de 0 à 100 sur cinq axes (style, sources, traçabilité, terminologie et nombres, lisibilité), pénalités fixes, calcul montré, verdict.

```
python3 scorecard.py FICHIER [--format text|json]
```

## ai-fingerprint.py

Mesure les marqueurs d'empreinte IA : variabilité de longueur de phrase, ouvertures répétitives, cadence ternaire, connecteurs suremployés, bigrammes répétés, amplification contrastive.

```
python3 ai-fingerprint.py FICHIER [--format text|json]
```

## coherence.py

Repère les paragraphes quasi dupliqués (auto-plagiat), les phrases répétées, et liste les promesses du texte à vérifier.

```
python3 coherence.py FICHIER [--format text|json]
```

## tables.py

Génère un tableau Markdown autonome depuis un CSV ou un JSON, et audite les tableaux d'un document (cellules vides, colonne sans unité, total incohérent).

```
python3 tables.py gen DATA.csv|.json [--caption "..."] [--source "..."]
python3 tables.py audit DOCUMENT.md
```

## plan-check.py

Confronte un plan (plan.json) au document : sections prévues présentes ou manquantes, sections hors plan, couverture.

```
python3 plan-check.py PLAN.json DOCUMENT.md [--format text|json]
```

## project.py

Mémoire de projet : un fichier projet.json conserve le brief, la charte, le glossaire, les sources, le profil et le plan.

```
python3 project.py init | show | get CLE | set CLE VALEUR
```

## audit-doc.py

Audit consolidé d'un document : scorecard, empreinte IA, cohérence, audit de tableaux, en un seul rapport.

```
python3 audit-doc.py FICHIER [--format text|json]
```

## images.py

Extrait les images d'un PDF ou d'un document Office (Word, PowerPoint, Excel, ODF), déduplique par empreinte, lit les dimensions dans l'en-tête, écrit un manifeste JSON. Le PDF passe par un backend optionnel (PyMuPDF, pdfimages, pypdf) ou, à défaut, par le skill pdf.

```
python3 images.py extract SOURCE --out DIR [--min-bytes N]
python3 images.py manifest DIR
```

## tools/check.py

Porte d'intégration continue éditoriale : passe ou échoue un ou plusieurs documents contre un seuil de scorecard.

```
python3 tools/check.py "chemin/**/*.md" --seuil 85
```
