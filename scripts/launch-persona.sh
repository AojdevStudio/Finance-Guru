#!/usr/bin/env bash
# Usage: launch-persona.sh <directory just was run from> <command> [args...]
# Resolves FIN_GURU_DATA_ROOT relative to the caller's directory, then runs the
# command inside that instance so every relative write lands there.
invocation_dir="$1"
shift

root="$(cd "$invocation_dir" && cd "${FIN_GURU_DATA_ROOT:-/nonexistent}" 2>/dev/null && pwd)"
if [ ! -f "$root/user-profile.yaml" ]; then
  echo "Export FIN_GURU_DATA_ROOT=<your instance directory> first. It must hold user-profile.yaml." >&2
  exit 1
fi

cd "$root" || exit 1
export FIN_GURU_DATA_ROOT="$root"
exec "$@"
