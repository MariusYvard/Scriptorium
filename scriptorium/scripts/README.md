# Scripts déterministes de Scriptorium

Vingt-sept outils en Python pur (bibliothèque standard, aucune dépendance). Ils déplacent la rigueur du jugement du modèle vers un contrôle mécanique et reproductible. Les compétences `controler`, `produire` et `livrer` les appellent, et le hook les exécute après chaque écriture de document.

Sur Windows, remplacer `python3` par `python` si nécessaire.

## lint-style.py

Détecte les écarts au style maison sans jugement de modèle : tiret cadratin, typographie courbe, lexique promotionnel banni, paramètres de suivi dans les URL, virgule d'Oxford, métadiscours, pronom « on », quantificateurs vagues, verbes tics, caractères invisibles. Français par défaut, anglais avec `--langue en` (voir le mode de langue plus bas).

```
python3 lint-style.py FICHIER [--format text|json] [--strict] [--quiet] [--langue fr|en|auto]
cat doc.md | python3 lint-style.py -
```

Code de sortie 1 si un constat critique est présent (ou majeur avec `--strict`). Pragmas dans le document : une ligne contenant `lint-style:ignore` est sautée, un fichier contenant `lint-style:ignore-file` dans ses cinq premières lignes est ignoré.

### Mode de langue

Le linter analyse en français ou en anglais. La langue se détermine par un ordre de priorité fixe : l'option `--langue fr|en` prime sur tout ; sinon le pragme `lint-style:langue=en` placé dans les cinq premières lignes du document, seul canal disponible pour le hook, qui ne passe aucune option fichier par fichier ; sinon le français. `--langue auto` lance une détection heuristique (comptage de mots outils exclusifs à chaque langue, verdict rendu au-dessus de douze mots reconnus et de 60 % de part pour le gagnant, défaut français en dessous). La détection n'est pas le comportement par défaut : le linter est appelé sans argument par le hook et par `scorecard.py`, et une bascule automatique changerait en silence le verdict d'un document déjà validé. Le mode français est identique à celui d'avant l'ajout de l'anglais, constat par constat.

Les règles se répartissent en trois familles, déclarées par le dictionnaire `FAMILLE`. Les communes valent dans les deux langues, avec le même motif : typographie courbe, caractères invisibles, paramètres de suivi dans les URL. Les françaises sortent de l'analyse anglaise : virgule d'Oxford, pronom « on », lexique promotionnel français, tournures faibles, quantificateurs vagues, tiret cadratin. Le métadiscours est banni des deux côtés, sous un motif propre à chaque langue. La virgule sérielle est le cas décisif : recommandée en anglais par Chicago, l'APA et la MLA, la signaler serait un faux positif à chaque énumération, donc `virgule-oxford` ne se déclenche jamais en mode anglais.

Onze règles de ligne sont propres à l'anglais. `lexique-promo` (critique) transpose le lexique d'éloge banni. `lexique-ia-en` (majeur) relève le vocabulaire dont la surreprésentation dans les textes assistés a été mesurée sur quinze millions de résumés PubMed, plus `landscape` au sens figuré repéré par cooccurrence. `significance-non-statistique` (majeur) signale `significant` hors contexte statistique explicite, et se tait quand la ligne porte une valeur de p, la mention `statistically`, un intervalle de confiance ou un nom de test. `hedge-empile` (majeur) attrape les modalisateurs superposés du type `may potentially suggest`. `metadiscours`, `nominalisation`, `verbe-tic` et `lexique-faible` couvrent les périphrases et les verbes tics. Trois règles visent le francophone : `espace-avant-ponctuation` (majeur) pour l'espace avant `: ; ! ?`, correcte en français et fautive en anglais, `indenombrable-en` (majeur) pour `informations` ou `researches`, `faux-ami` (mineur) pour `actually`, `eventually`, `control that`, `allow to` et leurs voisins.

Trois règles anglaises de plus se lisent à l'échelle du document plutôt que de la ligne. `orthographe-melangee` (majeur) signale la présence simultanée de formes exclusivement britanniques et exclusivement américaines, sans recommander l'une des deux variantes. Le suffixe `-ize` n'entre pas dans le calcul : l'orthographe d'Oxford l'emploie en anglais britannique, donc il ne prouve rien ; et aucun motif général en `-ise` n'est utilisé, ce qui met hors d'atteinte les verbes toujours en `-ise` (exercise, comprise, revise, surprise). `tiret-cadratin-densite` (mineur) remplace l'interdiction du tiret cadratin, ponctuation légitime en anglais : le constat n'apparaît qu'à partir de trois occurrences et d'une densité supérieure à trois pour mille mots, seuils de convention maison réglables. `passif-excessif` (mineur) mesure la part de phrases passives et se tait sous la moitié, la section Methods admettant le passif (APA 7, section 4.13).

