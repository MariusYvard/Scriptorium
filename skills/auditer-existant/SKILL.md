---
name: auditer-existant
description: >
  Audite un document déjà rédigé (PDF, Word ou Markdown) en extrayant son texte puis en passant tout le contrôle déterministe et le scorecard dessus. À utiliser quand l'utilisateur demande "audite ce PDF", "note ce rapport", "passe ce document au scorecard", "audite mon Word", "que vaut ce document existant" ou fournit un document fini à évaluer.
metadata:
  version: "0.1.0"
---

# Auditer un document existant

Évaluer un document déjà produit, pas seulement ceux que l'on rédige. Extraire le texte, puis lancer l'audit consolidé.

## 1. Extraire le texte

Selon le format.

- Markdown ou texte : lire directement.
- PDF : extraire le texte avec le skill `pdf` (ou l'outil `pdftotext` si disponible).
- Word : extraire le texte avec le skill `docx`.

Sauvegarder le texte extrait dans un fichier `.md` de travail. Conserver la structure (titres, tableaux) autant que possible, l'audit s'appuie dessus.

## 2. Lancer l'audit consolidé

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/audit-doc.py texte-extrait.md
```

Le rapport réunit le scorecard sur 100, les signaux d'empreinte IA, les redites et duplications, et l'audit des tableaux. Pour le détail d'un axe, lancer le script correspondant (`scorecard.py`, `traceability.py`, `numbers.py`, etc.).

## 3. Restituer

Présenter le scorecard avec le détail par axe, puis les constats complémentaires (empreinte IA, cohérence, tableaux), classés par priorité. Proposer les correctifs, sans réécrire le document sauf demande.

## Format de sortie

Le rapport d'audit consolidé (note sur 100, axes, signaux), plus une courte liste d'actions prioritaires. Si l'utilisateur le souhaite, enchaîner vers `reviser` pour corriger.

## Règles

1. L'extraction préserve la structure (titres, tableaux, références) autant que possible.
2. L'audit ne modifie pas le document, il l'évalue.
3. Le scorecard est déterministe et reproductible, la note ne dépend pas de l'humeur du modèle.
4. Classer les constats par priorité, du critique au mineur.
