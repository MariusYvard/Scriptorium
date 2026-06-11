# Checklist de release

Procédure versionnée pour publier une nouvelle version de Scriptorium. Respecter l'ordre.

## 1. Préparer

- Décider du saut de version (sémantique) : correctif (0.2.x), mineur (0.x.0), majeur (x.0.0).
- Lister les changements depuis la dernière version.

## 2. Aligner les versions

Le numéro de version vit à deux endroits, qui doivent rester synchronisés.

- `.claude-plugin/plugin.json`, champ `version`.
- `.claude-plugin/marketplace.json`, champ `metadata.version` et le `version` de l'entrée plugin.

## 3. Contrôler la qualité

```
python3 evals/run-evals.py
```

Tous les cas doivent passer. Lancer ensuite l'auto-contrôle de style sur les fichiers d'instruction (hors fixtures et fichiers qui citent le lexique banni) :

```
python3 scripts/lint-style.py <fichier>
```

## 4. Valider le manifeste

```
claude plugin validate .claude-plugin/plugin.json
```

Corriger toute erreur ou tout avertissement.

## 5. Packager

```
cd <dossier-du-plugin>
zip -r /tmp/scriptorium.plugin . -x "*.DS_Store" -x "*/__pycache__/*"
```

Vérifier le contenu de l'archive : `.claude-plugin/plugin.json`, `README.md`, `skills/`, `agents/`, `scripts/`, `hooks/`, `evals/` présents.

## 6. Publier

- Copier le `.plugin` vers le dossier de sortie ou le dépôt.
- Taguer la version dans le gestionnaire de versions (`v0.2.0`).
- Mettre à jour le journal des changements.

## 7. Après publication

- Vérifier l'installation depuis l'artefact publié.
- Tester un déclenchement de chaque nouvelle compétence.

## Journal des versions

- 0.6.0 : consolidation de dix-neuf compétences en quatre à sous-commandes (`atelier` : piloter, cadrer, projet ; `produire` : genre, sourcer, revue-litterature, figure, tableau, equation, style, charte ; `controler` : revue, contredire, consensus, humaniser, audit, relecteurs ; `livrer` : document, decliner), sortie HTML autonome pilotée par la charte graphique (`theme.py --format css`), profil de discipline analyse géopolitique, plugin ouvert au chercheur, à l'ingénieur et à l'analyste géopolitique, evals portés à 33 cas.
- 0.5.0 : mémoire de projet (`project.py`), conformité au plan (`plan-check.py`), détecteur d'empreinte IA (`ai-fingerprint.py`), cohérence interne (`coherence.py`), génération et audit de tableaux (`tables.py`), audit de document existant (`audit-doc.py`), intégration continue éditoriale (`tools/check.py`, action GitHub, modèle), compétences `memoire-projet`, `auditer-existant`, `tableaux`, `revue-litterature`, `humaniser`, scorecard étendu (empreinte IA et cohérence), evals portés à 32 cas.
- 0.4.0 : scorecard déterministe 0-100 (`scripts/scorecard.py`), traçabilité (`traceability.py`), terminologie et glossaire (`terminology.py`), intégrité numérique (`numbers.py`), moteur de citations BibTeX (`citations.py`), diff de versions (`diff-versions.py`), compétences `equations`, `repondre-relecteurs`, `decliner`, `consensus`, agent `verificateur-faits`, evals portés à 25 cas.
- 0.3.0 : charte graphique appliquée au texte et aux figures (`scripts/theme.py` avec contrôle de contraste WCAG, `figures.py --theme`, compétence `charte-graphique`, exemple `assets/charte-graphique.exemple.json`), evals portés à 17 cas.
- 0.2.0 : scripts déterministes (style, sources, lisibilité, figures), hook d'application, compétences `finaliser`, `schematiser`, `contredire`, agent `contradicteur`, harnais d'évaluation, maturité de distribution.
- 0.1.0 : six compétences (atelier, cadrer, sourcer, rediger, reviser, style-maison), trois agents, playbooks de genre, boîtes à outils stratégie et prospective, style maison à directives strictes.
