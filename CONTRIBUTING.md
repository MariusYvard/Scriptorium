# Contribuer à Scriptorium

Les contributions sont bienvenues : signalement d'un faux positif d'un script, correction d'une source, genre ou public manquant, amélioration d'un garde-fou. Une issue avant une pull request évite le travail perdu.

## Règles du dépôt

1. Style maison sur tout texte du plugin (fichiers .md des compétences, références, agents) : registre encyclopédique, zéro tiret cadratin, pas de virgule d'Oxford, guillemets droits, lexique promotionnel banni. Le linter fait foi : `python3 scriptorium/scripts/lint-style.py FICHIER`.
2. Scripts en Python pur, bibliothèque standard uniquement. Le réseau reste optionnel, derrière un drapeau explicite, avec dégradation gracieuse : un service qui ne répond pas produit une mesure omise et déclarée, jamais une valeur inventée.
3. Toute affirmation factuelle ou référence ajoutée est vérifiée à sa source primaire (URL sans paramètres de suivi). Une source invérifiable est décrite sans attribution plutôt que citée de confiance.
4. Les evals passent au vert avant toute proposition : `python3 evals/run-evals.py` (523 cas, hors ligne). Un mécanisme déterministe nouveau arrive avec son cas d'eval ; un nouveau lot de cas se range dans un module de `evals/cas/` plutôt que d'allonger le fichier unique.
5. Toute nouvelle vérification naît consultative ; sa politique de blocage vient dans une version ultérieure, une fois calibrée (voir `docs/CONCEPTION.md`).
6. Le code adapté d'un projet tiers porte son attribution en tête de fichier et respecte la licence d'origine.

## Flux de release

La publication est pilotée par tag : bump de version dans `scriptorium/.claude-plugin/plugin.json` (seul endroit où vit le numéro), section datée dans `CHANGELOG.md`, tag `vX.Y.Z`, push. La CI vérifie la cohérence, rejoue les evals, construit le `.plugin` et crée la Release. Détail dans `docs/RELEASE.md`.
