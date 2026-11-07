# How to work on this task

You are working unattended: nobody will answer questions until you finish. Keep going until `python3 -I check_answers.py` passes, or until you have recorded in `work/decisions.tsv` why it can't.

## Deliverables

- `deliverables/answers.csv`: the table the brief asks for, with exactly this header row: `Request,Item,Answer,Unit,Period,Basis,Source,Location,Note`. Request is the request number. Write Source as `2.4 v1` for a document or `Q-07` for a Q&A entry; separate several sources with `; `. Fill every column except Note; write `n/a` where one doesn't apply.
- `deliverables/files/`: the original files the brief asks for, under the names the data room gives them. Nothing else goes in this folder.

## Tools

- Drive the browser with the `agent-browser` CLI. Read `agent-browser --help` before your first command, and `agent-browser <command> --help` before using a command you haven't used.
- Pass `--session {{session}} --allowed-domains {{domain}}` on every command, so the browser stays inside the data room. Start a fresh headless session; never attach to another browser or profile.
- To download a file, pass `--download-path <absolute path to deliverables/files>` when you open the session, click the document's Download button, and wait for the file to appear. A download you don't direct lands in `work/downloads/`.
- Read PDFs with `pdftotext -layout` and workbooks with Python's `openpyxl` (both installed). Run Python as `python3 -I`.
- Close the browser when you finish: `agent-browser --session {{session}} close`.

## Workflow

1. **Spec first.** Write `work/spec.md`: for each request, the items you will report, each with its period, unit and basis, and where you expect to find it.
2. **One slice end to end.** Do request 1 completely before the others: find the source, save the evidence, record the rows and run the check. Then do the rest one request at a time.
3. **Evidence before answers.** For every source you cite, save what you read under `evidence/`, in a file whose name starts with its index and version (`evidence/2.4-v1.txt`, `evidence/2.4-v1.xlsx`) or its Q&A reference (`evidence/Q-07.txt`), with the URL on the first line of text files.
4. **Keep to the data room's terms.** A document marked view only may be read in the viewer, but not downloaded, printed, saved or exported. For one, your evidence is a note in your own words (`evidence/4.2-v1.md`): the URL, the section and the facts you used, never a copy, screenshot or extract of the page.
5. **Calculate with code.** Copy source figures into `work/figures.json` first. Compute any derived figure, such as a sum, a share or a growth rate, with a script in `work/`, never by hand, and keep the script.
6. **Check after every change.** Run `python3 -I check_answers.py` after each change to `answers.csv`. When it fails, fix the deliverable, not the check.
7. **Verify against the source.** Before you finish, open each cited source in the data room again and confirm the figure, the version and the location. Write what you checked, and how, in `work/verification.md`.
8. **Decision trail.** Log each choice you make without a human in `work/decisions.tsv`, with the columns `time`, `decision`, `reason` and `evidence`: a reading of an unclear request, a source you preferred over another, anything you couldn't find.

A reviewer running a different model will check your deliverables against the data room after you finish, without seeing your notes.
