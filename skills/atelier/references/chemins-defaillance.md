# Chemins de défaillance (atelier)

Douze scénarios d'échec nommés, chacun avec son symptôme, un message prêt à adapter pour l'utilisateur et un chemin de récupération vers la bonne sous-commande. Consulter cette liste dès qu'une étape de `piloter.md` bloque, plutôt que d'improviser une réponse au cas par cas.

## D1. Sources introuvables ou contradictoires

Symptôme : aucune source vérifiable ne couvre une affirmation prévue au plan, ou deux sources de niveau de preuve comparable se contredisent sans qu'un facteur de contexte explique l'écart.

Message : "Aucune source vérifiable ne soutient [affirmation] pour l'instant (ou : les sources disponibles se contredisent sans facteur qui explique l'écart). Je peux élargir la recherche, affaiblir l'affirmation en la qualifiant, ou la retirer du plan."

Récupération : retour à `produire` (sourcer), `hierarchie-preuve.md` et `discipline-synthese.md`. Si la contradiction persiste, marquer `[LACUNE MATERIELLE]` et continuer plutôt que de bloquer tout le document.

## D2. Matériau fourni illisible

Symptôme : un fichier fourni par l'utilisateur (PDF scanné, export corrompu, encodage cassé) ne s'extrait pas.

Message : "Le fichier [nom] ne s'ouvre pas correctement ([raison technique brève]). Je peux continuer sans lui en le signalant comme absent, ou vous pouvez fournir une autre version (texte brut, export propre, sortie OCR)."

