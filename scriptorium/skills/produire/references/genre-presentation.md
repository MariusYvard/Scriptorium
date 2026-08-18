# Playbook : présentation et soutenance

Support de présentation orale, projeté pendant que l'auteur parle. Le support n'est pas le document : il appuie le discours, il ne le remplace pas. Couvre la soutenance scolaire ou académique et la présentation professionnelle qui expose un travail ou un résultat. Pour convaincre d'acheter ou d'investir, voir le genre pitch. La préparation l'emporte sur l'improvisation. L'attention d'une audience tient sept à dix minutes, prévoir une rupture de rythme au-delà. Sortie en PowerPoint (skill pptx) ou en HTML.

## Langue

La langue se fixe au cadrage, avec le genre. Le support de présentation professionnelle ne change pas d'une langue à l'autre. L'exercice académique, si : la soutenance française (publique, support projeté, jury constitué, mention) n'est pas le viva voce britannique (examen oral fermé devant deux examinateurs, sans support projeté par défaut), ni la defense nord-américaine (séminaire public puis session fermée). Établir le dispositif avant de bâtir le support. Voir `genres-anglais.md`, chargé en plus de ce playbook pour une présentation en anglais.

## Principe

Une idée par diapositive. Le titre de chaque diapositive est une phrase assertive qui porte le message, pas une étiquette : "Les ventes ont doublé en un an", pas "Ventes". Le texte est réduit, la donnée ou la figure porte la preuve.

## Fil d'une soutenance

Contexte et problème, question ou objectif, méthode, résultats, limites, conclusion. Une diapositive de plan en ouverture, une de synthèse en clôture. Le propos suit l'ordre de la démonstration, chaque section sert la suivante.

## Arc narratif en sept temps

Le fil ci-dessus se détaille en sept temps quand la durée le permet. Accroche : une phrase, un chiffre ou une image qui capte l'attention avant même le contexte, absente des formats les plus courts où le contexte assure déjà ce rôle. Contexte : le cadre nécessaire pour comprendre l'enjeu. Problème : ce qui manque, ce qui coince ou la question ouverte. Approche : la méthode choisie, brièvement justifiée (correspond à la méthode du fil ci-dessus). Résultats : la preuve, portée par les figures. Implications : ce que les résultats changent pour le public visé, en plus du constat brut. Appel : la clôture qui engage (question ouverte, recommandation ou prochaine étape), jamais un simple "merci" (voir la barre de qualité plus bas).

Les sept temps ne remplacent pas le fil en six étapes déjà présent : ils le détaillent pour les formats disposant de plus de temps, en ajoutant l'accroche en ouverture et en distinguant les implications d'un simple énoncé de conclusion.

## Minutage par durée

Le nombre de diapositives et leur répartition entre les sept temps se calibrent par la durée annoncée. Ces repères prolongent la règle 10/20/30 déjà citée plus bas (dix diapositives pour vingt minutes, soit environ une diapositive pour deux minutes) : le rythme reste sobre, à l'opposé d'une diapositive par minute qui convient à d'autres styles plus denses. Le script `scripts/check-presentation.py` valide une bande plus large (environ une à deux diapositives par minute) car il couvre des styles de présentation plus larges que celui documenté ici : les deux repères divergent volontairement, celui-ci reste le plus sobre des deux pour une soutenance ou une présentation de résultats.

| Durée | Diapositives | Accroche | Contexte | Problème | Approche | Résultats | Implications | Appel |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 min | 5 | 1 | 1 (avec problème) | - | 1 | 1 | 1 (avec appel) | - |
| 15 min | 8 | 1 | 1 | 1 | 1 | 2 | 1 | 1 |
| 30 min | 14 | 1 | 2 | 1 | 2 | 5 | 2 | 1 |
| 45 min | 20 | 1 | 2 | 2 | 3 | 7 | 3 | 2 |

À cinq minutes, contexte et problème tiennent sur une seule diapositive, de même qu'implications et appel : le format le plus court n'a pas la place pour sept temps distincts, il en fusionne deux paires en préservant les sept idées. Passé quinze minutes, les résultats concentrent une part croissante du temps : c'est la partie qui porte la preuve, elle mérite la place la plus large.

