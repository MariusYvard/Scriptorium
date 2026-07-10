# Glossaire transverse de sévérité et seuils partagés

Définition unique de chaque niveau de sévérité et des seuils numériques partagés par les scripts déterministes et les agents du plugin. Toute référence qui a besoin de définir critique, majeur, mineur ou signal, ou de citer un seuil, renvoie ici plutôt que de le redéfinir localement avec des mots différents qui dériveraient avec le temps.

## 1. Quatre niveaux de sévérité

- Critique : fausse une affirmation, source manquante ou inventée, violation dure du style maison ou toute condition d'échec qui bloque à elle seule un verdict favorable. Exemple : une référence fabriquée, un tiret cadratin dans un texte qui l'interdit, un axe du scorecard sous le plancher. À corriger avant toute finalisation, jamais reporté.
- Majeur : nuit à la clarté, à la rigueur ou à la structure sans fausser un fait à lui seul. Exemple : une section obligatoire du genre absente, un paragraphe qui casse la progression connu-inconnu, une ligne "à sourcer" non résolue dans la carte preuve-affirmation. À corriger avant la revue suivante, peut attendre un tour si le volume l'exige.
- Mineur : confort de lecture, forme, sans effet sur le fond ni sur la validité. Exemple : une variante orthographique d'un terme technique, un rythme de phrase monotone sur un seul paragraphe. Corrigé si le temps le permet, jamais bloquant.
- Signal : indice consultatif, jamais une preuve à lui seul, seulement une raison de regarder de plus près. Exemple : un préprint récent absent des index bibliographiques consultés, une citation sans ancre exploitable, un désaccord entre deux voix du consensus sur une seule dimension. Ne bloque rien seul.

Un signal qui se corrobore, par une seconde source, une seconde voix ou un second contrôle, devient une sévérité ordinaire (mineur, majeur ou critique selon ce qu'il révèle). Il ne reste jamais un signal indéfiniment une fois vérifié.

## 2. Seuils numériques partagés

| Seuil | Valeur par défaut | Défini dans | Consommé par |
| --- | --- | --- | --- |
| Verdict scorecard | Prêt à partir de 85, à réviser de 70 à 84, à refondre sous 70 | `scripts/scorecard.py` | `controler` (revue), `controler` (consensus), CI éditoriale |
| Plancher par axe | 8/20 (`PLANCHER_DEFAUT`), ajustable par `--plancher N` | `scripts/scorecard.py` | Décision éditoriale à quatre valeurs, revue par consensus |
| Régression de trajectoire | Delta d'axe sous -3 points entre deux rapports | `scripts/scorecard.py` (`trajectoire()`) | `controler` (relecteurs), re-revue |
| Gain marginal de trajectoire (arrêt anticipé) | Delta total sous +3 points sans régression sur aucun axe | `scripts/scorecard.py` (`trajectoire()`, champ `arret_anticipe`) | `atelier` (chemins-defaillance, scénario D6), re-revue |
| Seuil par type de document | Brouillon 65, rapport 80, publication 85, sur 100 | `scripts/scorecard.py` (`SEUILS_TYPE`, option `--seuil-type`) | `controler` (revue), `controler` (consensus), `atelier` (chemins-defaillance, scénario D6) |
| Taux d'égalité de la comparaison par paires | Sous 10% écart net, 10 à 30% normal, 30 à 50% versions proches, au-dessus de 50% grille à resserrer | `controler/references/consensus.md` (section 8) | `controler` (consensus), `controler/references/contrat-notation.md` |
| Friction des outrepassements | Cran 1 avertissement seul, cran 2 justification non vide, cran 3 et plus 100 caractères au moins | `scripts/project.py` (`valider_justification`), `tools/check.py` | `atelier` (piloter), CI éditoriale |
| Seuil de scorecard en CI | 85 par défaut, ajustable par `profil.json` (`seuil_scorecard`) | `docs/CI.md`, `controler/references/profils-discipline.md` | `tools/check.py`, CI du projet d'écriture |

Ces valeurs sont fixées une seule fois, dans leur script ou fichier d'origine. Une référence qui cite un de ces seuils le fait par renvoi ("voir `scorecard.py`"), jamais en recopiant un chiffre qui pourrait diverger de l'original après une évolution du script.

## 3. Fraîcheur des sources par type de document

Le facteur de récence détaillé (poids par ancienneté) reste défini une seule fois dans `produire/references/ponderation-sources.md`, section Facteur de récence. Ce glossaire n'en reprend que le principe d'usage par type de document cité, pour éviter qu'une référence invente son propre barème de fraîcheur.

| Type de document cité | Fenêtre de fraîcheur attendue | Hors de la fenêtre |
| --- | --- | --- |
| Fait du monde présent (chiffre, acteur en poste, prix, état d'une loi) | Vérifié au moment de la rédaction, jamais restitué de mémoire | Invalide, à revérifier systématiquement avant usage |
| Donnée chiffrée sectorielle ou de marché | Moins de deux ans (voir `ponderation-sources.md`) | Traitée avec prudence, signalée comme telle dans le texte |
| Norme ou standard cité (schéma de reporting, format de citation) | Version en vigueur au moment de la vérification | Signalé comme daté avec la date de vérification, jamais tu |
| Référence fondatrice ou historique | Sans fenêtre, la stabilité de la référence est le critère, pas son âge | Sans objet |

Pour la cadence de veille post-publication (vitesse du champ, périodicité indicative), voir `produire/references/veille.md`, section cadence conseillée, qui détaille ce principe plutôt que de le répéter ici.

## 4. Nombre minimal de sources par genre exigeant

Ce plancher est consultatif, jamais un seuil qui bloque une livraison à lui seul (voir `docs/CONCEPTION.md`, principe de mesure avant politique) : un document sous le plancher se signale, il ne se refuse pas mécaniquement pour ce seul motif.

| Catégorie de genre | Exemple de genre | Plancher indicatif de sources |
| --- | --- | --- |
| Académique ou scientifique à revue de littérature | Revue de littérature, rapport scientifique, dissertation | 10 sources en mode complet, 5 en mode resserré |
| Professionnel à enjeu de décision | Analyse stratégique, étude de marché, note financière, rapport d'évaluation | 6 sources, dont au moins deux triangulées sur toute affirmation centrale |
| Bref ou à circulation interne | Pitch, post professionnel, communiqué | Pas de plancher fixe, mais toute affirmation chiffrée exige au moins une source vérifiée |

## Comment renvoyer ici

Une référence ou un agent qui a besoin d'un niveau de sévérité ou d'un seuil charge ce fichier et cite la section précise, par exemple "critique, voir `controler/references/severite.md` section 1", plutôt que de redéfinir critique ou majeur avec ses propres mots. Une redéfinition locale dérive avec le temps sans que personne ne le remarque. Un renvoi ne dérive jamais, puisqu'il n'existe qu'à un seul endroit.
