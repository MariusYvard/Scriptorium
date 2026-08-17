---
name: livrer
description: >
  Met en forme le livrable final et le décline par canal. Deux sous-commandes. document : mise en forme aboutie en Word, PDF, HTML ou LaTeX selon les conventions du genre (page de garde, sommaire, texte justifié, bibliographie formatée, annexes, résumé), CSS et préambule LaTeX dérivés de la charte graphique, exigences de la destination vérifiées, gabarit imposé rempli plutôt que régénéré, logos placés selon leur registre, contrôle de fuites sur le fichier final avant envoi "mets en forme", "génère le Word", "produis le PDF", "exporte en HTML", "compile en LaTeX", "finalise le document", "remplis le modèle imposé". decliner : tirer d'un document validé plusieurs formats à faits et charte constants (présentation, poster, résumé d'une page, résumé bilingue FR/EN, abstract, post professionnel, communiqué) "décline ce rapport", "version courte", "résumé exécutif", "fais-en un deck", "un abstract". Sert le chercheur, l'ingénieur et l'analyste géopolitique.
metadata:
  version: "0.12.0"
---

# Livrer (mettre en forme, décliner)

Transforme un texte validé en livrable abouti, puis le décline par canal. N'intervient qu'après la révision : mettre en forme un texte non validé revient à polir un brouillon.

## Sous-commandes

Si une action est passée en argument (par exemple `decliner`), suivre directement sa section. Sinon, déduire l'action de la demande.

- document : mise en forme aboutie en Word, PDF, HTML ou LaTeX selon les conventions du genre (page de garde, sommaire, texte justifié, bibliographie formatée, annexes numérotées, résumé ou abstract), exigences de la destination vérifiées avant l'envoi. Charger `references/document.md`.
- decliner : tirer d'un document validé plusieurs formats à faits et charte constants (présentation, poster, résumé d'une page, résumé bilingue FR/EN, abstract, post professionnel, communiqué). Charger `references/decliner.md`.

## Gabarit imposé

Quand la destination fournit son propre modèle (rapport de stage d'une école, mémoire d'un laboratoire, feuille de style d'une conférence, charte d'un client), ce modèle l'emporte sur les gabarits internes du plugin. Le geste change alors : au lieu de générer un fichier neuf, remplir le gabarit fourni, ce qui préserve son filigrane, sa numérotation liée et son thème de couleurs.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gabarit.py inventorier MODELE.docx --out gabarit-inventaire.json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gabarit.py remplir gabarit-inventaire.json document.md --out livrable.docx --logo logo-ecole.png
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/gabarit.py comparer gabarit-inventaire.json livrable.docx
```

Les logos suivent leur propre registre (`produire`, action logos) : `logos.py placer` rend le fragment pour le HTML et le LaTeX, `gabarit.py remplir --logo` fait l'insertion en Word. Un conflit entre le gabarit de la destination et la charte graphique interne se signale à l'auteur, il ne s'arbitre pas en silence. Détail dans `produire`, actions gabarit et logos.

## Formats de sortie

Le format natif de travail est le Markdown. La finalisation produit un Word (.docx via le skill `docx`), un PDF (skill `pdf`), un HTML autonome (CSS dérivé de la charte graphique, figures SVG embarquées, feuille d'impression), un document LaTeX (gabarit `assets/gabarit-rapport.tex`, préambule couleurs et polices émis par `theme.py --format latex`, compilation xelatex quand elle est disponible) ou une présentation (.pptx via le skill `pptx`). Le HTML offre la plus grande marge de mise en forme et respecte la charte graphique au plus près ; le LaTeX donne le rendu le plus abouti pour un rapport scientifique ou technique dense (encadrés sémantiques, macros statistiques). Le poster passe par `assets/gabarit-poster.tex`. Voir `references/document.md` pour le détail par format.

## Contrôle avant envoi

Un livrable qui part chez un client, une école ou une revue emporte les traces de sa fabrication : auteur d'origine, dernière personne à avoir enregistré, organisation, commentaires et modifications suivies oubliés, notes du présentateur, chemins locaux. Passer le fichier final, pas le Markdown source.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-fuites.py livrable.docx --auteur "Prenom Nom"
```

Le script inspecte et ne nettoie pas ; traiter les constats confirmés avant l'envoi. Détail dans `references/document.md`.

## Charte et style

Tout livrable respecte le style maison (voir `produire`, action style) et, si elle est définie, la charte graphique (voir `produire`, action charte). Les faits et la terminologie restent constants d'un canal à l'autre.

## Trois publics

Le canal suit le public : article et résumé analytique pour le chercheur, rapport technique et note de synthèse pour l'ingénieur, note décisionnelle et briefing pour l'analyste géopolitique. Le fond validé ne change pas, seul le format s'adapte.

## Règles

1. Ne mettre en forme qu'un texte dont la révision a rendu un verdict "Prêt".
2. Garder les faits, les chiffres et la terminologie identiques à la version validée.
3. Joindre une note de version courte qui liste ce qui a été vérifié et ce qui reste ouvert.
