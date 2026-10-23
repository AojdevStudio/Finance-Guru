#!/usr/bin/env bun
/**
 * PreToolUse (Bash) hook: every PR create, edit, and merge goes through the PR kit.
 *
 * - create and edit: the body must pass the contract in contract.ts.
 * - merge: the PR body must pass, and the review bot must have passed the exact head
 *   (land-pr/merge.ts).
 *
 * - graphql: a PR create, update, or merge through `gh api graphql` is refused, and so
 *   is any GraphQL call whose query this gate cannot read.
 *
 * Two installs run this same file. A repo carries it at .claude/skills/open-pr/gate.ts,
 * wired in the repo's .claude/settings.json, so cloud sessions get it. The MacBook also
 * wires the kit's source copy globally. The global copy never
 * stands down: in a repo with its own copy both run, and both check the same contract,
 * so a repo cannot swap in a weaker gate.
 *
 * Exit 0 allows, exit 2 denies with the reason on stderr. A PR write that cannot be
 * checked is denied, never passed. Claude Code lets the tool call run when a hook times
 * out, fails to start, or exits with another code, so kit.ts wires the hook with
 * `onFailure: "block"`. PR_KIT_OFF=1 is the owner's switch, never an agent's.
 */

import { existsSync, lstatSync, readFileSync, realpathSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, resolve } from "node:path";
import { checkPullRequest, formatViolations, titleViolation, type PullRequest } from "./contract";
import { atSource, findPrCommands, graphqlRisk, type BodySource, type FieldValue, type HeadMatch, type PrCommand } from "./command";
import { botExempt, decideMerge, PASS_SIGNAL, verdictOf, type CheckRun } from "../land-pr/merge";

interface HookInput {
  tool: string;
  command: string;
  cwd: string;
}

function parseInput(raw: string): HookInput {
  const x: unknown = raw.trim() ? JSON.parse(raw) : {};
  const obj = isObj(x) ? x : {};
  const toolInput = isObj(obj.tool_input) ? obj.tool_input : {};
  return {
    tool: isStr(obj.tool_name) ? obj.tool_name : "",
    command: isStr(toolInput.command) ? toolInput.command : "",
    cwd: isStr(obj.cwd) ? obj.cwd : process.cwd(),
  };
}

class Refusal extends Error {}

function run(argv: string[], cwd: string): string {
  const r = Bun.spawnSync(argv, { cwd, stdout: "pipe", stderr: "pipe", timeout: 8_000 });
  if (r.exitCode !== 0) throw new Refusal(`\`${argv.join(" ")}\` failed: ${(r.stderr.toString() || r.stdout.toString()).trim()}`);
  return r.stdout.toString().trim();
}

const ghJson = (path: string, cwd: string): unknown => JSON.parse(run(["gh", "api", path], cwd));

type Json = Record<string, unknown>;
const isObj = (x: unknown): x is Json => typeof x === "object" && x !== null && !Array.isArray(x);

function field<T>(obj: unknown, key: string, guard: (v: unknown) => v is T, what: string): T {
  const v = isObj(obj) ? obj[key] : undefined;
  if (!guard(v)) throw new Refusal(`GitHub returned ${what} without a valid "${key}".`);
  return v;
}
const isStr = (v: unknown): v is string => typeof v === "string";
const isNum = (v: unknown): v is number => typeof v === "number";
const isBool = (v: unknown): v is boolean => typeof v === "boolean";
const isArr = (v: unknown): v is unknown[] => Array.isArray(v);
const isStrOrNull = (v: unknown): v is string | null => v === null || typeof v === "string";

/** A directory as bash's cd enters it: `..` is taken by spelling, as cd does by default. */
function expand(path: string, cwd: string): string {
  return resolve(cwd, path.replace(/^~(?=\/|$)/, homedir()));
}

/** A file as the OS opens it: joined, never collapsed, so `..` after a symlink leaves the symlink's target. */
function open(path: string, cwd: string): string {
  const full = path.replace(/^~(?=\/|$)/, homedir());
  return full.startsWith("/") ? full : `${cwd}/${full}`;
}