La règle de temps (présent pour un fait établi et pour ce que montre une figure, passé pour ce qui a été fait dans l'étude) reste hors du code : un linter voit le temps sans voir ce que la proposition énonce. Elle est documentée dans `skills/produire/references/style-anglais.md`, qui porte aussi les listes complètes et leurs sources.

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

Génère des figures en SVG (sans dépendance) et porte un regard critique déterministe sur la figure avant insertion. Deux familles : les figures stratégiques rangent des éléments dans des cases, les figures de données portent des axes gradués dont chacun reçoit un titre et son unité.

```
python3 figures.py TYPE --out fichier.svg [--data data.json|-] [--title "Titre"]
python3 figures.py TYPE --data - --audit < data.json
```

TYPE stratégiques : `swot`, `bcg`, `ansoff`, `pestel`, `chaine-valeur`, `tam-sam-som`. TYPE de données : `courbe`, `nuage`, `histogramme`, `boite`, `flux`, `prisma`. L'option `--audit` liste les défauts structurels (cases vides, surcharge, déséquilibre, valeurs hors bornes, points non étiquetés, axe sans titre ou sans unité, échelle d'histogramme tronquée, quartiles hors ordre, comptes PRISMA qui ne bouclent pas) sans écrire de fichier.

Formats de données attendus :

- swot : `{"forces":[...],"faiblesses":[...],"opportunites":[...],"menaces":[...]}`
- bcg : `{"items":[{"nom":"...","croissance":0-100,"part":0-100,"taille":8-40}]}`
- ansoff : `{"penetration":[...],"extension_produit":[...],"extension_marche":[...],"diversification":[...]}`
- pestel : `{"politique":[...],"economique":[...],"social":[...],"technologique":[...],"environnemental":[...],"legal":[...]}`
- chaine-valeur : `{"soutien":[...],"principales":[...]}`
- tam-sam-som : `{"tam":{"libelle":"...","valeur":"..."},"sam":{...},"som":{...}}` (audit : ordre TAM >= SAM >= SOM)
- courbe : `{"axe_x":{"titre":"...","unite":"..."},"axe_y":{...},"series":[{"nom":"...","points":[[x,y]],"erreurs":[e]}]}`
- nuage : `{"axe_x":{...},"axe_y":{...},"series":[{"nom":"...","points":[[x,y]],"ajustement":true}]}` (droite des moindres carrés déclarée en légende)
- histogramme : `{"axe_x":{"titre":"..."},"axe_y":{"titre":"...","unite":"..."},"barres":[{"categorie":"...","valeur":n,"erreur":e}]}` (ordonnées à partir de zéro)
- boite : `{"axe_x":{...},"axe_y":{...},"groupes":[{"nom":"...","valeurs":[...]}]}` ou les cinq nombres `min`, `q1`, `mediane`, `q3`, `max` avec `aberrants`
- flux : `{"niveaux":[{"titre":"...","boites":[{"libelle":"...","effectif":n,"sous":[...],"exclusions":[{"libelle":"...","effectif":n}]}]}]}`
- prisma : `{"identifiees":{"source":n},"doublons":n,"examinees":n,"ecartees_titre":[{"motif":"...","n":n}],"evaluees":n,"ecartees_texte":[...],"incluses":n}` (audit : les comptes bouclent aux trois jonctions)

Les séries d'une figure de données se distinguent par la couleur et par un second canal (forme du marqueur, style de trait). Les couleurs viennent de la palette de la charte, filtrées sur leur contraste avec le fond.

## traceability.py

Boucle la traçabilité : références citées mais absentes de la bibliographie, références listées mais jamais citées, objets définis mais non appelés, appels à un objet inexistant. Quatre types d'objets sont suivis : figures, tableaux, équations et annexes. Compte aussi les tags de lacune normalisés `[LACUNE MATERIELLE]` et `[PREUVE FAIBLE]` (casse stricte), ventilés par section, et signale toute variante mal formée.

