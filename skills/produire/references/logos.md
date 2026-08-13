# Logos (registre et placement)

Cette fiche sert dès qu'un document doit porter un ou deux logos, parfois davantage : page de garde institutionnelle, en-tête à l'identité d'un laboratoire, pied de page d'un client, co-signature entre une école et une entreprise d'accueil. Un logo ne vit pas dans la charte graphique (voir `produire`, action charte) parce qu'il porte des règles propres à l'organisation qui le possède, pas au document produit : zone de respiration, taille minimale, usages autorisés, rang protocolaire face à d'autres logos. Ces règles vivent dans un fichier séparé, `registre-logos.json`, référencé par la charte plutôt que fondu dedans. Le script associé est `scripts/logos.py`, deux actions : valider, placer.

## Format du registre

Le registre est un objet JSON avec une clé `logos`, une liste d'entrées. Chaque entrée décrit un logo :

- `id` : identifiant court, unique dans le registre. Obligatoire.
- `fichier` : chemin de l'image, relatif au dossier du registre ou absolu. Obligatoire.
- `usages` : sous-liste parmi `page-garde`, `en-tete`, `pied`, `co-signature`. Absent, la valeur par défaut est les quatre usages.
- `rang` : entier, ordre protocolaire en co-signature ou en placement multiple. Absent, le logo passe en dernier rang.
- `largeur_cm` : largeur d'affichage générale, en centimètres. Absent, une largeur par défaut s'applique selon l'usage (5 cm en page de garde, 2,5 cm en en-tête, 2 cm en pied, 3 cm en co-signature).
- `largeur_cm_par_usage` : objet qui fixe une largeur différente par usage, prioritaire sur `largeur_cm` pour l'usage concerné.
- `respiration` : marge autour du logo, en fraction de sa largeur affichée. Absent, la valeur par défaut est 0,25.
- `ratio_verrouille` : ratio largeur sur hauteur attendu. Absent, aucun contrôle de ratio n'est fait.
- `alt` : texte alternatif. Absent, l'identifiant `id` sert de repli.

Exemple :

```json
{
  "logos": [
    {
      "id": "ecole",
      "fichier": "logos/ecole.svg",
      "usages": ["page-garde", "en-tete"],
      "rang": 1,
      "largeur_cm_par_usage": {"page-garde": 6.0, "en-tete": 2.0},
      "alt": "Logo de l'école"
    },
    {
      "id": "labo",
      "fichier": "logos/labo.png",
      "usages": ["page-garde", "co-signature"],
      "rang": 2,
      "ratio_verrouille": 1.8,
      "alt": "Logo du laboratoire d'accueil"
    }
  ]
}
```

Le premier logo porte le rang 1 (l'école, logo hôte) et une largeur différente selon qu'il apparaît en page de garde ou en en-tête. Le second, en PNG, déclare un ratio verrouillé que `valider` contrôle contre les pixels réels du fichier.

## Règles de placement par usage

- Page de garde : le logo hôte (l'organisation qui produit le document) prime, un logo invité se place en second, taille moindre. L'ordre suit le rang déclaré, jamais l'alphabet.
- En-tête : taille réduite, largeur par défaut 2,5 cm, le plus souvent un seul logo sauf co-tutelle déclarée.
- Pied : la plus petite taille des quatre usages, largeur par défaut 2 cm, discret par construction.
- Co-signature : tous les logos autorisés pour cet usage s'alignent dans l'ordre protocolaire du rang. Deux tutelles ou plus (école et laboratoire, entreprise et financeur) s'alignent côte à côte, jamais superposées ni fondues en une seule image.

Une variante claire ou sombre du même logo se choisit selon le fond du support (un fond sombre appelle la variante claire du logo). Le registre ne modélise pas cette bascule automatiquement, elle reste un choix de l'auteur au moment du placement. Un logo ne se pose jamais sans zone opaque sur une image chargée en arrière-plan : la lisibilité du logo prime sur l'esthétique du fond.

## Vérifications de `valider`

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/logos.py valider registre-logos.json
```

Erreur bloquante : identifiant manquant, identifiant dupliqué, fichier absent, usage inconnu (hors des quatre usages du registre), ratio déclaré non respecté par les pixels réels du fichier.

Avertissement consultatif, jamais bloquant : résolution effective sous 300 points par pouce pour un usage imprimé (page de garde, co-signature) ou sous 150 pour un usage écran (en-tête, pied), format matriciel là où un format vectoriel tiendrait mieux à l'agrandissement, dimensions illisibles qui empêchent la mesure.

La résolution effective se calcule en divisant les pixels de largeur du fichier par la largeur d'affichage en pouces. Ce calcul est plus juste qu'un simple compte de pixels : un logo de 3000 pixels de large reste net affiché en pleine page mais devient flou affiché à 2 cm en pied, puis net à nouveau affiché à 20 cm en page de garde. La résolution effective capture cette dépendance à l'usage, un compte de pixels brut ne la voit pas.

## Placement par format

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/logos.py placer registre-logos.json --usage page-garde --format html
```

En HTML et en LaTeX, le script rend un fragment prêt à insérer (une balise `img` stylée, une commande `includegraphics`). En docx, le script rend les chemins des fichiers, l'insertion réelle passe par `gabarit.py remplir --logo`, qui écrit aussi la relation OOXML et le manifeste de types (voir `produire`, action gabarit). Un logo dont le fichier est absent est écarté du placement plutôt que référencé à vide dans le fragment produit.

## Tutelles multiples

Une école et un laboratoire, une entreprise et un financeur : deux organisations peuvent imposer chacune sa propre charte de logo, taille minimale ou zone de respiration. Ces deux chartes ne se moyennent pas. Quand elles se contredisent (une taille minimale de l'une qui dépasse la largeur maximale tolérée par l'autre), le désaccord se nomme à l'utilisateur, qui tranche.

## Règles

1. Un logo suit les règles de son propriétaire, pas la charte graphique du document.
2. Une erreur de format ou de fichier bloque le placement, une résolution basse ou un format matriciel n'avertit que.
3. Un fichier absent écarte le logo du placement plutôt que de le référencer à vide.
4. Deux chartes de logo contradictoires ne se moyennent pas, le désaccord se signale.