const ALONE =
  "the PR command does not run on its own. Run it as the only command in this call, after at most a literal cd, a set -euxo pipefail, and one cat > <file> <<'EOF' that writes its body file and that && joins to it, and gh reads no other file. Before gh, assign no HOME, GH_REPO, GH_HOST, GH_CONFIG_DIR, XDG_CONFIG_HOME, or CDPATH. You may pipe its output into a read-only filter such as tail or jq.";
const LOST = "the command changes directory in a way this gate cannot follow (pushd, popd, source, eval, a cd after a prefix word or inside braces, or a cd that CDPATH can redirect), so a relative path can name another file. Use an absolute path, or cd to a literal path that starts with / or ./.";
const DRIFT = {
  repo: "gh takes this merge's repo or PR from the current directory, and a word before gh or a directory change this gate cannot follow can make that differ from what this gate checks. Name the PR with its number and -R owner/name, or its github.com URL.",
  host: "the command can change the host or config gh uses (GH_HOST, GH_CONFIG_DIR, XDG_CONFIG_HOME, HOME, or a variable it computes), so gh can merge somewhere this gate does not check. Leave them unset in a merge command, or name the PR by its github.com URL.",
};
const NO_BODY = "the command sets no body. Write the body with the open-pr skill and pass it with --body-file.";
const EXPANDED = "the command holds `$`, a backquote, `~`, or an escape that a shell expands after this gate reads it, so the gate cannot see what gh gets. Write the text as gh should get it: quote a heredoc delimiter (<<'EOF'), and put an ssh or bash -c command in single quotes.";
const OPAQUE: Record<"control" | "field" | "program" | "shell", string> = {
  field: "a -f or -F field name comes from the shell, so this gate cannot tell which PR fields the request sets. Write each field name as text.",
  control: "the shell computes the method or a flag of this PR write, or can split an unquoted `$...` into more flags, so this gate cannot tell whether it writes a PR or what it sends. Write the method and every flag as text, and double-quote each `$...`.",
  program: "a shell reads its program from an unquoted heredoc, a here-string, a -c script, an ssh command, or echo or printf output that the outer shell expands first, a descriptor copy such as <&3, or a file through < or <>, which can be a path to a heredoc, a pipe, or a descriptor, so this gate cannot see the PR write it runs. Quote the heredoc delimiter (<<'EOF') and give it to the shell directly, or run the PR command on its own.",
  shell: "this gate cannot read the options of the shell this command runs: fish, csh, tcsh, mksh, yash, or posh given an option or stdin, a shell given an option word the shell computes, such as \"$opts\", or a command name the shell computes, which can be a shell. So it cannot see the PR write that shell runs. Run the PR command in bash with every option written as text, or on its own.",
};

/**
 * Whether cat writing `path` leaves gh a plain file: one already there, or a new name cat creates. Under /dev and /proc a
 * name such as /dev/fd/3 can exist for the shell's process alone, so a missing one there is not a new file.
 */
function plainFile(path: string): boolean {
  try {
    const stat = lstatSync(path, { throwIfNoEntry: false });
    return stat === undefined ? !/^\/(?:dev|proc)(?:\/|$)/.test(realpathSync(dirname(path))) : stat.isFile();
  } catch {
    return false;
  }
}

function readBody(source: BodySource, cmd: PrCommand, cwd: string): string {
  if (source.kind === "inline" && source.expands) throw new Refusal(EXPANDED);
  if (source.kind === "inline" && source.written !== undefined) {
    if (cmd.host) throw new Refusal(`the body heredoc writes a file on ${cmd.host}, so this gate cannot tell whether it is a plain file. Pass the body inline with a heredoc.`);
    if (!plainFile(source.written)) throw new Refusal(`${source.written} is not a plain file, so this gate cannot know what cat writes into it. Write the body to a new plain file.`);
  }
  if (source.kind === "inline") return source.text;
  if (source.kind === "missing") throw new Refusal(NO_BODY);
  if (cmd.host) throw new Refusal(`the body file ${source.path} is on ${cmd.host}, so this gate cannot read it. Pass the body inline with a heredoc.`);
  if (cmd.lost && !/^[/~]/.test(source.path)) throw new Refusal(LOST);
  const file = open(source.path, cwd);
  if (!existsSync(file)) throw new Refusal(`the body file ${file} does not exist yet. Write it in an earlier command.`);
  const text = readFileSync(file, "utf8");
  return source.chomp ? text.replace(/\n+$/, "") : text;
}

