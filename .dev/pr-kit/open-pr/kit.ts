#!/usr/bin/env bun
/**
 * Installs the PR kit into a repo, so every agent that opens the repo carries it,
 * cloud sessions included. Run it again to update; a second run changes nothing.
 *
 *   bun kit.ts install <repo> [--runs-on <label>] [--layout skills|developer]
 *   bun kit.ts stamp    rewrite VERSION after a kit change, bumping its version by one (source folder only)
 *   bun kit.ts check    exit 1 when VERSION does not match the shipped files
 *
 * VERSION holds `<version> <digest>`: an integer that gives every copy of the kit one total
 * order, and the sha256 of the shipped files it describes. It ships with the kit, and each
 * installed skill's .pr-kit marker records it as a second line, `version <N> <digest>`. An
 * install refuses, before any write, to run from a copy whose files do not match its VERSION,
 * to replace a newer installed kit or the same version with other files, or to run from a copy
 * that differs from the source repo's main when gh can read it.
 *
 * The sources sit next to this file: `open-pr` is its folder and `land-pr` is the sibling.
 * That holds in the kit's source folder, the fleet store, and an installed repo's
 * .claude/skills, so any copy can install the kit into another repo.
 *
 * Writes, inside <repo>:
 *   .claude/skills/open-pr, .claude/skills/land-pr   the skills, gate, and checker
 *   .agents/skills/{open-pr,land-pr}                  symlinks for Codex and Cursor
 *   .claude/settings.json                             the PreToolUse gate hook
 *   .github/workflows/pr-kit.yml                      the PR body check in CI
 *   AGENTS.md (and CLAUDE.md when it does not load AGENTS.md)  the rule block
 *   only the real one of AGENTS.md and CLAUDE.md when the other is a symlink whose text is exactly its name
 */

import { existsSync, lstatSync, mkdirSync, readdirSync, readFileSync, readlinkSync, rmSync, statSync, symlinkSync, writeFileSync } from "node:fs";
import { basename, join, relative, resolve } from "node:path";
import { parseArgs } from "node:util";

const SKILLS = ["open-pr", "land-pr"] as const;
const LAYOUTS = [
  { name: "skills", directory: ".claude/skills" },
  { name: "developer", directory: ".dev/pr-kit" },
] as const;
const SOURCE = { "open-pr": import.meta.dir, "land-pr": join(import.meta.dir, "..", "land-pr") } satisfies Record<(typeof SKILLS)[number], string>;
const MARKER = ".pr-kit";
const VERSION = "VERSION";
/**
 * The sha256 of the kit's source repo as lowercase `owner/name`. The kit ships to public repos
 * and names no private one, so the remote check finds the source among the owner's repos by
 * digest. The kit sits there under a folder named for the repo, at `<name>/kits/pr`.
 */
const SOURCE_OWNER = "AojdevStudio";
const SOURCE_REPO = "sha256:61:59:f3:8c:55:de:a3:14:c9:6c:15:a2:b5:dd:f2:ed:d3:2a:5b:51:01:9c:9d:0b:45:21:e2:ff:07:7c:08:15";
const STAMP_FIX = "VERSION does not match the kit's shipped files. Run bun kit.ts stamp after a kit change, and commit VERSION with it.";
const UPDATE_COPY = "Update the copy from the kit's source folder (kits/pr) with sk push or a pull. Only the source folder stamps.";
const BLOCK_START = "<!-- pr-kit:start -->";
const BLOCK_END = "<!-- pr-kit:end -->";
const ruleBlock = (directory: string) => `${BLOCK_START}
## Pull requests

- Open every PR with \`${directory}/open-pr/SKILL.md\` and land it with \`${directory}/land-pr/SKILL.md\`. Read the full skill before use.
- The PR body has five fixed sections: Problem, Change, Proof, Review, Merge danger. Merge danger names the door and the blast radius.
- The open-pr gate and the \`pr-kit\` CI check refuse a body that breaks the contract. Fix the body. Never route around either.
${BLOCK_END}`;

