# Save each Q&A entry, as served by the data room's Q&A module, to evidence/Q-xx.txt
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
for e in d["entries"]:
    if e["id"] not in sys.argv[2:]:
        continue
    with open(f"/tmp/akw-runs/final-claude/evidence/{e['id']}.txt", "w", encoding="utf-8") as f:
        f.write("https://akw-data-room.maxfabian31.workers.dev/qa.html (entry data: https://akw-data-room.maxfabian31.workers.dev/data/qa.json)\n")
        f.write(f"Retrieved 2026-11-07 via agent-browser session.\n\n{e['id']} [{e['topic']}] status: {e['status']}; asked {e['asked']}; answered {e['answered']}\n")
        f.write(f"Question: {e['question']}\nAnswer: {e['answer']}\nReferenced documents: {', '.join(e['refs'])}\n")