/** The PR fields a create or edit sets. An absent field is undefined, and on an edit it keeps the PR's value. */
interface PrFields {
  title?: string;
  draft?: boolean;
  body?: string;
}

/** The fields an `--input` JSON request sets. */
function readRequest(cmd: Extract<PrCommand, { kind: "input" }>, cwd: string): PrFields {
  if (cmd.request.kind === "missing") throw new Refusal("this gate cannot read the --input request. Pass it in a heredoc or a file.");
  const text = readBody(cmd.request, cmd, cwd);
  let json: unknown;
  try {
    json = JSON.parse(text);
  } catch {
    throw new Refusal("the --input request is not valid JSON, so this gate cannot read the PR fields it sets.");
  }
  if (!isObj(json)) throw new Refusal("the --input request is not a JSON object, so this gate cannot read the PR fields it sets.");
  const keys = topLevelKeys(text);
  const twice = ["title", "draft", "body"].find((k) => keys.indexOf(k) !== keys.lastIndexOf(k));
  if (twice) throw new Refusal(`the --input request sets "${twice}" twice, so this gate and GitHub could each keep a different one.`);
  return typedFields(json);
}

/** The JSON gh sends for one `-f` or `-F` field. */
function fieldJson({ source, typed, at }: FieldValue, cmd: PrCommand, cwd: string): unknown {
  const text = readBody(source, cmd, cwd);
  // gh reads `@path` in the text a file gave, and sends that file's text as a string.
  if (at && text.startsWith("@")) return readBody(atSource(text.slice(1), at), cmd, cwd);
  return typed ? ghTyped(text) : text;
}

/** The JSON the `-f`/`-F` flags of a REST write send, read into the same fields as an `--input` request. */
function readFields(cmd: Extract<PrCommand, { kind: "fields" }>, cwd: string): PrFields {
  const json: Json = {};
  for (const [key, value] of Object.entries(cmd.fields)) json[key] = fieldJson(value, cmd, cwd);
  return typedFields(json);
}

/** The JSON gh 2.101 sends for a `-F` value: an integer, true, false, or null, and any other text as a string. */
function ghTyped(text: string): unknown {
  if (/^[+-]?\d+$/.test(text)) return Number(text);
  if (text === "true" || text === "false") return text === "true";
  return text === "null" ? null : text;
}

/** The PR fields a REST request sets. A null body is an empty one. Any other wrong type is refused. */
function typedFields(json: Json): PrFields {
  const body = optional(json, "body", isStrOrNull);
  return { title: optional(json, "title", isStr), draft: optional(json, "draft", isBool), body: body === null ? "" : body };
}

/** The keys of a valid JSON object's outermost level, in order, repeats kept. JSON.parse keeps only the last. */
function topLevelKeys(text: string): string[] {
  const keys: string[] = [];
  let depth = 0;
  for (let i = 0; i < text.length; i++) {
    if (text[i] === '"') {
      let end = i + 1;
      while (text[end] !== '"') end += text[end] === "\\" ? 2 : 1;
      const key: unknown = depth === 1 && /^\s*:/.test(text.slice(end + 1)) ? JSON.parse(text.slice(i, end + 1)) : null;
      if (isStr(key)) keys.push(key);
      i = end;
    } else if (text[i] === "{" || text[i] === "[") depth++;
    else if (text[i] === "}" || text[i] === "]") depth--;
  }
  return keys;
}

function optional<T>(obj: Json, key: string, guard: (v: unknown) => v is T): T | undefined {
  if (!Object.hasOwn(obj, key)) return undefined;
  if (!guard(obj[key])) throw new Refusal(`the request sets "${key}" to ${JSON.stringify(obj[key])}, which GitHub does not take as a PR ${key}.`);
  return obj[key];
}

function contract(pr: PullRequest): void {
  const verdict = checkPullRequest(pr);
  if (!verdict.ok) throw new Refusal(`the PR body breaks the contract:\n${formatViolations(verdict.violations)}`);
}

function checkFields(write: "create" | "edit", fields: PrFields): void {
  if (write === "create") {
    if (fields.body === undefined) throw new Refusal(NO_BODY);
    return contract({ title: fields.title, draft: fields.draft, body: fields.body });
  }
  if (fields.body !== undefined) return contract({ title: fields.title, body: fields.body });
  const title = fields.title === undefined ? null : titleViolation(fields.title);
  if (title) throw new Refusal(`the PR title breaks the contract:\n${formatViolations([title])}`);
}