const shippedFiles = (dir: string) => readdirSync(dir).filter((f) => !f.startsWith(".") && !f.endsWith(".test.ts") && statSync(join(dir, f)).isFile());
const sha256 = (data: string | Uint8Array) => new Bun.CryptoHasher("sha256").update(data).digest("hex");
const fingerprint = (hex: string) => `sha256:${hex.replace(/(..)(?=.)/g, "$1:")}`;

/** The sha256 of every shipped file but VERSION, as sorted `<skill>/<file>\n<file sha256>\n` lines. */
function kitDigest(): string {
  const files = SKILLS.flatMap((name) => shippedFiles(SOURCE[name]).filter((f) => f !== VERSION).map((f) => `${name}/${f}`)).sort();
  return fingerprint(sha256(files.map((rel) => `${rel}\n${sha256(readFileSync(join(SOURCE["open-pr"], "..", rel)))}\n`).join("")));
}

interface Stamp {
  version: number;
  digest: string;
}

const DIGEST_PATTERN = "(?:[0-9a-f]{64}|sha256:(?:[0-9a-f]{2}:){31}[0-9a-f]{2})";
const STAMP_LINE = new RegExp(`^(\\d+) (${DIGEST_PATTERN})$`);

function parseStamp(text: string): Stamp | undefined {
  const m = STAMP_LINE.exec(text.replace(/\n$/, ""));
  const version = Number(m?.[1]);
  return m && Number.isSafeInteger(version) ? { version, digest: m[2].startsWith("sha256:") ? m[2] : fingerprint(m[2]) } : undefined;
}

const versionPath = join(SOURCE["open-pr"], VERSION);
const ownStamp = () => (existsSync(versionPath) ? parseStamp(readFileSync(versionPath, "utf8")) : undefined);

/**
 * Whether this copy is the kit's source folder, `<repo>/kits/pr/open-pr` in a git checkout.
 * A stamp in any other copy would bless files that never came from the source, so an install
 * from it could downgrade a repo.
 */
function inSourceFolder(): boolean {
  const dir = SOURCE["open-pr"];
  if (basename(join(dir, "..")) !== "pr" || basename(join(dir, "..", "..")) !== "kits" || existsSync(join(dir, MARKER))) return false;
  return Bun.spawnSync(["git", "rev-parse", "--show-toplevel"], { cwd: dir, stdout: "ignore", stderr: "ignore" }).exitCode === 0;
}

const USAGE = "usage: bun kit.ts install <repo> [--runs-on <label>] [--layout skills|developer] | stamp | check";
const { values, positionals } = parseArgs({ allowPositionals: true, options: { "runs-on": { type: "string" }, layout: { type: "string" }, help: { type: "boolean", short: "h" } } });
if (values.help) {
  console.log(USAGE);
  process.exit(0);
}
const [verb, target] = positionals;
if (verb === "stamp") {
  if (!inSourceFolder()) throw new Error("stamp runs only in the kit's source folder (<repo>/kits/pr/open-pr). This copy is installed or synced; update it instead.");
  const text = existsSync(versionPath) ? readFileSync(versionPath, "utf8") : undefined;
  const own = text === undefined ? undefined : parseStamp(text);
  if (text !== undefined && !own) {
    const lines = text.replace(/\n$/, "").split("\n");
    const at = lines.findIndex((line, i) => i > 0 || !parseStamp(line));
    throw new Error(`${versionPath} line ${at + 1} does not read as "<version> <digest>": ${JSON.stringify(lines[at])}. Fix it by hand. stamp starts at 1 only when VERSION is missing.`);
  }
  const digest = kitDigest();
  if (own?.digest === digest) {
    console.log(`VERSION is current at version ${own.version}.`);
  } else {
    const version = (own?.version ?? 0) + 1;
    writeFileSync(versionPath, `${version} ${digest}\n`);
    console.log(`Stamped version ${version}.`);
  }
  process.exit(0);
}
if (verb === "check") {
  const own = ownStamp();
  if (own?.digest !== kitDigest()) {
    console.error(STAMP_FIX);
    process.exit(1);
  }
  console.log(`VERSION ${own.version} matches the shipped files.`);
  process.exit(0);
}
if (verb !== "install" || !target) {
  console.error(USAGE);
  process.exit(1);
}
const repo = resolve(target);
if (!existsSync(join(repo, ".git"))) throw new Error(`${repo} is not a git checkout`);
const requestedLayout = LAYOUTS.find((layout) => layout.name === values.layout);
if (values.layout !== undefined && !requestedLayout) throw new Error("--layout must be skills or developer");
const installedLayouts = () => LAYOUTS.filter(({ directory }) => SKILLS.some((name) => existsSync(join(repo, directory, name, MARKER))));
const installed = installedLayouts();
if (installed.length > 1) throw new Error("PR kit markers exist in both layouts. Resolve the duplicate install before updating.");
if (requestedLayout && installed[0] && requestedLayout !== installed[0]) throw new Error("Changing PR kit layout requires removing the old install and its hook and discovery links first.");
const layout = requestedLayout ?? installed[0] ?? LAYOUTS[0];
const HOOK = `bun "$CLAUDE_PROJECT_DIR/${layout.directory}/open-pr/gate.ts"`;
const BLOCK = ruleBlock(layout.directory);

