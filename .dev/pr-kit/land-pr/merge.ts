/**
 * The merge decision: may this PR head merge, judged from the review bot's check-runs.
 * Pure, so the gate and tests share it. The gate fetches the state over the REST API.
 *
 * Pullfrog is the active review bot. Its `pullfrog-approval` check-run concluding
 * `success` on the exact head is the pass signal. The gate reads the latest run per check
 * suite, and Pullfrog has one suite per commit, so its reruns collapse to one run. A second
 * run of that name, or a run from another app, means another producer used the name, and
 * no verdict on that commit is trusted. Every merge requires a successful verdict on the
 * exact head, including a merge commit that resolves conflicts.
 *
 * The kit's source repo is the owner's curated settings repo, and no review bot gates it.
 * The owner also exempted two repos with no review bot installed, which take local reviews only
 * (2026-10-27), and six product meta (planning) repos with no review bot installed (2026-10-29). The list lives here in the kit, never in a file the target repo could edit. It holds SHA-256
 * digests of lowercase `owner/name`, so the kit can ship to public repos without naming a
 * private one. The exemption holds only when the merge command names the repo itself,
 * because a repo guessed from the cwd or the environment can differ from the one gh merges.
 *
 * CodeRabbit is the review bot for the repos in CODERABBIT_GATED, the owner's call on
 * 2026-11-03 for his open-source fork of the CLIProxyAPI panel. His CodeRabbit plan posts
 * reviews but never approves, so the pass signal is a finished review of the exact head with
 * nothing left open. A finished review is CodeRabbit's own `CodeRabbit` check-run on the head
 * concluding `success` with "Review completed" in its summary, so a skipped or unknown run never
 * passes. Only the CodeRabbit app can write that check. Its summary comment is no
 * proof, because it names the head while the review is still running, and a review tied to the
 * head is none either, because a reply in a review thread also creates one. Open findings are
 * CodeRabbit review threads nobody resolved, and "Outside diff range" comments in any of its
 * reviews. Those have no thread, and an incremental review does not repeat them, so nothing on
 * GitHub shows them fixed. The owner checks them and merges in GitHub.
 */

export const PASS_SIGNAL = "pullfrog-approval";
/** Slug of the GitHub App that publishes PASS_SIGNAL. */
export const PASS_APP = "pullfrog";
/** Login of CodeRabbit's bot user. Only a GitHub App can hold a `[bot]` login. */
export const CODERABBIT = "coderabbitai[bot]";
/** The check-run CodeRabbit keeps on each commit it reviews, and the slug of the app that writes it. */
export const CODERABBIT_CHECK = "CodeRabbit";
export const CODERABBIT_APP = "coderabbitai";

const BOT_EXEMPT = new Set([
  "sha256:61:59:f3:8c:55:de:a3:14:c9:6c:15:a2:b5:dd:f2:ed:d3:2a:5b:51:01:9c:9d:0b:45:21:e2:ff:07:7c:08:15",
  "sha256:84:25:c2:e9:1b:73:ef:6b:8e:23:37:0c:43:b9:c5:d4:bb:3d:b3:76:68:4c:ba:dc:c1:31:c2:69:df:f4:7b:be",
  "sha256:2a:c1:f2:9e:c5:a3:38:67:97:c9:ab:31:e1:3b:8c:4f:63:46:b3:92:11:eb:40:66:e9:3f:44:8b:4c:f7:96:74",
  "sha256:9b:98:ef:a7:4d:ad:15:2a:b3:62:db:66:30:bb:27:60:3c:d2:ac:3c:13:b5:a5:65:44:32:a4:1e:3e:ca:46:3b",
  "sha256:c8:17:59:66:37:f0:0a:16:33:ec:6c:b2:54:96:61:8f:52:15:4b:43:eb:1a:e2:84:28:bc:b0:24:7a:34:72:6a",
  "sha256:00:cb:41:cb:ec:c8:f6:49:69:37:8b:d6:74:1e:bc:84:8b:e3:0a:77:3b:9e:14:b9:9f:36:09:18:07:20:3f:4a",
  "sha256:d0:b2:20:80:6e:04:c3:c3:e1:fb:f9:d5:b5:b1:47:14:10:c1:92:3d:b0:f0:10:c7:1c:5f:a0:1d:61:99:fb:a4",
  "sha256:31:4d:64:65:db:3e:85:9f:55:3a:7d:87:a9:0f:a9:55:9a:c6:81:1b:8f:a7:14:b9:69:d0:9a:53:6e:82:69:03",
  "sha256:8a:60:35:cf:9f:fe:e9:f6:e6:73:7e:2b:f7:84:b6:13:af:92:3f:a7:e4:f4:28:ba:d5:3e:d5:de:f6:7a:9b:07",
  "sha256:51:1f:ed:46:6f:52:26:97:e0:71:43:ad:a6:19:ec:44:c7:32:52:01:90:5d:9c:ac:b5:5f:b5:76:35:fa:7c:a8",
  "sha256:af:68:ff:91:e8:1e:9f:10:fe:b5:34:02:ca:5f:43:53:b5:be:14:60:2f:2d:36:0c:a7:c6:a6:4b:8d:f4:67:e0",
]);

