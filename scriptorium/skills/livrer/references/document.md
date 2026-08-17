# Finaliser (mise en forme du livrable)

Transformer un texte validé en document remis. Le fond ne change plus à cette étape, seule la forme s'ajoute. La mise en forme suit la structure standard du genre.

## Préalable

Ne finaliser qu'un texte passé par `controler` (revue) avec un verdict « Prêt ». Si le texte n'a pas été révisé, lancer d'abord `controler` (revue). Mettre en forme un texte fautif ne fait que rendre la faute présentable.

## 1. Choisir le format de sortie

Selon la demande et le genre. Charger ensuite le bon skill de production de fichier, et lui seul.

- Document Word : lire le skill `docx`, puis construire le fichier.
- PDF : lire le skill `pdf`, puis construire le fichier.
- Présentation : lire le skill `pptx` si la demande est une soutenance.

## 2. Appliquer la mise en forme du genre

Charger `references/mise-en-forme.md` pour les conventions détaillées par genre. Résumé :

- Rapport scientifique et mémoire : page de garde (titre précis), sommaire, listes des tableaux, figures et abréviations, texte justifié, police classique en 11 ou 12, interligne 1,5, pagination, bibliographie APA 7 ou Vancouver, annexes numérotées.
- Article : titre, chapô, intertitres, pas de page de garde lourde, références en fin.
- Long rapport professionnel : page de garde, résumé analytique en tête, sommaire, en-têtes et pieds de page, annexes.
- Analyse stratégique : sommaire, figures intégrées (voir `produire` (figure)), synthèse en tête.
- Étude de cas : format court, encadrés de chiffres clés, verbatims mis en exergue.

## Appliquer la charte graphique

Si une charte graphique existe (`charte-graphique.json`, voir la compétence `produire` (charte)), la valider puis appliquer sa police de titres, sa couleur d'encre et son accent aux titres, filets, légendes et liens du document. Produire les figures avec la même charte. Le corps de texte reste sobre et lisible. La charte graphique règle l'image, le style maison règle les mots, les deux s'appliquent ensemble.

## 3. Intégrer les figures

Si le document comporte des figures, les produire avec `produire` (figure), vérifier leur regard critique, puis les insérer numérotées et titrées, avec leur source. Une figure est autonome : elle se comprend sans le texte.

Contrôler la numérotation sur le Markdown source avant de couler le document, quelle que soit la voie de sortie.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/traceability.py FICHIER
```

Le script signale un numéro porté par deux légendes, un numéro sauté (figure 1 puis figure 3), une suite qui ne commence pas à 1, une numérotation d'annexes mêlant chiffres et lettres. Il signale aussi tout objet défini sans être appelé depuis le texte. Il couvre figures, tableaux, équations et annexes.

La liste des figures et la liste des tableaux exigées par `references/mise-en-forme.md` se produisent différemment selon la voie :

- LaTeX : `\listoffigures` et `\listoftables` du gabarit, remplis automatiquement depuis les `\caption` à la deuxième passe.
- HTML : rien d'automatique, la liste s'écrit comme un `<nav>` de liens vers les `id` des `<figure>` et des `<table>`.
- Word : rien d'automatique côté plugin, la liste s'écrit à l'insertion ou se délègue au champ "Table des illustrations" de Word, qui se met à jour dans l'application.
- PDF : hérite de la voie qui l'a produit.

## 4. Formater et vérifier la bibliographie

Passer la bibliographie au script de vérification avant de la couler dans le document.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/verify-sources.py FICHIER
```

Retirer les paramètres de suivi, supprimer les doublons, contrôler les DOI, appliquer une seule norme de bout en bout (voir `produire` (sourcer)).

## 5. Contrôle de forme final

