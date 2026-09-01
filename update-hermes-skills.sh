#!/usr/bin/env bash
# Installe/actualise Scriptorium pour Hermes Agent : compétences + hook.
#
# Scriptorium est un plugin Claude Code natif (agents/, hooks/ propriétaires
# sans équivalent portable). Le portage Hermes vit à côté, dans
# hermes-agent/, sans jamais toucher scriptorium/ (le plugin Claude Code
# original reste inchangé et continue de fonctionner à l'identique).
#
# Ce script :
#  1. copie les 4 compétences originales (scriptorium/skills/) + les 5
#     compétences portées depuis les sous-agents (hermes-agent/skills/) vers
#     ~/.hermes/skills/scriptorium/, en substituant ${CLAUDE_PLUGIN_ROOT} par
#     le chemin absolu du checkout ;
#  2. copie hermes-agent/hooks/scriptorium-lint-hook.py vers
#     ~/.hermes/agent-hooks/, portage du hook PostToolUse Claude Code
#     (scriptorium/hooks/) vers un hook Hermes pre_verify ;
#  3. enregistre le hook dans config.yaml via `hermes config set` et
#     l'allowliste si besoin (jamais d'édition manuelle du config).
#
# Usage: bash update-hermes-skills.sh [--no-pull] [--no-hook]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT_ABS="${SCRIPT_DIR}/scriptorium"
HERMES_PORT_DIR="${SCRIPT_DIR}/hermes-agent"
LOCALAPPDATA_DIR="${LOCALAPPDATA:-$HOME/AppData/Local}"
HERMES_HOME="$(cygpath -u "${LOCALAPPDATA_DIR}/hermes" 2>/dev/null || echo "${LOCALAPPDATA_DIR}/hermes")"
DEST_BASE="${HERMES_HOME}/skills/scriptorium"
HOOK_DEST_DIR="${HERMES_HOME}/agent-hooks"
HOOK_DEST="${HOOK_DEST_DIR}/scriptorium-lint-hook.py"
HOOK_SRC="${HERMES_PORT_DIR}/hooks/scriptorium-lint-hook.py"

log()  { echo "[scriptorium-sync] $*"; }
err()  { echo "[scriptorium-sync][ERROR] $*" >&2; }

DO_PULL=1
DO_HOOK=1
for arg in "$@"; do
  [ "$arg" = "--no-pull" ] && DO_PULL=0
  [ "$arg" = "--no-hook" ] && DO_HOOK=0
done

cd "$SCRIPT_DIR"

if [ "$DO_PULL" = "1" ] && [ -d .git ]; then
  if [ -z "$(git status --porcelain)" ]; then
    log "git pull..."
    git pull --ff-only || err "git pull a échoué, poursuite avec l'état local."
  else
    log "Arbre de travail non propre : git pull sauté."
  fi
fi

if [ ! -d "${PLUGIN_ROOT_ABS}/skills" ]; then
  err "scriptorium/skills introuvable. Checkout invalide ?"
  exit 1
fi

mkdir -p "$DEST_BASE"
CHANGED=0

sync_skill_dir() {
  # $1 = dossier compétence source (ex: scriptorium/skills/atelier)
  local skill_dir="$1"
  local name dest tmp
  name="$(basename "$skill_dir")"
  dest="$DEST_BASE/$name"
  tmp="$(mktemp -d)"
  cp -r "$skill_dir" "$tmp/$name"
  find "$tmp/$name" -type f \( -name '*.md' -o -name '*.py' \) -print0 \
    | while IFS= read -r -d '' f; do
        sed -i "s|\${CLAUDE_PLUGIN_ROOT}|${PLUGIN_ROOT_ABS}|g" "$f"
      done

  if [ -d "$dest" ] && diff -rq "$dest" "$tmp/$name" --exclude=.scriptorium-installed >/dev/null 2>&1; then
    log "$name : inchangé"
    rm -rf "$tmp"
    return
  fi

  rm -rf "$dest"
  mv "$tmp/$name" "$dest"
  date -u +%Y-%m-%dT%H:%M:%SZ > "$dest/.scriptorium-installed"
  rmdir "$tmp" 2>/dev/null || true
  CHANGED=1
  log "$name : mis à jour -> $dest"
}

for skill_dir in "${PLUGIN_ROOT_ABS}"/skills/*/; do
  sync_skill_dir "$skill_dir"
done
if [ -d "${HERMES_PORT_DIR}/skills" ]; then
  for skill_dir in "${HERMES_PORT_DIR}"/skills/*/; do
    sync_skill_dir "$skill_dir"
  done
fi

if [ "$DO_HOOK" = "1" ] && [ -f "$HOOK_SRC" ]; then
  mkdir -p "$HOOK_DEST_DIR"
  if ! diff -q "$HOOK_SRC" "$HOOK_DEST" >/dev/null 2>&1; then
    cp "$HOOK_SRC" "$HOOK_DEST"
    CHANGED=1
    log "hook : mis à jour -> $HOOK_DEST"
  else
    log "hook : inchangé"
  fi

  # Chemin du checkout pour la resolution SCRIPTORIUM_ROOT au runtime du
  # hook (pas de re-invocation de hermes config si déjà enregistré).
  if command -v hermes >/dev/null 2>&1; then
    HOOKS_DUMP="$(hermes config get hooks 2>/dev/null || true)"
    CURRENT_HOOK_CMD="$(printf '%s' "$HOOKS_DUMP" | grep -c "scriptorium-lint-hook" || true)"
    if [ "${CURRENT_HOOK_CMD:-0}" = "0" ]; then
      HOOK_DEST_WIN="$(cygpath -w "$HOOK_DEST" 2>/dev/null || echo "$HOOK_DEST")"
      HOOK_JSON="$(python3 -c "import json,sys; print(json.dumps([{'command': 'python3 ' + json.dumps(sys.argv[1]), 'timeout': 20}]))" "$HOOK_DEST_WIN")"
      hermes config set 'hooks.pre_verify' "$HOOK_JSON" \
        && log "hook enregistré dans config.yaml (hooks.pre_verify)" \
        || err "échec de l'enregistrement du hook dans config.yaml."
    else
      log "hook déjà enregistré dans config.yaml."
    fi
  else
    err "commande hermes introuvable, hook non enregistré dans config.yaml (le fichier est copié, à enregistrer manuellement)."
  fi
fi

if [ "$CHANGED" = "1" ]; then
  log "Scriptorium (compétences + hook) mis à jour dans Hermes."
else
  log "Rien à mettre à jour."
fi
