#!/usr/bin/env python3
"""Run dashboard for orchestrate-task: one local page for any agent's run folder.

    python3 server.py <run folder> [--port 8790] [--helper "<cmd>"] [--no-helper] [--open]

Reads the run files, shows blockers, approvals, questions and milestones, and writes
the user's answers to <run>/ANSWERS.md for the orchestrator's next tick. The side chat
runs a read-only agent CLI over the run folder. Python standard library only.

Safety: binds 127.0.0.1 only; every /api call needs the session token printed at start;
the Host header must be this machine; files are served only from inside the run folder.
"""
import argparse
import hmac
import json
import mimetypes
import os
import re
import secrets
import shlex
import shutil
import socket
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import runfiles  # noqa: E402

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
HELPER_TIMEOUT = 180
MAX_BODY = 64 * 1024

HELPER_PROMPT = """You are a read-only helper for a person supervising an orchestrated software run.
Your working folder is the run folder. Answer the person's question using only files in it:
REGISTER.md, PLAN.md, BOARD.md, FEED.md, BLOCKERS.md, QUESTIONS.md, cards/, milestones/*/STATUS.md,
milestones/*/evidence/, reviews/, prod/, chats/. Read what you need; never create, change or delete
any file, and never run commands that change anything.

How to answer:
- At most 6 short, whole sentences in plain words. Answer first.
- Name the milestone and goal like `M3 · #155 Feed thumbnails · g4` when you mention one.
- Say what you verified in a file and what is only a claim or a guess.
- If the files don't say, say so; don't invent.
- You can't decide or approve anything. If asked to, say the decision goes through the card.
- Reply in the person's language (they may mix Hindi and English).
- Last line exactly: `Sources: <the files you used, comma-separated>`

What the person is looking at:
{context}

{files}
Conversation so far:
{thread}

The person's question:
{question}
"""


# ---------- helper (side chat) ----------

def run_roles(run):
    t = runfiles.find_table(runfiles.read(os.path.join(run, "RUN.md")), "role", "platform")
    return {r.get("role", ""): r for r in (t["rows"] if t else [])}


def default_helper(run):
    """The review role's CLI from RUN.md, read-only; else claude, else codex, else none."""
    role = run_roles(run).get("review", {})
    platform = (role.get("platform") or "").lower()
    model = role.get("model") or ""
    if model in ("inherit", "—", "-") or " " in model:
        model = ""
    picks = []
    if platform.startswith("codex"):
        picks.append("codex")
    elif platform.startswith("gemini"):
        picks.append("gemini")
    elif platform.startswith("claude"):
        picks.append("claude")
    picks += ["claude", "codex"]
    for cli in picks:
        if not shutil.which(cli):
            continue
        m = model if platform.startswith(cli) else ""
        if cli == "claude":
            cmd = ["claude", "-p", "--allowedTools", "Read,Grep,Glob",
                   "--disallowedTools", "Bash,Edit,Write,NotebookEdit,WebFetch,WebSearch"]
            if m:
                cmd += ["--model", m]
        elif cli == "codex":
            cmd = ["codex", "exec", "-s", "read-only", "--skip-git-repo-check"]
            if m:
                cmd += ["-m", m]
            cmd += ["-"]
        else:
            cmd = ["gemini", "--approval-mode", "plan", "-p", "Read and follow {prompt_file}"]
            if m:
                cmd += ["-m", m]
        label = f"{cli}" + (f" · {m}" if m else " · default model") + (
            " (the run's review role)" if m else "")
        return cmd, label
    return None, "No agent CLI found"


class Helper:
    def __init__(self, cmd, label):
        self.cmd, self.label = cmd, label
        self.locks = {}
        self.guard = threading.Lock()

    def lock(self, key):
        with self.guard:
            return self.locks.setdefault(key, threading.Lock())

    def ask(self, run, prompt):
        if not self.cmd:
            return None, "The side chat has no helper. Start the dashboard with --helper \"<agent cli>\"."
        cmd = list(self.cmd)
        stdin = prompt
        pf = None
        if any("{prompt_file}" in c for c in cmd):
            os.makedirs(os.path.join(run, "chats", ".prompts"), exist_ok=True)
            pf = os.path.join(run, "chats", ".prompts", f"q-{secrets.token_hex(4)}.md")
            with open(pf, "w", encoding="utf-8") as f:
                f.write(prompt)
            cmd = [c.replace("{prompt_file}", pf) for c in cmd]
            stdin = None
        try:
            p = subprocess.run(cmd, input=stdin, cwd=run, capture_output=True, text=True,
                               timeout=HELPER_TIMEOUT)
        except subprocess.TimeoutExpired:
            return None, "The helper took longer than 3 minutes. Try a narrower question."
        except OSError as e:
            return None, f"The helper could not start: {e}"
        finally:
            if pf:
                try:
                    os.remove(pf)
                except OSError:
                    pass
        out = (p.stdout or "").strip()
        if p.returncode != 0 or not out:
            tail = (p.stderr or out or "").strip().splitlines()[-1:] or ["no output"]
            return None, f"The helper failed (exit {p.returncode}): {tail[0][:200]}"
        return out, None


