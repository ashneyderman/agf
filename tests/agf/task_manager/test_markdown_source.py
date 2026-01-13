import tempfile
from pathlib import Path

import pytest

from agf.task_manager.markdown_source import MarkdownTaskSource
from agf.task_manager.models import TaskStatus


@pytest.fixture
def example_tasks_file():
    """Fixture providing path to example tasks file"""
    return Path(__file__).parent / "fixtures" / "example_tasks.md"


@pytest.fixture
def single_worktree_file():
    """Fixture providing path to single worktree file"""
    return Path(__file__).parent / "fixtures" / "single_worktree.md"


@pytest.fixture
def blocked_tasks_file():
    """Fixture providing path to blocked tasks file"""
    return Path(__file__).parent / "fixtures" / "blocked_tasks.md"


@pytest.fixture
def multiline_tasks_file():
    """Fixture providing path to multiline tasks file"""
    return Path(__file__).parent / "fixtures" / "multiline_tasks.md"


@pytest.fixture
def temp_markdown_file():
    """Fixture providing a temporary markdown file"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("""# Test Tasks

## Git Worktree test-wt {TMP001}

- [, tmpidq] Test task one {tag1}
- [🟡, tmpidw] Test task two
""")
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


class TestMarkdownTaskSourceParsing:
    """Tests for parsing Markdown task files"""

    def test_list_worktrees_parses_multiple_worktrees(self, example_tasks_file):
        """Test parsing multiple worktrees from file"""
        source = MarkdownTaskSource(str(example_tasks_file))
        worktrees = source.list_worktrees()

        assert len(worktrees) == 2
        assert worktrees[0].worktree_name == "feature-auth"
        assert worktrees[0].worktree_id == "af_wt_001"
        assert worktrees[1].worktree_name == "feature-ui"
        assert worktrees[1].worktree_id == "af_wt_002"

    def test_parses_task_statuses(self, example_tasks_file):
        """Test that all status emojis are parsed correctly"""
        source = MarkdownTaskSource(str(example_tasks_file))
        worktrees = source.list_worktrees()

        auth_tasks = worktrees[0].tasks

        assert auth_tasks[0].status == TaskStatus.COMPLETED
        assert auth_tasks[1].status == TaskStatus.IN_PROGRESS
        assert auth_tasks[2].status == TaskStatus.NOT_STARTED
        assert auth_tasks[3].status == TaskStatus.BLOCKED

    def test_extracts_task_id_and_sha(self, example_tasks_file):
        """Test extraction of task_id and git_sha"""
        source = MarkdownTaskSource(str(example_tasks_file))
        worktrees = source.list_worktrees()

        task1 = worktrees[0].tasks[0]
        assert task1.task_id == "taskab"
        assert task1.commit_sha == "abc123"

        task2 = worktrees[0].tasks[1]
        assert task2.task_id == "taskcd"
        assert task2.commit_sha is None

    def test_extracts_tags(self, example_tasks_file):
        """Test extraction of tags from task descriptions"""
        source = MarkdownTaskSource(str(example_tasks_file))
        worktrees = source.list_worktrees()

        task1 = worktrees[0].tasks[0]
        assert task1.description == "Implement login endpoint"
        assert task1.tags == ["backend", "auth"]

        task3 = worktrees[0].tasks[2]
        assert task3.description == "Write authentication tests"
        assert task3.tags == ["testing"]

    def test_assigns_sequence_numbers(self, example_tasks_file):
        """Test that sequence numbers are assigned correctly"""
        source = MarkdownTaskSource(str(example_tasks_file))
        worktrees = source.list_worktrees()

        tasks = worktrees[0].tasks
        for i, task in enumerate(tasks):
            assert task.sequence_number == i

    def test_empty_file_returns_empty_list(self):
        """Test that empty file returns empty list"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            temp_path = Path(f.name)

        try:
            source = MarkdownTaskSource(str(temp_path))
            worktrees = source.list_worktrees()
            assert worktrees == []
        finally:
            temp_path.unlink()

    def test_nonexistent_file_returns_empty_list(self):
        """Test that nonexistent file returns empty list"""
        source = MarkdownTaskSource("/nonexistent/file.md")
        worktrees = source.list_worktrees()
        assert worktrees == []

    def test_parses_worktree_without_worktree_id(self, single_worktree_file):
        """Test parsing worktree header without worktree_id"""
        source = MarkdownTaskSource(str(single_worktree_file))
        worktrees = source.list_worktrees()

        assert len(worktrees) == 1
        assert worktrees[0].worktree_name == "test-worktree"
        assert worktrees[0].worktree_id is None

    def test_parses_worktree_with_agent(self):
        """Test parsing worktree with agent field"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("""## Git Worktree ai-feature {AI-001} [@claude]

