# Intégration continue éditoriale

Verrouiller un document comme du code : aucun document ne passe sous un seuil de qualité.

## Porte locale

```
python3 tools/check.py "chemin/**/*.md" --seuil 85
```

La commande lance le scorecard sur chaque document et renvoie un code de sortie 1 si l'un d'eux tombe sous le seuil. À utiliser en pré-commit ou avant une remise.

## Porte en intégration continue

Le modèle `templates/editorial-ci.yml` se copie dans `.github/workflows/` d'un projet d'écriture. À chaque push, la porte de scorecard s'exécute et bloque la fusion si un document n'atteint pas le seuil.

## CI du plugin

Le dépôt Scriptorium exécute `.github/workflows/evals.yml` : compilation des scripts et harnais d'évaluation. Une modification qui casse un contrôle déterministe fait échouer la CI.

## Seuils par discipline

Le seuil par défaut est 85. Un profil de discipline (voir `consensus`) peut fixer un seuil propre dans `profil.json`, repris par la porte.
