# Intégration continue éditoriale

Verrouiller un document comme du code : aucun document ne passe sous un seuil de qualité.

## Porte locale

```
python3 tools/check.py "chemin/**/*.md" --seuil 85
```

La commande lance le scorecard sur chaque document et renvoie un code de sortie 1 si l'un d'eux tombe sous le seuil. À utiliser en pré-commit ou avant une remise.

## Passer outre, avec friction

Un blocage se lève par `--outrepasser`, avec une friction croissante : le premier passage n'exige qu'un avertissement, le deuxième une justification (`--justification "..."`), le troisième une justification de cent caractères au moins. Chaque passage outre est journalisé (dans `projet.json` si présent, sinon dans `.outrepassements.json`) et reste visible dans le tableau de bord du projet.

## Porte en intégration continue

Le modèle `scriptorium/templates/editorial-ci.yml` se copie dans `.github/workflows/` d'un projet d'écriture. À chaque push, la porte de scorecard s'exécute et bloque la fusion si un document n'atteint pas le seuil.

## CI du plugin

Le dépôt Scriptorium exécute trois workflows de contrôle, plus `release.yml` au moment d'un tag.

`evals.yml` compile les scripts et lance le harnais d'évaluation, à chaque push et chaque pull request. Une modification qui casse un contrôle déterministe fait échouer la CI.

`verification.yml` couvre deux chemins que le harnais ne peut pas éprouver seul, parce qu'ils dépendent d'outils absents des machines de développement. Mêmes déclencheurs qu'`evals.yml`.

`gabarits-latex.yml` compile réellement les gabarits LaTeX dans une image TeX Live.

### Compilation des gabarits LaTeX

Job `compilation-latex`. Il se déclenche sur un push vers `main`, sur toute pull request et à la main, dans les trois cas restreint aux chemins qui peuvent casser la compilation : les gabarits, la charte d'exemple injectée, `scriptorium/scripts/theme.py`, `tools/ci-latex.py` et le workflow lui-même. L'image TeX Live pèse près de 9 Go, la tirer à chaque push de branche coûterait plus qu'elle ne prouve.

`tools/ci-latex.py preparer` fabrique un dossier de compilation : les deux gabarits dont le bloc CHARTE est remplacé par la sortie réelle de `theme.py --format latex`, un document pilote, et les images PNG que ce pilote inclut. Le pilote est le gabarit de rapport dont les deux exemples de figure, laissés en commentaire, sont décommentés verbatim, suivis de renvois. Verbatim est le point : le pilote compile l'exemple tel qu'il est écrit dans le gabarit, jamais une réécriture qui pourrait compiler là où l'exemple échouerait.

Ce que le job prouve : les deux gabarits passent dans `xelatex` ; le mécanisme d'injection de charte documenté en tête de chacun produit du LaTeX valide ; `\includegraphics`, `\caption`, `\label`, `\ref` et `\pageref` fonctionnent, y compris sur une figure composée en `subcaption` ; `\listoffigures` et `\listoftables` se remplissent depuis les légendes du document. `tools/ci-latex.py controler` relit les sorties après coup, parce qu'un `latexmk` qui rend 0 ne prouve ni qu'une table des figures s'est remplie ni qu'un renvoi s'est résolu.

Ce que le job ne prouve pas : la bibliographie, `latexmk` tournant avec `-bibtex-` et aucun fichier `.bib` n'étant compilé ; le rendu visuel, seule la compilation étant contrôlée ; le comportement avec la police demandée réellement installée, la charte d'exemple demandant Georgia, absente de TeX Live.

Le cache fontconfig est réchauffé avant tout appel, et cette précaution n'est pas cosmétique. `theme.py` interroge `fc-list` avec un délai de dix secondes pour savoir si la police demandée par la charte est installée. Sur un cache froid, `fc-list` met une douzaine de secondes, le délai expire, `theme.py` conclut à une disponibilité inconnue et émet la police demandée telle quelle. `xelatex` échoue alors sur une police absente, sans que le repli sur Latin Modern ait joué. Cache chaud, `fc-list` répond en trois dixièmes de seconde et le repli joue. La même panne attend un utilisateur qui compile sur une machine dont le cache de polices est froid.

### Conversion SVG vers PNG

Job `conversion-svg`. `images.py convertir` essaie quatre backends optionnels en cascade et aucun n'est une dépendance du plugin : sur une machine qui n'en porte aucun, seule la dégradation était éprouvée, jamais la conversion. Le job installe `librsvg2-bin`, produit une figure avec `figures.py`, la convertit, puis contrôle le PNG obtenu : signature de fichier, format et dimensions relus par `images.dimensions`, largeur demandée respectée, concordance entre les dimensions annoncées par le rapport et celles du fichier, poids cohérent avec une image pleine. Le backend employé est vérifié nommément, pour qu'un repli silencieux sur un autre outil ne passe pas pour le chemin nominal. La sortie Word en dépend.

Ce que le job ne prouve pas : les trois autres backends (Inkscape, cairosvg, ImageMagick), ni la fidélité du rendu, seule la validité du PNG étant contrôlée.

### Jeu d'or

Job `jeu-dor`. Il valide les neuf invariants du corpus figé (`tools/gold.py verifier`), rejoue les mesures, puis compare le rapport courant au rapport de référence versionné. La validation des invariants est bloquante : un jeu d'or malade ne mesure rien.

La comparaison est consultative. Elle ne pose pas `--bloquant` et ne fait donc jamais échouer la CI, conformément à la doctrine de `docs/CONCEPTION.md`. Son rapport est repris dans le résumé de l'exécution : une porte consultative que personne ne lit ne sert à rien.

Le rapport de référence vit dans `evals/gold/rapport-reference.json`, à la racine du corpus qu'il mesure et hors des sous-dossiers de tâche que `tools/gold.py` parcourt pour découvrir les tâches déclarées. Son historique est celui du fichier dans git : chaque version publiée y laisse un état daté, et c'est cet historique qui calibrera le seuil de blocage. Il se rafraîchit par `python3 tools/gold.py mesurer --out evals/gold/rapport-reference.json`, et le harnais d'évaluation vérifie qu'il couvre bien toutes les tâches déclarées.

## Fraîcheur des sources normatives

Chaque playbook de genre porte une section Sources dont les URL vieillissent. Un contrôle périodique (mensuel suffit) les repasse en revue :

```
python3 scriptorium/scripts/verify-sources.py scriptorium/skills/produire/references/genre-*.md --check-links
```

Le contrôle est consultatif : une URL morte se remplace par une source équivalente vérifiée, elle ne bloque pas une release.

## Seuils par discipline

Le seuil par défaut est 85. Un profil de discipline (voir `controler` (consensus)) peut fixer un seuil propre dans `profil.json`, repris par la porte.
