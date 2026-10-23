/**
 * Finds pull-request writes inside a Bash command, so the gate can check them.
 * Pure: it never reads files or calls gh. The gate resolves file bodies and merge state.
 *
 * Covered: `gh pr create|edit|merge`, `gh api` POST/PATCH on `repos/O/R/pulls[/N]` and PUT on
 * `repos/O/R/pulls/N/merge`, PATCH on numbered `repos/O/R/issues/N`, and every `gh api graphql` call whose query is not a literal that provably
 * neither merges nor writes a PR. The same holds inside `ssh host '...'`, `bash -c`, and a program a shell
 * reads on stdin: its last heredoc or here-string, a pipe from cat or from echo or printf of literal words,
 * also into a group or compound opened right after `|`, a heredoc on a closing `)`, `}`, `done`, `fi`, or
 * `esac`, or the stdin of the ssh or bash -c it runs in. A descriptor copy onto that stdin, such as `<&3` or
 * `< /dev/fd/3`, comes back `opaque`, and `<&0` or `< /dev/stdin` changes nothing. A REST write whose PR number is not literal comes back `unresolved`,
 * for the gate to refuse.
 *
 * The alone rule: a PR write or merge is checked only when it runs alone in its call, and is otherwise
 * `crowded`. The gh command sits at the top of its shell, outside any group or compound body, in the
 * foreground, first in any pipeline, with no output redirect to a file and no substitution but a cat
 * read, or `gh auth token` in an assignment before it, which names no context variable. After it come
 * only filters that cannot write a file, in gh's own shell, and none after a merge. Before a write that
 * reads a file, or a merge, run only a literal cd, a set of -e, -u, -x, or -o pipefail, and, for a write,
 * one `cat > f <<'EOF'` whose file is the only file the body, title, and payload reads open, by that same name,
 * joined to gh by `&&`. A write whose text is all inline may follow other commands, but not one joined by `||`.
 * A handed-over shell must be alone too, inside and out.
 *
 * The command is read the way bash reads it: quotes, escapes, comments, redirections as tokens, and
 * heredocs as the shell expands them. Text the shell computes comes back marked `expands`, and a PR
 * write whose method, flag, field name, or gh name the shell computes, or that holds an unquoted `$...`,
 * comes back `opaque`. `"$(cat f)"`, `"$(< f)"`, and `"$(cat <<'EOF' ...)"` are read as text, unless the
 * cat copies or closes a descriptor. `~` or `$HOME` at the start of a path is the home directory, unless the
 * command can set HOME. A merge carries its GitHub hosts and the head it requires, and drifts when a word
 * before gh or a cd the gate cannot follow can change the repo gh picks, or the command can change gh's
 * host or config.
 *
 * Limit: this is a static read of the command text. `eval "gh ..."`, `gh api "$P"`, aliases, shell
 * functions, globs, and profile settings are not followed. A script a shell runs as an operand
 * (`bash script.sh`), a program a shell reads through a pipe from any other command (`curl ... | bash`), or
 * one the outer shell splices an expansion into as an argument, is not read, and the gate allows it, as it
 * allows `eval`. A program a shell reads from a `<` or `<>` file is opaque, since a path can reach a heredoc,
 * a pipe, or a descriptor, so `bash < script.sh` is refused even when the script holds no PR command. fish, csh,
 * tcsh, yash, posh, and Korn shells other than plain ksh (mksh, ksh93, pdksh) take options the gate does not model,
 * so one given any option word or any stdin is opaque.
 * A word the shell computes where any shell still reads options, as in `bash "$opts" ...`, is opaque, since it can be `-c`.
 * So is a command name the shell computes, which can be a shell, when a later word or its stdin holds a PR command.
 * A `-c` script or ssh command the outer shell computes is opaque when a command name in it is computed, since that can be gh.
 * Output the outer shell computes, piped into a shell, is opaque too, whatever command or group prints it.
 */

import { ASSIGN, atSource, type AtFiles, type BodySource, CONTEXT, drift, fileKey, type Head, head, KEYWORDS, move, readFile, RUNS_CODE, SETTERS, type Where, type Written } from "./context";

export { atSource, fileKey } from "./context";
export type { AtFiles, BodySource, Where } from "./context";

export type PrField = "title" | "draft" | "body";

/** A REST field: the text gh sends, and `typed` when `-F` turns true, false, null, or an integer in that text into JSON. */
export interface FieldValue {
  source: BodySource;
  typed: boolean;
  /** Set when a typed value is a file's text, known only once the gate reads it. gh reads `@path` text through `atSource`. */
  at?: AtFiles;
}


interface Base {
  /** The command segment, for messages. */
  via: string;
  /** Directory the segment runs in: the last top-level `cd` before it, relative to the hook cwd. Exact only when not `crowded`. */
  dir?: string;
  /** Set when the segment runs on another machine over ssh. */
  host?: string;
  /** `owner/name` when the command names it. */
  repo?: string;
  /** The command changed directory in a way the parser cannot follow, so `dir` is unknown. */
  lost?: boolean;
  /** The PR command does not run on its own in its call, so another command can change what gh reads or merges. */
  crowded?: true;
}

type RestWrite =
  | { kind: "input"; write: "create" | "edit"; request: BodySource }
  | { kind: "fields"; write: "create" | "edit"; fields: Partial<Record<PrField, FieldValue>> };

type IssueEditAction = (RestWrite & { write: "edit" }) | { kind: "opaque"; part: "field" };

export type PrCommand =
  | (Base & { kind: "create"; title?: BodySource; draft: boolean; body: BodySource })
  | (Base & { kind: "edit"; title?: BodySource; body?: BodySource })
  /** A REST create or edit, decoded from --input JSON or -f/-F fields. */
  | (Base & RestWrite)
  /** A numbered Issues edit whose resource must be classified before applying PR rules. */
  | (Base & { kind: "issue-edit"; repo: string; target: string; hosts: string[]; drift?: "repo" | "host"; edit: IssueEditAction })
  /**
   * A PR write the shell computes part of: the method or a word gh could read as flags (`control`), a field name (`field`), or the
   * stdin program it runs in (`program`), or a shell whose options the gate does not read (`shell`). Any write could hide in it.
   */
  | (Base & { kind: "opaque"; part: "control" | "field" | "program" | "shell" })
  /**
   * `pinned`: the command itself names the repo with `-R`, a PR URL, or a literal REST path. `hosts`: every GitHub host it names.
   * `match`: the head commit the merge requires, which gh or GitHub checks when it merges.
   * `drift`: the gate cannot know the `repo` or PR gh picks from the current directory, or the `host` and config gh uses.
   */
  | (Base & { kind: "merge"; target?: string; pinned: boolean; drift?: "repo" | "host"; hosts: string[]; match?: HeadMatch })
  /** `query` is the GraphQL text, or with `json` the `--input` request whose `query` field holds it. */
  | (Base & { kind: "graphql"; query: FieldValue; json: boolean; operationName: boolean })
  /** A REST PR write whose PR number the command builds at run time, so no check can name the PR. */
  | (Base & { kind: "unresolved"; target: string });

/** The head a merge names: `--match-head-commit`, a REST `sha` field, or with `json` the `--input` request whose `sha` field holds it. */
export interface HeadMatch {
  value: FieldValue;
  json: boolean;
}

/**
 * What a GraphQL document can do to a PR: merge it, write it (create or update), or
 * `opaque` when shell expansion in the text could turn it into either. Null means neither.
 */
