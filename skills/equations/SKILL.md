---
name: equations
description: >
  Gère les équations, les unités SI et les chiffres significatifs d'un écrit scientifique, et produit un export PDF de qualité typographique (LaTeX). À utiliser quand l'utilisateur demande "ajoute une équation", "écris la formule", "en LaTeX", "unités SI", "chiffres significatifs", "rapport scientifique avec des maths", "exporte en PDF LaTeX" ou rédige un contenu à formules.
metadata:
  version: "0.1.0"
---

# Équations, unités SI et export LaTeX

Traiter les mathématiques comme du contenu de premier ordre dans un écrit scientifique : équations correctes, unités SI conformes, précision honnête, sortie typographique soignée.

## 1. Écrire les équations

Employer LaTeX. Équation en ligne entre `$...$`, équation hors texte entre `$$...$$`. Numéroter les équations hors texte appelées dans le corps. Définir chaque symbole à sa première apparition. Voir `references/si-latex.md` pour les modèles courants.

## 2. Respecter les unités SI

Charger `references/si-latex.md`. Règles clés : une espace insécable entre le nombre et l'unité (10 kg, pas 10kg), symboles d'unité au singulier et non en italique (m, s, kg, pas « kgs »), préfixes corrects (km, MPa, µm). Pour LaTeX, le paquet siunitx (`\SI{10}{\kilo\gram}`) garantit la cohérence.

## 3. Tenir les chiffres significatifs

Garder une précision constante et honnête. Ne pas reporter plus de chiffres significatifs que la mesure n'en porte. Une moyenne de mesures à deux chiffres significatifs ne se présente pas avec six décimales. Croiser avec `scripts/numbers.py` pour le séparateur décimal et les incohérences.

## 4. Exporter en PDF

Si pandoc et un moteur LaTeX (xelatex) sont disponibles, produire un PDF de qualité.

```
pandoc document.md -o document.pdf --pdf-engine=xelatex
```

Pour les références et la numérotation, ajouter `--citeproc` avec un fichier `.bib` et un style CSL. Si pandoc ou xelatex manque, livrer le Markdown avec le LaTeX intact et signaler que l'export PDF demande ces outils, sans bloquer.

## 5. Intégration

La mise en forme finale passe par `finaliser`. Les formules et unités relèvent de cette compétence, la structure et la bibliographie des compétences `rediger` et `sourcer`. Le contrôle des nombres relève de `scripts/numbers.py`.

## Format de sortie

Le document avec ses équations LaTeX numérotées et ses unités SI conformes, plus le PDF si l'export a réussi, plus une note sur les symboles définis et la précision retenue.

## Règles

1. Chaque symbole est défini à sa première apparition.
2. Unités SI conformes, espace entre nombre et unité, symboles non italiques.
3. Précision honnête, pas de faux chiffres significatifs.
4. Équations hors texte numérotées si elles sont appelées.
5. Export PDF tenté, fallback propre si les outils manquent.
