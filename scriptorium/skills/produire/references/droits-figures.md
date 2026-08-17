# Droits de réutilisation d'une figure tierce

Reproduire dans un document une figure tirée d'une publication pose deux questions distinctes. Citer la source règle l'honnêteté intellectuelle. Le droit de reproduction est une autre affaire : une figure est une oeuvre protégée indépendamment du texte de l'article qui la porte ; la permission de la lire n'emporte pas la permission de la republier. Cette référence décrit ce que les licences déclarent. Elle ne vaut pas avis juridique : le contrat signé avec une revue, la politique d'un employeur ou le droit applicable peuvent en décider autrement.

## Quand la question se pose

- Une figure, une photographie, une carte ou une capture d'écran extraite d'un article, d'un rapport ou d'un site.
- Un tableau mis en forme par son auteur : la présentation éditoriale est protégée, les valeurs brutes non.
- Une figure recadrée, retouchée, traduite ou recolorée à partir d'un original tiers.

La question ne se pose pas pour une figure produite par l'auteur du document, ni pour un graphique tracé à partir de valeurs relevées dans une source.

## Citer n'est pas obtenir le droit de reproduire

Une référence bibliographique désigne l'origine d'un fait. Elle ne transfère aucun droit patrimonial. Un document dont chaque figure porte sa source peut rester en infraction si aucune ne porte de licence permissive ni d'autorisation écrite.

## Familles de licences

| Famille | Reproduction | Adaptation | Usage commercial | Verdict |
| --- | --- | --- | --- | --- |
| CC0, domaine public | oui | oui | oui | `reutilisable avec attribution` |
| CC BY | oui | oui | oui | `reutilisable avec attribution` |
| CC BY-SA | oui | oui | oui | `reutilisable sous conditions` |
| CC BY-NC | oui | oui | non | `reutilisable sous conditions` |
| CC BY-ND | oui | non | oui | `reutilisable sous conditions` |
| CC BY-NC-ND | oui | non | non | `reutilisable sous conditions` |
| Tous droits réservés | sur accord | sur accord | sur accord | `autorisation requise` |
| Aucune licence lisible | indéterminée | indéterminée | indéterminée | `licence inconnue` |

Trois clauses commandent le reste. SA impose au document dérivé la licence de la figure, contrainte lourde pour un mémoire ou un livrable client. NC ferme l'usage commercial, ce qui vise un livre vendu, un support de formation payante ou un rapport facturé. ND interdit la distribution du matériel modifié : un recadrage, une retouche ou la traduction d'une légende incrustée sortent de la licence, alors qu'un simple changement de format ne crée pas d'adaptation. CC0 et le domaine public n'exigent pas d'attribution : la ligne de crédit reste due au titre du sourçage, pas au titre de la licence. `licence inconnue` ne vaut ni interdiction, ni permission ; une absence d'information reste une absence d'information, à lever avant diffusion.

## Le cas ordinaire d'une revue sur abonnement

Un article d'une revue sur abonnement n'est pas sous licence ouverte. Crossref expose pourtant souvent un tableau `license` pour ces articles, rempli de conditions propres à l'éditeur (fouille de textes et de données, licence utilisateur). Ces conditions couvrent l'exploration automatisée du texte, pas la republication d'une figure dans un autre document. Un tableau `license` rempli ne vaut donc pas licence de réutilisation.

## Demander une autorisation

Pour un mémoire, une thèse ou un article, la demande passe par le service des droits de l'éditeur (rubrique Permissions ou Rights, souvent servie par le guichet RightsLink de Copyright Clearance Center).

1. Identifier le titulaire : l'éditeur dans la majorité des cas, l'auteur quand il a conservé ses droits, une agence pour une photographie.
2. Décrire la figure sans ambiguïté : DOI de l'article, numéro de figure, page.
3. Décrire l'usage : support (mémoire, thèse, article), diffusion (dépôt institutionnel, tirage papier), langue, tirage, caractère commercial ou non.
4. Indiquer les modifications prévues : recadrage, redessin, traduction de la légende.
5. Conserver la réponse écrite avec sa date et sa référence de dossier, puis la consigner dans le registre.

Les délais vont de la réponse automatique immédiate à quelques semaines. Une demande déposée après la rédaction bloque la remise ; la déposer au moment où la figure est retenue coûte moins cher.

## L'exception de courte citation en droit français

L'article L122-5 du code de la propriété intellectuelle autorise, sous réserve que le nom de l'auteur et la source soient clairement indiqués, "les analyses et courtes citations justifiées par le caractère critique, polémique, pédagogique, scientifique ou d'information de l'oeuvre à laquelle elles sont incorporées". Le texte vise des citations courtes. Une figure reproduite intégralement n'est courte à aucun titre : elle est l'oeuvre entière, pas un extrait. La voie est donc étroite pour une image.

Le même article porte une exception d'illustration de la recherche (3° e), assortie de conditions cumulatives : public composé majoritairement de chercheurs concernés par la recherche en cause, aucune publication ni diffusion hors de ce public, aucune exploitation commerciale, rémunération forfaitaire négociée. Un mémoire déposé en ligne sort de ce cadre. L'article ferme par une clause générale : les exceptions ne peuvent porter atteinte à l'exploitation normale de l'oeuvre ni causer un préjudice injustifié aux intérêts légitimes de l'auteur.

