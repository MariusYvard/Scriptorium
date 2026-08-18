# Langue du document (portée du bilinguisme)

Le bilinguisme du plugin tient sur deux couches distinctes. La langue d'ANALYSE est celle avec laquelle un script mesure un texte (motifs de style anglais ou français, taux de passif, connecteurs). La langue d'AFFICHAGE est celle dans laquelle le résultat de cette mesure s'imprime au terminal (rapport, message, aide). La version 0.12.0 a ouvert la première, sur `lint-style.py` seul. La version 0.13.0 l'a étendue à la notation entière. La version 0.14.0 ouvre la seconde sur les vingt-sept scripts. Ce fichier documente l'état réel des deux et ce qui reste délibérément hors de leur portée. Il complète `style.md` et `style-anglais.md`, qui portent le versant rédaction, par le versant notation et affichage.

## Comment la langue d'analyse se déclare

Trois canaux, dans un ordre de priorité fixe, défini une fois dans `lint-style.py` (`resoudre_langue`) et repris par délégation ou par transmission dans tous les autres scripts qui en dépendent.

1. Option explicite `--langue fr|en` (ou `--langue auto`, détection heuristique par comptage de mots outils exclusifs à chaque langue, jamais le comportement par défaut).
2. Pragme du document, `lint-style:langue=en` dans les cinq premières lignes du fichier : seul canal que le hook peut utiliser, il n'appelle aucun script avec une option par fichier.
3. Français, à défaut des deux précédents.

`citations.py` sort de cet ordre : un fichier `.bib` est une suite de champs, pas de la prose, la détection heuristique n'y trouverait aucun échantillon fiable. Sa langue se déclare uniquement par `--langue`, jamais par pragme ni détection, défaut français inchangé.

## Exemple

Un document dont les cinq premières lignes portent `<!-- lint-style:langue=en -->` se note ainsi, sans rien passer en plus :

```
python3 scripts/scorecard.py rapport.md --format json
```

Le rapport porte alors `"langue": "en"`, le taux de passif se mesure avec le motif anglais, la règle du pronom « on » ne se déclenche plus sur la préposition anglaise homographe et les figures produites ensuite par `figures.py --langue en` portent des étiquettes anglaises. Passer `--langue fr` à `scorecard.py` forcerait le mode français malgré le pragme, priorité de l'option sur le pragme oblige.

## Ce qui traverse : scorecard.py

`scorecard.evaluer(texte, langue=None)` résout la langue d'analyse une seule fois (délégation à `lint.resoudre_langue`) puis la redescend telle quelle dans le linter, la traçabilité, les nombres, la lisibilité, l'empreinte IA et la cohérence. Un pragme `lint-style:langue=en` posé dans le document est ainsi honoré par la notation entière, sans qu'aucune option supplémentaire soit nécessaire. Deux clés s'ajoutent au rapport, `langue` et `mesures_non_faites` (portée par l'axe Lisibilité quand le taux de passif n'est pas mesurable) ; aucune clé existante ne change de forme ni de sens.

## Script par script (langue d'analyse)

