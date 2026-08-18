# Style maison en anglais

Transposition du style maison pour un document rédigé en anglais. Le fond des directives strictes ne bouge pas : registre encyclopédique, fait précis ou rien, entrée directe en matière, sources vérifiées. Ce qui bouge est la liste des règles de forme, dont certaines sont calibrées sur le français et deviennent fausses en anglais. Contrôle mécanique correspondant : `scripts/lint-style.py --langue en`, propagé par `scripts/scorecard.py --langue en` à toute la notation. Portée exacte du bilinguisme, script par script : `references/langue.md`.

## Fixer la langue du document

La langue se fixe au cadrage, avec le genre et le plan, avant la première ligne. Elle ne change plus ensuite. Un document dont la langue change en cours de route accumule les deux jeux de règles sans en satisfaire aucun.

Trois façons de la déclarer au linter, par priorité décroissante. L'option `--langue fr|en` passée à l'appel prime sur tout. Le pragme `lint-style:langue=en` placé dans les cinq premières lignes du fichier vient ensuite : c'est le seul canal utilisable par le hook, qui ne passe aucune option fichier par fichier. Sans rien, le français. La détection heuristique existe (`--langue auto`, comptage de mots outils exclusifs à chaque langue) sans être le comportement par défaut, parce que le linter est appelé sans argument par le hook et par `scorecard.py` : une bascule automatique changerait en silence le verdict d'un document déjà validé. Les autres scripts du plugin qui dépendent de la langue (readability.py, numbers.py, traceability.py, citations.py, figures.py, ai-fingerprint.py, check-temporel.py, coherence.py) suivent le même ordre de priorité, soit par délégation directe à la résolution du linter, soit par transmission depuis `scorecard.py` : voir `references/langue.md`.

## Ce qui ne change pas

Valables dans les deux langues et actives en mode anglais : guillemets et apostrophes droits, aucun paramètre de suivi dans une URL, aucun caractère invisible (largeur nulle, contrôle bidirectionnel, caractère de tag, zone à usage privé, espace exotique). Le métadiscours reste banni des deux côtés, avec des tournures visées différentes.

## Ce qui change

Virgule sérielle. Le style maison bannit la virgule d'Oxford en français, où elle n'a pas cours. En anglais la virgule sérielle est recommandée par le Chicago Manual of Style, par l'APA et par la MLA. L'AP Stylebook l'omet sauf risque d'ambiguïté. La signaler produirait un faux positif à chaque énumération : la règle `virgule-oxford` sort donc du mode anglais. Choisir une convention (la sérielle par défaut, celle des trois manuels académiques) puis la tenir sur tout le document.

Pronom indéfini. La règle française vise « on ». L'anglais n'a pas d'équivalent direct : `one` est rare et très formel, le passif ou `we` occupent ce rôle. Aucune règle de substitution n'est ajoutée, la question se traite par la voix.

## Lexique

Le lexique promotionnel banni se transpose terme à terme. La liste anglaise ajoute une couche absente du français : le vocabulaire dont la surreprésentation dans les textes assistés par modèle a été mesurée.

```
critique (registre promotionnel)
  pivotal, crucial, groundbreaking, revolutionary, visionary,
  game-changer, game-changing, cutting-edge, unparalleled,
  rich tapestry, shape the landscape
majeur (vocabulaire en exces mesure)
  delve, delves, delved, delving, intricate, intricacies, intricately,
  realm, realms, meticulous, meticulously, seamless, seamlessly,
  commendable, multifaceted, interplay, garnered, elucidate, unveil,
  landscape (au sens figure)
mineur (verbes tics)
  underscore, showcase, highlight, foster, harness, streamline,
  leverage, navigate (au sens figure), utilize
```

