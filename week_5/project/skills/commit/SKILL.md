---
name: commit
description: Stage changes and write a clean conventional-commit message. Use when the user asks to commit, save work, or "wrap this up".
---

# Commit workflow
1. Run the test suite with `run_command` using `pytest`. If it fails, stop and report — do not commit broken code.
2. Run `git status` and `git diff` to see what's actually changing.
3. Stage the relevant files using `git add`.
4. Write a conventional-commit message: `type(scope): summary`, imperative mood, under 72 chars.
5. Show me the message and the file list, then commit using `run_command` once I approve.