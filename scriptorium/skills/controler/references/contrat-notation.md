# Contrat de notation préenregistré

Fixer la grille de notation avant de lire le document, pas après. Une voix qui lit d'abord le texte puis ajuste son barème pour justifier le verdict qu'elle a déjà en tête ne note plus, elle rationalise. Le contrat de notation préenregistré sert de garde contre ce biais, pour la revue par consensus (`references/consensus.md`) et pour toute lettre de décision à enjeu (`references/lettre-decision.md`).

## 1. Deux phases séparées

Phase aveugle (avant lecture) : chaque voix (`controle-qualite`, `contradicteur`, `verificateur-faits`) reçoit uniquement le contrat, jamais le texte. Elle paraphrase chaque dimension et chaque condition d'échec avec ses propres mots, puis s'engage par écrit sur un plan de notation daté avant d'avoir vu la moindre phrase du document.

Phase de lecture (après engagement) : la voix reçoit le texte réel, note chaque dimension contre l'engagement pris, vérifie chaque condition d'échec. Le plan de notation de la phase aveugle reste affiché à côté du résultat final, pour qu'un écart entre l'engagement et la notation réelle saute aux yeux plutôt que de rester invisible.

## 2. Contenu du plan de notation

Chaque voix produit trois éléments avant lecture.

- Dimensions d'acceptation : reprises du profil de discipline actif (`references/profils-discipline.md`) ou des cinq axes de `references/grille-revue.md` selon le contexte.
- Conditions d'échec : chacune porte un identifiant court (F1, F2...), une sévérité (critique, majeur, mineur, voir `references/grille-revue.md`) et un quantificateur d'agrégation (section 5).
- Procédure de mesure : comment la condition sera vérifiée concrètement (quel script déterministe, quelle question posée au texte, quelle section examinée en priorité).

## 3. Interdits fermes

- Moyenne qui masque un désaccord : quand deux dimensions jugées par la même voix pointent dans des directions contradictoires, les deux scores sont rapportés tels quels, jamais lissés en une moyenne qui efface le désaccord.
- Adoucissement après coup : le plan de notation engagé en phase aveugle ne se réécrit pas après lecture pour coller à un verdict plus confortable. Un changement de barème après lecture se déclare comme tel, il ne se dissimule pas.
- Score de substitution : quand une voix ne produit aucun rapport exploitable (échec technique, réponse hors sujet), elle est déclarée manquante dans l'agrégation. Aucune moyenne des voix restantes ni aucune estimation ne comble ce vide en silence.
- Deux dimensions contradictoires jamais lissées : reprise du premier interdit, appliquée aussi au niveau de l'agrégation entre voix (voir `references/consensus.md`).

## 4. Dissidence

Une voix peut exprimer une dissidence limitée à une seule dimension : elle rejoint le consensus sur l'ensemble mais maintient un désaccord motivé sur un point précis. Deux dissidences simultanées (deux voix dissidentes sur des dimensions différentes ou une voix dissidente sur deux dimensions) déclenchent un unique nouveau cycle de notation complet. Ce cycle ne se répète pas indéfiniment : une seule reprise est autorisée, la dissidence résiduelle après ce second cycle se tranche par la procédure d'agrégation normale (section 5), pas par un troisième tour.

## 5. Agrégation mécanique

Chaque condition d'échec est évaluée par le quantificateur fixé dans le contrat avant la lecture, jamais choisi après coup pour obtenir le résultat voulu.

- Au moins un : une seule voix qui déclenche la condition suffit à la retenir.
- Majorité : plus de la moitié des voix actives la déclenchent (une voix manquante, voir section 3, ne compte ni pour ni contre).
- Tous : toutes les voix actives doivent la déclencher.

Quand plusieurs conditions se déclenchent en même temps, la précédence de sévérité tranche : critique l'emporte sur majeur, majeur sur mineur. Une égalité entre deux conditions de même sévérité se résout par l'ordre où elles apparaissent dans le contrat, pas par un choix fait après coup.

## 6. Exemple minimal de contrat

```json
{
  "dimensions": ["Preuve et rigueur", "Structure et clarte", "Style maison"],
  "conditions_echec": [
    {"id": "F1", "severite": "critique", "quantificateur": "au moins un", "description": "affirmation centrale non etayee"},
    {"id": "F2", "severite": "majeur", "quantificateur": "majorite", "description": "structure du genre non respectee"}
  ],
  "procedure_mesure": "carte preuve-affirmation (grille-revue.md) plus scripts deterministes (scorecard.py, traceability.py)"
}
```

## Sources

- Center for Open Science. Preregistration. https://www.cos.io/initiatives/prereg (consultée le 2026-07-08)
- Kerr, N. L. (1998). HARKing: Hypothesizing After the Results are Known. Personality and Social Psychology Review, 2(3), 196-217. https://doi.org/10.1207/s15327957pspr0203_4
