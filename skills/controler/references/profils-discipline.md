# Profils de discipline

Chaque profil cale la norme de citation, la structure attendue et la pondération des sources. Un fichier `profil.json` dans le dossier de travail peut fixer ces choix une fois pour toutes.

## Format profil.json

```json
{
  "discipline": "sciences-dures",
  "norme_citation": "vancouver",
  "structure": "IMRAD",
  "seuil_scorecard": 85,
  "sources_privilegiees": ["publication evaluee par les pairs", "donnee primaire"]
}
```

## Profils de référence

| Discipline | Norme | Structure | Sources privilégiées |
| --- | --- | --- | --- |
| Sciences dures et ingénierie | Vancouver | IMRAD | publication évaluée par les pairs, donnée primaire |
| Sciences humaines et sociales | APA 7 | introduction, développement argumenté, conclusion | ouvrages de référence, articles évalués |
| Droit | propre au champ | plan binaire ou ternaire | textes, jurisprudence, doctrine |
| Gestion et conseil | libre ou APA | résumé analytique, constat, diagnostic, recommandations | rapports sectoriels, données d'entreprise |
| Médecine et santé | Vancouver | IMRAD, lignes directrices CONSORT ou PRISMA | essais cliniques, méta-analyses |
| Analyse géopolitique et prospective | sources primaires datées | acteurs, rapports de force, scénarios contrastés | sources primaires, institutions, presse de référence recoupée |
| Communication et marketing | libre ou APA | accroche, message clé, preuve, appel à l'action | études de marché, données d'usage, sources sectorielles |
| Présentation et soutenance | selon le cadre | une idée par diapositive, fil narratif | données clés, figures sourcées |
| Travail étudiant | APA 7 ou consigne | structure imposée par la consigne | cours, manuels, articles évalués |

## Usage

Le profil ajuste la norme et la structure, il ne baisse jamais l'exigence de preuve. Le seuil de scorecard reste élevé (85 par défaut). Une discipline qui tolère un plan particulier ne tolère pas une affirmation non étayée.
