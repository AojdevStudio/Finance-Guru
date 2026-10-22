---
name: open-pr
description: Open every pull request through this skill. It self-reviews the diff, proves the change, measures the merge danger, and writes the fixed PR body (Problem, Change, Proof, Review, Merge danger) that the PR gate and the pr-kit CI check require. Use before any `gh pr create`, `gh api .../pulls`, or PR body edit.
metadata:
  category: git/pr
  lanes: [claude, codex, pi]
  machines: [universal]
  requires: [bun, git, gh]
---

# open-pr

The PR body is a briefing for a reviewer who has one minute. A gate checks the body on create, edit, and merge, and the `pr-kit` CI check checks it again. A body that breaks the contract does not open.

## Steps

1. **Rebase.** Fetch the base and rebase onto it. Stop on a conflict you cannot prove correct.
2. **Self-review with the review-gate skill.** Its pre-push receipt already needs a second-model review, so that review is the only one. Do not run `/code-review` as well.
   - Run the checks: `bun ~/.agents/skills/review-gate/scripts/review-receipt.ts run`.
   - Review the diff against the merge base with the reviewer that review-gate step 3 names. Give the reviewer what Pullfrog reads in this repo: the repo's AGENTS.md (and CLAUDE.md when AGENTS.md is absent), plus any file under `.github/pullfrog/`. A local pass then predicts a Pullfrog pass.
   - Give every finding one disposition: **Fix** (fix it now, then review again), **Decline** (write why), or **Defer** (open an issue and link it).
   - A Decline that states a fact about the code must cite the `path:line` or command that proved it in its Reason cell.
   - Record it: `bun ~/.agents/skills/review-gate/scripts/review-receipt.ts review --skill <interrogate|code-review> --act-on N --closed N --notes "<one line>"`.
   - The receipt stores only the counts. Fill the Review table from that same review, one row per finding, so the rows match the receipt.
   - Where the review-gate skill is absent, as in a cloud session, give one fresh-context reviewer the same inputs and skip the receipt commands.
3. **Prove it.** Show evidence that could fail, best first. Evidence that passes while the real goal fails is a Goodhart test, so prove the behavior a user sees, not a mock.
   - For a bug fix, reproduce the reported behavior on the base first and keep it as the before. Check the report against what really happens, since it may not be exact.
   - For a UI or API change, walk the real user path on the base and on the branch, and show the before and after: a screenshot pair or a 15 to 45 second walkthrough for UI, the request and response for an API. Use the repo's recorder script when it has one.
   - For a performance change, a chart or table of the before and after numbers.
   - The test that fails on the base and passes on the branch. Quote the failure.
   - Command output in a code block.
4. **Measure the merge danger.**
   - **Door.** Two-way when a revert undoes it. One-way when it deletes something you didn't make (dead entries that point at nothing stay two-way), deletes data or work that cannot be put back, migrates a schema, publishes, sends, deploys to users, spends money, changes prod user data, or changes a contract that others consume. The door rates the change, not the merge. Merge always waits for the owner's word (see `land-pr`).
   - **Blast radius.** Find what the change can break outside the diff: callers, consumers, config, jobs, other repos. Prove the one fact that makes it safe by running code, not by reading it. Name the radius in one word: `none`, `low`, `medium`, `high`.
5. **Write the body** to a file with the template below. Write in ASD-STE100:
   - Start with the problem. No preamble, no "This PR".
   - One topic per sentence, at most 25 words. Active voice, present tense.
   - Periods and commas. No em dashes.
   - Problem uses at most four sentences.
6. **Check the body.** Run `bun <this skill's dir>/check.ts body.md --title "<title>"`. Fix every violation it names.
7. **Open the PR ready for review.** Never a draft.
   - `gh pr create --title "<title>" --body-file body.md --base <base>`
   - Run the push in its own call before the create, since the alone rule refuses `git push && gh pr create ...`.
   - To write the body in the same call, put the heredoc first and join it with `&&`: `cat > body.md <<'EOF' && gh pr create --title "<title>" --body-file body.md --base <base>`, with the body lines and `EOF` after it. Under noclobber `cat` fails on an existing file, and only `&&` stops gh from then reading the old file. Use `cat >| body.md` when the file already exists.
   - Run it as the only command in its call. The gate checks a PR write only when it runs alone: before it, at most a literal `cd`, a `set` of `-e`, `-u`, `-x`, or `-o pipefail` (other options can change what `cd` or a redirect does), and one `cat > body.md <<'EOF'` joined by `&&` that writes the body file it reads. After it, at most a pipe into a read-only filter such as `tail` or `jq`, with no option or redirect that writes a file. The pipe must follow `gh` itself, not a `bash -c` or `ssh` that runs it, and `tee` is not a filter. With `--body-file`, any other command in the call, such as `git push && gh pr create ...`, a background `&`, a subshell, or an output redirect to a file, makes the gate refuse it. A body passed inline may follow other commands, but not one joined by `||`.
   - In a cloud session, `gh pr` can fail with a 403 because the proxy blocks GraphQL. Use REST: `gh api repos/{owner}/{repo}/pulls -f title="<title>" -F body=@body.md -f head=<branch> -f base=<base>`.
   - Attach screenshots and videos with `gh pr create|edit --attach <file>`. It needs gh 2.99 or newer. Run `gh --version` first.
   - For a remote checkout, prefer an agent session on that machine, in that checkout, so the gate and `gh` share one filesystem.
   - When `gh` runs through `ssh`, put the remote command in single quotes and pass the body inline with a quoted heredoc. Inside single quotes, quote the delimiter with double quotes: `<<"EOF"`.
   - The gate refuses text a shell changes after the gate reads it. That is an unquoted heredoc with `$` or backquotes, and any `$` or backquote in a double-quoted ssh command. The local shell expands the second kind before ssh runs, even under a quoted heredoc. The gate also refuses remote `--body-file` paths, even when the file exists there. It refuses a `gh pr` or `gh api` PR write whose method, a flag, or a field name comes from the shell, such as `-X "$M"` or `"$DRAFT_FLAG"`, since any request could hide in it. Write those as text. It also refuses an unquoted `$...` anywhere in that command, even after `--jq`, because the shell can split it into more flags. Double-quote it: `--jq "$Q"`.
   - After `--attach`, move any appended image links into Proof and keep `Changes made by ...` last. Check the body again before submitting the edit.
