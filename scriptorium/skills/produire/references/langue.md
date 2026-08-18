# Langue du document (portée du bilinguisme)

Ce que la langue change dans les scripts déterministes du plugin et ce qui reste écrit en français quelle que soit la langue du document analysé. Complète `style.md` et `style-anglais.md`, qui portent le versant rédaction, par le versant notation et livrables.

## Comment la langue se déclare

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

## Pourquoi ce lot

Avant cette version, seul `lint-style.py` portait un mode de langue. Les autres scripts existaient déjà en anglais dans leurs motifs internes mais restaient injoignables depuis la notation et certaines mesures rendaient un résultat faux sur un texte anglais plutôt qu'une absence de mesure. Exemple mesuré avant correction, sur un texte anglais dont chaque phrase est au passif : le linter en mode français relevait dix-huit fois la règle du pronom « on », qui frappait en réalité la préposition anglaise « on », pendant que la lisibilité annonçait zéro pour cent de passif faute de motif anglais. Le score s'en trouvait faux dans les deux sens à la fois.

## Ce qui traverse : scorecard.py

`scorecard.evaluer(texte, langue=None)` résout la langue une seule fois (délégation à `lint.resoudre_langue`) puis la redescend telle quelle dans le linter, la traçabilité, les nombres, la lisibilité, l'empreinte IA et la cohérence. Un pragme `lint-style:langue=en` posé dans le document est ainsi honoré par la notation entière, sans qu'aucune option supplémentaire soit nécessaire. Deux clés s'ajoutent au rapport, `langue` et `mesures_non_faites` (portée par l'axe Lisibilité quand le taux de passif n'est pas mesurable) ; aucune clé existante ne change de forme ni de sens.

## Script par script

- `lint-style.py` : trois familles de règles (communes aux deux langues, françaises, anglaises). Détail dans `scripts/README.md`.
- `readability.py` : le taux de passif se mesure par le motif français ou par le motif anglais de `lint-style.py`, lu et non recopié. Hors de ces deux langues ou sans phrase mesurable, la mesure se déclare non faite (`None`), jamais zéro. L'indice LIX reste agnostique à la langue par construction ; la bande 30-56 qu'applique `scorecard.py` reste calibrée sur le français faute de calibrage anglais mesuré, limite déclarée plutôt que corrigée à l'estime.
- `numbers.py` : le séparateur décimal mixte ignore d'abord les groupes de milliers anglais bien formés (1,234,567.89) avant de chercher un mélange réel. L'espacement du signe pourcent se contrôle contre la convention de la langue (collé au nombre en anglais, précédé d'une espace en français).
- `traceability.py` : reconnaît `Table` et `Appendix` en plus de `Figure`, commun aux deux langues. Les clés de sortie restent françaises (figures, tableaux, equations, annexes) : seule la forme cherchée dans le texte change, pas le modèle de données que `scorecard.py` consomme.
- `citations.py` : `--langue fr|en`, défaut français. En anglais, APA relie le dernier auteur par l'esperluette et Chicago par « and » ; les replis de champ manquant deviennent Anonymous, Untitled, n.d.
- `figures.py` : `--langue fr|en`, défaut français, pour les étiquettes écrites dans le code de six figures stratégiques et du diagramme PRISMA. Les libellés anglais de PRISMA viennent des gabarits officiels de la déclaration PRISMA 2020, pas d'une traduction : trois bandes de phase seulement (Identification, Screening, Included), la bande Eligibility de la version 2009 a disparu. Les clés JSON et les libellés fournis par l'appelant ne sont jamais traduits. Le regard critique de `--audit` reste en français dans les deux langues : diagnostic pour l'auteur, pas une pièce du livrable.
- `ai-fingerprint.py` : quatre signaux sur six dépendent de la langue (connecteurs, cadence ternaire, amplification contrastive, mots outils qui filtrent les bigrammes) ; l'écart-type de longueur de phrase et la répétition d'ouverture ne lisent aucun mot et ne changent pas.
- `check-temporel.py` : quatre détections sur cinq dépendent de la langue (marqueur de temps passé, connecteur causal, langage à péremption, marqueur de version publiée) ; le glossaire de versions fourni par l'utilisateur et le marqueur de preprint restent communs aux deux langues.
- `coherence.py` : seule la liste des promesses dépend de la langue ; le rapprochement de paragraphes quasi dupliqués et la répétition de phrases travaillent sur les mots du texte, quels qu'ils soient.

## Ce qui reste monolingue

Le contrôle mécanique change de langue, ses comptes rendus non. Chaque script imprime ses libellés, ses verdicts et ses messages d'erreur en français, y compris sur un texte analysé en anglais : « Scorecard », « Tracabilite », « Empreinte IA », les noms des cinq axes du scorecard (Style, Sources, Tracabilite, Terminologie et nombres, Lisibilite) et les clés internes de `analyser()`. La langue déclarée figure dans le rapport (clé `langue` ou ligne « langue analysee » en mode texte) ; le rapport lui-même ne change pas de langue.

Les vingt-six playbooks de genre (`skills/produire/references/genre-*.md`) et les quatre-vingt-dix références du plugin sont écrits en français et le restent : ce lot ne les traduit pas. Un utilisateur qui rédige un document en anglais lit une méthode en français pour produire un texte anglais, exactement comme avant ce lot. Seule la sortie mesurable des scripts (constats, scores, étiquettes de figures, bibliographie formatée) suit la langue du document.

## Le hook et le pragme

Le hook qui contrôle un document après chaque écriture appelle `lint-style.py` sans argument de langue : le pragme du document est donc son seul levier, l'option `--langue` restant réservée à un appel manuel ou à `scorecard.py` lancé depuis une compétence. C'est pourquoi `cadrer.md` fixe la langue au brief, avant la première ligne : un pragme posé dès le début se propage à tout contrôle automatique qui suit, un pragme ajouté après coup ne rattrape que les contrôles lancés depuis ce moment.

## Ce qu'il ne faut pas en conclure

Un `--langue en` sur `scorecard.py` note un texte anglais avec les règles anglaises. Il ne traduit rien, ne génère aucun texte en anglais et ne contrôle pas la grammaire anglaise : accord sujet-verbe, article, préposition restent hors de portée d'une expression régulière, comme le rappelle `style-anglais.md`. La langue déclarée est un paramètre de mesure, pas une garantie de qualité rédactionnelle.

## Voir aussi

`references/style-anglais.md` (règles de forme propres à l'anglais scientifique, sources citées), `references/style.md` (hiérarchie d'application du style, mode 1), `atelier/references/cadrer.md` (fixation de la langue au brief), `scripts/README.md` (détail des familles de règles de `lint-style.py`).
