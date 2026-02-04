# Finance Guru™ Distribution Plan
<!-- Version: 1.0 | Date: 2025-10-08 -->

> **Goal:** Transform Finance Guru™ into a standalone, installable package via npm/bun/pip

---

## 📋 Overview

This plan outlines the complete process to make Finance Guru™ available as:
- ✅ **npm package** - `npm install @finance-guru/core`
- ✅ **bun package** - `bun add @finance-guru/core`
- ✅ **pip package** - `pip install finance-guru`

---

## 🎯 Phase 1: Repository Restructuring

### 1.1 Create Standalone Repository

**New Repository Structure:**
```
finance-guru/
├── .github/
│   ├── workflows/
│   │   ├── npm-publish.yml
│   │   ├── pypi-publish.yml
│   │   └── test.yml
│   └── ISSUE_TEMPLATE/
├── src/
│   ├── agents/              # All agent files
│   ├── tasks/               # All task workflows
│   ├── templates/           # All templates
│   ├── data/                # Knowledge base
│   ├── checklists/          # Quality checklists
│   └── framework/           # Framework configs
├── cli/
│   ├── install.js           # Node.js installer
│   ├── install.py           # Python installer
│   └── commands/            # CLI commands
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/
│   ├── installation.md
│   ├── usage.md
│   ├── api.md
│   └── contributing.md
├── scripts/
│   ├── setup.sh
│   ├── validate.sh
│   └── publish.sh
├── package.json             # npm/bun config
├── pyproject.toml           # Python package config
├── setup.py                 # Python setup (legacy)
├── bun.lockb                # Bun lock file
├── README.md
├── LICENSE
├── CHANGELOG.md
├── .gitignore
└── .npmignore
```

**Action Items:**
- [ ] Create new GitHub repository: `finance-guru`
- [ ] Initialize with proper .gitignore
- [ ] Copy all module files to src/
- [ ] Create directory structure
- [ ] Set up README with badges

---

## 🎯 Phase 2: NPM/Bun Package Setup

### 2.1 Package Configuration (package.json)

**File:** `package.json`

```json
{
  "name": "@finance-guru/core",
  "version": "2.0.0",
  "description": "Institutional-grade multi-agent family office system for Claude AI",
  "main": "cli/install.js",
  "type": "module",
  "bin": {
    "finance-guru": "./cli/install.js",
    "fin-guru": "./cli/install.js"
  },
  "scripts": {
    "install": "node cli/install.js",
    "test": "bun test",
    "validate": "node scripts/validate.sh",
    "prepublishOnly": "npm run validate"
  },
  "keywords": [
    "finance",
    "ai-agents",
    "claude",
    "bmad",
    "family-office",
    "investment-analysis",
    "portfolio-management",
    "financial-planning"
  ],
  "author": "{user_name}",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/yourusername/finance-guru.git"
  },
  "bugs": {
    "url": "https://github.com/yourusername/finance-guru/issues"
  },
  "homepage": "https://github.com/yourusername/finance-guru#readme",
  "engines": {
    "node": ">=18.0.0",
    "bun": ">=1.0.0"
  },
  "files": [
    "src/",
    "cli/",
    "README.md",
    "LICENSE",
    "CHANGELOG.md"
  ],
  "dependencies": {
    "chalk": "^5.3.0",
    "commander": "^11.1.0",
    "inquirer": "^9.2.12",
    "ora": "^7.0.1",
    "fs-extra": "^11.2.0"
  },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "prettier": "^3.1.0",
    "eslint": "^8.55.0"
  },
  "publishConfig": {
    "access": "public"
  }
}
```

### 2.2 CLI Installer (install.js)

**File:** `cli/install.js`

