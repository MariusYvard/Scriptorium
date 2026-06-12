# Playbook : rapport d'incident et post-mortem

Compte rendu d'un incident, écrit pour apprendre, pas pour blâmer. Finalité : réduire la probabilité et l'impact d'une récurrence. Culture sans blâme.

## Sans blâme

Se concentrer sur les causes systémiques, jamais sur une personne. Partir du principe que chaque intervenant a agi correctement avec l'information dont il disposait. Le post-mortem ne sert pas à exprimer une frustration.

## Critères de déclenchement

Définir à l'avance quand un post-mortem est requis (indisponibilité au-delà d'un seuil, perte de données, intervention de l'astreinte, dépassement d'un délai de résolution), pour que chacun sache.

## Contenu

Documenter les faits : impact, chronologie, actions de mitigation et de résolution, causes racines, actions de suivi priorisées. Soumettre le brouillon à une revue par des pairs, puis le diffuser largement.

## Barre de qualité

- Ton sans blâme, causes systémiques et non personnes.
- Impact et chronologie factuels, datés.
- Cause racine atteinte, pas seulement les symptômes.
- Actions de suivi concrètes, assignées, priorisées.
- Brouillon relu par des pairs avant diffusion.

## Pièges à éviter

- Désigner un coupable.
- S'arrêter au symptôme sans remonter à la cause racine.
- Des actions vagues, sans responsable ni échéance.
- Un post-mortem rédigé puis jamais relu ni diffusé.

## Sources

- Postmortem Culture: Learning from Failure, The Site Reliability Workbook, chapitre 10, Google, 2018. https://sre.google/workbook/postmortem-culture/
- Postmortem Culture: Learning from Failure, Site Reliability Engineering, chapitre 15, J. Lunney et S. Lueder, Google, 2017. https://sre.google/sre-book/postmortem-culture/

## Publics et exemples

Genre de l'ingénieur, de l'exploitant et de l'équipe d'astreinte. Exemples : le post-mortem d'une panne de service (chronologie, cause racine, actions) ; un retour d'expérience après incident de sécurité.
