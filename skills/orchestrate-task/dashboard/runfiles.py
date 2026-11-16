"""Read an orchestrate-task run folder into one JSON-ready state.

Read-only except for the two things the dashboard owns: ANSWERS.md and chats/.
Formats: references/status-and-register.md. Every parser tolerates missing files and
missing columns, because a run folder is written by an agent, not a schema.
"""
import os
import re
import time
from datetime import datetime

TEXT_LIMIT = 512 * 1024
IMAGE_EXT = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
             ".gif": "image/gif", ".webp": "image/webp"}

STATE_WORDS = {
    "not-started": "Not started",
    "plan-review": "Goal plan under review",
    "red": "Writing failing tests",
    "green": "Tests pass, checking the change",
    "mutation-ok": "Mutation check passed",
    "review": "Review running",
    "waiting-gate": "Waiting on your approval",
    "paused": "Paused",
    "done": "Goal done",
}


# ---------- small helpers ----------

def read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def mtime(path):
    try:
        return os.path.getmtime(path)
    except OSError:
        return 0


def clean(cell):
    """Strip markdown decoration from a table cell."""
    cell = cell.strip()
    cell = re.sub(r"`([^`]*)`", r"\1", cell)
    cell = re.sub(r"\*\*([^*]*)\*\*", r"\1", cell)
    return "" if cell in ("—", "-", "–") else cell


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    parts = re.split(r"(?<!\\)\|", line)
    return [clean(p.replace("\\|", "|")) for p in parts]


def tables(md):
    """All pipe tables in a markdown text: [{heading, cols, rows:[dict]}]."""
    out, heading, lines = [], "", md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#"):
            heading = line.lstrip("#").strip()
        if (line.strip().startswith("|") and i + 1 < len(lines)
                and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1])):
            cols = [c.lower() for c in split_row(line)]
            rows = []
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = split_row(lines[i])
                rows.append({cols[k]: (cells[k] if k < len(cells) else "")
                             for k in range(len(cols))})
                i += 1
            out.append({"heading": heading, "cols": cols, "rows": rows})
            continue
        i += 1
    return out


def find_table(md, *must):
    for t in tables(md):
        if all(any(c.startswith(m) for c in t["cols"]) for m in must):
            return t
    return None


def col(row, prefix):
    for k, v in row.items():
        if k.startswith(prefix):
            return v
    return ""


def kv_lines(md):
    """`key: value` lines; repeated keys become lists."""
    out = {}
    for line in md.splitlines():
        m = re.match(r"^([a-z][a-z0-9 _-]*):\s?(.*)$", line.strip())
        if m:
            out.setdefault(m.group(1).strip(), []).append(m.group(2).strip())
    return out


def first(d, key, default=""):
    v = d.get(key)
    return v[0] if v else default


def mid(goal_id):
    m = re.match(r"(M\d+[a-z]?)", goal_id or "")
    return m.group(1) if m else ""


def num(mid_):
    m = re.match(r"M(\d+)([a-z]?)", mid_)
    return (int(m.group(1)), m.group(2)) if m else (999, "")


# ---------- individual files ----------

def parse_register(md):
    title = ""
    m = re.search(r"^#\s+(.+?)\s+register\s*$", md, re.M)
    if m:
        title = m.group(1).strip()
    header = {}
    for key in ("heartbeat", "open blockers", "progress", "run folder"):
        mm = re.search(r"^" + key + r":\s*(.+)$", md, re.M)
        header[key] = mm.group(1).strip() if mm else ""
    platform = re.search(r"platform:\s*([\w-]+)", header["run folder"])
    beat = re.match(r"(\d+)\s*([smh])", header["heartbeat"])
    last = re.search(r"last tick\s+([0-9:T-]+)", header["heartbeat"])
    t = find_table(md, "m", "session")
    rows = t["rows"] if t else []
    ledger = find_table(md, "goal", "title", "state")
    answers_log = ""
    am = re.search(r"^##\s+Answers log\s*$(.*?)(?=^##\s|\Z)", md, re.M | re.S)
    if am:
        answers_log = am.group(1)
    merges = ""
    mm = re.search(r"^##\s+Merges.*?$(.*?)(?=^##\s|\Z)", md, re.M | re.S)
    if mm:
        merges = mm.group(1)
    status_paths = dict(re.findall(r"^status path (M\d+[a-z]?):\s*(.+)$", md, re.M))
    secs = 300
    if beat:
        secs = int(beat.group(1)) * {"s": 1, "m": 60, "h": 3600}[beat.group(2)]
    return {
        "title": title,
        "platform": platform.group(1) if platform else "",
        "heartbeat_s": secs,
        "last_tick": last.group(1) if last else "",
        "rows": rows,
        "ledger": ledger["rows"] if ledger else [],
        "answers_log": answers_log,
        "merges": merges,
        "status_paths": status_paths,
    }


