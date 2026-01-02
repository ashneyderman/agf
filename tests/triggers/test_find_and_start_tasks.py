"""Tests for the find_and_start_tasks trigger script."""

import signal
from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest
from click.testing import CliRunner

from agent.base import AgentResult
from triggers.find_and_start_tasks import (
    TriggerContext,
    build_process_tasks_prompt,
    extract_json_from_markdown,
    extract_tasks_from_agent_result,
    invoke_process_tasks,
    log,
    main,
    parse_and_print_results,
    setup_signal_handlers,
    validate_project_dir,
    validate_tasks_file,
)


class TestTriggerContext:
    """Tests for TriggerContext class."""

    def test_initial_state(self):
        """Test that context starts in running state."""
        ctx = TriggerContext()
        assert ctx.running is True
        assert ctx.current_iteration == 0

    def test_stop(self):
        """Test that stop sets running to False."""
        ctx = TriggerContext()
        ctx.stop()
        assert ctx.running is False


class TestExtractJsonFromMarkdown:
    """Tests for extract_json_from_markdown function."""

    def test_extract_json_code_block(self):
        """Test extraction from ```json ... ``` block."""
        text = 'Some text before\n\n```json\n[{"key": "value"}]\n```\n\nSome text after'
        result = extract_json_from_markdown(text)
        assert result == '[{"key": "value"}]'

    def test_extract_generic_code_block(self):
        """Test extraction from generic ``` ... ``` block."""
        text = 'Some text\n\n```\n[{"key": "value"}]\n```\n\nMore text'
        result = extract_json_from_markdown(text)
        assert result == '[{"key": "value"}]'

    def test_json_block_preferred_over_generic(self):
        """Test that ```json block is preferred over generic block."""
        text = '```\ngeneric\n```\n\n```json\n[{"preferred": true}]\n```'
        result = extract_json_from_markdown(text)
        assert result == '[{"preferred": true}]'

    def test_multiline_json(self):
        """Test extraction of multiline JSON."""
        text = '''Here are the results:

```json
[
  {
    "worktree_name": "test",
    "tasks_to_start": []
  }
]
```

All done.'''
        result = extract_json_from_markdown(text)
        assert '"worktree_name": "test"' in result
        assert '"tasks_to_start": []' in result

    def test_no_code_block(self):
        """Test handling of text with no code block."""
        text = 'Just plain text without any code blocks.'
        result = extract_json_from_markdown(text)
        assert result is None

    def test_empty_code_block(self):
        """Test handling of empty code block."""
        text = '```json\n```'
        result = extract_json_from_markdown(text)
        assert result == ''

    def test_whitespace_handling(self):
        """Test that whitespace is stripped from extracted content."""
        text = '```json\n  \n  []\n  \n```'
        result = extract_json_from_markdown(text)
        assert result == '[]'


