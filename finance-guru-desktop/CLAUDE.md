# Finance Guru Desktop

Electron desktop GUI for the family-office Python analysis engine.

## Build & Run

```bash
bun install            # First time only
bun run start          # Build renderer + launch app
bun run start:dev      # With DevTools open
bun run watch          # Auto-rebuild renderer on changes
bun run build:renderer # Build renderer only
```

## Tests

```bash
bun test               # Run all tests
bun test --watch       # Watch mode
```

## Architecture

- **Main process** (`main.js`): Electron bootstrap, IPC handlers
- **Preload** (`preload.js`): Narrow IPC bridge (app, analysis, csv, chat)
- **Renderer** (`renderer.js`): Bundled by esbuild -> `dist/renderer.bundle.js`
- **Python bridge**: `src/main/ipc/analysis.ipc.js` spawns `family-office/.venv/bin/python3`
- **State**: Observable pattern in `src/renderer/state/State.js`
- **Runtime config**: `src/main/config/runtimePaths.js` and `validateRuntime.js`
- **Commands**: Registry at `src/renderer/commands/registry.js` (V1 allowlisted tools only)

## Key Paths

- Family office engine: `../../` (relative to this project)
- Python venv: `../../.venv/bin/python3`
- CLI tools: `../../src/analysis/*_cli.py`
- Skills: `../../.claude/skills/`

## CSS

7 files in `styles/`, CSS variables in `base.css`. Green accent (#22c55e) for financial theme.

## After modifying renderer files

Always run `bun run build:renderer` or use `bun run watch`.
