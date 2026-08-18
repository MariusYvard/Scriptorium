# Genres en anglais (ce que la langue change à la structure)

Ce que l'anglais change à la structure attendue d'un écrit, genre par genre. Se charge EN PLUS du playbook du genre (`references/genre-*.md`) quand le document est en anglais, jamais à sa place. Un document en français ne charge pas ce fichier.

Le partage avec `style-anglais.md` est net. Là-bas les règles de forme : lexique, ponctuation, orthographe, faux amis, temps verbaux au niveau de la phrase. Ici la charpente : quelles sections, dans quel ordre, sous quels noms, à quelle longueur, puis le cas où le genre français n'a tout simplement pas de correspondant.

## Pourquoi un fichier et non vingt-six

Trois formes étaient possibles. Un fichier anglais par genre doublait le nombre de playbooks et laissait deux textes dériver l'un de l'autre sans qu'aucun contrôle ne le voie. Une section anglaise dans chacun des vingt-six playbooks obligeait tout lecteur français à charger un contenu anglais qu'il ne lira jamais, contre la règle du routeur qui charge un fichier de référence et lui seul. Un fichier transverse chargé conditionnellement coûte zéro au document français, tient en un seul endroit et suit une convention déjà en place dans le dépôt : `style.md` se charge toujours, `style-anglais.md` s'y ajoute pour un document anglais. Le même couple vaut ici.

Le reproche fait à la forme transverse est la dilution. Il est traité par la mise en page : ce fichier est organisé par genre, pas par thème transversal. Un genre dont la structure ne bouge pas n'a pas de section propre, sa ligne au tableau suffit.

## Trois catégories et leur portée

UNIVERSEL : la structure du playbook français vaut telle quelle. Seuls les noms de section et les conventions de surface changent. Aucune section propre plus bas.

VARIANTE : le genre existe des deux côtés, avec des attentes différentes. Ce que l'anglais attend en plus ou à la place est écrit plus bas.

PROPRE À UNE LANGUE : le genre n'a pas de correspondant. Le fichier nomme l'écrit le plus proche et ce qui l'en sépare. Il ne fabrique pas d'équivalence.

## Classement des vingt-six genres

| Playbook | Catégorie | Nom anglais et point de bascule |
| --- | --- | --- |
| genre-analyse-strategique | UNIVERSEL | strategic analysis. Porter et le SWOT sont d'origine anglophone, la charpente ne bouge pas. |
| genre-article | VARIANTE | op-ed, feature, explainer, blog post. Le français range sous "article" ce que l'anglais sépare par genre de presse. |
| genre-business-plan | VARIANTE | business plan. Le lecteur bancaire français attend le prévisionnel, l'investisseur anglophone attend l'executive summary et la traction. |
| genre-cahier-des-charges | VARIANTE | requirements specification. Contractuel en France, artefact d'ingénierie en anglais, le contrat étant un Statement of Work distinct. |
| genre-cas-clinique | UNIVERSEL | case report. CARE, CONSORT, STROBE et SPIRIT sont rédigés en anglais d'abord. |
| genre-conclusions-contentieux | PROPRE | pas d'équivalent dans les deux sens. Voir plus bas. |
| genre-contrat | VARIANTE | contract. La charpente de common law (Recitals, Definitions, Representations and Warranties, Indemnification, Boilerplate) n'est pas celle d'un contrat de droit civil. |
| genre-demande-financement | VARIANTE | grant proposal. Le playbook est déjà anglophone (NIH, Horizon Europe) ; ce qui change est le critère NSF sans contrepartie européenne. |
| genre-discours | UNIVERSEL | speech. Les sources du playbook sont déjà des writing centers anglophones. |
| genre-dissertation | PROPRE | pas d'équivalent. Le voisin anglais est l'academic essay, bâti sur un thesis statement annoncé. Voir plus bas. |
| genre-documentation-technique | UNIVERSEL | technical documentation. Diátaxis est né en anglais, ses quatre modes portent déjà leurs noms anglais. |
| genre-etude-de-cas | UNIVERSEL | business case study. Méthode Harvard, anglophone d'origine. |
| genre-etude-de-marche | UNIVERSEL | market study. Segmentation, TAM-SAM-SOM et analyse concurrentielle ne dépendent pas de la langue. |
| genre-livre-blanc | UNIVERSEL | white paper. Genre anglais importé en français, y compris son nom. |
| genre-long-rapport | VARIANTE | report. L'anglais sépare l'abstract (informatif, lecteur technique) de l'executive summary (décisionnel, dirigeant) ; le français fond les deux dans "résumé". |
| genre-note-financiere | UNIVERSEL | equity research report, investment memo. Cadre CFA Institute, anglophone. |
| genre-note-juridique | VARIANTE | legal memorandum. L'IRAC est universel, le vocabulaire de procédure ne l'est pas. |
| genre-pitch | UNIVERSEL | pitch. Genre anglophone jusqu'au mot, importé tel quel en français, charpente inchangée. |
| genre-politique-publique | VARIANTE | policy brief. Le policy brief anglophone s'adresse à un décideur hors administration ; la note française s'adresse à une hiérarchie qui décide. |
| genre-post-mortem | UNIVERSEL | postmortem, incident report. Cadre Google SRE, anglophone. |
| genre-poster | UNIVERSEL | conference poster. Ten Simple Rules est en anglais. |
| genre-presentation | VARIANTE | presentation, thesis defense, viva voce. La soutenance française n'a pas le même dispositif que l'examen oral britannique. |
| genre-proposition-commerciale | VARIANTE | proposal, RFP response. Le mémoire technique de la commande publique française est noté sur critères pondérés, la réponse anglophone suit le cadre du client. |
| genre-prospective | UNIVERSEL | foresight report. Wack et le Futures Toolkit britannique sont anglophones. |
| genre-rapport-evaluation | UNIVERSEL | evaluation report. Les critères du CAD de l'OCDE sont publiés en anglais et en français, mêmes définitions. |
| genre-rapport-scientifique | VARIANTE | research paper, thesis. IMRAD est universel, ses variantes de revue ne le sont pas. Voir plus bas. |

