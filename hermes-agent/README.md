# Scriptorium pour Hermes Agent

Ce dossier porte Scriptorium sur [Hermes Agent](https://github.com/NousResearch/hermes-agent), en plus du plugin Claude Code natif servi par `scriptorium/` à la racine du repo. Les deux cohabitent sans se gêner : rien ici ne modifie `scriptorium/`.

## Pourquoi un dossier séparé

Scriptorium est un plugin Claude Code natif : sous-agents délégués (`agents/`) et hook `PostToolUse` (`hooks/`) reposent sur des mécanismes propres à Claude Code, sans équivalent portable. Plutôt que de dénaturer le plugin d'origine, ce dossier fournit le portage Hermes à côté :

- **`skills/`** — les 5 sous-agents de `scriptorium/agents/` (`redacteur`, `verificateur-faits`, `contradicteur`, `synthese-sources`, `controle-qualite`), reformulés en compétences [Agent Skills](https://hermes-agent.nousresearch.com/docs/) (SKILL.md + frontmatter). Les 4 compétences originales (`atelier`, `produire`, `controler`, `livrer`) n'ont pas besoin de portage : elles sont copiées telles quelles depuis `scriptorium/skills/`.
- **`hooks/scriptorium-lint-hook.py`** — portage du hook Claude Code `PostToolUse` (`scriptorium/hooks/`) vers un hook Hermes `pre_verify`. Sous Hermes, `post_tool_call` est un simple observateur (retour ignoré) ; `pre_verify` est le vrai équivalent avec pouvoir de blocage (`{"decision": "block", "reason": ...}` fait continuer l'agent au lieu de conclure).

## Installation

```bash
bash update-hermes-skills.sh          # depuis la racine du repo
```

Le script :
1. `git pull` (si l'arbre est propre) ;
2. copie les 9 compétences (4 originales + 5 portées) vers `~/.hermes/skills/scriptorium/` (ou `%LOCALAPPDATA%\hermes\skills\scriptorium\` sous Windows), en substituant `${CLAUDE_PLUGIN_ROOT}` par le chemin absolu du checkout ;
3. copie `hooks/scriptorium-lint-hook.py` vers `~/.hermes/agent-hooks/` ;
4. enregistre le hook `pre_verify` dans `config.yaml` via `hermes config set` (jamais d'édition manuelle) et l'allowliste (`shell-hooks-allowlist.json`) si nécessaire ;
5. vérifie l'état avec `hermes hooks doctor`.

Pour une synchronisation automatique quotidienne, planifier ce script en cron Hermes (`cronjob` MCP tool, `no_agent: true`) pointant sur un wrapper dans `~/.hermes/scripts/`.

> **Note d'exploitation** — si la gateway Hermes tourne en arrière-plan pendant l'exécution du script, elle peut réécrire `config.yaml` depuis sa propre copie en mémoire et effacer l'entrée `hooks.pre_verify` juste après son écriture. Si `hermes hooks doctor` ne voit pas le hook après un run du script, relancer `bash update-hermes-skills.sh --no-pull` une fois la gateway au repos, ou redémarrer la gateway après le run.

## Différences connues avec le plugin Claude Code

| Aspect | Claude Code | Hermes |
|---|---|---|
| Sous-agents délégués | `agents/*.md`, invocation native | 5 skills équivalents, invoqués manuellement ou via `delegate_task` |
| Hook post-écriture | `PostToolUse`, bloque avant fin de tour | `pre_verify`, même effet, déclenché une fois par tour (`changed_paths`) |
| Portée du lint au hook | dernier fichier écrit seulement | tous les `.md`/`.txt` modifiés dans le tour (plus complet) |
| `${CLAUDE_PLUGIN_ROOT}` | résolu par Claude Code au runtime | substitué en dur au moment de la copie par `update-hermes-skills.sh` |

Aucune de ces différences ne dégrade le plugin Claude Code d'origine : `scriptorium/` reste inchangé et continue de fonctionner de façon identique sous Claude Code.