Base factuelle de ces listes. Kobak et al. (2025) mesurent le vocabulaire en excès sur quinze millions de résumés PubMed publiés de 2010 à 2024 : delve, intricate, underscore, realm, meticulous, showcase, seamless, commendable, multifaceted, interplay, garnered, elucidate y figurent. Liang et al. (2024) trouvent la même dérive dans les rapports de relecture ICLR (commendable, meticulous, intricate), absente des revues Nature Portfolio. Trois termes souvent cités ne sont documentés par aucune de ces deux études : `tapestry`, `testament to`, `robust`. Les deux premiers restent bannis au titre du lexique promotionnel maison, décision éditoriale assumée plutôt que mesure. `robust` est laissé libre : terme technique légitime (robust estimator, robust to outliers), le signaler produirait plus de bruit que de signal.

## Le tiret cadratin : deux lectures

Lecture 1, le style maison. Le tiret cadratin est banni en français comme marqueur d'écriture assistée. Par cohérence de voix, il devrait l'être dans toutes les langues.

Lecture 2, la typographie anglaise. Le tiret cadratin est une ponctuation standard de l'anglais, décrite par le Chicago Manual of Style et employée par les revues scientifiques. Aucun manuel n'en limite la densité. L'interdire reviendrait à proscrire une ponctuation correcte, ce qu'aucun relecteur ne demande.

Comportement retenu par défaut : en anglais, le tiret cadratin cesse d'être un constat critique. Une règle de densité le remplace, `tiret-cadratin-densite`, sévérité mineure, déclenchée à partir de trois occurrences et d'une densité supérieure à trois pour mille mots. Motif : le suremploi est un marqueur reconnu (OpenAI a publié en novembre 2025 un correctif portant sur ce point précis), l'emploi mesuré ne l'est pas. Les deux seuils sont une convention maison réglable ; aucune étude évaluée par les pairs ne fixe de densité normale. Le chiffre qui circule provient d'un billet commercial de détecteur. Pour revenir à l'interdiction pure en anglais, déplacer `tiret-cadratin` de la famille `fr` à la famille `commune` dans le dictionnaire `FAMILLE` de `scripts/lint-style.py`, sans autre modification.

## La règle qui compte le plus : significant

`significant` se réserve à la signification statistique. L'employer au sens de « important » est une faute de fond dans un article, pas un écart de style : le lecteur ne peut plus distinguer un résultat testé d'une appréciation d'auteur. Les recommandations ICMJE l'énoncent pour la section Results, en demandant de ne pas employer hors de leur sens technique les termes techniques de la statistique (random, normal, significant, correlations, sample), puis de distinguer en discussion la portée clinique de la portée statistique. Substitutions selon l'ampleur visée : important, substantial, large, marked, considerable.

Le linter signale `significant` et `significantly` en sévérité majeure, sauf quand la ligne porte une marque statistique explicite : `p` suivi d'un opérateur, `p-value`, `statistically`, `confidence interval`, un intervalle de confiance chiffré, un nom de test (ANOVA, t-test, chi-square, Wilcoxon, Mann-Whitney, Kruskal, Bonferroni). Un résultat statistique écrit sans sa marque déclenche donc un constat, ce qui est voulu : la mention du test manque de toute façon.

## Nominalisations, voix passive, modalisateurs

Une nominalisation enferme le verbe dans un substantif : `make an assessment of` pour `assess`, `perform an analysis of` pour `analyse`, `provide a description of` pour `describe`. La phrase s'allonge sans rien gagner. Les Federal Plain Language Guidelines nomment ces formes des verbes cachés. Sévérité mineure, parce que la forme longue reste correcte, seulement plus lourde.

La voix passive n'est pas une faute en anglais scientifique. L'APA 7 (section 4.13) recommande la voix active sauf possiblement en section Methods, où le passif place l'objet de l'étude en tête de phrase. Le linter mesure la part de phrases passives à l'échelle du document et se tait tant qu'elle reste sous la moitié, avec un plancher de six phrases. Un constat sur un texte entièrement composé de méthodes est attendu et ne vaut pas ordre de correction.