Contrôle en plus la séquence des numéros, type par type : deux légendes portant le même numéro, un numéro absent de l'intervalle observé (figure 1 puis figure 3), une suite qui ne commence pas à 1, une numérotation d'annexes qui mélange chiffres et lettres. Apparier les numéros ne suffit pas, un document où la figure 2 manque reste cohérent au sens des appels alors qu'il est faux à la lecture.

Motifs de légende retenus, sur le Markdown source :

- Figure, tableau, annexe : une ligne qui ouvre sur le nom du type suivi de son numéro et d'un séparateur (`Figure 1 :`, `Tableau 2.`, `Annexe B :`), précédée au besoin d'une image Markdown. Les annexes se numérotent en chiffres ou en lettres capitales, sont lues sur le texte entier (elles se placent après la bibliographie) et la lettre doit rester capitale pour que "l'annexe a été jointe" ne passe pas pour une annexe A.
- Équation : trois notations acceptées, la légende en toutes lettres (`Équation 3 :`), la balise LaTeX `\tag{3}`, le numéro de droite en fin de ligne d'affichage (`$$ ... $$ (3)`). Une seule est comptée par ligne. La numérotation automatique de LaTeX (`\begin{equation}` sans `\tag`) ne laisse aucun numéro dans la source et sort du périmètre, le compilateur tenant alors la séquence.

