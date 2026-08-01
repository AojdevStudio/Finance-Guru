#!/usr/bin/env node

import { readdir, readFile } from "node:fs/promises";
import { relative, resolve } from "node:path";

const wikiDirectory = process.argv[2];

if (!wikiDirectory) {
  console.error("Usage: bun run scripts/qa/validate-wiki-source.mjs <wiki-directory>");
  process.exit(1);
}

const wikiRoot = resolve(wikiDirectory);
const files = (await readdir(wikiRoot))
  .filter((file) => file.endsWith(".md"))
  .sort();
const contents = new Map(
  await Promise.all(
    files.map(async (file) => [file, await readFile(resolve(wikiRoot, file), "utf8")]),
  ),
);
const errors = [];
const pageFiles = files.filter((file) => !file.startsWith("_"));
const pageNames = new Set(pageFiles.map((file) => file.slice(0, -3)));
const navigationFiles = ["_Sidebar.md", "_Footer.md"];
const wikiLinkTargets = (content) =>
  new Set(
    [...content.matchAll(/\[\[([^\]|]+)(?:\|[^\]]+)?\]\]/g)].map(([, target]) =>
      target.trim().replace(/ /g, "-"),
    ),
  );
const proseWithoutFences = (content, file) => {
  const prose = [];
  let fence;

  for (const line of content.split("\n")) {
    if (!fence) {
      const opening = line.match(/^\s*(`{3,}|~{3,})/);
      if (opening) {
        fence = { character: opening[1][0], length: opening[1].length };
      } else {
        prose.push(line);
      }
      continue;
    }

    const closing = new RegExp(`^\\s*${fence.character}{${fence.length},}\\s*$`);
    if (closing.test(line)) fence = undefined;
  }

  if (fence) errors.push(`${file}: unbalanced fenced code blocks`);
  return prose.join("\n");
};
const isCredentialPlaceholder = (value) =>
  /^(?:your[-_]|example[-_]|placeholder[-_]|replace[-_]|redacted[-_]|<|\$\{|\{\{)/i.test(
    value.replace(/^["']|["'.,;:]+$/g, ""),
  );

for (const navigationFile of navigationFiles) {
  if (!contents.has(navigationFile)) {
    errors.push(`Missing required navigation file: ${navigationFile}`);
  }
}

for (const [file, content] of contents) {
  const prose = proseWithoutFences(content, file).replace(/`[^`]+`/g, "");
  const h1Count = [...prose.matchAll(/^# (?!#)/gm)].length;
  if (!file.startsWith("_") && h1Count !== 1) {
    errors.push(`${file}: expected exactly one H1, found ${h1Count}`);
  }

  const inlineLinks = prose.matchAll(/(?<!!)\[[^\]]+\]\(([^)]*)\)/g);
  for (const link of inlineLinks) {
    const destination = link[1].trim().split(/\s+/, 1)[0];
    if (!destination) {
      errors.push(`${file}: malformed inline Markdown link`);
      continue;
    }

    if (/^(?:https?:\/\/|mailto:|#)/i.test(destination)) continue;

    const target = relative(wikiRoot, resolve(wikiRoot, destination.split("#", 1)[0]));
    if (!contents.has(target)) {
      errors.push(`${file}: unresolved inline Markdown link ${destination}`);
    }
  }

  for (const match of prose.matchAll(/\[\[([^\]|]+)(?:\|[^\]]+)?\]\]/g)) {
    const target = match[1].trim().replace(/ /g, "-");
    if (!pageNames.has(target)) {
      errors.push(`${file}: unresolved Wiki link [[${match[1]}]]`);
    }
  }

  if (/\/Users\/|BEGIN (?:RSA |OPENSSH )?PRIVATE KEY/i.test(content)) {
    errors.push(`${file}: contains a possible private path or credential`);
  }
  for (const credential of content.matchAll(
    /(?:api[_-]?key|token|secret)\s*[:=]\s*([^\s`]+)/gi,
  )) {
    if (!isCredentialPlaceholder(credential[1])) {
      errors.push(`${file}: contains a possible private credential value`);
    }
  }
}

const sidebar = contents.get("_Sidebar.md") ?? "";
const sidebarTargets = wikiLinkTargets(sidebar);
for (const pageName of pageNames) {
  const expectedLink = `[[${pageName.replace(/-/g, " ")}]]`;
  if (!sidebarTargets.has(pageName)) {
    errors.push(`_Sidebar.md: missing page inventory link ${expectedLink}`);
  }
}

const footer = contents.get("_Footer.md") ?? "";
const footerTargets = wikiLinkTargets(footer);
for (const requiredLink of ["[[Privacy]]", "[[Wiki Maintenance]]"]) {
  const requiredTarget = requiredLink.slice(2, -2).replace(/ /g, "-");
  if (!footerTargets.has(requiredTarget)) {
    errors.push(`_Footer.md: missing required link ${requiredLink}`);
  }
}

if (errors.length > 0) {
  console.error("Wiki source validation failed:");
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}

console.log(`Wiki source validation passed for ${pageFiles.length} pages and ${navigationFiles.length} navigation files.`);