interface RestPull {
  number: number;
  title: string;
  body: string | null;
  draft: boolean;
  headSha: string;
  baseSha: string;
  baseRepo: string;
}

function parsePull(x: unknown): RestPull {
  return {
    number: field(x, "number", isNum, "a PR"),
    title: field(x, "title", isStr, "a PR"),
    body: field(x, "body", isStrOrNull, "a PR"),
    draft: field(x, "draft", isBool, "a PR"),
    headSha: field(field(x, "head", isObj, "a PR"), "sha", isStr, "a PR head"),
    baseSha: field(field(x, "base", isObj, "a PR"), "sha", isStr, "a PR base"),
    baseRepo: field(field(field(x, "base", isObj, "a PR"), "repo", isObj, "a PR base"), "full_name", isStr, "a PR base repo"),
  };
}

function parseRun(x: unknown): CheckRun {
  return {
    name: field(x, "name", isStr, "a check-run"),
    status: field(x, "status", isStr, "a check-run"),
    conclusion: field(x, "conclusion", isStrOrNull, "a check-run"),
    app: field(field(x, "app", isObj, "a check-run"), "slug", isStr, "a check-run app"),
  };
}

function resolvePull(cmd: Extract<PrCommand, { kind: "merge" }>, cwd: string): { repo: string; pull: RestPull } {
  const url = cmd.target?.match(/github\.com\/([^/]+\/[^/]+)\/pull\/(\d+)/);
  let repo = url?.[1] ?? cmd.repo;
  if (!repo) {
    if (cmd.host) throw new Refusal(`a merge over ssh on ${cmd.host} must name the repo with --repo owner/name, so the gate can check it.`);
    repo = run(["gh", "api", "repos/{owner}/{repo}", "--jq", ".full_name"], cwd);
  }
  const number = url?.[2] ?? (cmd.target && /^#?\d+$/.test(cmd.target) ? cmd.target.replace("#", "") : undefined);
  if (number) return { repo, pull: parsePull(ghJson(`repos/${repo}/pulls/${number}`, cwd)) };
  if (cmd.host && !cmd.target) throw new Refusal(`a merge over ssh on ${cmd.host} must name the PR number.`);
  const branch = cmd.target ?? run(["git", "branch", "--show-current"], cwd);
  const owner = repo.split("/")[0];
  const open = ghJson(`repos/${repo}/pulls?state=open&head=${owner}:${encodeURIComponent(branch)}`, cwd);
  if (!isArr(open) || open.length === 0) throw new Refusal(`no open PR in ${repo} has head branch ${branch}.`);
  return { repo, pull: parsePull(open[0]) };
}

function latestRuns(repo: string, sha: string, cwd: string): CheckRun[] {
  const page = ghJson(`repos/${repo}/commits/${sha}/check-runs?check_name=${PASS_SIGNAL}&filter=latest`, cwd);
  return field(page, "check_runs", isArr, "a check-run list").map(parseRun);
}

const UNREADABLE = "this gate cannot read the GraphQL query, so it cannot prove the call neither writes nor merges a PR. Pass the query as a literal with values as GraphQL variables (`-F name=value`), or use `gh pr` or the REST pulls endpoint.";

/** The GraphQL text of a `graphql` command, read as gh sends the query field or `--input` file, or null when this gate cannot read it. */
function graphqlText(cmd: Extract<PrCommand, { kind: "graphql" }>, cwd: string): string | null {
  let raw: unknown;
  try {
    raw = fieldJson(cmd.query, cmd, cwd);
  } catch (err) {
    if (err instanceof Refusal) return null;
    throw err;
  }
  if (!isStr(raw)) return null;
  if (!cmd.json) return raw;
  try {
    const json: unknown = JSON.parse(raw);
    return isObj(json) && isStr(json.query) ? json.query : null;
  } catch {
    return null;
  }
}

function checkGraphql(cmd: Extract<PrCommand, { kind: "graphql" }>, cwd: string): void {
  const text = graphqlText(cmd, cwd);
  // A JSON request can carry its own operationName, and an unquoted heredoc expands `$`.
  const risk = text === null ? "opaque" : graphqlRisk(text, cmd.operationName || cmd.json);
  if (risk === "merge") throw new Refusal("a GraphQL merge skips the policy check. Merge with `gh pr merge <n>` or the REST merge endpoint.");
  if (risk === "write") throw new Refusal("a GraphQL createPullRequest or updatePullRequest skips the body contract. Use `gh pr create` or `gh pr edit`, or the REST pulls endpoint (`gh api repos/{owner}/{repo}/pulls`).");
  if (risk === "opaque") throw new Refusal(UNREADABLE);
}

/** The host the gate's own gh calls reach when they name none. */
const DEFAULT_HOST = (process.env.GH_HOST || "github.com").toLowerCase();

/** The head commit a merge requires, as gh or GitHub reads it, or undefined when a REST request names none. */
function namedHead({ value, json }: HeadMatch, cmd: PrCommand, cwd: string): string | undefined {
  const raw = fieldJson(value, cmd, cwd);
  if (!json) return String(raw);
  let request: unknown;
  try {
    request = JSON.parse(String(raw));
  } catch {
    throw new Refusal("the merge's --input request is not valid JSON, so this gate cannot read the head it names.");
  }
  return isObj(request) ? optional(request, "sha", isStr) : undefined;
}

function checkMerge(cmd: Extract<PrCommand, { kind: "merge" }>, cwd: string): void {
  const host = cmd.hosts.find((h) => h.toLowerCase().replace(/^api\.(?=github\.com$)/, "") !== DEFAULT_HOST);
  if (host !== undefined) {
    throw new Refusal(`the merge names the GitHub host ${host}, but this gate reads PRs and review verdicts on ${DEFAULT_HOST} only, so it cannot check this merge. Name no host, or merge on ${DEFAULT_HOST}.`);
  }
  const { repo, pull } = resolvePull(cmd, cwd);
  contract({ title: pull.title, body: pull.body ?? "", draft: pull.draft });
  const sha = pull.headSha;
  const named = cmd.match && namedHead(cmd.match, cmd, cwd);
  if (named !== undefined && named.toLowerCase() !== sha.toLowerCase()) {
    throw new Refusal(`the merge names head ${named}, but the gate checked ${sha}, so it cannot vouch for the head gh would merge. Name the head the gate checked, or drop the head check.`);
  }
  if (botExempt(pull.baseRepo) && cmd.pinned) return;
  const commit = ghJson(`repos/${repo}/commits/${sha}`, cwd);
  const parents = field(commit, "parents", isArr, "a commit").map((p) => field(p, "sha", isStr, "a commit parent"));
  const runs = latestRuns(repo, sha, cwd);
  // Only a merge commit whose own verdict is missing or running can inherit, so only it needs the parent's.
  const mergeCommit = parents.length === 2 && verdictOf(runs).state === "open";
  const parentRuns = mergeCommit ? latestRuns(repo, parents[0], cwd) : undefined;
  const compare = mergeCommit ? ghJson(`repos/${repo}/compare/${parents[1]}...${pull.baseSha}`, cwd) : undefined;
  const mergesBase = compare === undefined ? undefined : ["identical", "ahead"].includes(field(compare, "status", isStr, "a compare"));
  const verdict = decideMerge({ repo: pull.baseRepo, pinned: cmd.pinned, sha, parents, runs, parentRuns, mergesBase });
  if (!verdict.ok) throw new Refusal(`${repo}#${pull.number} cannot merge: ${verdict.reason} Follow the land-pr skill.`);
}

function classifyIssue(cmd: Extract<PrCommand, { kind: "issue-edit" }>, cwd: string): "issue" | "pull-request" {
  if (cmd.host || cmd.drift || cmd.lost) throw new Refusal("the Issues edit has an unknown host or repository context. Run it locally with a stable directory and GitHub configuration.");
  if (cmd.hosts.some((h) => h.toLowerCase().replace(/^api\.(?=github\.com$)/, "") !== DEFAULT_HOST)) {
    throw new Refusal(`the Issues edit names another GitHub host. This gate reads ${DEFAULT_HOST} only.`);
  }
  const parts = cmd.repo.split("/");
  if (!parts.every((part, i) => /^[a-z0-9_.-]+$/i.test(part) || part === (i === 0 ? "{owner}" : "{repo}")) ||
    !Number.isSafeInteger(Number(cmd.target)) || Number(cmd.target) < 1) {
    throw new Refusal("the Issues edit does not name a literal repository and issue number, or stable owner/repo placeholders.");
  }
  const response = ghJson(`repos/${cmd.repo}/issues/${cmd.target}`, cwd);
  const number = field(response, "number", isNum, "an issue");
  const url = new URL(field(response, "url", isStr, "an issue"));
  const identity = url.pathname.match(/^\/(?:api\/v3\/)?repos\/([a-z0-9_.-]+)\/([a-z0-9_.-]+)\/issues\/(\d+)$/i);
  const host = DEFAULT_HOST === "github.com" ? "api.github.com" : DEFAULT_HOST;
  if (!Number.isSafeInteger(number) || number !== Number(cmd.target) || !identity || Number(identity[3]) !== number ||
    url.protocol !== "https:" || url.host.toLowerCase() !== host || url.username || url.password || url.search || url.hash ||
    parts.some((part, i) => !part.startsWith("{") && part.toLowerCase() !== identity[i + 1].toLowerCase())) {
    throw new Refusal("GitHub returned an issue whose identity does not match the Issues edit target.");
  }
  if (!isObj(response) || !Object.hasOwn(response, "pull_request")) return "issue";
  field(response, "pull_request", isObj, "an issue");
  return "pull-request";
}

function check(cmd: PrCommand, hookCwd: string): void {
  if (cmd.kind === "merge" && cmd.drift) throw new Refusal(DRIFT[cmd.drift]);
  if (cmd.crowded) throw new Refusal(ALONE);
  const cwd = cmd.host || cmd.lost ? hookCwd : expand(cmd.dir ?? ".", hookCwd);
  if (cmd.kind === "issue-edit") {
    if (classifyIssue(cmd, cwd) === "issue") return;
    return check({ ...cmd, ...cmd.edit }, hookCwd);
  }
  if (cmd.kind === "merge") return checkMerge(cmd, cwd);
  if (cmd.kind === "graphql") return checkGraphql(cmd, cwd);
  if (cmd.kind === "opaque") throw new Refusal(OPAQUE[cmd.part]);
  if (cmd.kind === "unresolved") throw new Refusal(`the PR or issue number \`${cmd.target}\` is not a literal number, so this gate cannot tell which PR this writes. Put the number in the path, for example \`repos/${cmd.repo}/pulls/38\`.`);
  const title = cmd.kind === "create" || cmd.kind === "edit" ? cmd.title && readBody(cmd.title, cmd, cwd) : undefined;
  if (cmd.kind === "create") return checkFields("create", { title, draft: cmd.draft, body: readBody(cmd.body, cmd, cwd) });
  if (cmd.kind === "input") return checkFields(cmd.write, readRequest(cmd, cwd));
  if (cmd.kind === "fields") return checkFields(cmd.write, readFields(cmd, cwd));
  return checkFields("edit", { title, body: cmd.body === undefined ? undefined : readBody(cmd.body, cmd, cwd) });
}

if (process.env.PR_KIT_OFF === "1") process.exit(0);
let input: HookInput;
let commands: PrCommand[];
try {
  input = parseInput(await new Response(Bun.stdin.stream()).text());
  commands = input.tool === "Bash" ? findPrCommands(input.command, { cwd: input.cwd, home: homedir(), cdpath: Boolean(process.env.CDPATH) }) : [];
} catch (err) {
  // An exit other than 0 or 2 lets the tool call run, so a payload the gate cannot read is refused here.
  process.stderr.write(`PR kit blocked this command: the gate could not read the hook input (${String(err)}).\n`);
  process.exit(2);
}
if (commands.length === 0) process.exit(0);
const cwd = input.cwd;

for (const cmd of commands) {
  try {
    check(cmd, cwd);
  } catch (err) {
    const reason = err instanceof Refusal ? err.message : `the gate could not check this command: ${String(err)}`;
    process.stderr.write(`PR kit blocked \`${cmd.via}\`.\n${reason}\nThe open-pr and land-pr skills write and land a PR that passes.\n`);
    process.exit(2);
  }
}
process.exit(0);