const MARKER_HEADER = "Installed by the PR kit (open-pr/kit.ts). Edit the kit at its source, not here.";
const MARKER_LINE = new RegExp(`^version (\\d+) (${DIGEST_PATTERN})\\r?$`);

/**
 * Both skills' installed markers: the version and digest each records. A marker with only its
 * header line predates the version line and counts as version 0. Any other line, or more than
 * one version line, refuses, since reading it as 0 would let an older copy overwrite a newer install.
 */
function installedMarkers(): { marker: string; version: number; digest?: string }[] {
  return SKILLS.flatMap((name) => {
    const marker = join(repo, layout.directory, name, MARKER);
    if (!existsSync(marker)) return [];
    const rest = readFileSync(marker, "utf8").replace(/\n$/, "").split("\n").filter((line) => line.replace(/\r$/, "") !== MARKER_HEADER);
    if (rest.length === 0) return [{ marker, version: 0 }];
    const m = rest.length === 1 ? MARKER_LINE.exec(rest[0]) : null;
    const version = Number(m?.[1]);
    if (!m || !Number.isSafeInteger(version)) {
      throw new Error(`${marker} does not read as "version <version> <digest>": ${JSON.stringify(rest.join("\n"))}. Delete the marker's damaged lines, or the whole marker if you cannot tell which install wrote it, then rerun.`);
    }
    return [{ marker, version, digest: m[2].startsWith("sha256:") ? m[2] : fingerprint(m[2]) }];
  });
}

const own = ownStamp();
if (own?.digest !== kitDigest()) throw new Error(`this kit copy cannot install. Its files do not match its VERSION, so they changed after it was stamped. ${UPDATE_COPY}`);
const markerText = `${MARKER_HEADER}\nversion ${own.version} ${own.digest}\n`;

/** Refuses when the repo's installed kit is newer than this copy, or the same version with other files. */
const guardInstalled = () => {
  if (installedLayouts().some((other) => other !== layout)) throw new Error("PR kit markers exist in both layouts. Resolve the duplicate install before updating.");
  for (const { marker, version, digest } of installedMarkers()) {
    const where = `The installed version is recorded in ${marker}.`;
    if (version > own.version) {
      throw new Error(`this kit copy is version ${own.version} but ${repo} already has version ${version}. ${where} Install from the kit's source folder (kits/pr), or a copy at least that new.`);
    }
    if (version === own.version && digest !== undefined && digest !== own.digest) {
      throw new Error(`${repo} already has version ${version} with other files; this copy is not that kit. ${where}`);
    }
  }
};

const GH_TIMEOUT_MS = Number(process.env.PR_KIT_GH_TIMEOUT_MS) || 15_000;

