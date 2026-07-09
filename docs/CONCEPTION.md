# Principes de conception

Principes transverses qui expliquent des choix répétés dans plusieurs fichiers du plugin, plutôt que d'être justifiés localement à chaque fois. Un mécanisme qui semble s'écarter d'un de ces principes devrait être reconsidéré plutôt qu'accepté tel quel.

## Mesure avant politique

Toute nouvelle vérification déterministe entre dans le plugin consultative : elle mesure et signale, elle ne bloque rien. Sa politique de blocage (seuil, plancher, refus) n'arrive que dans une version ultérieure, une fois calibrée sur des documents réels. Le signal de contamination de source (`produire/references/integrite-sources.md`) reste consultatif par ce principe ; le plancher par axe du scorecard (`scripts/scorecard.py`) n'est arrivé qu'après que le score global lui-même ait été calibré sur plusieurs audits.

## Dégradation gracieuse

Un contrôle qui dépend du réseau (triangulation Crossref, OpenAlex, Semantic Scholar, vérification croisée par un second modèle) reste optionnel. Une panne, un délai dépassé ou une clé absente retire le contrôle du calcul, jamais ne le remplace par un résultat inventé. Un verdict par omission, le contrôle ne s'est pas prononcé, est toujours préféré à un faux verdict généré pour combler une panne.

## Jamais de moyenne qui masque un désaccord

Deux dimensions ou deux voix qui jugent différemment un même point se rapportent telles quelles, jamais lissées en une moyenne qui efface le désaccord. Un consensus qui gomme un signal critique est un échec du consensus, pas une réussite. Cette règle traverse le scorecard (plancher par axe), la revue par consensus (anti-ancrage entre voix) et le contrat de mission (dimensions notées individuellement).

## Source canonique unique

Une règle partagée par plusieurs fichiers, un seuil, une définition de sévérité, un chiffre, se définit à un seul endroit, dont tous les autres se contentent de faire renvoi. `controler/references/severite.md` et `produire/references/ponderation-sources.md` en sont les exemples les plus visibles. Une règle recopiée à deux endroits dérive avec le temps sans que personne ne le remarque. Un renvoi ne dérive jamais, puisqu'il n'existe qu'à un seul endroit.

## Append-only pour la mémoire de projet

`projet.json` ne réécrit jamais une entrée de son journal. Une correction, une reprise, un changement de modèle s'ajoutent comme une nouvelle entrée horodatée, l'ancienne reste lisible. Cette discipline rend la mémoire de projet auditable : reconstituer l'état à n'importe quel instant passé reste possible, pas seulement l'état courant.

## Verdicts fermés et nommés

Un contrôle rend un verdict choisi dans une liste finie et nommée (Prêt, à réviser ou à refondre ; vérifié, plausible, invérifiable ou fabriqué ; résolu, limite assumée, non résoluble ou désaccord fondé sur preuve), jamais une nuance libre non comparable d'un document à l'autre. Un verdict fermé se compte, se compare et s'agrège mécaniquement. Une nuance libre ne le permet pas.

## Le déterministe mesure, le modèle juge

Un script (`scorecard.py`, `verify-sources.py`, `traceability.py`) produit un chiffre ou un fait reproductible, jamais une appréciation. Un agent ou le modèle produit un jugement (sévérité, verdict, arbitrage d'un désaccord), jamais un chiffre inventé sans calcul dessous. Le détail du calcul reste toujours montré à côté du chiffre, pour qu'un désaccord humain sur le résultat se rattache à une étape précise du calcul plutôt qu'à une boîte noire.

## Attribution

Une partie des mécanismes ajoutés aux références de `controler`, `produire` et `atelier` depuis la version 0.7.0 s'inspire, entre autres sources, du plugin academic-research-skills de Cheng-I Wu (licence CC BY-NC 4.0) : idées et mécanismes réimplémentés à neuf, en français, dans l'architecture propre de Scriptorium, sans reprise de texte ni de gabarit source ni traduction directe. Le dépôt source est cité ici par courtoisie ; le README ne porte pas encore de section dédiée aux inspirations externes, à créer lors de la finalisation de la version qui intègre cette récolte.
