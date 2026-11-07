#!/usr/bin/env bash
# Runs one toolkit-side worked example of the browser guide: the producer, an independent review on the other
# harness, then the producer settling the review. Every agent stage runs inside sandbox.sh, and each stage is
# committed in the run's workspace.
# Usage: run.sh <case.json> claude|codex <run-id>
# case.json gives the room's address and domain, a short codename for browser sessions, the request numbers and the
# brief's file name, relative to the case file. Results go to results/<run-id>/ next to case.json.
set -euo pipefail

kit=$(cd "$(dirname "$0")" && pwd)
case_file=$(realpath -e "${1:-}")
producer=${2:-}
id=${3:-}
case $producer in
  claude) reviewer=codex ;;
  codex) reviewer=claude ;;
  *) echo "usage: run.sh <case.json> claude|codex <run-id>" >&2; exit 2 ;;
esac
[[ $id =~ ^[a-z0-9-]+$ ]] || { echo "the run id must be lower-case letters, digits and hyphens" >&2; exit 2; }
case_dir=$(dirname "$case_file")
read_case() { python3 -I -c 'import json, sys; print(json.load(open(sys.argv[1]))[sys.argv[2]])' "$case_file" "$1"; }
room=$(read_case room); domain=$(read_case domain); codename=$(read_case codename)
brief=$case_dir/$(read_case brief)
[[ -n $room && -n $domain && $codename =~ ^[a-z]+$ && -f $brief ]] || { echo "case.json is incomplete" >&2; exit 2; }

root=/tmp/akw-runs
work=$root/$id
check=$root/$id-review
logs=$root/$id-logs
out=$case_dir/results/$id
for path in "$work" "$check" "$logs" "$out"; do
  [[ ! -e $path ]] || { echo "$path already exists" >&2; exit 1; }
done
suffix=$(openssl rand -hex 3)
[[ -n $suffix ]]
session=$codename-$id-$suffix
review_session=$codename-$id-review-$suffix
limit=45m

mkdir -p "$work" "$check/review" "$logs"
python3 -I - "$case_file" "$work/task.json" <<'EOF'
import json, sys
case = json.load(open(sys.argv[1]))
json.dump({"room": case["room"], "requests": case["requests"]}, open(sys.argv[2], "w"), indent=1)
EOF
cp "$kit/toolkit/check_answers.py" "$work/"
# The check has to reach the data room, or every run fails it for a reason the agent can't fix.
(cd "$work" && python3 -I -c 'import sys; sys.path.insert(0, "."); import check_answers as c; c.fetch("/data/index.json"); c.fetch("/data/qa.json")') \
  || { echo "check_answers.py can't read the data room" >&2; exit 1; }

fill() {  # template session output
  sed "s/{{session}}/$2/g; s/{{domain}}/$domain/g" "$1" >"$3"
  if grep -q '{{' "$3"; then echo "unfilled placeholder in $3" >&2; exit 1; fi
}

run_agent() {  # harness directory log-name prompt
  local harness=$1 dir=$2 name=$3 prompt=$4 status=0
  # A download the agent doesn't direct lands in its own workspace, never in the user's Downloads folder.
  local downloads=$dir/work/downloads
  if [[ $name == review ]]; then downloads=$dir/review/downloads; fi
  local stage_out=$root/$id-out-$name
  mkdir -p "$downloads" "$stage_out"
  local sandbox=("$kit/sandbox.sh" --harness "$harness" --rw "$dir" --rw "$stage_out"
    --env "AGENT_BROWSER_DOWNLOAD_PATH=$downloads")
  case $harness in
    claude)
      timeout "$limit" "${sandbox[@]}" -- claude -p \
        --model claude-opus-5-5 --effort high --permission-mode bypassPermissions --setting-sources project \
        --strict-mcp-config --disable-slash-commands --no-session-persistence --output-format stream-json --verbose \
        "$prompt" </dev/null >"$logs/$name.jsonl" 2>"$logs/$name.stderr" || status=$? ;;
    codex)
      timeout "$limit" "${sandbox[@]}" -- codex exec -m gpt-6-astra \
        -c model_reasoning_effort=high --dangerously-bypass-approvals-and-sandbox --json \
        -o "$stage_out/last.txt" "$prompt" </dev/null >"$logs/$name.jsonl" 2>"$logs/$name.stderr" || status=$?
      if [[ -f $stage_out/last.txt ]]; then cp "$stage_out/last.txt" "$logs/$name.last.txt"; fi ;;
  esac
  rm -rf "$stage_out"
  printf '%s\t%s\t%s\t%s\n' "$(date -Is)" "$name" "$harness" "$status" >>"$logs/stages.tsv"
}

