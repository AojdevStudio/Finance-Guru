/**
 * Where a command runs and which file bytes gh reads, as far as a static read of the command can prove it.
 * command.ts reads the words. This module finds a simple command's head after prefixes, decides what a cd
 * does to the directory and what a merge leaves to the environment, and names the file each read opens.
 * Pure: it never reads files. The gate reads the files this module names.
 */

import { posix } from "node:path";

export type BodySource =
  /**
   * `expands`: text the shell changes before gh reads it, so `text` is not what gh sends. `written`: the absolute name of
   * the file a `cat > f <<'EOF'` puts this text in, when gh reads it back from there.
   */
  | { kind: "inline"; text: string; expands?: true; written?: string }
  /** `chomp`: read through `$(cat f)`, which drops the file's trailing newlines. */
  | { kind: "file"; path: string; chomp?: true }
  | { kind: "missing" };

/** Where a command runs, as far as the parser can follow it. */
export interface Where {
  /** The hook's directory and home, so file names resolve to absolute ones. `cdpath`: CDPATH is set, so a bare relative cd can go elsewhere. */
  base: { cwd: string; home: string; cdpath: boolean };
  /** The directory literal cds led to, relative to the hook's. */
  dir?: string;
  /** A cd, pushd, popd, source, or eval changed the directory in a way the parser does not follow. */
  lost?: boolean;
}

/** The file the one `cat > f <<'EOF'` before a PR command writes: its absolute name and the heredoc's text. */
export interface Written {
  key: string;
  source: BodySource;
}

/** What gh reads for `-F key=@path` once the shell gives the path: stdin for `-`, and the file this command writes before gh runs. */
export interface AtFiles {
  stdin: BodySource;
  written?: Written;
  where: Where;
}

/**
 * The absolute name of `path` where a command runs. Undefined for a relative path in a directory the parser
 * lost, and for a path with `..`, which the OS resolves through symlinks, not by its spelling.
 */
export function fileKey(path: string, where: Where): string | undefined {
  const { cwd, home } = where.base;
  const abs = (p: string, from: string): string => (p.startsWith("/") ? p : p === "~" || p.startsWith("~/") ? home + p.slice(1) : posix.join(from, p));
  if ((where.lost && !/^[/~]/.test(path)) || path.split("/").includes("..")) return undefined;
  return posix.normalize(abs(path, abs(where.dir ?? ".", cwd)));
}

/** The file gh reads: the heredoc's text when this command writes it by the same name first, else the file on disk. */
export function readFile(path: string, written: Written | undefined, where: Where): BodySource {
  const key = fileKey(path, where);
  return written !== undefined && key === written.key ? written.source : { kind: "file", path };
}

/** The text gh sends for an `@path` value. The shell does not touch text a substitution gives, so a leading `~` is a relative name. */
export function atSource(path: string, at: AtFiles): BodySource {
  if (path === "-") return at.stdin;
  return readFile(path.startsWith("~") ? "./" + path : path, at.written, at.where);
}

/** Variables that change where gh reads files, which repo it picks, or which host and config it uses. */
export const CONTEXT = ["HOME", "GH_REPO", "GH_HOST", "GH_CONFIG_DIR", "XDG_CONFIG_HOME", "CDPATH"];
const HOST_CONTEXT = ["*", "HOME", "GH_HOST", "GH_CONFIG_DIR", "XDG_CONFIG_HOME"];
/** Builtins and commands that set variables, and ones that run shell code the parser does not read. */
export const SETTERS = ["export", "declare", "typeset", "local", "readonly", "read", "unset", "env", "getopts", "mapfile", "readarray"];
export const RUNS_CODE = ["eval", "source", "."];
/** A shell variable assignment word, `NAME=value`. */
export const ASSIGN = /^[A-Za-z_]\w*=/;

/** What a merge leaves to the environment: the host and config, or the repo or PR when it takes them from a directory the gate cannot know. */
export function drift(names: Set<string>, needsCwd: boolean, url: boolean, at: { known?: boolean; lost?: boolean }): "repo" | "host" | undefined {
  if (!url && HOST_CONTEXT.some((n) => names.has(n))) return "host";
  return needsCwd && (!at.known || at.lost) ? "repo" : undefined;
}

/** Words after which bash still reads a command name in this shell: reserved words, `builtin`, `command`, and `time`. */
export const KEYWORDS = ["!", "{", "if", "then", "else", "elif", "do", "while", "until", "time", "builtin", "command"];
const KEYWORD_FLAGS: Record<string, string[]> = { time: ["-p"], command: ["-p", "-v", "-V"] };

