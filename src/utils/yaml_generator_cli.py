#!/usr/bin/env python3
"""
YAML Generator CLI for Finance Guru™

This module provides command-line access to configuration file generation.
Finance Guru agents use this CLI to generate personalized config files from user data.

ARCHITECTURE NOTE:
This is Layer 3 of our 3-layer architecture:
    Layer 1: Pydantic Models - Data validation (yaml_generation_inputs.py)
    Layer 2: Calculator Classes - Business logic (yaml_generator.py)
    Layer 3: CLI Interface (THIS FILE) - Agent integration

USAGE:
    # Generate configs from JSON input file
    uv run python src/utils/yaml_generator_cli.py --input user_data.json

    # Generate configs and save to custom directory
    uv run python src/utils/yaml_generator_cli.py --input user_data.json --output /path/to/dir

    # Generate specific config file only
    uv run python src/utils/yaml_generator_cli.py --input data.json --type user-profile

    # Validate user data without generating files
    uv run python src/utils/yaml_generator_cli.py --input data.json --validate-only

AGENT USE CASES:
    - Builder: Generate configuration files during onboarding
    - Finance Orchestrator: Setup new Finance Guru installations
    - Onboarding Specialist: Create personalized user configs

Author: Finance Guru™ Development Team
Created: 2026-01-16
"""

import argparse
import json
import sys
from pathlib import Path

from src.models.yaml_generation_inputs import (
    CashFlowInput,
    DebtProfileInput,
    InvestmentPortfolioInput,
    LiquidAssetsInput,
    MCPConfigInput,
    UserDataInput,
    UserIdentityInput,
    UserPreferencesInput,
)
from src.utils.yaml_generator import YAMLGenerator, write_config_files


def load_user_data_from_json(json_path: str) -> UserDataInput:
    """
    Load and validate user data from JSON file.

    Args:
        json_path: Path to JSON file with user data

    Returns:
        Validated UserDataInput

    Raises:
        FileNotFoundError: If JSON file doesn't exist
        ValueError: If JSON is invalid or fails validation
    """
    json_file = Path(json_path)
    if not json_file.exists():
        raise FileNotFoundError(f"User data file not found: {json_path}")

    with open(json_file, encoding="utf-8") as f:
        raw_data = json.load(f)

    # Parse nested structures
    try:
        user_data = UserDataInput(
            identity=UserIdentityInput(**raw_data["identity"]),
            liquid_assets=LiquidAssetsInput(**raw_data["liquid_assets"]),
            portfolio=InvestmentPortfolioInput(**raw_data["portfolio"]),
            cash_flow=CashFlowInput(**raw_data["cash_flow"]),
            debt=DebtProfileInput(**raw_data["debt"]),
            preferences=UserPreferencesInput(**raw_data["preferences"]),
            mcp=MCPConfigInput(**raw_data.get("mcp", {})),
            project_root=raw_data.get("project_root"),
            google_sheets_credentials=raw_data.get("google_sheets_credentials"),
        )
        return user_data
    except Exception as e:
        raise ValueError(f"Invalid user data: {e}") from e