class TestExtractTasksFromAgentResult:
    """Tests for extract_tasks_from_agent_result function."""

    def test_none_input(self):
        """Test handling of None input."""
        result = extract_tasks_from_agent_result(None)
        assert result is None

    def test_list_input_with_worktree_structure(self):
        """Test that list with worktree_name structure is returned directly."""
        tasks = [{"worktree_name": "test", "tasks_to_start": []}]
        result = extract_tasks_from_agent_result(tasks)
        assert result == tasks

    def test_opencode_event_list(self):
        """Test extraction from OpenCode NDJSON event list."""
        parsed_output = [
            {
                "type": "step_finish",
                "timestamp": 1767304893138,
                "sessionID": "ses_123",
                "part": {"id": "prt_1", "type": "step-finish"},
            },
            {
                "type": "text",
                "timestamp": 1767304900737,
                "sessionID": "ses_123",
                "part": {
                    "id": "prt_2",
                    "type": "text",
                    "text": 'Here are the tasks:\n\n```json\n[{"worktree_name": "feature", "tasks_to_start": [{"description": "Task 1", "tags": []}]}]\n```',
                },
            },
        ]
        result = extract_tasks_from_agent_result(parsed_output)
        assert result is not None
        assert len(result) == 1
        assert result[0]["worktree_name"] == "feature"
        assert result[0]["tasks_to_start"][0]["description"] == "Task 1"

    def test_opencode_event_list_multiple_worktrees(self):
        """Test extraction from OpenCode with multiple worktrees."""
        json_content = '''[
            {"worktree_name": "validation-workflow", "tasks_to_start": [{"description": "Task A", "tags": []}]},
            {"worktree_name": "classify-primary-topic", "tasks_to_start": [{"description": "Task B", "tags": ["sonnet"]}]}
        ]'''
        parsed_output = [
            {"type": "step_start", "part": {}},
            {
                "type": "text",
                "part": {
                    "type": "text",
                    "text": f'Analyzing tasks...\n\n```json\n{json_content}\n```',
                },
            },
        ]
        result = extract_tasks_from_agent_result(parsed_output)
        assert result is not None
        assert len(result) == 2
        assert result[0]["worktree_name"] == "validation-workflow"
        assert result[1]["worktree_name"] == "classify-primary-topic"

    def test_opencode_event_list_no_text_event(self):
        """Test handling OpenCode events without text event."""
        parsed_output = [
            {"type": "step_start", "part": {}},
            {"type": "step_finish", "part": {}},
        ]
        result = extract_tasks_from_agent_result(parsed_output)
        assert result is None

    def test_opencode_event_list_empty_text(self):
        """Test handling OpenCode text event with empty text."""
        parsed_output = [
            {
                "type": "text",
                "part": {"type": "text", "text": ""},
            },
        ]
        result = extract_tasks_from_agent_result(parsed_output)
        assert result is None

    def test_opencode_event_list_no_json_block(self):
        """Test handling OpenCode text without JSON code block."""
        parsed_output = [
            {
                "type": "text",
                "part": {"type": "text", "text": "No tasks found."},
            },
        ]
        result = extract_tasks_from_agent_result(parsed_output)
        assert result is None

    def test_claude_code_result_structure(self):
        """Test extraction from Claude Code nested result structure."""
        parsed_output = {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": 'Based on my analysis:\n\n```json\n[{"worktree_name": "feature", "tasks_to_start": [{"description": "Task 1", "tags": []}]}]\n```\n\nAll done.',
            "session_id": "test-session",
        }
        result = extract_tasks_from_agent_result(parsed_output)
        assert result is not None
        assert len(result) == 1
        assert result[0]["worktree_name"] == "feature"
        assert result[0]["tasks_to_start"][0]["description"] == "Task 1"

    def test_claude_code_empty_tasks(self):
        """Test extraction when Claude Code returns empty array."""
        parsed_output = {
            "type": "result",
            "result": 'No eligible tasks.\n\n```json\n[]\n```',
        }
        result = extract_tasks_from_agent_result(parsed_output)
        assert result == []

    def test_claude_code_multiple_worktrees(self):
        """Test extraction with multiple worktrees."""
        json_content = '''[
            {"worktree_name": "feature-1", "tasks_to_start": [{"description": "Task A", "tags": ["api"]}]},
            {"worktree_name": "feature-2", "tasks_to_start": [{"description": "Task B", "tags": []}]}
        ]'''
        parsed_output = {
            "type": "result",
            "result": f'Here are the tasks:\n\n```json\n{json_content}\n```',
        }
        result = extract_tasks_from_agent_result(parsed_output)
        assert result is not None
        assert len(result) == 2
        assert result[0]["worktree_name"] == "feature-1"
        assert result[1]["worktree_name"] == "feature-2"

    def test_dict_with_worktree_name(self):
        """Test handling of single worktree dict."""
        parsed_output = {
            "worktree_name": "single-worktree",
            "tasks_to_start": [{"description": "Task", "tags": []}],
        }
        result = extract_tasks_from_agent_result(parsed_output)
        assert result is not None
        assert len(result) == 1
        assert result[0]["worktree_name"] == "single-worktree"

    def test_invalid_json_in_result(self):
        """Test handling of invalid JSON in result field."""
        parsed_output = {
            "type": "result",
            "result": "```json\ninvalid json here\n```",
        }
        result = extract_tasks_from_agent_result(parsed_output)
        assert result is None

    def test_no_result_field(self):
        """Test handling of dict without result field."""
        parsed_output = {
            "type": "result",
            "other_field": "value",
        }
        result = extract_tasks_from_agent_result(parsed_output)
        assert result is None

    def test_result_not_a_list(self):
        """Test handling when parsed JSON is not a list."""
        parsed_output = {
            "type": "result",
            "result": '```json\n{"not": "a list"}\n```',
        }
        result = extract_tasks_from_agent_result(parsed_output)
        assert result is None


