# Changelog

Toutes les évolutions notables de Scriptorium sont consignées ici.
Format : [Keep a Changelog](https://keepachangelog.com) ; versionnage [SemVer](https://semver.org).

---

## [Unreleased]

<!-- Les changements à venir s'ajoutent ici avant la prochaine version. -->

---

## [0.13.0] - 2026-08-17

Anglais scientifique dans la notation entière, pas seulement dans le linter. Trois lots referment la dette laissée par le mode de langue de la version 0.12.0.

### Added
- Langue traversant la notation : `scorecard.evaluer` accepte `langue` (option `--langue fr|en|auto` en ligne de commande), résout la langue une seule fois par délégation à `lint-style.py` et la redescend dans le linter, la traçabilité, les nombres, la lisibilité, l'empreinte IA et la cohérence. Un pragme `lint-style:langue=en` posé dans le document est ainsi honoré par la notation entière, sans option supplémentaire. Deux clés ajoutées au rapport, `langue` et `mesures_non_faites` (portée par l'axe Lisibilité quand le taux de passif n'est pas mesurable) ; aucune clé existante ne change de forme.
- Nouvelle référence skills/produire/references/langue.md : comment la langue se déclare (option, pragme, détection), ce qui change script par script et ce qui reste délibérément monolingue (rapports et verdicts des scripts, vingt-six playbooks de genre, quatre-vingt-dix références).
- Evals : 523 cas (457 auparavant). Trois nouveaux modules (evals/cas/bilingue-mesures.py, bilingue-raccord.py, bilingue-sorties.py) couvrent les mesures corrigées, le raccordement de la langue à travers scorecard.py et les sorties multilingues des livrables.

### Changed
- Surface : `produire` (style, figure, sourcer) et `controler` (contrôles déterministes) citent l'option `--langue` des scripts concernés et renvoient vers `references/langue.md` ; `atelier` (cadrer) fixe la langue du document au brief, avec le genre et le plan, avant la première ligne, cohérent avec `references/style-anglais.md`.
- readability.py, numbers.py, traceability.py, ai-fingerprint.py, check-temporel.py, coherence.py, citations.py et figures.py gagnent chacun une option `--langue` (`fr|en` pour citations.py et figures.py, `fr|en|auto` pour les six autres), détaillée dans `scripts/README.md`.

### Fixed
- Mesures faussées en anglais : avant ce lot, seul `lint-style.py` portait un mode de langue, les autres scripts restant injoignables depuis la notation ou rendant un résultat faux plutôt qu'une absence de mesure. Mesuré sur un texte anglais dont chaque phrase est au passif : le linter en mode français relevait dix-huit fois la règle du pronom « on », qui frappait en réalité la préposition anglaise homographe, pendant que readability.py annonçait zéro pour cent de passif faute de motif anglais. Parade : readability.py réutilise le motif de passif anglais de lint-style.py et déclare la mesure non faite (`None`) quand elle ne s'applique pas, plutôt que de rendre zéro.
- numbers.py signalait un séparateur décimal mixte sur un nombre anglais bien formé comme 1,234,567.89 : les groupes de milliers anglais bien formés sont désormais retirés avant l'examen.
- traceability.py ne reconnaissait ni `Table` ni `Appendix` en anglais : les deux rejoignent `Figure`, commun aux deux langues, sans changer les clés de sortie que scorecard.py consomme.
- citations.py reliait le dernier auteur par « et » en anglais dans les formats APA et Chicago, alors qu'APA 7 (section 9.8) emploie l'esperluette et que Chicago emploie « and » : les deux formats rendent désormais la forme de leur norme ; les replis de champ manquant deviennent Anonymous, Untitled et n.d.
- figures.py, ai-fingerprint.py, check-temporel.py et coherence.py produisaient leurs étiquettes ou ne lisaient leurs motifs qu'en français. Le diagramme PRISMA en anglais reprend les libellés des gabarits officiels de la déclaration PRISMA 2020 plutôt qu'une traduction : trois bandes de phase (Identification, Screening, Included), la bande Eligibility de la version 2009 ayant disparu.

---

## [0.12.0] - 2026-08-17

Anglais scientifique dans le linter, trois dettes de vérification fermées par une compilation réelle en conteneur TeX Live, un défaut de repli de police que cette compilation a mis au jour, déclaration de disponibilité des données et du code.

### Added
- Mode de langue du linter : lint-style.py analyse en français ou en anglais. La langue se détermine par priorité fixe : l'option `--langue fr|en` d'abord, sinon le pragme `lint-style:langue=en` posé dans les cinq premières lignes du document (seul canal pour le hook, qui ne passe aucune option fichier par fichier), sinon le français par défaut, inchangé. `--langue auto` détecte par comptage de mots outils exclusifs à chaque langue, verdict rendu au-dessus de douze mots reconnus et de 60 % de part pour le gagnant. Quatorze règles propres à l'anglais : lexique promotionnel et lexique d'empreinte IA transposés (mesuré sur quinze millions de résumés PubMed), `significant` réservé à la signification statistique et silencieux devant une valeur de p, un intervalle de confiance ou un nom de test, modalisateurs empilés, espace avant `: ; ! ?` (correcte en français, fautive en anglais), pluriel d'un nom indénombrable, faux amis (`actually`, `control that`, `allow to`), mélange orthographique britannique et américain sans recommander de variante, densité du tiret cadratin (ponctuation légitime en anglais, jugée sur sa fréquence plutôt qu'interdite au premier usage), part de phrases passives. La virgule sérielle ne se déclenche jamais en anglais, où elle est recommandée par Chicago, l'APA et la MLA : la signaler y serait un faux positif à chaque énumération. Nouvelle référence skills/produire/references/style-anglais.md (règle de temps, listes complètes et sources). Le mode français appelle sans changement l'objet `REGLES` d'avant l'ajout de l'anglais, constat par constat, non-régression vérifiée par eval sur l'ensemble des fichiers Markdown du dépôt.
- Vérification en conteneur : nouveau workflow gabarits-latex.yml, qui compile réellement les deux gabarits dans une image TeX Live à partir d'un document pilote. Le pilote décommente verbatim les exemples de figure déjà écrits dans le gabarit de rapport (figure simple, figure composée en sous-figures) et exerce légende, étiquette, renvoi et table des figures, plutôt que de compiler une réécriture qui pourrait réussir là où l'exemple du gabarit échouerait. Nouveau workflow verification.yml, à deux jobs : l'un installe librsvg et prouve la conversion SVG vers PNG par `images.py convertir`, jusque là seulement testée en dégradation faute de backend sur les machines de développement ; l'autre valide les neuf invariants du jeu d'or puis compare le rapport courant à un premier rapport de référence versionné (evals/gold/rapport-reference.json), en mode consultatif. Nouvel outil tools/ci-latex.py (préparation du dossier de compilation, injection de charte, extraction des figures, construction du pilote).
- Disponibilité des données et du code : nouveau script check-disponibilite.py, à contrôler sur le manuscrit source avant soumission. Six régimes fermés (dépôt ouvert, sur demande, embargo, restriction légale, données de tiers, aucune donnée nouvelle), chacun tenu à sa propre preuve : identifiant pérenne (DOI, handle, ARK, SWHID, numéro d'accession, jamais une adresse web ordinaire) pour un dépôt ouvert, date de levée pour un embargo, licence nommée pour du code, détenteur pour des données de tiers, contact avec critères et durée pour un accès sur demande. `regime non identifie` (une section existe sans dire sous quel régime elle place le matériel) ne se confond jamais avec `declaration absente`. Confiance graduée sur la même échelle que check-fuites.py, verdict fermé sur cinq valeurs, consultatif par défaut. Nouvelle référence skills/produire/references/disponibilite.md (formulations types en français et en anglais, dépôts, principes FAIR, obligations des financements européens).
- Evals : 457 cas (347 auparavant). Quatre nouveaux modules (evals/cas/anglais.py, disponibilite.py, polices.py, verification.py).

### Changed
- Surface : `produire` (style) route vers style-anglais.md pour un document en anglais et cite check-disponibilite.py parmi ses scripts déterministes ; `controler` (audit) contrôle la déclaration de disponibilité avant soumission au même titre que les fuites avant envoi ; les playbooks genre-article.md et genre-rapport-scientifique.md placent la déclaration de disponibilité juste avant la bibliographie, aux côtés des déclarations CRediT, financement et usage de l'IA.

### Fixed
- Repli de police silencieux sur cache froid : theme.py interrogeait `fc-list` avec un délai de dix secondes pour savoir si la police demandée par la charte était installée. Sur un cache fontconfig froid (conteneur neuf, machine qui vient d'installer des polices), `fc-list` répond en une douzaine de secondes : le délai expirait, la disponibilité restait déclarée inconnue et le préambule émettait la police demandée telle quelle plutôt que le repli. `xelatex` échouait alors sur une police absente de la distribution, sans que le repli sur Latin Modern ait joué, un défaut trouvé par la compilation réelle ajoutée dans gabarits-latex.yml plutôt que par une lecture du code. Deux parades. La mesure réessaie une fois avec un délai large avant de conclure à une disponibilité inconnue. Le préambule pose surtout la police sous `\IfFontExistsTF`, ce qui déporte la décision dans le document compilé plutôt que dans le script qui l'émet : une police présente sur la machine qui rédige la charte et absente sur celle qui compile ne casse plus rien, le repli sur Latin Modern joue et prévient par `\PackageWarningNoLine`.

---

## [0.11.0] - 2026-08-17

Publication scientifique longue de bout en bout : figures de données auditées, numérotation contrôlée jusqu'aux équations et annexes, gabarit LaTeX qui compile avec des figures, droits de reproduction résolus par DOI et récupération limitée aux sources en accès ouvert.

### Added
- Figures de données : figures.py ajoute six types (courbe, nuage, histogramme, boîte, flux, prisma) aux six figures stratégiques existantes, en SVG et bibliothèque standard seule. Chaque axe porte un titre et une unité, chaque série se distingue par la couleur et par un second canal (forme du marqueur, style de trait), pour rester lisible en impression noir et blanc ou en vision dichromate. L'audit structurel couvre la série vide, l'axe sans unité, l'échelle d'un histogramme tronquée sous zéro, les quartiles hors ordre d'une boîte à moustaches et les jonctions PRISMA qui ne bouclent pas aux trois comptes (identifiées, examinées, incluses). references/prisma.md renvoyait vers `produire figure` pour un schéma que le script ne savait pas encore tracer ; la promesse est honorée.
- Numérotation des objets : traceability.py contrôle la séquence des numéros pour quatre types d'objets (figures, tableaux, équations, annexes) : un numéro dupliqué, un numéro absent de l'intervalle observé, une suite qui ne commence pas à 1, une numérotation d'annexes qui mélange chiffres et lettres. Les équations et les annexes rejoignent les figures et les tableaux dans le contrôle appels-définitions, sur trois notations de légende d'équation (texte, `\tag{n}`, numéro de fin de ligne d'affichage). Les clés ajoutées à `analyser()` s'ajoutent aux clés existantes, `scorecard.py` continue de les lire sans changement.
- Gabarit LaTeX à figures : assets/gabarit-rapport.tex charge désormais graphicx, float, caption et subcaption, dans l'ordre qui préserve les ancres de légende après hyperref et porte `\listoffigures`, `\listoftables` ainsi qu'un exemple commenté de figure simple et de figure composée en sous-figures. Le gabarit ne chargeait jusque là ni de quoi insérer une image ni de quoi légender un flottant : une publication à figures ne compilait pas.
- Illustrations : images.py gagne `catalogue`, qui applique à un dossier d'illustrations déjà produites les mêmes mesures qu'aux médias extraits d'un document (déduplication par empreinte, résolution effective à la largeur d'insertion prévue, verdict fermé) et `convertir`, qui rend un SVG en PNG pour la voie Word par une cascade de backends optionnels (rsvg-convert, inkscape, cairosvg, ImageMagick), aucun n'étant une dépendance du plugin. project.py transporte le glossaire et les objets déjà numérotés dans la passation vers l'agent `redacteur`, pour que la section suivante n'invente ni un synonyme ni un numéro déjà servi.
- Droits de réutilisation : nouveau script check-droits.py, à contrôler avant de reproduire une figure extraite d'une publication tierce. La licence se résout par DOI via Crossref et OpenAlex, derrière un drapeau réseau optionnel, sur quatre verdicts fermés (reutilisable avec attribution, reutilisable sous conditions, autorisation requise, licence inconnue) : le quatrième ne se confond jamais avec le troisième, une absence d'information n'étant ni une interdiction ni une permission. Le script écrit la ligne d'attribution conforme à la licence, valide le registre des figures empruntées et rend une section de crédits. Nouvelle référence skills/produire/references/droits-figures.md.
- Récupération de figures : nouveau script emprunts.py, chaînon amont de check-droits.py. `inventorier` apparie une image extraite d'un PDF à sa légende et à sa page avec une confiance graduée (elevee, moyenne, faible, nulle). `localiser` trouve une version en accès ouvert par DOI via OpenAlex. `recuperer` ne télécharge que depuis une localisation déclarée en accès ouvert par l'index, ne contourne aucun contrôle d'accès et refuse par un message nommé (source non ouverte, adresse absente, localisation inconnue) plutôt que de deviner une adresse ; le cas d'un article sous abonnement renvoie vers la demande d'autorisation à l'éditeur décrite dans droits-figures.md. `chainer` relie localisation, récupération, inventaire et verdict de licence jusqu'à l'écriture du registre.
- Evals : 347 cas (238 auparavant). Cinq nouveaux modules (evals/cas/figures-scientifiques.py, numerotation.py, illustrations.py, droits.py, emprunts.py) couvrent les six lots, avec une fixture PDF régénérable par evals/fixtures/generer-pdf-emprunts.py.

### Changed
- Surface : `produire` (image) charge aussi `references/droits-figures.md` quand la figure vient d'une publication tierce et route vers emprunts.py et check-droits.py en plus d'images.py. `produire` (figure) couvre désormais les figures de données en plus des six figures stratégiques.
- Le calcul de résolution effective (pixels divisés par la largeur en pouces) et ses seuils consultatifs, jusque là écrits dans logos.py, vivent désormais dans images.py et s'importent par chemin, comme gabarit.py importe déjà images.py : une photo de dispositif se mesure avec la même règle qu'un logo.

### Fixed
- Encodage sur console Windows : check-droits.py, emprunts.py, verify-sources.py et citations.py plantaient en UnicodeEncodeError dès qu'un titre renvoyé par un index portait un caractère hors Latin-1 (titre en japonais, tiret long, guillemet courbe), sur une console restée en page de code héritée. Le défaut a été reproduit en test puis corrigé : la sortie standard et la sortie d'erreur se reconfigurent pour dégrader le caractère plutôt que le résultat, sans effet quand la sortie est déjà redirigée vers un fichier ou un pipe.

---

## [0.10.2] - 2026-08-14

Contrôle de ce qu'un livrable trahit de son auteur avant envoi, détection des caractères invisibles. Le parti pris tient en une phrase : ces contrôles inspectent et ne nettoient pas, retirer une trace restant une décision de l'auteur.

### Added
- Audit de fuites : nouveau script check-fuites.py, quatre familles lues avec la bibliothèque standard seule (texte OOXML, diapositives OOXML, ODF, PDF). Il relève les propriétés de document (auteur d'origine, dernière personne à avoir enregistré, organisation, responsable déclaré, titre, sujet, mots-clés), l'historique d'édition (enregistrements successifs, temps d'édition cumulé), les résidus de travail (modifications suivies non acceptées, commentaires nommant leur auteur, texte masqué, notes du présentateur, dossier customXml, liste des collaborateurs), les chemins locaux fuités par les relations du paquet et, pour un PDF, le dictionnaire Info, le bloc XMP, le chiffrement, les fichiers embarqués et les annotations. Chaque constat porte sa confiance (confirme, probable, informatif, douteux), parce qu'un champ rempli et un champ présent ne disent pas la même chose ; le verdict se ferme sur quatre valeurs (fuites confirmees, fuites probables, traces sans identite lisible, rien a signaler). L'option `--auteur` reclasse en douteux un champ qui porte l'auteur déclaré du document, déjà public sur la page de garde, plutôt que de le compter comme une fuite. Consultatif par défaut, code de sortie 1 avec `--strict` dès le premier constat confirmé. Le script n'écrit jamais dans le fichier examiné : supprimer une trace est une décision éditoriale, un outil qui efface d'office tranche à la place de l'auteur et rend le geste invisible. Le rapport se termine par la liste de ce qu'il n'a pas regardé, pour qu'une absence de constat ne se lise pas comme un quitus.
- Mise à jour incrémentale d'un PDF : le même script compte les marqueurs `%%EOF` et les renvois `/Prev` vers une table xref antérieure, puis rend un constat confirmé quand les deux sont réunis. Un outil comme exiftool écrit dans un PDF de façon incrémentale : il ajoute un bloc qui libère l'objet Info et le retire du trailer, mais les octets d'origine restent dans le fichier, verbatim et récupérables. La commande sort en succès, le lecteur n'affiche plus rien et le fichier grossit au lieu de maigrir. Croire une métadonnée supprimée alors qu'elle reste lisible ferme la vérification, ce qui est pire que de la savoir présente. Le cas légitime est décrit plutôt que traité en faute : une signature électronique procède ainsi, mais l'état antérieur du document reste dans le fichier.
- Caractères invisibles : six règles dans lint-style.py. `caractere-invisible` (largeur nulle U+200B, U+2060, U+FEFF, plus le trait d'union conditionnel U+00AD) et `zone-privee` (U+E000 à U+F8FF) en majeur, `controle-bidi` (U+202A à U+202E, U+2066 à U+2069) et `caractere-tag` (U+E0000 à U+E007F) en critique, `espace-exotique` en mineur. Ces caractères survivent au copier-coller, cassent la recherche plein texte, l'appariement d'une citation à son ancre et la lecture d'un diff. `liant-inutile` (majeur) traite à part les liants de largeur nulle U+200C et U+200D : ils portent du sens dans les écritures arabe et indiennes et dans les séquences d'emoji composées, donc ils ne sont relevés qu'entre deux lettres latines, où ils ne servent à rien, plutôt que de lever un faux positif à chaque drapeau et à chaque famille.
- Surface : `controler` (audit) contrôle les fuites avant envoi en plus du fond et de la conformité à un gabarit imposé ; `livrer` (document) ajoute une étape de contrôle qui porte sur le fichier final et jamais sur le Markdown source, puis rappelle qu'un PDF sensible se réexporte depuis la source au lieu de se corriger sur place.
- Evals : 238 cas (211 auparavant). Le nouveau module evals/cas/fuites.py couvre l'audit de fuites et les invisibles, y compris les faux positifs à ne pas lever (emoji composé, drapeau, liant en écriture arabe). Ses fixtures sont régénérables par evals/fixtures/generer-fuites.py : docx piégé, docx sans identité lisible, PDF simple, PDF à mise à jour incrémentale.

---

## [0.10.1] - 2026-08-13

Mise à jour sans désinstallation. Le dépôt adopte la disposition des marketplaces à plusieurs plugins, seule forme observée qui reçoit les versions suivantes chez un utilisateur déjà installé.

### Changed
- Le plugin vit dans le sous-dossier `scriptorium/`, et `.claude-plugin/marketplace.json` reste seul à la racine avec `"source": "./scriptorium"`. Les deux marketplaces qui se mettent à jour correctement sur une installation témoin (celui d'Anthropic et celui que l'application génère pour les dépôts locaux) déclarent tous leurs plugins dans un sous-dossier ; un plugin dont la source est la racine du marketplace restait figé à sa version d'installation. Les 145 fichiers déplacés l'ont été par renommage, l'historique suit.
- Le numéro de version ne vit plus qu'à un seul endroit, `scriptorium/.claude-plugin/plugin.json`. Il était auparavant répété dans `marketplace.json`, où il pouvait diverger en silence. La porte de release vérifie désormais la structure de `marketplace.json` (une entrée nommée scriptorium dont la source est `./scriptorium`) au lieu d'y comparer une version.
- L'artefact `.plugin` s'archive depuis `HEAD:scriptorium` et non depuis la racine, sinon il ne porterait plus son `plugin.json` à la racine de l'archive et serait ininstallable.
- Le README documente la mise à jour en deux commandes, sans désinstallation ni retrait du marketplace.

---

## [0.10.0] - 2026-08-13

Gabarits multi-format (texte OOXML, diapositives OOXML, texte et diapositives ODF, PDF en lecture seule), préflight de lecture PDF, ancrage à trois couches et jeu d'or versionné.

### Added
- Gabarits multi-format : gabarit.py passe de Word seul à quatre familles, détectées par le contenu du fichier puis par son extension (un .docx renommé en .pdf reste traité comme un .docx, un fichier qui commence par `%PDF-` reste un PDF quelle que soit son extension). Texte OOXML (.docx, .dotx, .docm) et diapositives OOXML (.pptx, .potx, .pptm) gardent inventaire, comparaison et remplissage complets ; les diapositives ajoutent les dispositions nommées, les espaces réservés et la taille de diapositive à l'inventaire. Une nouvelle option `--disposition` choisit dans quelle disposition du gabarit le remplissage crée ses diapositives. Texte et diapositives ODF (.odt, .ott, .odp, .otp) gagnent l'inventaire et la comparaison ; leur remplissage reste ouvert. PDF gagne l'inventaire et la comparaison, jamais le remplissage : une page fixe déjà composée se compare, elle ne se remplit pas. Le script le refuse par un message nommé plutôt que par un résultat approximatif. L'inventaire d'un PDF se fait en lecture binaire pure, sans aucun moteur : nombre de pages, format de page nommé (A4, Letter) ou signalé non reconnu, orientation, polices utilisées et proportion incorporée, chiffrement, version PDF. Les marges d'un PDF ne sont pas inventoriées, faute d'être une donnée du fichier plutôt qu'un effet de sa composition. Comparer deux familles différentes est refusé plutôt que rendu à faux. Nouvelle sous-commande `formats` qui liste les familles et leurs extensions.
- Préflight de lecture PDF : nouveau script check-lecture-pdf.py, à lancer avant tout ancrage de citation sur une source PDF. Verdict fermé sur quatre valeurs (lecture fiable, lecture partielle, lecture non fiable, non mesurable), le dernier ne se confondant jamais avec le troisième : l'absence de tout backend PDF dégrade proprement vers non mesurable plutôt que de se faire passer pour un constat d'échec de lecture. Le rapport nomme les pages ancrables et les pages non ancrables. Les contrôles binaires (en-tête %PDF-, marqueur %%EOF, table xref, chiffrement déclaré) restent disponibles sans aucun backend installé. Réutilise la cascade de backends de check-presentation.py par import de chemin plutôt que de la redire.
- Ancrage à trois couches : citations.py qualifie chaque ancre en type fermé (citation, page, structure, horodatage, aucune) et nomme les formes mal formées (page nulle ou négative, plage inversée, citation trop longue, guillemets non fermés) comme un défaut plutôt que de les faire passer pour une ancre valide. Une troisième couche (`auditer_fidelite`, `--auditer-fidelite`) mesure l'écart entre une affirmation et le texte de l'ancre qui la soutient (montée en force modale, chiffre orphelin, généralisation retirée) sans jamais émettre de verdict de fidélité global, ce jugement restant consultatif. La couche 1 (existence de la référence) reste couverte par verify-sources.py, inchangée.
- Jeu d'or versionné : nouveau tools/gold.py et corpus evals/gold/ figé, à manifeste, pour deux tâches mesurées (scorecard, lint-style). Neuf invariants numérotés valident la santé du corpus, le plus important (I6) imposant que chaque étiquette attendue soit recalculable par la vraie fonction de mesure du dépôt plutôt que par une liste recopiée dans le validateur : un jeu d'or dont le validateur réimplémente sa propre logique de notation ne teste que cette réimplémentation. Une porte de régression directionnelle (`comparer`) compare deux rapports polarité par polarité, chaque métrique déclarant son sens ; consultative par défaut, non câblée en intégration continue tant qu'aucun rapport de référence n'est publié.
- Harnais extensible : evals/run-evals.py exécute désormais chaque module de evals/cas/ en plus de son fichier unique, qui reste le socle. Les evals passent de 126 à 211 cas. Nouveaux générateurs de fixtures régénérables evals/fixtures/generer-gabarits-formats.py (pptx, odt, pdf) et evals/fixtures/generer-pdf.py.

### Fixed
- figures.py insérait le dossier scripts/ en tête de sys.path, ce qui faisait masquer le module standard `numbers` par scripts/numbers.py pour tout le processus Python, y compris pour `decimal`, qui en dépend en interne ; l'échec en résultant était ensuite avalé par un `except` large plutôt que signalé. theme.py se charge désormais par chemin explicite, comme gabarit.py charge déjà images.py. Un contrôle des evals échoue bruyamment si la pratique revient.

---

## [0.9.0] - 2026-08-13

Gabarits de document imposés et registre de logos, plus onze mécanismes de rigueur dans les références de revue et de sourcing.

### Added
- Gabarits imposés : nouveau script gabarit.py (bibliothèque standard seule, zipfile et xml.etree). `inventorier` lit la structure d'un .docx ou .dotx fourni par un tiers (styles nommés, hiérarchie de titres, style de corps, marges et format de page, en-têtes et pieds avec leurs champs, polices, protection en édition) dans un JSON déclaratif qui porte sa propre liste de lacunes. `comparer` rend un verdict fermé (conforme, écarts mineurs, écarts majeurs) sur un document produit, par identifiant de style (`w:styleId`) et jamais par le libellé affiché, qu'un Word francisé renomme. `remplir` injecte le contenu dans le gabarit lui-même, dans ses styles existants, ce qui préserve filigrane, numérotation liée et thème de couleurs qu'une régénération perdrait ; l'insertion est chirurgicale sur ancre XML, sans réécriture complète d'un fragment (un aller-retour par ElementTree renommerait les préfixes OOXML). Un gabarit protégé en édition arrête le remplissage au lieu de produire un fichier douteux.
- Logos : nouveau script logos.py et registre séparé `registre-logos.json` (exemple dans assets/), référencé par la charte plutôt que fondu dedans, parce qu'un logo obéit aux règles de l'organisation qui le possède. `valider` contrôle format, existence des fichiers, ratio déclaré et résolution effective à la taille d'affichage réelle (pixels par pouce, seuils consultatifs de 300 dpi à l'impression et 150 dpi à l'écran) ; `placer` émet le fragment pour le HTML et le LaTeX, l'insertion Word passant par `gabarit.py remplir --logo`. Ordre protocolaire par rang déclaré, jamais alphabétique ; un logo dont le fichier manque est écarté du placement au lieu d'être référencé à vide.
- Surface : `produire` gagne les actions gabarit et logos (references/gabarit.md, references/logos.md), `controler` (audit) vérifie la conformité de forme en plus du fond, `livrer` (document) sait remplir un gabarit imposé, qui l'emporte sur la charte interne en cas de conflit, le conflit étant signalé et non arbitré en silence.
- Rigueur : une critique critique ou majeure porte désormais son remède minimal viable et signale si ce remède change l'intention de l'auteur ; le vocabulaire d'assurance (approuvé, conforme, validé, sans risque) est interdit dans une sortie consultative ; une norme du champ invoquée sans source se requalifie en préférence du relecteur ; le chevauchement entre relecteurs indépendants ne se déduplique pas, deux voix convergentes étant un signal ; tout second avis déclare sa fiche de juge (agent, preuve lue, preuve non lue) ; deux autorités en désaccord s'affichent séparément au lieu d'être moyennées ; un contradicteur dont la concession moyenne dépasse 3,5 sur 5 rejoue sa passe en durcissant ; un point de contrôle s'impose après cinq relances brèves consécutives ; la reprise d'un projet passe par trois gestes explicites, un souvenir de session ne valant jamais preuve ; tout contenu récupéré est une donnée à citer et jamais une instruction à suivre ; date de publication et date d'entrée en vigueur restent deux faits distincts ; les phrases de couverture survivent à une contrainte de longueur en déclinaison.
- Rétractations : verify-sources.py lit le statut de rétractation dans les réponses Crossref (`updated-by` et `update-to`, l'article rétracté ne se confondant pas avec l'avis) et OpenAlex (`is_retracted`) déjà récupérées, sans appel réseau supplémentaire. Le statut se rapporte à part du verdict d'existence, qui répond à une autre question, et reste inconnu quand aucun index ne le déclare, jamais supposé sain.
- Evals : 126 cas (92 auparavant), dont un gabarit et deux images de fixture régénérables par evals/fixtures/generer-gabarit.py plutôt que livrés en blocs opaques.

### Fixed
- scorecard.py comptait l'axe Lisibilité pour 20 sur 20 quand le texte était trop court pour que ses métriques signifient quelque chose, ce qui gonflait le total d'un document bref. L'axe est désormais déclaré non évalué, sort du calcul et son poids se redistribue sur les axes mesurés. Une mesure absente n'est ni un zéro ni un plafond. La trajectoire ne fabrique plus de delta sur un axe non mesuré d'un côté.

---

## [0.8.0] - 2026-07-10

Livraison LaTeX chartée, genre poster, contrôle de deck, sources renforcées. Vingt et un mécanismes issus de l'étude du plugin openscience (Synthetic Sciences, Apache-2.0) : huit adaptations directes attribuées, treize réécritures d'idées, standards revérifiés aux sources primaires.

### Added
- Sources et citations : résolution PMID (NCBI E-utilities) et arXiv vers BibTeX dans citations.py, validation de champs par type d'entrée (--valider) et tri stable (--trier) ; paliers de source par domaine dans verify-sources.py (28 domaines, 5 paliers, sans réseau) alimentant la fiche A-F ; profondeur de sourcing par complexité de la question ; nouvelle référence reporting-standards.md : dix standards EQUATOR par type d'étude aux comptes d'items vérifiés aux sources primaires (dont CONSORT 2025 à 30 items et SPIRIT 2025 à 34, versions que la source d'inspiration ignorait ; TRIPOD+AI remplaçant TRIPOD 2015 ; SRQR décrit sans compteur faute de vérification possible).
- Revue et évaluation : diagramme en barres ASCII, forces et faiblesses nommées, poids externes (--poids, avec correction d'un bug de double renormalisation hérité de la source, documentée en commentaire) et seuils par type de document (--seuil-type brouillon 65, rapport 80, publication 85) dans scorecard.py, note d'arrêt anticipé dans la trajectoire (gain sous +3 sans régression) ; comparaison par paires anti-biais de position et taux d'égalité comme diagnostic de grille dans consensus.md ; grille de revue portée à huit dimensions (rigueur méthodologique, portée et transférabilité, honnêteté des limites, en dimensions qualitatives) ; calibration de sévérité du juge dans biais-relecteur.md ; sept critères de qualité d'hypothèse dans cadre-finer.md ; biais cognitifs du chercheur (HARKing, p-hacking Simmons et al. 2011, biais de publication Rosenthal 1979, apophénie, survivant) dans sophismes-causalite.md ; arrêt anticipé dans chemins-defaillance.md.
- Livraison et visuel : sortie LaTeX chartée (assets/gabarit-rapport.tex : page de titre, encadrés sémantiques, macros \pvalue, \CI, \effectsize ; theme.py --format latex émet couleurs et polices depuis la charte ; les deux gabarits compilés en test réel par xelatex) ; genre poster scientifique (genre-poster.md, 26e genre, lecture à trois distances, gabarit assets/gabarit-poster.tex en tikzposter) ; arc narratif en sept temps et minutage par durée dans genre-presentation.md ; nouveau script check-presentation.py (deck PDF : pages par durée, densité de texte, backends optionnels en cascade, consultatif par défaut) ; exigences par destination dans document.md et genre-article.md ; type de figure TAM-SAM-SOM avec audit structurel dans figures.py ; palettes daltonisme-sûres Okabe-Ito et Wong dans theme.py avec avertissement de paires indiscernables en vision dichromate (approximation documentée) ; encodage redondant et grille de raffinement à seuils gradués dans figure.md et charte.md.
- Evals : harnais étendu de nouveaux cas déterministes (validation de champs, tri stable, paliers, garde structurelle de reporting-standards.md, barres et poids du scorecard, arrêt anticipé, TAM-SAM-SOM, préambule LaTeX, palettes, dégradation de check-presentation).

### Changed
- Les routeurs des quatre compétences passent à vingt-six genres et vingt scripts, la voie LaTeX rejoint les formats de sortie, l'audit couvre les decks PDF.

---
## [0.7.0] - 2026-07-09

Intégrité des sources, comité de revue durci, journal de projet. Quarante-sept mécanismes ajoutés, standards cités depuis leurs sources primaires.

### Added
- Intégrité des sources : triangulation multi-index en option réseau (Crossref, OpenAlex, Semantic Scholar, similarité de titre 0,70) avec verdicts gradués par référence (vérifié, plausible, invérifiable, fabriqué) et signaux de contamination ; taxonomie des citations fabriquées ; ancre par citation dans le BibTeX (citation exacte ou localisation, `--exiger-ancres`) ; tags de lacune normalisés `[LACUNE MATERIELLE]` et `[PREUVE FAIBLE]` comptés par traceability.py ; nouveau script check-temporel.py (cinq défaillances chronologiques, consultatif par défaut) ; hiérarchie de preuve à sept niveaux et fiche source A-F ; logique GRADE générale ; chronologie des sources et garde anti-anachronisme ; corpus utilisateur pré-criblé (BibTeX, Zotero) avec traçabilité inclus/exclus. Références : integrite-sources.md, hierarchie-preuve.md, corpus-utilisateur.md, discipline-synthese.md.
- Comité de revue : contrat de notation préenregistré en aveugle pour le consensus (contrat-notation.md), anti-ancrage entre les voix et vérification croisée optionnelle par un second modèle ; discipline de concession du contradicteur (réfutations notées 1-5, jamais deux concessions consécutives, sévérité DA-CRITIQUE, détection du verrouillage de cadrage) ; plancher par axe et décision éditoriale à quatre valeurs dans scorecard.py, mode trajectoire entre deux revues (régression sous -3 = point de contrôle) ; lettre de décision (lettre-decision.md) ; biais et lentilles du relecteur (biais-relecteur.md) ; santé du dialogue anti-complaisance (sante-dialogue.md) ; 28 sophismes en six familles, critères de Bradford Hill et statuts épistémiques (sophismes-causalite.md) ; protocole d'originalité et d'auto-plagiat (plagiat.md) ; statuts fermés par remarque de relecteur dont la limite assumée, registre d'engagements, revue externe réelle (relecteurs.md étendu).
- Atelier : cadre FINER (cadre-finer.md) et boîte socratique (boite-socratique.md) au cadrage ; aiguilleur des demandes (aiguilleur.md) ; douze chemins de défaillance avec récupération (chemins-defaillance.md) ; registre des modes sur le spectre fidélité-originalité (registre-modes.md) ; schémas de passation entre sous-commandes (passations.md) ; renforcement aux transitions et bilan de fin de mission avec auto-audit dans piloter.
- Journal de projet : project.py passe en journal append-only horodaté (frontières à hash de continuité SHA-256, reprise par hash à usage unique, décision en attente reposée, états d'étapes à transitions vérifiées, versions d'artefacts strictement croissantes, tableau de bord `status`, bloc de reproductibilité honnête). Compatibilité de lecture des projet.json antérieurs conservée.
- Production : calibration d'un style personnel sur échantillons, subordonnée au style maison (style.md, mode 4) ; formats Chicago, MLA et IEEE et bascule entre formats dans citations.py ; déclarations CRediT, financement et usage de l'IA avec politiques d'éditeurs vérifiées et datées (credit-divulgation.md) ; résumé bilingue FR/EN aligné (decliner.md) ; vérification visuelle du rendu des figures (figure.md) ; nouvelle sous-commande produire veille (veille.md : requêtes par plateforme, digest, rétractations via le jeu de données Retraction Watch chez Crossref) ; contrat rédacteur-évaluateur par mission (contrat-mission.md, exemple JSON dans assets/).
- Outillage : friction à trois crans sur les passages outre de tools/check.py, journalisés et non supprimables ; glossaire transverse de sévérité (severite.md) ; principes de conception documentés (docs/CONCEPTION.md : mesure avant politique, dégradation gracieuse, jamais de moyenne qui masque un désaccord) ; contrôle de fraîcheur des sources normatives documenté (docs/CI.md) ; quatre fixtures d'evals à double usage (test et exemple de référence) ; harnais étendu d'une trentaine de cas dont un lint de prompt (références citées existantes, frontmatters d'agents, chemins périmés, sections Sources).

### Changed
- Les agents contradicteur, controle-qualite, verificateur-faits et synthese-sources intègrent les nouvelles grilles (concession, lentilles, verdicts gradués, statuts épistémiques, hiérarchie de preuve). Les routeurs des quatre compétences référencent les nouvelles sous-commandes et références transverses.

### Fixed
- Chemins périmés hérités de la réorganisation 0.6.0 dans les agents redacteur (skills/rediger/) et controle-qualite (skills/reviser/, skills/style-maison/), désormais couverts par un cas d'eval dédié.
- Virgules d'Oxford résiduelles dans consensus.md et contredire.md.

---
## [0.6.7] - 2026-06-12

Pitch : ancrage dans une valeur fondamentale et soin de la clôture.

### Added
- genre-pitch.md gagne deux principes. L'ancrage du projet dans une valeur fondamentale universelle (application concrète du recadrage moral, avec un garde-fou éthique contre la valeur plaquée sans preuve). Et le soin de l'ouverture et de la clôture, adossé à l'effet de position sérielle (Murdock, 1962) et à la règle du pic et de la fin (Kahneman et al., 1993). Deux sources primaires ajoutées.

---

## [0.6.6] - 2026-06-12

Scission du genre présentation en deux playbooks distincts.

### Changed
- Le genre présentation est scindé en deux. Présentation et soutenance (genre-presentation.md) est allégé et centré sur la conception de diapositives, le non-verbal, l'interactivité et le trac. Pitch commercial et levée de fonds (genre-pitch.md) regroupe les cadres narratifs, la règle 10/20/30, le traitement des objections, l'humour, les études de cas et le renvoi au module pitch-narratif. Vingt-cinq genres au total.

### Added
- references/genre-pitch.md. Le pitch renvoie au genre présentation pour la délivrance non verbale commune, afin d'éviter la redite.

---

## [0.6.5] - 2026-06-12

Module narratif et cadrage de valeur pour le pitch.

### Added
- references/pitch-narratif.md, boîte à outils rattachée au genre présentation : paradigme narratif (Fisher), sparkline (Duarte) et lecture du keynote iPhone, structures comparées (Freytag, sept points, SCR de Minto et McKinsey, étude de cas), cadrage de valeur (Lakoff, fondations morales de Haidt et recadrage moral de Feinberg et Willer, épisodique contre thématique de FrameWorks, ancrage de Tversky et Kahneman), approche dramaturgique du pitch et éthique du cadrage (rhétorique invitationnelle de Foss et Griffin). Dix-huit sources vérifiées.

### Changed
- Recadrages de rigueur : la base limbique du Golden Circle est présentée comme une vulgarisation et non une neuroscience établie ; la règle dite des neuf minutes est corrigée en règle des dix minutes (Medina, via Gallo) ; les fondations morales sont données avec exactitude (cinq canoniques, la liberté restant une candidate) ; la recherche sur les émotions faciales est située sur des pitchs de financement participatif.

---

## [0.6.4] - 2026-06-12

Volet humour ajouté au playbook pitch, traité comme un levier à risque.

### Added
- Section Humour du genre présentation : mécanique d'écriture (formule attitude-sujet-prémisse-chute, règle de trois, mot-clé en fin de phrase), autodérision et empathie de situation. Traitement rigoureux des risques : downside asymétrique (Bitterly, Brooks et Schweitzer, 2017), biais de genre (Evans et al., Journal of Applied Psychology, 2019), rire contraint sous asymétrie de pouvoir (Harvard Business Review, 2025). Sources ajoutées (Aaker et Bagdonas, Nihill, Klaff, Kerr).

---

## [0.6.3] - 2026-06-12

Playbook pitch enrichi et sourcé.

### Changed
- Le genre présentation devient un playbook de pitch complet (soutenance, vente, levée de fonds) : cadres narratifs (cascade, Golden Circle de Sinek, Show and Tell de Roam), règle 10/20/30 de Kawasaki et répartition temporelle, conception des diapositives, délivrance non verbale (kinésique, proxémique, paraverbal), règle 7-38-55 de Mehrabian recadrée pour en éviter la surinterprétation, interactivité et brise-glaces calibrés par taille d'auditoire, régulation du trac, traitement des objections, études de cas (SécurClés, YouTube, Airbnb).

### Added
- Sources d'autorité sur la persuasion orale : Kawasaki (10/20/30), Sinek (Golden Circle), Mehrabian (7-38-55 et sa portée réelle), Ekman (micro-expressions), Roam (Show and Tell), Bpifrance et CCI.

---

## [0.6.2] - 2026-06-12

Treize genres et six publics supplémentaires, chaque genre adossé à des sources faisant autorité.

### Added
- Treize genres sourcés : demande de financement et proposition de recherche, dissertation et commentaire, business plan, proposition commerciale et réponse à appel d'offres, étude de marché, documentation technique (Diátaxis), rapport d'incident et post-mortem, note d'analyse financière, rapport d'évaluation (critères OCDE/CAD), livre blanc, discours et allocution, conclusions et mémoire contentieux, rédaction de contrat. Vingt-quatre genres au total.
- Six publics : analyste financier, entrepreneur, enseignant, chef de projet, agent public, journaliste. Quatorze publics au total.
- Section Sources dans chaque playbook, adossée à des standards et guides vérifiés (ICMJE, PRISMA 2020, IEEE/ISO/IEC 29148, INCOSE, Google SRE, CFA Institute, OCDE/CAD, IRAC, CARE, CONSORT, STROBE, Diátaxis, entre autres). Profils de discipline portés à quinze, avec leurs sources normatives.
- Conventions de mise en forme pour les treize nouveaux genres.

### Changed
- Description et section publics de produire ouvertes aux vingt-quatre genres et quatorze publics.
- evals portés à 39 cas (présence d'une section Sources dans chaque playbook).

---

## [0.6.1] - 2026-06-12

Cinq genres et cinq publics, README visuel, automatisation de release.

### Added
- Cinq genres : note de politique publique (policy brief), note et consultation juridique (méthode IRAC), cahier des charges et spécification technique, cas clinique et protocole de recherche (CONSORT, PRISMA, STROBE), présentation (soutenance et pitch). Onze genres au total.
- Cinq publics : juriste, professionnel de santé, consultant et dirigeant, communicant et marketing, étudiant. Huit publics au total, avec leurs profils de discipline.
- README refondu : bannière SVG adaptative (thème clair ou sombre), badges, diagramme Mermaid du fonctionnement, exemple concret, tableau des garde-fous déterministes.
- Automatisation de release : workflow `.github/workflows/release.yml` (un tag `vX.Y.Z` vérifie que le tag correspond à `plugin.json` et `marketplace.json` et qu'une section CHANGELOG existe, lance les evals, construit `scriptorium-X.Y.Z.plugin` et publie la Release avec ses notes et l'artefact) et ce `CHANGELOG.md`.

### Changed
- Description et section publics de `produire` ouvertes aux onze genres et huit publics.
- Conventions de mise en forme ajoutées pour les cinq nouveaux genres ; profils de discipline étendus (communication et marketing, présentation et soutenance, travail étudiant).

---

## [0.6.0] - 2026-06-11

Simplification de l'usage, sortie HTML et extraction d'images. Plugin ouvert au chercheur, à l'ingénieur et à l'analyste géopolitique.

### Changed
- Dix-neuf compétences ramenées à quatre à sous-commandes : `atelier` (piloter, cadrer, projet), `produire` (genre, sourcer, revue-litterature, figure, tableau, equation, style, charte, image), `controler` (revue, contredire, consensus, humaniser, audit, relecteurs), `livrer` (document, decliner). Chaque ancienne compétence devient une sous-commande chargée à la demande depuis `references/`, les routeurs `SKILL.md` restent légers.
- Descriptions et exemples ouverts aux trois publics. Profil de discipline analyse géopolitique ajouté à la sous-commande consensus.

### Added
- Sortie HTML autonome pilotée par la charte graphique : `scripts/theme.py --format css` (jetons `:root`, propriétés logiques, mesure fluide, focus visible, feuille d'impression) et une section HTML dans `livrer` (document) alignée sur des standards d'HTML propre (sémantique, jetons, WCAG 2.2). Le HTML sert de source pour un PDF fidèle.
- Extraction et placement d'images : `scripts/images.py` (Office .docx/.pptx/.xlsx et ODF via `zipfile` en pur stdlib ; PDF via PyMuPDF, pdfimages ou pypdf, sinon repli sur le skill pdf ; déduplication par empreinte, lecture des dimensions, signalement EMF/WMF, manifeste JSON) et la sous-commande `produire` (image), où le modèle rédige l'alt et la légende, le script ne juge rien.
- `evals/run-evals.py` porté à 37 cas (theme css, extraction d'images).

---

## [0.5.0] - 2026-06-11

### Added
- Persistance, cohérence d'ensemble et intégration continue éditoriale : mémoire de projet (`project.py`), conformité au plan (`plan-check.py`), empreinte IA (`ai-fingerprint.py`), cohérence interne (`coherence.py`), génération et audit de tableaux (`tables.py`), audit consolidé (`audit-doc.py`), porte d'intégration continue (`tools/check.py`). Compétences memoire-projet, auditer-existant, tableaux, revue-litterature, humaniser. evals 32 cas.

---

## [0.4.0] - 2026-06-11

### Added
- Colonne déterministe étendue : scorecard 0-100 (`scorecard.py`), traçabilité (`traceability.py`), terminologie (`terminology.py`), intégrité numérique (`numbers.py`), citations BibTeX (`citations.py`), diff de versions (`diff-versions.py`). Compétences equations, repondre-relecteurs, decliner, consensus. Agent verificateur-faits. evals 25 cas.

---

## [0.3.0] - 2026-06-11

### Added
- Charte graphique appliquée au texte et aux figures : `scripts/theme.py` (contrôle de contraste WCAG), `figures.py --theme`, compétence charte-graphique, exemple `assets/charte-graphique.exemple.json`. evals 17 cas.

---

## [0.2.0] - 2026-06-10

### Added
- Scripts déterministes (style, sources, lisibilité, figures), hook d'application, compétences finaliser, schematiser, contredire, agent contradicteur, harnais d'évaluation, maturité de distribution.

---

## [0.1.0] - 2026-06-10

### Added
- Six compétences (atelier, cadrer, sourcer, rediger, reviser, style-maison), trois agents, playbooks de genre, boîtes à outils stratégie et prospective, style maison à directives strictes.
