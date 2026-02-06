"""
Onboarding Wizard State Models for Finance Guru

Pydantic models for tracking wizard progress and section state.
These models are wizard-specific -- they do NOT duplicate or replace
the existing yaml_generation_inputs.py models.

ARCHITECTURE NOTE:
The OnboardingState.data dict holds raw collected values keyed by section
name as plain dicts. Pydantic model instances (UserDataInput, etc.) are
created at generation time in the wizard CLI (Plan 02), keeping wizard
state decoupled from yaml_generation_inputs.py validation during collection.

Author: Finance Guru Development Team
Created: 2026-02-05
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class SectionName(str, Enum):
    """Wizard section identifiers, ordered by flow."""

    LIQUID_ASSETS = "liquid_assets"
    INVESTMENTS = "investments"
    CASH_FLOW = "cash_flow"
    DEBT = "debt"
    PREFERENCES = "preferences"
    BROKER = "broker"
    ENV_SETUP = "env_setup"
    SUMMARY = "summary"


class OnboardingState(BaseModel):
    """Tracks wizard progress across all 8 onboarding sections.

    The data dict stores raw section data as plain dicts keyed by
    SectionName value strings. No Pydantic model instances are stored
    here -- conversion to UserDataInput happens at generation time.
    """

    current_section: SectionName = Field(
        default=SectionName.LIQUID_ASSETS,
        description="Section the wizard is currently on",
    )
    completed_sections: list[SectionName] = Field(
        default_factory=list,
        description="Sections that have been completed",
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Raw collected values keyed by section name",
    )
    started_at: str = Field(
        default="",
        description="ISO timestamp of when the wizard was started",
    )

    @classmethod
    def create_new(cls) -> "OnboardingState":
        """Create a fresh wizard state with the current timestamp."""
        return cls(
            current_section=SectionName.LIQUID_ASSETS,
            completed_sections=[],
            data={},
            started_at=datetime.now(timezone.utc).isoformat(),
        )

    def is_section_complete(self, section: SectionName) -> bool:
        """Check whether a specific section has been completed."""
        return section in self.completed_sections

    def mark_complete(
        self, section: SectionName, next_section: Optional[SectionName] = None
    ) -> None:
        """Mark a section as complete and advance to the next one.

        Args:
            section: The section to mark as completed.
            next_section: The next section to move to. If None, the
                current_section is left unchanged (end of wizard).
        """
        if section not in self.completed_sections:
            self.completed_sections.append(section)
        if next_section is not None:
            self.current_section = next_section