/** Wrappers that run the command as their own child: options that take a value, ones that do not, and words before the command. */
const WRAPPERS: Record<string, { valued: string[]; flags: string[]; positional: number; split?: true }> = {
  env: { valued: ["-u", "--unset", "-C", "--chdir"], flags: ["-i", "-0", "-v", "--ignore-environment", "--null", "--debug"], positional: 0, split: true },
  nohup: { valued: [], flags: [], positional: 0 },
  timeout: { valued: ["-k", "--kill-after", "-s", "--signal"], flags: ["--preserve-status", "--foreground", "-v", "--verbose"], positional: 1 },
  nice: { valued: ["-n", "--adjustment"], flags: [], positional: 0 },
  exec: { valued: ["-a"], flags: ["-c", "-l"], positional: 0 },
};

/** The command a simple command runs, after its assignments, keywords, and wrappers. */
export interface Head {
  /** The command word's index, or -1 for a command of assignments only. */
  at: number;
  /** Words came before it. */
  prefixed: boolean;
  /** A wrapper changes the directory it runs in (`env -C`). */
  chdir: boolean;
  /** Every prefix and option was read, and the command word is fixed text. */
  sure: boolean;
  /** A wrapper splits text into the command it runs by rules the gate does not read, as `env -S` does. */
  split?: true;
}

/** env's long options as GNU getopt reads them, by any unique prefix, and whether each takes the next word as its value. */
const ENV_LONG: Record<string, boolean> = { "--unset": true, "--chdir": true, "--ignore-environment": false, "--null": false, "--debug": false };

/** Whether env's options up to its first operand can turn on -S, or hold one the gate does not know, read as getopt reads them. */
function envSplits(words: string[], from: number): boolean {
  for (let i = from; i < words.length && words[i].startsWith("-") && words[i] !== "--"; i++) {
    const word = words[i];
    if (word.startsWith("--")) {
      const [name, value] = [word.split("=")[0], word.includes("=")];
      const known = Object.keys(ENV_LONG).filter((long) => long.startsWith(name));
      if (known.length !== 1) return true;
      if (ENV_LONG[known[0]] && !value) i++;
      continue;
    }
    const cluster = /^-[iv0]*(?:([uC])(.*))?$/.exec(word);
    if (!cluster) return true;
    if (cluster[1] && cluster[2] === "") i++;
  }
  return false;
}

/** Finds the command head. A prefix option the table does not know, or a command word the shell computes, leaves it unsure. */
export function head(words: string[], computed: (word: string) => boolean): Head {
  const found: Head = { at: -1, prefixed: false, chdir: false, sure: true };
  let i = 0;
  for (;;) {
    while (i < words.length && ASSIGN.test(words[i])) i++;
    const word = words[i];
    if (word === undefined) return { ...found, prefixed: found.prefixed || i > 0 };
    found.prefixed ||= i > 0;
    if (computed(word)) return { ...found, at: i, sure: false };
    const wrapper = WRAPPERS[word.replace(/^.*\//, "")];
    if (wrapper?.split && envSplits(words, i + 1)) return { ...found, at: i, sure: false, split: true };
    if (!wrapper && !KEYWORDS.includes(word)) return { ...found, at: i };
    found.prefixed = true;
    const valued = wrapper?.valued ?? [];
    const flags = wrapper?.flags ?? KEYWORD_FLAGS[word] ?? [];
    for (i++; i < words.length && /^-./.test(words[i]); i++) {
      const name = words[i].split("=")[0];
      if (words[i] === "--") {
        i++;
        break;
      }
      if (valued.includes(name)) {
        found.chdir ||= name === "-C" || name === "--chdir";
        if (!words[i].includes("=")) i++;
      } else if (!flags.includes(words[i])) return { ...found, at: i, sure: false };
    }
    i += wrapper?.positional ?? 0;
  }
}

/** What a command does to the directory of the shell it runs in. */
export type Move = { kind: "follow"; to: string } | { kind: "keep" } | { kind: "lose" };

/**
 * What a cd does to the directory. Only `cd <dir>` with nothing around it, which the shell surely runs, is followed.
 * A relative name that does not start with `.` or `..` goes through CDPATH when it is set, so it is lost then. Any
 * other cd loses the directory. Any other command keeps it, since one that can change it crowds any later PR write that
 * reads a file, and any later merge.
 */
export function move(words: string[], found: Head, always: boolean, place: (word: string) => string | undefined, cdpath: boolean): Move {
  if (found.at < 0 || !found.sure || words[found.at] !== "cd") return { kind: "keep" };
  const to = always && !found.prefixed && words.length === 2 ? place(words[1]) : undefined;
  return to !== undefined && !to.startsWith("-") && (/^(?:[/~]|\.\.?(?:\/|$))/.test(to) || !cdpath) ? { kind: "follow", to } : { kind: "lose" };
}
