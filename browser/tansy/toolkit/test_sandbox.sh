#!/usr/bin/env bash
# Tests sandbox.sh before a round of runs, and exits non-zero if any test fails.
# Usage: test_sandbox.sh <canary file>
# The canary file holds a string that is also planted in the private case files (answer key, design). The tests:
# the canary is found in a positive-control file inside the sandbox's workspace and nowhere else the sandbox can read;
# no case name is visible; only the sandbox's own processes are visible; Windows programs don't start; /run is absent;
# and every TCP port listening on this machine is listed with what it answers, for the record.
set -uo pipefail

canary=$(cat "${1:?usage: test_sandbox.sh <canary file>}")
[[ $canary =~ ^akwcanary-[0-9a-f]{16}$ ]] || { echo "the canary file doesn't hold a canary" >&2; exit 2; }
here=$(cd "$(dirname "$0")" && pwd)
probe=/tmp/akw-runs/sandbox-test-$(openssl rand -hex 3)
mkdir -p "$probe"
trap 'rm -rf "$probe"' EXIT
# The canary is split in the scripts, so only control.txt holds it whole.
printf '%s\n' "$canary" >"$probe/control.txt"
cp /mnt/c/Windows/System32/whoami.exe "$probe/whoami.exe" 2>/dev/null || true
head=${canary:0:13}
tail=${canary:13}
cat >"$probe/inside.sh" <<EOF
canary="$head""$tail"
dirs="/usr /etc /opt /home /tmp /var /mnt"
echo "canary-files: \$(rg -uuu -l --no-messages -F "\$canary" \$dirs | sort | tr '\n' ' ')"
echo "grep-files: \$(grep -rlF --binary-files=text -s "\$canary" \$dirs | sort | tr '\n' ' ')"
echo "case-names: \$(rg -uuu -l --no-messages -e Vennacott -e Quillmoor -e 'Project Tansy' -e 'Project Larkspur' -e Kilcarrow -e Ardnacree \$dirs | grep -v '^$probe/' | sort | tr '\n' ' ')"
echo "processes: \$(ls /proc | grep -c '^[0-9]')"
echo "run-exists: \$([[ -e /run ]] && echo yes || echo no)"
echo "interop: \$(if [[ -f ./whoami.exe ]] && ./whoami.exe >/dev/null 2>&1; then echo works; else echo blocked; fi)"
echo "home: \$(ls -A ~ | tr '\n' ' ')"
for port in $(ss -ltnH | awk '{print $4}' | grep -E '^(127\.0\.0\.1|0\.0\.0\.0|\*):' | sed 's/.*://' | sort -un | tr '\n' ' '); do
  echo "port \$port: \$(timeout 5 curl -s -m 4 -o /dev/null -w '%{http_code}' http://127.0.0.1:\$port/ 2>/dev/null || echo closed)"
done
EOF
result=$("$here/sandbox.sh" --harness claude --rw "$probe" -- bash ./inside.sh 2>&1)
echo "$result"

fail=0
check() { if eval "$2"; then echo "PASS $1"; else echo "FAIL $1"; fail=1; fi; }
line() { grep "^$1:" <<<"$result" | head -1 | cut -d: -f2- | xargs; }
check "the positive control is found" '[[ $(line canary-files) == "$probe/control.txt" ]]'
check "grep agrees" '[[ $(line grep-files) == "$probe/control.txt" ]]'
check "no case name is visible outside the workspace" '[[ -z $(line case-names) ]]'
check "only the sandbox's processes are visible" '(( $(line processes) < 10 ))'
check "/run is absent" '[[ $(line run-exists) == no ]]'
check "Windows programs don't start" '[[ $(line interop) == blocked ]]'
exit $fail
