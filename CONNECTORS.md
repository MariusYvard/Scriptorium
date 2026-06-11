# Connecteurs

Scriptorium fonctionne en autonomie. Il utilise la recherche web pour sourcer et vérifier les faits. Les connecteurs ci-dessous sont optionnels : ils enrichissent le sourcing sans jamais être requis.

## Comment fonctionnent les références d'outils

Les fichiers du plugin désignent les outils par catégorie, avec un marqueur `~~categorie`, et non par produit. Une catégorie correspond à l'outil que vous connectez. La personnalisation remplace ces marqueurs par les noms réels (voir la compétence de personnalisation de plugin).

## Catégories utilisées

| Catégorie | Marqueur | Sert à | Exemples |
| --- | --- | --- | --- |
| Gestionnaire de références | `~~gestionnaire de references` | Puiser dans une bibliothèque de sources déjà constituée | Zotero, Mendeley |
| Base de connaissances | `~~base de connaissances` | Récupérer des documents internes, notes, rapports | Notion, Confluence, Google Drive, SharePoint |

## Dégradation gracieuse

Sans connecteur, `sourcer` et l'agent `synthese-sources` s'appuient sur la recherche web seule, ce qui suffit pour la plupart des écrits. Si un gestionnaire de références ou une base de connaissances est connecté, ils l'interrogent en plus, pour réutiliser des sources déjà validées et des documents internes. Aucune compétence ne tombe en panne en l'absence de connecteur.

## Vérification des sources

Quelle que soit l'origine d'une source, elle passe par le script `scripts/verify-sources.py` : nettoyage des paramètres de suivi, détection des doublons, contrôle des DOI. Un connecteur ne dispense jamais de la vérification.
