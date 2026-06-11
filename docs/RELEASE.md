# Checklist de release

Procédure versionnée pour publier une nouvelle version de Scriptorium. La publication est automatisée par `.github/workflows/release.yml` : pousser un tag `vX.Y.Z` déclenche la vérification, les evals, la construction du `.plugin` et la création de la Release. Respecter l'ordre.

## 1. Préparer

- Décider du saut de version (sémantique) : correctif (0.6.x), mineur (0.x.0), majeur (x.0.0).
- Renseigner la section `## [X.Y.Z] — AAAA-MM-JJ` dans `CHANGELOG.md` en y déplaçant le contenu de `## [Unreleased]`.

## 2. Aligner les versions

Le numéro vit à deux endroits, qui doivent rester synchronisés. Le workflow refuse le tag sinon.

- `.claude-plugin/plugin.json`, champ `version`.
- `.claude-plugin/marketplace.json`, champ `metadata.version` et le `version` de l'entrée plugin.

## 3. Contrôler en local

```
python3 evals/run-evals.py
python3 scripts/lint-style.py <fichier>
```

Tous les cas doivent passer.

## 4. Taguer et pousser

```
git commit -am "X.Y.Z : <resume>"
git tag vX.Y.Z
git push origin main --tags
```

Le workflow `release.yml` vérifie que le tag correspond aux deux manifestes et qu'une section `## [X.Y.Z]` existe dans `CHANGELOG.md`, lance les evals, construit `scriptorium-X.Y.Z.plugin` avec `git archive`, extrait les notes du CHANGELOG et publie la Release avec l'artefact attaché.

## 5. Après publication

- Vérifier que la Release apparaît sur la page Releases avec le `.plugin` attaché.
- Installer depuis l'artefact publié et tester un déclenchement de chaque compétence.

## Journal des versions

Le journal vit dans `CHANGELOG.md`, au format Keep a Changelog.
