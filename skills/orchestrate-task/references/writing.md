# Writing to the user

Applies to everything a person reads: orchestrator cards, digests and board; a child's
`BLOCKED` block, `need:` line and reports; PR descriptions. The reader is switching in
from other work, often on a phone, and reads only this message.

The project's communication-style line sets the tone. These rules set the structure;
where the two disagree in text meant for the user, these win.

1. **Answer first.** The first line is the decision needed or the outcome. Background
   comes after, or stays in a file.
2. **Say where it comes from.** Name the milestone and goal on first mention:
   `M4 · #150 Profile tiles · g2`. Never a bare id, never "it" or "the PR".
3. **Short, whole sentences.** One idea per sentence. Terse is fine; dropping the
   subject or the verb is not. No private abbreviations.
4. **Plain words.** Explain a needed term in a few words. Leave out commit hashes,
   file paths, agent ids and tool names unless the reader needs them to act.
5. **Numbers with meaning.** "13 of 17 tests pass; the other 4 only run in the QA
   build", not "13/17".
6. **One word per thing.** Milestone, goal, blocker, approval, question, digest, board.
7. **Shape follows content.** A list for parallel items, one line each. A table only
   to compare several things on the same attributes. No nested bullets. A card is at
   most 10 lines.
8. **Say what is not done.** Not tested, not verified, assumed: stated, never implied.
9. **Verified or claimed.** Say which: "verified: I read the code" or "the child's
   claim, not checked".
10. **End with the ask.** If something waits on the user, the last line says what and
    how to answer. Otherwise end; no summary of the summary.
11. **The user's language.** Mirror it, mixed languages included. Code, commands, paths and
    error text stay exactly as they are.

Before sending, read it as someone who just arrived: do they know what this is about,
what was decided, and what to do next?
