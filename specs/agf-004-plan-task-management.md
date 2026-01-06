# Plan: Task Management System

## Metadata

agf_id: `agf-004`
prompt: `prompts/af-tasks-management-coded.md`
task_type: feature
complexity: complex

## Task Description

Create a comprehensive task management system that can read tasks from various sources (starting with Markdown files), manage task deduplication and state, and provide a conduit between task sources and execution systems. The system includes:

1. **Pydantic Data Models** - Base models for Tasks and Worktrees with validation
2. **TaskSource Protocol** - Interface for reading/updating tasks from different sources
3. **MarkdownTaskSource** - First implementation for reading tasks from Markdown files
4. **TaskManager** - Global singleton for managing tasks, deduplication, and state

Tasks are organized within Worktrees (git worktree containers), with support for task dependencies, blocking states, and rich metadata tracking.

## Objective

When this plan is complete, the system will:
1. Define Pydantic models for Task and Worktree with proper validation
2. Provide a TaskSource protocol for extensible task source implementations
3. Implement MarkdownTaskSource to parse and update tasks in Markdown files
4. Implement TaskManager as a singleton for centralized task state management
5. Support task deduplication by description and worktree deduplication by name
6. Support task status transitions and blocked task detection
7. Enable fetching next available (pending) tasks for execution

## Problem Statement

Agentic Flow needs a robust system to manage tasks across multiple git worktrees. Tasks are defined in various formats (Markdown files, potentially JIRA in the future) and need to be:
- Deduplicated to avoid redundant work
- Tracked with status, IDs, and git SHAs
- Organized within worktrees
- Filtered for availability (handling blocked dependencies)
- Updated at the source when state changes

Without a centralized task management system, each component would need to implement its own task parsing, state tracking, and deduplication logic.

## Solution Approach

Implement a layered architecture:

1. **Data Layer** (`task_manager/models.py`) - Pydantic models for Task and Worktree
2. **Protocol Layer** (`task_manager/source.py`) - TaskSource protocol defining source interface
3. **Source Implementation** (`task_manager/markdown_source.py`) - Parse and update Markdown task lists
4. **Manager Layer** (`task_manager/manager.py`) - TaskManager singleton for state management
5. **Utility Layer** (`task_manager/utils.py`) - Helper functions like generate_short_id

The system uses:
- **Protocol pattern** for extensible task sources
- **Singleton pattern** for centralized task state
- **Pydantic** for validation and type safety
- **Cryptographic randomness** for secure ID generation

## Relevant Files

Use these files to complete the task:

- `pyproject.toml` - Verify pydantic dependency exists, add any new dependencies
- `prompts/af-tasks-management-coded.md` - Source specification with examples and format

### New Files

- `task_manager/__init__.py` - Package exports
- `task_manager/models.py` - Task and Worktree Pydantic models
- `task_manager/utils.py` - Utility functions (generate_short_id)
- `task_manager/source.py` - TaskSource protocol definition
- `task_manager/markdown_source.py` - MarkdownTaskSource implementation
- `task_manager/manager.py` - TaskManager singleton implementation
- `tests/task_manager/__init__.py` - Test package
- `tests/task_manager/test_models.py` - Tests for Pydantic models
- `tests/task_manager/test_utils.py` - Tests for utilities
- `tests/task_manager/test_markdown_source.py` - Tests for Markdown parsing/updating
- `tests/task_manager/test_manager.py` - Tests for TaskManager
- `tests/task_manager/fixtures/` - Directory for test fixture files

## Implementation Phases

### Phase 1: Foundation

- Create `task_manager` package structure
- Implement utility functions (generate_short_id)
- Define Pydantic models for Task and Worktree
- Create comprehensive unit tests for models and utilities

### Phase 2: Core Implementation

- Define TaskSource protocol
- Implement MarkdownTaskSource with parsing logic
- Handle all task status states and emoji markers
- Implement task state updates back to Markdown files
- Create comprehensive tests with fixture files

### Phase 3: Integration & Polish

- Implement TaskManager singleton
- Add task and worktree deduplication logic
- Implement fetch_next_available_tasks with blocking logic
- Add status update and error marking methods
- Create integration tests for full workflows

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Create Package Structure

- Create `task_manager/` directory
- Create `task_manager/__init__.py` with package exports
- Create `tests/task_manager/` directory
- Create `tests/task_manager/__init__.py`
- Create `tests/task_manager/fixtures/` directory for test data

### 2. Implement Utility Functions