def parse_status(md):
    kv = kv_lines(md)
    head = re.search(r"^#\s+(M\d+[a-z]?)\s+(.+)$", md, re.M)
    blocked = None
    bm = re.search(r"^BLOCKED (M\S+)\s*$(.*?)(?=^\S+:\s*$|^resolved:|\Z)", md, re.M | re.S)
    if bm:
        bkv = kv_lines(bm.group(2))
        blocked = {"id": bm.group(1), "need": first(bkv, "need"),
                   "diagnosis": first(bkv, "diagnosis"), "class": first(bkv, "class")}
    evidence = re.findall(r"^-\s*g\d+:\s*(.+)$", md, re.M)
    goals_m = re.search(r"^goals[^:]*:\s*(.+)$", md, re.M)
    return {
        "id": head.group(1) if head else "",
        "name": head.group(2).strip() if head else "",
        "updated": first(kv, "updated"),
        "goal": first(kv, "goal"),
        "goals": goals_m.group(1).strip() if goals_m else "",
        "state": first(kv, "state"),
        "lease": first(kv, "lease"),
        "next": first(kv, "next"),
        "blocked": blocked,
        "evidence": [e.strip() for e in evidence],
    }


def parse_card(md, card_id):
    kv = kv_lines(md)
    options = []
    for o in kv.get("option", []):
        p = [x.strip() for x in o.split("|")]
        p += [""] * (4 - len(p))
        options.append({"k": p[0], "title": p[1], "good": p[2], "cost": p[3]})
    facts = []
    for f in kv.get("fact", []):
        k, _, v = f.partition("|")
        v = v.strip()
        verified = None
        if v.lower().startswith("verified"):
            verified = True
        elif v.lower().startswith(("claimed", "hypothesis", "the child's claim")):
            verified = False
        facts.append({"k": k.strip(), "v": v, "verified": verified})
    return {
        "id": card_id,
        "kind": first(kv, "kind"),
        "milestone": first(kv, "milestone"),
        "opened": first(kv, "opened"),
        "headline": first(kv, "headline"),
        "body": first(kv, "body"),
        "facts": facts,
        "proof": kv.get("proof", []),
        "now": first(kv, "now"),
        "after": first(kv, "after"),
        "undo": first(kv, "undo"),
        "options": options,
        "recommend": first(kv, "recommend"),
        "why": first(kv, "why"),
        "reply": first(kv, "reply"),
        "evidence": kv.get("evidence", []),
    }


def parse_answers(md):
    """ANSWERS.md entries: [{id, n, time, card, command, choice, note, chat}]."""
    out = []
    for m in re.finditer(r"^##\s+(ANS-(\d+))\s+·\s+(\S+)\s+·\s+(.+?)\s*$(.*?)(?=^##\s|\Z)",
                         md, re.M | re.S):
        body = m.group(5)
        kv = kv_lines(body)
        note = "\n".join(l[2:] if l.startswith("> ") else l[1:]
                         for l in body.splitlines() if l.startswith(">"))
        target = m.group(4)
        out.append({
            "id": m.group(1), "n": int(m.group(2)), "time": m.group(3),
            "card": target[5:].strip() if target.startswith("card ") else "",
            "command": first(kv, "command"),
            "choice": first(kv, "choice"),
            "note": note,
            "chat": first(kv, "chat"),
        })
    return out


# ---------- state ----------

def goal_cell(state, blocked):
    s = state.lower()
    if s == "done":
        return "d"
    if s.startswith("active"):
        if blocked:
            return "b"
        if "waiting-gate" in s:
            return "w"
        return "n"
    if s == "unconfirmed":
        return "n"
    return "t"


