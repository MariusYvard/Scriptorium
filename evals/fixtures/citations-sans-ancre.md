<!--
Fixture a double usage (test dans evals/run-evals.py et gabarit de reference
montrable a l'utilisateur). Le bloc BibTeX ci-dessous contient 3 entrees :
"ancre_citation2024" porte une ancre par citation exacte (champ annote),
"ancre_localisation2022" porte une ancre par localisation (champ note, "p.
118"), "orphan2024" n'a ni l'un ni l'autre : scripts/citations.py
(rapport_ancrage) doit la signaler seule dans "sans_ancre". Sert aussi de
gabarit : a quoi ressemble une bibliographie correctement ancree face a une
entree fautive.
-->

# Exemple : bibliographie avec une citation sans ancre

Extrait de bibliographie annotee. Deux entrées portent une ancre exploitable
(une citation exacte de 25 mots au plus ou une localisation précise), une
troisième n'en porte aucune : un signal à corriger avant publication, voir
`skills/produire/references/integrite-sources.md`.

```bibtex
@article{ancre_citation2024,
  author = {Dupont, Marie},
  title = {Effets mesures de la reforme sur l'emploi local},
  journal = {Revue d'economie appliquee},
  year = {2024},
  doi = {10.1000/exemple.001},
  annote = {La reforme a reduit le chomage local de 3,2 points en dix-huit mois}
}
@book{ancre_localisation2022,
  author = {Martin, Paul},
  title = {Politiques publiques et emploi},
  publisher = {Editions du Savoir},
  year = {2022},
  note = {p. 118}
}
@article{orphan2024,
  author = {Nguyen, Thi},
  title = {Reforme et marche du travail : un panorama},
  journal = {Cahiers de politique economique},
  year = {2024}
}
```

Vérification attendue :

```
python3 scripts/citations.py FICHIER.bib --exiger-ancres
```

Code de sortie 1, `orphan2024` seule listée dans `ancrage.sans_ancre`, les deux autres classées `citation` et `localisation`.
