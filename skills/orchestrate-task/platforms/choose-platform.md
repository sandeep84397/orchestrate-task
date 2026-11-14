# Choosing a platform (`platform` command)

Run this when the user types `platform`, or at setup when more than one platform
could host the run. Check what is actually installed and signed in on this machine,
fill the table with what you find, then recommend one platform with one line of why.

## What to check
- Which host this chat is in (native session tools present → its adapter).
- Other CLIs on PATH and their versions: `claude --version`, `codex --version`,
  `gemini --version`, `agy --version`.
- Whether each one is signed in: run a trivial read-only prompt, or look for an auth
  file without reading its contents.
- The models each one offers today (each adapter's "Model discovery").

## Comparison

| Need | claude-code (desktop) | codex (app) | cli-fallback (Gemini, Antigravity, any CLI) |
|---|---|---|---|
| Children as visible sessions you can open and talk to | Yes, sidebar group | Yes, threads | No, background processes + logs |
| Message a running child | Yes, at its next tool step | Yes | Only between turns (resume) |
| Liveness | Running / last activity | Thread status / wait | PID + log time |
| Heartbeat | `loop` skill | `automation_update` | cron / launchd / shell loop, or manual |
| Subagents with a chosen model | Yes | Yes (`spawn_agent`) | Depends on the CLI |
| Explicit-only invocation | Yes | Yes | Gemini: no (use a custom command) |
| Unattended commands in children | Permission mode | Sandbox + approvals | Needs an autonomy flag |
| Setup effort | Lowest | Low | Highest |

## Recommend by situation
- **You want to watch, open and steer each milestone chat:** a native platform
  (`claude-code` or `codex`), whichever you work in daily.
- **You want the strongest models for planning and review from another vendor:** stay
  on your daily platform and set `plan`/`review` to the other vendor's CLI
  (`references/models.md`, cross-platform roles). Children stay on your platform.
- **Your only agent is Gemini CLI or Antigravity, or you're on a server without a
  desktop app:** `cli-fallback`.
- **Long unattended runs:** native, because their heartbeats are built in.

Output to the user: the filled table (only the columns that are installed), your
recommendation, and one question if a choice is needed.