Récupération : repli gracieux comme documenté dans `produire/references/corpus-utilisateur.md` (lecture seule, rien d'écarté en silence). Consigner l'échec dans le bloc de traçabilité plutôt que d'abandonner tout le sourcing.

## D3. Sujet trop large après cadrage

Symptôme : même après les cinq filtres de délimitation, le plan garde plus de sections que le volume cible ne peut soutenir, ou le critère faisable du cadre FINER reste à 1.

Message : "Le sujet reste trop large pour le format visé ([volume cible]) même après délimitation. Je propose de le resserrer sur [sous-thème le plus solide] et de traiter le reste en perspective ou en annexe."

Récupération : repasser par `cadrer.md`, étape des cinq filtres, et par `cadre-finer.md`. Si le critère faisable reste à 1 après resserrement, renoncer au sujet tel quel (voir `cadre-finer.md`, section sous le seuil).

## D4. Contexte saturé en cours de piloter

Symptôme : la session s'allonge (cadrage, sourcing, rédaction et révision cumulés), des décisions déjà validées commencent à se répéter ou à se contredire.

Message : "Cette session porte beaucoup de contexte accumulé. Je fixe l'état courant dans la mémoire de projet avant de continuer, pour ne rien perdre si la session doit reprendre plus tard."

Récupération : `atelier` (projet), poser une frontière (`project.py frontiere "libellé"`) et vérifier `project.py status`. Reprise ultérieure par `project.py reprendre HASH` (voir `projet.md`).

## D5. Désaccord persistant en consensus

Symptôme : après un cycle de renotation, une dissidence documentée par `contrat-notation.md` reste non résolue entre deux voix du consensus.

Message : "Les voix du consensus restent en désaccord sur [dimension] après un cycle de renotation ([voix A] contre [voix B]). Je rapporte les deux scores tels quels plutôt que de les moyenner, et vous demande un arbitrage."

Récupération : `controler` (consensus), section agrégation par quantificateur et interdit de lissage. Si le désaccord porte sur le fond de la thèse, escalader vers `controler` (contredire) pour un test de résistance dédié.

## D6. Scorecard sous le seuil en boucle

Symptôme : deux passes de correction consécutives ne relèvent pas le total du scorecard au-dessus du seuil, ou une dimension reste effondrée sous le plancher.

Message : "Le scorecard reste sous le seuil ([total]/100, seuil [N]) après deux passes de correction. Plutôt que de recommencer à l'identique, je propose de cibler uniquement [axe le plus faible], ou de revoir le seuil avec vous."

Récupération : `scripts/scorecard.py --trajectoire` pour objectiver la régression ou la stagnation. Si l'axe effondré est Sources ou Traçabilité, retour à `produire` (sourcer) plutôt qu'une nouvelle passe de style.

Chemin d'arrêt anticipé : si `scripts/scorecard.py --trajectoire` signale un gain total sous +3 points sans régression sur aucun axe (champ `arret_anticipe` du rapport JSON, voir `controler/references/severite.md` section 2), ne pas relancer une troisième passe identique. Message dédié : "Le gain entre les deux dernières revues est de [delta_total] point(s), sous le seuil de +3 et sans régression. Une nouvelle passe à l'identique a peu de chances d'apporter plus. Je vous propose un arbitrage : accepter l'état actuel, cibler un seul axe précis ou revoir le seuil ensemble." Ce chemin remplace la boucle par un arbitrage explicite avec l'utilisateur plutôt que de relancer indéfiniment la même correction. Le seuil visé peut lui-même venir du type de document (`--seuil-type brouillon|rapport|publication`, 65/80/85 par défaut) plutôt que du seul verdict générique à trois valeurs.

## D7. Charte graphique invalide

Symptôme : `theme.py` signale une couleur mal formée ou un contraste sous 4,5:1 sur un contenu déjà mis en forme.

Message : "La charte graphique contient une erreur ([couleur ou contraste précis]). Je corrige [proposition concrète], ou j'utilise la charte par défaut du plugin en attendant une charte valide."

Récupération : `produire` (charte), revalider avec `theme.py charte.json` avant de relancer `livrer` (document).

## D8. Plan et document divergents

Symptôme : `plan-check.py` signale une section prévue absente, ou une section hors plan non annoncée.

Message : "Le document s'écarte du plan validé ([section manquante ou ajoutée]). Je peux l'aligner sur le plan d'origine, ou vous pouvez valider explicitement cette évolution."

Récupération : `scripts/plan-check.py PLAN.json DOCUMENT.md`. Si l'évolution est voulue, mettre à jour `plan.json` et la mémoire de projet (`project.py artefact plan`) plutôt que de laisser plan et document diverger en silence.

## D9. Glossaire incohérent

Symptôme : `terminology.py` signale un sigle employé avant sa définition, ou deux variantes orthographiques d'un même terme.

Message : "Le terme [terme] apparaît sous deux formes ([variante A], [variante B]), ou est utilisé avant d'être défini. Je fixe une forme unique pour tout le document."

Récupération : `scripts/terminology.py FICHIER`, puis mettre à jour le glossaire de la mémoire de projet (`projet.json`, clé glossaire) pour que la forme retenue survive à la session suivante.

## D10. Sortie tronquée

Symptôme : un export (Word, PDF, HTML) s'arrête avant la fin du document, ou une section attendue manque du fichier final sans message d'erreur.

Message : "L'export généré est incomplet ([section manquante ou fichier coupé]). Je régénère la sortie et vérifie sa longueur avant de vous la présenter."

Récupération : `livrer` (document), revérifier par un compte de sections ou de mots avant présentation. Ne jamais présenter un fichier tronqué comme terminé.

## D11. URL mortes dans les sources

Symptôme : `verify-sources.py --check-links` signale une URL qui ne résout plus au moment de la vérification.

Message : "L'URL [url] ne répond plus (code [statut] ou délai dépassé). Je cherche une source de remplacement équivalente, ou je retire l'affirmation qui ne s'appuie que sur elle."

Récupération : `scripts/verify-sources.py --check-links`, puis `hierarchie-preuve.md` pour requalifier ou remplacer la source. Ne jamais laisser une URL morte dans la bibliographie finale sans statut déclaré.

## D12. Utilisateur qui veut sauter le contrôle

Symptôme : l'utilisateur demande explicitement de passer outre un blocage (seuil de scorecard, vérification de sources, revue) pour aller plus vite.

Message : "Passer outre laisse [ce que le contrôle protégeait] non vérifié. Je peux le faire, mais ce passage sera journalisé et, à la troisième fois, exigera une justification substantielle."

Récupération : `tools/check.py --outrepasser`, échelle de friction à 3 crans (voir `check.py` et `piloter.md`, section friction des outrepassements). Le passage outre reste tracé dans le journal de projet ou dans `.outrepassements.json`, jamais silencieux.
