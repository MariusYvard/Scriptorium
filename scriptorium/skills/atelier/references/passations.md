# Schémas de passation entre sous-commandes

Ce que chaque sous-commande doit livrer à la suivante, ce que la suivante exige pour ne pas repartir de zéro et ce qui manque le plus souvent en pratique. Une passation ratée ne se voit pas tout de suite : la sous-commande consommatrice avance quand même, avec moins que ce dont elle avait besoin et le défaut ne remonte qu'à la revue. Ce fichier rend explicite ce que `atelier` (piloter) fait déjà implicitement d'une phase à l'autre (voir `piloter.md`, section renforcement aux transitions, qui rappelle la règle et l'anti-pattern de chaque transition) : ici, ce sont les champs précis qui voyagent, pas le rappel de discipline.

## Table des passations du flux type

| Passation | Le producteur livre | Le consommateur exige | Ce qui manque le plus souvent |
| --- | --- | --- | --- |
| cadrer vers sourcer | Genre choisi, problématique en question fermée, plan validé avec une commande de preuve par section (quelle affirmation prévue, quelle preuve attendue) | Une cible précise par affirmation à sourcer, pas une consigne générale de type "trouve des sources" | La commande de preuve par section : sans elle, sourcer cherche sans savoir quoi chercher précisément |
| sourcer vers genre | Carte preuve-affirmation, bibliographie formatée selon la norme choisie, faits attribués avec leur niveau de preuve | Une preuve datée par affirmation centrale, ancrée par une citation exacte ou une localisation précise (voir `produire/references/integrite-sources.md`) | L'ancrage : une source existe et convient, mais sans citation ni localisation exploitable |
| genre vers rédacteur (sous-agent) | Plan de la section, carte preuve-affirmation du périmètre confié, glossaire des termes fixés, liste des figures et tableaux déjà numérotés avec le prochain numéro libre par type | Le glossaire et les numéros déjà servis, dans le prompt lui-même : l'agent `redacteur` n'a que Read, Glob et Grep, il ne lit pas `projet.json` | Le glossaire et la liste des objets numérotés : sans eux la deuxième section rebaptise un terme fixé en première et rouvre la numérotation des figures à 1 |
| genre vers revue | Document complet, carte preuve-affirmation à jour après les coupes et ajustements de la rédaction | Le document et sa carte ensemble, jamais le document seul | La carte preuve-affirmation mise à jour : la rédaction en coupe des lignes sans répercuter la coupe sur la carte |
| revue vers relecteurs | Verdict, constats classés par sévérité, chacun citant sa règle et sa section, carte preuve-affirmation | Un constat avec règle citée et section visée, jamais une note de lecture vague | La règle citée : un constat sans elle ne permet pas une réponse point par point traçable |
| genre vers document | Texte au verdict "Prêt" explicite, bibliographie formatée, figures et tableaux numérotés et vérifiés (voir `produire/references/figure.md`) | La confirmation explicite du verdict "Prêt" avant toute mise en forme | La confirmation elle-même : mettre en forme un texte dont le statut de revue n'est pas rappelé explicitement |
| document vers decliner | Document mis en forme validé, charte graphique appliquée, noyau du contenu identifiable | Le noyau déjà isolé (thèse en une phrase, faits porteurs, conclusion, sources clés), pas à reconstituer depuis le document mis en forme | La révision préalable : décliner un document dont la revue n'a pas rendu de verdict propage une erreur dans tous les canaux à la fois |
| projet (partout) | Contexte accumulé et à jour : genre, problématique, charte, profil de discipline, plan, sources, état de chaque étape, version de chaque artefact | L'état exact au moment de la reprise (voir `projet.md`, section frontières et reprise), jamais une paraphrase reconstituée de mémoire | La mise à jour au fil de l'eau : un `projet.json` qui retarde d'une étape fait redemander à l'utilisateur ce qu'il a déjà donné |

## Le passeport porte ces passations

`projet.json` (voir `projet.md`) est le support concret de la colonne "le producteur livre" pour la ligne `projet (partout)` : chaque champ qu'il conserve (genre, problématique, charte, profil, plan, sources) est un des champs qu'une passation exige en aval. Une sous-commande qui alimente `projet.json` à chaque étape assure du même geste la passation vers toutes les suivantes, sans avoir à répéter la commande de preuve, la carte preuve-affirmation ou le verdict à chaque appel.

## La passation vers un sous-agent est différente

Une passation entre sous-commandes s'appuie sur des fichiers que les deux côtés peuvent lire. Une passation vers un sous-agent, non. L'agent `redacteur` n'a que Read, Glob et Grep, il rend son texte au parent et ne touche pas au passeport : ce que son prompt ne porte pas explicitement n'existe pas pour lui. Un document long rédigé section par section en subit les deux conséquences. La terminologie dérive (un terme fixé en section 2 revient sous un synonyme en section 5) et la numérotation se rouvre (chaque passe renumérote ses figures à partir de 1 ou saute un rang qu'une autre passe a déjà pris).

Le parent tire donc du passeport le glossaire et les objets déjà numérotés, puis les colle dans le prompt de chaque passe.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py passation
```

La sortie porte le glossaire des termes fixés, la liste des figures, tableaux, équations et annexes déjà numérotés avec leur libellé, puis le prochain numéro libre par type. Au retour de la passe, le parent enregistre les objets que la section a introduits, avant de lancer la suivante.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py objet figure 3 "Courbe de conversion"
```

Un numéro déjà pris par un autre libellé est refusé plutôt que réaffecté : deux figures 3 dans un même document ne se rattrapent plus à la mise en forme. Les numéros ainsi fixés sont ceux que `traceability.py` contrôle ensuite sur le texte assemblé (doublon, saut, départ hors 1).

## Règles

1. Une passation incomplète se signale au moment où elle se produit, pas seulement quand la revue s'en aperçoit en aval.
2. Le champ manquant le plus fréquent (colonne 4) se vérifie en premier avant de déclarer une passation réussie.
3. `projet.json` reste la source unique de l'état transmis d'une sous-commande à l'autre au sein d'une même mission.
4. Vers un sous-agent, le contexte voyage dans le prompt ou ne voyage pas. Aucune passe de rédaction ne commence sans le glossaire et les numéros déjà servis.
