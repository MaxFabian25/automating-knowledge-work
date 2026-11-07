# Sandbox tests

Working record, 2026-11-07. Rerun `test_sandbox.sh <canary file>` before each round; it exits non-zero on any failure.

## What sandbox.sh does

Every agent stage (producer, review, resolve, and the case validation) runs its whole harness process inside bubblewrap 0.9.0 with an allowlisted filesystem: /usr, /etc, /opt/google, /sys and the resolver file read-only; the harness, Node, Python and tool installs read-only; a fresh tmpfs home and /tmp; the stage's workspace read-write. Claude Code sees the real ~/.claude with every entry except .credentials.json replaced by an empty directory or file, so token refreshes behave as in any other session. Codex gets a fresh home holding only a copy of the runs' login and a one-line config; a refreshed login is copied back. New process, IPC and UTS namespaces, a new /proc, no /run and no /mnt apart from the resolver file. The network is shared.

## Results on 2026-11-07

| Test | Result |
|---|---|
| Canary planted in the Tansy answer key, design and canary file: found by rg and grep across /usr /etc /opt /home /tmp /var /mnt inside the sandbox | Only the positive-control file in the workspace |
| Case names (Vennacott, Quillmoor, Project Tansy, Project Larkspur, Kilcarrow, Ardnacree) | None. A bare "Larkspur" matches a hard-disk model in /usr/share/misc/pci.ids |
| Processes visible | 4 to 5, all the sandbox's own; PID 1 is bwrap |
| WSL interop | A copied whoami.exe fails ("UtilGetPpid: failed to parse /proc/1/stat"); powershell.exe isn't on the PATH; /run is absent |
| Home | Only .agent-browser (config), .claude (masked), .local (installs), bin |
| Claude Code 2.1.318 inside | Works; its own tools run in the same namespace (this version has no separate Grep or Glob tool); agent-browser opens the data room |
| Codex 0.166.0 inside | Works with the copied login; its home starts empty of sessions and memories; agent-browser opens the data room |
| Earlier probe: rg with `--glob '!/proc/**'` from / | Never finished, because rg globs are relative and it walked /proc and /sys. The positive control showed the first probe's empty result was a missing rg, not a clean search; both are fixed in test_sandbox.sh |

## Network: what a sandboxed agent can reach on this machine

| Port | What answers | Exposure |
|---|---|---|
| 3773 | <redacted: a local app server> | Serves its app shell to any path; refuses WebSocket connections without a token (tested from Node: closed 1006). No thread data over plain HTTP on the paths tried. |
| 8765 | <redacted: a local file server for an unrelated task> | Unrelated files of that task, nothing from this series |
| 52078 | cloudflared's metrics endpoint | Tunnel metrics |
| 2222 | SSH | Needs keys, which aren't in the sandbox |
| Others in the 51000 to 54000 range | agent-browser daemons and their browsers, including those of other sandboxed runs at the same time | One run could reach another concurrent run's browser. So the final runs go one at a time, and the listening ports are recorded just before each |

The agents can also read the Claude Code login inside the sandbox, which any run needs. The guide claims only what this table and the results above show.