Treize universels, onze variantes, deux sans équivalent.

## Rapport scientifique et article IMRAD

### IMRAD n'est pas un gabarit unique

L'ICMJE décrit IMRAD comme le reflet du déroulement d'une recherche, pas comme un format arbitraire. La même page énonce ses limites : une méta-analyse peut réclamer un autre format, un case report, une revue narrative ou un éditorial admettent une structure faible ou absente. Trois variantes réelles, à vérifier dans l'instruction aux auteurs avant d'écrire la première section.

Modèle ICMJE (biomédical). Introduction, Methods, Results, Discussion, sous ces quatre titres. Sous-titres admis à l'intérieur de chaque section.

Modèle IEEE (ingénierie, informatique). Title, Authors, Abstract, Keywords, Introduction, Methodology, Results, Discussion, Conclusion, References, Acknowledgments. La Conclusion y est une section distincte de la Discussion, ce qu'IMRAD ne prévoit pas : la Discussion interprète, la Conclusion énonce la portée et les suites.

Modèle Nature. Ni abstract ni titres IMRAD. L'article ouvre sur un summary paragraph référencé, puis le corps, puis les références, les tableaux, les légendes de figures, puis seulement ensuite la section Methods, qui ne paraît pas dans l'édition imprimée. L'ordre imposé est : titre, auteurs, affiliations, paragraphe en gras, corps, références principales, tableaux, légendes de figures, Methods (avec les déclarations de disponibilité des données et du code, séparées), références de Methods, remerciements, contributions, conflits d'intérêts, informations additionnelles, légendes des Extended Data. Un auteur qui pose ses Methods après l'introduction se fait renvoyer la mise en page.

### Temps verbaux, section par section

La convention est stable et le linter ne la contrôle pas, faute de savoir ce qu'une proposition énonce (raison détaillée dans `style-anglais.md`).

| Section | Temps | Exemple |
| --- | --- | --- |
| Introduction | présent pour l'acquis, present perfect pour l'état du domaine | The mechanism remains unclear. Several studies have reported... |
| Methods | passé | Participants were recruited between March and July. We measured... |
| Results | passé pour ce qui a été trouvé, présent pour ce que montre un objet | The concentration decreased by 12 %. Figure 1 shows the calibration curve. |
| Discussion | présent pour l'interprétation, passé pour rappeler un résultat propre | These findings suggest... We observed no effect in the control group. |
| Abstract | temps mixtes assumés | contexte au présent, méthode et résultats au passé, conclusion au présent |

La faute qui coûte le plus cher est le présent sur un résultat propre à l'étude : il transforme une observation datée en loi générale.

