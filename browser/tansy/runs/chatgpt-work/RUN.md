# ChatGPT in Work mode on Project Tansy, run 1

| | |
|---|---|
| Product | ChatGPT on the web (chatgpt.com) in Google Chrome, a new regular chat in Work mode. The web app shows no version number, so none is recorded. |
| Model and effort | GPT-6 Astra, High (3 of 6 on the effort slider; the default is Medium) |
| Sent | 7 November 2026 at 16:31:47 CET (UTC+1) |
| Finished | At about 16:37. ChatGPT reported "Worked for 5m 43s". |
| Brief | `brief.md`, pasted whole into the composer once and sent, with no follow-ups. The composer's text matched the file after whitespace was normalised (4,118 characters each). Nothing else was typed into the chat during the run. |

## How it was set up

- Work mode isn't offered in temporary chats, so the run used a regular chat, which uses the account's memory and custom instructions.
- For the run, every connected plugin was set to Always ask. ChatGPT asked for none, and no approval request came up. The settings were restored afterwards.
- The brief was pasted and sent by an agent driving the browser with agent-browser. It sent nothing else.
- After the results were saved, the chat and the two files the run uploaded to the ChatGPT library were deleted.

## Where it ran

In ChatGPT's own cloud browser, with one tab on the data room, and its own sandbox, where it ran about 43 commands. It asked no questions.

## What it returned

- A reply with the answer table, its arithmetic in the Note column, and the two files request 10 asks for, attached to the chat.
- It withheld document 4.2, which is view only, and said why.

### The PDF carries an appended C2PA manifest

The delivered `files/2.2-v1-audited-consolidated-financial-statements-fy2026.pdf` is 94,350 bytes. Its first 69,321 bytes are the data room's file unchanged: they hash to `9d641a07…`, the same sha256 as the original. After them comes an incremental PDF update that embeds a C2PA "Content Credentials" manifest. The manifest records the action `c2pa.created`, with digital source type `trainedAlgorithmicMedia`, software agent `gpt-6-astra`, and the time 2026-11-07T15:37:09Z. So the content is the original, but the file isn't, and it labels an unaltered vendor document as created by a model. To check it:

```sh
head -c 69321 files/2.2-v1-audited-consolidated-financial-statements-fy2026.pdf | sha256sum
```

The XLSX is byte-identical to the served file (`628de0ed…`).

## Files here

| File | What it is |
|---|---|
| `reply.txt` | The chat page's text after the run, with the brief at the top |
| `reply-table.csv` | The reply's table as shown |
| `answers.csv` | The same table, the copy the scorer reads (byte-identical to `reply-table.csv`) |
| `files/` | The two files from request 10, as downloaded from the chat's file viewer |
| `adjudication.json` | The nine points read by hand against the rubric in `case/score-key.json` |
| `score.txt` | The scorer's output: 32 of 33 checks. The one miss is the PDF above, which isn't the original bytes. |