function gh(args: string[]): { out: string } | { why: string } {
  const r = Bun.spawnSync(["gh", ...args], { stdout: "pipe", stderr: "pipe", timeout: GH_TIMEOUT_MS });
  if (r.exitCode === 0) return { out: r.stdout.toString() };
  if (r.exitedDueToTimeout) return { why: `gh did not answer within ${GH_TIMEOUT_MS} ms` };
  return { why: r.stderr.toString().trim().split("\n")[0] || `gh exited ${r.exitCode ?? r.signalCode}` };
}

/** The source repo's VERSION on main, or why gh could not read it. */
function sourceStamp(): { repo: string; stamp: Stamp } | { why: string } {
  if (!Bun.which("gh")) return { why: "gh is not on PATH" };
  const list = gh(["repo", "list", SOURCE_OWNER, "--limit", "1000", "--json", "nameWithOwner", "--jq", ".[].nameWithOwner"]);
  if ("why" in list) return list;
  const source = list.out.split("\n").find((r) => fingerprint(sha256(r.toLowerCase())) === SOURCE_REPO);
  if (!source) return { why: "gh cannot see the kit's source repo" };
  const answer = gh(["api", "-H", "Accept: application/vnd.github.raw", `repos/${source}/contents/${source.split("/")[1]}/kits/pr/open-pr/${VERSION}?ref=main`]);
  if ("why" in answer) return answer;
  const stamp = parseStamp(answer.out);
  return stamp ? { repo: source, stamp } : { why: "its answer is not a VERSION line" };
}

const changes: string[] = [];
const note = (what: string) => changes.push(what);

function writeIfChanged(path: string, text: string): void {
  if (existsSync(path) && readFileSync(path, "utf8") === text) return;
  mkdirSync(join(path, ".."), { recursive: true });
  writeFileSync(path, text);
  note(`wrote ${relative(repo, path)}`);
}

function copySkill(name: (typeof SKILLS)[number]): void {
  const dest = join(repo, layout.directory, name);
  if (existsSync(dest) && !existsSync(join(dest, MARKER))) {
    throw new Error(`${relative(repo, dest)} exists and is not the PR kit. Move it, then rerun.`);
  }
  const src = SOURCE[name];
  if (!existsSync(join(src, "SKILL.md"))) throw new Error(`${src} is not the ${name} skill. Run kit.ts from a full copy of the kit.`);
  const shipped = shippedFiles(src);
  for (const file of shipped) writeIfChanged(join(dest, file), readFileSync(join(src, file), "utf8"));
  for (const file of existsSync(dest) ? readdirSync(dest) : []) {
    if (file === MARKER || shipped.includes(file)) continue;
    rmSync(join(dest, file), { recursive: true });
    note(`removed ${relative(repo, join(dest, file))}`);
  }
  writeIfChanged(join(dest, MARKER), markerText);
}

function linkSkill(name: string): void {
  const link = join(repo, ".agents", "skills", name);
  const to = join("..", "..", ".claude", "skills", name);
  if (existsSync(link) || lstatSync(link, { throwIfNoEntry: false })) {
    if (lstatSync(link).isSymbolicLink() && readlinkSync(link) === to) return;
    console.warn(`skip ${relative(repo, link)}: it exists and is not the kit link`);
    return;
  }
  mkdirSync(join(link, ".."), { recursive: true });
  symlinkSync(to, link);
  note(`linked ${relative(repo, link)}`);
}

const isObj = (x: unknown): x is Record<string, unknown> => typeof x === "object" && x !== null && !Array.isArray(x);

/**
 * The gate hook's settings. 120 seconds covers a merge check's chain of `gh` calls (8 seconds
 * each). `onFailure: "block"` makes a gate that times out, fails to start, or crashes deny
 * the call, since Claude Code otherwise lets it run.
 */
const HOOK_SETTINGS = { timeout: 120, onFailure: "block" } as const;

