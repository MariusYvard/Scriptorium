# Déclaration de disponibilité des données et du code

Une déclaration de disponibilité dit où se trouvent les données et le code qui soutiennent les résultats publiés, à quelles conditions un tiers y accède, puis ce qui ferme l'accès quand il est fermé. Les revues la réclament, les financeurs publics en font une obligation contractuelle. `credit-divulgation.md` couvre les trois autres déclarations de fin de manuscrit (contribution CRediT, financement, usage de l'IA) et renvoie ici pour celle-ci.

## 1. Ce que la déclaration engage

Elle énonce un fait vérifiable, pas une intention : un lecteur suit l'adresse donnée, un évaluateur demande le jeu de données, un éditeur contrôle que l'identifiant résout. Une déclaration qui promet un accès inexistant est une affirmation fausse dans un article, du même ordre qu'un chiffre erroné.

L'écart entre la promesse et le fait est mesuré. Gabelica, Bojcic et Puljak (2022) ont analysé 3 556 articles publiés en janvier 2019 dans 333 revues en accès ouvert de BioMed Central, dont 3 416 portaient une déclaration de disponibilité. La catégorie la plus fréquente (42 %) annonçait des données accessibles sur demande motivée. Parmi les 1 792 manuscrits dont la déclaration disait les auteurs prêts à partager, 1 669 (93 %) n'ont pas répondu à la demande ou l'ont refusée ; 254 (14 %) ont répondu. Sur les 1 792, 123 (6,8 %) ont fourni les données demandées.

## 2. Emplacement dans le manuscrit

Section propre en fin de manuscrit, après la discussion et avant la bibliographie, distincte de la déclaration de financement comme de celle de conflit d'intérêts. Intitulés courants : "Disponibilité des données", "Data availability statement", "Data and code availability". Un article qui partage aussi du code porte deux paragraphes séparés sous ce titre. Pour un texte IMRAD, la place est fixée par `genre-rapport-scientifique.md`. La politique de la revue cible prime sur cet emplacement générique.

## 3. Les six régimes de disponibilité

Un régime par catégorie de matériel. Un article peut en combiner deux (données ouvertes, code sur demande) à condition de nommer ce que chaque régime couvre.

| Régime | Ce qu'il oblige à écrire |
| --- | --- |
| Dépôt public ouvert | nom du dépôt, identifiant pérenne, licence |
| Sur demande motivée | qui décide, sur quels critères, par quel mécanisme, jusqu'à quand |
| Embargo | date de levée, motif, dépôt visé |
| Non partageable | motif précis, ce qui reste accessible malgré la fermeture |
| Données de tiers | détenteur, procédure d'accès auprès de lui, interdiction de rediffuser |
| Aucune donnée nouvelle | le déclarer, avec renvoi aux sources déjà publiées |

Formulations types à adapter, jamais à recopier telles quelles. Les lignes marquées EN sont rédigées en anglais pour un manuscrit anglais : les règles de forme françaises ne leur sont pas appliquées.

```
1. DÉPÔT PUBLIC OUVERT
FR  Les données qui soutiennent les résultats de cette étude sont déposées dans
    [DÉPÔT], identifiant [DOI], sous licence [LICENCE].
EN  The data supporting the findings of this study are openly available in
    [REPOSITORY] at [DOI], under a [LICENCE] licence.

2. SUR DEMANDE MOTIVÉE
FR  Les données sont conservées par [ÉTABLISSEMENT] et communiquées par
    [CONTACT INSTITUTIONNEL] sur demande motivée, pour [ANALYSES ADMISES],
    après signature de [ACCORD], pendant [DURÉE] à compter de la publication.
EN  The data are held by [INSTITUTION] and are available from [INSTITUTIONAL
    CONTACT] upon reasonable request, for [PERMITTED ANALYSES], subject to
    [AGREEMENT], for [PERIOD] after publication.

3. EMBARGO
FR  Les données sont déposées dans [DÉPÔT], identifiant [DOI], sous embargo
    jusqu'au [AAAA-MM-JJ], date fixée par [MOTIF].
EN  The data are deposited in [REPOSITORY] at [DOI] and remain under embargo
    until [YYYY-MM-DD], a date set by [REASON].

4. NON PARTAGEABLE POUR RAISON LÉGALE
FR  Les données ne peuvent pas être partagées : elles portent [MOTIF : données
    à caractère personnel, secret industriel, localisation d'une espèce
    protégée, localisation d'un bien patrimonial]. [CE QUI RESTE ACCESSIBLE]
    est déposé dans [DÉPÔT], identifiant [DOI].
EN  The data cannot be shared because they contain [REASON]. [WHAT REMAINS
    AVAILABLE] is deposited in [REPOSITORY] at [DOI].

5. DONNÉES DE TIERS
FR  Les données proviennent de [DÉTENTEUR] et ont été utilisées sous licence
    pour cette étude. Les auteurs ne sont pas autorisés à les rediffuser. Elles
    s'obtiennent auprès de [DÉTENTEUR] selon la procédure décrite en [ADRESSE].
EN  The data were obtained from [HOLDER] under licence for this study. The
    authors are not permitted to redistribute them. They are available from
    [HOLDER] following the procedure described at [ADDRESS].

6. AUCUNE DONNÉE NOUVELLE
FR  Cette étude n'a produit aucune donnée nouvelle. Les données analysées sont
    celles de [SOURCES], accessibles sous [IDENTIFIANTS].
EN  No new data were generated in this study. The analysed data are those of
    [SOURCES], available at [IDENTIFIERS].
```

