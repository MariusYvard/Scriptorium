# Unités SI et modèles LaTeX

## Règles SI

- Espace insécable entre le nombre et l'unité : 10 kg, 3,5 m, 20 °C (mais 50 % et 30° sans espace par convention).
- Symboles d'unité en romain (non italique), au singulier : m, s, kg, A, K, mol, cd. Pas de point abréviatif.
- Préfixes : k (kilo), M (méga), G (giga), m (milli), µ (micro), n (nano). Un seul préfixe par unité.
- Unités composées : m/s ou m s⁻¹, N·m, kW·h. Le point médian ou l'espace sépare les facteurs.
- Le séparateur décimal est la virgule en français, le point en anglais. Une seule convention par document.
- Grands nombres : espace fine comme séparateur de milliers (10 000), jamais le point ni la virgule.

## Modèles LaTeX

Équation en ligne : `$E = mc^2$`.

Équation hors texte numérotée :
```
$$
\nabla \cdot \mathbf{E} = \frac{\rho}{\varepsilon_0}
$$
```

Unités avec siunitx :
```
\usepackage{siunitx}
\SI{9.81}{\meter\per\second\squared}
\SI{1.5}{\mega\pascal}
\num{12000}
```

Fractions, sommes, intégrales : `\frac{a}{b}`, `\sum_{i=1}^{n}`, `\int_0^\infty`.

Matrices :
```
$$
A = \begin{pmatrix} a & b \\ c & d \end{pmatrix}
$$
```

## Export

```
pandoc doc.md -o doc.pdf --pdf-engine=xelatex
pandoc doc.md -o doc.pdf --pdf-engine=xelatex --citeproc --bibliography refs.bib --csl style.csl
```

## Chiffres significatifs

- Reporter la précision de la mesure, pas celle du calcul. Une règle au millimètre donne 12,3 cm, pas 12,300 cm.
- Arrondir le résultat final, pas les valeurs intermédiaires.
- Une incertitude se présente avec un ou deux chiffres significatifs : (12,3 ± 0,4) cm.