```javascript
#!/usr/bin/env node

import { Command } from 'commander';
import inquirer from 'inquirer';
import chalk from 'chalk';
import ora from 'ora';
import fs from 'fs-extra';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const program = new Command();

program
  .name('finance-guru')
  .description('Finance Guru™ - Institutional-grade AI family office')
  .version('2.0.0');

program
  .command('install')
  .description('Install Finance Guru™ to your project')
  .option('-p, --path <path>', 'Installation path', './fin-guru')
  .option('-y, --yes', 'Skip prompts and use defaults')
  .action(async (options) => {
    console.log(chalk.cyan.bold('\n🎯 Finance Guru™ Installer\n'));

    let installPath = options.path;

    if (!options.yes) {
      const answers = await inquirer.prompt([
        {
          type: 'input',
          name: 'installPath',
          message: 'Where should Finance Guru™ be installed?',
          default: './fin-guru'
        },
        {
          type: 'confirm',
          name: 'confirm',
          message: 'Install Finance Guru™ to this location?',
          default: true
        }
      ]);

      if (!answers.confirm) {
        console.log(chalk.yellow('Installation cancelled.'));
        process.exit(0);
      }

      installPath = answers.installPath;
    }

    const spinner = ora('Installing Finance Guru™...').start();

    try {
      // Resolve paths
      const sourcePath = path.join(__dirname, '../src');
      const targetPath = path.resolve(installPath);

      // Create target directory
      await fs.ensureDir(targetPath);

      // Copy all files
      await fs.copy(sourcePath, targetPath, {
        overwrite: false,
        errorOnExist: false
      });

      spinner.succeed(chalk.green('Finance Guru™ installed successfully!'));

      console.log(chalk.cyan('\n📚 Next Steps:\n'));
      console.log(chalk.white('1. Load the Finance Orchestrator:'));
      console.log(chalk.gray(`   ${installPath}/agents/finance-orchestrator.md`));
      console.log(chalk.white('\n2. Type *help to see available commands'));
      console.log(chalk.white('\n3. Start with onboarding: *onboarding'));
      console.log(chalk.yellow('\n⚠️  Educational Only - Consult licensed advisors\n'));
    } catch (error) {
      spinner.fail(chalk.red('Installation failed'));
      console.error(chalk.red(error.message));
      process.exit(1);
    }
  });

program
  .command('list-agents')
  .description('List all available agents')
  .action(() => {
    console.log(chalk.cyan.bold('\n🤖 Finance Guru™ Agents:\n'));
    const agents = [
      '1. Finance Orchestrator - Master Coordinator',
      '2. Market Researcher - Intelligence Gathering',
      '3. Quant Analyst - Quantitative Modeling',
      '4. Strategy Advisor - Portfolio Planning',
      '5. Compliance Officer - Risk & Compliance',
      '6. Teaching Specialist - Financial Education',
      '7. Margin Specialist - Margin Trading',
      '8. Dividend Specialist - Income Optimization',
      '9. Onboarding Specialist - Client Profiling',
      '10. Builder - Document Creation',
      '11. QA Advisor - Quality Assurance',
      '12. Specialist - Base Template',
      '13. Agent Template - Creation Template'
    ];
    agents.forEach(agent => console.log(chalk.white(agent)));
    console.log();
  });

program
  .command('validate')
  .description('Validate Finance Guru™ installation')
  .option('-p, --path <path>', 'Installation path to validate')
  .action(async (options) => {
    const installPath = options.path || './fin-guru';
    const spinner = ora('Validating installation...').start();

    try {
      const required = [
        'agents',
        'tasks',
        'templates',
        'data',
        'config.yaml',
        'README.md'
      ];

      for (const item of required) {
        const itemPath = path.join(installPath, item);
        if (!await fs.pathExists(itemPath)) {
          throw new Error(`Missing required component: ${item}`);
        }
      }

      spinner.succeed(chalk.green('Installation is valid!'));
    } catch (error) {
      spinner.fail(chalk.red('Validation failed'));
      console.error(chalk.red(error.message));
      process.exit(1);
    }
  });

program.parse();
```

**Action Items:**
- [ ] Create package.json with all dependencies
- [ ] Implement CLI installer with inquirer prompts
- [ ] Add validate command
- [ ] Add list-agents command
- [ ] Test with npm and bun

---

## 🎯 Phase 3: Python Package Setup (pip)

### 3.1 Python Package Configuration

**File:** `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "finance-guru"
version = "2.0.0"
description = "Institutional-grade multi-agent family office system for Claude AI"
readme = "README.md"
authors = [
    {name = "{user_name}", email = "your.email@example.com"}
]
license = {text = "MIT"}
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Financial and Insurance Industry",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Office/Business :: Financial :: Investment",
]
keywords = ["finance", "ai-agents", "claude", "portfolio-management"]
dependencies = [
    "click>=8.1.0",
    "rich>=13.0.0",
    "pyyaml>=6.0.0",
]
requires-python = ">=3.9"

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
    "mypy>=1.0.0",
]

[project.urls]
Homepage = "https://github.com/yourusername/finance-guru"
Repository = "https://github.com/yourusername/finance-guru"
Documentation = "https://github.com/yourusername/finance-guru#readme"
"Bug Tracker" = "https://github.com/yourusername/finance-guru/issues"

[project.scripts]
finance-guru = "finance_guru.cli:main"
fin-guru = "finance_guru.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
finance_guru = [
    "agents/**/*.md",
    "tasks/**/*.md",
    "templates/**/*.md",
    "data/**/*",
    "checklists/**/*.md",
    "framework/**/*.yaml",
]
```

### 3.2 Python CLI Installer

