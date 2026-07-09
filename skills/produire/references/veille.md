# Veille (surveillance documentaire d'un sujet)

Mettre en place une veille sur un sujet déjà sourcé, pour repérer les nouveautés, les rétractations et les glissements de terminologie qui rendraient une source ou une affirmation périmée après la rédaction. Cette compétence ne surveille rien en tâche de fond : elle configure des requêtes que l'utilisateur exécute lui-même à la cadence choisie et structure le digest qu'il en tire.

## 1. Requêtes de veille par plateforme

Configurer une requête par plateforme pertinente au sujet, en réutilisant les mots-clés et les auteurs déjà identifiés au sourcing. Patrons d'URL vérifiés à la date indiquée en Sources, à adapter au sujet plutôt qu'à recopier tels quels.

| Plateforme | Mécanisme | Patron vérifié | Limite constatée |
| --- | --- | --- | --- |
| arXiv (préprints) | Flux RSS ou Atom par catégorie, mis à jour chaque jour à minuit heure de l'Est | `https://rss.arxiv.org/rss/CATEGORIE` (Atom : `/atom/CATEGORIE`), catégories combinables avec un signe plus (`cs.AI+q-bio.NC`), limite de 2000 résultats | Flux par catégorie entière, pas par requête de mots-clés : filtrer le résultat après réception |
| PubMed (NCBI, biomédical) | E-utilities, `esearch.fcgi` avec `usehistory=y` pour rejouer une recherche sauvegardée | Base `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`, ex. `esearch.fcgi?db=pubmed&term=REQUETE&sort=date&retmax=20` | Débit limité à 3 requêtes/seconde sans clé (10 avec une clé API NCBI gratuite) ; paramètres `tool` et `email` à fournir par courtoisie dès un usage régulier |
| Google Scholar | Alerte email seulement, aucun flux RSS ni API publique | Depuis une page de résultats de recherche, icône enveloppe dans la colonne de gauche ; depuis un profil d'auteur, bouton "Suivre" puis "Nouveaux articles de cet auteur" | Fréquence d'envoi non garantie (plusieurs fois par semaine en pratique), pas d'opérateur NOT booléen dans la requête |

Pour un serveur de préprints spécialisé (bioRxiv, medRxiv, SSRN), vérifier le mécanisme d'alerte propre au site au moment de la mise en place : chacun documente sa propre page d'alertes, non couverte ici faute de vérification directe au moment de la rédaction de ce fichier.

## 2. Construire le digest périodique

Structurer chaque digest en quatre blocs, même quand un bloc reste vide (le dire plutôt que l'omettre).

1. Nouveautés : publications directement ou périphériquement pertinentes parues depuis le dernier digest, classées par pertinence au sujet plutôt que par date brute.
2. Rétractations : toute source déjà citée dans le document qui apparaît rétractée depuis (voir section 3).
3. Évolutions de terminologie : un terme du champ qui a changé de sens, de définition officielle ou d'usage dominant depuis la rédaction.
4. Auteurs suivis : activité récente des auteurs les plus cités dans le document (nouvelle publication, prise de position, correction).

## 3. Contrôler les rétractations

Croiser chaque source déjà citée dans le document contre le jeu de données Retraction Watch, hébergé et mis à jour quotidiennement par Crossref à son emplacement actuel (voir Sources : l'ancien point d'accès `api.labs.crossref.org` est hors service depuis 2024, ne plus le documenter ni le citer). Une source rétractée détectée n'est pas retirée silencieusement : signaler si elle est citée pour discuter la rétractation elle-même, si le résultat qu'elle porte n'est pas affecté par le motif de rétractation ou si elle doit être retirée et remplacée.

## 4. Cadence conseillée (indicative)

La cadence suit la vitesse de publication du champ, jamais un défaut unique. Indicative seulement : l'utilisateur ajuste selon son besoin réel.

| Vitesse du champ | Exemple de champ | Cadence indicative | Date d'expiration indicative de la veille |
| --- | --- | --- | --- |
| Rapide | Intelligence artificielle, épidémiologie en phase aiguë | Hebdomadaire | 6 mois |
| Modérée | Sciences sociales appliquées, gestion, technologie | Mensuelle | 12 mois |
| Lente | Histoire, philosophie, droit constitutionnel | Trimestrielle | 24 mois |

## 5. Maintenance

Élaguer les requêtes mortes : une requête qui ne remonte plus rien de pertinent depuis plusieurs cycles consécutifs, une alerte sur un auteur qui a cessé de publier dans le champ, un flux dont l'URL ne répond plus. Une veille qui accumule des requêtes mortes noie le signal utile sous du bruit silencieux.

## Format de sortie

La liste des requêtes configurées par plateforme, avec leur patron d'URL ou leur mode de configuration. Le digest structuré en quatre blocs (section 2), même partiellement vide. La cadence retenue et sa justification par la vitesse du champ.

## Règles

1. Ne jamais surveiller en tâche de fond : cette compétence configure et structure, l'utilisateur exécute à sa cadence.
2. Un digest annonce un bloc vide plutôt que de l'omettre.
3. Une source rétractée détectée se traite (contexte de citation vérifié), elle ne se retire jamais en silence.
4. Élaguer une requête morte plutôt que la garder par défaut.
5. Un patron d'URL non vérifié directement se signale comme tel, il ne se présente jamais comme confirmé.

## Sources

- arXiv. RSS Feeds. https://info.arxiv.org/help/rss.html (consultée le 2026-07-08)
- NCBI. A General Introduction to the E-utilities, Entrez Programming Utilities Help. https://www.ncbi.nlm.nih.gov/books/NBK25497/ (consultée le 2026-07-08)
- Google Scholar Search Help (section Alertes). https://scholar.google.com/intl/en/scholar/help.html (consultée le 2026-07-08)
- Crossref. Retraction Watch data now freely available (annonce de l'ouverture des données, 12 septembre 2023). https://www.crossref.org/blog/news-crossref-and-retraction-watch/
- Dépôt de données Retraction Watch tenu par Crossref, mise à jour quotidienne (442 commits constatés le 2026-07-08). https://gitlab.com/crossref/retraction-watch-data (consultée le 2026-07-08)