class TestValidateTasksFile:
    """Tests for validate_tasks_file function."""

    def test_valid_md_file(self, tmp_path):
        """Test validation of existing .md file."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("# Tasks\n")

        result = validate_tasks_file(None, None, str(tasks_file))

        assert result == tasks_file.resolve()

    def test_file_does_not_exist(self, tmp_path):
        """Test that non-existent file raises BadParameter."""
        non_existent = tmp_path / "missing.md"

        with pytest.raises(click.BadParameter) as exc_info:
            validate_tasks_file(None, None, str(non_existent))

        assert "does not exist" in str(exc_info.value)

    def test_file_wrong_extension(self, tmp_path):
        """Test that non-.md file raises BadParameter."""
        txt_file = tmp_path / "tasks.txt"
        txt_file.write_text("# Tasks\n")

        with pytest.raises(click.BadParameter) as exc_info:
            validate_tasks_file(None, None, str(txt_file))

        assert "must be a .md file" in str(exc_info.value)


class TestValidateProjectDir:
    """Tests for validate_project_dir function."""

    def test_valid_directory(self, tmp_path):
        """Test validation of existing directory."""
        result = validate_project_dir(None, None, str(tmp_path))

        assert result == tmp_path.resolve()

    def test_directory_does_not_exist(self, tmp_path):
        """Test that non-existent directory raises BadParameter."""
        non_existent = tmp_path / "missing_dir"

        with pytest.raises(click.BadParameter) as exc_info:
            validate_project_dir(None, None, str(non_existent))

        assert "does not exist" in str(exc_info.value)

    def test_path_is_file_not_directory(self, tmp_path):
        """Test that file path raises BadParameter."""
        file_path = tmp_path / "somefile.txt"
        file_path.write_text("content")

        with pytest.raises(click.BadParameter) as exc_info:
            validate_project_dir(None, None, str(file_path))

        assert "not a directory" in str(exc_info.value)


class TestBuildProcessTasksPrompt:
    """Tests for build_process_tasks_prompt function."""

    def test_prompt_format(self, tmp_path):
        """Test that prompt is formatted correctly."""
        tasks_file = tmp_path / "tasks.md"

        result = build_process_tasks_prompt(tasks_file)

        assert result == f"/af:process_tasks {tasks_file}"


class TestParseAndPrintResults:
    """Tests for parse_and_print_results function."""

    def test_none_results(self):
        """Test handling of None results."""
        count = parse_and_print_results(None)
        assert count == 0

    def test_empty_results(self):
        """Test handling of empty list."""
        count = parse_and_print_results([])
        assert count == 0

    def test_non_list_results(self):
        """Test handling of non-list results."""
        count = parse_and_print_results({"key": "value"})
        assert count == 0

    def test_single_worktree_single_task(self):
        """Test parsing single worktree with single task."""
        results = [
            {
                "worktree_name": "feature-auth",
                "tasks_to_start": [
                    {"description": "Implement login", "tags": ["api", "auth"]}
                ],
            }
        ]

        count = parse_and_print_results(results)

        assert count == 1

    def test_multiple_worktrees_multiple_tasks(self):
        """Test parsing multiple worktrees with multiple tasks."""
        results = [
            {
                "worktree_name": "feature-auth",
                "tasks_to_start": [
                    {"description": "Implement login", "tags": ["api"]},
                    {"description": "Add logout", "tags": []},
                ],
            },
            {
                "worktree_name": "feature-ui",
                "tasks_to_start": [
                    {"description": "Create dashboard", "tags": ["ui", "frontend"]}
                ],
            },
        ]

        count = parse_and_print_results(results)

        assert count == 3

    def test_worktree_with_no_tasks(self):
        """Test worktree with empty tasks list."""
        results = [
            {
                "worktree_name": "feature-empty",
                "tasks_to_start": [],
            }
        ]

        count = parse_and_print_results(results)

        assert count == 0

    def test_task_without_tags(self):
        """Test task that has no tags field."""
        results = [
            {
                "worktree_name": "feature-simple",
                "tasks_to_start": [{"description": "Simple task"}],
            }
        ]

        count = parse_and_print_results(results)

        assert count == 1

    def test_malformed_worktree_data(self):
        """Test handling of malformed worktree data."""
        results = ["not a dict", None, 123]

        count = parse_and_print_results(results)

        assert count == 0


class TestInvokeProcessTasks:
    """Tests for invoke_process_tasks function."""

    def test_dry_run_mode(self, tmp_path):
        """Test that dry run doesn't invoke agent."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("# Tasks\n")

        result = invoke_process_tasks(tasks_file, tmp_path, agent="claude-code", model="standard", dry_run=True)

        assert result == []

    @patch("triggers.find_and_start_tasks.AgentRunner")
    def test_successful_invocation_with_list(self, mock_runner, tmp_path):
        """Test successful agent invocation returning list directly."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("# Tasks\n")

        mock_result = AgentResult(
            success=True,
            output="[]",
            parsed_output=[],
            error=None,
            exit_code=0,
            duration_seconds=1.0,
            agent_name="claude-code",
        )
        mock_runner.run.return_value = mock_result

        result = invoke_process_tasks(tasks_file, tmp_path, agent="claude-code", model="standard", dry_run=False)

        assert result == []
        mock_runner.run.assert_called_once()

    @patch("triggers.find_and_start_tasks.AgentRunner")
    def test_successful_invocation_with_claude_code_structure(self, mock_runner, tmp_path):
        """Test successful invocation with Claude Code nested result structure."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("# Tasks\n")

        # Simulate the actual Claude Code response structure
        parsed_output = {
            "type": "result",
            "subtype": "success",
            "is_error": False,
            "result": 'Here are the tasks:\n\n```json\n[{"worktree_name": "test", "tasks_to_start": [{"description": "Task 1", "tags": ["api"]}]}]\n```',
            "session_id": "test-session",
        }
        mock_result = AgentResult(
            success=True,
            output="",
            parsed_output=parsed_output,
            error=None,
            exit_code=0,
            duration_seconds=1.0,
            agent_name="claude-code",
        )
        mock_runner.run.return_value = mock_result

        result = invoke_process_tasks(tasks_file, tmp_path, agent="claude-code", model="standard", dry_run=False)

        assert result is not None
        assert len(result) == 1
        assert result[0]["worktree_name"] == "test"
        assert result[0]["tasks_to_start"][0]["description"] == "Task 1"

    @patch("triggers.find_and_start_tasks.AgentRunner")
    def test_failed_invocation(self, mock_runner, tmp_path):
        """Test failed agent invocation."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("# Tasks\n")

        mock_result = AgentResult(
            success=False,
            output="",
            parsed_output=None,
            error="Agent failed",
            exit_code=1,
            duration_seconds=1.0,
            agent_name="claude-code",
        )
        mock_runner.run.return_value = mock_result

        result = invoke_process_tasks(tasks_file, tmp_path, agent="claude-code", model="standard", dry_run=False)

        assert result is None

    @patch("triggers.find_and_start_tasks.AgentRunner")
    def test_invocation_exception(self, mock_runner, tmp_path):
        """Test handling of exception during invocation."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("# Tasks\n")

        mock_runner.run.side_effect = Exception("Connection error")

        result = invoke_process_tasks(tasks_file, tmp_path, agent="claude-code", model="standard", dry_run=False)

        assert result is None

    @patch("triggers.find_and_start_tasks.AgentRunner")
    def test_invocation_with_unparseable_response(self, mock_runner, tmp_path):
        """Test handling when agent response cannot be parsed."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("# Tasks\n")

        # Response with no extractable tasks
        parsed_output = {
            "type": "result",
            "result": "Some text without any JSON code blocks.",
        }
        mock_result = AgentResult(
            success=True,
            output="",
            parsed_output=parsed_output,
            error=None,
            exit_code=0,
            duration_seconds=1.0,
            agent_name="claude-code",
        )
        mock_runner.run.return_value = mock_result

        result = invoke_process_tasks(tasks_file, tmp_path, agent="claude-code", model="standard", dry_run=False)

        assert result is None

    @patch("triggers.find_and_start_tasks.AgentRunner")
    def test_invocation_with_custom_agent(self, mock_runner, tmp_path):
        """Test invocation with a custom agent name."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("# Tasks\n")

        mock_result = AgentResult(
            success=True,
            output="[]",
            parsed_output=[],
            error=None,
            exit_code=0,
            duration_seconds=1.0,
            agent_name="opencode",
        )
        mock_runner.run.return_value = mock_result

        result = invoke_process_tasks(tasks_file, tmp_path, agent="opencode", model="standard", dry_run=False)

        assert result == []
        mock_runner.run.assert_called_once_with("opencode", f"/af:process_tasks {tasks_file}", mock_runner.run.call_args[0][2])

    @patch("triggers.find_and_start_tasks.AgentRunner")
    def test_invocation_with_custom_model(self, mock_runner, tmp_path):
        """Test invocation with a custom model type."""
        tasks_file = tmp_path / "tasks.md"
        tasks_file.write_text("# Tasks\n")

        mock_result = AgentResult(
            success=True,
            output="[]",
            parsed_output=[],
            error=None,
            exit_code=0,
            duration_seconds=1.0,
            agent_name="claude-code",
        )
        mock_runner.run.return_value = mock_result

        result = invoke_process_tasks(tasks_file, tmp_path, agent="claude-code", model="thinking", dry_run=False)

        assert result == []
        # Verify the config was passed with the correct model
        call_args = mock_runner.run.call_args
        config = call_args[0][2]
        assert config.model == "thinking"


