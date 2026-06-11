---
name: finaliser
description: >
  Met en forme un texte validé en livrable abouti (Word ou PDF) selon les conventions académiques et professionnelles du genre : page de garde, sommaire, texte justifié, bibliographie formatée, annexes numérotées, résumé. À utiliser quand l'utilisateur demande "mets en forme", "génère le Word", "produis le PDF", "finalise le document", "ajoute la page de garde", "formate la bibliographie" ou veut transformer un brouillon validé en document remis.
metadata:
  version: "0.1.0"
---

# Finaliser (mise en forme du livrable)

Transformer un texte validé en document remis. Le fond ne change plus à cette étape, seule la forme s'ajoute. La mise en forme suit la structure standard du genre.

## Préalable

Ne finaliser qu'un texte passé par `reviser` avec un verdict « Prêt ». Si le texte n'a pas été révisé, lancer d'abord `reviser`. Mettre en forme un texte fautif ne fait que rendre la faute présentable.

## 1. Choisir le format de sortie

Selon la demande et le genre. Charger ensuite le bon skill de production de fichier, et lui seul.

- Document Word : lire le skill `docx`, puis construire le fichier.
- PDF : lire le skill `pdf`, puis construire le fichier.
- Présentation : lire le skill `pptx` si la demande est une soutenance.

## 2. Appliquer la mise en forme du genre

Charger `references/mise-en-forme.md` pour les conventions détaillées par genre. Résumé :

- Rapport scientifique et mémoire : page de garde (titre précis), sommaire, listes des tableaux, figures et abréviations, texte justifié, police classique en 11 ou 12, interligne 1,5, pagination, bibliographie APA 7 ou Vancouver, annexes numérotées.
- Article : titre, chapô, intertitres, pas de page de garde lourde, références en fin.
- Long rapport professionnel : page de garde, résumé analytique en tête, sommaire, en-têtes et pieds de page, annexes.
- Analyse stratégique : sommaire, figures intégrées (voir `schematiser`), synthèse en tête.
- Étude de cas : format court, encadrés de chiffres clés, verbatims mis en exergue.

## Appliquer la charte graphique

Si une charte graphique existe (`charte-graphique.json`, voir la compétence `charte-graphique`), la valider puis appliquer sa police de titres, sa couleur d'encre et son accent aux titres, filets, légendes et liens du document. Produire les figures avec la même charte. Le corps de texte reste sobre et lisible. La charte graphique règle l'image, le style maison règle les mots, les deux s'appliquent ensemble.

## 3. Intégrer les figures

Si le document comporte des figures, les produire avec `schematiser`, vérifier leur regard critique, puis les insérer numérotées et titrées, avec leur source. Une figure est autonome : elle se comprend sans le texte.

## 4. Formater et vérifier la bibliographie

Passer la bibliographie au script de vérification avant de la couler dans le document.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify-sources.py FICHIER
```

Retirer les paramètres de suivi, supprimer les doublons, contrôler les DOI, appliquer une seule norme de bout en bout (voir `sourcer`).

## 5. Contrôle de forme final

Avant de remettre, repasser le linter de style sur le texte source.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lint-style.py FICHIER
```

Vérifier la liste de contrôle avant publication (voir `reviser/references/checklist-pre-publication.md`) : sections obligatoires présentes, abréviations définies, figures et tableaux titrés et sourcés, pagination, résumé autonome.

## Format de sortie

Le fichier final (Word ou PDF), plus une note de remise courte : genre, format, nombre de pages, norme bibliographique, figures incluses, points de vigilance restants.

## Règles

1. La mise en forme n'altère ni le fond ni les faits.
2. Ne pas finaliser un texte non révisé.
3. Une seule norme bibliographique par document.
4. Toute figure insérée est numérotée, titrée, sourcée et autonome.
5. Respecter le style maison jusque dans les légendes et les notes.
