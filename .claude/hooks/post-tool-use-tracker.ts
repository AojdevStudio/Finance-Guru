#!/usr/bin/env bun

import { existsSync, mkdirSync, appendFileSync, readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

interface ToolInput {
  file_path?: string;
}

interface HookInput {
  tool_name: string;
  tool_input: ToolInput;
  session_id?: string;
}

function getProjectRoot(): string {
  return process.env.CLAUDE_PROJECT_DIR || process.cwd();
}

const TOP_LEVEL_REPOS: ReadonlySet<string> = new Set([
  'frontend', 'client', 'web', 'app', 'ui',
  'backend', 'server', 'api', 'src', 'services',
  'database', 'prisma', 'migrations',
]);

const NESTED_REPO_PARENTS: ReadonlySet<string> = new Set(['packages', 'examples']);

function detectRepo(filePath: string, projectRoot: string): string {
  const relativePath = filePath.replace(projectRoot + '/', '');
  const [firstDir, secondDir] = relativePath.split('/');

  if (TOP_LEVEL_REPOS.has(firstDir)) {
    return firstDir;
  }
  if (NESTED_REPO_PARENTS.has(firstDir)) {
    return secondDir ? `${firstDir}/${secondDir}` : firstDir;
  }
  return relativePath.includes('/') ? 'unknown' : 'root';
}

function getBuildCommand(repo: string, projectRoot: string): string {
  const repoPath = join(projectRoot, repo);
  const packageJsonPath = join(repoPath, 'package.json');

  if (existsSync(packageJsonPath)) {
    const packageJson = JSON.parse(readFileSync(packageJsonPath, 'utf-8'));
    if (packageJson.scripts && packageJson.scripts.build) {
      if (existsSync(join(repoPath, 'pnpm-lock.yaml'))) {
        return `cd ${repoPath} && pnpm build`;
      }
      if (existsSync(join(repoPath, 'yarn.lock'))) {
        return `cd ${repoPath} && yarn build`;
      }
      return `cd ${repoPath} && npm run build`;
    }
  }

  if (repo === 'database' || repo.includes('prisma')) {
    if (existsSync(join(repoPath, 'schema.prisma')) ||
        existsSync(join(repoPath, 'prisma', 'schema.prisma'))) {
      return `cd ${repoPath} && npx prisma generate`;
    }
  }

  return '';
}

function getTscCommand(repo: string, projectRoot: string): string {
  const repoPath = join(projectRoot, repo);
  const tsconfigPath = join(repoPath, 'tsconfig.json');

  if (existsSync(tsconfigPath)) {
    if (existsSync(join(repoPath, 'tsconfig.app.json'))) {
      return `cd ${repoPath} && npx tsc --project tsconfig.app.json --noEmit`;
    } else {
      return `cd ${repoPath} && npx tsc --noEmit`;
    }
  }

  return '';
}

function main() {
  let inputData = '';
  process.stdin.setEncoding('utf-8');
  process.stdin.on('data', chunk => {
    inputData += chunk;
  });
  process.stdin.on('end', () => {
    processHook(inputData);
  });
}

function processHook(inputData: string) {
  try {
    const toolInfo: HookInput = JSON.parse(inputData);
    const projectRoot = getProjectRoot();

    const toolName = toolInfo.tool_name;
    const filePath = toolInfo.tool_input?.file_path;
    const sessionId = toolInfo.session_id || 'default';

    if (!['Edit', 'MultiEdit', 'Write'].includes(toolName) || !filePath) {
      process.exit(0);
    }

    if (filePath.match(/\.(md|markdown)$/)) {
      process.exit(0);
    }

    const cacheDir = join(projectRoot, '.claude', 'tsc-cache', sessionId);
    mkdirSync(cacheDir, { recursive: true });

    const repo = detectRepo(filePath, projectRoot);

    if (repo === 'unknown' || !repo) {
      process.exit(0);
    }

    const timestamp = Math.floor(Date.now() / 1000);
    const logEntry = `${timestamp}:${filePath}:${repo}\n`;
    appendFileSync(join(cacheDir, 'edited-files.log'), logEntry);

    const affectedReposPath = join(cacheDir, 'affected-repos.txt');
    const existingRepos = existsSync(affectedReposPath)
      ? readFileSync(affectedReposPath, 'utf-8').split('\n').filter(r => r.length > 0)
      : [];

    if (!existingRepos.includes(repo)) {
      appendFileSync(affectedReposPath, `${repo}\n`);
    }

    const commandsTmpPath = join(cacheDir, 'commands.txt.tmp');
    const buildCmd = getBuildCommand(repo, projectRoot);
    const tscCmd = getTscCommand(repo, projectRoot);

    if (buildCmd) {
      appendFileSync(commandsTmpPath, `${repo}:build:${buildCmd}\n`);
    }

    if (tscCmd) {
      appendFileSync(commandsTmpPath, `${repo}:tsc:${tscCmd}\n`);
    }

    if (existsSync(commandsTmpPath)) {
      const commands = readFileSync(commandsTmpPath, 'utf-8')
        .split('\n')
        .filter(cmd => cmd.length > 0);

      const uniqueCommands = [...new Set(commands)].sort().join('\n') + '\n';
      writeFileSync(join(cacheDir, 'commands.txt'), uniqueCommands);
    }

    process.exit(0);

  } catch (err) {
    console.error(`post-tool-use-tracker: ${err instanceof Error ? err.message : String(err)}`);
    process.exit(0);
  }
}

main();