## Concevoir une diapositive

Un titre assertif, un visuel ou une donnée, le minimum de texte. Pas de paragraphe projeté, trois à cinq puces courtes au maximum ou une figure (approche assertion-preuve d'Alley). Une figure par diapositive de fond (produite par `produire` figure), légendée et sourcée. Charte graphique appliquée, contraste suffisant pour la projection. La règle 10/20/30 de Kawasaki sert de garde-fou : au plus dix diapositives, vingt minutes, aucune police sous trente points.

## Délivrer : verbal, vocal, visuel

La règle 7-38-55 de Mehrabian (7 % verbal, 38 % vocal, 55 % visuel) est souvent surinterprétée. Mehrabian précise qu'elle vaut pour la communication de sentiments et d'attitudes quand les canaux se contredisent, pas pour tout message. La leçon n'est pas que le fond compte peu, mais que le verbal, le vocal et le visuel doivent être congruents : une dissonance détruit la confiance.

- Kinésique : mains ouvertes, éliminer les gestes parasites (jouer avec un stylo, bras croisés, mains dans le dos). Regard segmentant la salle en quatre à six blocs, balayés sans fixer personne.
- Proxémique : respecter l'espace personnel (environ 1,20 m). Se déplacer aux transitions, rester immobile sur les messages clés.
- Paraverbal : projeter la voix là où se pose le regard, ralentir le débit que le stress accélère, articuler, phrases courtes. Silences avant une affirmation clé et après un chiffre majeur.

## Impliquer l'audience

La passivité est le premier vecteur de décrochage. Un brise-glace installe l'attente d'interaction et réduit la nervosité, sous trois règles : des questions ciblées, positives et fermées ; une activité calibrée sur la taille de la salle ; jamais de participant forcé à s'exprimer.

| Technique | Taille d'auditoire | Durée | Risque à maîtriser |
| --- | --- | --- | --- |
| Questions ciblées | 1 à 10 | 2 à 3 min | Ton inquisiteur |
| Deux vérités, un mensonge | 10 à 30 | 5 à 7 min | Dépassement du temps |
| Bataille de boules de neige | 30 à 100 | 5 min | Désordre logistique |
| Sondage numérique (vote en direct) | plus de 50 | 1 à 2 min | Panne technique |

## Réguler le trac

Le trac est une activation du système nerveux sympathique (accélération cardiaque, sécheresse buccale, mémoire de travail réduite). Le canaliser plutôt que l'éteindre : respiration abdominale lente avant l'entrée en scène, audience abordée comme un public curieux et non un tribunal, visualisation positive du déroulé.

## Barre de qualité

- Une idée par diapositive, titre assertif.
- Chaque diapositive de fond porte une preuve : chiffre, figure ou exemple.
- Le fil se suit sans saut, l'enchaînement est démonstratif.
- Verbal, vocal et visuel congruents.
- Une conclusion qui répond à la question posée, jamais un "merci" seul.

## Pièges à éviter

- La diapositive surchargée, lue mot à mot par l'orateur.
- Le titre étiquette qui ne dit rien.
- Surinterpréter Mehrabian, croire que le contenu ne compte pas.
- L'improvisation non répétée.

## Sources

- The 10/20/30 Rule of PowerPoint, Guy Kawasaki, 2005. https://guykawasaki.com/the_102030_rule/
- Assertion-Evidence Approach, Rethinking Scientific and Technical Presentations, Michael Alley, Pennsylvania State University. https://www.assertion-evidence.com
- Silent Messages, Implicit Communication of Emotions and Attitudes (règle 7-38-55 et sa portée), Albert Mehrabian, 1981. http://www.kaaj.com/psych/smorder.html
- Micro Expressions, Paul Ekman Group, consulté 2026. https://www.paulekman.com/resources/micro-expressions/

## Publics et exemples

Genre de l'étudiant, de l'enseignant et du chercheur. Exemples : une soutenance de mémoire (plan clair, résultats appuyés sur des figures) ; une présentation de résultats en réunion ; un cours illustré.
