---
name: livrer
description: >
  Met en forme le livrable final et le décline par canal. Deux sous-commandes. document : mise en forme aboutie en Word, PDF ou HTML selon les conventions du genre (page de garde, sommaire, texte justifié, bibliographie formatée, annexes, résumé), CSS dérivé de la charte graphique pour le HTML "mets en forme", "génère le Word", "produis le PDF", "exporte en HTML", "finalise le document". decliner : tirer d'un document validé plusieurs formats à faits et charte constants (présentation, résumé d'une page, abstract, post professionnel, communiqué) "décline ce rapport", "version courte", "résumé exécutif", "fais-en un deck", "un abstract". Sert le chercheur, l'ingénieur et l'analyste géopolitique.
metadata:
  version: "0.6.0"
---

# Livrer (mettre en forme, décliner)

Transforme un texte validé en livrable abouti, puis le décline par canal. N'intervient qu'après la révision : mettre en forme un texte non validé revient à polir un brouillon.

## Sous-commandes

Si une action est passée en argument (par exemple `decliner`), suivre directement sa section. Sinon, déduire l'action de la demande.

- document : mise en forme aboutie en Word, PDF ou HTML selon les conventions du genre (page de garde, sommaire, texte justifié, bibliographie formatée, annexes numérotées, résumé ou abstract). Charger `references/document.md`.
- decliner : tirer d'un document validé plusieurs formats à faits et charte constants (présentation, résumé d'une page, abstract, post professionnel, communiqué). Charger `references/decliner.md`.

## Formats de sortie

Le format natif de travail est le Markdown. La finalisation produit un Word (.docx via le skill `docx`), un PDF (skill `pdf`), un HTML autonome (CSS dérivé de la charte graphique, figures SVG embarquées, feuille d'impression) ou une présentation (.pptx via le skill `pptx`). Le HTML offre la plus grande marge de mise en forme et respecte la charte graphique au plus près, il sert aussi de source pour un PDF fidèle. Voir `references/document.md` pour le détail par format.

## Charte et style

Tout livrable respecte le style maison (voir `produire`, action style) et, si elle est définie, la charte graphique (voir `produire`, action charte). Les faits et la terminologie restent constants d'un canal à l'autre.

## Trois publics

Le canal suit le public : article et résumé analytique pour le chercheur, rapport technique et note de synthèse pour l'ingénieur, note décisionnelle et briefing pour l'analyste géopolitique. Le fond validé ne change pas, seul le format s'adapte.

## Règles

1. Ne mettre en forme qu'un texte dont la révision a rendu un verdict "Prêt".
2. Garder les faits, les chiffres et la terminologie identiques à la version validée.
3. Joindre une note de version courte qui liste ce qui a été vérifié et ce qui reste ouvert.
