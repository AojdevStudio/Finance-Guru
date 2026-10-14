#!/usr/bin/env python3
"""Finance Guru TUI Dashboard Entry Point.

WHAT: CLI entry point for Finance Guru dashboard
WHY: Provides single command (`fin-guru`) to launch dashboard
ARCHITECTURE: Simple wrapper that imports and runs the Textual app

Usage:
    fin-guru

Author: Finance Guru™ Development Team
Created: 2025-11-17
"""

from src.ui.app import FinanceGuruApp


def main():
    """Launch Finance Guru TUI Dashboard."""
    app = FinanceGuruApp()
    app.run()


if __name__ == "__main__":
    main()
