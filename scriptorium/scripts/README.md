# Scripts déterministes de Scriptorium

Vingt-quatre outils en Python pur (bibliothèque standard, aucune dépendance). Ils déplacent la rigueur du jugement du modèle vers un contrôle mécanique et reproductible. Les compétences `controler`, `produire` et `livrer` les appellent, et le hook les exécute après chaque écriture de document.

Sur Windows, remplacer `python3` par `python` si nécessaire.

## lint-style.py

Détecte les écarts au style maison sans jugement de modèle : tiret cadratin, typographie courbe, lexique promotionnel banni, paramètres de suivi dans les URL, virgule d'Oxford, métadiscours, pronom « on », quantificateurs vagues, verbes tics, caractères invisibles.

```
python3 lint-style.py FICHIER [--format text|json] [--strict] [--quiet]
cat doc.md | python3 lint-style.py -
```

Code de sortie 1 si un constat critique est présent (ou majeur avec `--strict`). Pragmas dans le document : une ligne contenant `lint-style:ignore` est sautée, un fichier contenant `lint-style:ignore-file` dans ses cinq premières lignes est ignoré.

Six règles couvrent les caractères invisibles, ce qui ne s'affiche pas à l'écran mais voyage avec le fichier. `caractere-invisible` (majeur) relève la largeur nulle (U+200B, U+2060, U+FEFF) et le trait d'union conditionnel (U+00AD). `zone-privee` (majeur) relève la zone à usage privé (U+E000 à U+F8FF), dont le rendu dépend de la police installée. `controle-bidi` (critique) relève les marques d'écriture bidirectionnelle (U+202A à U+202E, U+2066 à U+2069), qui font lire un texte autrement qu'il n'est écrit. `caractere-tag` (critique) relève les caractères de tag (U+E0000 à U+E007F), invisibles et porteurs de données. `espace-exotique` (mineur) relève les espaces typographiques hors espace ordinaire et insécable (U+2000 à U+200A, U+2028, U+2029, U+205F, U+3000). Ces caractères survivent au copier-coller, cassent la recherche plein texte, l'appariement d'une citation à son ancre et la lecture d'un diff ; certaines revues rejettent un fichier qui en porte.

`liant-inutile` (majeur) traite à part les liants de largeur nulle (U+200C, U+200D). Ils portent du sens dans les écritures arabe et indiennes ainsi que dans les séquences d'emoji composées, où ils soudent des codes distincts en un seul signe : les relever partout lèverait un faux positif à chaque drapeau et à chaque famille. Ils ne sont donc signalés qu'entre deux lettres latines, où ils ne servent à rien.

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

Ancrage à trois couches (`references/integrite-sources.md`). La couche 1, existence de la référence, reste couverte par verify-sources.py. La couche 2, localisation, qualifie chaque ancre en type fermé (citation, page, structure, horodatage, aucune) et nomme les formes mal formées (page nulle ou négative, plage inversée, citation trop longue, guillemets non fermés) comme un défaut plutôt que de les faire passer pour une ancre valide. La couche 3, fidélité (`--auditer-fidelite DOCUMENT.md`), mesure l'écart entre une affirmation et le texte de l'ancre qui la soutient (montée en force modale, chiffre orphelin, généralisation retirée), uniquement quand l'ancre porte une citation exacte, et n'émet jamais de verdict de fidélité global : ce jugement reste consultatif.

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

## gabarit.py

Gabarits de document imposés par un tiers, en quatre familles détectées par le contenu du fichier puis par son extension (un fichier qui commence par `%PDF-` est un PDF quelle que soit son extension). Texte OOXML (.docx, .dotx, .docm) et diapositives OOXML (.pptx, .potx, .pptm) : inventaire complet, comparaison et remplissage. Texte et diapositives ODF (.odt, .ott, .odp, .otp) : inventaire et comparaison, remplissage non implémenté. PDF : inventaire et comparaison en lecture seule, jamais de remplissage, une page fixe déjà composée ne se remplit pas. Tout est lu avec `zipfile` et `xml.etree` (ou en binaire direct pour un PDF), sans dépendance.