commit() {  # directory message
  git -C "$1" add -A
  git -C "$1" commit -q --allow-empty -m "$2"
}

new_repo() {  # directory
  git -C "$1" init -q
  git -C "$1" config user.name 'akw runner'
  git -C "$1" config user.email 'runner@example.invalid'
}

{
  printf 'date\t%s\ncase\t%s\nproducer\t%s\nreviewer\t%s\nsession\t%s\nlimit\t%s\n' \
    "$(date -Is)" "$case_file" "$producer" "$reviewer" "$session" "$limit"
  printf 'claude\t%s\tclaude-opus-5-5\teffort high\n' "$(claude --version)"
  printf 'codex\t%s\tgpt-6-astra\teffort high\n' "$(codex --version)"
  printf 'agent-browser\t%s\n' "$(agent-browser --version)"
  printf 'chrome\t%s\n' "$(google-chrome --version)"
  printf 'bwrap\t%s\n' "$(bwrap --version)"
  printf 'pdftotext\t%s\n' "$(pdftotext -v 2>&1 | head -1)"
  printf 'python\t%s\n' "$(python3 -I --version)"
  printf 'openpyxl\t%s\n' "$(python3 -I -c 'import openpyxl; print(openpyxl.__version__)')"
  for file in "$kit/run.sh" "$kit/sandbox.sh" "$kit/toolkit/AGENTS.md" "$kit/toolkit/CLAUDE.md" \
    "$kit/toolkit/check_answers.py" "$kit/review/AGENTS.md" "$kit/review/CLAUDE.md" "$case_file" "$brief"; do
    printf 'sha256\t%s\t%s\n' "$(sha256sum "$file" | cut -d' ' -f1)" "$file"
  done
} >"$logs/versions.tsv"

# The producer's workspace: the brief, the operating instructions, the task metadata and the check, nothing else.
cp "$brief" "$work/brief.md"
fill "$kit/toolkit/AGENTS.md" "$session" "$work/AGENTS.md"
cp "$kit/toolkit/CLAUDE.md" "$work/CLAUDE.md"
new_repo "$work"
commit "$work" "Start with the brief, the instructions and the check"

run_agent "$producer" "$work" producer "$(cat "$brief")"
(cd "$work" && python3 -I check_answers.py) >"$logs/check-producer.txt" 2>&1 || true
commit "$work" "Producer's deliverables"

# The reviewer's workspace: the brief and the deliverables, not the producer's notes or evidence.
cp "$brief" "$check/brief.md"
fill "$kit/review/AGENTS.md" "$review_session" "$check/AGENTS.md"
cp "$kit/review/CLAUDE.md" "$check/CLAUDE.md"
if [[ -d $work/deliverables ]]; then cp -a "$work/deliverables" "$check/deliverables"; fi
new_repo "$check"
commit "$check" "Start the review"
run_agent "$reviewer" "$check" review \
  "Review another agent's answers to the task in brief.md. Its deliverables are in deliverables/. Follow AGENTS.md."
commit "$check" "Reviewer's findings"

# The producer settles the review in its own workspace.
mkdir -p "$work/review"
for file in findings.csv review.md; do
  if [[ -f $check/review/$file ]]; then cp "$check/review/$file" "$work/review/$file"; fi
done
commit "$work" "Add the independent review"
run_agent "$producer" "$work" resolve "An independent reviewer on a different model has checked your deliverables \
against the data room. Its findings are in review/findings.csv and review/review.md. For each disagreement or gap, \
check the data room again and settle it against the evidence: correct the deliverable where the reviewer is right, \
and where you keep your answer, record why in work/decisions.tsv. Follow AGENTS.md, and finish when \
python3 -I check_answers.py passes."
(cd "$work" && python3 -I check_answers.py) >"$logs/check-resolved.txt" 2>&1 || true
commit "$work" "Settle the review"

mkdir -p "$out"
cp -a "$work" "$out/workspace"
cp -a "$check" "$out/review-workspace"
cp -a "$logs" "$out/logs"
echo "$out"