8. **Read it back.** `gh api repos/{owner}/{repo}/pulls/<n>` and confirm base, body, and draft state. Then hand over to the `land-pr` skill.

## Install the kit

A repo without the kit gets it in its own PR, opened with this skill. Use the first source you have:

- The fleet store: `bun ~/.agents/skills/open-pr/kit.ts install <repo>`
- A repo that already has the kit: `bun .claude/skills/open-pr/kit.ts install <repo>`
- Neither: download the two skill folders with `gh` from a repo that carries the kit in `.claude/skills/`, then run `kit.ts` from them. Set `src` to that repo.

  ```bash
  repo=/path/to/repo
  (set -e; kit=$(mktemp -d); trap 'rm -rf "$kit"' EXIT
   src=repos/OWNER/REPO/contents/.claude/skills
   for s in open-pr land-pr; do
     mkdir "$kit/$s"
     gh api "$src/$s?ref=main" --jq '.[] | select(.type == "file") | .name' >"$kit/$s.files"
     while read -r f; do gh api -H "Accept: application/vnd.github.raw" "$src/$s/$f?ref=main" >"$kit/$s/$f"; done <"$kit/$s.files"
   done
   bun "$kit/open-pr/kit.ts" install "$repo")
  ```

The runner label comes from `--runs-on <label>`, else the label in the installed `pr-kit.yml`, else the one self-hosted label the repo's other workflows use most. The kit refuses before writing anything when it finds none, a tie, or only a hosted label. Pass `--runs-on` then. A hosted label such as `ubuntu-24.04` is your call to make, never the kit's. A second run keeps the label and prints "PR kit already current".

For a product that ships `.claude/skills`, install with `--layout developer`. The unchanged skill folders go under `.dev/pr-kit`. The installer creates no Claude or Codex discovery links there. Repository instructions point at each `SKILL.md` explicitly. The repository hook and CI checker use that directory. Run an installed developer copy with `bun .dev/pr-kit/open-pr/kit.ts install <repo>`. A bare rerun keeps the recorded layout. The installer refuses conflicting layouts or an implicit move between them.

Keep product instances separate from repository settings. A developer layout still adds a repository hook to `.claude/settings.json`. Instances need their own product settings and must not inherit that file. Bun is required for every repository Bash tool call because the PR gate runs before it.

Every copy of the kit carries a `VERSION` file, and each installed skill's `.pr-kit` marker records the version it installed. An install refuses before writing anything when it runs from a copy behind `kits/pr` in the kit's source repo: the target repo already has a newer version or the same version with other files, the source repo's main has a different `VERSION`, newer, older, or the same one with other files, or the copy's files do not match its own `VERSION`. There is no override. Update the copy with `sk push` or a pull of the kit's source repo, then rerun. After a kit change, run `bun kit.ts stamp` in `kits/pr/open-pr` and commit `VERSION` with the change. `bun test` fails until you do. `stamp` refuses in any other copy, so an installed or synced copy is updated, never restamped.

Stored SHA-256 fingerprints use `sha256:` followed by all 32 bytes as colon-separated hex. The digest calculation is unchanged. Strict parsing accepts older contiguous hex stamps for updates and compares the complete digest.

The gate hook uses `onFailure: "block"`, so a gate that times out or cannot start refuses the command instead of letting it run.

## Template

The title is a conventional commit: `fix(web): new threads no longer spike CPU`. An emoji prefix is allowed when the repo uses one.

```markdown
## Problem
One to four sentences. What is wrong, for whom, and where.

## Change
The smallest visual of the change: a shape-matched diff, a call tree, a file tree, or pseudocode. One sentence above it when the visual needs a caption.

## Proof
| Check | Before | After |
|---|---|---|
| test_name | fails: <quoted error> | passes |

Screenshot pair or walkthrough link when the change is visible.

## Review
| Finding | Disposition | Reason |
|---|---|---|
| The finding in one line | Fix / Decline / Defer #N | Why, with path:line or a proof command for a Decline about code |

## Merge danger
Door: two-way. Revert this PR to undo it.
Blast radius: low. What outside the diff could break, and the fact that proves it safe.

Closes #N
Changes made by <model> via <harness>
```

Rules the check enforces:

- `## Problem` is the first line. The five sections appear in this order, and none is empty. Extra sections such as `## Deviations` may sit between them.
- Proof holds a table, a code block, or a link.
- Code blocks use backtick or tilde fences. A heading inside one is not a section.
- Review holds a table with a `Disposition` column, and each row starts its disposition with `Fix`, `Decline`, or `Defer #<issue>`. Write `No findings.` only when it is the whole section, after a real review.
- Merge danger holds a `Door:` line and a `Blast radius:` line.
- The last line is exactly `Changes made by <model> via <harness>`, for example `Changes made by Claude Opus 5.5 via Claude Code`.