Avant de remettre, repasser le linter de style sur le texte source.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lint-style.py FICHIER
```

Vérifier la liste de contrôle avant publication (voir `reviser/references/checklist-pre-publication.md`) : sections obligatoires présentes, abréviations définies, figures et tableaux titrés et sourcés, pagination, résumé autonome.

## 6. Contrôle de fuites avant envoi

Un livrable qui part chez un client, une école ou une revue emporte plus que son texte : le nom de qui l'a rédigé et de qui l'a enregistré en dernier, celui de l'organisation, le nombre d'enregistrements successifs, les commentaires et les modifications suivies restés dans le fichier, les notes du présentateur d'un deck, le chemin local d'un fichier lié. Le contrôle porte sur le fichier final, pas sur le Markdown source.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/check-fuites.py livrable.docx --auteur "Prenom Nom"
```

Le verdict se ferme sur quatre valeurs (fuites confirmees, fuites probables, traces sans identite lisible, rien a signaler) et chaque constat porte sa confiance. L'option `--auteur` évite le faux positif du nom déjà imprimé sur la page de garde. Traiter les constats confirmés avant l'envoi, signaler les probables à l'auteur.

Le script inspecte et ne nettoie pas : retirer une trace est une décision, elle ne s'automatise pas. Le nettoyage se fait dans l'application d'origine (inspecteur de document Word, export neuf pour un PDF), puis le contrôle se rejoue sur le fichier corrigé. Pour un PDF, ne pas éditer les métadonnées d'un fichier déjà produit : un outil comme exiftool écrit une mise à jour incrémentale qui masque l'ancienne valeur sans la retirer du fichier, où elle reste lisible ; le script signale ce cas. Réexporter depuis la source.

Reporter dans la note de remise la ligne de verdict et ce qui reste ouvert. Détail du script dans `controler` (audit), section audit de fuites.

## Format de sortie

Le fichier final (Word ou PDF), plus une note de remise courte : genre, format, nombre de pages, norme bibliographique, figures incluses, points de vigilance restants.

## Règles

1. La mise en forme n'altère ni le fond ni les faits.
2. Ne pas finaliser un texte non révisé.
3. Une seule norme bibliographique par document.
4. Toute figure insérée est numérotée, titrée, sourcée et autonome.
5. Respecter le style maison jusque dans les légendes et les notes.

## Sortie HTML (charte graphique, HTML propre)

Le HTML donne la plus grande latitude de mise en forme et respecte la charte au plus près. Produire un seul fichier `.html` autonome, CSS et figures inclus, sans dépendance externe. Les règles suivent les standards du plugin NullToHero : HTML sémantique, jetons de design, accessibilité WCAG 2.2.

### CSS dérivé de la charte

Si `charte-graphique.json` existe dans le dossier de travail, générer la feuille de style et la coller dans un bloc `<style>` du `<head>` (jamais de fichier externe) :

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/theme.py charte-graphique.json --format css
```

Le script émet des jetons en `:root` (couleurs, polices, accent, rayon), des propriétés logiques, une mesure fluide `clamp(45ch, 90%, 75ch)`, un focus visible et une feuille d'impression. Il contrôle le contraste WCAG et refuse une charte illisible. Sans charte, il sort un CSS sobre par défaut.

### Structure sémantique

Un seul `<h1>`, hiérarchie de titres sans saut de niveau. Repères : `<header>` de page de garde, `<nav>` de sommaire avec ancres, `<main>` et `<section>` par partie, `<figure>` plus `<figcaption>` pour les figures numérotées, `<table>` avec `<caption>` pour les tableaux. Marquage valide, balises fermées, pas d'identifiant en double. Sur le `<html>`, poser `lang="fr"`, un `<title>` parlant et `<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">`.

### Jetons et patrons interdits

Couleurs et espacements passent par les jetons de la charte, aucun code hexadécimal en dur, jamais de noir ou de blanc purs. Proscrire `!important`, le `style` en ligne répété, `transition: all`, un `z-index` exagéré, un filet d'accent `border-left` sur les cartes. Animer au besoin `transform` et `opacity` seulement, jamais une propriété de mise en page.

