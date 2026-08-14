# Aiguilleur (ce que l'utilisateur dit, ce dont il a besoin)

Distinguer la formulation de surface d'une demande du besoin réel qu'elle cache. Une demande mal aiguillée saute une étape en amont (cadrage, sourcing, vérification) et produit un livrable qui a l'air fini sans l'être.

## 1. Table de correspondance

| L'utilisateur dit | Ce dont il a besoin | Pourquoi |
|---|---|---|
| "Écris-moi un rapport sur X" | `atelier` (cadrer) puis `produire` (sourcer), avant `produire` (genre) | Sans périmètre fermé ni preuves réunies, la rédaction produit du remplissage générique plutôt qu'une démonstration |
| "Vérifie ce texte" | À préciser : `controler` (revue) si le texte vient du plugin et pose une question de fond ou de style, `controler` (audit) s'il s'agit d'un document externe déjà rédigé, `controler` (humaniser) si le doute porte sur une empreinte de génération | Les trois sous-commandes répondent à des questions différentes, un mauvais choix produit un rapport hors sujet |
| "Fais une synthèse" | `produire` (revue-litterature) si la synthèse part de sources non encore reliées, `livrer` (decliner) si elle condense un document déjà validé | La première construit une matrice de preuves, la seconde reformule des faits déjà établis |
| "Relis mon rapport" | `controler` (revue) pour une critique interne, `controler` (relecteurs) si de vrais commentaires de relecteurs externes existent déjà à intégrer | Intégrer un retour humain réel suit un protocole distinct (confirmation du découpage, jugement d'accord ou de désaccord) d'une critique menée seule |
| "Rends ce document plus convaincant" | `controler` (contredire) avant toute réécriture de style | Polir le style d'un argument qui n'a pas été mis à l'épreuve renforce sa forme sans corriger sa faiblesse de fond |
| "Mets ça en forme" | `livrer` (document), seulement si `controler` (revue) a déjà rendu un verdict prêt | Mettre en forme un brouillon non validé habille un texte qui n'est pas encore fiable |
| "Fais-moi un résumé d'une page ou un pitch" | `livrer` (decliner) à partir d'un document déjà validé, sinon `produire` (genre) d'abord | Décliner un contenu qui n'existe pas encore revient à improviser un nouveau texte sous couvert de résumé |
| "Trouve-moi des sources" | `produire` (sourcer), après que `atelier` (cadrer) a fixé la problématique et le plan | Sourcer sans cible fixée revient à collectionner des références sans savoir ce qu'elles doivent prouver |
| "Trouve-moi vite fait deux ou trois trucs sur X" ou toute demande de sourcing sans profondeur précisée | Estimer la complexité de la question avant de chercher (nombre de concepts distincts, besoin de triangulation, controverse), puis router `produire` (sourcer) vers le palier rapide, standard ou approfondi | Sourcer à profondeur fixe par défaut sur-source une question simple ou sous-source une question à fort enjeu, voir `references/sourcer.md` |
| "Ce chiffre est-il exact ?" | Vérification factuelle disciplinée (agent `verificateur-faits`, via `produire` (sourcer) ou `controler` (revue)) | Une réponse impressionniste sans confrontation à une source datée n'est pas une vérification |
| "Fais-moi un plan" | `atelier` (cadrer), étape bâtir le plan, après la problématique et le genre | Un plan sans problématique fermée ni genre choisi est une table des matières, pas une démonstration |

## 2. Anti-patterns de workflow

1. Rédiger avant de sourcer : la rédaction commence sans carte preuve-affirmation. Bon réflexe : charger `produire` (sourcer) d'abord, ou à défaut marquer chaque affirmation sans preuve `[LACUNE MATERIELLE]` plutôt que de l'écrire comme un fait établi.
2. Réviser avant de vérifier les faits : `controler` (revue) rend un verdict sans que l'agent `verificateur-faits` ait confirmé les affirmations chiffrées ou factuelles. Bon réflexe : inclure la vérification factuelle dans la revue ou le consensus avant tout verdict prêt.
3. Livrer sans contrôle : `livrer` (document ou decliner) s'exécute alors que la revue n'a pas rendu de verdict prêt, ou que des constats critiques restent ouverts. Bon réflexe : refuser de mettre en forme et renvoyer vers `controler` (revue).
4. Décliner un document non validé : `livrer` (decliner) part d'un brouillon sans version validée. Bon réflexe : vérifier qu'un verdict prêt existe (mémoire de projet ou confirmation explicite de l'utilisateur) avant de produire une déclinaison, sinon une erreur non vérifiée se propage vers plusieurs canaux à la fois.