def build_state(run):
    run = os.path.abspath(run)
    reg_md = read(os.path.join(run, "REGISTER.md"))
    reg = parse_register(reg_md)
    plan_md = read(os.path.join(run, "PLAN.md"))
    plan_t = find_table(plan_md, "id", "name")
    plan_names = {r.get("id", ""): r.get("name", "") for r in (plan_t["rows"] if plan_t else [])}

    # answers the dashboard sent, and which of those the orchestrator has read
    answers = parse_answers(read(os.path.join(run, "ANSWERS.md")))
    read_ids = set(re.findall(r"\bANS-\d+\b", reg["answers_log"]))
    pending = [a for a in answers if a["id"] not in read_ids]
    pending_cards = {a["card"] for a in pending if a["card"]}

    # blockers + questions → cards
    cards = []
    bt = find_table(read(os.path.join(run, "BLOCKERS.md")), "id", "milestone")
    open_blockers = []
    for r in (bt["rows"] if bt else []):
        if col(r, "closed"):
            continue
        bid = r.get("id", "")
        open_blockers.append(bid)
        cards.append({"id": bid, "kind": "blocker", "queue": "blocker",
                      "milestone": col(r, "milestone"), "opened": col(r, "opened"),
                      "headline": col(r, "what happened"), "class": col(r, "class")})
    qt = find_table(read(os.path.join(run, "QUESTIONS.md")), "#", "status")
    for r in (qt["rows"] if qt else []):
        st = r.get("status", "").lower()
        if st not in ("open", "queued"):
            continue
        qid = "Q" + r.get("#", "").lstrip("Qq")
        cards.append({"id": qid, "kind": "question", "queue": st,
                      "milestone": col(r, "unblocks"), "unblocks": col(r, "unblocks"),
                      "opened": col(r, "asked"), "headline": col(r, "question"),
                      "recommend": col(r, "recommend"), "source": col(r, "source")})
    for c in cards:
        cf = os.path.join(run, "cards", c["id"] + ".md")
        if os.path.isfile(cf):
            full = parse_card(read(cf), c["id"])
            for k, v in full.items():
                if v:
                    c[k] = v
            c["has_card_file"] = True
        c.setdefault("options", [])
        c.setdefault("facts", [])
        c.setdefault("proof", [])
        c.setdefault("evidence", [])
        c["sent"] = c["id"] in pending_cards
    # order: blockers oldest first, then the OPEN question, then the queue in file order
    blockers = [c for c in cards if c["queue"] == "blocker"]
    opened = [c for c in cards if c["queue"] == "open"]
    queued = [c for c in cards if c["queue"] == "queued"]
    cards = blockers + opened + queued

    # milestones
    ledger = reg["ledger"]
    ms = []
    for r in reg["rows"]:
        m = r.get("m", "")
        if not m:
            continue
        sp = reg["status_paths"].get(m) or os.path.join(run, "milestones", m, "STATUS.md")
        st = parse_status(read(sp)) if os.path.isfile(sp) else parse_status("")
        name = st["name"] or plan_names.get(m, "")
        ticket = ""
        tm = re.match(r"(#\d+)\s+(.*)", name)
        if tm:
            ticket, name = tm.group(1), tm.group(2)
        mstate = col(r, "milestone").lower() or "active"
        blocker = col(r, "blocker")
        has_col = any(k.startswith("blocker") for k in r)
        # REGISTER is orchestrator-confirmed; a child's STATUS can lag behind an UNBLOCK.
        blocked = bool(blocker) if has_col else (bool(st["blocked"]) and mstate == "active")
        goals = []
        for g in ledger:
            gid = g.get("goal", "")
            if mid(gid) != m or g.get("state", "").lower() == "dropped":
                continue
            gb = blocked and g.get("state", "").lower().startswith("active")
            goals.append({"id": gid, "title": g.get("title", ""), "s": goal_cell(g.get("state", ""), gb),
                          "state": g.get("state", ""), "review": g.get("review", ""),
                          "gate": g.get("gate", ""), "done": g.get("done", "")})
        if not goals and st["goals"]:
            for part in st["goals"].split("·"):
                p = part.strip()
                gid = p.split()[0] if p else ""
                if not gid:
                    continue
                s = "d" if "✓" in p else ("b" if blocked else "n") if "▸" in p else "t"
                goals.append({"id": gid, "title": "", "s": s, "state": "", "review": "", "gate": "", "done": ""})
        for g in goals:
            k = g["id"].split(".")[-1]
            g["evidence"] = [e for e in st["evidence"] if (f"/{k}/" in e or f"{k}-" in e)
                             and resolve(run, e) and os.path.exists(resolve(run, e))]
            ed = os.path.join("milestones", m, "evidence", k)
            if os.path.isdir(os.path.join(run, ed)) and ed + "/" not in g["evidence"]:
                g["evidence"].append(ed + "/")
        cur_id = (st["goal"].split() or [""])[0]
        my_cards = [c for c in cards if mid(c.get("milestone", "")) == m
                    or m in re.split(r"[\s,]+", c.get("unblocks", ""))]
        if mstate in ("merged", "closed"):
            sig, line = "d", "Done and merged" if mstate == "merged" else "Closed"
        elif blocked:
            sig, line = "b", "Blocked, waiting on you" if any(c["queue"] == "blocker" for c in my_cards) else "Blocked"
        elif mstate == "on-hold":
            sig, line = "w", "On hold by your choice"
        elif mstate == "merge-ready":
            sig, line = "w", "Merge waiting on you"
        elif st["state"] == "paused":
            sig, line = "p", "Paused"
        elif st["state"] == "waiting-gate" or any(
                c["queue"] in ("open", "queued") and cur_id and cur_id in re.split(r"[\s,]+", c.get("unblocks", ""))
                for c in my_cards):
            sig, line = "w", "Waiting on you"
        elif mstate == "goals-complete":
            sig, line = "n", "Goals done, checking merge readiness"
        else:
            sig, line = "n", STATE_WORDS.get(st["state"], st["state"].capitalize() or "Working")
        merge = None
        if goals:
            merge = {"merged": "d", "closed": "d", "merge-ready": "w", "on-hold": "w"}.get(mstate, "t")
        cur = st["goal"]
        cur_short = re.sub(r"^M\d+[a-z]?\.(g\d+)\s*", r"\1: ", cur) if cur else ""
        now = cur_short
        if mstate == "merged":
            mt = re.search(r"(\d\d:\d\d)\s+" + re.escape(m) + r"\s+merged", reg["merges"])
            now = f"Merged at {mt.group(1)}" if mt else "Merged"
        elif goals and all(g["s"] == "d" for g in goals):
            now = f"All {len(goals)} goals done"
        asks = [c["id"] for c in my_cards]
        ms.append({
            "id": m, "asks": asks, "ticket": ticket, "name": name,
            "label": f"{m} · {ticket} {name}".replace("  ", " ").strip(),
            "session": r.get("session (child id)", "") or col(r, "session"),
            "st": sig, "stateLine": line, "now": now, "milestone_state": mstate,
            "updated": st["updated"], "lease": st["lease"] or col(r, "lease") or "none",
            "next": st["next"], "blocked": st["blocked"], "goals": goals, "merge": merge,
            "status_file": os.path.relpath(sp, run) if sp.startswith(run) else sp,
        })
    labels = {x["id"]: x["label"] for x in ms}
    for c in cards:
        lab = c.get("milestone", "")
        if " · " not in lab:
            parts = [p for p in re.split(r"[\s,]+", lab) if p]
            named = []
            for p in parts:
                mm = mid(p)
                if mm in labels:
                    goal = p[len(mm) + 1:] if p.startswith(mm + ".") else ""
                    named.append(labels[mm] + (f" · {goal}" if goal else ""))
            c["milestone"] = " + ".join(named) if named else lab
    order = {"b": 0, "w": 1, "n": 2, "p": 3, "d": 4}
    ms.sort(key=lambda x: (order.get(x["st"], 5), num(x["id"])))

    # feed (newest first)
    ft = find_table(read(os.path.join(run, "FEED.md")), "time", "event")
    feed = []
    for r in (ft["rows"] if ft else []):
        g = col(r, "m.goal") or col(r, "m")
        feed.append({"time": r.get("time", ""), "m": mid(g), "goal": g,
                     "lane": col(r, "lane").lower(), "text": col(r, "event"),
                     "link": col(r, "link")})
    feed.reverse()

    total = sum(len(m["goals"]) for m in ms)
    done = sum(1 for m in ms for g in m["goals"] if g["s"] == "d")
    cells = [g["s"] for m in sorted(ms, key=lambda x: num(x["id"])) for g in m["goals"]]
    shipped = sum(1 for m in ms if m["milestone_state"] == "merged")

    files = [os.path.join(run, f) for f in ("REGISTER.md", "QUESTIONS.md", "BLOCKERS.md",
                                             "FEED.md", "ANSWERS.md")]
    updated = max([mtime(f) for f in files] + [0])
    reg_m = mtime(os.path.join(run, "REGISTER.md"))
    stale_after = 3 * reg["heartbeat_s"]
    stale = bool(reg_m) and (time.time() - reg_m) > stale_after

    return {
        "run": {
            "title": reg["title"] or os.path.basename(run),
            "folder": run,
            "platform": reg["platform"],
            "heartbeat_s": reg["heartbeat_s"],
            "last_tick": reg["last_tick"],
            "register_changed": int(reg_m),
            "updated": int(updated),
            "stale": stale,
            "found": bool(reg_md),
        },
        "progress": {"done": done, "total": total, "cells": cells},
        "counts": {"blockers": len(open_blockers), "for_you": len([c for c in cards if not c["sent"]]),
                   "shipped": shipped, "milestones": len(ms)},
        "cards": cards,
        "sent": [{"id": a["id"], "card": a["card"], "command": a["command"],
                  "choice": a["choice"], "time": a["time"]} for a in pending],
        "milestones": ms,
        "feed": feed,
    }


