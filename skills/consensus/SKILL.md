---
name: consensus
description: >
  Soumet un document à une revue par consensus de plusieurs agents (contrôle qualité, contradicteur, vérificateur de faits) qui votent le verdict, et calibre les normes selon un profil de discipline. À utiliser quand l'utilisateur demande "revue par consensus", "double validation", "fais voter les agents", "vérification croisée", "calibre pour ma discipline", "norme des sciences dures", "profil de discipline" ou veut réduire les angles morts d'une passe unique.
metadata:
  version: "0.1.0"
---

# Revue par consensus et profils de discipline

Réduire les angles morts d'une révision en passe unique : faire évaluer le document par plusieurs agents indépendants, agréger leurs verdicts, et caler les normes sur la discipline visée.

## 1. Calibrer le profil de discipline

Charger `references/profils-discipline.md`. Le profil fixe la norme de citation, la structure attendue et la pondération des sources pour le champ visé (sciences dures, sciences humaines, droit, gestion, médecine). Si un fichier `profil.json` existe dans le dossier de travail, l'utiliser. Sinon, demander la discipline une fois, puis appliquer son profil.

## 2. Lancer la revue à trois voix

Déléguer en parallèle, via l'outil Task, à trois agents indépendants.

- `controle-qualite` : conformité au style maison, rigueur, structure. Pré-passe déterministe comprise.
- `contradicteur` : contre-thèse la plus forte, points de rupture.
- `verificateur-faits` : vérification des affirmations factuelles contre les sources.

Chaque agent rend un verdict : Prêt, À réviser, ou À refondre.

## 3. Ancrer sur le scorecard déterministe

Calculer la note objective du document.

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/scorecard.py FICHIER
```

Le scorecard sert d'ancre commune et de départage. Un document que les agents jugent prêt mais que le scorecard place sous 70 n'est pas prêt.

## 4. Agréger le verdict

Règle de consensus sur trois voix.

- Prêt seulement si au moins deux agents disent Prêt, qu'aucun ne signale de point critique non résolu, et que le scorecard atteint le seuil du profil (souvent 85).
- À refondre si au moins deux agents disent À refondre, ou si le scorecard tombe sous 70.
- À réviser sinon.

Surfacer les désaccords entre agents, ils signalent les zones à trancher. Un consensus mou qui efface un signal critique est un échec.

## Format de sortie

```
Profil de discipline : [champ] (norme [APA/Vancouver/...], structure [...])

Votes :
- controle-qualite : [verdict] - [motif clé]
- contradicteur : [verdict] - [faille principale]
- verificateur-faits : [verdict] - [affirmation à étayer]

Scorecard : [note]/100

Verdict de consensus : [Prêt / À réviser / À refondre]
Désaccords à trancher : [...]
Actions prioritaires : [...]
```

## Règles

1. Trois voix indépendantes, jamais une seule passe déguisée en consensus.
2. Le scorecard déterministe départage et ancre les verdicts qualitatifs.
3. Un point critique signalé par un seul agent suffit à retenir le verdict Prêt.
4. Surfacer les désaccords, ne pas les moyenner.
5. Le profil de discipline cale la norme, il ne relâche pas la rigueur.