/** Wires the gate hook, and brings an entry from an earlier install up to HOOK_SETTINGS. */
function wireHook(): void {
  const path = join(repo, ".claude", "settings.json");
  const settings: unknown = existsSync(path) ? JSON.parse(readFileSync(path, "utf8")) : {};
  if (!isObj(settings)) throw new Error(`${relative(repo, path)} is not a JSON object`);
  const hooks = isObj(settings.hooks) ? settings.hooks : {};
  const pre: unknown[] = Array.isArray(hooks.PreToolUse) ? hooks.PreToolUse : [];
  const ours = pre.flatMap((m) => (isObj(m) && Array.isArray(m.hooks) ? m.hooks.filter((h): h is Record<string, unknown> => isObj(h) && h.command === HOOK) : []));
  const stale = ours.filter((h) => Object.entries(HOOK_SETTINGS).some(([k, v]) => h[k] !== v));
  if (ours.length > 0 && stale.length === 0) return;
  for (const h of stale) Object.assign(h, HOOK_SETTINGS);
  if (ours.length === 0) pre.push({ matcher: "Bash", hooks: [{ type: "command", command: HOOK, ...HOOK_SETTINGS }] });
  hooks.PreToolUse = pre;
  settings.hooks = hooks;
  writeIfChanged(path, JSON.stringify(settings, null, 2) + "\n");
}

const RUNS_ON = /^\s*runs-on:\s*(\S.*?)\s*$/gm;

/**
 * The runner label: the flag, else the label the installed pr-kit.yml already uses, else the
 * one label most of the repo's other workflows use. Inference never picks a paid hosted
 * label, and a tie for most used is refused, so the result never depends on file order.
 */
