# Lettre de décision éditoriale

Gabarit de sortie pour une revue par consensus (`references/consensus.md`) quand l'enjeu justifie une décision formelle et traçable, dans un format plus complet que celui de `references/revue.md`. La lettre rend visible non seulement le verdict mais la façon dont il a été obtenu : qui a voté quoi, avec quelle confiance et comment chaque désaccord a été tranché.

## 1. Verdict (une valeur parmi quatre)

- Accepter
- Révision mineure
- Révision majeure
- Refus, avec un sous-type nommé : hors périmètre, défaut fondamental, contribution insuffisante, prématuré ou à retravailler en profondeur

Le sous-type de refus se choisit en lecture humaine à partir du détail des constats, pas par une formule automatique : `scripts/scorecard.py` propose un sous-type indicatif en commentaire (voir section suivante et `_cablage-lot2.md`), jamais un verdict définitif.

## 2. Tableau des votes

| Voix | Recommandation | Confiance (1-5) |
| --- | --- | --- |
| controle-qualite | [verdict] | [1-5] |
| contradicteur | [verdict] | [1-5] |
| verificateur-faits | [verdict] | [1-5] |

Grille de confiance : 5 signifie une voix très sûre de sa recommandation sur ce point précis. 4 signifie confiante avec une réserve mineure déclarée. 3 signifie incertaine, l'avis pèse moins dans l'arbitrage. 2 signifie peu confiante, le point se signale sans s'imposer. 1 signifie que la recommandation de cette voix est ignorée dans l'agrégation du verdict, mais ses commentaires restent conservés dans le rapport complet : une confiance basse ne supprime jamais la trace de ce qui a été dit.

## 3. Analyse de consensus et arbitrage des désaccords

Classer l'accord entre les voix en trois cas : unanime (les trois voix convergent), majoritaire (deux voix contre une, la voix dissidente nommée) ou partagé (désaccord réel qui exige un arbitrage). Pour chaque désaccord partagé, préciser son type (désaccord de fait vérifiable, désaccord de jugement sur la sévérité ou désaccord de portée sur ce que le document doit couvrir) et motiver l'arbitrage : quelle donnée ou quel critère fait pencher la décision, pas seulement laquelle des voix l'emporte.

## 4. Révisions obligatoires et révisions suggérées

Deux tableaux distincts, jamais fusionnés.

Révisions obligatoires (numéro, source, sévérité, section visée, effort estimé), une fiche par item avec la justification précise. Révisions suggérées, listées séparément, sans effort estimé obligatoire puisqu'elles n'engagent pas la décision.

## 5. Feuille de route en trois priorités

P1 (bloquant, condition du prochain tour), P2 (attendu, forte proportion à traiter), P3 (optionnel, sans effet sur la décision), avec un effort total estimé par priorité et une date indicative si le contexte s'y prête.

## 6. Correspondance sévérité vers priorité

| Sévérité | Priorité |
| --- | --- |
| Critique | P1 |
| Majeur | P1 si l'affirmation centrale est touchée, P2 sinon |
| Mineur | P2 si répété sur plusieurs sections, P3 sinon |

## Format de sortie imposé

```
Verdict : [Accepter / Révision mineure / Révision majeure / Refus (sous-type)]

Votes :
- controle-qualite : [verdict] - confiance [1-5] - [motif clé]
- contradicteur : [verdict] - confiance [1-5] - [faille principale]
- verificateur-faits : [verdict] - confiance [1-5] - [affirmation à étayer]

Analyse de consensus : [unanime / majoritaire (dissident : X) / partagé]
Désaccords arbitrés :
- [type] -> [arbitrage motivé]

Révisions obligatoires :
| # | Source | Sévérité | Section | Effort |

Révisions suggérées :
| # | Source | Section |

Feuille de route :
- P1 (bloquant) : [items], effort [estimation]
- P2 (attendu) : [items], effort [estimation]
- P3 (optionnel) : [items]

Justification (200 à 300 mots) : [paragraphe]
```

## Sources

- ICMJE. C. Responsibilities in the Submission and Peer-Review Process. https://www.icmje.org/recommendations/browse/roles-and-responsibilities/responsibilities-in-the-submission-and-peer-peview-process.html (consultée le 2026-07-08)
- COPE. Ethical guidelines for peer reviewers. https://publicationethics.org/guidance/guideline/ethical-guidelines-peer-reviewers (consultée le 2026-07-08)
