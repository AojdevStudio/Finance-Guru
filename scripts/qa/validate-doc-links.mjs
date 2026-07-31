#!/usr/bin/env node

import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, relative, resolve } from "node:path";

const root = process.cwd();
const roots = ["README.md", "RELEASE_NOTES.md", "PRIVACY.md", "docs"];
const markdownLink = /!?\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)/g;
const ignoredPrefix = /^(?:[a-z][a-z0-9+.-]*:|#|\/)/i;

function markdownFiles(path) {
  const absolute = resolve(root, path);
  if (statSync(absolute).isFile()) return [absolute];
  return readdirSync(absolute, { withFileTypes: true }).flatMap((entry) => {
    const child = relative(root, resolve(absolute, entry.name));
    if (entry.isDirectory()) return markdownFiles(child);
    return entry.name.endsWith(".md") ? [resolve(absolute, entry.name)] : [];
  });
}

const failures = [];
for (const file of roots.flatMap(markdownFiles)) {
  const text = readFileSync(file, "utf8");
  for (const match of text.matchAll(markdownLink)) {
    const target = match[1].replace(/^<|>$/g, "");
    if (ignoredPrefix.test(target)) continue;
    const pathname = decodeURIComponent(target.split(/[?#]/, 1)[0]);
    const resolved = resolve(dirname(file), pathname);
    if (!existsSync(resolved)) {
      const line = text.slice(0, match.index).split("\n").length;
      failures.push(`${relative(root, file)}:${line} -> ${target}`);
    }
  }
}

if (failures.length > 0) {
  console.error("Broken repository-relative documentation links:");
  console.error(failures.join("\n"));
  process.exit(1);
}

console.log("Repository-relative documentation links are valid.");