## 4. Le cas de "disponibles sur demande"

C'est la formule la moins suivie d'effet (section 1). Elle reste acceptable quand elle cesse d'être une formule, c'est-à-dire quand elle porte les éléments exigés par l'ICMJE depuis le 1er juillet 2018 des manuscrits d'essais cliniques soumis à ses revues : quelles données précisément, quels documents liés (protocole, plan d'analyse statistique), à partir de quand et pour combien de temps, selon quels critères d'accès (avec qui, pour quels types d'analyses, par quel mécanisme). L'ICMJE écarte explicitement la réponse "indécis". Un essai qui commence à recruter à partir du 1er janvier 2019 porte en plus un plan de partage dans son enregistrement.

Deux règles pratiques complètent ces éléments : nommer un contact institutionnel plutôt qu'une adresse personnelle, qui expire avec le contrat de son titulaire ; déposer dès la publication ce qui ne pose aucune difficulté (code, dictionnaire des variables, protocole), pour que la demande ne porte que sur ce qui la justifie.

## 5. Le code

Le code obéit à des règles voisines de celles des données, avec trois exigences propres. Licence explicite : un dépôt sans fichier de licence reste sous le droit d'auteur par défaut, donc lisible et non réutilisable. Version figée par un identifiant : une adresse de dépôt de développement désigne un état mouvant, puisqu'un dépôt se renomme, passe en privé, se réécrit, se supprime ; la déclaration cite la version exacte employée pour les résultats publiés (étiquette de version avec DOI d'archive, à défaut empreinte de commit). Dépendances déclarées : versions des bibliothèques, fichier de verrouillage, version du langage, système d'exploitation quand il compte, faute de quoi le code ne rejoue pas.

```
FR  Le code d'analyse est archivé dans [DÉPÔT], identifiant [DOI], version
    [ÉTIQUETTE], sous licence [LICENCE]. Le développement se poursuit à
    [ADRESSE]. Les dépendances sont déclarées dans [FICHIER].
EN  The analysis code is archived in [REPOSITORY] at [DOI], version [TAG],
    under a [LICENCE] licence. Development continues at [ADDRESS].
    Dependencies are declared in [FILE].
```

## 6. Dépôts et identifiant pérenne

Un dépôt de recherche se distingue d'un hébergement par cinq propriétés : il attribue un identifiant pérenne, exige des métadonnées structurées, versionne sans modification silencieuse, prend un engagement de conservation, déclare des conditions d'usage. Une plateforme de développement logiciel, une page personnelle, un espace de stockage institutionnel non catalogué n'en offrent aucune. Un lien vers un dépôt de code ne vaut donc pas archivage : il pointe vers un état qui peut changer ou disparaître sans trace, ce qui contredit ce que la déclaration promet.

Trois voies vers un identifiant pérenne : déposer dans un dépôt qui attribue un DOI (DataCite), relier le dépôt de développement à un dépôt d'archivage pour qu'une version publiée reçoive son propre DOI, archiver le code source dans Software Heritage, qui délivre un identifiant SWHID calculé sur le contenu.

Exemples vérifiés le 2026-08-17, liste partielle qui vieillit vite. Généralistes : Zenodo (opéré par le CERN, soutenu par la Commission européenne), Dryad, figshare, OSF. Disciplinaires : ENA et GenBank pour les séquences nucléotidiques, la Protein Data Bank pour les structures macromoléculaires, PANGAEA pour les données de la Terre et de l'environnement. Chercher le dépôt du domaine dans les registres re3data ou FAIRsharing avant de retomber sur un généraliste : un dépôt disciplinaire impose un format que ses lecteurs savent déjà lire.

## 7. Ce que FAIR demande d'un jeu déposé

Les principes FAIR (Wilkinson et al., 2016) se traduisent en gestes vérifiables.

- Trouvable : identifiant pérenne, métadonnées riches qui portent cet identifiant, jeu indexé dans un dépôt interrogeable.
- Accessible : protocole d'accès standard et ouvert ; les métadonnées restent accessibles même quand les données ne le sont plus, de sorte qu'un jeu fermé reste décrit et citable.
- Interopérable : format ouvert lisible par machine, vocabulaire du domaine, liens déclarés vers les autres jeux.
- Réutilisable : licence explicite, provenance documentée, description conforme aux usages de la discipline.

FAIR ne veut pas dire ouvert. Un jeu sous accès contrôlé est FAIR quand ses métadonnées sont publiques et sa procédure d'accès décrite.

## 8. Obligations de science ouverte des financements européens

Sous Horizon Europe, la science ouverte est une obligation contractuelle, gouvernée par le principe "as open as possible, as closed as necessary". Deux pratiques sont obligatoires : l'accès ouvert aux publications évaluées par les pairs, par dépôt de la version finale ou du manuscrit accepté dans un dépôt de confiance (licence CC BY ou équivalente pour un article de revue), puis l'accès ouvert aux données de recherche selon le même principe. Un plan de gestion des données est exigé puis tenu à jour. Les frais de publication ne sont remboursables que dans une revue intégralement en accès ouvert, pas dans une revue hybride. Une restriction reste possible pour intérêt légitime (exploitation commerciale), protection des données, vie privée, confidentialité, secret d'affaires, sécurité, droits de propriété intellectuelle ; sa justification s'écrit dans le plan de gestion des données.

Ces lignes valent pour Horizon Europe à la date de vérification, dans leurs grandes lignes seulement. Les numéros d'article de la convention de subvention, les délais exacts, les règles propres à un appel ou à un programme national ne sont pas repris ici : les vérifier dans la convention du projet, auprès du financeur ou du service compétent de l'établissement. Un contrat industriel, un programme régional, un financement national portent leurs propres clauses, parfois plus fermées.

## 9. Ce que la déclaration ne règle pas

Consentement des personnes concernées. Déclarer un partage ne crée pas le consentement. Un jeu qui porte des données à caractère personnel se partage dans les limites de l'information donnée aux participants et du fondement juridique du traitement.

Autorisation de l'employeur. Le déposant n'est pas toujours titulaire des droits. Un accord de consortium, un contrat de recherche, une politique d'établissement peuvent conditionner ou interdire le dépôt.

Licence des données de tiers. Annoncer disponible un jeu reçu d'un partenaire ne confère aucun droit de rediffusion. `droits-figures.md` applique la même règle aux figures empruntées : citer la source règle l'honnêteté intellectuelle, pas le droit de diffusion.

Contrôle mécanique. `scripts/check-disponibilite.py` vérifie la forme de la déclaration : présence d'une section, régime identifiable, identifiant pérenne bien formé quand l'ouverture est annoncée, licence quand du code est annoncé, date quand un embargo est annoncé. Il ne vérifie ni que l'identifiant résout, ni que le jeu déposé contient ce que la déclaration annonce, ni qu'une autorisation existe.

## Sources

- Wilkinson MD, Dumontier M, Aalbersberg IJ et al. The FAIR Guiding Principles for scientific data management and stewardship. Scientific Data, 2016, 3:160018. https://doi.org/10.1038/sdata.2016.18
- Gabelica M, Bojcic R, Puljak L. Many researchers were not compliant with their published data sharing statement: a mixed-methods study. Journal of Clinical Epidemiology, 2022, 150:33-41. https://doi.org/10.1016/j.jclinepi.2022.05.019
- ICMJE, Clinical Trials, section Data Sharing. https://www.icmje.org/recommendations/browse/publishing-and-editorial-issues/clinical-trial-registration.html (consultée le 2026-08-17)
- European Research Executive Agency (Commission européenne), Open science. https://rea.ec.europa.eu/open-science_en (consultée le 2026-08-17)
- Dépôts généralistes : Zenodo https://zenodo.org/ ; Dryad https://datadryad.org/ ; figshare https://figshare.com/ ; Open Science Framework https://osf.io/ (consultés le 2026-08-17)
- Registres de dépôts : re3data https://www.re3data.org/ ; FAIRsharing https://fairsharing.org/ (consultés le 2026-08-17)
- Dépôts disciplinaires cités : European Nucleotide Archive https://www.ebi.ac.uk/ena/browser/home ; GenBank https://www.ncbi.nlm.nih.gov/genbank/ ; RCSB Protein Data Bank https://www.rcsb.org/ ; PANGAEA https://www.pangaea.de/ (consultés le 2026-08-17)
- Software Heritage https://archive.softwareheritage.org/ et son identifiant SWHID https://www.swhid.org/ (consultés le 2026-08-17)
