---
name: create-issue
description: Create a GitHub issue with title, body, and optional label, then return the issue URL.
---

# Create a GitHub Issue

- Collect the issue `title` and `body` from me. If either is missing, ask before running anything.
- Optionally collect a `label`. If provided, include it; otherwise omit it.
- Create the issue with `gh`:
  - With label: `GIT_EDITOR=true gh issue create --title "<title>" --body "<body>" --label "<label>"`
  - Without label: `GIT_EDITOR=true gh issue create --title "<title>" --body "<body>"`
- Always paste the link to the created issue in your response so I can click it easily.
- Prepend `GIT_EDITOR=true` to all `gh`/`git` commands you run, so you can avoid getting blocked as you execute commands.