def print_generation_summary(
    output, output_dir: str, config_type: str | None = None
) -> None:
    """
    Print summary of generated configuration files.

    Args:
        output: YAMLGenerationOutput with generated content
        output_dir: Directory where files were saved
        config_type: Specific config type if only one was generated
    """
    print(f"\n{'=' * 70}")
    print("CONFIGURATION GENERATION COMPLETE")
    print(f"{'=' * 70}")
    print(f"User: {output.user_name}")
    print(f"Generation Date: {output.generation_date}")
    print(f"Output Directory: {output_dir}")
    print()

    if config_type:
        print(f"Generated: {config_type}")
    else:
        print("Generated Files:")
        files = [
            ("user-profile.yaml", "fin-guru/data/user-profile.yaml"),
            ("config.yaml", "fin-guru/config.yaml"),
            ("system-context.md", "fin-guru/data/system-context.md"),
            ("CLAUDE.md", "CLAUDE.md"),
            (".env", ".env"),
        ]
        for name, path in files:
            print(f"  ✓ {name:<20} → {path}")

    print()
    print("Next Steps:")
    print("  1. Review generated files for accuracy")
    print("  2. Update .env with actual API keys")
    print("  3. Run Finance Guru CLI to verify setup")
    print(f"{'=' * 70}\n")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Finance Guru configuration files from user data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all config files
  uv run python src/utils/yaml_generator_cli.py --input user_data.json

  # Save to custom directory
  uv run python src/utils/yaml_generator_cli.py --input data.json --output /tmp/test

  # Generate only user-profile.yaml
  uv run python src/utils/yaml_generator_cli.py --input data.json --type user-profile

  # Validate without generating files
  uv run python src/utils/yaml_generator_cli.py --input data.json --validate-only
        """,
    )

    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to JSON file with user data",
    )

    parser.add_argument(
        "--output",
        "-o",
        default=".",
        help="Output directory for generated files (default: current directory)",
    )

    parser.add_argument(
        "--template-dir",
        default="scripts/onboarding/modules/templates",
        help="Directory containing template files (default: scripts/onboarding/modules/templates)",
    )

    parser.add_argument(
        "--type",
        choices=["user-profile", "config", "system-context", "claude-md", "env", "all"],
        default="all",
        help="Type of config to generate (default: all)",
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate user data without generating files",
    )

    parser.add_argument(
        "--pretty-print",
        action="store_true",
        help="Pretty-print generated YAML to stdout (for debugging)",
    )

    args = parser.parse_args()

    try:
        # Load and validate user data
        print(f"Loading user data from {args.input}...")
        user_data = load_user_data_from_json(args.input)
        print(f"✓ User data validated for: {user_data.identity.user_name}")

        if args.validate_only:
            print("\n✓ Validation successful. Use --generate to create config files.")
            sys.exit(0)

        # Initialize generator
        print(f"Loading templates from {args.template_dir}...")
        generator = YAMLGenerator(args.template_dir)

        # Generate configurations
        print("Generating configuration files...")

        if args.type == "all":
            output = generator.generate_all_configs(user_data)

            # Pretty-print if requested
            if args.pretty_print:
                print("\n--- user-profile.yaml ---")
                print(output.user_profile_yaml)
                print("\n--- config.yaml ---")
                print(output.config_yaml)

            # Write files
            if not args.pretty_print:
                write_config_files(output, args.output)
                print_generation_summary(output, args.output)

        else:
            # Generate specific config
            config_map = {
                "user-profile": generator.generate_user_profile,
                "config": generator.generate_config,
                "system-context": generator.generate_system_context,
                "claude-md": generator.generate_claude_md,
                "env": generator.generate_env,
            }

            generated_content = config_map[args.type](user_data)

            if args.pretty_print:
                print(f"\n--- {args.type} ---")
                print(generated_content)
            else:
                # Write single file
                file_map = {
                    "user-profile": Path(args.output)
                    / "fin-guru"
                    / "data"
                    / "user-profile.yaml",
                    "config": Path(args.output) / "fin-guru" / "config.yaml",
                    "system-context": Path(args.output)
                    / "fin-guru"
                    / "data"
                    / "system-context.md",
                    "claude-md": Path(args.output) / "CLAUDE.md",
                    "env": Path(args.output) / ".env",
                }

                output_path = file_map[args.type]
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_text(generated_content, encoding="utf-8")

                # Create minimal output object for summary
                from datetime import date

                from src.models.yaml_generation_inputs import YAMLGenerationOutput

                output = YAMLGenerationOutput(
                    user_profile_yaml="",
                    config_yaml="",
                    system_context_md="",
                    claude_md="",
                    env_file="",
                    generation_date=date.today(),
                    user_name=user_data.identity.user_name,
                )
                print_generation_summary(output, args.output, args.type)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
