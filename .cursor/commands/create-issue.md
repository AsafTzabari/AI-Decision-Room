---
name: create-issue
description: Create a GitHub issue with title, body, and optional label, then return the issue URL.
---

# Create a GitHub Issue

Use this command to create a new GitHub issue in the current repository using minimal inputs, with an optional label.

## Prechecks

1. Verify GitHub CLI is installed:
   - Run: `gh --version`
   - If it fails, stop and instruct the user to install GitHub CLI: [https://cli.github.com/](https://cli.github.com/)

2. Verify the user is authenticated:
   - Run: `gh auth status`
   - If it fails, stop and instruct the user to run: `gh auth login`

3. Verify this repository supports Issues and access is valid:
   - Run: `gh issue list --limit 1`
   - If it fails because issues are disabled or permissions are missing, stop and explain the error with a next action.

## Input

Collect the following fields:

Required:
- `title`
- `body`

Optional:
- `label`

If `title` or `body` is missing, ask the user before executing.

## Execution

1. Create the issue with GitHub CLI:
   - If `label` is provided, run: `gh issue create --title "<title>" --body "<body>" --label "<label>"`
   - If `label` is not provided, run: `gh issue create --title "<title>" --body "<body>"`
2. Capture the command output. It should contain the created issue URL.

## Output

In your final response:
1. Confirm that the issue was created.
2. Always include the full clickable GitHub issue URL.

## Failure handling

If any command fails:
- Explain which check/step failed.
- Include the relevant error message in short form.
- Provide one concrete next action.

Examples:
- `gh` not found -> install GitHub CLI.
- auth failed -> run `gh auth login`.
- repo issues disabled -> enable Issues in repository settings.
- permission denied -> use an account with repo write/triage access.
- label not found/invalid -> create the label in the repo first, or rerun without a label.