def split_sources(text):
    m = re.search(r"^\s*`?Sources:\s*(.+?)`?\s*$", text, re.M | re.I)
    if not m:
        return text.strip(), ""
    return (text[:m.start()] + text[m.end():]).strip(), m.group(1).strip()


# ---------- HTTP ----------

class App:
    def __init__(self, run, token, helper, port):
        self.run = os.path.abspath(run)
        self.token = token
        self.helper = helper
        self.port = port
        self.write_lock = threading.Lock()


def make_handler(app):
    class H(BaseHTTPRequestHandler):
        server_version = "RunDashboard"
        sys_version = ""

        def log_message(self, fmt, *args):
            if os.environ.get("DASHBOARD_LOG"):
                super().log_message(fmt, *args)

        # -- plumbing --
        def headers_common(self, ctype, length):
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(length))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy",
                             "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                             "font-src https://fonts.gstatic.com; img-src 'self' blob: data:; "
                             "connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")

        def send(self, code, body, ctype="application/json; charset=utf-8"):
            if isinstance(body, (dict, list)):
                body = json.dumps(body).encode()
            elif isinstance(body, str):
                body = body.encode()
            self.send_response(code)
            self.headers_common(ctype, len(body))
            self.end_headers()
            self.wfile.write(body)

        def fail(self, code, msg):
            self.send(code, {"error": msg})

        def host_ok(self):
            host = (self.headers.get("Host") or "").lower()
            return host in (f"127.0.0.1:{app.port}", f"localhost:{app.port}")

        def token_ok(self):
            got = self.headers.get("X-Token") or ""
            return hmac.compare_digest(got.encode(), app.token.encode())

        def r_body(self):
            if "application/json" not in (self.headers.get("Content-Type") or ""):
                return None
            n = int(self.headers.get("Content-Length") or 0)
            if n <= 0 or n > MAX_BODY:
                return None
            try:
                return json.loads(self.rfile.read(n))
            except ValueError:
                return None

        # -- routes --
        def do_GET(self):
            if not self.host_ok():
                return self.fail(403, "Open the dashboard at 127.0.0.1.")
            u = urlparse(self.path)
            if u.path in ("/", "/index.html"):
                return self.r_static("index.html")
            if u.path.startswith("/static/"):
                return self.r_static(u.path[len("/static/"):])
            if not u.path.startswith("/api/"):
                return self.fail(404, "Not found")
            if not self.token_ok():
                return self.fail(401, "Missing or wrong token. Open the link the dashboard printed.")
            q = parse_qs(u.query)
            if u.path == "/api/state":
                sig = runfiles.signature(app.run)
                if q.get("since", [""])[0] == sig:
                    return self.send(200, {"unchanged": True, "sig": sig})
                st = runfiles.build_state(app.run)
                st["sig"] = sig
                st["helper"] = {"available": bool(app.helper.cmd), "label": app.helper.label}
                return self.send(200, st)
            if u.path == "/api/file":
                return self.r_file(q.get("path", [""])[0])
            if u.path == "/api/chat":
                key = runfiles.safe_key(q.get("key", [""])[0])
                return self.send(200, {"key": key, "thread": runfiles.read_thread(app.run, key),
                                       "file": f"chats/{key}.md"})
            return self.fail(404, "Not found")

        def do_POST(self):
            if not self.host_ok():
                return self.fail(403, "Open the dashboard at 127.0.0.1.")
            if not self.token_ok():
                return self.fail(401, "Missing or wrong token. Open the link the dashboard printed.")
            data = self.r_body()
            if not isinstance(data, dict):
                return self.fail(400, "Send JSON.")
            u = urlparse(self.path)
            if u.path == "/api/answer":
                return self.r_answer(data)
            if u.path == "/api/command":
                return self.r_command(data)
            if u.path == "/api/chat":
                return self.r_chat(data)
            return self.fail(404, "Not found")

        def r_static(self, rel):
            full = os.path.realpath(os.path.join(STATIC, rel))
            if not full.startswith(os.path.realpath(STATIC) + os.sep) or not os.path.isfile(full):
                return self.fail(404, "Not found")
            ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
            if ctype.startswith("text/") or ctype.endswith("javascript"):
                ctype += "; charset=utf-8"
            with open(full, "rb") as f:
                self.send(200, f.read(), ctype)

        def r_file(self, rel):
            full = runfiles.resolve(app.run, rel)
            if not full:
                return self.fail(403, "Only files inside the run folder can be shown.")
            if os.path.isdir(full):
                items = []
                for n in sorted(os.listdir(full))[:200]:
                    if n.startswith("."):
                        continue
                    p = os.path.join(full, n)
                    items.append({"name": n + ("/" if os.path.isdir(p) else ""),
                                  "path": os.path.relpath(p, app.run),
                                  "size": os.path.getsize(p) if os.path.isfile(p) else None})
                return self.send(200, {"kind": "dir", "path": rel, "items": items})
            if not os.path.isfile(full):
                return self.fail(404, f"{rel} doesn't exist (yet).")
            ext = os.path.splitext(full)[1].lower()
            if ext in runfiles.IMAGE_EXT:
                if os.path.getsize(full) > 15 * 1024 * 1024:
                    return self.fail(413, "Image is too large to show here.")
                with open(full, "rb") as f:
                    return self.send(200, f.read(), runfiles.IMAGE_EXT[ext])
            size = os.path.getsize(full)
            with open(full, "rb") as f:
                raw = f.read(runfiles.TEXT_LIMIT)
            if b"\x00" in raw[:4096]:
                return self.send(200, {"kind": "binary", "path": rel, "size": size})
            return self.send(200, {"kind": "text", "path": rel, "size": size,
                                   "text": raw.decode("utf-8", "replace"),
                                   "truncated": size > runfiles.TEXT_LIMIT})

        def r_answer(self, d):
            card_id = str(d.get("card") or "")
            choice = str(d.get("choice") or "").strip()
            note = str(d.get("note") or "")
            with app.write_lock:
                st = runfiles.build_state(app.run)
                card = next((c for c in st["cards"] if c["id"] == card_id), None)
                if not card:
                    return self.fail(409, f"{card_id} is no longer open. It may have been answered in the chat.")
                if card["sent"]:
                    return self.fail(409, f"You already answered {card_id}. The orchestrator applies it on its next check.")
                keys = [o["k"] for o in card["options"]]
                if keys and choice and choice not in keys:
                    return self.fail(400, f"Option {choice} isn't on this card.")
                if not keys and choice not in ("", "ok"):
                    return self.fail(400, "This card takes \"ok\" or a written answer.")
                if not choice and not note.strip():
                    return self.fail(400, "Pick an option or write an answer first.")
                chats = [f"chats/{n}" for n in sorted(os.listdir(os.path.join(app.run, "chats")))
                         if n.startswith(runfiles.safe_key(card_id)) and n.endswith(".md")] \
                    if os.path.isdir(os.path.join(app.run, "chats")) else []
                aid, stamp = runfiles.append_answer(app.run, card=card_id, choice=choice, note=note,
                                                    chat=", ".join(chats))
            return self.send(200, {"id": aid, "time": stamp, "card": card_id})

        def r_command(self, d):
            cmd = str(d.get("command") or "")
            m = str(d.get("milestone") or "")
            if cmd not in ("pause", "resume"):
                return self.fail(400, "Only pause and resume are allowed here.")
            with app.write_lock:
                st = runfiles.build_state(app.run)
                if m not in [x["id"] for x in st["milestones"]]:
                    return self.fail(400, f"{m} isn't a milestone in this run.")
                aid, stamp = runfiles.append_answer(app.run, command=f"{cmd} {m}",
                                                    note=str(d.get("note") or ""))
            return self.send(200, {"id": aid, "time": stamp})

        def r_chat(self, d):
            q = str(d.get("question") or "").strip()
            if not q:
                return self.fail(400, "Type a question first.")
            if len(q) > 2000:
                return self.fail(400, "Keep the question under 2,000 characters.")
            st = runfiles.build_state(app.run)
            card_id, opt, mid_ = str(d.get("card") or ""), str(d.get("option") or ""), str(d.get("milestone") or "")
            files = []
            if card_id:
                card = next((c for c in st["cards"] if c["id"] == card_id), None)
                if not card:
                    return self.fail(409, f"{card_id} is no longer open.")
                key = card_id + (f"-opt{opt}" if opt else "")
                context = f"Card {card_id} ({card['kind']}), {card['milestone']}: {card['headline']}"
                if opt:
                    o = next((o for o in card["options"] if o["k"] == opt), None)
                    context += f"\nThey are asking about option {opt}" + (f": {o['title']}" if o else "")
                files.append(f"cards/{card_id}.md")
                files += card.get("evidence", [])
                m = runfiles.mid(card["milestone"])
            elif mid_:
                ms = next((x for x in st["milestones"] if x["id"] == mid_), None)
                if not ms:
                    return self.fail(400, f"{mid_} isn't a milestone in this run.")
                key, m = mid_, mid_
                context = f"Milestone {ms['label']}: {ms['stateLine']}. {ms['now']}"
            else:
                return self.fail(400, "Say what the question is about.")
            if m:
                ms = next((x for x in st["milestones"] if x["id"] == m), None)
                if ms:
                    files.append(ms["status_file"])
            key = runfiles.safe_key(key)
            thread = runfiles.read_thread(app.run, key)[-8:]
            prompt = HELPER_PROMPT.format(
                context=context,
                files="Start with: " + ", ".join(dict.fromkeys(files)) + "\n" if files else "",
                thread="\n".join(f"{'Person' if t['who'] == 'me' else 'Helper'}: {t['text']}"
                                 for t in thread) or "(none)",
                question=q)
            with app.helper.lock(key):
                out, err = app.helper.ask(app.run, prompt)
                if err:
                    return self.fail(502, err)
                text, src = split_sources(out)
                runfiles.append_thread(app.run, key, context, "me", q)
                saved = runfiles.append_thread(app.run, key, context, "ai", text, src)
            return self.send(200, {"key": key, "answer": text, "src": src, "file": saved})

    return H