### Le résumé : place, forme, contenu

Trois choses distinguent l'abstract anglais du résumé français. Aucune n'est une question de traduction.

Sa fonction. L'ICMJE rappelle que l'abstract est souvent la seule partie de l'article indexée dans les bases documentaires ainsi que la seule partie lue par une part du lectorat. Il note que son contenu diffère fréquemment de celui du texte. Un abstract qui affirme plus que le corps est une erreur de fond, pas un défaut de vitrine.

Sa forme. L'ICMJE impose l'abstract structuré pour la recherche originale, les revues systématiques et les méta-analyses, tout en précisant que le découpage exact varie d'une revue à l'autre et que certaines en emploient plus d'un. Structuré ou non structuré n'est donc pas un choix d'auteur. L'IEEE demande l'inverse : un paragraphe unique, jusqu'à 250 mots, autonome, sans abréviation, note, référence ni équation. Nature demande un summary paragraph de 200 mots au plus, entièrement référencé et compté dans le texte principal, bâti en quatre mouvements : deux ou trois phrases d'introduction au domaine pour un lecteur extérieur, le contexte et la raison d'être du travail, l'énoncé des conclusions principales introduit par la formule "Here we show" ou son équivalent, deux ou trois phrases de mise en perspective.

Ce qui s'y accroche. L'ICMJE demande que le financement soit listé séparément après l'abstract, que le numéro d'enregistrement d'un essai clinique figure à sa fin, puis que l'identifiant pérenne d'un jeu de données déposé y soit énoncé avec le nom du dépôt. La déclaration de disponibilité elle-même reste en fin de manuscrit, régimes et formulations dans `disponibilite.md` : ce sont deux emplacements différents pour deux objets différents.

### Mots-clés

L'ICMJE ne fixe aucun nombre. La revue le fixe, ainsi que le vocabulaire d'où les tirer. L'IEEE demande 3 à 5 termes, abréviations définies, puis met à disposition l'IEEE Thesaurus pour employer des entrées normalisées plutôt que des formulations libres. Pour une revue indexée dans MEDLINE, les termes MeSH de la National Library of Medicine sont le vocabulaire contrôlé de l'indexation. Un mot-clé qui reprend un mot déjà présent dans le titre gaspille une entrée : l'appariement documentaire couvre déjà le titre.

### Première personne

`style-anglais.md` porte la règle : `we` est admis par les revues qui suivent l'ICMJE, `I` reste rare hors sciences humaines, le passage à `The authors` est une convention de revue. Deux compléments propres au genre. Nature ne se contente pas de tolérer la première personne du pluriel, elle la prescrit dans le summary paragraph par la formule "Here we show". En mathématiques, l'usage du `we` vaut même pour un auteur unique, Krantz le décrit comme la coutume du domaine et lui prête un effet d'association du lecteur au raisonnement. Hors de ces cas documentés, l'instruction aux auteurs tranche. Ce fichier ne substitue pas une règle générale à une lecture de cette instruction.

### Longueurs attendues

Le playbook français donne des pages, l'anglais compte des mots. Le décompte porte des exclusions explicites. L'ICMJE demande un compte de mots du texte hors résumé, remerciements, tableaux, légendes de figures et références, plus un compte séparé pour le résumé. Nature chiffre : environ 2 500 mots de texte pour un article de six pages avec quatre objets graphiques modestes, environ 4 300 mots pour huit pages avec cinq ou six objets, une section Methods qui ne dépasse pas 3 000 mots, jusqu'à 50 références dans le corps, un titre de 75 caractères au plus, des sous-titres de 40 caractères au plus. L'orthographe y suit l'Oxford English Dictionary, ce qui règle la question britannique contre américaine traitée dans `style-anglais.md`.

Le mémoire universitaire de 30 à 60 pages décrit dans `genre-rapport-scientifique.md` n'a pas de correspondant dans le monde des revues. Son correspondant est le mémoire de fin de cycle. Le mot pour le dire est un piège : en usage américain, `dissertation` désigne la thèse de doctorat et `thesis` souvent le mémoire de master, tandis que l'usage britannique inverse fréquemment les deux. Écrire "my dissertation" à un interlocuteur sans préciser le cycle laisse l'ambiguïté entière.

## Revue de littérature

