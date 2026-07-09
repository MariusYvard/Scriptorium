<!--
Fixture a double usage (test dans evals/run-evals.py et gabarit de reference
montrable a l'utilisateur). Attention en cas de modification : ce commentaire
d'en-tete decrit les tags sans jamais reproduire leur syntaxe exacte entre
crochets, pour ne pas fausser le compte que la fixture est censee illustrer.
Le corps du document ci-dessous porte deux tags de lacune materielle bien
formes (majuscules strictes), un tag de preuve faible bien forme et une
variante du premier tag ecrite en minuscules, qui doit remonter comme forme
mal cassee plutot que comme tag strict (scripts/traceability.py, fonction
tags_lacune). Sert aussi de gabarit : a quoi ressemble un tag de lacune
correct face a une variante qui echappe au grep strict par la casse.
-->

# Exemple : document avec lacunes de preuve taguées

## Contexte du marché

La croissance du segment premium atteint 8 % par an selon les rapports
sectoriels disponibles [LACUNE MATERIELLE] : aucune source primaire ne
couvre directement le sous-segment régional visé par cette analyse.

## Position concurrentielle

Le principal concurrent aurait perdu des parts de marché en 2025
[PREUVE FAIBLE] : l'affirmation ne repose que sur un article de presse
généraliste sans donnée chiffrée vérifiable.

## Risques

Le risque réglementaire reste mal documenté pour la période récente
[lacune materielle] : ce tag est mal cassé (minuscules), il doit être
signalé comme variante plutôt que compté comme un tag strict.

Un second risque, celui de la disponibilité des matières premières, n'est
appuyé par aucune source publique récente [LACUNE MATERIELLE].

Vérification attendue (`python3 scripts/traceability.py FICHIER --format json`) : `tags_lacune_materielle` égal à 2, `tags_preuve_faible` égal à 1, `tags_variantes_mal_formees` égal à une liste avec une seule entrée, la forme en minuscules.
