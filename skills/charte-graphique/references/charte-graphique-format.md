# Format de la charte graphique

Une charte graphique est un fichier JSON. Tous les champs sont optionnels : un champ absent prend la valeur par defaut sobre. Le script `scripts/theme.py` normalise et valide la charte, et controle le contraste.

## Champs

| Champ | Type | Defaut | Role |
| --- | --- | --- | --- |
| `police` | chaine | Helvetica, Arial, sans-serif | Police du corps et des etiquettes |
| `police_titre` | chaine | = `police` | Police des titres |
| `graisse_titre` | entier | 700 | Graisse des titres |
| `couleurs.encre` | #RRGGBB | #2E2A26 | Texte et traits forts |
| `couleurs.trait` | #RRGGBB | #8A8175 | Filets, contours, libelles secondaires |
| `couleurs.fond` | #RRGGBB | #FFFFFF | Fond de la figure |
| `couleurs.accent` | #RRGGBB | #6E6356 | Filet sous le titre, bulles BCG, fleche de marge |
| `couleurs.palette` | liste de 4 #RRGGBB | tons clairs | Remplissage des cases et quadrants |
| `logo_texte` | chaine | absent | Filigrane texte en haut a droite |
| `rayon` | entier | 8 | Rayon des angles arrondis |

Les couleurs acceptent aussi un objet `couleurs` ou les champs a plat (`encre`, `trait`, ...). La palette est completee a quatre entrees si elle en compte moins.

## Exemple

```json
{
  "police": "Georgia, serif",
  "couleurs": {
    "encre": "#16314E",
    "trait": "#9AA7B8",
    "fond": "#FFFFFF",
    "accent": "#C8102E",
    "palette": ["#EEF2F6", "#E7EDF3", "#F3EEE7", "#EDE7F0"]
  },
  "logo_texte": "ACME"
}
```

## Application

- Figures : `python3 scripts/figures.py TYPE --theme charte.json --out f.svg`. Toutes les couleurs, polices et le filigrane suivent la charte.
- Documents : la competence `finaliser` lit la charte et applique la police des titres, la couleur d'encre et l'accent aux titres, filets et legendes.

## Garde-fou de contraste

`theme.py` calcule le ratio de contraste WCAG entre l'encre et le fond, et entre l'encre et chaque fond de palette. Un ratio sous 4,5:1 produit un avertissement (texte peu lisible). Une couleur mal formee produit une erreur. Une charte en erreur ne doit pas etre utilisee telle quelle.

## Ce que la charte couvre, et ses limites

Couvre : couleurs, polices, graisse des titres, accent, fond, rayon, filigrane texte. Ne couvre pas, sans travail supplementaire : un logo en image (a inserer separement dans le document), des illustrations sur mesure, une grille de mise en page complexe. Pour ces cas, la charte fixe le socle et la mise en forme manuelle complete.