**File:** `cli/install.py`

```python
#!/usr/bin/env python3
"""Finance Guru™ CLI Installer"""

import click
import os
import shutil
from pathlib import Path
from rich.console import Console
from rich.progress import Progress
from rich.prompt import Confirm, Prompt

console = Console()

@click.group()
@click.version_option(version="2.0.0")
def cli():
    """Finance Guru™ - Institutional-grade AI family office"""
    pass

@cli.command()
@click.option('--path', '-p', default='./fin-guru',
              help='Installation path')
@click.option('--yes', '-y', is_flag=True,
              help='Skip prompts and use defaults')
def install(path, yes):
    """Install Finance Guru™ to your project"""

    console.print("\n[cyan bold]🎯 Finance Guru™ Installer[/]\n")

    if not yes:
        install_path = Prompt.ask(
            "Where should Finance Guru™ be installed?",
            default=path
        )

        if not Confirm.ask(f"Install to [green]{install_path}[/]?"):
            console.print("[yellow]Installation cancelled.[/]")
            return
    else:
        install_path = path

    # Get package installation directory
    package_dir = Path(__file__).parent.parent / 'src'
    target_dir = Path(install_path).resolve()

    with Progress() as progress:
        task = progress.add_task(
            "[cyan]Installing Finance Guru™...",
            total=100
        )

        try:
            # Create target directory
            target_dir.mkdir(parents=True, exist_ok=True)
            progress.update(task, advance=20)

            # Copy files
            if package_dir.exists():
                shutil.copytree(
                    package_dir,
                    target_dir,
                    dirs_exist_ok=True
                )
            progress.update(task, advance=80)

            console.print("[green]✓ Finance Guru™ installed successfully![/]\n")

            console.print("[cyan]📚 Next Steps:[/]\n")
            console.print("1. Load the Finance Orchestrator:")
            console.print(f"   [gray]{install_path}/agents/finance-orchestrator.md[/]")
            console.print("\n2. Type *help to see available commands")
            console.print("\n3. Start with onboarding: *onboarding")
            console.print("\n[yellow]⚠️  Educational Only - Consult licensed advisors[/]\n")

        except Exception as e:
            console.print(f"[red]✗ Installation failed: {e}[/]")
            raise click.Abort()

@cli.command()
def list_agents():
    """List all available agents"""
    console.print("\n[cyan bold]🤖 Finance Guru™ Agents:[/]\n")

    agents = [
        "1. Finance Orchestrator - Master Coordinator",
        "2. Market Researcher - Intelligence Gathering",
        "3. Quant Analyst - Quantitative Modeling",
        "4. Strategy Advisor - Portfolio Planning",
        "5. Compliance Officer - Risk & Compliance",
        "6. Teaching Specialist - Financial Education",
        "7. Margin Specialist - Margin Trading",
        "8. Dividend Specialist - Income Optimization",
        "9. Onboarding Specialist - Client Profiling",
        "10. Builder - Document Creation",
        "11. QA Advisor - Quality Assurance",
        "12. Specialist - Base Template",
        "13. Agent Template - Creation Template"
    ]

    for agent in agents:
        console.print(f"  {agent}")
    console.print()

@cli.command()
@click.option('--path', '-p', help='Installation path to validate')
def validate(path):
    """Validate Finance Guru™ installation"""

    install_path = Path(path or './fin-guru')

    required = [
        'agents',
        'tasks',
        'templates',
        'data',
        'config.yaml',
        'README.md'
    ]

    console.print("[cyan]Validating installation...[/]")

    missing = []
    for item in required:
        item_path = install_path / item
        if not item_path.exists():
            missing.append(item)

    if missing:
        console.print(f"[red]✗ Validation failed[/]")
        console.print(f"[red]Missing: {', '.join(missing)}[/]")
        raise click.Abort()
    else:
        console.print("[green]✓ Installation is valid![/]")

def main():
    cli()

if __name__ == '__main__':
    main()
```

**File:** `setup.py` (Legacy support)

```python
from setuptools import setup, find_packages

setup(
    name="finance-guru",
    version="2.0.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=[
        "click>=8.1.0",
        "rich>=13.0.0",
        "pyyaml>=6.0.0",
    ],
    entry_points={
        "console_scripts": [
            "finance-guru=finance_guru.cli:main",
            "fin-guru=finance_guru.cli:main",
        ],
    },
)
```

**Action Items:**
- [ ] Create pyproject.toml
- [ ] Create setup.py for legacy support
- [ ] Implement Python CLI with Click and Rich
- [ ] Add package metadata
- [ ] Test with pip install

---

## 🎯 Phase 4: GitHub Actions CI/CD

### 4.1 NPM Publish Workflow

