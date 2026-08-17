# Playbook : article

Couvre l'article éditorial, la tribune, la vulgarisation, la note de fond et l'article de blog professionnel. Finalité : éclairer, expliquer ou convaincre un lectorat large ou semi-spécialisé. Critères clés : accroche, fil conducteur, preuve, lisibilité.

## Langue

La langue du document se fixe au cadrage, avec le genre et le plan, et ne change plus ensuite. Un article rédigé en anglais suit `produire` (style), référence `style-anglais.md` : les règles de forme calibrées sur le français y sont remplacées, non ajoutées, et le contrôle mécanique se lance avec `scripts/lint-style.py --langue en`. Changer de langue en cours de rédaction accumule deux jeux de règles contradictoires sans en satisfaire aucun.

## Structure

1. Accroche : une donnée surprenante, une question, ou une situation concrète. Elle crée la curiosité et promet une valeur.
2. Introduction : contexte, problème, ce que l'article couvre.
3. Sections de corps : chaque section un point clé, étayé par un exemple, une donnée ou une citation sourcée.
4. Contre-arguments : adresser les objections sérieuses, c'est gagner en crédibilité.
5. Conclusion : synthèse des points, et selon le but, ouverture ou appel à l'action.
6. Références : sources vérifiées, liens nettoyés des paramètres de suivi.

Un article qui s'appuie sur un jeu de données ou sur du code produits pour l'occasion (note de fond chiffrée, article de blog technique) porte en plus une déclaration de disponibilité, juste avant les références : où se trouvent les données, sous quel identifiant pérenne, sous quelle licence. Régimes, formulations et contrôle mécanique dans `disponibilite.md`. Un article d'opinion sans donnée propre n'en a pas besoin.

## Quatre angles selon le but

- Vulgarisation : partir du connu du lecteur, introduire un concept neuf par section, illustrer par analogie ou exemple. Définir chaque terme technique.
- Tribune ou point de vue : thèse forte et assumée, preuves à l'appui, réfutation des objections, conclusion qui engage.
- Note de fond ou explication : structurer par questions que le lecteur se pose, dans l'ordre où il les pose. S'inspirer du modèle Diátaxis (distinguer le tutoriel pas à pas, le guide pratique orienté tâche, la référence, l'explication conceptuelle, et ne pas les mélanger).
- Leadership intellectuel : angle original, recension des perspectives existantes, thèse différenciante, preuves, conclusion mémorable.

## Travail de l'accroche

Proposer trois variantes et choisir.

- Donnée : un chiffre précis et inattendu, suivi de sa portée.
- Question : une interrogation qui ouvre une tension réelle.
- Situation : un cas concret, court, qui incarne le problème.

Tester : crée-t-elle la curiosité, promet-elle une valeur, est-elle précise, parle-t-elle au public.

## Lisibilité

- Phrases de longueur variée, phrase courte pour le message clé.
- Un paragraphe, un message, première phrase en tête.
- Langage clair, mots simples, pas de jargon non défini.
- Ne pas enterrer l'information utile sous le récit du cheminement.

## Workflow recommandé

1. Plan commun, repérage des points à sourcer.
2. Recherche et citations.
3. Rédaction de l'introduction, puis retour sur l'accroche.
4. Rédaction des sections, revue après chacune.
5. Conclusion, puis revue d'ensemble (fluidité, cohérence, liens).
6. Polissage : lecture à voix haute pour repérer les phrases lourdes.

## Barre de qualité

- L'accroche tient sa promesse à la fin.
- Chaque affirmation forte est sourcée.
- Les objections sérieuses sont adressées, pas esquivées.
- Le fil conducteur est continu, aucune section interchangeable.
- Style maison respecté (registre neutre, lexique banni absent, typographie droite).

## Pièges à éviter

- L'accroche racoleuse que le corps ne tient pas.
- L'empilement d'exemples sans thèse.
- Le ton promotionnel (proscrire incontournable, révolutionnaire, qui change la donne).
- La conclusion qui introduit un fait nouveau au lieu de synthétiser.

## Exigences de la destination

Un article destiné à une revue, une conférence ou un support externe précis porte ses propres règles de forme (limite de mots, anonymisation, format de citation imposé) avant même la question du style. Vérifier ces exigences en tout début de mise en forme, jamais après rédaction complète : voir `livrer`, action document, section exigences par destination, pour la table des grandes familles de venues et le renvoi aux gabarits officiels.

## Sources

- Recommendations for the Conduct, Reporting, Editing and Publication of Scholarly Work in Medical Journals (page de titre, résumé, références, soumission), ICMJE, 2026. https://www.icmje.org/recommendations/browse/manuscript-preparation/preparing-for-submission.html
- Writing a Scientific Paper (Title, Abstract, Peer Review), University of California Irvine Libraries, 2026. https://guides.lib.uci.edu/scientificwriting

## Publics et exemples

Le chercheur en tire une tribune ou un article de vulgarisation, l'analyste géopolitique une note d'opinion argumentée. Exemple : un analyste signe un article sur une recomposition régionale, accroche factuelle puis thèse défendue pas à pas.