def free_port(start):
    for p in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    raise SystemExit(f"No free port between {start} and {start + 19}.")


def make_server(run, port=0, token=None, helper_cmd=None, helper_label=""):
    token = token or secrets.token_urlsafe(18)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), None)
    real_port = httpd.server_address[1]
    app = App(run, token, Helper(helper_cmd, helper_label), real_port)
    httpd.RequestHandlerClass = make_handler(app)
    httpd.daemon_threads = True
    return httpd, app


def main(argv=None):
    ap = argparse.ArgumentParser(description="Local dashboard for an orchestrate-task run folder.")
    ap.add_argument("run", help="the run folder (holds REGISTER.md)")
    ap.add_argument("--port", type=int, default=8790)
    ap.add_argument("--helper", help='side chat CLI, e.g. "claude -p --model claude-sonnet-5-5 '
                                     '--allowedTools Read,Grep,Glob". Use {prompt_file} to pass a file '
                                     'instead of stdin.')
    ap.add_argument("--no-helper", action="store_true", help="turn the side chat off")
    ap.add_argument("--open", action="store_true", help="open the page in the browser")
    a = ap.parse_args(argv)
    run = os.path.abspath(os.path.expanduser(a.run))
    if not os.path.isdir(run):
        raise SystemExit(f"{run} is not a folder.")
    if not os.path.isfile(os.path.join(run, "REGISTER.md")):
        print(f"Note: {run} has no REGISTER.md yet; the page will be empty until the run starts.")
    if a.no_helper:
        cmd, label = None, "Side chat is off"
    elif a.helper:
        cmd, label = shlex.split(a.helper), a.helper.split()[0] + " (from --helper)"
    else:
        cmd, label = default_helper(run)
    httpd, app = make_server(run, free_port(a.port), helper_cmd=cmd, helper_label=label)
    url = f"http://127.0.0.1:{app.port}/#t={app.token}"
    print(f"Run dashboard for {run}")
    print(f"Side chat: {label}")
    print(f"Open: {url}")
    print("Ctrl+C stops it. The link holds this session's token; don't share it.")
    sys.stdout.flush()
    if a.open:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    main()
