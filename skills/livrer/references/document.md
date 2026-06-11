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
