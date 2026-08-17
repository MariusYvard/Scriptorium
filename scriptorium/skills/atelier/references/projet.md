# Mémoire de projet

Éviter de repartir de zéro. Un fichier `projet.json` dans le dossier de travail conserve ce qui définit le projet, rechargé au début de chaque session. Depuis l'extension qui introduit le journal (section 5), il conserve aussi un historique append-only des étapes, décisions, artefacts et frontières de la mission. La lecture d'un `projet.json` créé avant cette extension reste possible : les nouvelles clés sont ajoutées en mémoire avec des valeurs vides si elles sont absentes du fichier.

## 1. Initialiser

Au lancement d'un nouveau document, créer la mémoire de projet.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py init
```

Le squelette contient : titre, genre, problématique, brief, chemin de la charte, chemin du profil de discipline, chemin du plan, glossaire, liste des objets numérotés, sources, notes, plus un journal vide, un état vide par étape et un état vide par artefact.

## 2. Remplir au fil du cadrage

Quand `atelier` (cadrer) fixe le genre, la problématique et le plan, les enregistrer. Quand `produire` (sourcer) réunit des références, les ajouter. Quand `produire` (style) ou `produire` (charte) produisent une charte, en noter le chemin.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py set genre '"analyse-strategique"'
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py set problematique '"..."'
```

## 3. Recharger au début de session

Si `projet.json` existe, le lire pour retrouver le contexte sans le redemander.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py show
```

Reprendre le genre, la problématique, la charte, le profil et le plan tels quels. La session continue le travail au lieu de le redécouvrir.

À la reprise, trois gestes explicites priment sur le souvenir de la session : relire le passeport (`show` ou `status`), relire les artefacts nommés dans leur état courant et énoncer ce qui a changé depuis leur dernière version. Un souvenir de session ne vaut jamais preuve : ce qui n'est pas dans `projet.json` ou sur le disque est à revérifier, jamais supposé acquis.

## 4. Synchroniser avec Dream (optionnel)

Si la mémoire Dream est disponible, y stocker les décisions de cadrage et la charte comme événements, pour une persistance en dehors du dossier de travail. Cette synchronisation est optionnelle, `projet.json` reste la source dans le dossier.

## 5. Journal append-only

Chaque événement notable de la mission s'ajoute au journal (clé `journal`) comme une entrée horodatée (ISO 8601) et typée. Une entrée n'est jamais modifiée ni supprimée, seulement ajoutée : `project.py` ne fournit aucune commande qui réécrit une entrée existante, et sa fonction interne de journalisation numérote chaque entrée à la position courante plutôt que d'écrire à un index arbitraire.

Sept types d'entrée.

- `etape` : un changement d'état d'étape (voir section 7), avec l'état avant et après.
- `decision` : une décision clef, journalisée avec `project.py decision "libellé"`.
- `artefact` : une nouvelle version d'un artefact (voir section 8).
- `frontiere` : une frontière posée (voir section 6).
- `reprise` : la reprise d'une frontière.
- `objet` : le numéro d'une figure, d'un tableau, d'une équation ou d'une annexe, fixé pour la mission (voir section 11).
- `outrepassement` : un passage outre un blocage, non supprimable (voir `tools/check.py` et `piloter.md`, section friction des outrepassements).

## 6. Frontières et reprise par hash

Poser une frontière fixe un point de reprise explicite, utile avant une pause ou quand la session porte beaucoup de contexte accumulé (voir `chemins-defaillance.md`, D4).

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py frontiere "fin du sourcing" --decision-attente "garder ou non l'étude X, contestée par une source plus récente"
```

La frontière porte un hash tronqué à 12 caractères hexadécimaux, calculé par une sérialisation JSON canonique maison (clés triées, séparateurs compacts, UTF-8) de toutes les entrées de journal qui précèdent la frontière, puis SHA-256. Cette canonicalisation s'inspire de RFC 8785 (JSON Canonicalization Scheme) sans en être une implémentation conforme : voir le docstring de `project.py` pour le détail des écarts.

Reprendre une frontière dans une session ultérieure :

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py reprendre HASH
```

La reprise retrouve la frontière, affiche un accusé (étape courante, artefacts, décision en attente le cas échéant, à reposer à l'utilisateur plutôt qu'à trancher seul), puis journalise la reprise. Une deuxième reprise de la même frontière est refusée : le hash a déjà été consommé.

## 7. États d'étape

Chaque étape suivie porte un état parmi `en_attente`, `en_cours`, `termine`, `saute`, `bloque`. Changer d'état :

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py etape sourcing en_cours
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py etape sourcing termine
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py etape figures saute --motif "hors périmètre validé au cadrage"
```

