# Recherche académique ciblée (arXiv, Semantic Scholar)

Pour un genre académique ou une affirmation qui s'appuie sur la littérature de recherche (papier, préprint, citation), la recherche web générale de `sourcer.md` ne suffit pas : elle ne donne ni la liste structurée des publications sur un sujet, ni leur impact réel. Cette recherche ciblée complète `sourcer.md` sans le remplacer, pour la partie spécifiquement académique d'une commande de preuve.

## Quand l'utiliser

- Le genre retenu est `genre-rapport-scientifique.md`, `genre-article.md`, `genre-dissertation.md`, ou une revue de littérature (`revue-litterature.md`).
- Une affirmation cite ou doit citer un papier de recherche précis (méthode, résultat expérimental, état de l'art d'un domaine).
- L'utilisateur demande explicitement de chercher dans la littérature scientifique, un état de l'art, ou de vérifier si un résultat est repris ailleurs.

Ne pas l'utiliser pour un fait du monde présent (chiffre, acteur en poste, prix) : ça reste `sourcer.md` et la recherche web générale.

## 1. Chercher sur arXiv

Sans clé, API REST ouverte. Utile pour les domaines qu'arXiv couvre (informatique, physique, mathématiques, statistique, quantitatif en général) ; hors de ce périmètre, passer directement à la recherche web générale de `sourcer.md`.

```
curl -s "https://export.arxiv.org/api/query?search_query=all:TERME&max_results=10&sortBy=relevance"
curl -s "https://export.arxiv.org/api/query?search_query=ti:%22titre+exact%22&max_results=5"
curl -s "https://export.arxiv.org/api/query?id_list=2402.03300"
```

Réponse en Atom XML. Extraire pour chaque résultat : identifiant, titre, auteurs, date de publication, catégorie, résumé, lien PDF. Un résumé (`<summary>`) qui contient les mots « withdrawn » ou « retracted » signale un papier retiré : ne jamais le citer comme preuve valide sans le signaler explicitement comme retiré.

Un identifiant arXiv porte une version (`1706.03762v3`). Toujours conserver le suffixe de version effectivement lu dans la citation : une version ultérieure peut changer substantiellement le contenu, et une ancre sur une version non précisée n'est pas vérifiable après une mise à jour du papier.

## 2. Évaluer l'impact réel (Semantic Scholar)

arXiv ne donne aucune donnée de citation. Semantic Scholar Graph API, sans clé pour un usage basique (1 requête/seconde), complète le tri par fiabilité de `ponderation-sources.md` avec une mesure d'impact réel.

```
curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:2402.03300?fields=title,authors,year,citationCount,influentialCitationCount,referenceCount,isOpenAccess,externalIds"
```

Champs utiles : `citationCount` (nombre brut de citations), `influentialCitationCount` (citations jugées structurantes par l'algorithme de Semantic Scholar, un sous-ensemble plus significatif que le brut), `year` (recouper avec le facteur de récence de `ponderation-sources.md`).

Une citation élevée n'élève jamais mécaniquement le niveau de preuve de `hierarchie-preuve.md` : un papier très cité mais méthodologiquement faible reste noté sur sa méthode, pas sur son score de citation. Le compte de citations sert à trois choses, seulement :

1. Distinguer un résultat consensuel (des dizaines de citations indépendantes qui le reprennent sans contestation) d'un résultat isolé encore non répliqué.
2. Prioriser, à niveau de preuve égal, le papier de référence d'un domaine plutôt qu'une variante peu reprise.
3. Signaler un papier très récent (moins de 6 mois) à zéro citation comme non encore éprouvé par les pairs, pas comme faible en soi — la fenêtre de citation n'a simplement pas eu le temps de s'ouvrir.

## 3. Trouver l'état de l'art et les travaux liés

```
curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:2402.03300/references?fields=title,year,citationCount&limit=20"
curl -s "https://api.semanticscholar.org/graph/v1/paper/arXiv:2402.03300/citations?fields=title,year,citationCount&limit=20"
```

`references` donne ce que le papier cite (utile pour reconstruire une chronologie ou trouver les travaux fondateurs). `citations` donne qui l'a cité depuis (utile pour vérifier qu'un résultat n'a pas été depuis contredit ou dépassé). Avant de citer un papier comme état de l'art actuel, vérifier dans ses citants les plus récents qu'aucun ne le supplante explicitement ; sinon la référence est datée et doit être présentée comme telle.

## 4. Vers la bibliographie

Une fois un papier retenu, le faire entrer dans le pipeline BibTeX standard plutôt que de le citer à la main :

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/citations.py --arxiv 2402.03300
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/citations.py --doi 10.1145/xxxxx
```

Ceci émet une entrée BibTeX prête à coller, qui rejoint ensuite le même formatage, la même déduplication et la même vérification d'ancre que toute autre source (voir `sourcer.md`, sections 7-8, et `scripts/citations.py`).

## 5. Chaîne de version (prépublication → version évaluée)

Un même travail existe parfois sous plusieurs formes : préprint arXiv, actes de colloque, version revue en revue. `revue-litterature.md` section 3 en tient déjà compte pour la synthèse multi-sources ; la même règle s'applique ici à une source unique. Reconstruire la chaîne dans l'ordre de publication réel. Une chaîne incohérente (le préprint daté après la version revue) est un signal à corriger avant de citer, pas un détail : soit la date d'un des deux maillons est fausse, soit ce ne sont pas les mêmes versions.

## Règles

1. Ne jamais citer un résumé de recherche seul comme preuve d'un contenu : le résumé dit ce que le papier annonce, pas ce qu'il démontre. Lire le corps (`web_extract` sur le PDF) avant de sourcer une affirmation précise.
2. Conserver le suffixe de version arXiv effectivement lu.
3. Vérifier le statut de retrait avant de citer.
4. Le compte de citations informe la priorisation et le contexte, jamais le niveau de preuve individuel d'une source.
5. Un résultat sans réplication indépendante reste au niveau de preuve d'une étude isolée (`hierarchie-preuve.md`, niveau 3 ou 5 selon le type), quel que soit son nombre de citations.

## Sources

- arXiv API User's Manual. https://info.arxiv.org/help/api/user-manual.html (consultée le 2026-08-15)
- Semantic Scholar Academic Graph API, documentation des champs. https://api.semanticscholar.org/api-docs/graph (consultée le 2026-08-15)