Le contenu de méthode est dans `revue-litterature.md` et `prisma.md`, tous deux appuyés sur des standards rédigés en anglais : la structure ne change pas. Ce qui change est le nom. Or le nom engage.

Le français dit "revue de littérature" pour tout. L'anglais nomme des objets distincts que les revues traitent différemment : `systematic review` (protocole préenregistré, recherche exhaustive et reproductible, sélection à deux lecteurs), `scoping review` (cartographie de l'étendue d'un champ, standard PRISMA-ScR), `narrative review` (synthèse d'auteur, sans prétention d'exhaustivité), `rapid review` (méthode systématique allégée, allègements déclarés), `umbrella review` (revue de revues). Soumettre sous l'étiquette `systematic review` un travail sans protocole ni stratégie de recherche reproductible expose à un rejet éditorial sur ce seul motif. Pour une revue systématique, l'enregistrement du protocole dans PROSPERO avant l'extraction est la pratique attendue et se cite dans les Methods.

## Demande de financement

Ce playbook est déjà anglophone par construction : ses deux modèles, NIH et Horizon Europe, sont des formulaires en anglais. Rédiger cette demande en anglais ne change donc rien à la structure. Deux points s'ajoutent.

Le critère qui n'existe qu'aux États-Unis. La NSF évalue toute proposition sur deux critères de mérite, l'Intellectual Merit et les Broader Impacts. L'absence de la section Broader Impacts est un motif de retour sans évaluation. Ni Horizon Europe ni l'ANR ne portent ce critère sous cette forme : la section Impact d'Horizon Europe couvre la diffusion et l'exploitation des résultats, pas la contribution sociétale au sens de la NSF. Transposer l'une dans l'autre produit un hors sujet.

La page unique du NIH. Le Specific Aims tient en une page. Cette page est une convention de lecture des study sections, pas une contrainte de gabarit à négocier. La proposition européenne, elle, se plie à la limite de pages fixée par l'appel, qui porte sur l'ensemble de la partie B.

## Poster scientifique

Genre universel : la lecture à trois distances, le ratio texte-figures et le flux en colonnes décrits dans `genre-poster.md` ne dépendent pas de la langue. Sa source principale est déjà en anglais. Trois points de surface.

Les intitulés de bandeau se lisent Background ou Introduction, Methods, Results, Conclusions, References, Acknowledgements, souvent Take-home message pour la bande de synthèse que le français appelle "à retenir". Le format physique et l'orientation viennent de l'appel, jamais d'une habitude locale.

Le vrai décalage est en amont. Ce qui décide de l'acceptation n'est pas le poster mais le conference abstract soumis des mois plus tôt, sous une limite de mots stricte fixée par l'appel, souvent structuré. Le poster est ensuite construit à partir de cet abstract déjà accepté, ce qui interdit d'y changer les résultats annoncés.

## Présentation et soutenance

Le support de présentation professionnelle ne change pas d'une langue à l'autre. L'exercice académique, si.

La soutenance française est publique, s'appuie sur un support projeté, se tient devant un jury constitué, puis débouche sur une mention. L'examen doctoral britannique, le viva voce, est un examen oral fermé conduit par deux examinateurs, l'un interne l'autre externe, sans public. Le support projeté n'y est pas le dispositif par défaut : Cambridge indique que les examinateurs préviennent à l'avance si une présentation est demandée et, dans ce cas, au moins deux semaines avant, ce qui suppose qu'elle ne l'est pas toujours. Préparer un deck de trente diapositives pour un viva revient donc à préparer ce qui ne sera peut-être jamais projeté, pendant que l'épreuve réelle est une défense orale du manuscrit, chapitre par chapitre.

Le modèle nord-américain se situe entre les deux : un séminaire public, puis une session fermée avec le comité. Le mot `defense` couvre ces deux moments sans les distinguer.

Conséquence pratique : avant de bâtir un support pour un examen doctoral anglophone, établir de quel dispositif il s'agit. La question se pose au cadrage, avec le genre, elle ne se déduit pas du mot employé.

## Les genres sans équivalent

Le plugin déclare ce qu'il ne sait pas plutôt que d'inventer une correspondance. Deux playbooks tombent dans ce cas.

### Dissertation

La dissertation est un exercice scolaire et universitaire français. Sa marque est le plan en parties annoncé dans l'introduction, dont le plan dialectique (thèse, antithèse, synthèse) est la forme la plus reconnaissable. L'évaluation porte autant sur la construction du plan que sur son contenu. Les deux sources du playbook sont francophones, Montréal et Genève, ce qui n'est pas un hasard de sourcing.