Create `task_manager/utils.py` with:
- `generate_short_id(length: int) -> str` function
  - Use `secrets.choice()` for cryptographic randomness
  - Alphabet: `"ABCDEFGHJKLMNPQRSTUWXYZ"` (excludes ambiguous chars)
  - Return random string of specified length

### 3. Define Pydantic Models

Create `task_manager/models.py` with:

**TaskStatus Enum**:
- `NOT_STARTED = "not_started"`
- `BLOCKED = "blocked"`
- `IN_PROGRESS = "in_progress"`
- `COMPLETED = "completed"`
- `FAILED = "failed"`

**Task Model**:
- `task_id: str` - 6-character random ID (generated)
- `description: str` - Task description (required)
- `status: TaskStatus` - Current status (default: NOT_STARTED)
- `sequence_number: int` - Position within worktree (auto-assigned)
- `tags: list[str]` - Optional tags (default: [])
- `commit_sha: str | None` - Git SHA when completed (optional)
- `@field_validator` for task_id to ensure 6 uppercase chars

**Worktree Model**:
- `worktree_name: str` - Name of the git worktree (required)
- `agf_id: str | None` - Unique worktree ID (optional, auto-generated if not provided)
- `tasks: list[Task]` - List of tasks in this worktree (default: [])
- `directory_path: str | None` - Path to worktree directory (optional)
- `head_sha: str | None` - Current HEAD SHA of worktree (optional)
- `@field_validator` for worktree_name to ensure non-empty

**WorktreeInput Model** (for parsing JSON):
- `worktree_name: str`
- `tasks_to_start: list[dict]` - Raw task data with description and optional tags

### 4. Implement TaskSource Protocol

Create `task_manager/source.py` with:

**TaskSource Protocol**:
- `list_worktrees() -> list[Worktree]` - Return all worktrees with tasks
- `update_task_status(worktree_name: str, task_id: str, status: TaskStatus, commit_sha: str | None = None) -> None` - Update task status at source
- `update_task_id(worktree_name: str, sequence_number: int, task_id: str) -> None` - Write generated task_id back to source
- `mark_task_error(worktree_name: str, task_id: str, error_msg: str) -> None` - Mark task with error (implementation-specific)

### 5. Implement MarkdownTaskSource

Create `task_manager/markdown_source.py` with:

**MarkdownTaskSource Class**:
- `__init__(self, file_path: str)` - Store path to Markdown file
- `list_worktrees() -> list[Worktree]`:
  - Read Markdown file
  - Parse worktrees (lines starting with `## `)
  - Extract worktree name and optional `{agf_id}` from header
  - Parse tasks as unordered list items under each worktree
  - Parse task format: `[status, task_id, git_sha] description {tag1, tag2}`
  - Map emoji status to TaskStatus enum:
    - `[]` → NOT_STARTED
    - `[⏰]` → BLOCKED
    - `[🟡]` → IN_PROGRESS
    - `[✅]` → COMPLETED
    - `[❌]` → FAILED
  - Extract task_id (if present)
  - Extract git_sha (if present)
  - Extract tags from `{tag1, tag2}` format
  - Assign sequence_number based on order
  - Return list of Worktree objects with populated tasks

- `update_task_status(worktree_name, task_id, status, commit_sha)`:
  - Read file, find worktree and task by task_id
  - Update status emoji and commit_sha in place
  - Write file back

- `update_task_id(worktree_name, sequence_number, task_id)`:
  - Read file, find worktree and task by sequence
  - Insert task_id into status field
  - Write file back

- `mark_task_error(worktree_name, task_id, error_msg)`:
  - Update task status to FAILED
  - Optionally append error comment after task

**Helper Methods**:
- `_parse_task_line(line: str, sequence: int) -> Task | None` - Parse single task line
- `_status_to_emoji(status: TaskStatus) -> str` - Convert status to emoji
- `_emoji_to_status(emoji: str) -> TaskStatus` - Convert emoji to status
- `_parse_tags(text: str) -> tuple[str, list[str]]` - Extract tags from description

### 6. Implement TaskManager

Create `task_manager/manager.py` with:

**TaskManager Class** (Singleton):
- `_instance: TaskManager | None` - Singleton instance
- `_worktrees: dict[str, Worktree]` - Worktree name → Worktree mapping
- `_task_source: TaskSource` - Reference to task source

