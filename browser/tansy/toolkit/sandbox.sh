#!/usr/bin/env bash
# Runs one command inside a bubblewrap sandbox for an unattended agent stage.
#
# The sandbox sees: system directories read-only, the harness and tool installs read-only, the harness's own
# credentials, a fresh home and /tmp, and the directories passed with --rw. Nothing else from the home directory is
# mounted, so case sources, answer keys, scorers, transcripts, histories, memories and earlier outputs are absent.
# It has its own process namespace and /proc, no /mnt and no /run, so WSL interop can't start Windows programs.
# It shares the network, because the agent needs the data room and its model API.
#
# Usage: sandbox.sh --harness claude|codex [--rw DIR]... [--env NAME=VALUE]... -- COMMAND [ARG]...
# The command runs with the first --rw directory as its working directory.
set -euo pipefail

home=$HOME
harness=
rw=()
envs=()
while [[ $# -gt 0 ]]; do
  case $1 in
    --harness) harness=$2; shift 2 ;;
    --rw) rw+=("$(realpath -e "$2")"); shift 2 ;;
    --env) envs+=("$2"); shift 2 ;;
    --) shift; break ;;
    *) echo "sandbox.sh: unknown argument $1" >&2; exit 2 ;;
  esac
done
[[ $harness == claude || $harness == codex ]] || { echo "sandbox.sh: --harness claude|codex" >&2; exit 2; }
[[ ${#rw[@]} -gt 0 && $# -gt 0 ]] || { echo "sandbox.sh: need --rw DIR and a command" >&2; exit 2; }
for dir in "${rw[@]}"; do
  case $dir in
    /tmp/akw-runs/*) ;;
    *) echo "sandbox.sh: writable directories must be under /tmp/akw-runs, not $dir" >&2; exit 2 ;;
  esac
done

node_bin=$home/.local/share/mise/installs/node/26.13.0/bin
claude_bin=$(readlink -f "$home/.local/bin/claude")
codex_bin=$(readlink -f "$(command -v codex)")
browser_bin=$(readlink -f "$(command -v agent-browser)")
python_dir=$home/.local/share/agent-python
rg_dir=$(dirname "$(readlink -f "$(command -v rg)")")
for path in "$node_bin/node" "$claude_bin" "$codex_bin" "$browser_bin" "$python_dir/bin/python3" /opt/google/chrome/chrome; do
  [[ -x $path ]] || { echo "sandbox.sh: missing $path" >&2; exit 1; }
done

private=$(mktemp -d /tmp/akw-sandbox.XXXXXX)
trap 'rm -rf "$private"' EXIT
printf '{}\n' >"$private/empty.json"
: >"$private/empty"
mkdir -p "$private/agent-browser"
cp "$home/.agent-browser/config.json" "$private/agent-browser/config.json"

args=(
  --die-with-parent --new-session --unshare-pid --unshare-ipc --unshare-uts --unshare-cgroup-try
  --ro-bind /usr /usr --symlink usr/bin /bin --symlink usr/sbin /sbin --symlink usr/lib /lib --symlink usr/lib64 /lib64
  --ro-bind /etc /etc --ro-bind /mnt/wsl/resolv.conf /mnt/wsl/resolv.conf --ro-bind /opt/google /opt/google
  --ro-bind /sys /sys --proc /proc --dev /dev --tmpfs /tmp --tmpfs /var/tmp
  --tmpfs "$home"
  --ro-bind "$home/.local/share/mise" "$home/.local/share/mise"
  --ro-bind "$home/.local/share/uv/python" "$home/.local/share/uv/python"
  --ro-bind "$python_dir" "$python_dir"
  --ro-bind "$(dirname "$claude_bin")" "$(dirname "$claude_bin")"
  --dir "$home/.agent-browser" --ro-bind "$private/agent-browser/config.json" "$home/.agent-browser/config.json"
  --dir "$home/bin"
  --symlink "$claude_bin" "$home/bin/claude" --symlink "$codex_bin" "$home/bin/codex"
  --symlink "$browser_bin" "$home/bin/agent-browser"
)

case $harness in
  claude)
    # The real ~/.claude, so token refreshes reach the shared credentials file exactly as in a normal session,
    # with every other entry in it replaced by an empty directory or file.
    args+=(--bind "$home/.claude" "$home/.claude")
    for entry in "$home/.claude"/* "$home/.claude"/.[!.]*; do
      [[ -e $entry || -L $entry ]] || continue
      [[ $(basename "$entry") == .credentials.json ]] && continue
      if [[ -L $entry ]]; then
        # A symlink can't be covered; it stays dangling, because nothing it points to outside ~/.claude is mounted.
        case $(realpath -m "$entry") in "$home"/.claude/*) echo "sandbox.sh: $entry points inside ~/.claude" >&2; exit 1 ;; esac
        continue
      elif [[ -d $entry ]]; then
        args+=(--tmpfs "$entry")
      elif [[ $entry == *.json ]]; then
        args+=(--ro-bind "$private/empty.json" "$entry")
      else
        args+=(--ro-bind "$private/empty" "$entry")
      fi
    done
    ;;
  codex)
    # A fresh Codex home holding only the login and the config, so no sessions or memories carry over between runs.
    # A refreshed login is copied back afterwards.
    akw=$home/.local/share/akw/codex-home
    mkdir -p "$private/codex-home"
    cp "$akw/auth.json" "$private/codex-home/auth.json"
    printf 'model = "gpt-6-astra"\n' >"$private/codex-home/config.toml"
    args+=(--bind "$private/codex-home" "$home/.codex")
    envs+=("CODEX_HOME=$home/.codex")
    ;;
esac

for dir in "${rw[@]}"; do
  args+=(--bind "$dir" "$dir")
done

args+=(--clearenv --chdir "${rw[0]}"
  --setenv HOME "$home" --setenv USER "$USER" --setenv LOGNAME "$USER" --setenv LANG C.UTF-8 --setenv TERM dumb
  --setenv TMPDIR /tmp --setenv PATH "$home/bin:$python_dir/bin:$node_bin:$rg_dir:/usr/bin:/bin")
for pair in "${envs[@]}"; do
  args+=(--setenv "${pair%%=*}" "${pair#*=}")
done

status=0
bwrap "${args[@]}" -- "$@" || status=$?

if [[ $harness == codex ]] && ! cmp -s "$private/codex-home/auth.json" "$akw/auth.json"; then
  # Keep the newer login if Codex refreshed it during the run.
  python3 -I - "$private/codex-home/auth.json" "$akw/auth.json" <<'EOF' || true
import json, shutil, sys
new, old = sys.argv[1], sys.argv[2]
if json.load(open(new)).get("last_refresh", "") > json.load(open(old)).get("last_refresh", ""):
    shutil.copyfile(new, old)
    print("sandbox.sh: kept Codex's refreshed login", file=sys.stderr)
EOF
fi
exit $status
