"""Integration tests for configuration loading and merging."""

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from agf.config import (
    AGFConfig,
    CLIConfig,
    EffectiveConfig,
    find_agf_config,
    load_agf_config_from_file,
    merge_configs,
)


class TestConfigLoading:
    """Tests for loading configuration from YAML files."""

    def test_load_default_config(self):
        """Test loading config with default values."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        config_path = fixtures_dir / "default.agf.yaml"

        config = load_agf_config_from_file(config_path)

        assert config.worktrees == ".worktrees"
        assert config.concurrent_tasks == 5
        assert config.agent == "claude-code"
        assert config.model_type == "standard"
        assert "claude-code" in config.agents
        assert "opencode" in config.agents

    def test_load_custom_config(self):
        """Test loading config with custom values."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        config_path = fixtures_dir / "custom.agf.yaml"

        config = load_agf_config_from_file(config_path)

        assert config.worktrees == ".custom-worktrees"
        assert config.concurrent_tasks == 10
        assert config.agent == "opencode"
        assert config.model_type == "thinking"
        assert "custom-agent" in config.agents
        assert config.agents["custom-agent"].thinking == "custom-thinking-model"

    def test_load_minimal_config(self):
        """Test loading minimal config uses defaults for unspecified fields."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        config_path = fixtures_dir / "minimal.agf.yaml"

        config = load_agf_config_from_file(config_path)

        assert config.agent == "opencode"  # specified
        assert config.worktrees == ".worktrees"  # default
        assert config.concurrent_tasks == 5  # default
        assert config.model_type == "standard"  # default

    def test_load_missing_file(self):
        """Test that loading missing file raises FileNotFoundError."""
        config_path = Path("/nonexistent/config.yaml")

        with pytest.raises(FileNotFoundError) as exc_info:
            load_agf_config_from_file(config_path)

        assert "Configuration file not found" in str(exc_info.value)

    def test_load_invalid_yaml(self):
        """Test that invalid YAML raises YAMLError."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        config_path = fixtures_dir / "invalid.agf.yaml"

        with pytest.raises(yaml.YAMLError):
            load_agf_config_from_file(config_path)

    def test_load_empty_yaml_uses_defaults(self, tmp_path):
        """Test that empty YAML file uses all defaults."""
        config_path = tmp_path / "empty.agf.yaml"
        config_path.write_text("")

        config = load_agf_config_from_file(config_path)

        # Should use all defaults
        assert config.worktrees == ".worktrees"
        assert config.concurrent_tasks == 5
        assert config.agent == "claude-code"
        assert config.model_type == "standard"


class TestConfigDiscovery:
    """Tests for discovering configuration files."""

    def test_find_dotfile_in_current_dir(self, tmp_path):
        """Test finding .agf.yaml in current directory."""
        config_path = tmp_path / ".agf.yaml"
        config_path.write_text("agent: test")

        found = find_agf_config(tmp_path)

        assert found == config_path

    def test_find_visible_file_in_current_dir(self, tmp_path):
        """Test finding agf.yaml in current directory."""
        config_path = tmp_path / "agf.yaml"
        config_path.write_text("agent: test")

        found = find_agf_config(tmp_path)

        assert found == config_path

    def test_prefer_dotfile_over_visible(self, tmp_path):
        """Test that .agf.yaml is preferred over agf.yaml."""
        dotfile = tmp_path / ".agf.yaml"
        dotfile.write_text("agent: dotfile")
        visible = tmp_path / "agf.yaml"
        visible.write_text("agent: visible")

        found = find_agf_config(tmp_path)

        assert found == dotfile

    def test_find_in_parent_directory(self, tmp_path):
        """Test finding config in parent directory."""
        config_path = tmp_path / ".agf.yaml"
        config_path.write_text("agent: parent")
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        found = find_agf_config(subdir)

        assert found == config_path

    def test_stop_at_git_root(self, tmp_path):
        """Test that search stops at git repository root."""
        # Create git root
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        config_in_git = tmp_path / ".agf.yaml"
        config_in_git.write_text("agent: git-root")

        # Create parent with config (should not be found)
        parent_config = tmp_path.parent / ".agf.yaml"
        parent_config.write_text("agent: parent")

        subdir = tmp_path / "subdir"
        subdir.mkdir()

        found = find_agf_config(subdir)

        # Should find config in git root, not parent
        assert found == config_in_git

    def test_return_none_if_not_found(self, tmp_path):
        """Test that None is returned if no config found."""
        # Create git root to stop search
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        found = find_agf_config(tmp_path)

        assert found is None


