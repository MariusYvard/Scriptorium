# Scripts déterministes de Scriptorium

Vingt outils en Python pur (bibliothèque standard, aucune dépendance). Ils déplacent la rigueur du jugement du modèle vers un contrôle mécanique et reproductible. Les compétences `controler`, `produire` et `livrer` les appellent, et le hook les exécute après chaque écriture de document.

Sur Windows, remplacer `python3` par `python` si nécessaire.

## lint-style.py

Détecte les écarts au style maison sans jugement de modèle : tiret cadratin, typographie courbe, lexique promotionnel banni, paramètres de suivi dans les URL, virgule d'Oxford, métadiscours, pronom « on », quantificateurs vagues, verbes tics.

```
python3 lint-style.py FICHIER [--format text|json] [--strict] [--quiet]
cat doc.md | python3 lint-style.py -
```

Code de sortie 1 si un constat critique est présent (ou majeur avec `--strict`). Pragmas dans le document : une ligne contenant `lint-style:ignore` est sautée, un fichier contenant `lint-style:ignore-file` dans ses cinq premières lignes est ignoré.

## verify-sources.py

Extrait les URL et les DOI, retire les paramètres de suivi, repère les doublons, contrôle la syntaxe des DOI. La résolution réseau est optionnelle, en deux niveaux.

```
python3 verify-sources.py FICHIER [--format text|json] [--check-links] [--reseau]
```

`--check-links` vérifie que les URL résolvent. `--reseau` va plus loin : il triangule chaque DOI contre Crossref, OpenAlex et Semantic Scholar (similarité de titre, seuil 0,70), rend un verdict gradué par référence (verifie, plausible, inverifiable, fabrique) et signale les sources potentiellement contaminées (année récente, absente des index interrogés). Un index qui ne répond pas est omis du verdict, jamais compté contre une référence. OpenAlex exige une clé (`--openalex-cle` ou `OPENALEX_API_KEY`), sinon il est simplement omis. Sans réseau, chaque URL reçoit aussi un palier de source (revue à comité, preprint, institutionnel, encyclopédie, presse et blog) par table locale de domaines. Code de sortie 1 si une URL est à nettoyer, un doublon existe, un DOI est douteux ou (réseau actif) un lien ne résout pas.

## readability.py

Métriques de lisibilité françaises : longueur de phrase moyenne et écart-type, part de phrases longues et courtes, longueur de paragraphe, densité lexicale, approximation du taux de passif, indice LIX. Transforme la règle « varier le rythme » en mesure.

```
python3 readability.py FICHIER [--format text|json]
```

## theme.py

Charge et valide une charte graphique (couleurs, polices, accent, palette), contrôle le contraste WCAG entre l'encre et les fonds. Une couleur mal formée est une erreur, un contraste sous 4,5:1 un avertissement.

```
python3 theme.py charte.json [--format text|json|css|latex]
```

`--format latex` émet le préambule de couleurs et de polices consommé par `assets/gabarit-rapport.tex` et `assets/gabarit-poster.tex`. Les palettes nommées `okabe-ito` et `wong` (daltonisme-sûres) s'injectent par la clé `palette` de la charte ; une palette manuelle est passée au crible d'une approximation dichromate (avertissement, jamais une erreur).

## figures.py

Génère des figures stratégiques en SVG (sans dépendance) et porte un regard critique déterministe sur la figure avant insertion.

```
python3 figures.py TYPE --out fichier.svg [--data data.json|-] [--title "Titre"]
python3 figures.py TYPE --data - --audit < data.json
```

TYPE : `swot`, `bcg`, `ansoff`, `pestel`, `chaine-valeur`, `tam-sam-som`. L'option `--audit` liste les défauts structurels (cases vides, surcharge, déséquilibre, valeurs hors bornes, points non étiquetés) sans écrire de fichier.

Formats de données attendus :

- swot : `{"forces":[...],"faiblesses":[...],"opportunites":[...],"menaces":[...]}`
- bcg : `{"items":[{"nom":"...","croissance":0-100,"part":0-100,"taille":8-40}]}`
- ansoff : `{"penetration":[...],"extension_produit":[...],"extension_marche":[...],"diversification":[...]}`
- pestel : `{"politique":[...],"economique":[...],"social":[...],"technologique":[...],"environnemental":[...],"legal":[...]}`
- chaine-valeur : `{"soutien":[...],"principales":[...]}`
- tam-sam-som : `{"tam":{"libelle":"...","valeur":"..."},"sam":{...},"som":{...}}` (audit : ordre TAM >= SAM >= SOM)

## traceability.py

Boucle la traçabilité : références citées mais absentes de la bibliographie, références listées mais jamais citées, figures et tableaux définis mais non appelés, appels à un objet inexistant. Compte aussi les tags de lacune normalisés `[LACUNE MATERIELLE]` et `[PREUVE FAIBLE]` (casse stricte), ventilés par section, et signale toute variante mal formée.

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

