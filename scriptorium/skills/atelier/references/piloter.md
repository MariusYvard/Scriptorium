# Atelier (pipeline de bout en bout)

Orchestrer la production d'un document complet en enchaînant quatre étapes. Cette compétence ne réécrit pas la méthode de chaque étape, elle appelle les compétences spécialisées dans le bon ordre et garde la cohérence d'ensemble.

## Quand router vers une seule étape

Si la demande ne porte que sur une étape (par exemple "trouve-moi des sources" ou "révise ce brouillon"), ne pas lancer tout le pipeline. Charger directement la compétence concernée (`atelier` (cadrer), `produire` (sourcer), `produire` (genre), `controler` (revue), `produire` (style)). L'atelier sert quand l'utilisateur veut un livrable abouti à partir d'un sujet. En cas de doute sur la sous-commande à charger face à une formulation ambiguë ("vérifie ce texte", "fais une synthèse"), consulter `aiguilleur.md`.

## Mémoire de projet

Au démarrage, si `projet.json` existe dans le dossier de travail, le recharger (voir `atelier` (projet)) pour reprendre le genre, la problématique, la charte et le plan sans les redemander. Sinon, l'initialiser au cadrage. Consulter `python3 scripts/project.py status` à tout moment pour un tableau de bord de l'état courant (étapes, artefacts, frontières, outrepassements) : voir `projet.md`.

## Pipeline en cinq temps

### 1. Cadrage

Charger la compétence `atelier` (cadrer). Établir le brief (commanditaire, problème déclencheur, public, contraintes de volume, jalons), appliquer les cinq filtres de délimitation, qualifier le sujet (cadre FINER, `cadre-finer.md`), formuler la problématique en question fermée, choisir le genre, produire un plan validé. Ne pas avancer tant que le genre et le plan ne sont pas confirmés par l'utilisateur. Marquer l'étape dans la mémoire de projet (`project.py etape cadrage en_cours` puis `termine`).

### 2. Sourcing

Charger la compétence `produire` (sourcer). Réunir les faits, chiffres et références qu'exige le plan. Pondérer chaque source par fiabilité et récence. Construire la carte preuve-affirmation qui relie chaque affirmation prévue à une preuve datée. Signaler les zones où la preuve manque avant d'écrire, pour éviter de rédiger des paragraphes que les faits ne soutiennent pas. En cas de sources introuvables ou contradictoires, voir `chemins-defaillance.md` (D1).

### 3. Rédaction

Charger la compétence `produire` (genre). Charger le playbook du genre retenu. Pour un document long (de plus de cinq pages ou à plusieurs sections denses), déléguer la rédaction à l'agent `redacteur` section par section. Appliquer le style maison à chaque paragraphe. Suivre le triptyque annonce, développement, synthèse et la progression connu-inconnu. Si l'analyse comporte des figures (SWOT, BCG, PESTEL, chaîne de valeur), les produire avec `produire` (figure), audit critique compris.

### 4. Révision

Charger la compétence `controler` (revue). Lancer la revue adversariale et le contrôle qualité via l'agent `controle-qualite`. Vérifier la carte preuve-affirmation, l'auto-revue en cinq dimensions, la conformité au style maison, la sévérité des constats et le verdict. Corriger tout constat critique avant de présenter le document. Lancer l'audit consolidé (`scripts/audit-doc.py`) et la conformité au plan (`scripts/plan-check.py`). Pour une thèse à fort enjeu, éprouver le raisonnement avec `controler` (contredire) (agent `contradicteur`). Si le dialogue de revue s'étire sur plusieurs tours, surveiller la santé du dialogue (`controler/references/sante-dialogue.md`).

### 5. Finalisation

Mettre en forme le livrable avec la compétence `livrer` (document) (Word ou PDF selon les conventions du genre) : page de garde, sommaire, bibliographie formatée, annexes, et si pertinent un résumé analytique ou un abstract. Joindre une note de version courte qui liste ce qui a été vérifié et ce qui reste ouvert. Présenter le fichier final à l'utilisateur, puis produire le bilan de fin de mission (voir plus bas).

## Points de contrôle obligatoires

Marquer une pause et demander validation à trois moments, jamais en bloc.

1. Après le cadrage : genre, problématique et plan.
2. Après le sourcing : suffisance des preuves et zones à risque.
3. Après la révision : verdict et constats critiques restants.

Entre ces points, avancer sans interrompre l'utilisateur à chaque micro-décision. Garde-fou de vigilance : après cinq relances brèves consécutives ("continue", "ok", "vas-y" ou équivalent, sans contenu nouveau), marquer un point de contrôle supplémentaire même hors des trois moments prévus. Rappeler l'objectif, ce qui est produit et ce qui reste, puis demander confirmation avant de poursuivre : une longue série d'acquiescements n'est pas une validation du travail produit. Si un point de contrôle échoue de façon répétée (sujet qui reste trop large, scorecard qui stagne sous le seuil, désaccord de consensus qui persiste), consulter `chemins-defaillance.md` plutôt que de répéter la même correction.

