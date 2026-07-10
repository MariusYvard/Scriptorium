# Standards de compte rendu (au-dela de PRISMA)

Dix standards du reseau EQUATOR (Enhancing the QUAlity and Transparency Of health Research), chacun propre a un type d'etude. `references/prisma.md` couvre deja la revue systematique et la meta-analyse : ce fichier couvre les neuf autres devis les plus courants plus CONSORT. Chaque compte d'items ci-dessous est verifie a la source primaire (site du standard ou equator-network.org), pas repris d'une source secondaire sans controle.

## 1. Tableau des dix standards

| Standard | Perimetre | Items (verifie) | Source primaire |
| --- | --- | --- | --- |
| CONSORT | Essai randomise controle | 25 (CONSORT 2010) ; une version CONSORT 2025 a 30 items existe depuis 2025, voir note | consort-statement.org/consort-2010 |
| STROBE | Etude observationnelle (cohorte, cas-temoins, transversale) | 22 | strobe-statement.org/checklists |
| SPIRIT | Protocole d'essai clinique | 33 (SPIRIT 2013) ; une version SPIRIT 2025 a 34 items existe depuis 2025, voir note | consort-spirit.org |
| STARD | Etude de precision diagnostique | 30 | equator-network.org, checklist STARD 2015 |
| TRIPOD | Modele de prediction diagnostique ou pronostique | 27 (TRIPOD+AI, remplace TRIPOD 2015) | tripod-statement.org/scope |
| ARRIVE | Recherche animale in vivo | 21 (10 items essentiels et 11 items recommandes, ARRIVE 2.0) | arriveguidelines.org/arrive-guidelines |
| CARE | Cas clinique ou serie de cas | 13 | care-statement.org/checklist |
| SQUIRE | Amelioration de la qualite des soins | 18 (SQUIRE 2.0) | squire-statement.org, page SQuIRE 2.0 |
| CHEERS | Evaluation economique en sante | 28 (CHEERS 2022, remplace les 24 items de CHEERS 2013) | ispor.org, page CHEERS 2022 |
| SRQR | Recherche qualitative | Non confirme en acces libre a la date de redaction (texte integral payant), voir note | equator-network.org/reporting-guidelines/srqr |

Note sur CONSORT et SPIRIT : les deux standards ont ete revises en 2025 sur un nouveau site conjoint (consort-spirit.org, finance par le MRC et le NIHR britanniques), qui annonce un CONSORT a 30 items et un SPIRIT a 34 items. Les sites historiques consort-statement.org et spirit-statement.org restent en ligne et presentent encore les versions 2010 (25 items) et 2013 (33 items) comme courantes au moment de la verification. Retenir la version exigee explicitement par la revue ou l'organe cible ; a defaut d'exigence precisee, verifier laquelle des deux versions est en vigueur au moment de la soumission plutot que de supposer.

Note sur SRQR : le standard existe et sa reference bibliographique est confirmee (O'Brien BC, Harris IB, Beckman TJ, Reed DA, Cook DA. Standards for reporting qualitative research: a synthesis of recommendations. Academic Medicine, 2014, 89(9):1245-1251), mais son texte integral se trouve derriere un paiement (Oxford Academic). Le nombre d'items exact n'est donc pas confirme ici a la source primaire et n'est pas avance. Verifier le compte directement sur le texte integral avant de l'inserer dans un document.

## 2. Quand exiger quel standard

| Devis de l'etude | Standard a exiger |
| --- | --- |
| Essai randomise controle | CONSORT |
| Cohorte, cas-temoins ou etude transversale | STROBE |
| Protocole d'essai avant son lancement | SPIRIT |
| Test diagnostique (sensibilite, specificite) | STARD |
| Modele predictif (diagnostique ou pronostique, y compris apprentissage automatique) | TRIPOD (TRIPOD+AI si le modele repose sur l'apprentissage automatique) |
| Etude animale in vivo | ARRIVE |
| Cas clinique ou serie de cas | CARE |
| Projet d'amelioration de la qualite des soins | SQUIRE |
| Evaluation cout-efficacite ou cout-utilite | CHEERS |
| Entretiens, groupes focalises, ethnographie | SRQR |

Le genre `genre-cas-clinique.md` et le genre `genre-rapport-scientifique.md` renvoient ici pour choisir leur standard. `references/revue-litterature.md` y renvoie aussi : le devis de chaque source incluse dans une synthese determine quel standard cette source aurait du suivre.

## 3. Regle : declaration au cadrage, verification a la revue

Le standard applicable se declare des le cadrage (`atelier` cadrer), au moment ou le devis de l'etude est fixe : un essai randomise sait des le depart qu'il repondra devant CONSORT, un cas clinique devant CARE. La verification effective (chaque item du standard couvert, avec sa localisation dans le texte) se fait a la revue (`controler` revue ou audit), jamais avant : verifier un standard sur un brouillon incomplet produit une liste de manques qui n'ont pas encore de raison d'etre combles.

Le controle reste manuel : aucun script du plugin n'automatise la verification d'un standard de compte rendu, la nature du contenu attendu par chaque item (une phrase decrivant l'insu, un tableau de caracteristiques de base) demande un jugement de lecture.

## Sources

- EQUATOR Network. https://www.equator-network.org/
- CONSORT 2010 Statement. https://www.consort-statement.org/consort-2010
- CONSORT 2025 et SPIRIT 2025 (site conjoint). https://www.consort-spirit.org/
- STROBE Statement, checklists. https://www.strobe-statement.org/checklists/
- SPIRIT 2013 Statement (EQUATOR Network). https://www.equator-network.org/reporting-guidelines/spirit-2013-statement-defining-standard-protocol-items-for-clinical-trials/
- STARD 2015 (EQUATOR Network). https://www.equator-network.org/reporting-guidelines/stard/
- TRIPOD et TRIPOD+AI. https://www.tripod-statement.org/scope
- ARRIVE guidelines 2.0. https://arriveguidelines.org/arrive-guidelines
- CARE Checklist. https://www.care-statement.org/checklist
- SQUIRE 2.0. https://www.squire-statement.org/index.cfm?fuseaction=Page.ViewPage&pageId=525
- CHEERS 2022 (ISPOR). https://www.ispor.org/heor-resources/good-practices/article/consolidated-health-economic-evaluation-reporting-standards-2022-cheers-2022-statement-updated-reporting-guidance-for-health-economic-evaluations
- CHEERS 2022 (EQUATOR Network). https://www.equator-network.org/reporting-guidelines/cheers/
- SRQR (EQUATOR Network). https://www.equator-network.org/reporting-guidelines/srqr/