const CODERABBIT_GATED = new Set([
  "sha256:64:c4:1e:62:42:e6:ea:d2:b5:75:66:b3:db:d3:99:49:d8:36:28:04:06:9a:ff:9e:f5:a4:72:c9:18:fd:ae:b1",
]);

const digest = (repo: string): string =>
  new Bun.CryptoHasher("sha256").update(repo.toLowerCase()).digest("hex").replace(/(..)(?=.)/g, "$1:").replace(/^/, "sha256:");

/** True for a repo that no review bot gates. `repo` is `owner/name`, any case. */
export const botExempt = (repo: string): boolean => BOT_EXEMPT.has(digest(repo));

export type ReviewBot = "pullfrog" | "coderabbit";

/** The review bot whose verdict gates a repo's merges. `repo` is `owner/name`, any case. */
export const reviewBotOf = (repo: string): ReviewBot => (CODERABBIT_GATED.has(digest(repo)) ? "coderabbit" : "pullfrog");

export interface Review {
  /** The REST login, null when the account was deleted. */
  login: string | null;
  body: string;
  /** The commit the review was submitted on, null when GitHub no longer has it. */
  commitId: string | null;
}

export interface Thread {
  /** REST-style login of the account that opened the thread (`[bot]` suffix for apps), null when deleted. */
  author: string | null;
  resolved: boolean;
}

/**
 * CodeRabbit reads its config (`.coderabbit.yaml`, `.coderabbit.yml`, `.coderabbit.config.ts`)
 * from the branch under review, so a PR that changes it could loosen the review that passes it.
 * Any path whose file name starts with `.coderabbit` counts, at any depth.
 */
const CODERABBIT_CONFIG = /(^|\/)\.coderabbit[^/]*$/;

/** What the gate read from GitHub for the repo's review bot. */
export type Evidence =
  | { bot: "pullfrog"; runs: CheckRun[] }
  /** `runs` are the latest CODERABBIT_CHECK runs on the head. `comments` are every top-level PR comment body. `paths` holds every path the PR adds, changes, removes, or renames from. */
  | { bot: "coderabbit"; runs: CheckRun[]; comments: string[]; reviews: Review[]; threads: Thread[]; paths: string[] };

/** Commands that make CodeRabbit approve or resolve its threads without a finished review (docs: pr-reviews/automatic-approvals). */
const ON_DEMAND_APPROVAL = /@coderabbitai\s+(approve|resolve)\b/i;
const OUTSIDE_DIFF = /Outside diff range comments \((\d+)\)/i;
const REVIEW_COMPLETED = /\bReview completed\b/;

export interface CheckRun {
  name: string;
  status: string;
  conclusion: string | null;
  /** Slug of the GitHub App that created the run. */
  app: string;
  /** The run's output summary, null when it has none. */
  summary: string | null;
}

export interface HeadState {
  /** The PR's base repo as GitHub reports it, `owner/name`. */
  repo: string;
  /** The merge command named the repo with `-R`, a PR URL, or a literal REST path. */
  pinned: boolean;
  sha: string;
  /** What the gate read for the repo's review bot. */
  evidence: Evidence;
}