Lit du BibTeX, formate en APA 7, Vancouver, Chicago (auteur-date), MLA ou IEEE, déduplique par DOI, bascule une bibliographie d'un format à l'autre. Chaque entrée peut porter une ancre (champ `note` ou `annote` : citation exacte de 25 mots au plus, ou localisation précise type `p. 12`, `section 3.2`) ; le rapport d'ancrage liste les entrées sans ancre exploitable. La récupération d'une référence depuis un DOI (Crossref) est réseau et optionnelle.

```
python3 citations.py FICHIER.bib --to apa|vancouver|chicago|mla|ieee [--dedupe] [--exiger-ancres] [--valider] [--trier cle|annee|auteur]
python3 citations.py FICHIER.bib --bascule apa ieee
python3 citations.py --doi 10.xxxx/yyyy | --pmid N | --arxiv ID
```

`--exiger-ancres` renvoie un code de sortie 1 si une entrée n'a pas d'ancre. `--valider` rapporte les champs obligatoires manquants par type d'entrée, `--pmid` et `--arxiv` résolvent une référence en BibTeX (réseau, NCBI E-utilities et export.arxiv.org).

## check-temporel.py

Détecte cinq défaillances chronologiques qui survivent à une relecture humaine : date future présentée comme passée, version citée avant sa date connue (glossaire `--versions` optionnel), inversion causale (la cause datée après son effet dans la même phrase), langage à péremption (« le plus récent », « à ce jour », à ancrer par une date), chaîne de dates incohérente dans une référence. Consultatif par défaut, bloquant avec `--strict`.

```
python3 check-temporel.py FICHIER [--date-reference AAAA-MM-JJ] [--versions versions.json] [--format text|json] [--strict]
```

## diff-versions.py

Journal des écarts entre deux versions : sections ajoutées, supprimées, modifiées, avec le compte de mots changés.

```
python3 diff-versions.py ANCIEN.md NOUVEAU.md [--format text|json]
```

## scorecard.py

Agrège les sorties des scripts en une note de 0 à 100 sur cinq axes (style, sources, traçabilité, terminologie et nombres, lisibilité), pénalités fixes, calcul montré, verdict. Un plancher par axe plafonne la décision éditoriale : un axe effondré bloque malgré un bon total. La décision se rend sur quatre valeurs (accepter, revision mineure, revision majeure, refus). Le mode trajectoire compare deux rapports JSON (revue puis re-revue) : delta par axe, régression signalée sous -3.

```
python3 scorecard.py FICHIER [--format text|json] [--plancher N] [--poids POIDS.json] [--seuil-type brouillon|rapport|publication]
python3 scorecard.py --trajectoire AVANT.json APRES.json
```

Le rapport texte porte une barre ASCII par axe et nomme le meilleur et le pire axe. Les poids externes sont renormalisés à somme 1. La trajectoire signale l'arrêt anticipé quand le gain total reste sous +3 sans régression.

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

Mémoire de projet : un fichier projet.json conserve le brief, la charte, le glossaire, les sources, le profil et le plan, plus un journal de mission append-only (entrées horodatées, jamais modifiées). Les frontières portent un hash de continuité (SHA-256 du journal, 12 hexadécimaux) et la reprise se fait par ce hash, une seule fois chacune. Les étapes suivent cinq états à transitions vérifiées, les artefacts des versions strictement croissantes, la configuration de génération se documente sans promettre le rejeu.

```
python3 project.py init | show | get CLE | set CLE VALEUR
python3 project.py etape NOM ETAT [--motif TEXTE]
python3 project.py artefact NOM | frontiere "LIBELLE" | reprendre HASH
python3 project.py reproductibilite --plugin-version X.Y.Z --modele NOM
python3 project.py status
```

## check-presentation.py

Valide un deck exporté en PDF : nombre de pages confronté à la durée annoncée (1 à 2 diapositives par minute), densité de texte par page, pages illisibles. L'extraction de texte et le rendu passent par des backends optionnels en cascade (pypdf, pdftotext, pdftoppm) ; un backend absent dégrade proprement (mesure sautée et déclarée, jamais inventée). Consultatif par défaut.

```
python3 check-presentation.py DECK.pdf [--duree MINUTES] [--format text|json] [--strict]
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

Porte d'intégration continue éditoriale : passe ou échoue un ou plusieurs documents contre un seuil de scorecard. Passer outre exige une friction croissante (avertissement, puis justification, puis justification de cent caractères au moins) et chaque passage outre est journalisé.

```
python3 tools/check.py "chemin/**/*.md" --seuil 85 [--outrepasser] [--justification "..."] [--projet projet.json]
```
