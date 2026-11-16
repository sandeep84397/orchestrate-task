"""Tests for the run dashboard. Run: python3 -m unittest test_dashboard (from this folder)."""
import http.client
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import runfiles  # noqa: E402
import server  # noqa: E402

SAMPLE = os.path.join(HERE, "sample-run")


class Base(unittest.TestCase):
    helper = None

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.run = os.path.join(self.tmp, "run")
        shutil.copytree(SAMPLE, self.run)
        self.httpd, self.app = server.make_server(self.run, 0, token="tok", helper_cmd=self.helper,
                                                  helper_label="fake")
        self.t = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.t.start()

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        shutil.rmtree(self.tmp)

    def req(self, method, path, body=None, token="tok", host=None, ctype="application/json"):
        c = http.client.HTTPConnection("127.0.0.1", self.app.port, timeout=10)
        h = {"Host": host or f"127.0.0.1:{self.app.port}"}
        if token is not None:
            h["X-Token"] = token
        data = None
        if body is not None:
            data = json.dumps(body).encode()
            h["Content-Type"] = ctype
        c.request(method, path, body=data, headers=h)
        r = c.getresponse()
        raw = r.read()
        c.close()
        try:
            return r.status, json.loads(raw)
        except ValueError:
            return r.status, raw


class ParseTests(unittest.TestCase):
    def test_sample_state(self):
        s = runfiles.build_state(SAMPLE)
        self.assertEqual(s["run"]["title"], "Sample run")
        self.assertEqual((s["progress"]["done"], s["progress"]["total"]), (17, 25))
        self.assertEqual([c["id"] for c in s["cards"]], ["B1", "Q7", "Q4", "Q8", "Q9"])
        b1 = s["cards"][0]
        self.assertEqual(b1["kind"], "blocker")
        self.assertEqual([o["k"] for o in b1["options"]], ["A", "B", "C"])
        self.assertTrue(b1["facts"][-1]["verified"])
        q9 = s["cards"][-1]
        self.assertFalse(q9.get("has_card_file", False))
        self.assertEqual(q9["milestone"], "M5 · #149 Upload UX · g4")
        ms = {m["id"]: m for m in s["milestones"]}
        self.assertEqual(s["milestones"][0]["id"], "M3")  # blocked sorts first
        self.assertEqual(ms["M3"]["st"], "b")
        self.assertEqual(ms["M2"]["stateLine"], "Merge waiting on you")
        self.assertEqual(ms["M1"]["st"], "w")  # Q4 unblocks its current goal
        self.assertEqual(ms["M5"]["st"], "n")  # questions about later goals don't stop it
        self.assertEqual(ms["M4"]["now"], "Merged at 12:10")
        self.assertEqual(ms["M3"]["goals"][3]["evidence"], ["milestones/M3/evidence/g4/"])
        self.assertEqual(s["feed"][0]["text"], "Review passed for g2")

    def test_empty_folder(self):
        d = tempfile.mkdtemp()
        try:
            s = runfiles.build_state(d)
            self.assertFalse(s["run"]["found"])
            self.assertEqual(s["cards"], [])
            self.assertEqual(s["milestones"], [])
        finally:
            shutil.rmtree(d)

    def test_tables_handle_escaped_pipes_and_missing_cells(self):
        t = runfiles.tables("| a | b |\n|---|---|\n| x \\| y |\n")[0]
        self.assertEqual(t["rows"][0], {"a": "x | y", "b": ""})

    def test_resolve_blocks_escape(self):
        self.assertIsNone(runfiles.resolve(SAMPLE, "../server.py"))
        self.assertIsNone(runfiles.resolve(SAMPLE, "/etc/passwd"))
        self.assertTrue(runfiles.resolve(SAMPLE, "cards/B1.md"))