def signature(run):
    """Cheap change detector for polling."""
    parts = []
    for root, dirs, fs in os.walk(run):
        dirs[:] = [d for d in dirs if d not in ("logs", "pids", ".git") and not d.startswith(".")]
        depth = root[len(run):].count(os.sep)
        if depth > 3:
            dirs[:] = []
        for f in fs:
            if f.endswith(".md"):
                p = os.path.join(root, f)
                parts.append(f"{p}:{mtime(p)}")
    return str(hash("|".join(sorted(parts))))


# ---------- the dashboard's own writes ----------

def next_answer_id(run):
    ans = parse_answers(read(os.path.join(run, "ANSWERS.md")))
    return "ANS-%d" % (max([a["n"] for a in ans] + [0]) + 1)


ANSWERS_HEAD = (
    "# Answers from the dashboard\n"
    "Written only by the dashboard (append-only). The orchestrator reads entries newer than\n"
    "the last `ANS-<n>` in REGISTER.md's Answers log on every tick; see pull-loop.md.\n"
)


def one_line(s, limit=500):
    return re.sub(r"\s+", " ", s or "").strip()[:limit]


def append_answer(run, card=None, choice="", note="", chat="", command=""):
    path = os.path.join(run, "ANSWERS.md")
    aid = next_answer_id(run)
    stamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    target = f"card {card}" if card else "command"
    lines = [f"\n## {aid} · {stamp} · {target}"]
    if command:
        lines.append(f"command: {one_line(command, 100)}")
    if choice:
        lines.append(f"choice: {one_line(choice, 100)}")
    for l in (note or "").strip().splitlines()[:40]:
        lines.append("> " + l[:500])
    if chat:
        lines.append(f"chat: {chat}")
    new = not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as f:
        if new:
            f.write(ANSWERS_HEAD)
        f.write("\n".join(lines) + "\n")
    return aid, stamp