- [] Task one
- [] Task two
""")
            temp_path = Path(f.name)

        try:
            source = MarkdownTaskSource(str(temp_path))
            worktrees = source.list_worktrees()

            assert len(worktrees) == 1
            assert worktrees[0].worktree_name == "ai-feature"
            assert worktrees[0].worktree_id == "AI-001"
            assert worktrees[0].agent == "claude"
            assert len(worktrees[0].tasks) == 2
        finally:
            temp_path.unlink()

    def test_parses_multiline_task_descriptions(self, multiline_tasks_file):
        """Test parsing tasks with multi-line descriptions"""
        source = MarkdownTaskSource(str(multiline_tasks_file))
        worktrees = source.list_worktrees()

        assert len(worktrees) == 2

        # Check taskab has multi-line description with preserved newlines
        task1 = worktrees[0].tasks[0]
        assert task1.task_id == "taskab"
        assert "second line of the description." in task1.description
        # Verify newline is preserved
        assert "\n" in task1.description
        assert (
            task1.description
            == "Implement login endpoint\nsecond line of the description."
        )
        assert task1.tags == ["backend", "auth"]
        assert task1.status == TaskStatus.COMPLETED

    def test_multiline_preserves_internal_whitespace(self):
        """Test that internal newlines are preserved but leading/trailing are stripped"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("""## Git Worktree test

- [] Line 1
  Line 2
  Line 3 {tag1}
""")
            temp_path = Path(f.name)

        try:
            source = MarkdownTaskSource(str(temp_path))
            worktrees = source.list_worktrees()

            task = worktrees[0].tasks[0]
            # Should have newlines between lines
            assert task.description == "Line 1\nLine 2\nLine 3"
            assert task.tags == ["tag1"]
            # No leading/trailing whitespace
            assert not task.description.startswith(" ")
            assert not task.description.endswith(" ")

        finally:
            temp_path.unlink()


class TestMarkdownTaskSourceUpdates:
    """Tests for updating tasks in Markdown files"""

    def test_update_task_status_changes_emoji(self, temp_markdown_file):
        """Test that update_task_status updates the status emoji"""
        source = MarkdownTaskSource(str(temp_markdown_file))

        # Update status to COMPLETED
        source.update_task_status("test-wt", "tmpidq", TaskStatus.COMPLETED)

        # Read back and verify
        worktrees = source.list_worktrees()
        task = worktrees[0].tasks[0]
        assert task.status == TaskStatus.COMPLETED

    def test_update_task_status_adds_commit_sha(self, temp_markdown_file):
        """Test that update_task_status adds commit SHA"""
        source = MarkdownTaskSource(str(temp_markdown_file))

        # Update with commit SHA
        source.update_task_status("test-wt", "tmpidq", TaskStatus.COMPLETED, "xyz789")

        # Read back and verify
        worktrees = source.list_worktrees()
        task = worktrees[0].tasks[0]
        assert task.status == TaskStatus.COMPLETED
        assert task.commit_sha == "xyz789"

    def test_update_task_id_inserts_id(self):
        """Test that update_task_id inserts task_id"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write("""## Git Worktree test