`may potentially suggest` empile trois réserves pour n'en produire aucune. Un seul degré par affirmation : `may suggest` ou `suggests`. Les formes visées mécaniquement sont `may/might/could` suivi de `potentially/possibly/perhaps`, la construction réciproque, `seems to possibly` puis la chaîne modal + verbe de suggestion + modal. Cette règle repose sur la pratique éditoriale, non sur une norme citable : ni l'APA, ni l'AMA, ni l'ICMJE ne l'énoncent. Sa justification tient à la redondance sémantique, vérifiable phrase par phrase, pas à une autorité.

## Temps verbaux : hors du linter, volontairement

La convention est stable. Présent pour un fait établi par la littérature et pour ce que montre une figure ou un tableau (`Figure 1 shows the calibration curve`). Passé pour ce qui a été fait et trouvé dans l'étude (`We measured`, `The concentration decreased`). Présent pour la conclusion générale que l'étude soutient.

Cette règle reste dans la référence et n'entre pas dans le code. Un linter voit un temps verbal sans voir ce que la proposition énonce. Le même `was measured` est juste en Methods et fautif dans une phrase qui énonce une constante physique ; le même `shows` est juste pour une figure et fautif pour un résultat propre à l'étude. Une règle mécanique signalerait indistinctement les deux cas ; le bruit produit ferait perdre confiance dans les constats qui, eux, sont sûrs.

## Orthographe britannique contre américaine

Le mélange dans un même document est un défaut réel, le choix ne l'est pas. Le linter signale le mélange, en sévérité majeure, puis nomme les formes trouvées de chaque côté. Il ne recommande aucune des deux variantes : l'instruction aux auteurs de la revue tranche.

Premier piège, le suffixe `-ize`. L'idée qu'il serait américain est fausse : l'orthographe d'Oxford (OED, Oxford University Press, revues Nature) écrit `-ize` en anglais britannique. Une forme en `-ize` ne prouve donc aucune appartenance. Seules les formes en `-ise` de verbes qui admettent `-ize` valent indice britannique (organise, recognise, summarise, optimise, characterise). Les formes en `-lyse` (analyse, paralyse, catalyse) sont britanniques dans tous les usages, orthographe d'Oxford comprise.

Second piège, symétrique. Une famille de verbes s'écrit toujours `-ise`, parce que le `-ise` y appartient à la racine et non au suffixe grec.

```
advertise, advise, apprise, arise, chastise, comprise, compromise,
despise, devise, disguise, enterprise, excise, exercise, franchise,
improvise, incise, merchandise, premise, revise, supervise, surmise,
surprise, televise
```

Aucune de ces formes n'est un indice britannique. Le linter ne s'y trompe jamais, parce qu'il travaille sur une liste fermée de formes et n'emploie aucun motif général en `-ise`, qui les prendrait toutes pour des britannismes. `capsize` fait l'inverse : toujours `-ize`.

Paires réellement variables retenues : colour/color, behaviour/behavior, centre/center, litre/liter, fibre/fiber, defence/defense, licence (nom), practise (verbe), analyse/analyze, modelling/modeling, labelling/labeling, sulphur/sulfur. Sont écartées `meter` (appareil de mesure aussi en anglais britannique), `program` (programme informatique aussi en anglais britannique), `gray` (unité SI de dose absorbée) et `aging`, dont l'appartenance ne tranche rien.

## Pièges du francophone qui écrit en anglais

Espace avant le signe double. Le français demande une espace avant les deux-points, le point-virgule, le point d'exclamation et le point d'interrogation. L'anglais l'interdit : le signe se colle au mot qui le précède. L'erreur est mécaniquement détectable, elle survit au copier-coller depuis un document français et elle saute aux yeux d'un relecteur anglophone. Sévérité majeure.

Pluriels indénombrables. `information`, `research`, `evidence`, `software`, `feedback`, `equipment`, `advice`, `knowledge`, `training` n'ont pas de pluriel en anglais. `informations` et `researches` sont des calques directs du français. Sévérité majeure.

