# Intégrité des sources (vérification et anti-fabrication)

Contrôler qu'une référence citée existe réellement, correspond bien à ce qu'elle prétend être et ne date pas d'un moment incompatible avec l'affirmation qu'elle soutient. Trois défaillances distinctes à ne pas confondre : la source n'existe pas, la source existe mais dit autre chose que ce qu'on lui fait dire, la source existe et dit vrai mais à un moment qui rend l'affirmation anachronique. Ce fichier couvre les deux premières. La troisième est traitée par `references/hierarchie-preuve.md` (fiabilité) et par `check-temporel.py` (chronologie).

## 1. Principe

Fait précis et vérifié, ou rien. Une référence qui ne se vérifie pas ne se cite pas : soit le mécanisme s'écrit sans elle, soit une source alternative vérifiée la remplace. Un résultat ambigu ne se reclasse jamais en positif par confort. La dégradation se fait par omission (un index ne répond pas, il est ignoré) et jamais par invention (un index qui ne répond pas ne devient pas un « non trouvé » ferme).

## 2. Triangulation multi-index

Une référence isolée dans un seul catalogue est un indice, pas une preuve. Trois index bibliographiques, interrogés indépendamment, corroborent ou infirment l'existence d'un travail cité.

| Index | Base | Accès constaté le 2026-07-08 |
| --- | --- | --- |
| Crossref | api.crossref.org | Ouvert, sans clé. `GET /works/{doi}` pour un DOI, `GET /works?query.bibliographic=...` pour une recherche par titre et auteurs. |
| Semantic Scholar (Graph API) | api.semanticscholar.org/graph/v1 | Ouvert, sans clé, débit limité (usage poli recommandé). `GET /paper/DOI:{doi}` ou `GET /paper/ARXIV:{id}` pour un identifiant direct. |
| OpenAlex | api.openalex.org | Clé API gratuite désormais exigée (évolution constatée par rapport aux versions antérieures de la documentation, qui décrivaient un accès anonyme à débit réduit). Un lookup par identifiant reste gratuit une fois la clé obtenue ; sans clé, l'index est ignoré et compté comme non consulté, pas comme un échec de la référence. |

Chaque index est interrogé avec un délai d'attente court et un User-Agent identifiant l'outil. Une panne réseau, un délai dépassé ou une clé absente retirent l'index du calcul sans faire pencher le verdict d'un côté ou de l'autre. Deux index ou plus consultés avec succès qui rapportent des titres concordants pour le même identifiant renforcent la confiance ; des titres discordants entre index sur le même identifiant sont eux-mêmes un signal à faire remonter.

### Similarité de titre

Le rapprochement entre le titre cité et le titre retourné par un index se mesure par `difflib.SequenceMatcher` (bibliothèque standard), seuil de concordance à 0,70. Sous ce seuil, les titres comptent comme discordants. Ce seuil reprend la convention documentée par plusieurs protocoles d'intégration académique à des index bibliographiques, ici appliquée avec l'outil de comparaison de la bibliothèque standard plutôt qu'une distance de Levenshtein dédiée.

## 3. Verdicts d'existence d'une référence

Quatre valeurs, jamais un simple vrai ou faux.