**Methods**:
- `__new__(cls)` - Singleton implementation
- `__init__(self, task_source: TaskSource)` - Initialize with task source (only on first call)
- `add_tasks(self, raw_worktrees: list[WorktreeInput]) -> None`:
  - For each input worktree:
    - Check if worktree exists by name (deduplication)
    - If new: create Worktree, generate agf_id if missing
    - For each task in tasks_to_start:
      - Check if task exists by description (deduplication)
      - If new: generate task_id, assign sequence_number, create Task
      - Add to worktree tasks
    - Update `_worktrees` dict
  - Call task_source.update_task_id for new tasks

- `update_task_status(self, worktree_name: str, task_id: str, status: TaskStatus, commit_sha: str | None = None) -> None`:
  - Find task in internal state
  - Update task status and commit_sha
  - Call task_source.update_task_status()

- `mark_task_error(self, worktree_name: str, task_id: str, error_msg: str) -> None`:
  - Update status to FAILED
  - Call task_source.mark_task_error()

- `fetch_next_available_tasks(self, count: int = 1) -> list[Task]`:
  - Iterate through all worktrees
  - For each worktree, find tasks where:
    - Status is NOT_STARTED
    - If status is BLOCKED, check all preceding tasks (by sequence_number):
      - All preceding tasks must be COMPLETED
      - If any preceding task is FAILED, IN_PROGRESS, NOT_STARTED, or BLOCKED → skip this task
  - Collect available tasks up to count
  - Return list of Task objects

- `get_worktree(self, name: str) -> Worktree | None` - Retrieve worktree by name
- `list_worktrees(self) -> list[Worktree]` - Return all worktrees

### 7. Update Package Exports

Update `task_manager/__init__.py` to export:
- `Task`, `Worktree`, `WorktreeInput`, `TaskStatus` from models
- `TaskSource` from source
- `MarkdownTaskSource` from markdown_source
- `TaskManager` from manager
- `generate_short_id` from utils

### 8. Create Unit Tests for Models and Utils

Create `tests/task_manager/test_utils.py`:
- Test `generate_short_id` generates correct length
- Test randomness (multiple calls produce different results)
- Test all chars are from valid alphabet

Create `tests/task_manager/test_models.py`:
- Test Task model creation with all fields
- Test Task model with defaults
- Test Task field validation
- Test Worktree model creation
- Test Worktree with tasks
- Test WorktreeInput parsing from JSON

### 9. Create Unit Tests for MarkdownTaskSource

Create test fixtures in `tests/task_manager/fixtures/`:
- `example_tasks.md` - Sample Markdown file with multiple worktrees and tasks
- `single_worktree.md` - Single worktree for focused testing
- `blocked_tasks.md` - Example with blocked tasks

Create `tests/task_manager/test_markdown_source.py`:
- Test `list_worktrees()` parsing:
  - Correctly parses worktree headers
  - Correctly parses task statuses (all emoji types)
  - Correctly extracts task_id and git_sha
  - Correctly parses tags
  - Assigns proper sequence_numbers
- Test `update_task_status()`:
  - Updates status emoji correctly
  - Adds commit_sha when provided
  - Preserves other task data
- Test `update_task_id()`:
  - Inserts task_id at correct position
  - Preserves existing data
- Test edge cases:
  - Empty file
  - Malformed task lines
  - Missing worktree sections

### 10. Create Unit Tests for TaskManager

Create `tests/task_manager/test_manager.py`:
- Test singleton behavior
- Test `add_tasks()`:
  - Deduplication by worktree name
  - Deduplication by task description
  - Task ID generation for new tasks
  - Sequence number assignment
- Test `update_task_status()`:
  - Updates internal state
  - Calls task_source.update_task_status
- Test `fetch_next_available_tasks()`:
  - Returns NOT_STARTED tasks
  - Skips IN_PROGRESS tasks
  - Handles BLOCKED tasks correctly:
    - Available when all preceding tasks COMPLETED
    - Blocked when any preceding task not COMPLETED
  - Respects count parameter
  - Returns tasks from multiple worktrees
- Test `mark_task_error()`:
  - Sets status to FAILED
  - Calls task_source.mark_task_error

### 11. Create Integration Tests

Create `tests/task_manager/test_integration.py`:
- Test full workflow:
  - Create MarkdownTaskSource from fixture
  - Create TaskManager with source
  - Fetch next tasks
  - Update task statuses
  - Verify changes in Markdown file
- Test blocked task transitions:
  - Start with blocked task
  - Complete preceding task
  - Verify blocked task becomes available

### 12. Validate Implementation

- Run syntax check: `uv run python -m py_compile task_manager/*.py`
- Verify imports: `uv run python -c "from task_manager import TaskManager, Task, Worktree, MarkdownTaskSource"`
- Run all tests: `uv run pytest tests/task_manager/ -v`
- Test with example Markdown file

