# Contrôle d'originalité (plagiat et auto-plagiat)

## 1. Principe et limites

Ce protocole est un contrôle de vraisemblance, pas un outil professionnel de détection de plagiat : il n'a pas accès à un corpus fermé de manuscrits comme en utilisent les services spécialisés, seulement à la recherche web publiquement indexée. Un résultat "aucune correspondance trouvée" signifie "non trouvé dans le web indexé accessible au moment du contrôle", jamais "prouvé original". Cette limite se déclare dans le rapport, elle ne se tait pas.

## 2. Échantillonnage de phrases caractéristiques

Extraire une à deux phrases caractéristiques par paragraphe : une formulation assez spécifique pour ne pas être un lieu commun, ni trop longue pour rester citable telle quelle dans une recherche. Taux d'échantillonnage :

- 30% des paragraphes en pré-revue.
- 50% des paragraphes en contrôle final.
- 100% des paragraphes ajoutés ou modifiés depuis la version précédente, identifiés par `scripts/diff-versions.py`.

## 3. Recherche web en deux passes

D'abord la phrase entre guillemets, qui capte le verbatim exact. Ensuite la même phrase sans guillemets, qui capte la paraphrase proche. Les deux passes sont nécessaires : la recherche entre guillemets seule manque toute reformulation. La recherche sans guillemets seule noie le signal dans des résultats trop généraux.

## 4. Cinq grades

- Original : aucune correspondance substantielle trouvée.
- Connaissance commune : la formulation recoupe un fait ou une expression largement partagée (définition de manuel, chiffre officiel connu), sans source unique identifiable.
- Paraphrase : le contenu recoupe une source précise mais la formulation est réellement reformulée.
- Correspondance proche : la formulation suit de très près une source sans être identique mot pour mot.
- Verbatim : vingt mots consécutifs ou plus identiques à une source, sans guillemets ni attribution.

## 5. Auto-plagiat distinct de l'auto-citation

Citer son propre travail antérieur en le reformulant et en l'attribuant est une auto-citation légitime. Recopier mot pour mot un passage de son propre travail antérieur est un auto-plagiat, même quand la source est citée en référence : la mention en bibliographie couvre la reprise de l'idée, pas la reprise verbatim du texte. Distinguer les deux avant de juger un passage repéré.

## 6. Signaux d'écriture générée

Des indices de texte généré par IA (fluidité uniforme, transitions formulaïques, absence de détail concret) ne sont jamais probants isolément. Un seul signal ne suffit à rien. Deux signaux ou plus justifient un simple signalement pour vérification humaine, jamais une conclusion tranchée sur l'origine du texte. Pour le détail des tics et leur correction, voir la sous-commande `humaniser` et `scripts/ai-fingerprint.py`.

## 7. Sévérité et action

- Verbatim ou correspondance proche sur un passage qui porte une affirmation centrale : critique, à corriger avant publication.
- Paraphrase proche répétée sur plusieurs passages : majeur, à reformuler.
- Connaissance commune signalée par erreur ou correspondance isolée sur un passage secondaire : mineur, à écarter du rapport ou à noter sans bloquer.

## Format de sortie

```
| Paragraphe | Phrase échantillonnée | Grade | Source trouvée | Action |
| --- | --- | --- | --- | --- |
```

Taux d'échantillonnage appliqué : [30% pré-revue / 50% final / 100% sur les paragraphes modifiés]
Signaux d'écriture générée : [aucun / n signaux, jamais concluant seul]
Verdict : [aucun problème / à corriger avant publication / à reformuler]

## Sources

- COPE / BioMed Central. Text recycling guidelines for editors. https://publicationethics.org/guidance/endorsed-guidance/text-recycling-guidelines-editors (consultée le 2026-07-08)
