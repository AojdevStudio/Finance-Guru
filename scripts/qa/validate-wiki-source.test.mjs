import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const validator = "scripts/qa/validate-wiki-source.mjs";
const navigation = `[[Home]]\n[[Privacy]]\n[[Wiki Maintenance]]\n`;
const pages = {
  "Privacy.md": "# Privacy\n",
  "Wiki-Maintenance.md": "# Wiki Maintenance\n",
  "_Sidebar.md": navigation,
  "_Footer.md": "[[Privacy]] [[Wiki Maintenance]]\n",
};

async function fixture(home) {
  const directory = await mkdtemp(join(tmpdir(), "finance-guru-wiki-test-"));
  await Promise.all([
    writeFile(join(directory, "Home.md"), home),
    ...Object.entries(pages).map(([file, content]) =>
      writeFile(join(directory, file), content),
    ),
  ]);
  return directory;
}

function validate(directory) {
  try {
    execFileSync("bun", ["run", validator, directory], { encoding: "utf8" });
    return { status: 0, output: "" };
  } catch (error) {
    return { status: error.status, output: `${error.stdout ?? ""}${error.stderr ?? ""}` };
  }
}

const accepted = await fixture(`# Home

API_KEY=your-api-key

\`\`\`python
# not a page heading
[[Not A Page]]
API_KEY=real-value-in-example
\`\`\`
`);
const rejectedCredential = await fixture("# Home\n\nAPI_KEY=real-secret-value\n");
const rejectedFence = await fixture("# Home\n\n~~~~\nnot closed\n");

try {
  assert.equal(validate(accepted).status, 0, "placeholder and code examples should pass");
  const credentialResult = validate(rejectedCredential);
  assert.notEqual(credentialResult.status, 0, "real credential values must fail");
  assert.match(credentialResult.output, /private credential value/);
  const fenceResult = validate(rejectedFence);
  assert.notEqual(fenceResult.status, 0, "unbalanced tilde fences must fail");
  assert.match(fenceResult.output, /unbalanced fenced code blocks/);
} finally {
  await Promise.all([accepted, rejectedCredential, rejectedFence].map((dir) => rm(dir, { recursive: true, force: true })));
}

console.log("Wiki source validator regression tests passed.");