## Redessiner depuis les données

Les données ne sont pas protégeables, leur mise en forme l'est. Relever les valeurs publiées (texte, tableau, données supplémentaires), puis tracer la figure avec la charte du document, produit une figure propre à l'auteur. La mention "d'après les données de X" garde la traçabilité intellectuelle sans emprunter d'oeuvre. Cette voie est la plus sûre quand le verdict est `autorisation requise` ou `licence inconnue`. `scripts/figures.py` couvre six types de figures de données : `courbe`, `nuage`, `histogramme`, `boite`, `flux`, `prisma`. Formats de données dans `references/figures-catalogue.md`. Deux réserves. Un décalque du rendu d'origine (mêmes couleurs, même disposition, mêmes ornements) reproduit la partie protégée. Une base de données peut porter un droit propre sur l'extraction d'une partie substantielle de son contenu, distinct du droit d'auteur.

## Registre des figures empruntées

Un document qui emprunte huit figures porte la liste de ses crédits, comme il porte sa bibliographie. Le registre est un fichier JSON déclaratif, une entrée par figure.

```json
{
  "document": "Mémoire de stage",
  "figures": [
    {"id": "fig-3", "libelle": "Figure 3", "titre": "Courbe de charge du réseau",
     "auteur": "Nguyen, T. et Roe, D.", "source": "Energy Policy",
     "doi": "10.1016/j.enpol.2023.113600",
     "licence": "https://creativecommons.org/licenses/by/4.0/",
     "verdict": "reutilisable avec attribution", "modifications": "recadrée",
     "autorisation": {"etat": "obtenue", "date": "2026-08-01",
                      "reference": "RightsLink 5012345"}}
  ]
}
```

`etat` prend quatre valeurs : `non demandee`, `demandee`, `obtenue`, `refusee`. Une figure sans source, un identifiant dupliqué, un verdict que la licence déclarée contredit, un recadrage sous licence ND ou une autorisation refusée rendent le registre invalide.

## Ligne d'attribution

Les licences 4.0 exigent le nom du créateur, la notice de droit d'auteur, la mention de la licence, la notice de garantie, un lien vers le matériel et l'indication des modifications. Les versions antérieures exigent en plus le titre. La forme recommandée par Creative Commons réunit titre, auteur, source, licence, ce qui couvre les deux cas. Exemple :
`Figure 3 : "Courbe de charge du réseau", Nguyen, T. et Roe, D., Energy Policy (https://doi.org/10.1016/j.enpol.2023.113600), sous licence CC BY 4.0. Figure modifiée (recadrée).`

## Contrôle déterministe

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-droits.py licence --doi 10.xxxx/yyyy --reseau
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-droits.py registre registre-figures.json --strict
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-droits.py credits registre-figures.json --sortie latex
```

Le script résout la licence déclarée par Crossref puis par OpenAlex, classe sur les quatre verdicts, écrit la ligne d'attribution en texte, en HTML et en LaTeX, propose le redessin quand la reproduction n'est pas acquise puis valide le registre. Sans `--reseau`, aucun index n'est interrogé : la licence reste à renseigner à la main plutôt que supposée. Le script rapporte ce que la licence déclare, il ne prononce pas la légalité d'un usage.

## Récupérer et identifier la figure

Cette référence traite de ce que la licence permet. Obtenir le fichier et savoir de quelle figure il s'agit est l'affaire de `scripts/emprunts.py`, décrite dans `references/image.md`.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/emprunts.py localiser --doi 10.xxxx/yyyy --reseau
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/emprunts.py inventorier SOURCE.pdf --out images/
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/emprunts.py chainer --doi 10.xxxx/yyyy --registre registre-figures.json --reseau
```

`localiser` donne l'état d'accès ouvert et l'adresse du PDF ouvert. `inventorier` apparie chaque image extraite à la légende de sa page, avec une confiance graduée qui interdit d'affirmer un appariement douteux. `chainer` enchaîne les deux, appelle `check-droits.py` et écrit l'entrée du registre décrite plus haut.

La récupération ne va chercher un fichier que là où l'index le déclare ouvert. Aucun contrôle d'accès n'est contourné, aucun identifiant n'est présenté, aucune adresse n'est devinée. Une source hors accès ouvert produit un refus nommé qui renvoie vers la demande d'autorisation ci-dessus : un article sous abonnement se demande à son éditeur.

## Sources

- Code de la propriété intellectuelle, article L122-5 : https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000037388886 (consulté le 2026-08-17)
- Creative Commons, contrat CC BY-ND 4.0 et ses notes d'attribution : https://creativecommons.org/licenses/by-nd/4.0/ (consulté le 2026-08-17)
- Crossref REST API, tableau `license` d'un article : https://api.crossref.org/works/10.1371/journal.pone.0000308 (réponse consultée le 2026-08-17)
- OpenAlex, champs `open_access` et `best_oa_location` : https://api.openalex.org/works/doi:10.1371/journal.pone.0000308 (réponse consultée le 2026-08-17)
