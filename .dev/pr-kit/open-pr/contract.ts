/**
 * The PR body contract: the shape every pull request must have before it opens or merges.
 * Pure functions only, so the hook, the CLI, and CI all run the same rules.
 *
 * The body is five fixed sections in order, with nothing above the first one:
 *   Problem, Change, Proof, Review, Merge danger
 * and its last line names the model and harness: `Changes made by <model> via <harness>`.
 */

export const SECTIONS = ["Problem", "Change", "Proof", "Review", "Merge danger"] as const;
export type Section = (typeof SECTIONS)[number];

export type Door = "one-way" | "two-way";

export interface PullRequest {
  title?: string;
  body: string;
  draft?: boolean;
}

export type Rule =
  | "draft"
  | "title"
  | "preamble"
  | "section"
  | "proof"
  | "review"
  | "door"
  | "blast-radius"
  | "style"
  | "blurb";

export interface Violation {
  rule: Rule;
  message: string;
}

export type Verdict =
  | { ok: true; door: Door; blastRadius: string }
  | { ok: false; violations: Violation[] };

const TITLE = /^(?:\p{Extended_Pictographic}️?\s+)?(feat|fix|docs|test|chore|refactor|perf|ci|build|style|revert)(\([A-Za-z0-9][A-Za-z0-9/._-]*\))?!?: \S.*$/u;
const BLURB = /^Changes made by [^<\s].* via [^<\s].*$/;
const DOOR = /^Door:\s*(one-way|two-way)\b/i;
const BLAST = /^Blast radius:\s*([^\s.,]+)/i;
const DISPOSITION = /^(?:Fix|Decline)\b|^Defer #\d+\b/;
const MAX_WORDS = 25;
const MAX_PROBLEM_SENTENCES = 4;

const FENCE = /^ {0,3}(`{3,}|~{3,})(.*)$/;

/**
 * Marks each line that belongs to a fenced code block, fence lines included.
 * CommonMark rules: backticks or tildes, three or more, up to three spaces of indent.
 * Only the same character, at least as long as the opener, closes the block.
 * An unclosed block runs to the end of the text.
 */
function fenced(lines: string[]): boolean[] {
  let open: string | null = null;
  return lines.map((line) => {
    const m = line.match(FENCE);
    if (open === null) {
      if (!m || (m[1][0] === "`" && m[2].includes("`"))) return false;
      open = m[1];
      return true;
    }
    if (m && m[1][0] === open[0] && m[1].length >= open.length && !m[2].trim()) open = null;
    return true;
  });
}

/** Removes fenced code blocks, so prose rules never fire on code. */
function stripFences(text: string): string {
  const lines = text.split(/\r?\n/);
  const mask = fenced(lines);
  return lines.filter((_, i) => !mask[i]).join("\n");
}

/** Bold and italic markers would hide `Door:` from the line rules. */
function plain(line: string): string {
  return line.replace(/[*_`]/g, "").trim();
}

interface Parsed {
  preamble: string;
  sections: Array<{ heading: string; text: string }>;
}