### Accessibilité

Contraste du texte au moins 4,5:1 et 3:1 pour les composants (déjà contrôlé par `theme.py`), focus visible sur chaque lien, texte alternatif sur les images informatives et `alt=""` sur les décoratives, aucune information portée par la seule couleur, animation non essentielle désactivée sous `prefers-reduced-motion`.

### Figures et impression

Embarquer les figures SVG en ligne (produites par `produire`, action figure) : elles héritent de la charte et restent nettes à l'impression. La feuille `@media print` fixe les marges `@page`, évite les coupures dans les figures et tableaux (`break-inside: avoid`) et conserve les couleurs (`print-color-adjust: exact`). Le HTML sert alors de source pour un PDF fidèle à la charte.

Contrôler le rendu avant remise. Le fond ne change pas, seule la forme s'ajoute.

## Images importées (depuis un PDF ou un document source)

Les images extraites d'un document source (voir `produire`, action image) se placent comme des figures de plein droit, à partir du manifeste enrichi.

- Chaque image informative devient une figure numérotée, avec sa légende et sa source, au ratio d'origine (largeur et hauteur du manifeste) et bornée à la mesure du texte.
- HTML : `<figure><img alt="..." width="W" height="H"><figcaption>Figure N. Légende. Source.</figcaption></figure>`, image embarquée en base64 pour garder le fichier autonome, `alt` repris du manifeste enrichi, coupure évitée entre image et légende.
- Word : insérer via le skill `docx`, légende sous l'image.
- PDF : via le skill `pdf`, ou par conversion du HTML.
- Les images décoratives reçoivent un `alt` vide et ne sont pas numérotées. Les images vectorielles non converties ne sont pas insérées en l'état, elles sont signalées.

La charte graphique cadre la légende et le filet, comme pour une figure générée. Une image n'est jamais recadrée au point de tromper.

## Sortie LaTeX (gabarit charté, rapport professionnel)

Une troisième voie de finalisation, à côté de Word, PDF et HTML : le gabarit `assets/gabarit-rapport.tex`, un rapport professionnel autonome avec page de titre, en-têtes, cinq encadrés sémantiques (résultat, méthode, avertissement, limite, note) et trois macros statistiques (`\pvalue`, `\CI`, `\effectsize`). Adapté du paquet `scientific_report` du dépôt openscience (Apache-2.0), simplifié à un seul fichier compilable.

### Figures dans le gabarit

Le gabarit charge `graphicx`, `float`, `caption` et `subcaption`. Il fixe le style des légendes sur la couleur d'encre de la charte. Un bloc laissé en commentaire dans la section Résultats donne l'environnement `figure` complet (`\includegraphics`, `\caption`, `\label`, dans cet ordre), le renvoi `\ref` depuis le texte et une figure composée en `subfigure`. Le décommenter et remplacer le nom de fichier. Les images se cherchent dans le dossier du `.tex`, dans `figures/` et dans `images/` (`\graphicspath`). Une figure SVG produite par `scripts/figures.py` se convertit en PDF avant inclusion (rsvg-convert, inkscape ou cairosvg) : xelatex n'insère pas de SVG. `\listoffigures` et `\listoftables` suivent le sommaire et se remplissent seuls à la deuxième passe.

### Quand préférer LaTeX au HTML

- La destination l'impose (revue ou conférence à gabarit LaTeX officiel, voir la section suivante).
- Le document porte une notation statistique ou mathématique dense : LaTeX la compose nativement, sans détour (voir `produire`, action equation, pour les équations et unités SI).
- Une pagination exacte est requise (en-têtes courants, numérotation romaine puis arabe, sauts de page maîtrisés), plus fine que ce qu'une feuille d'impression HTML garantit.
- Le document doit rester dans l'écosystème BibTeX déjà en place (voir `scripts/citations.py`) sans repasser par une conversion.

Le HTML reste préférable pour une publication web interactive, une itération rapide sans recompilation ou l'absence de toute chaîne LaTeX sur la machine.