## Testing Strategy

1. **Unit Tests**:
   - Models: Validate Pydantic validation, defaults, and field types
   - Utils: Test ID generation randomness and alphabet
   - MarkdownTaskSource: Test parsing with fixtures, test updates with temp files
   - TaskManager: Mock TaskSource, test deduplication and state management

2. **Integration Tests**:
   - Full workflow with real MarkdownTaskSource and temp files
   - Task lifecycle: NOT_STARTED → IN_PROGRESS → COMPLETED
   - Blocked task transitions

3. **Edge Cases**:
   - Empty Markdown files
   - Malformed task lines (graceful degradation)
   - Duplicate worktree names
   - Duplicate task descriptions
   - Tasks with no tags
   - Tasks with all optional fields
   - Blocked tasks with failed prerequisites
   - Blocked tasks with in-progress prerequisites

4. **Fixture Files**:
   - Cover all status types
   - Multi-line task descriptions
   - Tasks with and without tags, IDs, SHAs
   - Multiple worktrees in single file

## Acceptance Criteria

- `task_manager` package is properly structured and importable
- Pydantic models validate Task and Worktree data correctly
- `generate_short_id()` produces cryptographically random 6-char IDs
- TaskSource protocol defines clear interface
- MarkdownTaskSource correctly parses all task status emojis
- MarkdownTaskSource correctly extracts task_id, git_sha, tags
- MarkdownTaskSource updates task status in Markdown files
- TaskManager implements singleton pattern
- TaskManager deduplicates worktrees by name
- TaskManager deduplicates tasks by description within worktrees
- `fetch_next_available_tasks()` returns only available (NOT_STARTED) tasks
- Blocked tasks are only available when all preceding tasks are COMPLETED
- Failed tasks block subsequent BLOCKED tasks
- All unit tests pass
- Integration tests demonstrate full workflow

## Validation Commands

Execute these commands to validate the task is complete:

- `uv run python -m py_compile task_manager/*.py` - Verify all Python files compile
- `uv run python -c "from task_manager import TaskManager, Task, Worktree, TaskStatus, MarkdownTaskSource, generate_short_id; print('Imports OK')"` - Verify imports
- `uv run python -c "from task_manager import generate_short_id; print(generate_short_id(6))"` - Test ID generation
- `uv run python -c "from task_manager import TaskStatus; print([s.value for s in TaskStatus])"` - List status values
- `uv run pytest tests/task_manager/ -v` - Run all task_manager tests
- `uv run pytest tests/task_manager/test_models.py -v` - Run model tests
- `uv run pytest tests/task_manager/test_markdown_source.py -v` - Run Markdown source tests
- `uv run pytest tests/task_manager/test_manager.py -v` - Run TaskManager tests

## Notes

### Task Status Emoji Mapping

```python
STATUS_EMOJI = {
    TaskStatus.NOT_STARTED: "[]",
    TaskStatus.BLOCKED: "[⏰]",
    TaskStatus.IN_PROGRESS: "[🟡]",
    TaskStatus.COMPLETED: "[✅]",
    TaskStatus.FAILED: "[❌]",
}
```

### Markdown Task Format

```
## Git Worktree <worktree-name> {<agf_id>}

- [<status>, <task_id>, <git_sha>] <description> {<tag1>, <tag2>}
```

Example:
```
## Git Worktree feature-auth {af_wt_001}

- [✅, ntjnwftq, 17d16d17] Implement login endpoint
- [🟡, qbrlerfg] Add password hashing {security, auth}
- [] Write authentication tests {testing}
- [⏰] Deploy to staging {deployment}
```

### Task Availability Logic

A task is **available** for `fetch_next_available_tasks()` if:
1. `status == NOT_STARTED`, OR
2. `status == BLOCKED` AND all tasks with lower `sequence_number` in the same worktree have `status == COMPLETED`

A task is **not available** if:
- `status != NOT_STARTED and status != BLOCKED`
- `status == BLOCKED` and any preceding task has `status != COMPLETED`

### Deduplication Logic

- **Worktree deduplication**: Compare `worktree_name` (case-sensitive)
- **Task deduplication**: Compare `description` within the same worktree (case-sensitive, exact match)
- When duplicate found: Skip adding, reuse existing

### Dependencies

- `pydantic>=2.0.0` - Already in pyproject.toml
- `pytest>=8.0.0` - Already in dev dependencies
- No additional dependencies needed
