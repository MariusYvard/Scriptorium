# Rédiger (moteur unifié)

Produire un texte rigoureux, fluide et conforme au style maison, à partir d'un plan et de sources. Le genre détermine la structure, la méthodologie transverse détermine la mécanique de chaque paragraphe.

## 0. Préalables

Si le plan n'est pas posé, lancer d'abord `atelier` (cadrer). Si les preuves ne sont pas réunies, lancer d'abord `produire` (sourcer). Rédiger sans plan ni preuve produit du remplissage.

## 1. Charger le playbook du genre

Lire le fichier de genre correspondant dans `references/`, et lui seul, pour ne pas saturer le contexte.

- Rapport scientifique et mémoire : `references/genre-rapport-scientifique.md`
- Article : `references/genre-article.md`
- Long rapport professionnel : `references/genre-long-rapport.md`
- Analyse stratégique : `references/genre-analyse-strategique.md`
- Rapport de prospective : `references/genre-prospective.md`
- Étude de cas d'affaires : `references/genre-etude-de-cas.md`

Charger aussi `references/methodologie-transverse.md` pour la mécanique commune. Pour les outils d'analyse, charger `references/boite-outils-strategie.md` ou `references/boite-outils-prospective.md` selon le besoin.

## 2. Déléguer si le document est long

Pour un document de plus de cinq pages, ou à sections denses, déléguer la rédaction à l'agent `redacteur` via l'outil Task, section par section. Lui transmettre le plan, les preuves, le playbook de genre et le style maison. L'agent retourne le texte, il n'écrit pas de fichier. Assembler ensuite les sections et vérifier la cohérence d'ensemble.

## 3. Appliquer le triptyque

Structurer le document selon annonce, développement, synthèse.

- Introduction (annonce) : poser le cadre, le problème, son importance, et annoncer le fil conducteur.
- Corps (développement) : déployer l'argumentation hiérarchisée, chaque idée directrice étayée par une preuve.
- Conclusion (synthèse) : rappeler le problème, résumer les axes, dégager les implications, sans fait nouveau.

Ce triptyque vaut à l'échelle du document et de chaque partie.

## 4. Écrire paragraphe par paragraphe

Appliquer la mécanique de `methodologie-transverse.md`.

- Un paragraphe porte un seul message. La première phrase l'énonce.
- Progression connu-inconnu : chaque phrase part d'un élément déjà posé pour livrer un élément neuf. La phrase suivante reprend ce neuf, devenu connu, pour introduire la notion suivante.
- Lier les phrases par une relation claire : cause, conséquence, contraste, exemple, précision.
- Varier la longueur des phrases. Réserver les phrases courtes et affirmatives pour les conclusions intermédiaires.
- Nommer chaque chose avec précision. Verbes d'action (croître, diminuer, se stabiliser) plutôt que verbes flous (changer, évoluer). Valeurs chiffrées plutôt qu'adverbes vagues (pas "plusieurs cas" mais le nombre).

## 5. Soigner l'entrée en matière

Pour un article ou un rapport, travailler l'accroche : une donnée surprenante, une question, ou une situation concrète. Pour un résumé analytique ou un abstract, livrer la conclusion d'emblée, ne pas enterrer l'information utile sous le récit du cheminement.

## 6. Appliquer le style maison

Appliquer les directives strictes à chaque paragraphe (voir la compétence `produire` (style)). Registre encyclopédique et neutre. Zéro tiret cadratin ou demi-cadratin, utiliser parenthèses ou virgules. Pas de virgule d'Oxford. Guillemets et apostrophes droits. Gras rare. Lexique promotionnel banni (proscrire pivotal, crucial, emblématique, façonner le paysage, témoigne de, souligne, riche tapisserie, incontournable). Pas de métadiscours ("voici le texte", "en tant qu'IA"). Pour relater un travail de terrain, employer le passé composé, pas le passé simple. Proscrire le pronom indéfini "on" au profit d'une tournure passive ou de "nous" selon la norme de la revue.

## 7. Reverse outlining après chaque section

Une fois une section écrite, en extraire le squelette : thèse, puis phrase-sujet de chaque paragraphe, puis preuves rattachées. Vérifier la cartographie : chaque phrase-sujet sert la thèse, chaque preuve sert sa phrase-sujet. Réviser ou retirer tout paragraphe qui ne se rattache pas proprement.

## 8. Gérer les faits mineurs

Tout fait anecdotique mais nécessaire comme preuve part en encadré d'isolation ou en annexe numérotée. Le texte principal reste concis et démonstratif.

## Format de sortie (contrat)

1. Un mini-plan de section (trois à sept points) avant la prose.
2. Le texte, paragraphes au rôle explicite (ouverture, défi, méthode, preuve, limite).
3. Une carte preuve-affirmation pour les affirmations majeures de la section.
4. Une auto-revue courte (clarté, fluidité, stabilité terminologique, affirmations non étayées).

## Règles

1. Garder la terminologie stable sur tout le document. Définir un terme à sa première occurrence.
2. Ne pas écrire un paragraphe que les preuves ne soutiennent pas. Affaiblir ou retirer.
3. Respecter le périmètre validé. Pas de section dont l'ordre pourrait s'inverser sans perte.
4. Traiter les figures et tableaux comme du contenu, pas de la décoration. Un tableau est autonome et lisible.
5. À la fin d'une passe, enchaîner vers `controler` (revue) pour la revue adversariale.
