/**
 * Integration Test: Gitignore Protection
 * Verifies that sensitive financial data is properly ignored by git
 */

import { describe, test, expect, beforeEach, afterEach } from "bun:test";
import { existsSync, rmSync, mkdirSync, writeFileSync } from "fs";
import { join } from "path";
import { spawnSync } from "bun";

const PROJECT_ROOT = process.cwd();
const TEST_DIR = join("/tmp", `finance-guru-gitignore-test-${Date.now()}`);

describe("Gitignore Protection Integration Test", () => {
  beforeEach(async () => {
    // Create fresh test directory
    if (existsSync(TEST_DIR)) {
      rmSync(TEST_DIR, { recursive: true, force: true });
    }
    mkdirSync(TEST_DIR, { recursive: true });

    // Initialize git repository
    spawnSync(["git", "init", "-q"], { cwd: TEST_DIR });

    // Copy .gitignore from project root
    const gitignorePath = join(PROJECT_ROOT, ".gitignore");
    if (!existsSync(gitignorePath)) {
      throw new Error(".gitignore not found in project root");
    }
    const gitignoreContent = await Bun.file(gitignorePath).text();
    writeFileSync(join(TEST_DIR, ".gitignore"), gitignoreContent);
  });

  afterEach(() => {
    // Clean up test directory
    if (existsSync(TEST_DIR)) {
      rmSync(TEST_DIR, { recursive: true, force: true });
    }
  });

  test("CSV files are ignored", () => {
    // Create directory structure
    mkdirSync(join(TEST_DIR, "notebooks/updates"), { recursive: true });
    mkdirSync(join(TEST_DIR, "notebooks/retirement-accounts"), { recursive: true });
    mkdirSync(join(TEST_DIR, "notebooks/transactions"), { recursive: true });
    mkdirSync(join(TEST_DIR, "fin-guru-private/fin-guru/analysis"), { recursive: true });

    // Create test CSV files
    const csvFiles = [
      "notebooks/updates/Portfolio_Positions_Jan-12-2026.csv",
      "notebooks/updates/dividend.csv",
      "notebooks/retirement-accounts/OfxDownload.csv",
      "notebooks/transactions/History_for_Account_EXAMPLE123.csv",
      "fin-guru-private/fin-guru/analysis/watchlist.csv"
    ];

    csvFiles.forEach(file => {
      const filePath = join(TEST_DIR, file);
      writeFileSync(filePath, "Date,Ticker,Shares,Price,Value\n2026-01-12,TSLA,100,350.00,35000.00\n");
    });

    // Verify all CSV files are ignored
    csvFiles.forEach(file => {
      const result = spawnSync(["git", "check-ignore", "-q", file], { cwd: TEST_DIR });
      expect(result.exitCode).toBe(0);
    });
  });

  test("environment files are ignored", () => {
    const envFiles = [".env", ".env.local", "credentials.env"];

    envFiles.forEach(file => {
      const filePath = join(TEST_DIR, file);
      writeFileSync(filePath, "API_KEY=secret123456\n");
    });

    // Verify all environment files are ignored
    envFiles.forEach(file => {
      const result = spawnSync(["git", "check-ignore", "-q", file], { cwd: TEST_DIR });
      expect(result.exitCode).toBe(0);
    });
  });

  test("fin-guru-private directory is ignored", () => {
    mkdirSync(join(TEST_DIR, "fin-guru-private/fin-guru/analysis"), { recursive: true });
    mkdirSync(join(TEST_DIR, "fin-guru-private/fin-guru/strategies"), { recursive: true });

    const privateFiles = [
      "fin-guru-private/fin-guru/analysis/watchlist.csv",
      "fin-guru-private/fin-guru/strategies/buy-ticket-2026-01-12.md"
    ];

    privateFiles.forEach(file => {
      const filePath = join(TEST_DIR, file);
      writeFileSync(filePath, "# Sensitive Financial Analysis\n");
    });

    // Verify private files are ignored
    privateFiles.forEach(file => {
      const result = spawnSync(["git", "check-ignore", "-q", file], { cwd: TEST_DIR });
      expect(result.exitCode).toBe(0);
    });
  });

  test("notebooks directory is ignored", () => {
    const notebookDirs = [
      "notebooks/updates",
      "notebooks/retirement-accounts",
      "notebooks/transactions"
    ];

    notebookDirs.forEach(dir => {
      mkdirSync(join(TEST_DIR, dir), { recursive: true });
      const testFile = join(TEST_DIR, dir, "test.csv");
      writeFileSync(testFile, "test data\n");
    });

    // Verify notebook directories are ignored
    notebookDirs.forEach(dir => {
      const result = spawnSync(["git", "check-ignore", "-q", dir], { cwd: TEST_DIR });
      expect(result.exitCode).toBe(0);
    });
  });

  test("user profile is ignored", () => {
    mkdirSync(join(TEST_DIR, "fin-guru/data"), { recursive: true });
    const userProfilePath = join(TEST_DIR, "fin-guru/data/user-profile.yaml");
    writeFileSync(userProfilePath, `user:
  name: Test User
  risk_tolerance: moderate
assets:
  liquid: 100000
  investments: 500000
`);

    const result = spawnSync(["git", "check-ignore", "-q", "fin-guru/data/user-profile.yaml"], { cwd: TEST_DIR });
    expect(result.exitCode).toBe(0);
  });

  test("research directory is ignored", () => {
    mkdirSync(join(TEST_DIR, "research/finance"), { recursive: true });
    const researchFile = join(TEST_DIR, "research/finance/tsla-analysis.md");
    writeFileSync(researchFile, "# Market Analysis - TSLA\n");

    const result = spawnSync(["git", "check-ignore", "-q", "research/finance/tsla-analysis.md"], { cwd: TEST_DIR });
    expect(result.exitCode).toBe(0);
  });

  test("private/sensitive/credentials directories are ignored", () => {
    mkdirSync(join(TEST_DIR, "private"), { recursive: true });
    mkdirSync(join(TEST_DIR, "sensitive"), { recursive: true });
    mkdirSync(join(TEST_DIR, "credentials"), { recursive: true });

    const privateDirFiles = [
      "private/account-details.txt",
      "sensitive/portfolio.txt",
      "credentials/fidelity.key"
    ];

    privateDirFiles.forEach(file => {
      const filePath = join(TEST_DIR, file);
      writeFileSync(filePath, "sensitive data\n");
    });

    // Verify private directory files are ignored
    privateDirFiles.forEach(file => {
      const result = spawnSync(["git", "check-ignore", "-q", file], { cwd: TEST_DIR });
      expect(result.exitCode).toBe(0);
    });
  });

  test(".gitignore itself is tracked", () => {
    // Add .gitignore to git
    spawnSync(["git", "add", ".gitignore"], { cwd: TEST_DIR });

    // Verify .gitignore is tracked
    const result = spawnSync(["git", "ls-files", "--error-unmatch", ".gitignore"], { cwd: TEST_DIR });
    expect(result.exitCode).toBe(0);
  });

  test("git status shows no sensitive files", () => {
    // Create all types of sensitive files
    mkdirSync(join(TEST_DIR, "notebooks/updates"), { recursive: true });
    mkdirSync(join(TEST_DIR, "fin-guru-private/fin-guru/analysis"), { recursive: true });
    mkdirSync(join(TEST_DIR, "research/finance"), { recursive: true });
    mkdirSync(join(TEST_DIR, "private"), { recursive: true });

    writeFileSync(join(TEST_DIR, "notebooks/updates/portfolio.csv"), "data\n");
    writeFileSync(join(TEST_DIR, ".env"), "SECRET=key\n");
    writeFileSync(join(TEST_DIR, "fin-guru-private/fin-guru/analysis/report.csv"), "data\n");
    writeFileSync(join(TEST_DIR, "research/finance/analysis.md"), "# Analysis\n");
    writeFileSync(join(TEST_DIR, "private/data.txt"), "sensitive\n");

    // Try to add all files
    spawnSync(["git", "add", "-A"], { cwd: TEST_DIR });

    // Get tracked files
    const result = spawnSync(["git", "ls-files"], { cwd: TEST_DIR });
    const trackedFiles = result.stdout?.toString() || "";

    // Verify no sensitive patterns are tracked
    expect(trackedFiles).not.toMatch(/\.(csv|env)$/);
    expect(trackedFiles).not.toMatch(/notebooks\//);
    expect(trackedFiles).not.toMatch(/fin-guru-private\//);
    expect(trackedFiles).not.toMatch(/research\//);
    expect(trackedFiles).not.toMatch(/private\//);
    expect(trackedFiles).not.toMatch(/sensitive\//);
    expect(trackedFiles).not.toMatch(/credentials\//);
  });

  test("beads tracking data is ignored", () => {
    mkdirSync(join(TEST_DIR, ".beads"), { recursive: true });

    const beadsFiles = [
      ".beads/issues.jsonl",
      ".beads/interactions.jsonl"
    ];

    beadsFiles.forEach(file => {
      const filePath = join(TEST_DIR, file);
      writeFileSync(filePath, '{"id":"test-1"}\n');
    });

    // Verify beads files are ignored
    beadsFiles.forEach(file => {
      const result = spawnSync(["git", "check-ignore", "-q", file], { cwd: TEST_DIR });
      expect(result.exitCode).toBe(0);
    });
  });

  test("all sensitive file types are protected", () => {
    // Create comprehensive test structure
    const sensitiveStructure = {
      "notebooks/updates/Portfolio_Positions.csv": "portfolio data",
      "notebooks/retirement-accounts/401k.csv": "retirement data",
      "notebooks/transactions/history.csv": "transaction data",
      "fin-guru-private/fin-guru/strategies/buy-ticket.md": "strategy",
      "fin-guru/data/user-profile.yaml": "user profile",
      "research/finance/analysis.md": "research",
      "private/secrets.txt": "secrets",
      "sensitive/data.txt": "sensitive",
      "credentials/api.key": "api key",
      ".env": "env vars",
      ".beads/issues.jsonl": "beads data"
    };

    // Create all files
    Object.entries(sensitiveStructure).forEach(([path, content]) => {
      const dir = join(TEST_DIR, path.split("/").slice(0, -1).join("/"));
      mkdirSync(dir, { recursive: true });
      writeFileSync(join(TEST_DIR, path), content);
    });

    // Verify ALL are ignored
    Object.keys(sensitiveStructure).forEach(path => {
      const result = spawnSync(["git", "check-ignore", "-q", path], { cwd: TEST_DIR });
      expect(result.exitCode).toBe(0);
    });
  });
});

describe("Gitignore Coverage Verification", () => {
  test(".gitignore file exists in project root", () => {
    const gitignorePath = join(PROJECT_ROOT, ".gitignore");
    expect(existsSync(gitignorePath)).toBe(true);
  });

  test(".gitignore contains all required patterns", async () => {
    const gitignorePath = join(PROJECT_ROOT, ".gitignore");
    const gitignoreContent = await Bun.file(gitignorePath).text();

    const requiredPatterns = [
      "*.csv",
      ".env",
      "*.env",
      "private/",
      "sensitive/",
      "credentials/",
      "notebooks/",
      "fin-guru-private/",
      "fin-guru/data/user-profile.yaml",
      "research/",
      ".beads/issues.jsonl",
      ".beads/interactions.jsonl"
    ];

    requiredPatterns.forEach(pattern => {
      expect(gitignoreContent).toContain(pattern);
    });
  });
});
