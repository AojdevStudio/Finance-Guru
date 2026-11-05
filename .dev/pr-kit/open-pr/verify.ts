#!/usr/bin/env bun
/**
 * Which project verify skills a change must pass, in run order. open-pr runs them before it opens a PR, and
 * land-pr runs them before it merges.
 *
 * A skill is a tracked `.agents/skills/verify-<x>/SKILL.md` or `.claude/skills/verify-<x>/SKILL.md`.
 * It covers one app when it sits inside that app's folder, or when it sits at the repo root and exactly one
 * of `apps/<x>`, `packages/<x>`, or `services/<x>` exists. Every other skill covers the whole repo.
 * The plan lists the app skills whose app or skill folder the diff touches, then every repo-level skill.
 *
 * Usage: bun verify.ts --base <ref> [--json]. Run it in the repo, on the branch.
 */

export type Scope = { kind: "app"; root: string } | { kind: "repo" };

export interface VerifySkill {
  name: string;
  /** The skill's folder, relative to the repo root. */
  dir: string;
  scope: Scope;
}

export type VerifyPlan = { kind: "run"; skills: (VerifySkill & { touched: number })[] } | { kind: "none"; reason: string };

const APP_PARENTS = new Set(["apps", "packages", "services"]);
const SKILL = /^(?:(.+)\/)?\.(?:agents|claude)\/skills\/(verify-[^/]+)\/SKILL\.md$/;

const under = (path: string, dir: string) => path.startsWith(`${dir}/`);
const rootOf = (s: VerifySkill) => (s.scope.kind === "app" ? s.scope.root : "");

/** The verify skills in a repo, from its tracked file names. One entry per name and scope. */
export function findSkills(tracked: string[]): VerifySkill[] {
  const dirs = new Set(tracked.flatMap((f) => (f.split("/").length > 2 ? [f.split("/").slice(0, 2).join("/")] : [])));
  const found = new Map<string, VerifySkill>();
  for (const file of [...tracked].sort()) {
    const m = SKILL.exec(file);
    if (!m) continue;
    const [, prefix, name] = m;
    let scope: Scope;
    if (prefix) scope = { kind: "app", root: prefix };
    else {
      const app = name.slice("verify-".length);
      const roots = [...dirs].filter((d) => APP_PARENTS.has(d.split("/")[0]) && d.split("/")[1] === app);
      if (roots.length > 1) throw new Error(`${name} matches more than one app folder: ${roots.join(", ")}. Move the skill into its app folder.`);
      scope = roots.length === 1 ? { kind: "app", root: roots[0] } : { kind: "repo" };
    }
    const skill = { name, dir: file.slice(0, -"/SKILL.md".length), scope };
    const key = `${name} ${rootOf(skill)}`;
    if (!found.has(key)) found.set(key, skill);
  }
  return [...found.values()];
}

export function planVerify(tracked: string[], changed: string[]): VerifyPlan {
  const skills = findSkills(tracked);
  if (skills.length === 0) return { kind: "none", reason: "this repo has no project verify-* skill, so the PR flow runs as before" };
  if (changed.length === 0) return { kind: "none", reason: "the diff changes no files" };
  const touched = (s: VerifySkill) => changed.filter((f) => under(f, s.dir) || (rootOf(s) !== "" && under(f, rootOf(s)))).length;
  const apps = skills
    .filter((s) => s.scope.kind === "app")
    .map((s) => ({ ...s, touched: touched(s) }))
    .filter((s) => s.touched > 0)
    .sort((a, b) => rootOf(a).localeCompare(rootOf(b)) || a.name.localeCompare(b.name));
  const repo = skills
    .filter((s) => s.scope.kind === "repo")
    .map((s) => ({ ...s, touched: changed.length }))
    .sort((a, b) => a.name.localeCompare(b.name));
  const run = [...apps, ...repo];
  if (run.length === 0) return { kind: "none", reason: `no verify skill covers the ${changed.length} changed files: they sit outside every app that has one, and the repo has no repo-level skill` };
  return { kind: "run", skills: run };
}

function git(args: string[], cwd = "."): string[] {
  const r = Bun.spawnSync(["git", "-C", cwd, ...args], { stdout: "pipe", stderr: "pipe" });
  if (r.exitCode !== 0) throw new Error(`git ${args.join(" ")} failed: ${r.stderr.toString().trim()}`);
  return r.stdout.toString().split("\0").filter(Boolean);
}

export function render(plan: VerifyPlan): string {
  if (plan.kind === "none") return `verify: none. ${plan.reason}.`;
  const lines = plan.skills.map((s, i) => {
    const scope = s.scope.kind === "app" ? `app ${s.scope.root}` : "repo";
    return `${i + 1}. ${s.name} (${scope}, ${s.touched} changed files): ${s.dir}/SKILL.md`;
  });
  return [`verify: run ${plan.skills.length} skill${plan.skills.length === 1 ? "" : "s"} in this order, and stop at the first failure.`, ...lines].join("\n");
}

if (import.meta.main) {
  const args = process.argv.slice(2);
  const at = args.indexOf("--base");
  const base = at >= 0 ? args[at + 1] : undefined;
  if (!base || args.some((a, i) => a.startsWith("--") && !["--base", "--json"].includes(a) && i !== at + 1)) {
    console.error("usage: bun verify.ts --base <ref> [--json]");
    process.exit(2);
  }
  try {
    const top = git(["rev-parse", "--show-toplevel"])[0].replace(/\n$/, "");
    const plan = planVerify(git(["ls-files", "-z"], top), git(["diff", "-z", "--name-only", "--no-renames", `${base}...HEAD`], top));
    console.log(args.includes("--json") ? JSON.stringify(plan, null, 2) : render(plan));
  } catch (e) {
    console.error(`verify: ${(e as Error).message}`);
    process.exit(1);
  }
}
