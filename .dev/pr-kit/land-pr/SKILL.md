---
name: land-pr
description: Drive an open pull request to merge-ready (reviewed, CI green, comments resolved, spec fidelity checked, review bot passed on the head), then merge only on the owner's word. Owns the review-bot pass signal, the convergence rule for fix rounds, spec fidelity, and merge proof. Use after open-pr, for "babysit", "get it green", "address the review comments", or any `gh pr merge`.
metadata:
  category: git/pr
  lanes: [claude, codex, pi]
  machines: [universal]
  requires: [bun, git, gh]
---

# land-pr

The PR gate refuses a merge unless the PR body passes the contract and the review bot passed the exact head. This skill gets the PR to merge-ready, the point where the owner can say "merge". Merging is a separate step that takes the owner's word.

## Merge policy

| Condition | Rule |
|---|---|
| Pass signal | The `pullfrog-approval` check-run from the Pullfrog app concludes `success` on the exact head SHA. Missing, running, failed, or stale verdicts do not pass, and neither does a second run of that name or one from another app. The kit's source repo is the owner's curated settings repo and is never gated by a review bot. |
| Source repo merges | Name the repo in the merge command: `-R <owner>/<repo>` or the PR URL. The gate grants the exemption only then. |
| Conflict fix | When the bot approved the previous head and the only new commit merges the base to resolve conflicts, prove the resolution and merge on that approval. The gate allows this case. |
| CI | Required checks pass on the same head. |
| Threads | Fix actionable findings. Resolve bot threads with evidence. Resolve or disposition every other thread. |
| Authorization | Merge only on the owner's word: an explicit "merge", or a request whose wording implies it ("ship it", "get it merged", "merge when green"). Without it, stop at merge-ready and report the head SHA, CI, bot verdict, threads, and spec fidelity. Never merge when the repo's AGENTS.md forbids agent merges. |
| Other bots | Open Code Review, CodeRabbit, Greptile, and Codex are advisory unless branch rules require them. |

## Convergence rule

A stale PR costs more than one more round. Keep fixing while each round makes progress.

- Fix only confirmed, in-scope blockers. Verify each bot finding against the source first. Dismiss a false positive with a written reason.
- Count the reviews each open finding has been through. A push or a restart does not reset the count.
- The loop spins when one finding is still open at its fourth review, after three fixes.
- The first spin means the approach is wrong, not the patch. Throw out the fix, redesign from the original problem, and push the new approach as the next round. Do not patch the patch.
- If the redesign spins too, stop. Open an issue that names the root cause, link it in the PR, and report. The cause is usually a miss in the local review, or a disagreement between the local review and Pullfrog. A spinning loop is a bug to fix, not a reason to leave the PR.
- When a verdict never starts (no `pullfrog-approval` check-run on the head after 60 minutes), stop and report. That is a runner or app fault, not a review round.

## Steps

1. **Read the state.** `gh api repos/{owner}/{repo}/pulls/<n>` for the head SHA and draft flag, then `gh api repos/{owner}/{repo}/commits/<sha>/check-runs` for CI and `pullfrog-approval`. In a cloud session use REST only, because the proxy blocks GraphQL.
2. **Fix CI.** Read the failing log (`gh run view <id> --log-failed`). Tell a real break from a known infra flake. Fix real breaks in a new commit.
3. **Handle review comments.** Fetch them with `gh api repos/{owner}/{repo}/pulls/<n>/comments` and `.../reviews`. Fix, decline with a reason, or defer to an issue. Add each to the PR body's Review table.
   - Mark each Pullfrog finding that the local review missed with `missed locally` in its Reason cell, so the local review instructions can learn from it.
   - List unresolved threads with variables. Set `owner`, `repo`, and `pr` from the PR, then copy the returned thread ID into `thread_id`. Pagination includes threads after the first 50.

     ```bash
     gh api graphql --paginate -f query='query($owner:String!,$repo:String!,$n:Int!,$endCursor:String){repository(owner:$owner,name:$repo){pullRequest(number:$n){reviewThreads(first:50,after:$endCursor){pageInfo{hasNextPage endCursor} nodes{id isResolved comments(first:1){nodes{databaseId}}}}}}}' -f owner="$owner" -f repo="$repo" -F n="$pr" --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)'
     gh api graphql -f query='mutation($id:ID!){resolveReviewThread(input:{threadId:$id}){thread{isResolved}}}' -F id="$thread_id"
     ```

4. **Wait on the real state change.** Watch the check-run, not a timer. Count the round and apply the convergence rule.
   - When a T3 watch is the wake source and Bash supports `run_in_background`, also arm one bounded `until` loop on the head's `pullfrog-approval` check-run as a backstop.
5. **Check spec fidelity before merge.** Diff the result against the issue, the plan, or the mock. Post every deviation, or "no deviations", as a PR comment.
6. **Merge, on the owner's word.** Without it, stop here and report merge-ready. With it, first check allowed methods with `gh api repos/{owner}/{repo} --jq '{allow_squash_merge,allow_merge_commit,allow_rebase_merge}'`. Follow the repo's required method if allowed. Otherwise fetch main and run `git log origin/main --first-parent -10 --format='%h %p %s'`. Two parents show a merge commit. Squash and rebase history can look the same. Use an allowed method supported by policy or history, and prefer squash when neither names one. Stop if the evidence conflicts with the settings. Run `gh pr merge <n> <method flag>` alone in its call, with `-R <owner>/<repo>` when the current directory is not that repo's checkout. The gate checks a merge only when nothing runs before it but a literal `cd` or a `set` of `-e`, `-u`, `-x`, or `-o pipefail`, and nothing runs beside or after it, not even a pipe into a filter, since any other command can move the head. The merge is the only command in its call, so `git pull` or `git checkout main` runs in a later call. The gate checks the policy again.
7. **Prove the merge.** Only `gh api repos/{owner}/{repo}/pulls/<n> --jq .merged` returning `true` proves it. A tool's success message does not.

## Never

- Never pass `--no-verify`, skip a hook, or bypass the gate. Fix the cause or report the blocker.
- Never force-push, amend, or rebase a branch others fetched without the owner's yes for that push.
- Never write `CHANGELOG.md` on a PR branch. The release on main writes it.
- Never open or leave a PR as a draft. Drafts get no review-bot coverage.