- [] Task without ID
""")
            temp_path = Path(f.name)

        try:
            source = MarkdownTaskSource(str(temp_path))

            # Insert task_id
            source.update_task_id("test", 0, "newidq")

            # Read back and verify
            worktrees = source.list_worktrees()
            task = worktrees[0].tasks[0]
            assert task.task_id == "newidq"
        finally:
            temp_path.unlink()

    def test_update_preserves_other_data(self, temp_markdown_file):
        """Test that updates preserve other task data"""
        source = MarkdownTaskSource(str(temp_markdown_file))

        # Update status only
        source.update_task_status("test-wt", "tmpidq", TaskStatus.IN_PROGRESS)

        # Read back and verify all data preserved
        worktrees = source.list_worktrees()
        task = worktrees[0].tasks[0]
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.task_id == "tmpidq"
        assert task.description == "Test task one"
        assert task.tags == ["tag1"]

    def test_mark_task_error_sets_failed_status(self, temp_markdown_file):
        """Test that mark_task_error sets status to FAILED"""
        source = MarkdownTaskSource(str(temp_markdown_file))

        # Mark task as error
        source.mark_task_error("test-wt", "tmpidq", "Some error occurred")

        # Read back and verify
        worktrees = source.list_worktrees()
        task = worktrees[0].tasks[0]
        assert task.status == TaskStatus.FAILED


class TestMarkdownTaskSourceHelpers:
    """Tests for helper methods"""

    def test_parse_worktree_header_with_worktree_id(self):
        """Test parsing worktree header with worktree_id"""
        source = MarkdownTaskSource("dummy.md")
        name, worktree_id, agent = source._parse_worktree_header(
            "## Git Worktree my-feature {AF123}"
        )

        assert name == "my-feature"
        assert worktree_id == "AF123"
        assert agent is None

    def test_parse_worktree_header_without_worktree_id(self):
        """Test parsing worktree header without worktree_id"""
        source = MarkdownTaskSource("dummy.md")
        name, worktree_id, agent = source._parse_worktree_header("## Git Worktree my-feature")

        assert name == "my-feature"
        assert worktree_id is None
        assert agent is None

    def test_parse_worktree_header_with_agent(self):
        """Test parsing worktree header with agent"""
        source = MarkdownTaskSource("dummy.md")
        name, worktree_id, agent = source._parse_worktree_header(
            "## Git Worktree my-feature {AF123} [@claude]"
        )

        assert name == "my-feature"
        assert worktree_id == "AF123"
        assert agent == "claude"

    def test_parse_worktree_header_with_agent_no_id(self):
        """Test parsing worktree header with agent but no worktree_id"""
        source = MarkdownTaskSource("dummy.md")
        name, worktree_id, agent = source._parse_worktree_header(
            "## Git Worktree my-feature [@openai]"
        )

        assert name == "my-feature"
        assert worktree_id is None
        assert agent == "openai"

    def test_parse_worktree_header_full_format(self):
        """Test parsing worktree header with all fields"""
        source = MarkdownTaskSource("dummy.md")
        name, worktree_id, agent = source._parse_worktree_header(
            "## Git Worktree feature-xyz {PROJ-5678} [@anthropic]"
        )

        assert name == "feature-xyz"
        assert worktree_id == "PROJ-5678"
        assert agent == "anthropic"

    def test_parse_tags_extracts_correctly(self):
        """Test tag extraction from description"""
        source = MarkdownTaskSource("dummy.md")

        desc1, tags1 = source._parse_tags("Task description {tag1, tag2}")
        assert desc1 == "Task description"
        assert tags1 == ["tag1", "tag2"]

        desc2, tags2 = source._parse_tags("Task without tags")
        assert desc2 == "Task without tags"
        assert tags2 == []

    def test_emoji_status_conversion(self):
        """Test bidirectional emoji/status conversion"""
        source = MarkdownTaskSource("dummy.md")

        assert source._emoji_to_status("[]") == TaskStatus.NOT_STARTED
        assert source._emoji_to_status("[⏰]") == TaskStatus.BLOCKED
        assert source._emoji_to_status("[🟡]") == TaskStatus.IN_PROGRESS
        assert source._emoji_to_status("[✅]") == TaskStatus.COMPLETED
        assert source._emoji_to_status("[❌]") == TaskStatus.FAILED

        assert source._status_to_emoji(TaskStatus.NOT_STARTED) == "[]"
        assert source._status_to_emoji(TaskStatus.BLOCKED) == "[⏰]"
        assert source._status_to_emoji(TaskStatus.IN_PROGRESS) == "[🟡]"
        assert source._status_to_emoji(TaskStatus.COMPLETED) == "[✅]"
        assert source._status_to_emoji(TaskStatus.FAILED) == "[❌]"