Trois actions communes aux familles concernées. `inventorier` extrait la structure d'un gabarit fourni dans un JSON déclaratif qui porte lui-même la liste de ce qu'il ne couvre pas : pour un document texte, styles nommés, hiérarchie de titres, style de corps, marges et format de page, en-têtes et pieds, polices, protection en édition ; pour une diapositive, dispositions nommées, espaces réservés et taille de diapositive en plus ; pour un PDF, nombre de pages, format de page nommé (A4, Letter), orientation, polices et proportion incorporée, chiffrement et version, sans les marges, qui ne sont pas une donnée du fichier. `comparer` confronte un document à cet inventaire et rend un verdict fermé (conforme, écarts mineurs, écarts majeurs) par identifiant stable, jamais par le libellé affiché qu'un Word ou un PowerPoint francisé renomme ; comparer deux familles différentes est refusé. `remplir` injecte le contenu dans le gabarit lui-même, dans ses styles ou ses dispositions existants, plutôt que de générer un fichier neuf qui perdrait filigrane, numérotation liée, masque de diapositive ou thème de couleurs ; l'option `--disposition` choisit la disposition du gabarit dans laquelle les diapositives sont créées. Une nouvelle sous-commande `formats` liste les familles et leurs extensions.

```
python3 gabarit.py inventorier GABARIT.docx|.pptx|.odt|.pdf [--out INVENTAIRE.json] [--format text|json]
python3 gabarit.py comparer INVENTAIRE.json DOCUMENT [--format text|json] [--strict]
python3 gabarit.py remplir INVENTAIRE.json CONTENU.md --out SORTIE [--logo FICHIER] [--logo-largeur-cm N] [--disposition NOM]
python3 gabarit.py formats
```

La comparaison des styles se fait par identifiant (`w:styleId` en Word, nom de disposition en PowerPoint, `style:name` en ODF), jamais par le libellé affiché. Le remplissage s'arrête sur un gabarit protégé en édition, ou sur un ODF ou un PDF, plutôt que de produire un fichier douteux, et ajoute le contenu avant la dernière section sans supprimer les paragraphes ou les diapositives de remplissage du gabarit. Code de sortie 1 sur écart majeur.

## check-lecture-pdf.py

Préflight d'intégrité de lecture, à lancer avant tout ancrage de citation sur une source PDF : un ancrage sur une page suppose que le texte de cette page a réellement été extrait, ce que le script vérifie plutôt que de le supposer. Verdict fermé sur quatre valeurs : lecture fiable, lecture partielle, lecture non fiable, non mesurable, ce dernier ne se confondant jamais avec le troisième (l'absence de tout backend PDF dégrade proprement vers non mesurable). Le rapport liste les pages ancrables et les pages non ancrables, signale les pages sans texte (scan sans OCR), les pages à l'encodage suspect (mojibake) et un fichier chiffré ou protégé, déclaré et jamais contourné. Les contrôles binaires (en-tête `%PDF-`, marqueur `%%EOF`, table xref) restent disponibles sans aucun backend installé, en réutilisant la cascade de backends de check-presentation.py par import de chemin.

```
python3 check-lecture-pdf.py FICHIER.pdf [--format text|json] [--strict]
```

Module importable : `analyser(chemin)` renvoie le rapport, `rapport_texte(rapport)` le met en forme.

## check-fuites.py

Inventaire de ce qu'un livrable trahit de son auteur, à lancer avant de l'envoyer. Quatre familles lues avec la bibliothèque standard seule : texte OOXML (.docx, .dotx, .docm), diapositives OOXML (.pptx, .potx, .pptm), ODF (.odt, .ott, .odp, .otp) et PDF. Le script relève les propriétés de document (auteur d'origine, dernière personne à avoir enregistré, organisation, responsable déclaré, titre, sujet, mots-clés), l'historique d'édition (nombre d'enregistrements successifs, temps d'édition cumulé), les résidus de travail (modifications suivies non acceptées, commentaires avec le nom de leur auteur, texte masqué, notes du présentateur en PowerPoint, dossier customXml, liste des collaborateurs), les chemins locaux fuités par les relations du paquet et, pour un PDF, le dictionnaire Info, le bloc XMP, le chiffrement déclaré, les fichiers embarqués et les annotations.

```
python3 check-fuites.py FICHIER [--auteur "Prenom Nom"] [--format text|json] [--strict]
```

Chaque constat porte une confiance graduée, parce qu'un champ rempli et un champ présent ne disent pas la même chose : `confirme` (une valeur lisible identifie une personne, une organisation ou une machine), `probable` (une valeur existe et paraît identifiante sans certitude), `informatif` (une structure est présente sans contenu lisible), `douteux` (le constat a de bonnes chances d'être un faux positif, rapporté pour ne rien taire). Le verdict se ferme sur quatre valeurs : fuites confirmees, fuites probables, traces sans identite lisible, rien a signaler. L'option `--auteur` reclasse en `douteux` un champ qui porte l'auteur déclaré du document, déjà public sur la page de garde. Consultatif par défaut, `--strict` renvoie 1 dès le premier constat confirmé.