Les noms d'étape suivent par convention les cinq temps de `piloter.md` (cadrage, sourcing, redaction, revision, finalisation), sans que `project.py` les impose : toute étiquette est acceptée. Les transitions sont vérifiées : `termine` n'est atteignable que depuis `en_cours` (pas de passage direct depuis `en_attente`, `bloque` ou `saute`), et `saute` exige un `--motif`. Une transition hors de cette table est refusée avec un message qui nomme l'état de départ, l'état demandé et les états autorisés.

## 8. Versions d'artefacts

Chaque artefact (plan, brouillon, rapport de sources, figure) porte une version qui augmente strictement (`v1`, `v2`, ...), jamais réutilisée. L'ancienne version reste consultable dans le journal, seule la version courante change dans l'état rapide.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py artefact brouillon
```

## 9. Tableau de bord

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py status
```

Affiche un tableau de bord texte : chaque étape avec un symbole d'état, les artefacts et leur version courante, les décisions en attente (frontières dont la décision n'a pas encore été reposée par une reprise), les frontières posées avec leur hash et leur état de reprise, et le compte d'outrepassements. `scripts/audit-doc.py` pourra afficher ce compte via `project.compter_outrepassements()`, non encore câblé dans ce lot.

## 10. Reproductibilité honnête

Documenter la configuration de génération d'un document, sans jamais promettre qu'elle permette de le rejouer à l'identique.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py reproductibilite --plugin-version 0.7.0 --modele claude-sonnet-5
```

La commande enregistre une entrée de journal (type `reproductibilite`) avec la version du plugin, le modèle nommé et une date automatique (ISO 8601, comme toute autre entrée). Chaque entrée porte aussi, recopiée en clair, une déclaration de stochasticité fixe : documenter la configuration n'est pas garantir le rejeu, un modèle de langage reste stochastique par nature. Enregistrer une nouvelle configuration (changement de modèle en cours de mission, par exemple) ajoute une entrée, elle ne remplace jamais la précédente, par le même principe d'append-only que le reste du journal (section 5). `project.py status` affiche toutes les entrées de reproductibilité enregistrées.

## 11. Glossaire et objets numérotés transmis au rédacteur

Un document long se rédige section par section, chaque passe confiée à l'agent `redacteur`. Cet agent n'a que Read, Glob et Grep : il ne lit pas `projet.json` et n'y écrit rien. Sans transmission explicite, la passe suivante rebaptise un terme fixé par la précédente et rouvre la numérotation des figures à 1.

Fixer un numéro dès qu'un objet légendé entre dans le document.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py objet figure 3 "Courbe de conversion"
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py objet tableau 1 "Conditions opératoires"
```

Quatre types acceptés : `figure`, `tableau`, `equation`, `annexe`. Réenregistrer le même numéro avec le même libellé ne fait rien. Avec un libellé différent, c'est un refus : un numéro déjà servi ne se réaffecte pas, deux figures 3 dans un même document ne se rattrapent plus à la mise en forme.

Émettre la passation avant chaque appel au rédacteur, puis la coller dans son prompt.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py passation
```

Elle porte le genre, la problématique, le glossaire des termes fixés, les objets déjà numérotés avec leur libellé et le prochain numéro libre par type. Le format `--format json` sert quand la passation alimente un autre script, le format texte quand elle va dans un prompt. Voir `passations.md`, section sur la passation vers un sous-agent.

Le glossaire se remplit comme les autres champs, par `set`, chaque terme pointant sur sa définition retenue.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/project.py set glossaire '{"banc d essai": "montage instrumenté décrit en 2.1"}'
```

La clé `objets_numerotes` suit la règle de compatibilité générale : un `projet.json` écrit avant elle se recharge sans erreur, la clé est complétée à vide en mémoire et le fichier reste inchangé tant qu'aucune écriture ne survient.

## Format de sortie

L'état du projet rechargé (genre, problématique, charte, profil, plan, nombre de sources) et la confirmation de ce qui a été repris. Pour un état complet, utiliser `status` (section 9) plutôt que `show`.

## Règles

1. `projet.json` est la source dans le dossier de travail.
2. Ne pas redemander ce que la mémoire de projet contient déjà.
3. Tenir la mémoire à jour à chaque étape (cadrage, sourcing, charte).
4. Ne jamais stocker de secret ni de token dans `projet.json`.
5. Le journal ne se réécrit jamais. Une correction s'ajoute comme nouvelle entrée, elle ne remplace pas l'ancienne.
6. Une entrée de reproductibilité documente la configuration au moment de son enregistrement. Elle ne promet jamais qu'un rejeu ultérieur produise un texte identique.
7. Un numéro de figure ou de tableau se fixe au moment où l'objet entre dans le document, pas à la mise en forme. Aucune passe de rédaction ne part sans le glossaire ni la liste des numéros déjà servis.