Faux amis retenus par le linter, en sévérité mineure : `actually` (en fait, non actuellement), `eventually` (finalement, non éventuellement), `sensible` (raisonnable, non sensible), `to precise` (n'existe pas comme verbe, dire `to specify`), `control that/if/whether` (dire `check`), `an important number of` (dire `a large number of`), `allow/permit/enable to` suivi d'un verbe (ces verbes exigent un complément d'objet), `in the frame of` (dire `within` ou `as part of`), `assist at` (dire `attend`), `inconvenient` employé comme nom (dire `drawback`).

Faux amis écartés volontairement : `library`, `stage`, `formation`, `delay`, `experience`. Chacun a un emploi anglais légitime et fréquent en contexte scientifique (bibliothèque logicielle, étape d'un procédé, formation géologique, délai de propagation, expérience vécue). Les signaler produirait plus de faux positifs que de corrections.

## Conventions de l'article scientifique en anglais

Personne. `We` est admis par les revues qui suivent l'ICMJE ainsi que par Nature. Le `I` de l'auteur unique reste rare hors sciences humaines. Le passage à la troisième personne (`The authors`) est une convention de revue : la vérifier dans l'instruction aux auteurs plutôt que la décider.

Réserve calibrée. Une affirmation se gradue une seule fois, par le verbe : `suggests`, `indicates`, `shows`, `demonstrates`, dans l'ordre croissant de force. Le degré choisi doit correspondre à ce que la preuve porte. Une réserve absente sur un résultat fragile est aussi fautive qu'une réserve empilée sur un résultat solide. Abstract : temps mixtes assumés, contexte au présent, méthode et résultats au passé, conclusion au présent.

## Ce que le linter ne sait pas voir

- La justesse du temps verbal, faute de savoir ce que la proposition énonce.
- L'accord sujet-verbe, l'article (`a`, `the`, son absence) et la préposition, erreurs les plus fréquentes du francophone, hors de portée d'une expression régulière.
- Le sens figuré d'un mot dont la forme est identique au sens propre. `landscape` est traité par cooccurrence, `robust` ne l'est pas du tout.
- Le calque de structure : phrase française traduite mot à mot, avec sa longueur et son ordre d'origine.
- La cohérence entre l'anglais du texte et le français d'une version parallèle (voir `livrer`, action décliner, résumé bilingue).
- Le registre. Un texte peut ne déclencher aucun constat tout en restant trop familier ou trop pompeux.
- L'instruction aux auteurs de la revue visée, qui prime sur cette référence en cas de conflit.

## Sources

- Recommendations for the Conduct, Reporting, Editing and Publication of Scholarly Work in Medical Journals (Results, Discussion), ICMJE, 2026. https://www.icmje.org/recommendations/browse/manuscript-preparation/preparing-for-submission.html
- Kobak D. et al., Delving into LLM-assisted writing in biomedical publications through excess vocabulary, Science Advances, 2025. https://doi.org/10.1126/sciadv.adt3813
- Liang W. et al., Monitoring AI-Modified Content at Scale, ICML, 2024. https://arxiv.org/abs/2403.07183
- Chicago, MLA, APA, AP: What's the Difference?, CMOS Shop Talk, University of Chicago Press, 2019. https://cmosshoptalk.com/2019/02/19/chicago-mla-apa-ap-whats-the-difference/
- Active and Passive Voice, APA Style, 2026. https://apastyle.apa.org/style-grammar-guidelines/grammar/active-passive-voice
- Federal Plain Language Guidelines (hidden verbs, active voice), plainlanguage.gov, 2011. https://www.plainlanguage.gov/guidelines/
- Oxford spelling, Wikipedia, 2026. https://en.wikipedia.org/wiki/Oxford_spelling
- Verb Tense in Scientific Manuscripts, UNLV Graduate College, 2026. https://www.unlv.edu/sites/default/files/page_files/27/GradCollege-VerbTenseScientificManuscripts.pdf
- OpenAI says it's fixed ChatGPT's em dash problem, TechCrunch, 14 novembre 2025. https://techcrunch.com/2025/11/14/openai-says-its-fixed-chatgpts-em-dash-problem/
