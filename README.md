# Automating knowledge work: worked examples

This repository holds the material behind the worked example in [Choosing a browser automation toolkit for an agent](https://maximilianfabian.dev/guides/automating-knowledge-work/browser-automation/), a guide on maximilianfabian.dev. The example is "A worked example: a buyer’s request list".

**Everything in it is made up.** Vennacott Holdings Limited, Project Tansy, every person, customer, lender and figure, and the data room itself are fictional. Every page of the data room says so.

The runs took place on 7 November 2026.

## The case in brief

A buyer's advisers sent a list of ten requests about a company for sale. The answers sit in the seller's virtual data room: behind terms of access, in a document index that hides superseded versions, in a document viewer and in a log of questions and answers. Four setups got the same brief once, with no follow-ups:

| Setup | Model and effort | Browser |
|---|---|---|
| Claude in Chrome 1.0.105, in Chrome's side panel | Opus 5.5, High | Its own cloud browser |
| ChatGPT in Work mode | GPT-6 Astra, High | ChatGPT's cloud browser |
| Claude Code 2.1.318 with agent-browser 0.41.0 | claude-opus-5-5, high | Headless Chrome on the author's machine |
| Codex CLI 0.166.0 with agent-browser 0.41.0 | gpt-6-astra, high | Headless Chrome on the author's machine |

It's a worked example of first runs, not a ranking. ChatGPT's PDF isn't the file the room served: a manifest is appended to the original bytes. See `browser/tansy/runs/chatgpt-work/RUN.md`.

Claude Code and Codex shared one instruction file and one check script. Each ran in a sandbox, and an agent on the other vendor's model reviewed its table. The producer then settled the review.

## Layout

```
browser/tansy/
  brief.md               the brief every setup got, as sent
  data-room/             the data room's built files, as served
  case/                  the case's design, request list, answer key, score key and sources
  generator/             the scripts that build data-room/ from case/ and check it, with the page templates in site/
  toolkit/               the instruction files, the check, the runner, the sandbox and the scorer
  runs/
    claude-in-chrome/    reply, workbook, files, score and RUN.md
    chatgpt-work/        reply, table, files, score and RUN.md
    claude-code/         workspace, review workspace, transcripts and logs
    codex/               the same for Codex
  screenshots/           the five images in the guide
```

### `case/`

- `design.md`: the case's working design, with the review it went through and how each finding was settled.
- `request-list.md`: the buyer's ten requests.
- `answer-key.json`: the answers, their sources and the likely mistakes, written before the runs.
- `score-key.json`: what the scorer checks, with the rubric for the points read by hand and the sha256 of every served file.
- `index.json`, `qa.json`, `model.json`, `series.json`, `docs/`, `workbooks/`: the sources `build.py` turns into the data room.
- `reconciliations.json`, `evidence-revisions.json`, `name-checks.json`: inputs to `check.py`. `name-checks.json` records the searches that confirmed no real company uses the case's names.

### `toolkit/`

- `toolkit/AGENTS.md` and `toolkit/CLAUDE.md`: the instructions the producing agent got. `CLAUDE.md` only points Claude Code at `AGENTS.md`. In each run, `{{session}}` and `{{domain}}` were filled with the run's browser session and the data room's domain.
- `toolkit/check_answers.py`: the check the agents ran after every change. It knows nothing about the right answers.
- `review/AGENTS.md` and `review/CLAUDE.md`: the reviewer's instructions.
- `run.sh`: runs the producer, the review on the other harness and the producer settling the review, each stage inside `sandbox.sh`, and commits each stage in the run's workspace.
- `sandbox.sh`, `test_sandbox.sh`, `sandbox-tests.md`: the bubblewrap sandbox, its tests and their results.
- `score.py` and `test_score.py`: the scorer and its tests.
- `case.json`: the case as `run.sh` reads it.
- `freeze.tsv`: the sha256 of each file when the case was frozen, before the runs.
- `served-manifest.tsv`: the sha256 of each file the hosted data room served.

### `runs/claude-code/` and `runs/codex/`

- `workspace/`: the producer's workspace after the run.
  - `deliverables/answers.csv`: the settled table, after the review.
  - `deliverables/answers.producer.csv`: the producer's table before the review, taken from the workspace's "Producer's deliverables" commit (Claude Code 58d8936, Codex 70fe431). Claude Code's is identical to its settled table. In Codex's settled table, request 5 cites one more source with an explanation, and two customers in request 6 swap places so they run in order of revenue. No answer changed.
  - `deliverables/files/`: the files delivered for request 10.
  - `evidence/`: what the agent saved for each source it cited. For the view-only document 4.2, it's a note in the agent's own words.
  - `work/`: the spec (`work/spec.md`), the scripts, the figures, the decision log (`work/decisions.tsv`), the verification note and the agent's other working files, including any downloads.
  - `review/`: the reviewer's findings, as copied in for the producer to settle.
  - `task.json`: the room's address and the request numbers, which `check_answers.py` reads.
- `review-workspace/review/`: the reviewer's own workspace output, including the files it downloaded.
- `adjudication.json`: the nine points read by hand against the rubric.
- `logs/`:
  - `producer.jsonl`, `review.jsonl`, `resolve.jsonl`: the three stages' transcripts, as each harness printed them. Claude Code's are its `--output-format stream-json` output; Codex's are its `exec --json` output. The reviewer always runs on the other harness, so `claude-code/logs/review.jsonl` is a Codex transcript and `codex/logs/review.jsonl` a Claude Code one.
  - `*.last.txt`: Codex's last message for a stage.
  - `stages.tsv`: when each stage ended, on which harness, and its exit status.
  - `versions.tsv`: the tool versions and the sha256 of the run's inputs.
  - `check-producer.txt`, `check-resolved.txt`: the output of `check_answers.py` after the producer and after the settlement.

Each workspace was a Git repository. This repository holds the files, not that history.

## Serve the data room locally

The data room is static files. Any static web server can serve `browser/tansy/data-room/`. With Python 3:

```sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory browser/tansy/data-room
```

Then open http://127.0.0.1:8000/ and accept the terms. Acceptance is kept in the browser's session storage.

`_headers` is the Cloudflare format for extra response headers. It adds only `X-Robots-Tag: noindex, nofollow` to every response, to keep the hosted room out of search results. A local server doesn't need it. Python's server ignores it and serves it as a plain file.

The hosted room also differed from a plain static server in two ways. It answered at addresses without `.html`, such as `/doc?id=2.2-v1`, and it served `404.html` for unknown paths. The site's own links all use `.html`, so it works without either. The transcripts show both forms of address.

To check that the files are the bytes the hosted room served, from the repository's root:

```sh
cd browser/tansy/data-room
tail -n +2 ../toolkit/served-manifest.tsv | awk -F'\t' '{print $1"  "$2}' | sha256sum -c --quiet && echo "all files match"
```

All 61 files in the manifest match. `_headers` isn't in the manifest, because Cloudflare reads it and doesn't serve it.

## Rerun the scorer

`score.py` needs only Python 3. Run it from the repository's root, because `case/score-key.json` gives the data room's path relative to it:

```sh
key=browser/tansy/case/score-key.json
score=browser/tansy/toolkit/score.py
run=browser/tansy/runs/codex
python3 -I $score $key $run/workspace/deliverables/answers.csv \
  --files $run/workspace/deliverables/files --workspace $run/workspace --adjudication $run/adjudication.json
```

For Claude Code, set `run=browser/tansy/runs/claude-code`. For a chat app, pass its `answers.csv`, its `files/` and its `adjudication.json`, and leave out `--workspace`:

```sh
run=browser/tansy/runs/chatgpt-work
python3 -I $score $key $run/answers.csv --files $run/files --adjudication $run/adjudication.json
```

Without `--adjudication`, the nine points read by hand show as pending. To score `answers.producer.csv`, pass it in place of `answers.csv`. The scorer's own tests run with `python3 -I browser/tansy/toolkit/test_score.py browser/tansy/case/score-key.json`.

Run from this layout, the scorer gives 33 of 33 for Claude Code, Codex and Claude in Chrome, and 32 of 33 for ChatGPT, with the producers' and the settled tables alike. For Claude Code it also notes that another row matched for request 6's combined share holds 16,930, the four customers' combined revenue. That doesn't change the score.

## Rebuild and check the data room

The generator expects the layout it was written in: `cases/<case>/`, `dist/<case>/` and `site/` next to the scripts. To use it, copy the folders into that layout in a new working folder with a short path:

```sh
work=/tmp/tansy-build
mkdir -p $work/cases $work/dist
cp -R browser/tansy/generator/. $work/
cp -R browser/tansy/case $work/cases/pub-tansy
cp -R browser/tansy/data-room $work/dist/pub-tansy
cd $work
python3 -I check.py --case pub-tansy        # checks the served files against the case
python3 -I test_generator.py
python3 -I build.py --case pub-tansy        # rebuilds dist/pub-tansy/, replacing the copy
python3 -I check.py --case pub-tansy
```

It needs Python 3 with `openpyxl` and `pypdf`, and `build.py` needs Google Chrome at `/usr/bin/google-chrome` to print the PDFs. Keep the working folder's path short: Chrome refuses to start when the path of its temporary socket is too long.

`check.py` runs 755 checks. Expect 754 to pass and one to fail, reported as `[check_site] crashed: FileNotFoundError` for `wrangler.pub-tansy.jsonc`. That file is the Cloudflare deployment configuration, which this repository leaves out. Only the four checks on it, at the end of the site section, don't run.

A rebuild reproduces every HTML, JSON, JavaScript and CSS file byte for byte. The PDFs and workbooks come out with the same content but different bytes, because Chrome and openpyxl write the time of the build into them. So `data-room/` holds the served bytes, and a rebuild doesn't replace it.

`generator/README.md` is the generator's own README. It also describes a development case, Project Larkspur, which isn't in this repository.

## Rerun the case

The brief and `toolkit/case.json` give the hosted room's address, which may no longer answer. To run against a local copy, serve the room as above and change the address in `brief.md` and the `room` and `domain` in `case.json`.

`run.sh` takes `case.json`, the producer (`claude` or `codex`) and a run ID, and writes the results next to `case.json`. It needs Bash, bubblewrap, Claude Code, the Codex CLI, agent-browser, Google Chrome, `pdftotext`, Python 3 with `openpyxl`, OpenSSL and Git, with both harnesses signed in.

`sandbox.sh` is written for the author's machine, a Linux system under WSL. It expects Node, Python and the harnesses at the author's install paths, a Codex login copy under `~/.local/share/akw/`, and WSL's `/mnt/wsl/resolv.conf`. Adjust those paths before you use it. `test_sandbox.sh` takes a file holding a canary string of the form `akwcanary-` and 16 hexadecimal digits. Plant the same string in your private case files, so the test can show that the sandbox can't read them.

## Changes from the files as run

The files are as recorded, except for the removal of private details from the author's machine:

- In the transcripts and logs, the home directory is replaced by `<home>` and the user name by `<user>`. In the Claude Code transcripts, the start-up record's list of plugins and its memory path, the rate-limit records and the login's expiry time are replaced by `<redacted>`. Every line is still valid JSON, and nothing else in a transcript is changed or shortened.
- `toolkit/sandbox.sh` takes the home directory and user name from `$HOME` and `$USER` instead of naming them.
- `toolkit/sandbox-tests.md` doesn't name two unrelated programs that were listening on the machine's ports.
- `generator/README.md` leaves out a note on the author's local Python install.
- `case/score-key.json` gives the data room's path relative to this repository's root.

Because of the last two changes to code, the sha256 of `toolkit/sandbox.sh` and `case/score-key.json` no longer match `freeze.tsv`. Every other file listed in `freeze.tsv` matches.

## Not included

- The internal review of the case's design and the record of its validation run. `case/design.md` lists the review's findings and how each was settled.
- The canary file used for the sandbox tests. Its value is at the end of `case/design.md`.
- The Cloudflare deployment configuration.
- The chat runs' working notes and progress screenshots, which show the author's accounts and browser.
- The copies of `brief.md`, `CLAUDE.md` and `check_answers.py` in each workspace, which are identical to the files in `toolkit/`, and the workspace copies of `AGENTS.md`, which differ only in the filled session name and domain.
- The harnesses' standard error output, which is empty or holds only the line "Reading additional input from stdin...".

## Licence

The code is under the MIT licence in `LICENSE`: every `.py`, `.sh`, `.js` and `.css` file, and the page templates in `browser/tansy/generator/site/`. Everything else, including the text, data, documents, transcripts and images, is under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/) (CC BY 4.0). Third-party material quoted in the transcripts, such as a tool's help text, keeps its own licence.