export type MergeVerdict =
  | { ok: true; via: "approval" | "review" | "exempt" }
  | { ok: false; reason: string };

/** The bot's current verdict on one commit. Only a completed exact-head success passes. */
type Verdict = { state: "pass" } | { state: "refused"; why: string };

/** A bot's one latest check-run on the head, from its own app, completed with success. */
function verdictOf(runs: CheckRun[], name: string, app: string): Verdict {
  const named = runs.filter((r) => r.name === name);
  if (named.length === 0) return { state: "refused", why: `no ${name} check-run exists` };
  if (named.length > 1) {
    return { state: "refused", why: `${named.length} latest ${name} check-runs exist (apps: ${named.map((r) => r.app).join(", ")}), so the verdict is ambiguous` };
  }
  const [run] = named;
  if (run.app !== app) return { state: "refused", why: `${name} comes from the ${run.app} app, not ${app}` };
  if (run.status !== "completed") return { state: "refused", why: `${name} is ${run.status}` };
  return run.conclusion === "success" ? { state: "pass" } : { state: "refused", why: `${name} concluded ${run.conclusion}` };
}

function reviewOf({ runs, comments, reviews, threads, paths }: Extract<Evidence, { bot: "coderabbit" }>, sha: string): Verdict {
  const config = paths.find((p) => CODERABBIT_CONFIG.test(p));
  if (config !== undefined) return { state: "refused", why: `the PR changes ${config}, CodeRabbit's own config, so its review cannot vouch for the PR. The owner merges this one in GitHub` };
  const command = comments.map((c) => c.match(ON_DEMAND_APPROVAL)?.[0]).find((m) => m !== undefined);
  if (command !== undefined) return { state: "refused", why: `a PR comment says \`${command}\`, which skips or closes CodeRabbit's review, so the review cannot vouch for the PR. The owner merges this one in GitHub` };
  const finished = verdictOf(runs, CODERABBIT_CHECK, CODERABBIT_APP);
  if (finished.state === "refused") return { state: "refused", why: `${finished.why}, so CodeRabbit has not finished a review of the head. Ask with \`@coderabbitai review\` and wait for its check` };
  if (!runs.some((r) => r.summary !== null && REVIEW_COMPLETED.test(r.summary))) {
    return { state: "refused", why: `the ${CODERABBIT_CHECK} check succeeded without saying "Review completed", so it may have skipped the review. Ask with \`@coderabbitai review\`` };
  }
  const open = threads.filter((t) => t.author === CODERABBIT && !t.resolved).length;
  if (open > 0) return { state: "refused", why: `${open} ${CODERABBIT} review thread${open === 1 ? " is" : "s are"} unresolved. Fix or answer each finding, then resolve its thread` };
  const outside = reviews.filter((r) => r.login === CODERABBIT).reduce((n, r) => n + Number(r.body.match(OUTSIDE_DIFF)?.[1] ?? 0), 0);
  if (outside > 0) return { state: "refused", why: `${CODERABBIT}'s reviews left ${outside} outside-diff finding${outside === 1 ? "" : "s"}, which have no thread to resolve and are not repeated by later reviews. The owner checks them and merges in GitHub` };
  return { state: "pass" };
}

export function decideMerge(head: HeadState): MergeVerdict {
  if (botExempt(head.repo)) {
    if (head.pinned) return { ok: true, via: "exempt" };
    return { ok: false, reason: `${head.repo} skips the review bot only when the merge names it. Pass -R ${head.repo} or the PR URL.` };
  }
  const verdict = head.evidence.bot === "pullfrog" ? verdictOf(head.evidence.runs, PASS_SIGNAL, PASS_APP) : reviewOf(head.evidence, head.sha);
  if (verdict.state === "pass") return { ok: true, via: head.evidence.bot === "pullfrog" ? "approval" : "review" };
  return { ok: false, reason: `On head ${head.sha.slice(0, 7)}, ${verdict.why}. A missing, running, failed, or untrusted verdict does not pass.` };
}
