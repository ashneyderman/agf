"""Tests for CLIConfig model."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from agf.config.models import CLIConfig


def test_cli_config_required_fields_only(tmp_path):
    """Test creating CLIConfig with required fields only."""
    tasks_file = tmp_path / "tasks.md"
    tasks_file.touch()

    config = CLIConfig(tasks_file=tasks_file, project_dir=tmp_path)

    assert config.tasks_file == tasks_file
    assert config.project_dir == tmp_path
    assert config.agf_config is None
    assert config.sync_interval == 30
    assert config.dry_run is False
    assert config.single_run is False
    assert config.agent is None
    assert config.model_type is None


def test_cli_config_all_fields_specified(tmp_path):
    """Test creating CLIConfig with all fields specified."""
    tasks_file = tmp_path / "tasks.md"
    tasks_file.touch()
    agf_config_file = tmp_path / ".agf.yaml"
    agf_config_file.touch()

    config = CLIConfig(
        tasks_file=tasks_file,
        project_dir=tmp_path,
        agf_config=agf_config_file,
        sync_interval=60,
        dry_run=True,
        single_run=True,
        agent="opencode",
        model_type="thinking",
    )

    assert config.tasks_file == tasks_file
    assert config.project_dir == tmp_path
    assert config.agf_config == agf_config_file
    assert config.sync_interval == 60
    assert config.dry_run is True
    assert config.single_run is True
    assert config.agent == "opencode"
    assert config.model_type == "thinking"


def test_cli_config_defaults_for_optional_fields(tmp_path):
    """Test defaults for optional fields."""
    tasks_file = tmp_path / "tasks.md"
    tasks_file.touch()

    config = CLIConfig(tasks_file=tasks_file, project_dir=tmp_path)

    assert config.sync_interval == 30
    assert config.dry_run is False
    assert config.single_run is False
    assert config.agent is None
    assert config.model_type is None


def test_cli_config_agent_override(tmp_path):
    """Test agent override (None vs specified)."""
    tasks_file = tmp_path / "tasks.md"
    tasks_file.touch()

    # No override
    config1 = CLIConfig(tasks_file=tasks_file, project_dir=tmp_path)
    assert config1.agent is None

    # With override
    config2 = CLIConfig(
        tasks_file=tasks_file, project_dir=tmp_path, agent="custom-agent"
    )
    assert config2.agent == "custom-agent"


def test_cli_config_model_type_override(tmp_path):
    """Test model_type override (None vs specified)."""
    tasks_file = tmp_path / "tasks.md"
    tasks_file.touch()

    # No override
    config1 = CLIConfig(tasks_file=tasks_file, project_dir=tmp_path)
    assert config1.model_type is None

    # With override
    config2 = CLIConfig(
        tasks_file=tasks_file, project_dir=tmp_path, model_type="light"
    )
    assert config2.model_type == "light"


def test_cli_config_negative_sync_interval(tmp_path):
    """Test that negative sync_interval raises validation error."""
    tasks_file = tmp_path / "tasks.md"
    tasks_file.touch()

    with pytest.raises(ValidationError) as exc_info:
        CLIConfig(tasks_file=tasks_file, project_dir=tmp_path, sync_interval=-1)

    assert "sync_interval must be positive" in str(exc_info.value)


def test_cli_config_zero_sync_interval(tmp_path):
    """Test that zero sync_interval raises validation error."""
    tasks_file = tmp_path / "tasks.md"
    tasks_file.touch()

    with pytest.raises(ValidationError) as exc_info:
        CLIConfig(tasks_file=tasks_file, project_dir=tmp_path, sync_interval=0)

    assert "sync_interval must be positive" in str(exc_info.value)


def test_cli_config_missing_required_fields():
    """Test that missing required fields raises validation error."""
    with pytest.raises(ValidationError) as exc_info:
        CLIConfig()

    errors = str(exc_info.value)
    assert "tasks_file" in errors
    assert "project_dir" in errors


def test_cli_config_path_types(tmp_path):
    """Test that Path types work correctly."""
    tasks_file = tmp_path / "tasks.md"
    tasks_file.touch()
    agf_config_file = tmp_path / ".agf.yaml"
    agf_config_file.touch()

    config = CLIConfig(
        tasks_file=tasks_file,
        project_dir=tmp_path,
        agf_config=agf_config_file,
    )

    assert isinstance(config.tasks_file, Path)
    assert isinstance(config.project_dir, Path)
    assert isinstance(config.agf_config, Path)


def test_cli_config_string_paths_converted(tmp_path):
    """Test that string paths are converted to Path objects."""
    tasks_file = tmp_path / "tasks.md"
    tasks_file.touch()

    config = CLIConfig(
        tasks_file=str(tasks_file),
        project_dir=str(tmp_path),
    )

    assert isinstance(config.tasks_file, Path)
    assert isinstance(config.project_dir, Path)
    assert config.tasks_file == tasks_file
    assert config.project_dir == tmp_path


def test_cli_config_branch_prefix_default(tmp_path):
    """Test that branch_prefix defaults to None."""
    tasks_file = tmp_path / "tasks.md"
    tasks_file.touch()

    config = CLIConfig(tasks_file=tasks_file, project_dir=tmp_path)

    assert config.branch_prefix is None


def test_cli_config_branch_prefix_custom_value(tmp_path):
    """Test that custom branch_prefix value is preserved."""
    tasks_file = tmp_path / "tasks.md"
    tasks_file.touch()

    config = CLIConfig(
        tasks_file=tasks_file, project_dir=tmp_path, branch_prefix="custom-prefix"
    )

    assert config.branch_prefix == "custom-prefix"


def test_cli_config_commands_namespace_default(tmp_path):
    """Test that commands_namespace defaults to None."""
    tasks_file = tmp_path / "tasks.md"
    tasks_file.touch()

    config = CLIConfig(tasks_file=tasks_file, project_dir=tmp_path)

    assert config.commands_namespace is None


def test_cli_config_commands_namespace_custom_value(tmp_path):
    """Test that custom commands_namespace value is preserved."""
    tasks_file = tmp_path / "tasks.md"
    tasks_file.touch()

    config = CLIConfig(
        tasks_file=tasks_file, project_dir=tmp_path, commands_namespace="custom-ns"
    )

    assert config.commands_namespace == "custom-ns"
