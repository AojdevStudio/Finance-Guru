#!/usr/bin/env bun

import { spawn } from 'bun';
import { fileURLToPath } from 'url';

export async function main(args = process.argv.slice(2)): Promise<number> {
  const repoRoot = fileURLToPath(new URL('../../', import.meta.url));
  const child = spawn([
    'uv', 'run', '--project', repoRoot, 'python', '-m', 'src.cli.onboarding_wizard',
    ...args.filter(arg => arg !== '--resume'),
  ], { stdin: 'inherit', stdout: 'inherit', stderr: 'inherit' });
  return child.exited;
}

if (import.meta.main) process.exit(await main());
