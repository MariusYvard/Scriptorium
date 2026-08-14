# Intégration continue éditoriale

Verrouiller un document comme du code : aucun document ne passe sous un seuil de qualité.

## Porte locale

```
python3 tools/check.py "chemin/**/*.md" --seuil 85
```

La commande lance le scorecard sur chaque document et renvoie un code de sortie 1 si l'un d'eux tombe sous le seuil. À utiliser en pré-commit ou avant une remise.

## Passer outre, avec friction

Un blocage se lève par `--outrepasser`, avec une friction croissante : le premier passage n'exige qu'un avertissement, le deuxième une justification (`--justification "..."`), le troisième une justification de cent caractères au moins. Chaque passage outre est journalisé (dans `projet.json` si présent, sinon dans `.outrepassements.json`) et reste visible dans le tableau de bord du projet.

## Porte en intégration continue

Le modèle `scriptorium/templates/editorial-ci.yml` se copie dans `.github/workflows/` d'un projet d'écriture. À chaque push, la porte de scorecard s'exécute et bloque la fusion si un document n'atteint pas le seuil.

## CI du plugin

Le dépôt Scriptorium exécute `.github/workflows/evals.yml` : compilation des scripts et harnais d'évaluation. Une modification qui casse un contrôle déterministe fait échouer la CI.

## Fraîcheur des sources normatives

Chaque playbook de genre porte une section Sources dont les URL vieillissent. Un contrôle périodique (mensuel suffit) les repasse en revue :

```
python3 scriptorium/scripts/verify-sources.py scriptorium/skills/produire/references/genre-*.md --check-links
```

Le contrôle est consultatif : une URL morte se remplace par une source équivalente vérifiée, elle ne bloque pas une release.

## Seuils par discipline

Le seuil par défaut est 85. Un profil de discipline (voir `controler` (consensus)) peut fixer un seuil propre dans `profil.json`, repris par la porte.