Clés ajoutées à la sortie de `analyser()` : `equations_definies_non_appelees`, `equations_appelees_non_definies`, `annexes_definies_non_appelees`, `annexes_appelees_non_definies`, `sequences` (par type d'objet : `numeros`, `doublons`, `manquants`, `commence_a`, `commence_a_un`, `notation`) et `numerotation_anomalies` (liste de constats nommés `numero_duplique`, `numero_manquant`, `ne_commence_pas_a_un`, `notation_mixte`). Les clés antérieures sont inchangées, `scorecard.py` continue de les lire.

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

Il porte aussi le contrat de passation vers l'agent `redacteur`. Cet agent n'a que Read, Glob et Grep et rend son texte au parent : il ne lit pas `projet.json` et n'y écrit rien, donc ce que le parent ne lui passe pas explicitement n'existe pas pour lui. `objet` fixe le numéro d'un objet légendé (figure, tableau, équation, annexe) pour toute la mission, refuse de réaffecter un numéro déjà pris à un autre libellé et accepte le même enregistrement à l'identique. `passation` émet le glossaire des termes fixés, les objets déjà numérotés et le prochain numéro libre par type, en JSON ou en texte à coller dans le prompt du sous-agent, pour que la section suivante n'invente ni un synonyme ni un numéro déjà servi. La clé `objets_numerotes` suit la règle de compatibilité du script : absente d'un `projet.json` écrit avant elle, elle est complétée à vide en mémoire sans rien réécrire sur le disque.

```
python3 project.py init | show | get CLE | set CLE VALEUR
python3 project.py etape NOM ETAT [--motif TEXTE]
python3 project.py artefact NOM | frontiere "LIBELLE" | reprendre HASH
python3 project.py objet figure|tableau|equation|annexe NUMERO "LIBELLE"
python3 project.py passation [--format text|json]
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

`catalogue` applique les mêmes mesures à un dossier d'illustrations déjà produites (photos de dispositif, captures d'écran, schémas faits ailleurs) plutôt qu'aux médias tirés d'un document. Le catalogue écrit sert de liste des figures : par illustration, nom de fichier, format, dimensions, poids, empreinte, doublon éventuel, résolution effective à la largeur d'insertion prévue, largeur maximale qui tiendrait encore le seuil, plus un verdict pris dans une liste fermée (`utilisable`, `sous le seuil`, `doublon`, `dimensions illisibles`, `vecteur, resolution sans objet`, `hors perimetre`). Un fichier vectoriel n'est pas jugé sur une résolution qu'il n'a pas, un fichier qui n'est pas une image sort du périmètre sans devenir une alerte.

`convertir` rend un SVG en PNG pour la voie Word, qui n'affiche pas un SVG de façon fiable. Backends optionnels en cascade, dans l'ordre `rsvg-convert`, `inkscape`, le module Python `cairosvg`, puis ImageMagick (`magick` ou `convert`), aucun n'étant une dépendance du plugin. L'identité d'ImageMagick est vérifiée par `-version` avant usage : sous Windows, `convert.exe` est l'utilitaire système de conversion FAT vers NTFS, homonyme sans rapport, présent sur toute installation. Sans aucun backend, la commande sort en code 3 avec le statut `aucun-backend`, dit ce qu'il faut installer et déclare que le fichier source n'est pas en cause, ce qui la distingue de `echec-backend` (les backends présents ont échoué, le SVG est fautif), `source-absente` et `source-non-svg`.

Le calcul de résolution effective (pixels divisés par la largeur en pouces) et ses seuils consultatifs (300 dpi à l'impression, 150 dpi à l'écran) vivent ici pour tout le plugin. `logos.py` les reprend par import de chemin, comme `gabarit.py` importe déjà `images.py` : une photo de dispositif se mesure avec la même règle qu'un logo.

```
python3 images.py extract SOURCE --out DIR [--min-bytes N]
python3 images.py manifest DIR
python3 images.py catalogue DIR [--out FICHIER] [--largeur-cm N] [--usage impression|ecran] [--recursif] [--format text|json] [--strict]
python3 images.py convertir FIGURE.svg --out FIGURE.png [--largeur-px N] [--format text|json]
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

## check-droits.py

Droits de réutilisation d'une figure tierce, à contrôler avant de reproduire une image extraite d'une publication. Citer la source règle l'honnêteté intellectuelle, pas le droit de reproduction : une figure est une oeuvre protégée indépendamment du texte de l'article qui la porte. Le script résout la licence déclarée d'une source par son DOI, la classe sur quatre verdicts fermés, écrit la ligne d'attribution conforme puis valide le registre des figures empruntées.

```
python3 check-droits.py licence --doi 10.xxxx/yyyy [--reseau] [--openalex-cle CLE] [--format text|json] [--strict]
python3 check-droits.py registre REGISTRE.json [--reseau] [--format text|json] [--strict]
python3 check-droits.py credits REGISTRE.json [--sortie texte|html|latex]
```

Quatre verdicts : `reutilisable avec attribution` (CC BY, CC0, domaine public), `reutilisable sous conditions` (CC BY-SA impose sa licence au document dérivé, CC BY-NC ferme l'usage commercial, CC BY-ND interdit toute adaptation donc tout recadrage), `autorisation requise` (tous droits réservés, cas ordinaire d'une revue sur abonnement), `licence inconnue` (aucun index n'a répondu ou aucune licence déclarée). Le quatrième ne se confond jamais avec le troisième, comme `non mesurable` ne se confond pas avec `lecture non fiable` dans check-lecture-pdf.py : une absence d'information n'est ni une interdiction, ni une permission.

Le réseau est optionnel derrière `--reseau` et réutilise les fonctions de requête de verify-sources.py, chargées par chemin. Crossref porte un tableau `license` (URL, date d'application, version de contenu visée), OpenAlex porte la licence de la meilleure localisation ouverte plus le statut d'accès ouvert. Un tableau `license` rempli ne vaut pas licence de réutilisation : une revue sur abonnement y déclare souvent ses seules conditions de fouille de textes, qui ne couvrent pas la republication d'une figure. Un index qui ne répond pas sort du calcul et le dit.

Sur `autorisation requise` ou `licence inconnue`, le script nomme l'alternative qui évite la question. Les données ne sont pas protégeables : refaire la figure à partir des valeurs publiées, avec son propre rendu et la mention "d'après les données de X", ne reproduit aucune oeuvre. Il renvoie vers les types de figures de données de figures.py (`courbe`, `nuage`, `histogramme`, `boite`, `flux`, `prisma`).

Le registre est un JSON déclaratif de même forme que `assets/registre-logos.exemple.json` : une entrée par figure empruntée, avec sa source, son DOI, sa licence, son verdict, l'état de la demande d'autorisation (`non demandee`, `demandee`, `obtenue`, `refusee`) et la mention des modifications. La validation refuse un identifiant dupliqué, une source absente, un verdict hors liste fermée, un verdict que la licence déclarée contredit, un recadrage sous licence ND, une autorisation refusée. Le verdict du registre se ferme sur quatre valeurs : registre invalide, autorisations a obtenir, licences a etablir, credits complets. Consultatif par défaut, `--strict` renvoie 1 hors de `credits complets`.

Le script rapporte ce que la licence déclare, il ne prononce pas la légalité d'un usage : le contrat d'une revue ou la politique d'un employeur peuvent en décider autrement. Familles de licences, procédure d'autorisation auprès d'un éditeur et forme du registre dans `skills/produire/references/droits-figures.md`.

## check-disponibilite.py

Contrôle de la déclaration de disponibilité des données et du code, sur le manuscrit source, avant soumission. Les revues la réclament, les financeurs publics en font une obligation contractuelle, et une déclaration qui promet un accès inexistant est une affirmation fausse dans un article, du même ordre qu'un chiffre erroné.

```
python3 check-disponibilite.py FICHIER.md [--format text|json] [--strict]
cat manuscrit.md | python3 check-disponibilite.py -
```

Le script repère la section de disponibilité par son titre (intitulés français et anglais courants), y détecte le régime déclaré dans une liste fermée de six valeurs (`depot-ouvert`, `sur-demande`, `embargo`, `restriction-legale`, `donnees-de-tiers`, `aucune-donnee`), puis contrôle que chaque régime porte la preuve qu'il exige : identifiant pérenne quand l'ouverture est annoncée, date de levée quand un embargo est annoncé, licence nommée quand du code est annoncé, détenteur quand les données viennent d'un tiers, contact avec critères et durée quand l'accès est promis sur demande. Un exemple de déclaration cité dans un bloc de code n'est pas compté comme la déclaration du document.

Un identifiant pérenne est un DOI, un handle, un ARK, un SWHID ou un numéro d'accession, jamais une adresse web ordinaire : annoncer des données ouvertes en pointant une page de laboratoire est l'incohérence que ce contrôle sert à rendre visible. De même, un lien vers un dépôt de développement sans version figée ne vaut pas archivage, un dépôt pouvant être renommé, rendu privé, réécrit ou supprimé.

Chaque constat porte une confiance graduée, sur la même échelle que check-fuites.py : `confirme` (la section contredit ce qu'elle annonce, ou l'élément exigé est absent de bout en bout), `probable` (l'élément existe sous une forme qui ne suffit pas, licence évoquée sans être nommée par exemple), `informatif` (un état présent sans faute à corriger, comme la combinaison légitime de deux régimes), `douteux` (faux positif probable, rapporté pour ne rien taire). Une mention "sur demande" à côté d'un dépôt ouvert déjà identifié se dégrade ainsi en `douteux` : elle porte le plus souvent sur un élément secondaire.

Le verdict se ferme sur cinq valeurs : `declaration absente`, `declaration incoherente`, `regime non identifie`, `declaration a completer`, `declaration conforme`. `regime non identifie` ne se confond jamais avec `declaration absente`, comme `licence inconnue` ne se confond pas avec `autorisation requise` dans check-droits.py : une section qui existe sans dire sous quel régime elle place le matériel n'est pas une section manquante. Consultatif par défaut, `--strict` renvoie 1 hors de `declaration conforme`.

Le rapport se termine par ce que le contrôle ne regarde pas : aucun identifiant n'est résolu, aucun dépôt n'est ouvert, aucune autorisation n'est vérifiée, la politique de la revue cible n'est pas lue, et une déclaration exacte placée hors d'une section titrée échappe à la détection. Régimes, formulations types en français et en anglais, dépôts, principes FAIR et obligations des financements européens dans `skills/produire/references/disponibilite.md`.

Module importable : `reperer_section`, `detecter_regimes`, `identifiants_perennes`, `analyser`, `rapport_texte`.

## emprunts.py

Chaînon amont de check-droits.py : celui-ci dit ce que la licence permet, celui-là dit de quelle figure il s'agit et d'où le fichier vient. `images.py` sort des images anonymes, que rien ne relie à "Figure 3" ni à sa légende ; `emprunts.py` pose ce lien avec une confiance mesurée et refuse de l'affirmer quand la page est ambiguë.

```
python3 emprunts.py inventorier SOURCE.pdf [--out DIR] [--min-bytes N] [--format text|json] [--strict]
python3 emprunts.py localiser --doi 10.xxxx/yyyy [--reseau] [--openalex-cle CLE] [--format text|json] [--strict]
python3 emprunts.py recuperer --doi 10.xxxx/yyyy --out FICHIER.pdf [--reseau] [--format text|json] [--strict]
python3 emprunts.py chainer --doi 10.xxxx/yyyy [--out DIR] [--source FICHIER.pdf] [--figure N] [--modifications TEXTE] [--registre R.json] [--reseau] [--format text|json] [--strict]
```

`inventorier` extrait les images par `images.py`, lit le texte page par page par la cascade de backends de check-presentation.py (déjà partagée avec check-lecture-pdf.py, chargée par chemin plutôt que redite), repère les légendes en tête de ligne (`Figure 3.`, `Fig. 3`, `Figure 3:`, `Tableau 2.`, plus les formes anglaises `Figure`, `Fig.` et `Table`) puis les apparie aux images de la même page. L'appariement est une heuristique de mise en page et chaque fiche porte son niveau : `elevee` (une image et une légende sur la page), `moyenne` (comptes égaux pour plus d'une image, appariement par ordre de lecture), `faible` (comptes divergents), `nulle` (aucune légende disponible, le libellé restant vide). Cinq verdicts fermés : `inventaire apparie`, `inventaire partiel`, `inventaire sans legende`, `inventaire non apparie`, `extraction impossible`. Sans backend de texte, l'inventaire rend les images sans légende et le déclare, comme check-lecture-pdf.py dégrade vers `non mesurable` : il n'invente aucune légende. Les légendes repérées sans image extraite sont listées à part, signe d'une figure vectorielle tracée dans la page.

`localiser` interroge OpenAlex pour l'état d'accès ouvert (`is_oa`, `oa_status`), l'adresse du PDF de la meilleure localisation ouverte et la licence déclarée. État fermé sur quatre valeurs : `acces ouvert confirme`, `acces ouvert sans fichier`, `acces non ouvert`, `localisation inconnue`. Sans `--reseau` ou quand l'index ne répond pas, l'état reste inconnu : une mesure omise, jamais une valeur supposée.

`recuperer` ne télécharge que depuis une localisation déclarée en accès ouvert par l'index. Le script ne contourne aucun contrôle d'accès, ne présente aucun identifiant et ne tente aucune adresse devinée. La garantie est structurelle : la fonction prend la fiche produite par `localiser` plutôt qu'une adresse libre, puis elle lit l'adresse dedans. Les refus sont des chemins de première classe, distincts et testés : `refus source non ouverte` (un article sous abonnement se demande à son éditeur, il ne se contourne pas, voir la procédure de `droits-figures.md`), `refus adresse absente` (source ouverte mais aucune adresse publiée, ouvrir la page de dépôt à la main), `refus localisation inconnue` (une absence d'information ne vaut pas licence de télécharger). Une réponse sans en-tête `%PDF-` n'est pas écrite, pour qu'une page intermédiaire de dépôt ne passe pas pour un article.

`chainer` enchaîne localisation, récupération quand la source est ouverte, inventaire, appel à check-droits.py pour le verdict de licence et la ligne d'attribution, puis écriture de l'entrée dans le registre des figures empruntées. L'entrée porte la source, le DOI, le numéro de figure, la légende d'origine, la licence, le verdict, la mention des modifications et le chemin du fichier récupéré ; elle est validée par `valider_registre` de check-droits.py avant d'être écrite. Un registre existant se complète entrée par entrée. Verdict fermé sur cinq valeurs : `emprunt prepare`, `autorisation a demander`, `licence a etablir`, `source non ouverte`, `chaine incomplete`. Sur `autorisation requise` ou `licence inconnue`, le rapport nomme les deux voies ouvertes : demande écrite à l'éditeur ou redessin depuis les données publiées avec les types de figures.py. `--source` court-circuite la récupération quand le PDF est déjà possédé.

Limite honnête de l'appariement : il lit une mise en page, pas une figure. Une légende posée sur la page voisine de son image, une figure pleine page dont la légende tombe à la page suivante, une image découpée en quatre objets par le producteur du PDF, un backend qui ne dit pas la page d'origine (`pdfimages`) sortent tous de sa portée. Ils se traduisent par une confiance basse ou nulle plutôt que par un appariement affirmé.

## logos.py

Registre de logos, séparé de la charte graphique parce qu'un logo obéit aux règles de l'organisation qui le possède (zone de respiration, taille minimale, usages autorisés, rang protocolaire) et non à celles du document. `valider` contrôle le format du registre, l'existence des fichiers, le ratio déclaré et la résolution effective de chaque logo à la taille où il sera affiché (calcul et seuils repris de `images.py`, source unique pour toute illustration du plugin). `placer` rend le fragment prêt à insérer pour un usage, en HTML ou en LaTeX ; en docx l'insertion réelle passe par `gabarit.py remplir --logo`, qui écrit aussi la relation et le manifeste de types.

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
