"""
Progress Save/Resume System
Manages onboarding state persistence

This module provides functionality to save and resume onboarding progress,
allowing users to complete the Finance Guru setup in multiple sessions.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


SectionName = Literal[
    "liquid_assets",
    "investments",
    "cash_flow",
    "debt",
    "preferences",
    "mcp_config",
    "env_setup"
]

ALL_SECTIONS: list[SectionName] = [
    "liquid_assets",
    "investments",
    "cash_flow",
    "debt",
    "preferences",
    "mcp_config",
    "env_setup"
]


class OnboardingState(BaseModel):
    """Represents the current state of the onboarding process."""

    version: str = "1.0"
    started_at: str
    last_updated: str
    completed_sections: list[SectionName] = Field(default_factory=list)
    current_section: Optional[SectionName] = None
    data: dict[str, Any] = Field(default_factory=dict)


STATE_FILE = ".onboarding-state.json"


def get_state_path() -> Path:
    """
    Gets the path to the state file.

    Returns:
        Path: Absolute path to state file
    """
    return Path.cwd() / STATE_FILE


def has_existing_state() -> bool:
    """
    Checks if a saved state exists.

    Returns:
        bool: True if state file exists
    """
    return get_state_path().exists()


def load_state() -> Optional[OnboardingState]:
    """
    Loads the onboarding state from disk.

    Returns:
        OnboardingState or None: Loaded state or None if doesn't exist
    """
    state_path = get_state_path()

    if not state_path.exists():
        return None

    try:
        content = state_path.read_text(encoding='utf-8')
        data = json.loads(content)
        return OnboardingState(**data)
    except Exception as error:
        print(f"Failed to load onboarding state: {error}")
        return None


def save_state(state: OnboardingState) -> None:
    """
    Saves the onboarding state to disk.

    Args:
        state: OnboardingState to save

    Raises:
        Exception: If save operation fails
    """
    state_path = get_state_path()

    try:
        state.last_updated = datetime.now().isoformat()
        content = state.model_dump_json(indent=2)
        state_path.write_text(content, encoding='utf-8')
    except Exception as error:
        print(f"Failed to save onboarding state: {error}")
        raise


def create_new_state() -> OnboardingState:
    """
    Creates a new onboarding state.

    Returns:
        OnboardingState: New state initialized with current timestamp
    """
    now = datetime.now().isoformat()

    return OnboardingState(
        version="1.0",
        started_at=now,
        last_updated=now,
        completed_sections=[],
        current_section=None,
        data={}
    )


def mark_section_complete(
    state: OnboardingState,
    completed_section: SectionName,
    next_section: Optional[SectionName]
) -> OnboardingState:
    """
    Marks a section as completed and updates the current section.

    Args:
        state: Current state
        completed_section: Section that was completed
        next_section: Next section to work on (or None if done)

    Returns:
        OnboardingState: Updated state
    """
    # Add to completed list if not already there
    if completed_section not in state.completed_sections:
        state.completed_sections.append(completed_section)

    # Update current section
    state.current_section = next_section

    return state


def save_section_data(
    state: OnboardingState,
    section: SectionName,
    data: dict[str, Any]
) -> OnboardingState:
    """
    Saves section data to state.

    Args:
        state: Current state
        section: Section name
        data: Section data

    Returns:
        OnboardingState: Updated state
    """
    state.data[section] = data
    return state


def get_section_data(
    state: OnboardingState,
    section: SectionName
) -> Optional[dict[str, Any]]:
    """
    Gets data for a specific section.

    Args:
        state: Current state
        section: Section name

    Returns:
        dict or None: Section data or None if not found
    """
    return state.data.get(section)


def clear_state() -> None:
    """
    Deletes the onboarding state file.

    Raises:
        Exception: If delete operation fails
    """
    state_path = get_state_path()

    if state_path.exists():
        try:
            state_path.unlink()
        except Exception as error:
            print(f"Failed to delete onboarding state: {error}")
            raise


def get_next_section(state: OnboardingState) -> Optional[SectionName]:
    """
    Gets the next section to work on based on current progress.

    Args:
        state: Current state

    Returns:
        SectionName or None: Next section or None if all complete
    """
    # Find first section not in completed list
    for section in ALL_SECTIONS:
        if section not in state.completed_sections:
            return section

    return None


def is_complete(state: OnboardingState) -> bool:
    """
    Checks if onboarding is complete.

    Args:
        state: Current state

    Returns:
        bool: True if all sections completed
    """
    return all(section in state.completed_sections for section in ALL_SECTIONS)


def get_time_since_last_update(state: OnboardingState) -> str:
    """
    Formats time since state was last updated.

    Args:
        state: Current state

    Returns:
        str: Human-readable time difference
    """
    now = datetime.now()
    last_update = datetime.fromisoformat(state.last_updated)
    diff = now - last_update

    diff_seconds = diff.total_seconds()
    diff_minutes = int(diff_seconds / 60)
    diff_hours = int(diff_seconds / 3600)
    diff_days = diff.days

    if diff_days > 0:
        return f"{diff_days} day{'s' if diff_days > 1 else ''} ago"
    elif diff_hours > 0:
        return f"{diff_hours} hour{'s' if diff_hours > 1 else ''} ago"
    elif diff_minutes > 0:
        return f"{diff_minutes} minute{'s' if diff_minutes > 1 else ''} ago"
    else:
        return "just now"