export function graphqlRisk(text: string, operationName = false): "merge" | "write" | "opaque" | null {
  if (/\b(mergePullRequest|enablePullRequestAutoMerge)\b/.test(text)) return "merge";
  if (/\b(createPullRequest|updatePullRequest)\b/.test(text)) return "write";
  if (/[$`]/.test(topLevel(text).replace(/\$\w+\s*:/g, ""))) return "opaque";
  // A query cannot write. With operationName set, an expansion could add a mutation as a second operation.
  if (!operationName && !/\bmutation\b/.test(text)) return null;
  const declared = new Set([...text.matchAll(/\$(\w+)\s*:/g)].map((m) => m[1]));
  const undeclared = [...text.matchAll(/\$(\w+)/g)].some((m) => !declared.has(m[1]));
  return /\$\(|`|\$\{|\w\$/.test(text) || undeclared ? "opaque" : null;
}

/**
 * The text outside every `{...}` block, where operation types live. Braces in strings and
 * `#` comments do not count. Comments always count as top-level text, since an expansion
 * in one can end the comment.
 */
function topLevel(text: string): string {
  let out = "";
  let depth = 0;
  for (let i = 0; i < text.length; i++) {
    const end = text.startsWith('"""', i) ? text.indexOf('"""', i + 3) : -1;
    const str = text.startsWith('"""', i) ? (end < 0 ? text.length : end + 3) : text[i] === '"' ? closeQuote(text, i) : -1;
    if (text[i] === "#") {
      const eol = text.indexOf("\n", i);
      out += text.slice(i, eol < 0 ? text.length : eol);
      i = eol < 0 ? text.length : eol;
    } else if (str >= 0) {
      if (depth === 0) out += text.slice(i, str);
      i = str - 1;
    } else if (text[i] === "{") depth++;
    else if (text[i] === "}") depth = Math.max(0, depth - 1);
    else if (depth === 0) out += text[i];
  }
  return out;
}

/** The index just past the `"` string that opens at `start`. */
function closeQuote(text: string, start: number): number {
  for (let i = start + 1; i < text.length; i++) {
    if (text[i] === "\\") i++;
    else if (text[i] === '"' || text[i] === "\n") return i + 1;
  }
  return text.length;
}

/**
 * Markers for text the shell computes when it runs. A NUL never occurs in a bash command,
 * so a word holding one is never plain text. `\0n\0` is substitution n, `HOME` is `"$HOME"` or `~`.
 * `UNKNOWN` stays in its word, and `LOOSE` is unquoted, so the shell can split it into more words.
 * `LOOSE_HOME` is an unquoted `$HOME`: the home directory, which the shell can also split.
 */
const HOME = "\0~\0";
const UNKNOWN = "\0?\0";
const LOOSE = "\0*\0";
const LOOSE_HOME = "\0~*\0";
/** A path that starts at the home directory. */
const AT_HOME = /^\0~\*?\0(?=\/|$)/;
const MARKER = /\0[^\0]*\0/g;
const SUB = /\0(\d+)\0/g;

interface Heredoc {
  text: string;
  /** The delimiter was quoted (`<<'EOF'`), so the shell keeps the text as written. */
  quoted: boolean;
  /** An unquoted heredoc's text with each expansion as its marker, so the substitutions it runs are scanned. */
  marked?: string;
}

/**
 * One stdin redirection. bash applies them left to right, so gh reads the last one. `word` keeps a target whose substitutions run first.
 * A `copy` is `<&N`, `0>&N`, a `descriptorPath`, or a close or move with `-`: stdin becomes descriptor `fd`, or closes.
 */
type Stdin = { kind: "doc"; doc: number } | { kind: "file"; path: string } | { kind: "string"; word: string } | { kind: "copy"; fd: string; word: string } | { kind: "other"; word: string };

/** An output redirection to a file: `fd` is the descriptor, or `&` for stdout and stderr together. A copy such as `2>&1` is not one. */
interface Output {
  fd: string;
  append: boolean;
  target: string;
}

/**
 * One simple command: its words after quote removal, and its redirections in order. `always`: the shell runs it whenever
 * it reaches its list, since it starts the list and sits in no compound body.
 */
interface Segment {
  words: string[];
  stdin: Stdin[];
  /** Input redirections on other file descriptors. The command does not read them as stdin, but they still expand. */
  other: Stdin[];
  out: Output[];
  /** Output descriptor copies and closes, such as `2>&1` or `>&-`. */
  copies: number;
  /** It runs in a `( )` subshell. */
  subshell: boolean;
  /** In or opening a compound or `{ }` body. */
  nested: boolean;
  /** The operator that ends it, such as `;`, `&`, or `|`. */
  after?: string;
  always: boolean;
  /** The pipeline part whose output this command reads on stdin. */
  pipe?: Segment;
  /** The commands of the `{ }`, `( )`, or compound command this segment closes. They print to its pipe. */
  group?: Segment[];
}

/**
 * A `$(...)`, backquote, or `<(...)` command, and what the shell puts in its place: inside double
 * quotes its output as one `word`, unquoted its output split into `words`, and for `<(...)` a `path`.
 */
interface Sub {
  segments: Segment[];
  output: "word" | "words" | "path";
}

/** What a command can change in the environment gh and cd read, from its words after quote removal. */
interface Env {
  /** The context variables a setting word names, or `*` when a setter's name is computed or the command runs other shell code. */
  names: Set<string>;
}

/** One shell's parse: its commands, and the heredocs and substitutions their markers point at. */
interface Scope {
  segments: Segment[];
  docs: Heredoc[];
  subs: Sub[];
  /** No setting word names HOME, so `~` and `$HOME` are the gate's home directory. */
  home: boolean;
  env: Env;
  /** A single `&` runs a command in the background somewhere in this text. */
  background?: true;
}


/** What the commands of `scope`, its substitutions included, can change, added to what an outer shell changed. */
function envOf(scope: Scope, outer: Env): Env {
  const env: Env = { names: new Set(outer.names) };
  for (const seg of [scope.segments, ...scope.subs.map((s) => s.segments)].flat()) {
    const found = head(seg.words, (w) => computed(w, scope));
    const cmd = found.at < 0 ? "" : seg.words[found.at];
    if (!found.sure || RUNS_CODE.includes(cmd)) env.names.add("*");
    // Only words that set variables name one: the assignments and wrapper options before the command, and a setter's
    // operands. A literal argument, such as a merge subject that mentions HOME, sets nothing.
    const setting = found.at < 0 || SETTERS.includes(cmd) ? seg.words : seg.words.slice(0, found.at);
    for (const word of setting) {
      for (const name of word.replace(MARKER, " ").match(/[A-Za-z_]\w*/g) ?? []) if (CONTEXT.includes(name)) env.names.add(name);
      if (SETTERS.includes(cmd) && word.split("=")[0].includes("\0")) env.names.add("*");
    }
  }
  return env;
}

/** Reads `src`. When its words can set HOME, it is read again with `~` and `$HOME` as computed text. */
function lex(src: string, outer: Env = { names: new Set() }): Scope {
  const parse = (home: boolean): Scope => {
    const scope: Scope = { segments: [], docs: [], subs: [], home, env: outer };
    scope.segments = new Lexer(src, scope).commands(false);
    return scope;
  };
  const first = parse(true);
  const env = envOf(first, outer);
  const scope = env.names.has("HOME") || env.names.has("*") ? parse(false) : first;
  scope.env = env;
  return scope;
}

const REDIRECT = /(\d*)(<<<|<<-|<<|<&|<>|<)/y;

/**
 * The descriptor a literal redirection path opens a copy of: /dev/stdin, /dev/stdout, /dev/stderr, or /dev/fd/N, which
 * bash handles itself, or /proc/self/fd/N. `?` for any other path under /dev/fd/ or /proc/, which the gate cannot follow.
 * Any other path can still reach a descriptor, through `..`, a link, or text the shell computes, so `stdinText` decides.
 */
function descriptorPath(word: string): string | undefined {
  const path = localPath(word);
  if (path === undefined) return undefined;
  const std = ["/dev/stdin", "/dev/stdout", "/dev/stderr"].indexOf(path);
  if (std >= 0) return String(std);
  const fd = /^\/(?:dev|proc\/self)\/fd\/(\d+)$/.exec(path)?.[1];
  if (fd !== undefined) return String(Number(fd));
  return /^\/(?:dev\/fd|proc)\//.test(path) ? "?" : undefined;
}

const OUTPUT = /(\d*)(>>|>\||>&|>)|&>>?/y;
/** The characters that end a word. `commands` consumes each one, so every word read advances. */
const BREAK = /[ \t\n;&|()<>]/;

const ANSI_C: Record<string, string> = { a: "\x07", b: "\b", e: "\x1b", E: "\x1b", f: "\f", n: "\n", r: "\r", t: "\t", v: "\v", "\\": "\\", "'": "'", '"': '"', "?": "?" };

/**
 * The text of a `$'...'` body as bash decodes it. Undefined when the command text does not fix it:
 * a `\c` control escape, a NUL, which ends the string in bash, or an escape past ASCII, which bash encodes by locale.
 */
function ansiC(body: string): string | undefined {
  if (body.includes("\\c")) return undefined;
  let fixed = true;
  const text = body.replace(/\\(?:([0-7]{1,3})|x([0-9a-fA-F]{1,2})|u([0-9a-fA-F]{1,4})|U([0-9a-fA-F]{1,8})|([\s\S]))/g, (all, oct, hex, u, big, ch) => {
    const code = oct ? parseInt(oct, 8) & 0xff : hex || u || big ? parseInt(hex || u || big, 16) : undefined;
    if (code === undefined) return ANSI_C[ch] ?? all;
    if (code === 0 || code > 0x7f) fixed = false;
    return String.fromCharCode(code & 0x7f);
  });
  return fixed ? text : undefined;
}

/** Reads bash syntax far enough to find words, stdin redirections, heredocs, and substitutions. It never runs anything. */
class Lexer {
  private pos = 0;
  private pending: { delim: string; strip: boolean; doc: number }[] = [];
  /** The `( ... )` subshells open at `pos`. */
  private parens = 0;
  /** If, while, until, for, case, and select bodies open at `pos`. */
  private compound = 0;
  private groups = 0;
  /** The paren depth of each open case, so its pattern `)` closes no subshell. -1 marks a `$(` boundary. */
  private cases: number[] = [];
  /** Groups opened right after `|`: the pipeline part they read, and the depths they close at. Every command inside reads it. */
  private feeds: { pipe: Segment; parens: number; compound: number; groups: number }[] = [];

  constructor(
    private readonly src: string,
    private readonly scope: Scope,
  ) {}

  /** Commands until the end, or with `close` until the `)` that ends a `$(`. */
  commands(close: boolean): Segment[] {
    const out: Segment[] = [this.segment(true)];
    const opens: number[] = [];
    let depth = 0;
    this.cases.push(-1);
    while (this.pos < this.src.length) {
      const c = this.src[this.pos];
      const next = this.src[this.pos + 1];
      REDIRECT.lastIndex = this.pos;
      OUTPUT.lastIndex = this.pos;
      if (c === "\\" && next === "\n") this.pos += 2;
      else if (c === " " || c === "\t") this.pos++;
      else if (c === "#") {
        // A `#` that starts a word is a comment to the end of the line. The newline stays, so heredoc bodies still follow it.
        const eol = this.src.indexOf("\n", this.pos);
        this.pos = eol < 0 ? this.src.length : eol;
      } else if ((c === "<" || c === ">") && next === "(") {
        this.pos += 2;
        out.at(-1)!.words.push(this.sub(this.commands(true), "path"));
      } else if (OUTPUT.test(this.src)) this.output(out.at(-1)!);
      else if (c === "\n" || c === ";" || c === "&" || c === "|") {
        const pair = next === c && c !== "\n";
        const op = /^(?:;;&|;;|;&|\|&)/.test(this.src.slice(this.pos, this.pos + 3)) ? (this.src.startsWith(";;&", this.pos) ? ";;&" : this.src.slice(this.pos, this.pos + 2)) : pair ? c + c : c;
        this.pos += op.length;
        const left = out.at(-1)!;
        left.after = op === "|&" ? "|" : op;
        if (op === "&") this.scope.background = true;
        if (c === "\n") this.bodies();
        out.push(this.segment(!pair || c === ";"));
        if (left.after === "|") out.at(-1)!.pipe = left;
        if (["|", "&&", "||"].includes(left.after)) this.continuation();
      } else if (c === "(") {
        this.feed(out.at(-1)!);
        depth++;
        this.parens++;
        opens.push(out.length);
        out.push(this.segment(true));
        this.pos++;
      } else if (c === ")") {
        this.pos++;
        if (close && depth === 0) break;
        if (this.cases.at(-1) === depth) {
          out.push(this.segment(true));
          continue;
        }
        const start = depth > 0 ? opens.pop() : undefined;
        if (depth > 0) this.parens--;
        depth = Math.max(0, depth - 1);
        out.push(this.segment(true));
        if (start !== undefined) out.at(-1)!.group = out.slice(start, -1);
      } else if (REDIRECT.test(this.src)) this.redirect(out.at(-1)!);
      else {
        const seg = out.at(-1)!;
        const word = this.word();
        if (seg.words.every((w) => KEYWORDS.includes(w))) {
          this.keyword(word, seg, depth);
          if (["{", "if", "while", "until", "for", "case", "select"].includes(word)) opens.push(out.length - 1);
          else if (["}", "fi", "done", "esac"].includes(word)) seg.group = out.slice(opens.pop() ?? -1, -1);
        }
        seg.words.push(word);
      }
    }
    this.parens -= depth;
    while (this.cases.length > 0 && this.cases.pop() !== -1);
    return out.filter((s) => s.words.length > 0 || s.stdin.length > 0 || s.other.length > 0 || s.out.length > 0 || s.copies > 0);
  }

  /** After `|`, `&&`, or `||` a command must follow, so bash reads the newlines and comments before it as space. */
  private continuation(): void {
    for (;;) {
      const c = this.src[this.pos];
      if (c === " " || c === "\t") this.pos++;
      else if (c === "\\" && this.src[this.pos + 1] === "\n") this.pos += 2;
      else if (c === "\n") {
        this.pos++;
        this.bodies();
      } else if (c === "#") {
        const eol = this.src.indexOf("\n", this.pos);
        this.pos = eol < 0 ? this.src.length : eol;
      } else return;
    }
  }

  /** Tracks compound bodies from a word where a command name goes. A command that opens or sits in one may be skipped. */
  private keyword(word: string, seg: Segment, depth: number): void {
    if (["{", "if", "while", "until", "for", "case", "select"].includes(word)) this.feed(seg);
    if (word === "{") {
      this.groups++;
      seg.nested = true;
    } else if (word === "}") this.groups = Math.max(0, this.groups - 1);
    else if (["if", "while", "until", "for", "case", "select"].includes(word)) {
      this.compound++;
      seg.always = false;
      seg.nested = true;
      if (word === "case") this.cases.push(depth);
    } else if (["fi", "done", "esac"].includes(word)) {
      this.compound = Math.max(0, this.compound - 1);
      if (word === "esac" && this.cases.at(-1) !== -1) this.cases.pop();
    }
  }

  /**
   * One word after quote removal. Text the shell computes becomes a marker, including a `~` right after the
   * first `=`, as in `--flag=~/x`. An unquoted brace list such as `{a,b}` or `{1..3}` gets `LOOSE`, since bash
   * expands it into more words.
   */
  private word(): string {
    let out = "";
    let eq = -1;
    const brace = { depth: 0, open: 0, list: false, done: false };
    const start = this.pos;
    while (this.pos < this.src.length) {
      const c = this.src[this.pos];
      if (BREAK.test(c)) break;
      else if (c === "'") {
        const end = this.src.indexOf("'", this.pos + 1);
        out += this.src.slice(this.pos + 1, end < 0 ? undefined : end);
        this.pos = end < 0 ? this.src.length : end + 1;
      } else if (c === '"') {
        this.pos++;
        out += this.double();
      } else if (c === "\\") {
        if (this.src[this.pos + 1] !== "\n") out += this.src[this.pos + 1] ?? "";
        this.pos += 2;
      } else if (c === "$" || c === "`") out += this.dollar(false);
      else if (c === "~" && (this.pos === start || out.length === eq)) {
        const after = this.src[this.pos + 1] ?? "";
        out += this.scope.home && this.pos === start && (after === "" || after === "/" || BREAK.test(after)) ? HOME : UNKNOWN;
        this.pos++;
      } else {
        if (c === "{" && brace.depth++ === 0) brace.open = out.length;
        else if (brace.depth > 0 && (c === "," || (c === "." && this.src[this.pos + 1] === "."))) brace.list = true;
        else if (c === "}" && brace.depth > 0 && --brace.depth === 0) {
          if (brace.list && !brace.done) {
            out = out.slice(0, brace.open) + LOOSE + out.slice(brace.open);
            brace.done = true;
          }
          brace.list = false;
        }
        out += c;
        this.pos++;
        if (c === "=" && eq < 0) eq = out.length;
      }
    }
    return out;
  }

  /** The text of a `"..."` string, from just past its opening quote. */
  private double(): string {
    let out = "";
    while (this.pos < this.src.length && this.src[this.pos] !== '"') {
      const c = this.src[this.pos];
      const next = this.src[this.pos + 1];
      if (c === "\\" && next !== undefined && '$`"\\\n'.includes(next)) {
        if (next !== "\n") out += next;
        this.pos += 2;
      } else if (c === "$" || c === "`") out += this.dollar(true);
      else {
        out += c;
        this.pos++;
      }
    }
    this.pos++;
    return out;
  }

  /**
   * A `$` or backquote expansion: its marker, or a plain `$` the shell keeps. ANSI-C `$'...'` is its decoded
   * text, or computed when `ansiC` cannot fix it. Locale `$"..."` counts as computed, since bash can translate
   * it. An unquoted expansion, and `"$@"`, can become several words.
   */
  private dollar(quoted: boolean): string {
    const next = this.src[this.pos + 1] ?? "";
    const output = quoted ? "word" : "words";
    const param = (name: string): string =>
      name === "HOME" && this.scope.home ? (quoted ? HOME : LOOSE_HOME) : quoted && !name.includes("@") ? UNKNOWN : LOOSE;
    if (this.src[this.pos] === "`") {
      let inner = "";
      let i = this.pos + 1;
      for (; i < this.src.length && this.src[i] !== "`"; i++) {
        if (this.src[i] === "\\" && "$`\\".includes(this.src[i + 1] ?? "")) i++;
        inner += this.src[i];
      }
      this.pos = i + 1;
      return this.sub(new Lexer(inner, this.scope).commands(false), output);
    }
    if (next === "(") {
      this.pos += 2;
      return this.sub(this.commands(true), output);
    }
    if (next === "{") {
      let i = this.pos + 1;
      for (let depth = 0; i < this.src.length; i++) {
        if (this.src[i] === "{") depth++;
        else if (this.src[i] === "}" && --depth === 0) break;
      }
      const name = this.src.slice(this.pos + 2, i);
      this.pos = i + 1;
      // A default or alternate word runs its substitutions, so they are scanned like any other.
      const inner = new Lexer(name, this.scope).expansions().match(SUB) ?? [];
      return param(name) + inner.join("");
    }
    const name = /^[A-Za-z_]\w*/.exec(this.src.slice(this.pos + 1, this.pos + 256))?.[0];
    if (name) {
      this.pos += 1 + name.length;
      return param(name);
    }
    if (next !== "" && "0123456789@*#?$!-".includes(next)) {
      this.pos += 2;
      return param(next);
    }
    if (!quoted && next === "'") {
      let i = this.pos + 2;
      while (i < this.src.length && this.src[i] !== "'") i += this.src[i] === "\\" ? 2 : 1;
      const text = i < this.src.length ? ansiC(this.src.slice(this.pos + 2, i)) : undefined;
      this.pos = i + 1;
      return text ?? UNKNOWN;
    }
    this.pos++;
    return !quoted && next === '"' ? UNKNOWN : "$";
  }

  /** Starts a feed when `seg` opens a group as the first thing after `|`. */
  private feed(seg: Segment): void {
    if (seg.pipe && seg.words.length === 0) this.feeds.push({ pipe: seg.pipe, parens: this.parens, compound: this.compound, groups: this.groups });
  }

  private segment(always: boolean): Segment {
    const nested = this.compound + this.groups > 0;
    const open = (f: Lexer["feeds"][number]): boolean => this.parens > f.parens || this.compound > f.compound || this.groups > f.groups;
    while (this.feeds.length > 0 && !open(this.feeds.at(-1)!)) this.feeds.pop();
    return { words: [], stdin: [], other: [], out: [], copies: 0, subshell: this.parens > 0, nested, always: always && !nested, pipe: this.feeds.at(-1)?.pipe };
  }

  private sub(segments: Segment[], output: Sub["output"]): string {
    return `\0${this.scope.subs.push({ segments, output }) - 1}\0`;
  }

  /** A `<` redirection. Only fd 0 is stdin, and the others are kept apart. A heredoc body starts at the next newline. */
  private redirect(seg: Segment): void {
    REDIRECT.lastIndex = this.pos;
    const [, fd, op] = REDIRECT.exec(this.src)!;
    this.pos = REDIRECT.lastIndex;
    while (this.src[this.pos] === " " || this.src[this.pos] === "\t") this.pos++;
    const start = this.pos;
    const sub = /^[<>]\(/.test(this.src.slice(this.pos, this.pos + 2));
    if (sub) this.pos += 2;
    const target = sub ? this.sub(this.commands(true), "path") : this.word();
    let stdin: Stdin = { kind: "other", word: target };
    if (op === "<<" || op === "<<-") {
      const doc = this.scope.docs.push({ text: "", quoted: /['"\\]/.test(this.src.slice(start, this.pos)) }) - 1;
      this.pending.push({ delim: target, strip: op === "<<-", doc });
      stdin = { kind: "doc", doc };
    } else if (op === "<<<") stdin = { kind: "string", word: target };
    else if (op === "<&") stdin = { kind: "copy", fd: target, word: target };
    else if (descriptorPath(target) !== undefined) stdin = { kind: "copy", fd: descriptorPath(target)!, word: target };
    else if (op === "<") stdin = { kind: "file", path: target };
    (Number(fd || "0") === 0 ? seg.stdin : seg.other).push(stdin);
  }

  /** A `>` redirection. `>&` to a descriptor number, a number and `-`, or `-` copies, moves, or closes one, and to any other word writes that file, as `&>` does. */
  private output(seg: Segment): void {
    OUTPUT.lastIndex = this.pos;
    const [op, fd, kind] = OUTPUT.exec(this.src)!;
    this.pos = OUTPUT.lastIndex;
    while (this.src[this.pos] === " " || this.src[this.pos] === "\t") this.pos++;
    const target = this.word();
    // A target the shell computes can expand to a descriptor number, so it may copy one as well as write a file.
    const computed = kind === ">&" && target.includes("\0");
    if (computed || (kind === ">&" && /^(?:\d+-?|-)$/.test(target))) {
      seg.copies++;
      if (fd !== "" && Number(fd) === 0) seg.stdin.push({ kind: "copy", fd: target, word: target });
      if (!computed) return;
    }
    seg.out.push({ fd: kind === ">&" || kind === undefined ? "&" : fd || "1", append: op.endsWith(">>"), target });
  }

  /** Reads the bodies of the heredocs opened on the line that just ended. */
  private bodies(): void {
    for (const { delim, strip, doc } of this.pending.splice(0)) {
      const lines: string[] = [];
      while (this.pos < this.src.length) {
        const eol = this.src.indexOf("\n", this.pos);
        const end = eol < 0 ? this.src.length : eol;
        const raw = this.src.slice(this.pos, end);
        const line = strip ? raw.replace(/^\t+/, "") : raw;
        this.pos = end + 1;
        if (line === delim) break;
        lines.push(line);
      }
      const heredoc = this.scope.docs[doc];
      heredoc.text = lines.join("\n");
      if (!heredoc.quoted) heredoc.marked = new Lexer(heredoc.text, this.scope).expansions();
    }
  }

  /** The text of an unquoted heredoc as the shell expands it: each `$` or backquote expansion is its marker, and `\` drops before `$`, a backquote, `\`, or a newline. */
  private expansions(): string {
    let out = "";
    while (this.pos < this.src.length) {
      const c = this.src[this.pos];
      const next = this.src[this.pos + 1] ?? "";
      if (c === "\\" && next !== "" && "$`\\\n".includes(next)) {
        if (next !== "\n") out += next;
        this.pos += 2;
      } else if (c === "$" || c === "`") out += this.dollar(true);
      else {
        out += c;
        this.pos++;
      }
    }
    return out;
  }
}

/** A word for messages, with each computed part shown as `$...`. */
function display(word: string): string {
  return word.replace(MARKER, "$...");
}

/** Whether the shell can split `word` into several words: it holds an unquoted `$...`, `$(...)`, or backquote. */
function splits(word: string, scope: Scope): boolean {
  return word.includes(LOOSE) || word.includes(LOOSE_HOME) || [...word.matchAll(SUB)].some(([, n]) => scope.subs[Number(n)].output === "words");
}

/** One gh flag: its long name, and whether it takes a value. */
interface Flag {
  name: string;
  valued: boolean;
}

/** One gh command's flags, by long name and by short letter. */
interface FlagTable {
  long: Map<string, Flag>;
  short: Map<string, Flag>;
}

/** A table from gh's `--help` list, comma-separated: `"X method"` has a short letter, `"input"` has none. */
function flagTable(valued: string, boolean: string): FlagTable {
  const table: FlagTable = { long: new Map(), short: new Map() };
  for (const [list, takesValue] of [[valued, true], [boolean, false]] as const) {
    for (const entry of list.split(", ")) {
      const [letter, name] = entry.split(" ");
      const flag = { name: name ?? letter, valued: takesValue };
      table.long.set(flag.name, flag);
      if (name !== undefined) table.short.set(letter, flag);
    }
  }
  return table;
}

/** A gh command's words as gh's flag parser reads them. */
interface GhArgs {
  /** Each flag in order, by long name. `value` is the value a flag takes, or a boolean's `=` text. */
  flags: { name: string; value?: string }[];
  positionals: string[];
  /** The shell computes a word gh could read as a flag, or can split a word into more, so gh's reading is unknown. */
  unknown: boolean;
}

/**
 * Reads a gh command's words once, as gh's flag parser does. In a short group such as `-iX POST`, the
 * first letter that takes a value takes the rest of the group or the next word, even one that looks
 * like a flag. A flag missing from the table is unknown, since gh could have it.
 */
function readArgs(words: string[], table: FlagTable, scope: Scope): GhArgs {
  const args: GhArgs = { flags: [], positionals: [], unknown: false };
  const set = (flag: Flag, value: string | undefined): void => {
    if (value !== undefined && (splits(value, scope) || (!flag.valued && value.includes("\0")))) args.unknown = true;
    args.flags.push({ name: flag.name, value });
  };
  let flagsEnd = false;
  for (let i = 0; i < words.length; i++) {
    const word = words[i];
    if (splits(word, scope)) args.unknown = true;
    else if (flagsEnd || word === "-" || !/^[-\0]/.test(word) || word.startsWith(HOME)) args.positionals.push(word);
    else if (word === "--") flagsEnd = true;
    else if (word.startsWith("\0")) args.unknown = true;
    else if (word.startsWith("--")) {
      const eq = word.indexOf("=");
      const flag = table.long.get(word.slice(2, eq < 0 ? undefined : eq));
      if (flag === undefined) args.unknown = true;
      else set(flag, eq >= 0 ? word.slice(eq + 1) : flag.valued ? words[++i] : undefined);
    } else {
      for (let j = 1; j < word.length; j++) {
        const flag = table.short.get(word[j]);
        const rest = word.slice(j + 1);
        if (flag === undefined) args.unknown = true;
        else if (rest.length > 1 && rest[0] === "=") set(flag, rest.slice(1));
        else if (flag.valued) set(flag, rest || words[++i]);
        else {
          set(flag, undefined);
          continue;
        }
        break;
      }
    }
  }
  return args;
}

/** One level of gh's command tree: the flags its command finder reads with no value, and the subcommands the gate reads. */
interface Level {
  bools: string[];
  names: string[];
}

const GH_ROOT: Level = { bools: ["--help", "--version"], names: ["pr", "api"] };
const GH_PR: Level = { bools: ["--help"], names: ["create", "new", "edit", "merge"] };

/** The subcommand gh's command finder picks, and the words left for that subcommand's flag parser. */
interface Found {
  name?: string;
  words: string[];
  /** A word the shell computes came first, so the finder could pick a later name. */
  unknown: boolean;
}

/** Whether the shell computes part of `word`, other than a fixed home directory at its start. */
function computed(word: string, scope: Scope): boolean {
  return word.includes("\0") && (splits(word, scope) || !word.startsWith(HOME));
}

/**
 * Picks a subcommand the way gh's command finder (cobra) does: the first word that is neither a
 * flag nor a flag's value, removed so the flags around it go to the subcommand. The finder takes
 * any flag missing from `bools` to own the next word, even one it does not know. After a word the
 * shell computes, which could be any flag, the first later name from `names` is picked.
 */
function subcommand(words: string[], level: Level, scope: Scope, unknown = false): Found {
  for (let i = 0; i < words.length; i++) {
    const word = words[i];
    if (computed(word, scope)) unknown = true;
    else if (unknown ? level.names.includes(word) : word !== "" && !word.startsWith("-")) {
      return { name: word, words: [...words.slice(0, i), ...words.slice(i + 1)], unknown };
    } else if (unknown) continue;
    else if (word === "--") break;
    else if (!word.includes("=") && (word.startsWith("--") || word.length === 2) && !level.bools.includes(word)) i++;
  }
  return { words, unknown };
}

/** The value gh keeps for a flag that takes one: the last. */
function last(args: GhArgs, name: string): string | undefined {
  return args.flags.findLast((f) => f.name === name)?.value;
}

/** Whether a boolean flag ends up on: its last spelling is bare, or not text gh reads as false. */
function isOn(args: GhArgs, name: string): boolean {
  const flag = args.flags.findLast((f) => f.name === name);
  return flag !== undefined && !["0", "f", "F", "false", "FALSE", "False"].includes(flag.value ?? "true");
}

/** One shell's view while scanning. */
interface Ctx extends Where {
  scope: Scope;
  /** The file the one heredoc before the PR command writes. */
  written?: Written;
  host?: string;
  /** A word came before the shell that runs this text, such as an assignment or env, so it can change the repo gh picks. */
  wrapped?: boolean;
  /** Set for one gh call with no word before it or its shell, so the current directory names its repo and branch. */
  known?: boolean;
  /** The program text this shell was given on stdin, which a command here reads when it has no redirection or pipe of its own. */
  stdin?: Input;
  /** Collects the files the command being read makes gh read. */
  reads?: Read[];
}

/** A file a PR command reads, by its path and absolute name, or `unknown` when gh takes the path from text the shell gives it. */
type Read = { path: string; key?: string } | "unknown";


/** The fields every PR command carries about where it runs. */
function at(seg: Segment, ctx: Ctx): Base {
  return { via: display(seg.words.join(" ")).slice(0, 120), dir: ctx.dir, host: ctx.host, lost: ctx.lost };
}

const expanded = (word: string): BodySource => ({ kind: "inline", text: display(word), expands: true });

/** A path the gate can resolve: `~` at the start is the home directory, and a literal leading `~` is a relative name. Undefined when the shell computes any other part. */
function localPath(word: string): string | undefined {
  const home = AT_HOME.exec(word)?.[0];
  const path = home ? "~" + word.slice(home.length) : word.startsWith("~") ? "./" + word : word;
  return path.includes("\0") ? undefined : path;
}

function fileSource(word: string, ctx: Ctx): BodySource {
  const path = localPath(word);
  if (path === undefined) return expanded(word);
  ctx.reads?.push({ path, key: fileKey(path, ctx) });
  return readFile(path, ctx.written, ctx);
}

/** The text a heredoc gives, as the shell expands it. Text with an expansion in it is not what the command reads. */
function docSource(doc: Heredoc): BodySource {
  const text = doc.marked ?? doc.text;
  return text.includes("\0") ? { kind: "inline", text: display(text), expands: true } : { kind: "inline", text };
}

/** A command's stdin redirections, without `<&0` or `< /dev/stdin`, which copy stdin onto itself and change nothing. */
const given = (seg: Segment): Stdin[] => seg.stdin.filter((s) => !(s.kind === "copy" && s.fd === "0"));

/** What gh reads on stdin: the last stdin redirection, since bash applies them in order. */
function stdin(seg: Segment, ctx: Ctx): BodySource {
  const last = given(seg).at(-1);
  if (last?.kind === "doc") return docSource(ctx.scope.docs[last.doc]);
  if (last?.kind === "file") return fileSource(last.path, ctx);
  if (last?.kind === "string") return wordSource(last.word, ctx);
  return { kind: "missing" };
}

/** A `--body-file`, `-F key=@path`, or `--input` value: a file, or stdin for `-`. */
function pathSource(value: string, seg: Segment, ctx: Ctx): BodySource {
  return value === "-" ? stdin(seg, ctx) : fileSource(value, ctx);
}

/** What a word gives gh: its text, or the text `"$(cat f)"` prints. Any other computed part expands. */
function wordSource(word: string, ctx: Ctx): BodySource {
  const sub = /^\0(\d+)\0$/.exec(word);
  const printed = sub ? catSource(ctx.scope.subs[Number(sub[1])], ctx) : undefined;
  if (printed) return printed;
  return word.includes("\0") ? expanded(word) : { kind: "inline", text: word };
}

/**
 * The one command of `"$(cat f)"`, `"$(< f)"`, or `"$(cat <<'EOF' ...)"`, which only print a file or heredoc, and the file it
 * names, or `stdin`. Undefined for any other substitution, or one that writes a file, copies or closes a descriptor, or runs
 * another substitution.
 */
function catShape(sub: Sub, scope: Scope): { seg: Segment; file: string | "stdin" } | undefined {
  const [seg, ...more] = sub.segments;
  if (sub.output !== "word" || seg === undefined || more.length > 0 || seg.out.length > 0 || seg.copies > 0 || seg.other.length > 0) return undefined;
  if (seg.stdin.some((s) => s.kind === "copy")) return undefined;
  if (targets(seg, scope).some((t) => SUB.test(t))) return undefined;
  const [cmd, ...args] = seg.words;
  if (cmd === undefined && seg.stdin.length === 1 && seg.stdin[0].kind === "file") return { seg, file: seg.stdin[0].path };
  if (cmd === "cat" && args.length === 0 && seg.stdin.length > 0) return { seg, file: "stdin" };
  if (cmd === "cat" && args.length === 1 && seg.stdin.length === 0 && !args[0].startsWith("-") && !splits(args[0], scope)) return { seg, file: args[0] };
  return undefined;
}

/**
 * What a cat substitution prints: the file or heredoc, minus its trailing newlines. Other substitutions are unknown, and so
 * is one whose cat copies or closes a descriptor, as `1>&2` or `>&-` does, since gh may then get something other than the
 * file, or nothing.
 */
function catSource(sub: Sub, ctx: Ctx): BodySource | undefined {
  const shape = catShape(sub, ctx.scope);
  if (shape === undefined) return undefined;
  const source = shape.file === "stdin" ? stdin(shape.seg, ctx) : fileSource(shape.file, ctx);
  if (source?.kind === "file") return { ...source, chomp: true };
  return source?.kind === "inline" ? { ...source, text: source.text.replace(/\n+$/, "") } : source;
}

/** The flags of `gh pr create`, `edit`, and `merge` in gh 2.101, as `--help` lists them. */
const PR_FLAGS = {
  create: flagTable(
    "a assignee, attach, B base, b body, F body-file, H head, l label, m milestone, p project, recover, r reviewer, T template, t title, R repo",
    "d draft, dry-run, e editor, f fill, fill-first, fill-verbose, no-maintainer-edit, w web, help",
  ),
  edit: flagTable(
    "add-assignee, add-label, add-project, add-reviewer, attach, B base, b body, F body-file, m milestone, remove-assignee, remove-label, remove-project, remove-reviewer, t title, R repo",
    "remove-milestone, help",
  ),
  merge: flagTable("A author-email, b body, F body-file, match-head-commit, t subject, R repo", "admin, auto, d delete-branch, disable-auto, m merge, r rebase, s squash, help"),
};

function ghPr(found: Found, seg: Segment, ctx: Ctx): PrCommand | null {
  const verb = found.name === "new" ? "create" : found.name;
  if (verb !== "create" && verb !== "edit" && verb !== "merge") return found.unknown ? { ...at(seg, ctx), kind: "opaque", part: "control" } : null;
  const args = readArgs(found.words, PR_FLAGS[verb], ctx.scope);
  const base = { ...at(seg, ctx), repo: last(args, "repo") };
  if (args.unknown || found.unknown) return { ...base, kind: "opaque", part: "control" };
  if (verb === "merge") {
    const target = args.positionals[0];
    const url = /^https?:\/\/github\.com\/[^/]+\/[^/]+\/pull\/\d+/.test(target ?? "");
    const pinned = base.repo !== undefined || url;
    // -R takes [HOST/]OWNER/REPO.
    const repoHost = base.repo?.split("/").length === 3 ? display(base.repo.split("/")[0]) : undefined;
    const hosts = [urlHost(target), repoHost].filter((h) => h !== undefined);
    const head = last(args, "match-head-commit");
    const match = head === undefined ? undefined : { value: { source: wordSource(head, ctx), typed: false }, json: false };
    const repo = repoHost === undefined ? base.repo : base.repo?.split("/").slice(1).join("/");
    return { ...base, repo, kind: "merge", target, pinned, hosts, match, drift: drift(ctx.scope.env.names, !url && (base.repo === undefined || target === undefined), url, ctx) };
  }
  // gh reads --body-file over --body.
  const file = last(args, "body-file");
  const text = last(args, "body");
  const body = file !== undefined ? pathSource(file, seg, ctx) : text !== undefined ? wordSource(text, ctx) : undefined;
  const titleWord = last(args, "title");
  const title = titleWord === undefined ? undefined : wordSource(titleWord, ctx);
  if (verb === "create") return { ...base, kind: "create", title, draft: isOn(args, "draft"), body: body ?? { kind: "missing" } };
  return body === undefined && title === undefined ? null : { ...base, kind: "edit", title, body };
}

/**
 * The query of a `gh api graphql` call. As on REST, an `--input` file is the payload, wherever it
 * comes, and gh moves the field flags to the URL. Without it, the `query` field's value is read as
 * any REST field's. A field whose key is not literal, or a word gh could read as more flags, makes
 * the query missing, because the parser cannot read it.
 */
function graphqlQuery(args: GhArgs, seg: Segment, ctx: Ctx): { query: FieldValue; json: boolean } {
  const missing = { query: { source: { kind: "missing" } as const, typed: false }, json: false };
  if (args.unknown || args.flags.some((f) => isField(f) && !/^\w+(\[\w*\])*=/.test(f.value ?? ""))) return missing;
  const input = last(args, "input");
  if (input !== undefined) return { query: { source: pathSource(input, seg, ctx), typed: false }, json: true };
  const query = apiFields(args).fields.get("query");
  return query ? { query: fieldValue(query, seg, ctx), json: false } : missing;
}

/** The flags of `gh api` in gh 2.101, as `--help` lists them. */
const API_FLAGS = flagTable(
  "X method, f raw-field, F field, H header, input, q jq, t template, hostname, cache, p preview",
  "i include, paginate, silent, slurp, verbose, allow-escape-sequences, help",
);

const isField = (flag: { name: string }): boolean => flag.name === "raw-field" || flag.name === "field";

/** The host a URL names. */
function urlHost(word: string | undefined): string | undefined {
  const host = word?.match(/^https?:\/\/([^/]+)/i)?.[1];
  return host === undefined ? undefined : display(host);
}

/** The endpoint gh resolves: no scheme, host, Enterprise `api/v3` prefix, query string, or edge slashes. */
function apiPath(raw: string): string {
  // A computed part's marker can hold `?`, which is not the literal query string, so it becomes an empty marker first.
  return raw.replace(MARKER, "\0\0").replace(/^https?:\/\/[^/]+/i, "").replace(/\?.*$/, "").replace(/^\/+|\/+$/g, "").replace(/^api\/(?:v3\/)?/i, "");
}

function ghApi(found: Found, seg: Segment, ctx: Ctx): PrCommand | null {
  const args = readArgs(found.words, API_FLAGS, ctx.scope);
  args.unknown ||= found.unknown;
  const raw = args.positionals[0];
  const path = raw === undefined ? undefined : apiPath(raw);
  const where = at(seg, ctx);
  if (path?.toLowerCase() === "graphql") {
    const { query, json } = graphqlQuery(args, seg, ctx);
    const operationName = args.flags.some((f) => isField(f) && /^operationName[=[]/.test(f.value ?? ""));
    const { source } = query;
    if (source.kind === "inline" && !source.expands && !json && graphqlRisk(source.text, operationName) === null) return null;
    return { ...where, kind: "graphql", query, json, operationName };
  }
  const issue = path?.match(ISSUES);
  const m = path?.match(PULLS) ?? issue;
  const explicit = last(args, "method");
  const control = args.unknown || (explicit?.includes("\0") ?? false);
  // A computed word can be a flag that takes the real endpoint as its value, or the family name, which makes a later pulls or GraphQL path the endpoint.
  const endpoint = (w: string): boolean => (PULLS.test(apiPath(w)) || ISSUES.test(apiPath(w))) || apiPath(w).toLowerCase() === "graphql";
  if (!m) return control && seg.words.some(endpoint) ? { ...where, kind: "opaque", part: "control" } : null;
  const [, repo, number, merge] = m;
  const base = { ...where, repo };
  if (control) return { ...base, kind: "opaque", part: "control" };
  // `pulls/$PR` builds the PR number at run time, so a write there cannot be pinned to a PR.
  const unresolved = number !== undefined && !/^\d+$/.test(number) ? ({ ...base, kind: "unresolved", target: display(number) } as const) : undefined;
  const { fields, opaque } = apiFields(args);
  const input = last(args, "input");
  const method = (explicit ?? (args.flags.some(isField) || input !== undefined ? "POST" : "GET")).toUpperCase();
  const pinned = !repo.includes("{") && !args.flags.some((f) => f.name === "hostname");
  const hostname = last(args, "hostname");
  // gh sends a full URL to the host it names, and --hostname elsewhere, so the gate checks both.
  const hosts = [urlHost(raw), hostname === undefined ? undefined : display(hostname)].filter((h) => h !== undefined);
  if (merge) {
    if (method !== "PUT") return null;
    if (unresolved) return unresolved;
    const sha = fields.get("sha");
    const match = input !== undefined ? { value: { source: pathSource(input, seg, ctx), typed: false }, json: true } : sha && { value: fieldValue(sha, seg, ctx), json: false };
    return { ...base, kind: "merge", target: number, pinned, hosts, match, drift: drift(ctx.scope.env.names, !pinned, false, ctx) };
  }
  const write = !number && method === "POST" ? "create" : number && method === "PATCH" ? "edit" : null;
  if (write === null) return null;
  const issueEdit = (edit: IssueEditAction): PrCommand => ({
    ...base, kind: "issue-edit", repo, target: number, hosts,
    drift: drift(ctx.scope.env.names, !pinned, false, ctx), edit,
  });
  // With --input, gh sends the JSON as the payload and moves every field flag to the query string.
  if (input !== undefined) {
    if (unresolved) return unresolved;
    const request = pathSource(input, seg, ctx);
    return issue ? issueEdit({ kind: "input", write: "edit", request }) : { ...base, kind: "input", write, request };
  }
  if (opaque) return issue ? issueEdit({ kind: "opaque", part: "field" }) : { ...base, kind: "opaque", part: "field" };
  if (write === "edit" && !fields.has("title") && !fields.has("body")) return null;
  if (unresolved) return unresolved;
  const set: Partial<Record<PrField, FieldValue>> = {};
  for (const key of ["title", "draft", "body"] as const) {
    const field = fields.get(key);
    if (field) set[key] = fieldValue(field, seg, ctx);
  }
  return issue ? issueEdit({ kind: "fields", write: "edit", fields: set }) : { ...base, kind: "fields", write, fields: set };
}

const ISSUES = /^repos\/([^/]+\/[^/]+)\/issues\/([^/]+)$/i;
const PULLS = /^repos\/([^/]+\/[^/]+)\/pulls(?:\/([^/]+)(\/merge)?)?$/i;

interface ApiField {
  value: string;
  typed: boolean;
}

/** The REST payload fields by key. gh refuses a repeated key. `typed` marks `-F`. `opaque`: some key is computed by the shell. */
function apiFields(args: GhArgs): { fields: Map<string, ApiField>; opaque?: true } {
  const fields = new Map<string, ApiField>();
  let opaque: true | undefined;
  for (const flag of args.flags) {
    if (!isField(flag) || flag.value === undefined) continue;
    const eq = flag.value.indexOf("=");
    if ((eq < 0 ? flag.value : flag.value.slice(0, eq)).includes("\0")) opaque = true;
    else if (eq > 0) fields.set(flag.value.slice(0, eq), { value: flag.value.slice(eq + 1), typed: flag.name === "field" });
  }
  return { fields, opaque };
}

/**
 * What gh sends for one field. gh converts a `-F` value after the shell gives it: `@path` sends that
 * file's text as a string, and other text is typed. Text a substitution gives is converted here when
 * the parser knows it, and otherwise by the gate through `at` once it reads the file.
 */
function fieldValue(field: ApiField, seg: Segment, ctx: Ctx): FieldValue {
  if (field.typed && field.value.startsWith("@")) return { source: pathSource(field.value.slice(1), seg, ctx), typed: false };
  const source = wordSource(field.value, ctx);
  if (!field.typed) return { source, typed: false };
  const at: AtFiles = { stdin: stdin(seg, ctx), written: ctx.written, where: { base: ctx.base, dir: ctx.dir, lost: ctx.lost } };
  if (source.kind === "file") {
    ctx.reads?.push("unknown");
    return { source, typed: true, at };
  }
  if (source.kind === "inline" && !source.expands && source.text.startsWith("@")) {
    ctx.reads?.push("unknown");
    return { source: atSource(source.text.slice(1), at), typed: false };
  }
  return { source, typed: true };
}

const SSH_VALUED = ["-b", "-c", "-D", "-E", "-e", "-F", "-I", "-i", "-J", "-L", "-l", "-m", "-O", "-o", "-p", "-Q", "-R", "-S", "-W", "-w"];

/** Every pull-request write in `command`, in order. Empty when the command touches no PR. `base` is where the hook runs it. */
export function findPrCommands(command: string, base: Where["base"] = { cwd: ".", home: "~", cdpath: false }): PrCommand[] {
  const scope = lex(command);
  return scan(scope.segments, { scope, base });
}

/** The command an outer shell hands to `ssh` or `bash -c`. What the outer shell computed is unknown inside, and can end a quote or split a word there. */
function handOver(words: string[], outer: Scope): Scope {
  return lex(words.join(" ").replace(MARKER, LOOSE), outer.env);
}

/**
 * The PR command a gh call makes. A word the shell computes where gh reads the command name could
 * be `pr` or `api`, and one where gh reads the pr subcommand could be any write, so both are opaque.
 */
function ghCommand(seg: Segment, ctx: Ctx, unknown: boolean): PrCommand | null {
  const top = subcommand(seg.words.slice(1), GH_ROOT, ctx.scope, unknown);
  if (top.name === "pr" || (top.name === undefined && top.unknown)) {
    const pr = subcommand(top.words, GH_PR, ctx.scope, top.unknown);
    if (pr.name !== undefined || (top.name === "pr" && pr.unknown)) return ghPr(pr, seg, ctx);
  }
  return top.name === "api" || (top.name === undefined && top.unknown) ? ghApi(top, seg, ctx) : null;
}

/** The text a segment's substitutions sit in: its words, its redirect targets, and its unquoted heredocs, on any descriptor, since all of them expand before the command runs. */
function targets(seg: Segment, scope: Scope): string[] {
  return [
    ...seg.words,
    ...[...seg.stdin, ...seg.other].map((s) => (s.kind === "file" ? s.path : s.kind === "doc" ? (scope.docs[s.doc].marked ?? "") : s.word)),
    ...seg.out.map((o) => o.target),
  ];
}

/** The files a command's output redirects write: any target outside /dev/, where /dev/stderr and /dev/null are no file. */
const writes = (seg: Segment): string[] => seg.out.map((o) => o.target).filter((t) => !/^\/dev\//.test(t) || t.includes("\0") || t.split("/").includes(".."));

/**
 * The file `cat > f <<'EOF'` writes, the one write a PR command may follow: a quoted heredoc to a literal name, and nothing
 * else. A descriptor copy such as `1>&2` can send the text somewhere other than the file.
 */
function heredocTarget(seg: Segment): string | undefined {
  const [doc] = seg.stdin;
  const [to] = seg.out;
  if (seg.words.join(" ") !== "cat" || seg.stdin.length !== 1 || seg.out.length !== 1 || seg.other.length > 0 || seg.copies > 0) return undefined;
  return doc.kind === "doc" && to.fd === "1" && !to.append ? localPath(to.target) : undefined;
}

/** Marks PR commands that do not run alone in their call. */
function crowd(cmds: PrCommand[]): PrCommand[] {
  for (const cmd of cmds) cmd.crowded = true;
  return cmds;
}

/**
 * Commands a PR command may pipe its output into, by the arguments that keep them from writing a file. GNU sort takes any
 * unique prefix of a long option and runs a --compress-program, and uniq writes its second operand.
 */
const FILTERS: Record<string, (args: string[]) => boolean> = {
  cat: (args) => args.every((a) => a === "-"),
  head: () => true,
  tail: () => true,
  grep: () => true,
  wc: () => true,
  cut: () => true,
  tr: () => true,
  jq: () => true,
  pbcopy: () => true,
  sort: (args) => !args.some((a) => /^-[^-]*o|^--[oc]/.test(a)),
  uniq: (args) => args.filter((a) => !/^-./.test(a)).every((a) => a === "-") && args.filter((a) => a === "-").length <= 1,
  sed: (args) => args.every((a) => /^-[nEr]+$/.test(a) || SED.test(a)),
  awk: awkPrints,
};

const top = (seg: Segment): boolean => !seg.subshell && !seg.nested;
const bare = (seg: Segment): boolean => seg.stdin.length === 0 && seg.other.length === 0 && seg.out.length === 0;
const cd = (seg: Segment): boolean => bare(seg) && seg.words.length === 2 && seg.words[0] === "cd" && !seg.words[1].startsWith("-") && localPath(seg.words[1]) !== undefined;

/**
 * `set` with only the error and tracing options, where each `o` in a cluster takes one option name. Any other option can
 * change what cd or a redirect does, as -P and noclobber do.
 */
function setsOptions(seg: Segment): boolean {
  let names = 0;
  for (const word of seg.words.slice(1)) {
    if (names > 0 && ["pipefail", "errexit", "nounset", "xtrace"].includes(word)) names--;
    else if (names === 0 && /^-[euxo]+$/.test(word)) names = word.match(/o/g)?.length ?? 0;
    else return false;
  }
  return bare(seg) && seg.words[0] === "set" && seg.words.length > 1 && names === 0;
}

/** A pipeline part after a PR command that only reads its output: a FILTERS command with literal words and no redirect to a file. */
function filter(part: Segment, scope: Scope): boolean {
  const [cmd, ...args] = part.words;
  const readOnly = cmd !== undefined && Object.hasOwn(FILTERS, cmd) && FILTERS[cmd](args);
  return readOnly && top(part) && writes(part).length === 0 && targets(part, scope).every((t) => !t.includes("\0"));
}

/** A sed script that only prints, deletes, quits, or substitutes: no `w`, `e`, or `r` command and no `-i`. */
const SED = /^(?:(?:\d+|\$)(?:,(?:\d+|\$))?|\/[^/]*\/)?[pdq]$|^s(.)(?:(?!\1).)*\1(?:(?!\1).)*\1[gpI\d]*$/;

/** awk with only -F and -v options and a program that cannot write a file, run a command, or load more code. */
function awkPrints(args: string[]): boolean {
  let i = 0;
  while (/^-[Fv]/.test(args[i] ?? "")) i += args[i].length === 2 ? 2 : 1;
  const program = args[i];
  return program !== undefined && !program.startsWith("-") && !/system|getline|close|fflush|[|>@]/.test(program);
}

/** `gh auth token` with literal words: the one substitution an assignment before gh may run, since it reads a token and writes nothing. */
function tokenRead(sub: Sub): boolean {
  const [seg, ...more] = sub.segments;
  return more.length === 0 && seg !== undefined && bare(seg) && seg.words.slice(0, 3).join(" ") === "gh auth token" && seg.words.every((w) => !w.includes("\0"));
}

/** Whether the command before `at` in its and-or list is joined by `||`, so the PR command runs only when another fails. */
function orBefore(segments: Segment[], at: number): boolean {
  for (let i = at - 1; i >= 0 && (segments[i].after === "&&" || segments[i].after === "||"); i--) {
    if (segments[i].after === "||") return true;
  }
  return false;
}

/**
 * Whether the PR commands `made` by `segments[at]` run alone in their call, so no other command can change the bytes gh
 * reads or the head it merges. The command sits at the top of its shell, outside any pipeline but as its first part, in the
 * foreground, with no output redirect to a file and no substitution but a cat read, or `gh auth token` in an assignment
 * before it, which names no CONTEXT variable. After it come only FILTERS, and none after a merge or a shell it hands over
 * to. Before a write that reads a file, or a merge, run only a literal cd, a `setsOptions` set, and, for a write, one
 * `cat > f <<'EOF'` that `&&` joins to it, when f is the one file the body, title, and payload reads open. Before a write
 * whose text is all inline, any command may run, since none can change that text, but not one joined by `||` to it.
 */
function alone(segments: Segment[], at: number, made: PrCommand[], reads: Read[], scope: Scope, heredocs: Map<number, string | undefined>): boolean {
  const seg = segments[at];
  const merge = made.some((c) => c.kind === "merge");
  const lead = seg.words.findIndex((w) => !ASSIGN.test(w));
  const assigns = seg.words.slice(0, lead < 0 ? seg.words.length : lead);
  // targets() lists the words first, so the first assigns.length texts are the assignments.
  const subsOk = targets(seg, scope).every((t, j) =>
    [...t.matchAll(SUB)].every(([, n]) => catShape(scope.subs[Number(n)], scope) !== undefined || (j < assigns.length && tokenRead(scope.subs[Number(n)]))),
  );
  if (scope.background || !top(seg) || seg.pipe || writes(seg).length > 0 || !subsOk || assigns.some((w) => CONTEXT.includes(w.split("=")[0]))) return false;
  const found = head(seg.words, (w) => computed(w, scope));
  const gh = found.sure && found.at >= 0 && isGh(seg.words[found.at]);
  let end = at;
  for (; segments[end].after === "|"; end++) {
    const part = segments[end + 1];
    if (merge || !gh || part === undefined || !filter(part, scope)) return false;
  }
  if (end !== segments.length - 1 || orBefore(segments, at)) return false;
  if (reads.length === 0 && !merge && !made.some((c) => c.kind === "issue-edit")) return true;
  // A second read can open the heredoc's file by another name, a link, and get the bytes on disk before cat runs.
  const only = reads.length === 1 && reads[0] !== "unknown" ? reads[0].key : undefined;
  let docs = 0;
  return segments.slice(0, at).every((s, i) => {
    // A command after && is skipped when one before it fails, and the PR command still runs unless && joins them all.
    const runs = s.always || segments.slice(i, at).every((t) => t.after === "&&");
    if (!top(s) || s.pipe || !runs || !["\n", ";", "&&"].includes(s.after ?? "")) return false;
    if (cd(s) || setsOptions(s)) return true;
    const key = heredocs.get(i);
    // When cat fails, as under noclobber, only && keeps gh from reading the old file.
    const joined = segments.slice(i, at).every((t) => t.after === "&&");
    return !merge && joined && key !== undefined && key === only && ++docs === 1;
  });
}

/**
 * Every PR command in `segments`, run in order. Substitutions run first, and every PR command in one is crowded. Then
 * the command's PR commands are read, checked against the alone rule, and its top-level cd is followed, one after && only
 * to the end of an unbroken && chain from the start of its list. A cd in a subshell stays there, and any later PR write that reads a file, and any later merge, is crowded.
 */
function scan(segments: Segment[], ctx: Ctx): PrCommand[] {
  const found: PrCommand[] = [];
  /** By segment index: the absolute name a `cat > f <<'EOF'` before a PR command writes. */
  const heredocs = new Map<number, string | undefined>();
  /** The directory before a cd after && was followed, since that cd holds only until its chain ends. */
  let chained: { dir?: string } | undefined;
  for (const [i, seg] of segments.entries()) {
    for (const word of targets(seg, ctx.scope)) {
      for (const [, n] of word.matchAll(SUB)) found.push(...crowd(scan(ctx.scope.subs[Number(n)].segments, { ...ctx, reads: undefined })));
    }
    const cmd = head(seg.words, (w) => computed(w, ctx.scope));
    const doc = heredocTarget(seg);
    const key = doc === undefined ? undefined : fileKey(doc, ctx);
    if (doc !== undefined) heredocs.set(i, key);
    if (key !== undefined) {
      const text = stdin(seg, ctx);
      ctx.written = { key, source: text.kind === "inline" ? { ...text, written: key } : text };
    }
    const reads: Read[] = [];
    const made = command(seg, cmd, { ...ctx, reads });
    if (made.length > 0 && !alone(segments, i, made, reads, ctx.scope, heredocs)) crowd(made);
    found.push(...made);
    ctx.reads?.push(...reads);
    // `exec` with no command keeps its redirections, so every later command in this shell reads that stdin.
    if (cmd.at < 0 && given(seg).length > 0 && seg.words.some((w) => !ASSIGN.test(w) && w.replace(/^.*\//, "") === "exec")) ctx.stdin = stdinText(seg, ctx) ?? "unseen";
    if (!seg.subshell) {
      const names = ctx.scope.env.names;
      const step = move(seg.words, cmd, runs(segments, i) && seg.stdin.length === 0 && seg.other.length === 0, localPath, ctx.base.cdpath || names.has("CDPATH") || names.has("*"));
      if (step.kind === "follow") {
        if (!seg.always) chained ??= { dir: ctx.dir };
        const absolute = /^[/~]/.test(step.to);
        if (absolute) ctx.lost = undefined;
        ctx.dir = ctx.dir && !absolute ? `${ctx.dir}/${step.to}` : step.to;
      } else if (step.kind === "lose") ctx.lost = true;
    }
    // Past its && chain, a cd the chain ran may have been skipped.
    if (chained && seg.after !== "&&") {
      ctx.dir = chained.dir;
      ctx.lost = true;
      chained = undefined;
    }
  }
  return found;
}

/** Whether `segments[i]` runs whenever its list runs: it starts the list, or an unbroken && chain from the start reaches it. */
function runs(segments: Segment[], i: number): boolean {
  let start = i;
  while (start > 0 && segments[start - 1].after === "&&") start--;
  return segments[start].always;
}

/**
 * The PR commands an `ssh` word between `from` and `to` runs on its host: its remote command, read after the remote
 * shell joins and reads the words again, or with none, the program on its stdin. Undefined with no ssh and host there.
 */
function remote(seg: Segment, ctx: Ctx, from: number, to: number): PrCommand[] | undefined {
  const { words } = seg;
  const ssh = words.findIndex((w, i) => i >= from && i < to && /^(?:.*\/)?ssh$/.test(w));
  if (ssh < 0) return undefined;
  let i = ssh + 1;
  while (i < words.length && words[i].startsWith("-")) i += SSH_VALUED.includes(words[i]) ? 2 : 1;
  if (words[i] === undefined) return undefined;
  const argv = words.slice(i + 1);
  const into = { base: ctx.base, host: words[i], stdin: stdinOf(seg, ctx) };
  // `ssh host` with no remote command runs the remote shell on its stdin.
  if (argv.length === 0) return into.stdin === undefined ? [] : program(into.stdin, seg, ctx, into);
  const scope = handOver(argv, ctx.scope);
  // The outer shell computes part of this command, so a command name in it can be gh.
  if (argv.some((w) => w.includes("\0")) && hidden(scope)) return [{ ...at(seg, ctx), kind: "opaque", part: "program" }];
  return scan(scope.segments, { ...into, scope });
}

const isGh = (t: string): boolean => t === "gh" || t.endsWith("/gh");

/** A script operand that names the shell's own stdin, so stdin is the program. */
const STDIN = /^\/dev\/(?:stdin|fd\/0)$|^\/proc\/self\/fd\/0$/;

/** Commands that read their arguments as text and never run one, so a shell name among them is data. */
const DATA = ["grep", "egrep", "fgrep", "echo", "printf", "which", "type", "ps", "pgrep"];

/** A shell command word, by name or path. */
const SHELL = /^(?:.*\/)?(?:bash|sh|zsh|dash|ash|rbash|[a-z]*ksh\d*|yash|posh|fish|csh|tcsh)$/;

/** The shells in SHELL whose options and programs the gate does not read as bash's. */
const FOREIGN = /^(?:.*\/)?(?:[a-z]+ksh\d*|ksh\d+|yash|posh|fish|csh|tcsh)$/;

/**
 * A shell's own options after the shell word at `at`: where its operands start, and whether it runs a `-c` script
 * or reads its program on stdin with `-s`. As in bash, each `o` or `O` in a cluster takes the next word, and `--` or a lone `-` ends the options.
 */
function shellOptions(words: string[], at: number): { operand: number; script: boolean; stdin: boolean } {
  const found = { operand: at + 1, script: false, stdin: false };
  for (; found.operand < words.length && /^(?:-|[-+].+)$/.test(words[found.operand]); found.operand++) {
    const word = words[found.operand];
    if (word === "--" || word === "-") return { ...found, operand: found.operand + 1 };
    if (word === "--rcfile" || word === "--init-file") found.operand++;
    else if (/^[-+][A-Za-z]+$/.test(word)) {
      found.operand += word.match(/[oO]/g)?.length ?? 0;
      found.script ||= word[0] === "-" && word.includes("c");
      found.stdin ||= word[0] === "-" && word.includes("s");
    }
  }
  return found;
}

/** The `-c` script of a shell between `from` and `to`, after the shell's own options, and the shell word's index. */
function shellScript(words: string[], from: number, to: number): { at: number; script: string } | undefined {
  for (let i = from; i < to; i++) {
    if (!SHELL.test(words[i])) continue;
    const { operand, script } = shellOptions(words, i);
    if (script && words[operand] !== undefined) return { at: i, script: words[operand] };
  }
  return undefined;
}

/** A shell program a command reads on stdin. `expands`: the outer shell computes part of these bytes before the program runs. */
interface StdinProgram {
  text: string;
  expands: boolean;
}

/**
 * What a command reads on stdin: a program the gate can read, `unseen` text such as another command's output, or
 * `opaque` text: a descriptor copy, which can hold a heredoc or here-string opened anywhere in the command, a file, or
 * output the outer shell computes.
 */
type Input = StdinProgram | "unseen" | "opaque";

/**
 * The program text the last stdin redirection gives: a here-string, or a heredoc as the outer shell expands it. A file
 * other than /dev/null, or a descriptor copy, is opaque, since a path or descriptor can reach a heredoc, a pipe, or a
 * descriptor the gate cannot follow.
 */
function stdinText(seg: Segment, ctx: Ctx): StdinProgram | "opaque" | undefined {
  const { scope } = ctx;
  const last = given(seg).at(-1);
  if (last?.kind === "file" && last.path === "/dev/null") return undefined;
  if (last?.kind === "copy" || last?.kind === "file" || last?.kind === "other") return "opaque";
  if (last?.kind === "string") return { text: last.word, expands: last.word.includes("\0") };
  if (last?.kind !== "doc") return undefined;
  const text = scope.docs[last.doc].marked ?? scope.docs[last.doc].text;
  return { text, expands: text.includes("\0") };
}

/** Whether the command at `found` is a data command such as grep, which takes any later shell name as text. */
const dataCommand = (words: string[], found: Head): boolean => found.at >= 0 && DATA.includes(words[found.at].replace(/^.*\//, ""));

/** Whether a word of `seg` that `name` matches can run: any one, except an argument of a data command such as grep. */
function runsWord(seg: Segment, scope: Scope, name: (word: string) => boolean): boolean {
  const found = head(seg.words, (w) => computed(w, scope));
  return seg.words.some((w, i) => name(w) && (i === found.at || !dataCommand(seg.words, found)));
}

/** Whether any command in the scope can be a shell that reads a program on stdin: a shell or ssh word, or a command name the shell computes. */
const runsShell = (scope: Scope): boolean =>
  [scope.segments, ...scope.subs.map((s) => s.segments)]
    .flat()
    .some((s) => runsWord(s, scope, (w) => SHELL.test(w) || /^(?:.*\/)?ssh$/.test(w)) || !head(s.words, (w) => computed(w, scope)).sure);

/** What a command reads on stdin as program text: its last redirection, else the pipeline part before it, else the stdin its shell was given. */
function stdinOf(seg: Segment, ctx: Ctx): Input | undefined {
  if (given(seg).length > 0) return stdinText(seg, ctx);
  return seg.pipe ? piped(seg.pipe, ctx) : ctx.stdin;
}

/** Whether the shell computes part of `word`: any expansion or substitution but a leading literal `~`. */
const varies = (word: string): boolean => word.replace(MARKER, (t) => (t === HOME ? "" : t)).includes("\0");

/** The printf escapes the gate decodes. Any other `\` or `%` makes the output unseen. */
const PRINTF: Record<string, string> = { "%%": "%", "\\\\": "\\", "\\n": "\n", "\\t": "\t" };

/**
 * What a pipeline part prints, when the gate can read it: cat of its own stdin, or echo or printf of literal words.
 * echo decodes backslash escapes in some shells, zsh and dash among them, so echo text with one is unseen.
 */
function piped(left: Segment, ctx: Ctx): Input {
  const [cmd, ...rest] = left.words;
  const args = cmd === "printf" && rest[0] === "--" ? rest.slice(1) : rest;
  // Output the outer shell computes can be any program, whatever command or group prints it.
  if ([left, ...(left.group ?? [])].some((s) => s.words.some(varies))) return "opaque";
  if (cmd === "cat" && args.length === 0) return stdinOf(left, ctx) ?? "unseen";
  if (cmd === "echo") {
    const start = args.findIndex((w) => !/^-[neE]+$/.test(w));
    const text = start < 0 ? "" : args.slice(start).join(" ");
    return text.includes("\\") ? "unseen" : { text, expands: false };
  }
  if (cmd === "printf" && /^%s(?:\\n)?$/.test(args[0] ?? "") && args.length > 1) {
    return { text: args.slice(1).map((a) => (args[0] === "%s" ? a : `${a}\n`)).join(""), expands: false };
  }
  if (cmd === "printf" && args.length === 1 && !args[0].startsWith("-")) {
    let known = true;
    const text = args[0].replace(/%%|\\[\\nt]|[%\\]/g, (t) => {
      known &&= t in PRINTF;
      return PRINTF[t] ?? t;
    });
    return known ? { text, expands: false } : "unseen";
  }
  return "unseen";
}

/** Whether a command name in `scope` is one the shell computes, which can be gh when the outer shell computed the text. */
const hidden = (scope: Scope): boolean => scope.segments.some((s) => !head(s.words, (w) => computed(w, scope)).sure);

/**
 * The PR commands a program read on stdin runs, scanned in `into`. The program is that stdin, so its own commands get none.
 * A program the gate cannot read, such as an installer piped from curl, runs unread, like `eval`.
 */
function program(input: Input, seg: Segment, ctx: Ctx, into: Omit<Ctx, "scope">): PrCommand[] {
  if (input === "unseen") return [];
  const opaque: PrCommand[] = [{ ...at(seg, ctx), kind: "opaque", part: "program" }];
  if (input === "opaque") return opaque;
  const scope = handOver([input.text], ctx.scope);
  const inner = scan(scope.segments, { ...into, scope, stdin: undefined });
  // The outer shell expands this text before the program runs, so a write it shows is not the one gh receives, and a command name it computes can be gh.
  return input.expands && (inner.length > 0 || hidden(scope)) ? opaque : inner;
}

/**
 * The index of a shell between `from` and `to` that reads its program on stdin: one with no `-c` script. Without `-s`,
 * an operand, even one after `--`, names a script file, and stdin is that script's data. Shell words an earlier
 * command takes as arguments can be a stdin shell too, the way a `bash -c` among them is still read.
 */
function stdinShell(words: string[], from: number, to: number): number | undefined {
  for (let i = from; i < to; i++) {
    if (!SHELL.test(words[i])) continue;
    const { operand, script, stdin } = shellOptions(words, i);
    return script || (!stdin && words[operand] !== undefined && !STDIN.test(words[operand])) ? undefined : i;
  }
  return undefined;
}

/**
 * Whether a command whose name the shell computes, at `at`, can be a shell that runs a PR command: one in a later word it
 * could run as a `-c` script, after any `--name=` prefix, or in the program on its stdin. A file on its stdin is opaque, as it is to bash.
 * A script word the outer shell computes can name gh once an option, written or inside a name that splits, makes it a script.
 */
function hidesShell(seg: Segment, at: number, ctx: Ctx): boolean {
  const { words } = seg;
  const input = stdinOf(seg, ctx);
  if (input === "opaque" || (input !== undefined && program(input, seg, ctx, { ...ctx }).length > 0)) return true;
  return words.slice(at + 1).some((word, i) => {
    const text = word.replace(/^-[^=\0]*=/, "");
    const scope = handOver([text], ctx.scope);
    if (scan(scope.segments, { ...ctx, scope, reads: undefined, stdin: undefined }).length > 0) return true;
    const optioned = splits(words[at], ctx.scope) || words.slice(at + 1, at + 2 + i).some((w) => w.startsWith("-"));
    return text.includes("\0") && optioned && hidden(scope);
  });
}

/**
 * The PR commands one simple command runs: the ones inside a `bash -c` script or `ssh`, a shell program the
 * command reads on stdin, or a gh call. gh at the command head is read as gh reads it. gh anywhere else, or a
 * command name the shell computes, could be a write a wrapper hides, so it is read as opaque.
 */
function command(seg: Segment, found: Head, ctx: Ctx): PrCommand[] {
  const { words } = seg;
  // A redirection after `)`, `}`, `done`, `fi`, or `esac` is the stdin of every command inside, so a shell there can read it.
  if (seg.stdin.length > 0 && (words.length === 0 || ["}", "done", "fi", "esac"].includes(words[0]))) {
    const last = given(seg).at(-1);
    // A file is a program only to a shell that reads it, so a loop over a file's lines with no shell in the command is data.
    if ((last?.kind === "file" || last?.kind === "other") && !runsShell(ctx.scope)) return [];
    const input = stdinText(seg, ctx);
    if (input && ctx.scope.segments.some((s) => runsWord(s, ctx.scope, (w) => FOREIGN.test(w)))) return crowd([{ ...at(seg, ctx), kind: "opaque", part: "shell" }]);
    return input && program(input, seg, ctx, { ...ctx }).length > 0 ? crowd([{ ...at(seg, ctx), kind: "opaque", part: "program" }]) : [];
  }
  if (found.split) return [{ ...at(seg, ctx), kind: "opaque", part: "control" }];
  const lost = ctx.lost || found.chdir || undefined;
  const from = Math.max(found.at, 0);
  // A shell or ssh word after gh is a value gh reads, so only the words before the first gh can run one.
  const gh = words.findIndex((t, i) => i >= from && isGh(t));
  const to = gh < 0 ? words.length : gh;
  // A shell word a data command takes as an argument, as in `grep fish`, runs nothing.
  const first = words.findIndex((w, i) => i >= from && i < to && SHELL.test(w));
  const listed = first !== found.at && dataCommand(words, found);
  if (first >= 0 && !listed) {
    const foreign = FOREIGN.test(words[first]) && (/^[-+]/.test(words[first + 1] ?? "") || stdinOf(seg, ctx) !== undefined);
    const { operand, script } = shellOptions(words, first);
    // A word the shell computes where the shell still reads options can be one, such as -c, unless it starts with literal text.
    const option = words[operand] ?? "";
    const cluster = words.slice(first + 1, operand).some((w) => computed(w, ctx.scope));
    if (foreign || cluster || (!script && computed(option, ctx.scope) && (option.startsWith("\0") || splits(option, ctx.scope)))) {
      return [{ ...at(seg, ctx), kind: "opaque", part: "shell" }];
    }
  }
  const shell = shellScript(words, from, to);
  // ssh hands its words to the remote shell, which joins them and reads them again, so a shell among them is read there.
  const ssh = remote(seg, ctx, from, shell?.at ?? to);
  if (ssh) return ssh;
  if (shell) {
    const scope = handOver([shell.script], ctx.scope);
    if (shell.script.includes("\0") && hidden(scope)) return [{ ...at(seg, ctx), kind: "opaque", part: "program" }];
    return scan(scope.segments, { ...ctx, scope, lost, wrapped: ctx.wrapped || shell.at !== 0, stdin: stdinOf(seg, ctx) });
  }
  const name = found.at < 0 ? undefined : words[found.at];
  const reader = stdinShell(words, from, to);
  const input = reader === undefined ? undefined : stdinOf(seg, ctx);
  // A shell name a data command takes as an argument, as in `echo x | grep bash`, reads no program.
  const data = reader !== found.at && dataCommand(words, found);
  if (input !== undefined && !data && (input !== "unseen" || reader === found.at)) {
    return program(input, seg, ctx, { ...ctx, lost, wrapped: ctx.wrapped || found.at !== 0 });
  }
  if (name !== undefined && found.sure && isGh(name)) {
    const cmd = ghCommand({ ...seg, words: words.slice(found.at) }, { ...ctx, lost, known: !ctx.wrapped && found.at === 0 }, false);
    return cmd ? [cmd] : [];
  }
  if (!found.sure && found.at >= 0 && hidesShell(seg, found.at, ctx)) return [{ ...at(seg, ctx), kind: "opaque", part: "shell" }];
  const start = gh >= 0 ? gh : found.sure ? -1 : found.at;
  if (start < 0) return [];
  const cmd = ghCommand({ ...seg, words: words.slice(start) }, { ...ctx, lost, known: false }, true);
  return cmd ? [cmd] : [];
}
