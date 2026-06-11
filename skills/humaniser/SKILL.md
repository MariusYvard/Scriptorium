---
name: humaniser
description: >
  Détecte et corrige l'empreinte d'un texte généré : rythme uniforme, ouvertures de phrases répétitives, cadence ternaire systématique, connecteurs suremployés, bigrammes répétés, amplification contrastive. À utiliser quand l'utilisateur demande "humanise ce texte", "ça sonne IA", "enlève les tics d'écriture", "rends ce texte moins artificiel", "détecte l'empreinte IA" ou veut un texte qui ne trahit pas sa génération.
metadata:
  version: "0.1.0"
---

# Humaniser (empreinte IA)

Effacer les marqueurs statistiques d'un texte généré, sans toucher au fond. Les tics ciblés recoupent les directives strictes du style maison.

## 1. Mesurer

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ai-fingerprint.py FICHIER
```

Le script chiffre la variabilité de longueur de phrase, le taux d'ouvertures identiques, la densité de connecteurs, la cadence ternaire, les bigrammes répétés et les amplifications contrastives. Il signale les tics marqués.

## 2. Corriger tic par tic

- Rythme uniforme : varier la longueur des phrases, intercaler des phrases courtes et affirmatives entre les longues.
- Ouvertures répétitives : diversifier le premier mot des phrases, ne pas enchaîner les « De plus », « En effet », « Par ailleurs ».
- Cadence ternaire : briser la règle de trois, varier un, deux ou quatre éléments, comme l'exige le style maison.
- Connecteurs suremployés : couper les liaisons mécaniques, garder celles qui portent une vraie relation logique.
- Bigrammes répétés : remplacer les répétitions par des reprises variées ou des reformulations.
- Amplification contrastive : supprimer les tournures « non seulement ... mais », « il ne s'agit pas seulement de ... mais ».

## 3. Re-mesurer

Relancer le script jusqu'à ce que les signaux marqués disparaissent. Vérifier ensuite que le sens et les faits sont intacts, et que le style maison tient (`lint-style.py`).

## Format de sortie

Le texte corrigé, plus un avant-après des métriques d'empreinte (écart-type de longueur, ouvertures, connecteurs) qui montre la correction.

## Règles

1. Corriger la forme, jamais le fond ni les faits.
2. Re-mesurer jusqu'à disparition des signaux marqués.
3. Ne pas remplacer un tic par un autre (varier réellement, pas mécaniquement).
4. Le résultat respecte le style maison.