def safe_key(key):
    k = re.sub(r"[^A-Za-z0-9_-]+", "-", key or "").strip("-")[:80]
    return k or "chat"


def chat_path(run, key):
    return os.path.join(run, "chats", safe_key(key) + ".md")


def read_thread(run, key):
    md = read(chat_path(run, key))
    out = []
    for m in re.finditer(r"^\*\*(You|Helper)\s*\(([^)]*)\):\*\*\s?(.*?)(?=^\*\*(?:You|Helper)\s*\(|\Z)",
                         md, re.M | re.S):
        text = m.group(3).strip()
        src = ""
        sm = re.search(r"^Sources:\s*(.+)$", text, re.M)
        if sm:
            src = sm.group(1).strip()
            text = text[:sm.start()].strip()
        out.append({"who": "me" if m.group(1) == "You" else "ai", "time": m.group(2),
                    "text": text, "src": src})
    return out


def append_thread(run, key, context, who, text, src=""):
    path = chat_path(run, key)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new = not os.path.exists(path)
    stamp = datetime.now().strftime("%H:%M")
    with open(path, "a", encoding="utf-8") as f:
        if new:
            f.write(f"# Side chat · {safe_key(key)}\ncontext: {one_line(context, 300)}\n\n")
        label = "You" if who == "me" else "Helper"
        body = text.strip()
        if src:
            body += f"\nSources: {one_line(src, 300)}"
        f.write(f"**{label} ({stamp}):** {body}\n\n")
    return os.path.relpath(path, run)


def resolve(run, rel):
    """A path inside the run folder, or None."""
    if not rel or "\x00" in rel:
        return None
    full = os.path.realpath(os.path.join(run, rel))
    root = os.path.realpath(run)
    if full != root and not full.startswith(root + os.sep):
        return None
    return full