L'anglais n'a pas cet exercice. L'écrit le plus proche est l'`academic essay` ou l'`argumentative essay`. Trois différences interdisent de traiter l'un comme une traduction de l'autre.

L'essay s'organise autour d'un `thesis statement` : une phrase affirmative, placée en fin d'introduction, qui énonce la position que le texte va défendre. La dissertation, elle, pose une problématique, c'est-à-dire une question, puis se garde de répondre avant la conclusion. Annoncer sa réponse dès l'introduction est attendu en anglais et sanctionné en français.

L'essay ne présente pas de plan annoncé. La progression se lit par les `topic sentences` en tête de paragraphe. La phrase française d'annonce du plan, transposée telle quelle, sonne mécanique à une oreille anglophone.

L'essay ne pratique pas la dialectique comme charpente. Les objections se traitent en `counterargument` puis `rebuttal`, subordonnés à la thèse, non comme une deuxième partie qui la contredirait à égalité avant qu'une troisième les concilie.

Quant au commentaire de texte, son voisin anglais est le `close reading` ou l'`explication de texte` (l'anglais universitaire emploie le terme français), mais sans le format codifié de l'épreuve française.

Conduite à tenir : ne pas produire une dissertation en anglais. Demander à l'auteur lequel des deux attendus vaut. Un essay, auquel cas la charpente change et ce playbook ne s'applique plus. Une dissertation française rédigée en anglais pour un jury français, auquel cas le playbook s'applique et le mot `dissertation` sera compris de travers par tout lecteur anglophone (voir plus haut, il y désigne la thèse de doctorat).

### Conclusions et mémoire contentieux

Ce playbook est le cas le plus trompeur du lot. Le constat vaut aveu. La structure qu'il décrit (énoncé des questions soumises, exposé de l'affaire et des faits, résumé de l'argumentation, argumentation, demandes, standard de contrôle en appel) est celle du mémoire d'appel de la procédure américaine, dont ses deux sources sont les guides. Sous des mots français se lit donc un genre anglophone, avec ses intitulés : Questions Presented, Statement of the Case, Summary of Argument, Argument, Prayer for Relief, puis en appel Standard of Review.

Les conclusions de la procédure civile française sont un autre écrit. Elles articulent des prétentions, les moyens de fait et de droit qui les soutiennent, puis se terminent par un dispositif récapitulatif : ce que le juge ne retrouve pas dans ce dispositif, il n'en est pas saisi. Le Standard of Review n'y a aucun correspondant, la Prayer for Relief n'est pas une demande finale rédigée en une phrase mais l'énumération récapitulative qui fixe la saisine.

Conduite à tenir : établir la procédure avant d'ouvrir le playbook, puis la nommer. Pour une procédure américaine ou britannique, la structure décrite s'applique et ses intitulés anglais sont ceux ci-dessus. Pour une procédure française, la structure décrite est un faux ami : elle n'est ni interdite ni suffisante, tandis que le dispositif récapitulatif y devient l'élément décisif. Le playbook ne remplace pas un avocat, il le rappelle déjà. Cette limite pèse ici plus qu'ailleurs.

## Les variantes qui trompent le plus

Quatre pièges hors du champ scientifique, en une ligne chacun, à lire avec le playbook du genre.

Contrat. La charpente de common law enchaîne Recitals, Definitions, Representations and Warranties, Covenants, Conditions, Indemnification, Termination, puis les clauses générales dites Boilerplate ; un contrat de droit civil français n'a ni Representations and Warranties ni Boilerplate au sens technique. La source du playbook (Adams, American Bar Association) décrit la première.

Proposition commerciale. Le mémoire technique de la commande publique française répond à des critères pondérés publiés dans le règlement de consultation, la note se calcule ; la réponse anglophone à un RFP suit le plan du client sans grille publique dans le cas privé. La stratégie décrite par Shipley vise la conviction plutôt que le barème.

Note de politique publique. Le policy brief anglophone s'adresse à un décideur extérieur qu'il faut convaincer, d'où la recommandation unique et assumée ; la note française remonte une hiérarchie qui décide, d'où l'exposé d'options équilibré. Écrire l'un pour l'autre produit soit une note qui semble militer, soit un brief qui semble ne rien recommander.