**File:** `.github/workflows/npm-publish.yml`

```yaml
name: Publish to NPM

on:
  release:
    types: [created]

jobs:
  publish-npm:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-node@v3
        with:
          node-version: '20.x'
          registry-url: 'https://registry.npmjs.org'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test

      - name: Publish to NPM
        run: npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

### 4.2 PyPI Publish Workflow

**File:** `.github/workflows/pypi-publish.yml`

```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  publish-pypi:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install build tools
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: Build package
        run: python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}
```

**Action Items:**
- [ ] Create GitHub Actions workflows
- [ ] Set up NPM_TOKEN secret
- [ ] Set up PYPI_API_TOKEN secret
- [ ] Test workflows
- [ ] Add status badges to README

---

## 🎯 Phase 5: Documentation

### 5.1 Installation Documentation

**File:** `docs/installation.md`

```markdown
# Installation Guide

## Quick Install

### NPM
```bash
npm install -g @finance-guru/core
finance-guru install
```

### Bun (Recommended)
```bash
bun add -g @finance-guru/core
finance-guru install
```

### Pip
```bash
pip install finance-guru
finance-guru install
```

## Custom Installation

### NPM/Bun
```bash
npm install @finance-guru/core
finance-guru install --path ./custom/path
```

### Pip
```bash
pip install finance-guru
finance-guru install --path ./custom/path
```

## Verification
```bash
finance-guru validate
```

## Next Steps
1. Load Finance Orchestrator
2. Run *help
3. Start onboarding
```

**Action Items:**
- [ ] Write installation.md
- [ ] Write usage.md
- [ ] Write api.md
- [ ] Write contributing.md
- [ ] Add examples

---

## 🎯 Phase 6: Testing & Validation

### 6.1 Test Scripts

**File:** `tests/integration/test_install.js`

```javascript
import { describe, it, expect, beforeAll, afterAll } from 'bun:test';
import fs from 'fs-extra';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

describe('Installation Tests', () => {
  const testPath = './test-install';

  afterAll(async () => {
    await fs.remove(testPath);
  });

  it('should install successfully', async () => {
    const { stdout } = await execAsync(
      `node cli/install.js install --path ${testPath} --yes`
    );

    expect(stdout).toContain('installed successfully');
    expect(await fs.pathExists(testPath)).toBe(true);
  });

  it('should validate installation', async () => {
    const { stdout } = await execAsync(
      `node cli/install.js validate --path ${testPath}`
    );

    expect(stdout).toContain('valid');
  });
});
```

**Action Items:**
- [ ] Write integration tests
- [ ] Write unit tests
- [ ] Set up test CI workflow
- [ ] Add test coverage reporting

---

## 🎯 Phase 7: Publishing Checklist

### 7.1 Pre-Publish

- [ ] All tests passing
- [ ] Documentation complete
- [ ] CHANGELOG updated
- [ ] Version bumped
- [ ] License file present
- [ ] README badges added

### 7.2 NPM Publish

```bash
# Login to NPM
npm login

# Publish
npm publish --access public
```

### 7.3 PyPI Publish

```bash
# Build
python -m build

# Upload
twine upload dist/*
```

### 7.4 Post-Publish

- [ ] Create GitHub release
- [ ] Announce on social media
- [ ] Update documentation links
- [ ] Monitor for issues

---

## 📊 Timeline Estimate

| Phase | Estimated Time | Priority |
|-------|---------------|----------|
| Phase 1: Repo Setup | 2-3 hours | High |
| Phase 2: NPM Setup | 3-4 hours | High |
| Phase 3: Python Setup | 3-4 hours | High |
| Phase 4: CI/CD | 2-3 hours | Medium |
| Phase 5: Documentation | 3-4 hours | High |
| Phase 6: Testing | 4-5 hours | Medium |
| Phase 7: Publishing | 1-2 hours | High |
| **Total** | **18-25 hours** | |

---

## 🎯 Success Metrics

**Installation:**
- [ ] `npm install @finance-guru/core` works
- [ ] `bun add @finance-guru/core` works
- [ ] `pip install finance-guru` works

**CLI:**
- [ ] `finance-guru install` works
- [ ] `finance-guru validate` works
- [ ] `finance-guru list-agents` works

**Quality:**
- [ ] All tests pass
- [ ] Documentation complete
- [ ] No installation errors
- [ ] Cross-platform compatibility

---

## 📝 Notes

- Start with npm/bun (JavaScript ecosystem more familiar for BMAD users)
- Python package adds accessibility for data scientists
- Keep installer simple and robust
- Prioritize user experience
- Maintain backward compatibility

---

**Next Step:** Execute Phase 1 - Create standalone repository structure
