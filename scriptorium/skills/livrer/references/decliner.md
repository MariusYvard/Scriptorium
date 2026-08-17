# Décliner (adaptation multi-canal)

Tirer un jeu de livrables d'un document validé, chacun ajusté à son canal, sans trahir le fond. Mêmes faits, même charte graphique, longueur et registre adaptés.

## 0. Préalable

Ne décliner qu'un document déjà révisé. La déclinaison propage le contenu, elle ne le corrige pas. Si le source n'est pas validé, lancer `controler` (revue) d'abord.

## 1. Extraire le noyau

Du document source, isoler : la thèse en une phrase, les trois à cinq faits porteurs avec leurs chiffres, la recommandation ou la conclusion, les sources clés. Ce noyau est invariant d'un canal à l'autre.

## 2. Adapter par canal

Charger `references/canaux.md` pour les gabarits. Canaux courants.

- Présentation : une idée par diapositive, titre assertif qui porte le message, appui chiffré. Via le skill `pptx`.
- Résumé d'une page pour décideur : accroche, trois points clés chiffrés, prochaines étapes. Livrer la conclusion d'emblée.
- Abstract : 150 à 300 mots, un volet par section (contexte, méthode, résultats, portée).
- Résumé bilingue : résumé structuré français avec sa traduction anglaise alignée phrase à phrase, mots-clefs dans les deux langues. Mécanisme et contrôle propres à ce canal détaillés en section 3.
- Post professionnel : accroche, valeur concrète, une invitation à lire ou à échanger.
- Communiqué : chapô qui répond aux questions essentielles (quoi, qui, quand, où, pourquoi), citation attribuée, contact.

## 3. Résumé bilingue : alignement et contrôle

Produire un résumé structuré en français, puis sa traduction anglaise composée comme un résumé à part entière, jamais comme une traduction mécanique mot à mot.

1. Rédiger le résumé français, structuré selon le genre (contexte, méthode, résultats, portée pour un texte académique ; accroche, message clé, conclusion pour un texte professionnel).
2. Aligner l'anglais phrase à phrase sur le français : chaque phrase française porte sa phrase anglaise correspondante, dans le même ordre, pour la même affirmation. Un alignement qui ajoute ou retire une affirmation d'une langue à l'autre est une erreur, pas une variante de style.
3. Fournir des mots-clefs dans les deux langues, cinq à sept par langue, choisis pour compléter le titre plutôt que le répéter.
4. Contrôler chaque volet dans sa langue : `scripts/lint-style.py --langue en` sur le volet anglais, l'appel par défaut sur le volet français. Un passage unique sur le fichier entier appliquerait les règles d'une seule langue aux deux moitiés, et signalerait par exemple la virgule sérielle anglaise comme une virgule d'Oxford, ou le pronom « on » dans une phrase française qui n'en porte pas. Le volet anglais suit `produire` (style), référence `style-anglais.md`.
5. Signaler les faux amis techniques rencontrés pendant la traduction, des termes qui se ressemblent mais divergent de sens. Deux exemples fréquents : "évidence" (français : ce qui est manifeste) contre "evidence" (anglais : preuve) : et "actuellement" (français : en ce moment) contre "actually" (anglais : en fait). Un glissement sur un faux ami déforme le résumé sans que rien ne le signale à la lecture.

### Contrôle de traçabilité

Chaque affirmation du résumé, dans les deux langues, doit se retrouver dans le document source. Un résumé n'introduit jamais un fait, un chiffre ou une nuance absente du corps du texte. Reprendre la carte preuve-affirmation du document source (voir `produire`, action sourcer) et vérifier phrase par phrase que le résumé n'en dépasse pas le contenu. Une affirmation du résumé sans correspondance dans le source est retirée ou reformulée pour s'y limiter strictement.

## 4. Tenir l'invariance des faits

Aucun canal n'introduit un fait absent du source ni ne déforme un chiffre. Un raccourci de format ne devient pas une approximation. En cas de doute, revenir au source et à sa carte preuve-affirmation.

### Phrases de couverture protégées

Quand une déclinaison impose une contrainte de longueur stricte (résumé d'une page, abstract calibré), les réserves et les limites du document source ne sont pas les premières coupées pour tenir le format. Désigner avant la réduction une liste courte de phrases de couverture (limite de l'étude, portée du résultat, incertitude signalée) qui survit à la contrainte, quitte à raccourcir ailleurs. Un résumé plus affirmatif que le document qu'il résume est un faux, pas une simplification.

## 5. Appliquer la charte et le style

Appliquer la même charte graphique (voir `produire` (charte)) à tous les livrables visuels, et le style maison à tous les textes. Repasser chaque déclinaison par `scripts/lint-style.py` et le scorecard, avec `--langue en` pour toute déclinaison rédigée en anglais (abstract, résumé bilingue, post destiné à un canal anglophone).

## Format de sortie

Le jeu de livrables demandés, chacun dans son format, plus une note qui rappelle le noyau commun et confirme que les faits sont inchangés. Pour un résumé bilingue : les deux versions alignées phrase à phrase, les mots-clefs dans les deux langues et la liste des faux amis signalés le cas échéant.

## Règles

1. Aucun fait ni chiffre nouveau hors du document source.
2. Même charte et même style sur toutes les déclinaisons.
3. Chaque canal livre sa conclusion à sa place attendue (en tête pour un résumé, en chute pour un post).
4. Ne pas décliner un document non validé.
5. Un résumé bilingue n'introduit jamais, dans aucune des deux langues, une affirmation absente du document source.