- `lint-style.py` : trois familles de règles (communes aux deux langues, françaises, anglaises). Détail dans `scripts/README.md`.
- `readability.py` : le taux de passif se mesure par le motif français ou par le motif anglais de `lint-style.py`, lu et non recopié. Hors de ces deux langues ou sans phrase mesurable, la mesure se déclare non faite (`None`), jamais zéro. L'indice LIX reste agnostique à la langue par construction ; la bande 30-56 qu'applique `scorecard.py` reste calibrée sur le français faute de calibrage anglais mesuré, limite déclarée plutôt que corrigée à l'estime.
- `numbers.py` : le séparateur décimal mixte ignore d'abord les groupes de milliers anglais bien formés (1,234,567.89) avant de chercher un mélange réel. L'espacement du signe pourcent se contrôle contre la convention de la langue (collé au nombre en anglais, précédé d'une espace en français).
- `traceability.py` : reconnaît `Table` et `Appendix` en plus de `Figure`, commun aux deux langues. Les clés de sortie restent françaises (figures, tableaux, equations, annexes) : seule la forme cherchée dans le texte change, pas le modèle de données que `scorecard.py` consomme.
- `citations.py` : `--langue fr|en`, défaut français, uniquement par cette option. En anglais, APA relie le dernier auteur par l'esperluette et Chicago par « and » ; les replis de champ manquant deviennent Anonymous, Untitled, n.d.
- `figures.py` : `--langue fr|en`, défaut français, pour les étiquettes écrites dans le code de six figures stratégiques et du diagramme PRISMA. Les libellés anglais de PRISMA viennent des gabarits officiels de la déclaration PRISMA 2020, pas d'une traduction. Les clés JSON et les libellés fournis par l'appelant ne sont jamais traduits.
- `ai-fingerprint.py` : quatre signaux sur six dépendent de la langue (connecteurs, cadence ternaire, amplification contrastive, mots outils qui filtrent les bigrammes) ; l'écart-type de longueur de phrase et la répétition d'ouverture ne lisent aucun mot et ne changent pas.
- `check-temporel.py` : quatre détections sur cinq dépendent de la langue (marqueur de temps passé, connecteur causal, langage à péremption, marqueur de version publiée) ; le glossaire de versions fourni par l'utilisateur et le marqueur de preprint restent communs aux deux langues.
- `coherence.py` : seule la liste des promesses dépend de la langue ; le rapprochement de paragraphes quasi dupliqués et la répétition de phrases travaillent sur les mots du texte, quels qu'ils soient.

## La langue d'affichage : une couche séparée

Contrôler un document anglais avec des règles anglaises est une chose ; lire le résultat en anglais en est une autre. Avant la version 0.14.0, un seul canal était bilingue : la sortie JSON (elle ne fait que reporter ce qui a été mesuré). Le rapport texte, lui, restait français quelle que soit la langue analysée, ce qu'une ancienne version de ce fichier présentait à tort comme une limite durable, en l'attribuant à six scripts seulement.

Les vingt-sept scripts déterministes importent désormais `scripts/libelles.py`, une clé plate à espace de noms par script (`scorecard.entete`, `traceability.titre`), chaque clé portant le couple français-anglais et un formatage à paramètres nommés (`{total}`, pas un format positionnel : l'ordre des mots change d'une langue à l'autre). 812 clés. Trois fonctions : `t(cle, langue, **params)` rend un libellé et retombe sur le français en le déclarant si la clé manque dans la langue demandée ; `valeur(espace, machine, langue)` traduit l'affichage d'une valeur machine déjà fixée ailleurs, sans jamais la modifier ; `motif(motif_fr, langue)` relit un motif de mesure non faite porté par les données. Détail du module dans `scripts/README.md`.

Chaque script porte une option `--langue-affichage fr|en`, résolue une seule fois par `resoudre_affichage(demandee, langue_analyse)` : l'option explicite prime, sinon la langue déjà résolue s'il y en a une, sinon le français. Deux familles se distinguent par ce second terme.

Treize scripts mesurent un document et prennent par défaut sa langue d'analyse déjà résolue : `lint-style.py`, `scorecard.py`, `readability.py`, `traceability.py`, `audit-doc.py`, `ai-fingerprint.py`, `check-disponibilite.py`, `check-temporel.py`, `coherence.py`, `numbers.py`, `plan-check.py`, `terminology.py`, `diff-versions.py` (défaut la langue de la nouvelle version, par son pragme). Un pragme `lint-style:langue=en` posé dans le fichier suffit donc à obtenir un rapport entièrement anglais depuis n'importe lequel d'entre eux, sans option supplémentaire.

Treize scripts portent sur un objet qui ne peut matériellement pas porter de pragme et prennent par défaut le français, décrit dans leur propre aide : `verify-sources.py` (URL et DOI, agnostiques à toute langue), `check-droits.py` (un registre JSON), `check-fuites.py` (un binaire bureautique), `check-lecture-pdf.py` et `check-presentation.py` (un PDF), `citations.py` (un fichier `.bib`), `emprunts.py` (un PDF ou un DOI), `gabarit.py` (un gabarit bureautique), `images.py` (un dossier d'images), `logos.py` (un registre de logos), `project.py` (un projet, qui n'est pas un manuscrit), `theme.py` (une charte), `tables.py` (un CSV ou un JSON en génération, un document en audit mais une mesure indépendante de sa langue).

`figures.py` tient les deux langues sans les confondre, à part de ces deux familles : `--langue` est la langue de DESSIN, celle des étiquettes tracées dans le SVG livré au lecteur final. `--langue-affichage` est celle du regard critique de `--audit` et des messages de la commande au terminal ; sans l'option, elle suit `--langue` plutôt qu'une langue d'analyse, faute de document à analyser. Le SVG produit ne dépend jamais de `--langue-affichage`.

## Ce qui reste monolingue quoi qu'il arrive

La valeur machine ne change jamais de langue, dans aucune des deux couches. Les verdicts fermés (`conforme`, `ecarts majeurs`, `licence inconnue`, `autorisation requise`, `lecture fiable`, `Pret`, `A reviser`, `A refondre`), les décisions éditoriales, les noms de règle du linter, les sévérités, les noms des cinq axes du scorecard (Style, Sources, Tracabilite, Terminologie et nombres, Lisibilite) et toutes les clés JSON restent les chaînes françaises actuelles dans les deux langues d'affichage. La raison n'est pas la paresse : `emprunts.py` branche sur les verdicts de `check-droits.py`, des modules de `evals/cas/` les comparent littéralement et `tools/gold.py` les confronte aux étiquettes gelées de `evals/gold/*/manifeste.json`. Les traduire casserait la chaîne et le jeu d'or. La sortie `--format json` est donc française quelle que soit la langue d'affichage demandée.

Ce qui est ÉCRIT sur le disque n'est pas de l'affichage, même quand un script porte `--langue-affichage`. Le journal de mission de `projet.json`, le catalogue d'`images.py` et l'inventaire de `gabarit.py` gardent leurs chaînes françaises quelle que soit l'option passée à la commande qui les a produits : ce sont des données relues plus tard, par une autre commande ou une autre session, non un rapport lu une fois puis jeté. Le cas le plus contraignant est le journal de `projet.json` : le hash de continuité d'une frontière de projet est calculé sur la sérialisation de ce journal, si son contenu changeait de langue selon l'option de la commande qui l'a écrit, le hash changerait de valeur sans qu'aucune décision n'ait bougé, un projet commencé en français puis repris en anglais se contredirait alors à la relecture.

## Playbooks de genre et fichier transverse

Les vingt-six playbooks de genre (`skills/produire/references/genre-*.md`) sont écrits en français et le restent : aucun n'est traduit. C'est délibéré, pas une lacune à combler : ces fichiers sont lus par le modèle au moment de rédiger, jamais par l'utilisateur final : une méthode en français produit aussi bien un texte anglais qu'un texte français, la langue de la méthode n'étant pas celle du livrable. Un utilisateur qui commande un document en anglais fait donc rédiger un texte anglais à partir d'une méthode française : ce n'est ni une contradiction ni un défaut d'affichage, les deux langues n'ayant pas le même lecteur. Ce principe vaut plus largement : sur les 92 références du plugin (`skills/*/references/*.md`), une seule sort de ce monolinguisme, décrite plus bas.

Un audit des vingt-six playbooks a montré que leur structure n'est pas toujours portable d'une langue à l'autre : la dissertation est un exercice français sans correspondant anglais, `genre-conclusions-contentieux.md` décrit en réalité un mémoire d'appel de procédure américaine sous des mots français, l'article IMRAD change de charpente selon la revue visée. `references/genres-anglais.md` porte ce constat, en français comme les autres références : le classement des vingt-six genres en treize UNIVERSEL (la structure du playbook vaut telle quelle), onze VARIANTE (le genre existe des deux côtés avec des attentes différentes) et deux PROPRE À UNE LANGUE (dissertation, conclusions et mémoire contentieux, sans équivalent transposable), puis ce que l'anglais change à la structure attendue pour les genres scientifiques (temps verbaux par section, forme du résumé, mots-clés, première personne, longueurs). Les deux genres sans équivalent le disent aussi dans leur propre playbook, pas seulement dans le fichier transverse : un auteur qui charge `genre-dissertation.md` sans charger `genres-anglais.md` lit quand même l'absence de correspondant.

Ce fichier se charge EN PLUS du playbook du genre, jamais à sa place, seulement pour un document anglais : un document français ne le charge pas et ne paie donc rien pour son existence. La règle du routeur qui charge un fichier de référence et lui seul est ainsi tenue, sur le modèle déjà en place du couple `style.md` et `style-anglais.md`.

## Le hook et le pragme

Le hook qui contrôle un document après chaque écriture appelle `lint-style.py` sans argument de langue : le pragme du document est donc son seul levier pour la langue d'analyse, l'option `--langue` restant réservée à un appel manuel ou à `scorecard.py` lancé depuis une compétence. La langue d'affichage suit la même contrainte côté hook : sans pragme, le rapport du hook reste français. C'est pourquoi `atelier` (cadrer) fixe la langue au brief, avant la première ligne : un pragme posé dès le début se propage à tout contrôle automatique qui suit, un pragme ajouté après coup ne rattrape que les contrôles lancés depuis ce moment.

## Ce qu'il ne faut pas en conclure

Un `--langue en` sur `scorecard.py` note un texte anglais avec les règles anglaises ; un `--langue-affichage en` en imprime le rapport en anglais. Aucun des deux ne traduit le document, n'en génère une version anglaise ni ne contrôle sa grammaire anglaise : accord sujet-verbe, article, préposition restent hors de portée d'une expression régulière, comme le rappelle `style-anglais.md`. La langue déclarée est un paramètre de mesure et d'affichage, pas une garantie de qualité rédactionnelle.

## Voir aussi

`scripts/README.md` (section `libelles.py`, détail des familles de règles de `lint-style.py`, option `--langue-affichage` par script), `references/style-anglais.md` (règles de forme propres à l'anglais scientifique, sources citées), `references/genres-anglais.md` (structure attendue par genre en anglais, classement des vingt-six playbooks), `references/style.md` (hiérarchie d'application du style, mode 1), `atelier/references/cadrer.md` (fixation de la langue au brief).
