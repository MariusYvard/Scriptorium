# Corpus utilisateur (bibliothèque personnelle fournie)

Quand l'utilisateur fournit sa propre bibliothèque de références (export BibTeX depuis Zotero ou un autre gestionnaire), ce corpus passe en premier. La recherche externe vient compléter les manques, jamais remplacer ou écarter silencieusement ce qui a été fourni.

## 1. Principe : le corpus d'abord, la recherche comble les manques

1. Détecter la présence d'un corpus fourni (fichier `.bib` ou export Zotero converti en BibTeX).
2. Pré-cribler ce corpus aux mêmes critères que toute source externe : niveau de preuve (`references/hierarchie-preuve.md`), fiabilité et récence (`references/ponderation-sources.md`). La présence d'une référence dans la bibliothèque personnelle de l'utilisateur n'est pas une pré-approbation. Une source de note F reste une source de note F, qu'elle vienne du corpus ou d'une recherche externe.
3. Chercher en complément uniquement sur les sous-thèmes que le corpus ne couvre pas ou couvre insuffisamment (moins de deux sources concordantes sur une affirmation centrale).
4. Fusionner les inclusions internes et externes dans une seule bibliographie, sans marquer de hiérarchie artificielle entre les deux origines une fois le criblage passé.

## 2. Lecture seule

Le fichier fourni par l'utilisateur ne se modifie jamais. Aucune entrée n'est corrigée, reformatée ou supprimée dans le fichier source. Les corrections de forme (nettoyage d'URL, format de citation) s'appliquent uniquement à la sortie produite, jamais au fichier d'origine. En cas de fichier illisible ou de format non reconnu, le repli se fait vers une recherche entièrement externe, avec mention explicite du problème rencontré plutôt qu'un abandon silencieux du corpus.

## 3. Rien d'écarté en silence

Chaque entrée du corpus fourni reçoit un statut explicite. Aucune référence n'est simplement ignorée sans trace.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/citations.py corpus.bib --dedupe
```

Le dédoublonnage par DOI puis par titre (voir `scripts/citations.py`) retire les entrées strictement identiques avant le criblage. Le bloc de traçabilité qui suit couvre ensuite le criblage lui-même.

## 4. Bloc de traçabilité

Format attendu en sortie, avant la synthèse elle-même.

```
Corpus utilisateur (source : nom du fichier, capté le AAAA-MM-JJ)
  Entrées totales : N

Inclus (N1) :
- [clé BibTeX] | niveau de preuve | note | motif d'inclusion

Exclus (N2) :
- [clé BibTeX] | motif (hors sujet / preuve trop faible, note F / périmé / doublon)

Complété par recherche externe (N3) :
- [source] | thème couvert | motif (absent du corpus / insuffisamment couvert)
```

N1 + N2 doit égaler le nombre d'entrées totales du fichier fourni. Un écart signale une entrée perdue en cours de traitement, à corriger avant de continuer.

## 5. Ancre par citation

Chaque entrée du corpus utilisateur suit la même règle d'ancrage que les sources externes : une citation exacte de 25 mots au plus ou une localisation précise (page, section, paragraphe), portée par le champ `note` ou `annote` du BibTeX. Voir `scripts/citations.py` et sa section ancrage. Une entrée du corpus personnel sans ancre reste un signal, pas un motif d'exclusion : l'utilisateur a pu simplement ne pas renseigner ce champ.

## Sources

- Zotero, Creating Bibliographies (export au format BibTeX via Quick Copy). https://www.zotero.org/support/creating_bibliographies (consultée le 2026-07-08)
