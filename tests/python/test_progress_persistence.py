"""
Tests for Finance Guru progress persistence module.

This test suite validates the onboarding progress save/resume system:
- State creation and initialization
- State persistence (save/load)
- Section completion tracking
- Progress resumption
- Edge cases and error handling

Test Categories:
1. State Management Tests - Create, save, load state
2. Section Tracking Tests - Mark sections complete, track progress
3. Data Persistence Tests - Save/retrieve section data
4. Progress Calculation Tests - Next section, completion status
5. Edge Cases - File errors, invalid data, concurrent access
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.utils.progress_persistence import (
    ALL_SECTIONS,
    clear_state,
    create_new_state,
    get_next_section,
    get_section_data,
    get_state_path,
    get_time_since_last_update,
    has_existing_state,
    is_complete,
    load_state,
    mark_section_complete,
    save_section_data,
    save_state,
)


@pytest.fixture(autouse=True)
def isolated_state_file(tmp_path, monkeypatch):
    """Give every test its own directory for the onboarding state file.

    ``progress_persistence.get_state_path`` resolves ``STATE_FILE`` against
    ``Path.cwd()``, so without this the whole suite shares one repo-root
    ``.onboarding-state.json``. Under ``-n auto`` that file is read, written,
    and unlinked concurrently by every xdist worker, which produces torn reads
    and ``FileNotFoundError`` out of ``clear_state``'s check-then-unlink.
    """
    monkeypatch.chdir(tmp_path)


class TestStateManagement:
    """Test state creation, save, and load operations."""

    def test_create_new_state(self):
        """New state should be initialized correctly."""
        state = create_new_state()

        assert state.version == "1.0"
        assert state.started_at is not None
        assert state.last_updated is not None
        assert state.completed_sections == []
        assert state.current_section is None
        assert state.data == {}

    def test_save_and_load_state(self):
        """State should persist correctly to disk."""
        # Create and save state
        original_state = create_new_state()
        original_state.current_section = "liquid_assets"
        save_state(original_state)

        # Load state
        loaded_state = load_state()

        assert loaded_state is not None
        assert loaded_state.version == original_state.version
        assert loaded_state.started_at == original_state.started_at
        assert loaded_state.current_section == "liquid_assets"

    def test_has_existing_state(self):
        """Should correctly detect if state file exists."""
        # Initially no state
        assert not has_existing_state()

        # Create state
        state = create_new_state()
        save_state(state)

        # Now should exist
        assert has_existing_state()

    def test_load_nonexistent_state(self):
        """Loading nonexistent state should return None."""
        result = load_state()
        assert result is None

    def test_clear_state(self):
        """Clear should remove state file."""
        # Create state
        state = create_new_state()
        save_state(state)
        assert has_existing_state()

        # Clear
        clear_state()
        assert not has_existing_state()

    def test_clear_nonexistent_state(self):
        """Clearing nonexistent state should not error."""
        clear_state()  # Should not raise

    def test_clear_state_tolerates_concurrent_removal(self, monkeypatch):
        """A concurrent delete should leave the state cleared without error."""
        state_path = get_state_path()
        state_path.write_text("{}", encoding="utf-8")
        original_unlink = Path.unlink

        def remove_before_unlink(path: Path, *, missing_ok: bool = False) -> None:
            original_unlink(path, missing_ok=True)
            original_unlink(path, missing_ok=missing_ok)

        monkeypatch.setattr(Path, "unlink", remove_before_unlink)

        clear_state()

        assert not state_path.exists()

    def test_save_updates_timestamp(self):
        """Saving should update the last_updated timestamp."""
        state = create_new_state()
        original_timestamp = state.last_updated

        # Small delay to ensure timestamp difference
        import time

        time.sleep(0.01)

        save_state(state)
        loaded_state = load_state()

        assert loaded_state is not None
        assert loaded_state.last_updated > original_timestamp


class TestSectionTracking:
    """Test section completion tracking."""

    def test_mark_section_complete(self):
        """Should add section to completed list."""
        state = create_new_state()

        # Mark first section complete
        state = mark_section_complete(state, "liquid_assets", "investments")

        assert "liquid_assets" in state.completed_sections
        assert state.current_section == "investments"

    def test_mark_multiple_sections_complete(self):
        """Should track multiple completed sections."""
        state = create_new_state()

        state = mark_section_complete(state, "liquid_assets", "investments")
        state = mark_section_complete(state, "investments", "cash_flow")
        state = mark_section_complete(state, "cash_flow", "debt")

        assert len(state.completed_sections) == 3
        assert "liquid_assets" in state.completed_sections
        assert "investments" in state.completed_sections
        assert "cash_flow" in state.completed_sections
        assert state.current_section == "debt"

    def test_mark_same_section_twice(self):
        """Should not duplicate sections in completed list."""
        state = create_new_state()

        state = mark_section_complete(state, "liquid_assets", "investments")
        state = mark_section_complete(state, "liquid_assets", "investments")

        # Should only appear once
        assert state.completed_sections.count("liquid_assets") == 1

    def test_mark_final_section_complete(self):
        """Should set current_section to None when done."""
        state = create_new_state()

        # Complete all sections
        for i, section in enumerate(ALL_SECTIONS):
            next_section = ALL_SECTIONS[i + 1] if i + 1 < len(ALL_SECTIONS) else None
            state = mark_section_complete(state, section, next_section)

        assert state.current_section is None
        assert len(state.completed_sections) == len(ALL_SECTIONS)


class TestDataPersistence:
    """Test section data save/retrieve."""

    def test_save_section_data(self):
        """Should save data for a section."""
        state = create_new_state()

        section_data = {"total_value": 50000, "accounts": ["checking", "savings"]}

        state = save_section_data(state, "liquid_assets", section_data)

        assert state.data["liquid_assets"] == section_data

    def test_get_section_data(self):
        """Should retrieve saved section data."""
        state = create_new_state()

        section_data = {"portfolio_value": 500000}
        state = save_section_data(state, "investments", section_data)

        retrieved = get_section_data(state, "investments")

        assert retrieved == section_data

    def test_get_nonexistent_section_data(self):
        """Should return None for section with no data."""
        state = create_new_state()

        result = get_section_data(state, "liquid_assets")

        assert result is None

    def test_section_data_persists_across_save_load(self):
        """Section data should survive save/load cycle."""
        state = create_new_state()

        section_data = {"monthly_income": 25000}
        state = save_section_data(state, "cash_flow", section_data)

        save_state(state)
        loaded_state = load_state()

        assert loaded_state is not None
        retrieved = get_section_data(loaded_state, "cash_flow")
        assert retrieved == section_data

    def test_overwrite_section_data(self):
        """Should allow overwriting existing section data."""
        state = create_new_state()

        # Save initial data
        state = save_section_data(state, "debt", {"balance": 100000})

        # Overwrite
        new_data = {"balance": 90000}
        state = save_section_data(state, "debt", new_data)

        retrieved = get_section_data(state, "debt")
        assert retrieved == new_data


class TestProgressCalculation:
    """Test progress tracking and next section logic."""

    def test_get_next_section_at_start(self):
        """Should return first section when nothing completed."""
        state = create_new_state()

        next_section = get_next_section(state)

        assert next_section == "liquid_assets"

    def test_get_next_section_in_progress(self):
        """Should return next uncompleted section."""
        state = create_new_state()

        # Complete first two sections
        state.completed_sections = ["liquid_assets", "investments"]

        next_section = get_next_section(state)

        assert next_section == "cash_flow"

    def test_get_next_section_when_complete(self):
        """Should return None when all sections complete."""
        state = create_new_state()

        # Mark all sections complete
        state.completed_sections = list(ALL_SECTIONS)

        next_section = get_next_section(state)

        assert next_section is None

    def test_is_complete_false(self):
        """Should return False when sections remain."""
        state = create_new_state()
        state.completed_sections = ["liquid_assets", "investments"]

        assert not is_complete(state)

    def test_is_complete_true(self):
        """Should return True when all sections done."""
        state = create_new_state()
        state.completed_sections = list(ALL_SECTIONS)

        assert is_complete(state)

    def test_is_complete_empty_state(self):
        """Should return False for new state."""
        state = create_new_state()

        assert not is_complete(state)


class TestTimeTracking:
    """Test time since last update calculations."""

    def test_just_now(self):
        """Recent update should show 'just now'."""
        state = create_new_state()

        time_str = get_time_since_last_update(state)

        assert time_str == "just now"

    def test_minutes_ago(self):
        """Should show minutes for recent updates."""
        state = create_new_state()

        # Manually set last_updated to 5 minutes ago
        past_time = datetime.now() - timedelta(minutes=5)
        state.last_updated = past_time.isoformat()

        time_str = get_time_since_last_update(state)

        assert "minute" in time_str
        assert "5" in time_str

    def test_hours_ago(self):
        """Should show hours for older updates."""
        state = create_new_state()

        # Set to 3 hours ago
        past_time = datetime.now() - timedelta(hours=3)
        state.last_updated = past_time.isoformat()

        time_str = get_time_since_last_update(state)

        assert "hour" in time_str
        assert "3" in time_str

    def test_days_ago(self):
        """Should show days for very old updates."""
        state = create_new_state()

        # Set to 2 days ago
        past_time = datetime.now() - timedelta(days=2)
        state.last_updated = past_time.isoformat()

        time_str = get_time_since_last_update(state)

        assert "day" in time_str
        assert "2" in time_str

    def test_singular_vs_plural(self):
        """Should use singular/plural correctly."""
        state = create_new_state()

        # 1 day
        past_time = datetime.now() - timedelta(days=1)
        state.last_updated = past_time.isoformat()
        assert "day ago" in get_time_since_last_update(state)

        # 2 days
        past_time = datetime.now() - timedelta(days=2)
        state.last_updated = past_time.isoformat()
        assert "days ago" in get_time_since_last_update(state)


class TestEdgeCases:
    """Edge case handling and error scenarios."""

    def test_corrupted_state_file(self):
        """Should handle corrupted JSON gracefully."""
        # Write invalid JSON
        state_path = get_state_path()
        state_path.write_text("{ invalid json }", encoding="utf-8")

        result = load_state()

        assert result is None

    def test_empty_state_file(self):
        """Should handle empty file gracefully."""
        state_path = get_state_path()
        state_path.write_text("", encoding="utf-8")

        result = load_state()

        assert result is None

    def test_state_with_extra_fields(self):
        """Should handle state files with extra fields."""
        state_path = get_state_path()

        # Create state with extra field
        data = {
            "version": "1.0",
            "started_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "completed_sections": [],
            "current_section": None,
            "data": {},
            "extra_field": "should be ignored",
        }

        state_path.write_text(json.dumps(data), encoding="utf-8")

        result = load_state()

        # Should load successfully (Pydantic ignores extra fields)
        assert result is not None
        assert result.version == "1.0"

    def test_resume_after_interruption(self):
        """Should properly resume onboarding after interruption."""
        # Start onboarding
        state = create_new_state()
        state = mark_section_complete(state, "liquid_assets", "investments")
        state = save_section_data(state, "liquid_assets", {"total": 50000})
        save_state(state)

        # Simulate interruption and resume
        resumed_state = load_state()

        assert resumed_state is not None
        assert "liquid_assets" in resumed_state.completed_sections
        assert resumed_state.current_section == "investments"
        assert get_section_data(resumed_state, "liquid_assets") == {"total": 50000}

    def test_concurrent_access_safety(self):
        """Test that save operations are atomic."""
        state1 = create_new_state()
        state1.current_section = "liquid_assets"

        state2 = create_new_state()
        state2.current_section = "investments"

        # Save both
        save_state(state1)
        save_state(state2)

        # Last save should win
        loaded = load_state()
        assert loaded is not None
        assert loaded.current_section == "investments"

    def test_failed_atomic_replace_preserves_previous_state(self, monkeypatch):
        """An interrupted replacement should leave the prior state readable."""
        original_state = create_new_state()
        original_state.current_section = "liquid_assets"
        save_state(original_state)
        state_path = get_state_path()
        previous_content = state_path.read_text(encoding="utf-8")

        replacement_state = create_new_state()
        replacement_state.current_section = "investments"

        def fail_replace(source: Path, destination: Path) -> None:
            raise OSError(f"interrupted replacement of {source} with {destination}")

        monkeypatch.setattr("os.replace", fail_replace)

        with pytest.raises(OSError, match="interrupted replacement"):
            save_state(replacement_state)

        assert state_path.read_text(encoding="utf-8") == previous_content
        loaded = load_state()
        assert loaded is not None
        assert loaded.current_section == "liquid_assets"
