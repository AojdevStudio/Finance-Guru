---
name: land-pr
description: Drive an open pull request to merge-ready (reviewed, CI green, comments resolved, spec fidelity checked, project verify skills passed, review bot passed on the head), then merge under the merge policy (on its own at medium merge danger or lower, otherwise on the owner's word). Owns the review-bot pass signal, the convergence rule for fix rounds, spec fidelity, and merge proof. Use after open-pr, for "babysit", "get it green", "address the review comments", or any `gh pr merge`.
metadata:
  category: git/pr
  lanes: [claude, codex, pi]
  machines: [universal]
  requires: [bun, git, gh]
---

# land-pr

The PR gate refuses a merge unless the PR body passes the contract and the review bot passed the exact head. This skill gets the PR to merge-ready. Merging is a separate step: the agent merges on its own when the PR's merge danger is medium or lower, and otherwise takes the owner's word.

## Merge policy

| Condition | Rule |
|---|---|
| Pass signal | The `pullfrog-approval` check-run from the Pullfrog app concludes `success` on the exact head SHA. Missing, running, failed, or stale verdicts do not pass, and neither does a second run of that name or one from another app. The kit's source repo is the owner's curated settings repo and is never gated by a review bot. CodeRabbit is the review bot for the repos `merge.ts` lists in `CODERABBIT_GATED` (the CLIProxyAPI panel fork, 2026-11-03). The owner is on CodeRabbit's free plan, which posts reviews but never approves, so there the pass signal is a finished, clean review of the exact head. Finished means CodeRabbit's own `CodeRabbit` check-run (app `coderabbitai`) on the head concluded `success` with "Review completed" in its summary, so a skipped or unknown run never passes. Its summary comment is no proof, because it names the head while the review still runs. Clean means no CodeRabbit review thread is unresolved, and none of its reviews lists "Outside diff range comments". Fix or answer each finding, then resolve its thread. Outside-diff findings have no thread, and later incremental reviews do not repeat them, so a PR with any goes to the owner, who checks them and merges in GitHub. CodeRabbit reads its config from the branch under review, so the gate refuses a PR that touches any file whose name starts with `.coderabbit` (`.coderabbit.yaml`, `.coderabbit.yml`, `.coderabbit.config.ts`), and one whose file list GitHub returns incomplete. Keep no CodeRabbit config file on the default branch of a CodeRabbit-gated repo, because a config there (a `.coderabbit.config.ts` can import any file) could change the review through files the guard does not watch. A top-level `@coderabbitai approve` or `@coderabbitai resolve` comment skips or closes the review, so the gate also refuses a PR that has one. Never post either command. Ask for a review with `@coderabbitai review`. The owner merges a refused PR in GitHub. |
| Exempt repo merges | For any repo on the exemption list, name the repo in the merge command (`-R <owner>/<repo>` or the PR URL), even inside its checkout. The gate grants the exemption only then. |
| Conflict fix | A conflict-resolution commit changes the head. Wait for a successful `pullfrog-approval` check-run on that exact head before merging. An exempt repo has no check-run to wait for. It needs green CI and a local review of the new head instead. |
| CI | Required checks pass on the same head. |
| Threads | Fix actionable findings. Resolve bot threads with evidence. Resolve or disposition every other thread. |
| Agent merge | The agent merges without asking when all of these hold on the exact head: the PR body's Merge danger shows a blast radius of `none`, `low`, or `medium`, required CI passes, the project's verify skills pass (step 6), and the pass signal passes. A repo with no review bot qualifies only when this kit's exemption list (`merge.ts`) names it, because that list is the owner's record that the repo has no bot on purpose. Never add a repo to that list to make a merge pass. The rating counts only as the local review left it. If the blast radius was lowered after that review, the agent does not merge on its own. The gate checks the body and the bot verdict, not the rating, so this rule is the agent's to keep. The owner set this rule on 2026-10-30. |
| Owner's word | Every other merge takes the owner's word: a `high` blast radius, a rating lowered after review, or a repo with no review bot and no exemption. The word is an explicit "merge", or a request whose wording implies it ("ship it", "get it merged", "merge when green"). For "merge when green", wait for required checks and exact-head approval, then use a merge pinned to that approved head. Without the word, stop at merge-ready and report the head SHA, CI, bot verdict, threads, spec fidelity, verify skills, and merge danger. A `high` PR also gets an explainer video first (see Explainer video for a high PR). |
| Always | Never pass `--admin` or `--auto`. The gate refuses both. Never merge when the repo's AGENTS.md forbids agent merges. |
| Other bots | Open Code Review, CodeRabbit, Greptile, and Codex are advisory unless branch rules require them. |

## Convergence rule

A stale PR costs more than one more round. Keep fixing while each round makes progress.

- Fix only confirmed, in-scope blockers. Verify each bot finding against the source first. Dismiss a false positive with a written reason.
- Count the reviews each open finding has been through. A push or a restart does not reset the count.
- The loop spins when one finding is still open at its fourth review, after three fixes.
- The first spin means the approach is wrong, not the patch. Throw out the fix, redesign from the original problem, and push the new approach as the next round. Do not patch the patch.
- If the redesign spins too, stop. Open an issue that names the root cause, link it in the PR, and report. The cause is usually a miss in the local review, or a disagreement between the local review and Pullfrog. A spinning loop is a bug to fix, not a reason to leave the PR.
- When a verdict never starts (no `pullfrog-approval` check-run, or in a CodeRabbit-gated repo no `CodeRabbit` check-run, on the head after 60 minutes, in a repo that is not exempt), stop and report. That is a runner or app fault, not a review round.

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
6. **Run the project's verify skills on the head.** Run `git fetch origin <base>` and check out the exact head you will merge. Run `bun <this skill's dir>/../open-pr/verify.ts --base origin/<base>` in the repo, then read each listed `SKILL.md` in full and run it, in the listed order. The listed paths are relative to the repo root.
   - When one fails, stop. Do not merge. Report the skill, the failing step, and its output on the PR. A skill that cannot start counts as a failure, and so does a non-zero exit from `verify.ts`. Never read a `verify.ts` error as nothing to run. A fix is a new head, so it goes through this skill again.
   - When it prints `verify: none.`, note that line in the merge-ready report and go on.
7. **Merge under the merge policy.** Read the Merge danger section of the PR body as it is now, since a fix round can change it. If the policy leaves this merge to the owner and the owner has not given the word, stop here and report merge-ready. For a `high` blast radius, make the explainer video below before you report. Otherwise, first check allowed methods with `gh api repos/{owner}/{repo} --jq '{allow_squash_merge,allow_merge_commit,allow_rebase_merge}'`. Follow the repo's required method if allowed. Otherwise fetch main and run `git log origin/main --first-parent -10 --format='%h %p %s'`. Two parents show a merge commit. Squash and rebase history can look the same. Use an allowed method supported by policy or history, and prefer squash when neither names one. Stop if the evidence conflicts with the settings. Run `gh pr merge <n> <method flag> --match-head-commit <approved-head-sha>` alone in its call, with `-R <owner>/<repo>` when the current directory is not that repo's checkout or the repo is exempt. The gate checks a merge only when nothing runs before it but a literal `cd` or a `set` of `-e`, `-u`, `-x`, or `-o pipefail`, and nothing runs beside or after it, not even a pipe into a filter, since any other command can move the head. Nonexempt REST merges must also name that same head in the `sha` field. The asynchronous REST `merge-async` endpoint is refused. The merge is the only command in its call, so `git pull` or `git checkout main` runs in a later call. The gate checks the policy again.
8. **Prove the merge.** Only `gh api repos/{owner}/{repo}/pulls/<n> --jq .merged` returning `true` proves it. A tool's success message does not.

## Explainer video for a high PR

A `high` PR waits for the owner. He decides by watching a short video, not by reading the diff, so the PR reaches him with one. The owner set this rule on 2026-10-30.

1. Make the video when the PR is merge-ready, so it shows the final change. Use `Skill("explainer-video")`.
2. Build its `brief.md` only from the PR body, the diff, and the linked issue or plan. Cover what the change does, why, what outside the diff it can break, how to undo it, and the decision the owner makes. Aim for 2 to 3 minutes.
3. Post it on the PR with `gh pr comment <n> --attach <mp4>` and a one-line caption that names the head SHA. `<mp4>` is the copy the video skill's Deliver step puts in `~/Movies/` on the machine that runs `gh`, not the render folder, which the skill deletes. Add the `serve` URL in the same comment. Use `pr-media` when GitHub refuses the file.
4. Put the T3 embed and the URL in the merge-ready report.
5. When a later push changes what the video says, make it again. A video of an older head misleads the owner.
6. When hush has no ElevenLabs key, narrate with a free or local voice, as AGENTS.md says. If any other part of the skill cannot run, say which part failed in the PR comment and the report. Do not swap in a weaker format, such as slides or text, and call it the video.

## Never

- Never pass `--no-verify`, skip a hook, or bypass the gate. Fix the cause or report the blocker.
- Never force-push, amend, or rebase a branch others fetched without the owner's yes for that push.
- Never write `CHANGELOG.md` on a PR branch. The release on main writes it.
- Never open or leave a PR as a draft. Drafts get no review-bot coverage.
