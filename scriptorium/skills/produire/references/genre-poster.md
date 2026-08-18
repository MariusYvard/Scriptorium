# Playbook : poster scientifique

Support visuel affiché pendant une session dédiée (conférence, colloque, soutenance, journée portes ouvertes), consulté sans l'auteur present une partie du temps. Le poster n'est pas un article réduit ni un mur de texte : c'est une amorce de conversation. Le format et l'orientation sont imposés par l'organisateur : le portrait (a0 ou a1) domine dans les colloques, le paysage existe dans certaines conférences. Vérifier la consigne avant de composer, l'orientation commande toute la structure en colonnes. Sa réussite se mesure à ce qu'il déclenche un échange, pas à l'exhaustivité de ce qu'il couvre. Format LaTeX via `assets/gabarit-poster.tex` ou PowerPoint via le skill externe `pptx` quand LaTeX n'est pas disponible ou que le poster doit rester éditable après la session (voir `livrer`, action document, pour la même logique de choix appliquée au rapport).

## Langue

La langue se fixe au cadrage, avec le genre. La structure de ce playbook vaut telle quelle en anglais : seuls les intitulés de bandeau changent (Background, Methods, Results, Conclusions, Take-home message). Le décalage réel est en amont, l'acceptation se jouant sur le conference abstract soumis des mois plus tôt sous la limite de mots de l'appel. Voir `genres-anglais.md`, chargé en plus de ce playbook pour un poster en anglais, puis `style-anglais.md` pour la forme.

## Le poster comme amorce de conversation

Le passant ne lit pas un poster comme un texte suivi. Il en fait le tour du regard, retient une chose, puis décide d'approcher ou non. Le rôle du support est de rendre cette décision facile et de donner à l'auteur, présent devant sa planche, un point de départ pour parler. Un poster qui tente de tout dire dans le détail perd cette fonction : le visiteur le lit en silence et repart sans échanger un mot. Composer pour la conversation change les choix de fond : une seule idée centrale mise en avant, des détails tenus en réserve pour la discussion orale plutôt qu'imprimés en petits caractères.

## Lecture à trois distances

Un visiteur traverse trois paliers d'attention, chacun avec son propre contenu utile.

À trois secondes, de l'autre bout de l'allée : seuls le titre et l'image ou le chiffre dominant sont perçus. Le titre doit porter le message, pas juste le sujet ("Le délai de traitement chute de 40 %" plutôt que "Étude du délai de traitement"). À trente secondes, en s'approchant : les intitulés de section et la figure principale se lisent. Le visiteur décide ici s'il s'arrête. À trois minutes, poster en main ou en discussion avec l'auteur : le détail de la méthode, les chiffres secondaires et les limites deviennent accessibles, portés autant par l'échange oral que par le support.

Chaque palier a sa propre police minimale (voir `produire`, action charte, pour la table complète) : jamais moins de 24 points, y compris pour la légende la plus discrète, sous peine de perdre le palier des trois minutes lui-même.

## Hiérarchie visuelle et ratio texte-figures

Le visuel domine largement le texte. Une figure bien choisie remplace un paragraphe de description ; un tableau dense ne remplace jamais un graphique qui montre la même tendance d'un coup d'oeil. Le texte se limite à l'essentiel : contexte, méthode, résultat, limite, chacun en quelques phrases plutôt qu'en paragraphes complets.

Trois niveaux de hiérarchie suffisent. Le titre porte le message central. Les intitulés de section (introduction, méthode, résultat, conclusion) guident le parcours. Le corps de chaque bloc reste court, en puces plutôt qu'en prose quand c'est possible.

## Colonnes et flux de lecture

Un poster portrait se lit le plus souvent en colonnes verticales, de gauche à droite : deux colonnes pour un propos simple, trois pour un propos qui distingue nettement contexte, méthode et résultat, rarement plus de quatre. Une bordure de couleur distincte par bloc (voir `produire`, action charte) aide l'oeil à regrouper le contenu d'un même bloc et à repérer où commence le suivant.

Le sens de lecture doit rester devinable sans flèches ni numéros si possible : haut vers bas, gauche vers droite, comme un texte normal. Si l'ordre s'écarte de cette convention (un poster en paysage à lecture en Z, par exemple), le signaler explicitement par une numérotation ou un guide visuel discret plutôt que de laisser le visiteur deviner.

## Construire le poster

1. Réduire le propos à un message central tenant en une phrase, avant toute mise en page.
2. Choisir deux à quatre figures qui portent l'essentiel de la preuve (voir `produire`, action figure). Une figure sans légende autonome n'a pas sa place ici.
3. Rédiger chaque bloc de texte au minimum : quelques phrases ou puces, jamais un paragraphe académique complet.
4. Mettre en page en colonnes, charte graphique appliquée (couleurs, police, filet d'accent).
5. Vérifier la lecture aux trois distances avant impression : reculer physiquement ou réduire l'aperçu à l'écran pour simuler chaque palier.
6. Imprimer un brouillon à échelle réduite (A4) pour relire les défauts invisibles à l'écran, avant l'impression définitive au format complet.

## Gabarit et charte

Le gabarit LaTeX `assets/gabarit-poster.tex` fournit une structure en colonnes A0 prête à charter (voir `produire`, action charte, pour l'injection des couleurs via `theme.py --format latex`). Les couleurs daltonisme-sûres (`okabe-ito` ou `wong`, voir `produire`, action figure) sont recommandées par défaut : un poster se regarde souvent en lumière de salle changeante et de loin, deux conditions qui aggravent une confusion de couleurs déjà marginale sur écran.

Quand PowerPoint est requis (poster à modifier après la session, absence de compilation LaTeX), le skill externe `pptx` prend le relais avec la même charte et les mêmes figures, converties en images.

## Barre de qualité

- Le message central se lit et se retient en trois secondes.
- Aucune police sous 24 points, y compris les légendes.
- Le visuel domine le texte, chaque figure est autonome et légendée.
- Le sens de lecture se devine sans effort.
- Le poster se prête à la conversation : il laisse des questions ouvertes plutôt que de tout épuiser.

## Pièges à éviter

- Le poster qui copie l'article section par section, sans réduction du propos.
- Le texte en dessous de 24 points pour caser plus de contenu.
- Une palette de couleurs qui porte seule le sens, sans forme ni libellé de secours.
- L'absence de test à distance avant l'impression définitive, seul défaut qui ne se corrige plus après tirage.

## Sources

- Erren TC, Bourne PE. Ten Simple Rules for a Good Poster Presentation. PLoS Computational Biology, 2007, 3(5):e102. https://doi.org/10.1371/journal.pcbi.0030102
- Okabe M, Ito K. Color Universal Design (CUD) : How to make figures and presentations that are friendly to Colorblind people. 2008 (mis à jour 2008). https://jfly.uni-koeln.de/color/
- Table hexadécimale de la palette Okabe-Ito (référence croisée des valeurs). Siegal Lab, New York University. https://siegal.bio.nyu.edu/color-palette/

## Publics et exemples

Genre du chercheur, de l'étudiant en soutenance et de l'ingénieur qui présente un résultat de projet en session d'affichage. Exemple : un doctorant réduit six mois de travail à un message unique ("cette méthode réduit l'erreur de moitié à coût égal"), trois figures et un bloc de méthode de cinq phrases, plutôt qu'un article collé sur une planche.