class ApiTests(Base):
    def test_security(self):
        self.assertEqual(self.req("GET", "/api/state", token=None)[0], 401)
        self.assertEqual(self.req("GET", "/api/state", token="nope")[0], 401)
        self.assertEqual(self.req("GET", "/api/state", host="evil.example:80")[0], 403)
        self.assertEqual(self.req("GET", "/api/file?path=../../etc/passwd")[0], 403)
        self.assertEqual(self.req("POST", "/api/answer", {"card": "B1", "choice": "A"},
                                  ctype="text/plain")[0], 400)
        self.assertEqual(self.req("GET", "/static/../server.py")[0], 404)

    def test_index_needs_no_token(self):
        st, raw = self.req("GET", "/", token=None)
        self.assertEqual(st, 200)
        self.assertIn(b"Run board", raw)

    def test_state_and_unchanged(self):
        st, d = self.req("GET", "/api/state")
        self.assertEqual(st, 200)
        self.assertEqual(d["counts"]["blockers"], 1)
        st, d2 = self.req("GET", "/api/state?since=" + d["sig"])
        self.assertTrue(d2["unchanged"])

    def test_answer_flow(self):
        st, r = self.req("POST", "/api/answer", {"card": "B1", "choice": "A", "note": "line one\nline two"})
        self.assertEqual((st, r["id"]), (200, "ANS-1"))
        md = runfiles.read(os.path.join(self.run, "ANSWERS.md"))
        self.assertIn("## ANS-1 · ", md)
        self.assertIn("card B1", md)
        self.assertIn("> line two", md)
        a = runfiles.parse_answers(md)[0]
        self.assertEqual((a["card"], a["choice"], a["note"]), ("B1", "A", "line one\nline two"))
        # second answer to the same card is refused until the orchestrator reads it
        self.assertEqual(self.req("POST", "/api/answer", {"card": "B1", "choice": "B"})[0], 409)
        st, d = self.req("GET", "/api/state")
        self.assertTrue(d["cards"][0]["sent"])
        self.assertEqual(d["sent"][0]["id"], "ANS-1")
        # orchestrator logs it → no longer pending
        reg = os.path.join(self.run, "REGISTER.md")
        with open(reg, "a") as f:
            f.write("\n")
        txt = runfiles.read(reg).replace("## Answers log\n", "## Answers log\n- 15:00 ANS-1 (dashboard) B1 → \"A\"\n")
        with open(reg, "w") as f:
            f.write(txt)
        st, d = self.req("GET", "/api/state")
        self.assertEqual(d["sent"], [])

    def test_answer_validation(self):
        self.assertEqual(self.req("POST", "/api/answer", {"card": "B1", "choice": "Z"})[0], 400)
        self.assertEqual(self.req("POST", "/api/answer", {"card": "B1"})[0], 400)
        self.assertEqual(self.req("POST", "/api/answer", {"card": "Q3", "choice": "ok"})[0], 409)  # answered
        self.assertEqual(self.req("POST", "/api/answer", {"card": "Q9", "choice": "A"})[0], 400)
        st, r = self.req("POST", "/api/answer", {"card": "Q9", "choice": "", "note": "Use the Pixel 8"})
        self.assertEqual(st, 200)

    def test_command(self):
        st, r = self.req("POST", "/api/command", {"command": "pause", "milestone": "M5"})
        self.assertEqual(st, 200, r)
        self.assertIn("command: pause M5", runfiles.read(os.path.join(self.run, "ANSWERS.md")))
        self.assertEqual(self.req("POST", "/api/command", {"command": "merge", "milestone": "M2"})[0], 400)
        self.assertEqual(self.req("POST", "/api/command", {"command": "pause", "milestone": "M9"})[0], 400)

    def test_file(self):
        st, d = self.req("GET", "/api/file?path=milestones/M3/evidence/g4/")
        self.assertEqual(d["kind"], "dir")
        self.assertIn("real-sample.json", [i["name"] for i in d["items"]])
        st, d = self.req("GET", "/api/file?path=cards/B1.md")
        self.assertIn("kind: blocker", d["text"])
        self.assertEqual(self.req("GET", "/api/file?path=nope.md")[0], 404)

    def test_chat_without_helper(self):
        st, r = self.req("POST", "/api/chat", {"card": "B1", "question": "why?"})
        self.assertEqual(st, 502)
        self.assertIn("no helper", r["error"])


class ChatTests(Base):
    helper = [sys.executable, "-c",
              "import sys; p=sys.stdin.read(); assert 'read-only helper' in p; "
              "print('It is empty because the thumbnail is made later.'); print('Sources: cards/B1.md')"]

    def test_chat_round_trip(self):
        st, r = self.req("POST", "/api/chat", {"card": "B1", "option": "A", "question": "Why empty?"})
        self.assertEqual(st, 200, r)
        self.assertEqual(r["key"], "B1-optA")
        self.assertEqual(r["src"], "cards/B1.md")
        self.assertNotIn("Sources", r["answer"])
        st, t = self.req("GET", "/api/chat?key=B1-optA")
        self.assertEqual([m["who"] for m in t["thread"]], ["me", "ai"])
        self.assertEqual(t["thread"][1]["src"], "cards/B1.md")
        # the answer carries the chat file along
        self.req("POST", "/api/answer", {"card": "B1", "choice": "A"})
        self.assertIn("chat: chats/B1-optA.md", runfiles.read(os.path.join(self.run, "ANSWERS.md")))

    def test_chat_validation(self):
        self.assertEqual(self.req("POST", "/api/chat", {"card": "B1", "question": "  "})[0], 400)
        self.assertEqual(self.req("POST", "/api/chat", {"question": "hi"})[0], 400)
        self.assertEqual(self.req("POST", "/api/chat", {"milestone": "M9", "question": "hi"})[0], 400)
        st, r = self.req("POST", "/api/chat", {"milestone": "M3", "question": "status?"})
        self.assertEqual((st, r["key"]), (200, "M3"))


class HelperDefaultTests(unittest.TestCase):
    def test_review_role_model_is_used(self):
        cmd, label = server.default_helper(SAMPLE)
        if cmd and cmd[0] == "claude":
            self.assertIn("claude-sonnet-5-5", cmd)
            self.assertIn("Read,Grep,Glob", cmd)
            self.assertNotIn("Bash", cmd[cmd.index("--allowedTools") + 1])

    def test_split_sources(self):
        self.assertEqual(server.split_sources("Answer.\nSources: a.md, b.md"), ("Answer.", "a.md, b.md"))
        self.assertEqual(server.split_sources("No sources"), ("No sources", ""))


if __name__ == "__main__":
    unittest.main()