class TestSetupSignalHandlers:
    """Tests for setup_signal_handlers function."""

    def test_signal_handlers_set(self):
        """Test that signal handlers are configured."""
        ctx = TriggerContext()

        # Store original handlers
        original_sigint = signal.getsignal(signal.SIGINT)
        original_sigterm = signal.getsignal(signal.SIGTERM)

        try:
            setup_signal_handlers(ctx)

            # Verify handlers are set (not the default)
            new_sigint = signal.getsignal(signal.SIGINT)
            new_sigterm = signal.getsignal(signal.SIGTERM)

            assert new_sigint != original_sigint
            assert new_sigterm != original_sigterm
        finally:
            # Restore original handlers
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)


class TestCLI:
    """Tests for the CLI interface."""

    def test_help_option(self):
        """Test that --help works."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "Find and start eligible tasks" in result.output
        assert "--tasks-file" in result.output
        assert "--project-dir" in result.output
        assert "--sync-interval" in result.output
        assert "--dry-run" in result.output
        assert "--single-run" in result.output
        assert "--agent" in result.output
        assert "--model" in result.output

    def test_missing_required_options(self):
        """Test that missing required options cause error."""
        runner = CliRunner()
        result = runner.invoke(main, [])

        assert result.exit_code != 0
        assert "Missing option" in result.output

    def test_missing_tasks_file(self):
        """Test that missing --tasks-file causes error."""
        runner = CliRunner()
        result = runner.invoke(main, ["--project-dir", "."])

        assert result.exit_code != 0
        assert "--tasks-file" in result.output

    def test_missing_project_dir(self):
        """Test that missing --project-dir causes error."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")
            result = runner.invoke(main, ["--tasks-file", "tasks.md"])

        assert result.exit_code != 0
        assert "--project-dir" in result.output

    def test_invalid_tasks_file(self):
        """Test error when tasks file doesn't exist."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                main,
                ["--tasks-file", "nonexistent.md", "--project-dir", "."],
            )

        assert result.exit_code != 0
        assert "does not exist" in result.output

    def test_invalid_project_dir(self):
        """Test error when project dir doesn't exist."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")
            result = runner.invoke(
                main,
                ["--tasks-file", "tasks.md", "--project-dir", "nonexistent_dir"],
            )

        assert result.exit_code != 0
        assert "does not exist" in result.output

    def test_single_run_dry_run(self):
        """Test single-run with dry-run mode."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")
            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--dry-run",
                    "--single-run",
                ],
            )

        assert result.exit_code == 0
        assert "Starting task trigger" in result.output
        assert "DRY-RUN" in result.output
        assert "Single run completed" in result.output

    def test_custom_sync_interval(self):
        """Test custom sync interval is accepted."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")
            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--sync-interval",
                    "60",
                    "--dry-run",
                    "--single-run",
                ],
            )

        assert result.exit_code == 0
        assert "Sync interval: 60s" in result.output

    def test_default_agent(self):
        """Test that default agent is claude-code."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")
            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--dry-run",
                    "--single-run",
                ],
            )

        assert result.exit_code == 0
        assert "Agent: claude-code" in result.output

    def test_custom_agent(self):
        """Test custom agent option is accepted."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")
            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--agent",
                    "opencode",
                    "--dry-run",
                    "--single-run",
                ],
            )

        assert result.exit_code == 0
        assert "Agent: opencode" in result.output

    def test_invalid_agent(self):
        """Test that invalid agent option is rejected."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")
            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--agent",
                    "invalid-agent",
                    "--dry-run",
                    "--single-run",
                ],
            )

        assert result.exit_code != 0
        assert "Invalid value for '--agent'" in result.output

    def test_default_model(self):
        """Test that default model is standard."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")
            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--dry-run",
                    "--single-run",
                ],
            )

        assert result.exit_code == 0
        assert "Model: standard" in result.output

    def test_custom_model(self):
        """Test custom model option is accepted."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")
            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--model",
                    "thinking",
                    "--dry-run",
                    "--single-run",
                ],
            )

        assert result.exit_code == 0
        assert "Model: thinking" in result.output

    def test_light_model(self):
        """Test light model option is accepted."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")
            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--model",
                    "light",
                    "--dry-run",
                    "--single-run",
                ],
            )

        assert result.exit_code == 0
        assert "Model: light" in result.output

    def test_invalid_model(self):
        """Test that invalid model option is rejected."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("tasks.md").write_text("# Tasks\n")
            result = runner.invoke(
                main,
                [
                    "--tasks-file",
                    "tasks.md",
                    "--project-dir",
                    ".",
                    "--model",
                    "invalid-model",
                    "--dry-run",
                    "--single-run",
                ],
            )

        assert result.exit_code != 0
        assert "Invalid value for '--model'" in result.output


class TestLog:
    """Tests for the log function."""

    def test_log_without_dry_run(self, capsys):
        """Test log output without dry run prefix."""
        log("Test message", dry_run=False)

        captured = capsys.readouterr()
        assert "Test message" in captured.out
        assert "[DRY-RUN]" not in captured.out

    def test_log_with_dry_run(self, capsys):
        """Test log output with dry run prefix."""
        log("Test message", dry_run=True)

        captured = capsys.readouterr()
        assert "Test message" in captured.out
        assert "[DRY-RUN]" in captured.out

    def test_log_includes_timestamp(self, capsys):
        """Test that log includes timestamp."""
        log("Test message")

        captured = capsys.readouterr()
        # Check for timestamp format [YYYY-MM-DD HH:MM:SS]
        assert "[20" in captured.out  # Year starts with 20xx
