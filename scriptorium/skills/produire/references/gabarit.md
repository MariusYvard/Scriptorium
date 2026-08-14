# Gabarit (respecter une forme imposée par un tiers)

Un tiers impose la forme du document : rapport de stage au modèle de l'école, mémoire au format d'un laboratoire, article à la feuille de style d'une conférence, livrable à la charte d'un client. Cette fiche sert dès que la question n'est plus "comment mettre en forme" mais "comment respecter ce gabarit précis". Le script associé est `scripts/gabarit.py`, trois actions : inventorier, comparer, remplir.

## Trois voies d'entrée, par fiabilité décroissante

a. Un fichier `.docx` ou `.dotx` fourni par le tiers. La voie la plus fiable : le gabarit s'inventorie mécaniquement.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gabarit.py inventorier GABARIT.docx --out gabarit-inventaire.json
```

b. Un gabarit LaTeX (`.cls`, `.sty`). Ce n'est pas une donnée, c'est du code : aucun parseur ne le lit ici. Le mode d'emploi fourni avec le `.cls` se respecte tel quel, sans jamais le modifier. La charte graphique s'y injecte entre les marqueurs prévus, comme `theme.py` le fait déjà pour `assets/gabarit-rapport.tex` (voir `livrer`, action document, section sortie LaTeX).

c. Une consigne écrite (PDF de règlement, page web, courriel). La voie la moins fiable : rien n'est mécanisable. Le modèle lit la consigne et remplit `gabarit-inventaire.json` à la main, sous validation de l'utilisateur pour tout point ambigu (une marge en pouces plutôt qu'en centimètres, un intitulé de style non précisé).

La répartition ne varie pas d'une voie à l'autre : le modèle juge, le code mesure. Même sur un `.docx` inventorié mécaniquement, une consigne annexe non contenue dans le fichier (un courriel qui ajoute une règle) reste du ressort du modèle.

## Comparer : le geste de vérification

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gabarit.py comparer gabarit-inventaire.json DOCUMENT.docx
```

Le verdict est fermé à trois valeurs : conforme, écarts mineurs, écarts majeurs.

Un écart majeur change le rendu imposé : un style appliqué dans le document et inconnu du gabarit, une marge ou une orientation qui diverge de la mesure attendue, un en-tête ou un pied déclaré par le gabarit et absent du document. Un écart mineur signale que le document n'emploie pas le style de corps ou le titre de premier niveau du gabarit, un manque de forme réel mais qui ne change rien à ce qui est rendu. Une entrée de gravité info signale un style déclaré par le gabarit et jamais employé dans le document : c'est normal, un gabarit déclare toujours plus de styles qu'un document n'en utilise.

La comparaison des styles se fait par identifiant (`w:styleId`), jamais par le libellé affiché. Un Word francisé renomme les libellés à l'affichage, jamais les identifiants internes : comparer sur le libellé produirait des faux écarts sur toute machine dans une autre langue.

## Remplir : le geste de production

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gabarit.py remplir gabarit-inventaire.json CONTENU.md --out SORTIE.docx
```

Remplir le gabarit plutôt que régénérer un fichier neuf : un gabarit porte un filigrane, une numérotation liée, un thème de couleurs propres au modèle, qu'une régénération depuis zéro perd. Le remplissage injecte le contenu dans les styles existants du fichier fourni.

Limite honnête de l'implémentation : le contenu s'ajoute à la fin du corps, avant la dernière section. Les paragraphes de remplissage déjà présents dans le gabarit (texte d'exemple, instructions à l'auteur) ne sont pas supprimés automatiquement. Ce nettoyage reste un geste de l'auteur, à faire après le remplissage et avant l'envoi.

Le Markdown accepté est simple. Les titres `#` à `######` se mappent sur les styles de titre du gabarit selon leur niveau, le reste du texte prend le style de corps. Un niveau de titre absent du gabarit retombe sur le style de corps, avec un avertissement affiché : jamais un style inventé pour combler le manque.

## Refus et dégradations

- Un gabarit protégé en édition arrête le remplissage : mieux vaut ne rien produire qu'un fichier douteux qui contourne une restriction posée par le tiers.
- Les polices nommées dans le gabarit ne sont pas vérifiées comme présentes sur la machine qui compile ou affiche le document.
- Une consigne de forme donnée hors du fichier (PDF, page web, courriel) échappe à l'inventaire mécanique, voie (c) ci-dessus.

L'inventaire porte lui-même sa liste de lacunes, dans le champ `lacunes`. La lire à l'utilisateur plutôt que la taire : elle nomme ce que l'inventaire n'a pas pu vérifier (hiérarchie de titres non reconnue, absence d'en-tête ou de pied déclaré, polices non contrôlées sur machine, consigne hors fichier).

## Priorité en cas de conflit

Le gabarit imposé par la destination l'emporte toujours sur la charte graphique interne (voir `produire`, action charte). Un conflit entre les deux (une couleur de la charte qui heurte l'identité visuelle imposée par le gabarit, une police de la charte absente du gabarit officiel) se signale à l'utilisateur au lieu d'être arbitré en silence.

## Enchaînements

- Vers `controler` (audit) pour la vérification avant envoi, une fois le document rempli.
- Vers `livrer` (document) pour la production finale et sa section sortie LaTeX si la voie (b) est en jeu.

## Règles

1. Le modèle juge, le code mesure : jamais l'inverse, sur aucune des trois voies d'entrée.
2. La comparaison se fait par identifiant de style, jamais par libellé affiché.
3. Un gabarit protégé en édition n'est pas rempli de force.
4. Les paragraphes de remplissage du gabarit ne disparaissent pas seuls, le nettoyage reste manuel.
5. Le gabarit imposé prévaut sur la charte graphique interne. Le conflit se nomme, il ne s'arbitre pas en silence.