class TestConfigMerging:
    """Tests for merging AGF config with CLI config."""

    def test_merge_no_cli_overrides(self, tmp_path):
        """Test merging with no CLI overrides uses AGF config."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.touch()

        agf_config = AGFConfig.default()
        cli_config = CLIConfig(tasks_file=tasks_file, project_dir=tmp_path)

        effective = merge_configs(agf_config, cli_config)

        assert isinstance(effective, EffectiveConfig)
        assert effective.agent == "claude-code"  # from AGF config
        assert effective.model_type == "standard"  # from AGF config
        assert effective.tasks_file == tasks_file  # from CLI config
        assert effective.project_dir == tmp_path  # from CLI config

    def test_merge_cli_agent_override(self, tmp_path):
        """Test that CLI agent override wins."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.touch()

        agf_config = AGFConfig(agent="claude-code")
        cli_config = CLIConfig(
            tasks_file=tasks_file, project_dir=tmp_path, agent="opencode"
        )

        effective = merge_configs(agf_config, cli_config)

        assert effective.agent == "opencode"  # CLI wins

    def test_merge_cli_model_type_override(self, tmp_path):
        """Test that CLI model_type override wins."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.touch()

        agf_config = AGFConfig(model_type="standard")
        cli_config = CLIConfig(
            tasks_file=tasks_file, project_dir=tmp_path, model_type="thinking"
        )

        effective = merge_configs(agf_config, cli_config)

        assert effective.model_type == "thinking"  # CLI wins

    def test_merge_both_overrides(self, tmp_path):
        """Test that CLI wins on both agent and model_type."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.touch()

        agf_config = AGFConfig(agent="claude-code", model_type="standard")
        cli_config = CLIConfig(
            tasks_file=tasks_file,
            project_dir=tmp_path,
            agent="opencode",
            model_type="light",
        )

        effective = merge_configs(agf_config, cli_config)

        assert effective.agent == "opencode"  # CLI wins
        assert effective.model_type == "light"  # CLI wins

    def test_merge_all_fields_present(self, tmp_path):
        """Test that all fields from both configs appear in merged result."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.touch()

        agf_config = AGFConfig.default()
        cli_config = CLIConfig(
            tasks_file=tasks_file,
            project_dir=tmp_path,
            sync_interval=60,
            dry_run=True,
        )

        effective = merge_configs(agf_config, cli_config)

        # AGF config fields
        assert hasattr(effective, "worktrees")
        assert hasattr(effective, "concurrent_tasks")
        assert hasattr(effective, "agents")
        assert hasattr(effective, "agent")
        assert hasattr(effective, "model_type")

        # CLI config fields
        assert hasattr(effective, "tasks_file")
        assert hasattr(effective, "project_dir")
        assert hasattr(effective, "agf_config")
        assert hasattr(effective, "sync_interval")
        assert hasattr(effective, "dry_run")
        assert hasattr(effective, "single_run")

    def test_merge_preserves_agf_values(self, tmp_path):
        """Test that AGF config values are preserved in merge."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.touch()

        agf_config = AGFConfig(
            worktrees=".custom", concurrent_tasks=10
        )
        cli_config = CLIConfig(tasks_file=tasks_file, project_dir=tmp_path)

        effective = merge_configs(agf_config, cli_config)

        assert effective.worktrees == ".custom"
        assert effective.concurrent_tasks == 10

    def test_merge_preserves_cli_values(self, tmp_path):
        """Test that CLI config values are preserved in merge."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.touch()

        agf_config = AGFConfig.default()
        cli_config = CLIConfig(
            tasks_file=tasks_file,
            project_dir=tmp_path,
            sync_interval=120,
            dry_run=True,
            single_run=True,
        )

        effective = merge_configs(agf_config, cli_config)

        assert effective.sync_interval == 120
        assert effective.dry_run is True
        assert effective.single_run is True


class TestEndToEndConfigFlow:
    """End-to-end tests for configuration discovery and loading."""

    def test_discover_and_load_config(self, tmp_path):
        """Test discovering and loading config from project directory."""
        # Create config file
        config_path = tmp_path / ".agf.yaml"
        config_path.write_text(
            """
agent: opencode
model-type: thinking
concurrent-tasks: 15
"""
        )

        # Discover config
        found = find_agf_config(tmp_path)
        assert found is not None

        # Load config
        config = load_agf_config_from_file(found)
        assert config.agent == "opencode"
        assert config.model_type == "thinking"
        assert config.concurrent_tasks == 15

    def test_full_precedence_chain(self, tmp_path):
        """Test full precedence: CLI > AGF > defaults."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.touch()

        # AGF config overrides defaults
        config_path = tmp_path / ".agf.yaml"
        config_path.write_text(
            """
agent: opencode
model-type: thinking
"""
        )

        agf_config = load_agf_config_from_file(config_path)
        assert agf_config.agent == "opencode"  # AGF overrides default
        assert agf_config.worktrees == ".worktrees"  # default

        # CLI overrides AGF
        cli_config = CLIConfig(
            tasks_file=tasks_file,
            project_dir=tmp_path,
            agent="claude-code",  # Override AGF
        )

        effective = merge_configs(agf_config, cli_config)
        assert effective.agent == "claude-code"  # CLI wins
        assert effective.model_type == "thinking"  # AGF config
        assert effective.worktrees == ".worktrees"  # default