### Charte injectée

Les couleurs et polices du gabarit sont un bloc `\definecolor` et `\setmainfont` délimité par des marqueurs de commentaire (`DEBUT BLOC CHARTE` / `FIN BLOC CHARTE`). Le générer et le coller tel quel à la place du bloc par défaut :

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/theme.py charte-graphique.json --format latex
```

Même logique que `--format css` pour le HTML : un bloc prêt à coller, jamais à retaper à la main. Quand `fc-list` (fontconfig) est présent sur la machine, le script vérifie que la police demandée est installée et retombe sur une famille Latin Modern sinon, avec un commentaire d'avertissement dans le bloc généré ; sans `fc-list`, le nom demandé est repris tel quel, à vérifier avant compilation.

### Compilation optionnelle

Si `xelatex` est disponible, compiler directement :

```
xelatex gabarit-rapport.tex
```

Deux passes suffisent pour une table des matières correcte ; ajouter `bibtex` entre les deux si une bibliographie BibTeX est jointe (voir `scripts/citations.py` pour la produire depuis des sources vérifiées). Si `xelatex` manque, livrer le fichier `.tex` avec la charte déjà injectée et signaler que la compilation demande cet outil, sans bloquer la remise : même convention que l'export PDF via pandoc décrit dans `produire`, action equation.

### Gabarit associé pour un poster

Le même mécanisme de charte s'applique au poster scientifique : `assets/gabarit-poster.tex` (voir `produire`, action genre, playbook poster). Les deux gabarits partagent les mêmes noms de couleur (`ScriptoriumEncre`, `ScriptoriumTrait`, `ScriptoriumFond`, `ScriptoriumAccent`, `ScriptoriumPalUn` à `ScriptoriumPalQuatre`), un même bloc généré s'applique aux deux sans modification.

## Exigences par destination (revue, conférence, préprint)

En plus du genre, la destination impose ses propres contraintes de forme. Les vérifier avant la mise en forme, jamais après : reprendre une mise en forme déjà posée coûte plus cher que de partir du bon gabarit.

- Revue à comité de lecture : limite de longueur propre à la revue (souvent comptée en mots ou en pages, figures incluses ou non selon le titre), style de citation imposé (numérique, auteur-date ou propre à la revue), résumé structuré ou non selon la discipline, déclarations obligatoires (financement, conflits d'intérêts, disponibilité des données). Le gabarit LaTeX ou le modèle Word officiel de la revue prévaut toujours sur un gabarit générique.
- Conférence (informatique, apprentissage automatique, sciences de l'ingénieur) : limite de pages stricte pour le corps du texte, annexes et références parfois hors limite, anonymisation en double aveugle fréquente pour la soumission initiale (retirer noms, affiliations, remerciements, auto-citations à la première personne), gabarit LaTeX officiel propre à chaque conférence et millésime.
- Préprint (arXiv, HAL, bioRxiv et assimilés) : peu ou pas de limite de forme, mais une licence à déclarer, une version datée et citable, ainsi qu'une bascule ultérieure possible vers le gabarit d'une revue ou d'une conférence si le travail y est soumis ensuite.

Checklist de soumission, commune aux trois familles : format de fichier accepté (PDF le plus souvent, parfois LaTeX source), respect de la limite de pages ou de mots avant tout envoi, citations dans le style imposé, anonymisation vérifiée si requise, figures aux résolutions demandées, métadonnées de soumission renseignées (titre, auteurs, affiliations, mots-clés).

Ce plugin n'embarque pas de bibliothèque de gabarits propres à chaque revue ou conférence : ils changent chaque année et se trouvent officiellement sur le site de la destination (page auteurs, dépôt Overleaf officiel de la venue). Utiliser `assets/gabarit-rapport.tex` pour un rapport interne ou un document sans gabarit imposé. Utiliser le gabarit officiel de la destination dès qu'elle en fournit un.