function parse(body: string): Parsed {
  const out: Parsed = { preamble: "", sections: [] };
  const lines = body.split(/\r?\n/);
  const mask = fenced(lines);
  for (const [i, line] of lines.entries()) {
    const heading = !mask[i] && line.match(/^##\s+(.+?)\s*#*\s*$/);
    if (heading) {
      out.sections.push({ heading: heading[1], text: "" });
      continue;
    }
    const last = out.sections.at(-1);
    if (last) last.text += line + "\n";
    else out.preamble += line + "\n";
  }
  return out;
}

function sentences(text: string): string[] {
  return stripFences(text)
    .split("\n")
    .filter((l) => l.trim() && !/^\s*([|>#-]|\d+\.|!\[|<)/.test(l))
    .join(" ")
    .replace(/\b(e\.g|i\.e|etc|vs)\./gi, "$1")
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function words(sentence: string): number {
  return sentence.replace(/`[^`]*`/g, "x").split(/\s+/).filter(Boolean).length;
}

/** "No findings." passes only as the whole section. Anything else needs the table. */
function checkReview(text: string): Violation | null {
  if (text.trim() === "No findings.") return null;
  const rows = text.split("\n").filter((l) => l.trim().startsWith("|"));
  const header = rows[0]?.split("|").map((c) => c.trim().toLowerCase());
  const col = header?.indexOf("disposition") ?? -1;
  if (col < 0) {
    return {
      rule: "review",
      message: 'Review needs a table with a "Disposition" column, or "No findings." alone as the whole section after a real self-review.',
    };
  }
  const data = rows.slice(1).filter((r) => !/^\|?[\s:|-]+\|?$/.test(r.trim()));
  if (data.length === 0) return { rule: "review", message: "the Review table has no rows. Write \"No findings.\" when the review found nothing." };
  const bad = data.filter((r) => !DISPOSITION.test(r.split("|")[col]?.trim() ?? ""));
  if (bad.length > 0) {
    return { rule: "review", message: `each Review row starts its disposition with Fix, Decline, or Defer #<issue>. Bad row: ${bad[0].trim()}` };
  }
  return null;
}

/** The title rule alone, for an edit that changes only the title. */
export function titleViolation(title: string): Violation | null {
  if (TITLE.test(title.trim())) return null;
  return { rule: "title", message: `title ${JSON.stringify(title)} is not conventional-commit shaped, for example "fix(web): threads no longer spike CPU".` };
}

/** Checks one pull request against the contract. Every violation carries the fix in its message. */
// CodeRabbit appends its release notes inside these markers after the author's body.
const CODERABBIT_SUMMARY =
  /\n*<!-- This is an auto-generated comment: release notes by coderabbit\.ai -->[\s\S]*?<!-- end of auto-generated comment: release notes by coderabbit\.ai -->\n*/g;
const PR_LENS_DESCRIPTION = /\n*<!-- pr-lens:description -->[\s\S]*?<!-- \/pr-lens:description -->\n*/g;

export function checkPullRequest(input: PullRequest): Verdict {
  const pr = { ...input, body: input.body.replace(CODERABBIT_SUMMARY, "\n").replace(PR_LENS_DESCRIPTION, "\n") };
  const v: Violation[] = [];
  if (pr.draft) v.push({ rule: "draft", message: "drafts get no review-bot coverage. Open the PR ready for review." });
  const title = pr.title === undefined ? null : titleViolation(pr.title);
  if (title) v.push(title);

  const { preamble, sections } = parse(pr.body);
  if (preamble.trim() || (sections[0] && sections[0].heading.toLowerCase() !== "problem")) {
    v.push({ rule: "preamble", message: 'the body starts with "## Problem". Delete the text and headings above it.' });
  }

  const found = new Map<Section, string>();
  let cursor = -1;
  for (const name of SECTIONS) {
    const at = sections.findIndex((s, i) => i > cursor && s.heading.toLowerCase() === name.toLowerCase());
    if (at < 0) {
      const exists = sections.some((s) => s.heading.toLowerCase() === name.toLowerCase());
      v.push({ rule: "section", message: exists ? `"## ${name}" is out of order. The order is ${SECTIONS.join(", ")}.` : `"## ${name}" is missing.` });
      continue;
    }
    cursor = at;
    const text = sections[at].text;
    if (!text.trim()) v.push({ rule: "section", message: `"## ${name}" is empty.` });
    found.set(name, text);
  }

  const proof = found.get("Proof");
  if (proof?.trim() && !/^\s*\|.*\|/m.test(proof) && !fenced(proof.split("\n")).includes(true) && !/https?:\/\//.test(proof) && !/!\[/.test(proof)) {
    v.push({ rule: "proof", message: "Proof needs evidence that could fail: a before and after table, command output in a code block, or a screenshot or video link." });
  }

  const review = found.get("Review");
  if (review?.trim()) {
    const r = checkReview(review);
    if (r) v.push(r);
  }

  let door: Door | undefined;
  let blastRadius: string | undefined;
  const danger = found.get("Merge danger");
  if (danger !== undefined) {
    for (const line of danger.split("\n").map(plain)) {
      const d = line.match(DOOR)?.[1]?.toLowerCase();
      if (d === "one-way" || d === "two-way") door ??= d;
      blastRadius ??= line.match(BLAST)?.[1];
    }
    if (!door) v.push({ rule: "door", message: 'Merge danger needs a line "Door: one-way" or "Door: two-way".' });
    if (!blastRadius) v.push({ rule: "blast-radius", message: 'Merge danger needs a line "Blast radius: <one word>." followed by what outside the diff could break.' });
  }

  if (stripFences(pr.body).includes("—")) v.push({ rule: "style", message: "the body has an em dash. Use a period or a comma." });
  for (const name of ["Problem", "Merge danger"] as const) {
    const text = found.get(name);
    if (!text) continue;
    const s = sentences(text);
    const long = s.find((x) => words(x) > MAX_WORDS);
    if (long) v.push({ rule: "style", message: `a ${name} sentence has ${words(long)} words. The limit is ${MAX_WORDS}: "${long.slice(0, 80)}..."` });
    if (name === "Problem" && s.length > MAX_PROBLEM_SENTENCES) {
      v.push({ rule: "style", message: `Problem has ${s.length} sentences. State it in at most ${MAX_PROBLEM_SENTENCES}.` });
    }
  }

  const last = pr.body.split(/\r?\n/).map((l) => l.trim()).filter(Boolean).at(-1) ?? "";
  if (!BLURB.test(last)) v.push({ rule: "blurb", message: 'the last line is exactly "Changes made by <model> via <harness>", for example "Changes made by Claude Opus 5.5 via Claude Code".' });

  if (v.length > 0 || !door || !blastRadius) return { ok: false, violations: v };
  return { ok: true, door, blastRadius };
}

/** One message block for a refused PR, used by the hook and the CLI alike. */
export function formatViolations(violations: Violation[]): string {
  return violations.map((x) => `- [${x.rule}] ${x.message}`).join("\n");
}