- Vérifié : au moins un index résout l'identifiant, et si plusieurs index répondent, leurs titres concordent (similarité >= 0,70).
- Plausible : un élément de la référence est confirmé (l'auteur existe, la revue existe) sans que le travail précis cité ne soit lui-même retrouvé.
- Invérifiable : aucun index consulté ne confirme ni n'infirme, ou les index consultés se contredisent entre eux. Compte comme un échec de la porte de qualité, pas comme une case neutre.
- Fabriqué : un identifiant formellement valide (DOI bien formé, par exemple) résout vers un travail différent de celui cité, ou plusieurs index indépendamment joignables répondent explicitement qu'ils ne connaissent pas la référence. Un verdict fabriqué signale un cas à trancher par un humain, il ne constitue pas à lui seul une preuve définitive.

La zone grise (« difficile à vérifier ») ne se range jamais dans vérifié ou plausible par défaut. Elle reste invérifiable.

## 4. Taxonomie des citations fabriquées

Cinq familles utiles comme grille de lecture pour repérer une référence suspecte, qu'elle vienne d'une relecture humaine ou d'un contrôle outillé.

1. Fabrication totale : titre, auteurs et revue n'existent nulle part, invention de bout en bout.
2. Auteur ou venue plausible : le nom d'auteur ou le nom de revue cité existe réellement, mais jamais associé à ce titre précis.
3. Hallucination incomplète : un élément central manque au point de rendre la référence non vérifiable (pas d'année, pas de volume, pas de page), sans qu'aucun élément fourni ne soit lui-même faux.
4. Mélange de sources réelles : deux ou trois références existantes réellement sont recombinées en une seule (les auteurs d'un travail, le titre d'un autre, la revue d'un troisième).
5. Hallucination subtile : la référence ressemble fortement à une source réelle du même auteur ou de la même revue, avec une année, un volume ou une page légèrement décalés. La plus difficile à détecter par un contrôle mécanique, elle exige souvent la comparaison directe au texte de la source retrouvée.

Cette classification reste un outil de triage. Un verdict de fabrication engage toujours une vérification humaine avant d'être traité comme acquis.

## 5. Signaux de contamination

Un signal de contamination n'est jamais une preuve de fabrication à lui seul, seulement une raison de regarder de plus près.

- Preprint récent (serveur connu : arXiv, bioRxiv, medRxiv, SSRN, Research Square) absent de tous les index consultés avec succès. Un travail très récent peut simplement ne pas avoir encore été indexé ailleurs : le signal invite à vérifier si une version revue existe, pas à rejeter la référence.
- Référence à une source rétractée. Le croisement se fait contre la base de données Retraction Watch, hébergée par Crossref et mise à jour quotidiennement (voir Sources). Une source rétractée cité sans mention de la rétractation est un problème indépendant de son existence : la référence existe bel et bien, mais son usage comme preuve doit être révisé ou abandonné.

## 6. Verdicts de vérification de fidélité

Distincts des verdicts d'existence : ici, la référence existe et la question est de savoir si la citation représente fidèlement ce qu'elle dit. Cinq valeurs.

- Vérifié : le passage cité correspond au contenu réel de la source.
- Distorsion mineure : paraphrase qui préserve le sens d'origine.
- Distorsion majeure : simplification excessive ou changement de sens par rapport à la source.
- Invérifiable : la source ne contient pas l'information qu'on lui attribue.
- Accès payant : la source existe mais son contenu intégral n'est pas accessible pour vérifier la citation.

Un contrôle exige zéro distorsion majeure et zéro invérifiable pour passer. Une distorsion mineure se signale mais n'empêche pas à elle seule un verdict favorable.

## 7. Chronologie des sources

Chaque source porte une date à une précision déclarée : jour, mois, année, intervalle ou inconnue. Ne jamais prêter une précision que la source ne fournit pas (une année seule reste une année, pas une date arbitraire du 1er janvier).

Un même travail voyage parfois sous plusieurs formes successives : prépublication (preprint), présentation à des actes de colloque, puis version revue en revue. Ces étapes portent chacune leur propre date, et la chaîne complète doit rester cohérente (le preprint précède ou coïncide avec la version revue, jamais l'inverse). Une chaîne incohérente est elle-même un signal de contamination (voir section 5) ou une erreur de citation à corriger.

La garde anti-anachronisme (dates futures présentées comme passées, ordre causal inversé par les dates, langage à péremption non ancré) est un contrôle déterministe séparé : voir `check-temporel.py` et son usage documenté dans `agents/verificateur-faits.md`.

## 8. Outillage

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify-sources.py FICHIER --reseau
```

`--reseau` déclenche la triangulation Crossref, OpenAlex et Semantic Scholar sur les DOI trouvés dans le texte, calcule le verdict d'existence par référence et signale les préprints récents absents de tous les index consultés. Sans `--reseau`, le script se limite à son comportement existant (nettoyage d'URL, doublons, syntaxe des DOI), hors ligne.

## Sources

- Documentation d'authentification de l'API OpenAlex (clé requise, coûts par opération). https://developers.openalex.org/api-reference/authentication (consultée le 2026-07-08)
- Retraction Watch Database, annonce de l'ouverture des données via Crossref, 12 septembre 2023 (édition du 10 octobre 2024 sur le point d'accès en vigueur). https://www.crossref.org/blog/news-crossref-and-retraction-watch/
- Dépôt de données Retraction Watch tenu par Crossref, mise à jour quotidienne. https://gitlab.com/crossref/retraction-watch-data
- Lu, C. et al. (2026). Towards end-to-end automation of AI research. Nature, 651, 914-919. https://doi.org/10.1038/s41586-026-10265-5
