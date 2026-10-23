/**
 * The merge decision: may this PR head merge, judged from the review bot's check-runs.
 * Pure, so the gate and tests share it. The gate fetches the state over the REST API.
 *
 * Pullfrog is the active review bot. Its `pullfrog-approval` check-run concluding
 * `success` on the exact head is the pass signal. The gate reads the latest run per check
 * suite, and Pullfrog has one suite per commit, so its reruns collapse to one run. A second
 * run of that name, or a run from another app, means another producer used the name, and
 * no verdict on that commit is trusted. One exception: when the bot approved
 * the previous head and the head is a merge commit on top of it (a conflict fix), the
 * approval carries forward, provided the merged-in parent is on the base branch and no
 * finished verdict on the head itself says otherwise.
 *
 * The kit's source repo is the owner's curated settings repo, and no review bot gates it. The
 * list lives here in the kit, never in a file the target repo could edit. It holds SHA-256
 * digests of lowercase `owner/name`, so the kit can ship to public repos without naming a
 * private one. The exemption holds only when the merge command names the repo itself,
 * because a repo guessed from the cwd or the environment can differ from the one gh merges.
 */

export const PASS_SIGNAL = "pullfrog-approval";
/** Slug of the GitHub App that publishes PASS_SIGNAL. */
export const PASS_APP = "pullfrog";

const BOT_EXEMPT = new Set([
  "sha256:61:59:f3:8c:55:de:a3:14:c9:6c:15:a2:b5:dd:f2:ed:d3:2a:5b:51:01:9c:9d:0b:45:21:e2:ff:07:7c:08:15",
  "sha256:84:25:c2:e9:1b:73:ef:6b:8e:23:37:0c:43:b9:c5:d4:bb:3d:b3:76:68:4c:ba:dc:c1:31:c2:69:df:f4:7b:be",
]);

/** True for a repo that no review bot gates. `repo` is `owner/name`, any case. */
export const botExempt = (repo: string): boolean =>
  BOT_EXEMPT.has(new Bun.CryptoHasher("sha256").update(repo.toLowerCase()).digest("hex").replace(/(..)(?=.)/g, "$1:").replace(/^/, "sha256:"));

export interface CheckRun {
  name: string;
  status: string;
  conclusion: string | null;
  /** Slug of the GitHub App that created the run. */
  app: string;
}

export interface HeadState {
  /** The PR's base repo as GitHub reports it, `owner/name`. */
  repo: string;
  /** The merge command named the repo with `-R`, a PR URL, or a literal REST path. */
  pinned: boolean;
  sha: string;
  parents: string[];
  /** Latest check-runs named PASS_SIGNAL on the head. */
  runs: CheckRun[];
  /** Latest check-runs named PASS_SIGNAL on parents[0]. Fetched only for a merge commit. */
  parentRuns?: CheckRun[];
  /** For a merge commit: parents[1] is the base branch head or one of its ancestors. */
  mergesBase?: boolean;
}

export type MergeVerdict =
  | { ok: true; via: "approval" | "conflict-fix" | "exempt" }
  | { ok: false; reason: string };

/**
 * The bot's current verdict on one commit. `open` (missing or running) lets a conflict fix
 * inherit its parent's approval. `refused` (finished non-success, or untrusted) never does.
 */
export type Verdict = { state: "pass" } | { state: "open" | "refused"; why: string };

export function verdictOf(runs: CheckRun[]): Verdict {
  const named = runs.filter((r) => r.name === PASS_SIGNAL);
  if (named.length === 0) return { state: "open", why: `no ${PASS_SIGNAL} check-run exists` };
  if (named.length > 1) {
    return { state: "refused", why: `${named.length} latest ${PASS_SIGNAL} check-runs exist (apps: ${named.map((r) => r.app).join(", ")}), so the verdict is ambiguous` };
  }
  const [run] = named;
  if (run.app !== PASS_APP) return { state: "refused", why: `${PASS_SIGNAL} comes from the ${run.app} app, not ${PASS_APP}` };
  if (run.status !== "completed") return { state: "open", why: `${PASS_SIGNAL} is ${run.status}` };
  return run.conclusion === "success" ? { state: "pass" } : { state: "refused", why: `${PASS_SIGNAL} concluded ${run.conclusion}` };
}

export function decideMerge(head: HeadState): MergeVerdict {
  if (botExempt(head.repo)) {
    if (head.pinned) return { ok: true, via: "exempt" };
    return { ok: false, reason: `${head.repo} skips the review bot only when the merge names it. Pass -R ${head.repo} or the PR URL.` };
  }
  const verdict = verdictOf(head.runs);
  if (verdict.state === "pass") return { ok: true, via: "approval" };
  const conflictFix = verdict.state === "open" && head.parents.length === 2 && head.mergesBase === true;
  if (conflictFix && head.parentRuns && verdictOf(head.parentRuns).state === "pass") return { ok: true, via: "conflict-fix" };
  return { ok: false, reason: `${verdict.why} on head ${head.sha.slice(0, 7)}. A missing, running, failed, or untrusted verdict does not pass.` };
}