## Renforcement aux transitions

À chaque changement de phase, rappeler une règle ferme et un anti-pattern pertinent pour la phase suivante. Cette discipline compense l'érosion du contexte sur les sessions longues.

| Transition | Règle ferme rappelée | Anti-pattern pour la phase suivante |
|---|---|---|
| Vers le cadrage | Ne pas avancer tant que genre, problématique et plan ne sont pas validés | Sourcer sans cible : chercher des preuves avant que le plan ne dise ce qu'il faut démontrer |
| Cadrage vers sourcing | Chaque affirmation prévue reçoit une preuve datée ou un tag de lacune, jamais un vide silencieux | Rédiger avant de sourcer (voir `aiguilleur.md`) : écrire un paragraphe que les preuves ne soutiennent pas encore |
| Sourcing vers rédaction | Ne pas écrire un paragraphe que les preuves ne soutiennent pas ; l'affaiblir ou le retirer | Réviser avant de vérifier les faits : laisser un chiffre non confirmé passer en revue de style |
| Rédaction vers révision | Classer chaque constat par sévérité, corriger tout critique avant de présenter le document | Livrer sans contrôle : mettre en forme un texte que la revue n'a pas déclaré prêt |
| Révision vers finalisation | Ne mettre en forme qu'un texte dont la révision a rendu un verdict prêt | Clore la mission sans bilan ni auto-audit : une complaisance non déclarée reste invisible |
| Finalisation vers bilan | Le bilan cite les instructions initiales telles quelles, jamais reformulées de mémoire | Un bilan complaisant qui ne nomme aucune concession ni aucun contrôle sauté |

## Bilan de fin de mission

Après la finalisation, produire deux volets distincts.

### 1. Récapitulatif

- Instructions initiales, citées aussi textuellement que possible plutôt que résumées de mémoire.
- Décisions clefs prises en cours de mission (genre, périmètre, angle, arbitrages de consensus), tirées du journal de projet (`project.py status`, ou entrées journalisées avec `project.py decision "libellé"`).
- Corrections de cap : tout changement de plan, de genre ou de périmètre après validation initiale, avec sa raison.
- Statistiques : nombre de sources, verdict final de scorecard, nombre de tours de révision, nombre de frontières posées, nombre d'outrepassements (`project.py status`).

### 2. Auto-audit de l'assistant

- Taux de concession du contradicteur, si `controler` (consensus) ou `controler` (contredire) a tourné (voir `controler/references/contredire.md`, discipline de concession).
- Contrôles sautés : étapes en état `saute` (`project.py status`) ou vérification annoncée mais non exécutée.
- Outrepassements : compte et cran maximal atteint (`project.py status`, voir aussi la friction ci-dessous).
- Risque de complaisance en trois paliers.
  - Faible : aucune alerte de santé du dialogue déclenchée, aucun outrepassement, taux de concession sous 50 % si mesuré.
  - Moyen : une alerte de santé du dialogue déclenchée, ou un outrepassement de cran 1 ou 2, ou taux de concession entre 50 et 75 %.
  - Élevé : plusieurs alertes non traitées, ou un outrepassement de cran 3, ou taux de concession au-dessus de 75 %, ou un contrôle sauté sans motif tracé.

Réserve explicite : ce palier est estimé par le même assistant qui a conduit la mission. L'auditeur est l'audité. Le signaler dans le bilan plutôt que de présenter ce chiffre comme une mesure indépendante.

## Friction des outrepassements

Quand l'utilisateur force le passage outre un blocage (seuil de scorecard, vérification de sources, revue non conclue), le passage suit l'échelle de friction à trois crans de `tools/check.py` : premier passage avec simple avertissement, deuxième avec justification demandée, troisième avec justification substantielle exigée. Chaque passage outre se journalise (mémoire de projet si `projet.json` existe, sinon `.outrepassements.json`), jamais en silence. Voir `chemins-defaillance.md` (D12) pour le message à adapter à l'utilisateur.

## Format de sortie

Produire un fichier de document (Word, PDF ou Markdown selon la demande) plus une note de version. La note de version contient : le genre retenu, le périmètre validé, le nombre de sources et leur pondération moyenne, le verdict de révision, les questions ouvertes restantes avec une recommandation pour chacune.

## Règles

1. Respecter le style maison par défaut (voir `produire` (style)) sur tout le document.
2. Ne jamais inventer une source ni un chiffre. Une affirmation sans preuve est affaiblie ou retirée.
3. Garder la terminologie stable d'un bout à l'autre.
4. Tenir le périmètre validé au cadrage. Toute donnée hors démonstration part en encadré ou en annexe.
5. Échouer bruyamment : si une étape n'aboutit pas, le dire et nommer ce qui bloque, plutôt que de livrer un document incomplet présenté comme terminé.