Le script inspecte et ne nettoie jamais. Supprimer une trace est une décision éditoriale qui appartient à l'auteur, la repérer est une mesure ; un outil qui efface d'office déciderait à sa place et rendrait le geste invisible.

La détection de mise à jour incrémentale d'un PDF suit la même logique. Un outil comme exiftool écrit dans un PDF de façon incrémentale : il ajoute un bloc en fin de fichier qui libère l'objet Info et le retire du trailer, mais les octets d'origine restent dans le fichier, verbatim et récupérables. La commande sort en succès, le lecteur n'affiche plus rien et le fichier grossit au lieu de maigrir. Croire une métadonnée supprimée alors qu'elle reste lisible est pire que de la savoir présente, donc le script compte les marqueurs `%%EOF` et les renvois `/Prev` vers une table xref antérieure. Deux marqueurs de fin ou plus accompagnés d'un renvoi donnent un constat confirmé. Un PDF à mise à jour incrémentale n'est pas fautif en soi (une signature électronique procède ainsi), mais son état antérieur reste dans le fichier.

Le rapport se termine par ce que le contrôle ne regarde pas (contenu rédactionnel, métadonnées des images incorporées, macros et code embarqué, enveloppe seule d'un PDF chiffré, objets rangés dans un flux compressé), pour qu'une absence de constat ne se lise pas comme un quitus.

## logos.py

Registre de logos, séparé de la charte graphique parce qu'un logo obéit aux règles de l'organisation qui le possède (zone de respiration, taille minimale, usages autorisés, rang protocolaire) et non à celles du document. `valider` contrôle le format du registre, l'existence des fichiers, le ratio déclaré et la résolution effective de chaque logo à la taille où il sera affiché (pixels divisés par la largeur en pouces, seuils consultatifs de 300 dpi à l'impression et 150 dpi à l'écran). `placer` rend le fragment prêt à insérer pour un usage, en HTML ou en LaTeX ; en docx l'insertion réelle passe par `gabarit.py remplir --logo`, qui écrit aussi la relation et le manifeste de types.

```
python3 logos.py valider REGISTRE.json [--format text|json] [--strict]
python3 logos.py placer REGISTRE.json --usage page-garde|en-tete|pied|co-signature --format docx|latex|html
```

Format du registre dans `assets/registre-logos.exemple.json`. Un fichier absent est une erreur, une résolution basse un avertissement. Un logo dont le fichier manque est écarté du placement plutôt que référencé à vide.

## tools/check.py

Porte d'intégration continue éditoriale : passe ou échoue un ou plusieurs documents contre un seuil de scorecard. Passer outre exige une friction croissante (avertissement, puis justification, puis justification de cent caractères au moins) et chaque passage outre est journalisé.

```
python3 tools/check.py "chemin/**/*.md" --seuil 85 [--outrepasser] [--justification "..."] [--projet projet.json]
```

## tools/gold.py

Jeu d'or versionné et porte de régression directionnelle pour scorecard.py et lint-style.py. `verifier` contrôle la santé du corpus figé de `evals/gold/` contre neuf invariants numérotés (I1 à I9), dont le plus important (I6) impose que chaque étiquette attendue soit recalculable par les vraies constantes du dépôt (`AXES_CONNUS`, les sévérités du linter) plutôt que par une liste recopiée dans le validateur. `mesurer` rejoue le corpus avec les fonctions réelles du dépôt et écrit un rapport horodaté portant la version du plugin. `comparer` confronte deux rapports polarité par polarité (chaque métrique déclare si elle doit monter ou descendre) et signale une métrique absente au candidat comme une régression plutôt que comme un succès par défaut.

```
python3 tools/gold.py verifier [--format text|json]
python3 tools/gold.py mesurer [--format text|json] [--out FICHIER]
python3 tools/gold.py comparer REFERENCE.json CANDIDAT.json [--format text|json] [--bloquant] [--outrepasser] [--justification "..."] [--projet FICHIER]
```

Consultatif par défaut : `comparer` renvoie 0 même en régression, sauf avec `--bloquant`, qui exige alors `--outrepasser` à la même friction à trois crans que tools/check.py pour passer outre. Non câblé en intégration continue tant qu'aucun rapport de référence n'est publié.
