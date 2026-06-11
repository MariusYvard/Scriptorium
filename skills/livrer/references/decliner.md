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
- Post professionnel : accroche, valeur concrète, une invitation à lire ou à échanger.
- Communiqué : chapô qui répond aux questions essentielles (quoi, qui, quand, où, pourquoi), citation attribuée, contact.

## 3. Tenir l'invariance des faits

Aucun canal n'introduit un fait absent du source ni ne déforme un chiffre. Un raccourci de format ne devient pas une approximation. En cas de doute, revenir au source et à sa carte preuve-affirmation.

## 4. Appliquer la charte et le style

Appliquer la même charte graphique (voir `produire` (charte)) à tous les livrables visuels, et le style maison à tous les textes. Repasser chaque déclinaison par `scripts/lint-style.py` et le scorecard.

## Format de sortie

Le jeu de livrables demandés, chacun dans son format, plus une note qui rappelle le noyau commun et confirme que les faits sont inchangés.

## Règles

1. Aucun fait ni chiffre nouveau hors du document source.
2. Même charte et même style sur toutes les déclinaisons.
3. Chaque canal livre sa conclusion à sa place attendue (en tête pour un résumé, en chute pour un post).
4. Ne pas décliner un document non validé.
