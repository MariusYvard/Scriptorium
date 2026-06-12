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
| Sciences dures et ingénierie | Vancouver ou IEEE | IMRAD, spécification d'exigences | publication évaluée par les pairs, donnée primaire, standards |
| Sciences humaines et sociales | APA 7 | introduction, développement argumenté, conclusion | ouvrages de référence, articles évalués |
| Droit | propre au champ | IRAC, plan binaire ou ternaire | textes, jurisprudence, doctrine |
| Gestion et conseil | libre ou APA | résumé analytique, constat, diagnostic, recommandations | rapports sectoriels, données d'entreprise |
| Médecine et santé | Vancouver | IMRAD, CARE, CONSORT, STROBE, PRISMA | essais cliniques, méta-analyses |
| Analyse géopolitique et prospective | sources primaires datées | acteurs, rapports de force, scénarios contrastés | sources primaires, institutions, presse de référence recoupée |
| Communication et marketing | libre ou APA | accroche, message clé, preuve, appel à l'action | études de marché, données d'usage, sources sectorielles |
| Présentation et soutenance | selon le cadre | une idée par diapositive, fil narratif | données clés, figures sourcées |
| Travail étudiant | APA 7 ou consigne | structure imposée par la consigne | cours, manuels, articles évalués |
| Finance et investissement | CFA, sources datées | thèse, valorisation, risques | états financiers, données de marché |
| Évaluation et secteur public | critères OCDE/CAD | pertinence, efficacité, impact, durabilité | données officielles, rapports d'évaluation |
| Entrepreneuriat | libre | résumé, marché, modèle, finances | études de marché, données sectorielles |
| Enseignement et pédagogie | APA 7 ou consigne | objectifs, progression, évaluation | manuels, articles évalués, programmes |
| Gestion de projet | libre | besoin, exigences, jalons, risques | cahier des charges, données de projet |
| Journalisme | propre au média | accroche, faits vérifiés, sources croisées | sources primaires recoupées, témoignages |

## Sources normatives

- IMRAD et manuscrit scientifique : ICMJE. https://www.icmje.org/recommendations/browse/manuscript-preparation/preparing-for-submission.html
- Revue systématique : PRISMA 2020. https://www.prisma-statement.org/prisma-2020
- Essai randomisé, étude observationnelle, cas clinique : CONSORT (https://www.consort-spirit.org/), STROBE (https://www.strobe-statement.org/), CARE (https://www.care-statement.org/checklist)
- Ingénierie des exigences : IEEE/ISO/IEC 29148-2018. https://standards.ieee.org/ieee/29148/6937/
- Raisonnement juridique (IRAC) : Writing Center, Columbia Law School. https://www.law.columbia.edu/sites/default/files/2022-06/WC%20Handout%20IRAC%2C%20CRAC%2C%20CREAC.revised%205.22.pdf
- Évaluation : critères du CAD de l'OCDE. https://www.oecd.org/dac/evaluation/daccriteriaforevaluatingdevelopmentassistance.htm
- Analyse financière : CFA Institute, Equity Research Report Essentials. https://www.cfainstitute.org/sites/default/files/-/media/documents/support/research-challenge/challenge/rc-equity-research-report-essentials.pdf
- Documentation technique : Diátaxis. https://diataxis.fr/

## Usage

Le profil ajuste la norme et la structure, il ne baisse jamais l'exigence de preuve. Le seuil de scorecard reste élevé (85 par défaut). Une discipline qui tolère un plan particulier ne tolère pas une affirmation non étayée.