Cahier des charges. En France l'écrit est contractuel et engage le prestataire ; en anglais la spécification d'exigences est un artefact d'ingénierie, l'engagement contractuel vivant dans un Statement of Work distinct. La norme IEEE/ISO/IEC 29148 citée par le playbook décrit la seconde. Note juridique : l'IRAC vaut dans les deux, seul le vocabulaire de procédure change (holding, dictum, binding precedent, persuasive authority). La hiérarchie des sources d'un système de précédent n'est pas celle d'un système de droit écrit.

## Ce que ce fichier ne dit pas

- Les treize genres classés UNIVERSEL n'ont pas de section propre. Ce n'est pas un oubli : leur structure ne bouge pas. Écrire une section pour le dire l'aurait rendue fausse dès la première nuance ajoutée sans preuve.
- Les conventions de forme (lexique, ponctuation, orthographe, faux amis, voix passive, `significant`) ne sont pas répétées ici. Elles vivent dans `style-anglais.md`, un seul endroit.
- Aucune revue n'est décrite exhaustivement. Trois modèles sont donnés parce qu'ils diffèrent réellement entre eux. L'instruction aux auteurs de la revue visée prime sur tout ce qui précède, y compris sur les chiffres cités.
- Le classement en trois catégories est un jugement éditorial appuyé sur les sources de chaque playbook, pas une mesure. Un genre classé UNIVERSEL peut porter des attentes locales que le plugin ne connaît pas.
- Les langues autres que le français et l'anglais ne sont pas couvertes, ni ici ni dans les scripts.

## Sources

- Recommendations for the Conduct, Reporting, Editing and Publication of Scholarly Work in Medical Journals (General Principles, Abstract, Title Page, Methods, Results), ICMJE, 2026. https://www.icmje.org/recommendations/browse/manuscript-preparation/preparing-for-submission.html
- Formatting guide (Articles, Format of Articles, Text, Methods, References), Nature, 2025. https://www.nature.com/nature/for-authors/formatting-guide
- Structure Your Article (Abstract, Keywords, Conclusion), IEEE Author Center, 2026. https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/create-the-text-of-your-article/structure-your-article/
- Medical Subject Headings (MeSH), National Library of Medicine, consulté 2026. https://www.nlm.nih.gov/mesh/meshhome.html
- The PRISMA 2020 statement, PRISMA Group, 2020. https://www.prisma-statement.org/prisma-2020
- PROSPERO, International Prospective Register of Systematic Reviews, Centre for Reviews and Dissemination, University of York, consulté 2026. https://www.crd.york.ac.uk/prospero/
- Proposal and Award Policies and Procedures Guide, NSF 24-1 (Intellectual Merit et Broader Impacts), U.S. National Science Foundation, 2024. https://www.nsf.gov/policies/pappg
- The oral examination (viva), Cambridge Students, University of Cambridge, consulté 2026. https://www.cambridgestudents.cam.ac.uk/your-course/research-students-pgr/postgraduate-exam-information/writing-submitting-and-examination/phd/oral-examination
- Verb Tense in Scientific Manuscripts, UNLV Graduate College, 2026. https://www.unlv.edu/sites/default/files/page_files/27/GradCollege-VerbTenseScientificManuscripts.pdf
- A Primer of Mathematical Writing, 2e édition (usage du pluriel de modestie en mathématiques), Steven G. Krantz, 2016. https://arxiv.org/abs/1612.04888
- From Memo to Appellate Brief, Writing Center, Georgetown University Law Center, 2004. https://www.law.georgetown.edu/wp-content/uploads/2018/07/From-Memo-to-Appellate-Brief.pdf
- A Manual of Style for Contract Drafting, 5e édition, Kenneth A. Adams, American Bar Association, 2023. https://www.adamsdrafting.com/writing/mscd/
- IEEE/ISO/IEC 29148-2018, Systems and software engineering, requirements engineering, IEEE Standards Association, 2018. https://standards.ieee.org/ieee/29148/6937/

## Voir aussi

`references/style-anglais.md` (règles de forme de l'anglais scientifique), `references/langue.md` (portée du bilinguisme script par script, plus ce qui reste français), `references/disponibilite.md` (déclaration de disponibilité, formulations françaises et anglaises), `references/revue-litterature.md` et `references/prisma.md` (méthode de synthèse), `atelier/references/cadrer.md` (fixation de la langue au brief).