function runnerLabel(): string {
  if (values["runs-on"]) return values["runs-on"];
  const dir = join(repo, ".github", "workflows");
  const installed = join(dir, "pr-kit.yml");
  if (existsSync(installed)) {
    const label = [...readFileSync(installed, "utf8").matchAll(RUNS_ON)][0]?.[1];
    if (!label) throw new Error(`${relative(repo, installed)} has no single-line runs-on label. Pass --runs-on <label>.`);
    return label;
  }
  const counts = new Map<string, number>();
  for (const f of existsSync(dir) ? readdirSync(dir) : []) {
    for (const m of readFileSync(join(dir, f), "utf8").matchAll(RUNS_ON)) counts.set(m[1], (counts.get(m[1]) ?? 0) + 1);
  }
  const top = Math.max(0, ...counts.values());
  const best = [...counts].filter(([, n]) => n === top).map(([label]) => label).sort();
  if (best.length !== 1 || /^(ubuntu|macos|windows)-|\$\{\{/.test(best[0])) {
    throw new Error(`no single self-hosted runner label found (most used: ${best.join(", ") || "none"}). Pass --runs-on <label>. Never default to paid hosted minutes.`);
  }
  return best[0];
}

function writeWorkflow(label: string): void {
  const yml = readFileSync(join(SOURCE["open-pr"], "pr-kit.yml"), "utf8").replace("__RUNS_ON__", label).replaceAll(".claude/skills/", `${layout.directory}/`);
  writeIfChanged(join(repo, ".github", "workflows", "pr-kit.yml"), yml);
}

type InstructionWrite = { path: string; text: string };

function replaceRuleBlock(text: string, path: string): string {
  const starts = text.split(BLOCK_START).length - 1;
  const ends = text.split(BLOCK_END).length - 1;
  const at = text.indexOf(BLOCK_START);
  const end = text.indexOf(BLOCK_END);
  if (starts === 0 && ends === 0) return `${text}${text ? "\n\n" : ""}${BLOCK}\n`;
  if (starts !== 1 || ends !== 1 || end < at) {
    throw new Error(`${path} has invalid PR kit instruction markers. Expected none or one ordered pair, found ${starts} start and ${ends} end markers.`);
  }
  return text.slice(0, at) + BLOCK + text.slice(end + BLOCK_END.length);
}

function assertDestination(path: string, directory = false): void {
  const info = lstatSync(path, { throwIfNoEntry: false });
  if (info?.isSymbolicLink()) throw new Error(`${path} is a symlink. Install into real directories and files.`);
  if (info && (directory ? !info.isDirectory() : !info.isFile())) throw new Error(`${path} has the wrong file type for this install.`);
  if (path !== repo) assertDestination(join(path, ".."), true);
}

/**
 * The repo's only instruction file when one root instruction file is a symlink whose text is
 * exactly the other's name, the one link the kit accepts. The named file must be a real file.
 */
function instructionAlias(): "AGENTS.md" | "CLAUDE.md" | undefined {
  for (const [link, target] of [["AGENTS.md", "CLAUDE.md"], ["CLAUDE.md", "AGENTS.md"]] as const) {
    const linkPath = join(repo, link);
    if (!lstatSync(linkPath, { throwIfNoEntry: false })?.isSymbolicLink() || readlinkSync(linkPath) !== target) continue;
    const targetPath = join(repo, target);
    if (!lstatSync(targetPath, { throwIfNoEntry: false })?.isFile()) throw new Error(`${linkPath} links to ${targetPath}, which is not a real file. Point ${link} at a real ${target}, then rerun.`);
    return target;
  }
  return undefined;
}

function preflightDestinations(): InstructionWrite[] {
  for (const name of SKILLS) {
    const dest = join(repo, layout.directory, name);
    assertDestination(dest, true);
    if (existsSync(dest) && !existsSync(join(dest, MARKER))) throw new Error(`${relative(repo, dest)} exists and is not the PR kit. Move it, then rerun.`);
    for (const file of [...shippedFiles(SOURCE[name]), MARKER]) assertDestination(join(dest, file));
  }
  const alias = instructionAlias();
  const instructionFiles = alias ? [alias] : ["AGENTS.md", "CLAUDE.md"];
  for (const file of [".claude/settings.json", ".github/workflows/pr-kit.yml", ...instructionFiles]) assertDestination(join(repo, file));
  if (layout.name === "skills") assertDestination(join(repo, ".agents", "skills"), true);
  return instructionFiles.flatMap((file) => {
    const path = join(repo, file);
    if (file === "CLAUDE.md" && !existsSync(path)) return [];
    const text = existsSync(path) ? readFileSync(path, "utf8") : "";
    const next = replaceRuleBlock(text, path);
    return file === "CLAUDE.md" && !alias && text.includes("AGENTS.md") ? [] : [{ path, text: next }];
  });
}

const label = runnerLabel();
preflightDestinations();
guardInstalled();
const remote = sourceStamp();
if ("why" in remote) console.log(`Remote version check skipped (this install was not compared with kits/pr): ${remote.why}.`);
else if (remote.stamp.version > own.version) {
  throw new Error(`this kit copy is version ${own.version} but ${remote.repo} kits/pr is at ${remote.stamp.version}. Update the copy first.`);
} else if (remote.stamp.version === own.version && remote.stamp.digest !== own.digest) {
  throw new Error(`this copy claims version ${own.version} but its files differ from kits/pr at ${own.version} in ${remote.repo}. Update the copy first.`);
} else if (remote.stamp.version < own.version) {
  // A stale branch of the source repo can stamp past main. Installing it would lock main out.
  throw new Error(`this kit copy is version ${own.version} but ${remote.repo} kits/pr on main is at ${remote.stamp.version}. Install from kits/pr after the change merges to main.`);
}
// The remote lookup can take seconds, so read the markers again: another install may have landed.
const instructions = preflightDestinations();
guardInstalled();
for (const name of SKILLS) copySkill(name);
if (layout.name === "skills") for (const name of SKILLS) linkSkill(name);
wireHook();
writeWorkflow(label);
for (const { path, text } of instructions) writeIfChanged(path, text);

console.log(changes.length ? changes.map((c) => `- ${c}`).join("\n") : "PR kit already current.");
console.log("Next: commit these files in their own PR, then make the pr-kit check required in the repo ruleset.");
