# Chore: Add `--install-only` CLI option to `agf` CLI

## Metadata

agf_id: `agf-035`
prompt: `Add new CLI option --install-only. It will run the installer for the project and exit. No tasks processing will be done.`

## Chore Description

Add a `--install-only` CLI flag to the `agf` CLI (`process_tasks.py`). When this flag is specified, the script will:
1. Load configuration as usual
2. Run the `Installer` to install AGF commands to the project directory (not a worktree)
3. Exit immediately without initializing the TaskManager or processing any tasks

This is useful for setting up a project with AGF commands without running any task processing. The installer will:
- Copy the `.agf_config` directory to the project's `.agf` directory
- Create symlinks for agent command directories (claude-code and opencode)
- Update `.gitignore` with the necessary entries

The implementation requires:
1. Adding the `--install-only` flag to the CLI options in `process_tasks.py`
2. Adding an `install_only` field to `CLIConfig` and `EffectiveConfig` models
3. Updating `merge_configs` in `loader.py` to handle the new field
4. Creating a temporary Worktree object pointing to the project directory for the Installer
5. Modifying the main function to check for install-only mode and exit after installation
6. Adding tests for the new functionality

## Relevant Files

Use these files to complete the chore:

- `agf/triggers/process_tasks.py` - The CLI entry point where the `--install-only` option needs to be added. Contains the `main` function that orchestrates the task processing workflow.
- `agf/config/models.py` - Contains `CLIConfig` and `EffectiveConfig` pydantic models that need the new `install_only` field.
- `agf/config/loader.py` - Contains `merge_configs` function that merges AGFConfig and CLIConfig into EffectiveConfig.
- `agf/installer.py` - Contains the `Installer` class that handles command installation. Already has `install_commands()` method.
- `agf/task_manager/models.py` - Contains `Worktree` model definition, needed to create a temporary worktree for the installer.
- `tests/agf/triggers/test_process_tasks.py` - Contains tests for the CLI interface.
- `tests/config/test_cli_config.py` - Contains tests for CLIConfig model.

### New Files

None - all changes are to existing files.

## Step by Step Tasks

IMPORTANT: Execute every step in order, top to bottom.

### 1. Add `install_only` field to `CLIConfig` in `agf/config/models.py`

- Add a new field `install_only: bool = False` to the `CLIConfig` class (after `testing` field, around line 174)
- Update the class docstring to document the new field:
  ```
  install_only: Install commands only mode - install AGF commands and exit (default: False)
  ```

### 2. Add `install_only` field to `EffectiveConfig` in `agf/config/models.py`

- Add a new field `install_only: bool` to the `EffectiveConfig` class (after `testing` field, around line 240)
- Update the class docstring to document the new field under "Fields from CLIConfig":
  ```
  install_only: Install commands only mode flag
  ```

### 3. Update `merge_configs` in `agf/config/loader.py` to handle `install_only` field

- Read the file to understand the current `merge_configs` implementation
- Add `install_only=cli_config.install_only` to the `EffectiveConfig` constructor call

### 4. Add `--install-only` CLI option to `process_tasks.py`

- Add a new `@click.option` decorator for `--install-only` flag (after `--testing` option, around line 348):
  ```python
  @click.option(
      "--install-only",
      is_flag=True,
      default=False,
      help="Install AGF commands to the project directory and exit without processing tasks",
  )
  ```
- Add `install_only: bool` parameter to the `main` function signature
- Pass `install_only=install_only` to `CLIConfig` constructor

### 5. Implement install-only mode logic in `main` function

- After configuration loading and logging but BEFORE TaskManager initialization (around line 428), add the install-only check:
  ```python
  # Install-only mode
  if effective_config.install_only:
      log("Running in install-only mode")

      # Create a temporary worktree pointing to project directory
      from agf.task_manager.models import Worktree
      temp_worktree = Worktree(
          worktree_name="project",
          worktree_id=None,
          tasks=[],
          directory_path=str(project_dir),
      )

      # Install commands
      from agf.installer import Installer
      installer = Installer(effective_config, temp_worktree)
      installer.install_commands()

      log(f"AGF commands installed to: {project_dir}")
      log("Install-only completed, exiting")
      return
  ```
- Add logging to show install-only mode status in the startup logs (after line 422):
  ```python
  log(f"Install only: {effective_config.install_only}")
  ```

### 6. Add CLI tests for `--install-only` option

- In `tests/agf/triggers/test_process_tasks.py`, add new test methods to the `TestCLI` class:

- Add test method `test_install_only_option_in_help`:
  ```python
  def test_install_only_option_in_help(self):
      """Test that --install-only appears in help."""
      runner = CliRunner()
      result = runner.invoke(main, ["--help"])

      assert result.exit_code == 0
      assert "--install-only" in result.output
  ```

- Add test method `test_install_only_mode`:
  ```python
  def test_install_only_mode(self):
      """Test install-only mode installs commands and exits."""
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
                  "--install-only",
              ],
          )

      assert result.exit_code == 0
      assert "Running in install-only mode" in result.output
      assert "Install-only completed" in result.output
      # Should NOT initialize TaskManager or process tasks
      assert "Initialized TaskManager" not in result.output
  ```

- Add test method `test_install_only_creates_agf_directory`:
  ```python
  def test_install_only_creates_agf_directory(self):
      """Test that install-only creates .agf directory."""
      runner = CliRunner()
      with runner.isolated_filesystem():
          Path("tasks.md").write_text("# Tasks\n")

          agf_dir = Path(".agf")
          assert not agf_dir.exists()

          result = runner.invoke(
              main,
              [
                  "--tasks-file",
                  "tasks.md",
                  "--project-dir",
                  ".",
                  "--install-only",
              ],
          )

      assert result.exit_code == 0
      assert agf_dir.exists()
      assert (agf_dir / "claude" / "commands").exists()
      assert (agf_dir / "opencode" / "skill").exists()
  ```

- Add test method `test_install_only_creates_symlinks`:
  ```python
  def test_install_only_creates_symlinks(self):
      """Test that install-only creates command symlinks."""
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
                  "--install-only",
              ],
          )

      assert result.exit_code == 0
      claude_symlink = Path(".claude") / "commands" / "agf"
      opencode_symlink = Path(".opencode") / "skill" / "agf"
      assert claude_symlink.is_symlink()
      assert opencode_symlink.is_symlink()
  ```

- Add test method `test_install_only_updates_gitignore`:
  ```python
  def test_install_only_updates_gitignore(self):
      """Test that install-only updates .gitignore."""
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
                  "--install-only",
              ],
          )

      assert result.exit_code == 0
      gitignore = Path(".gitignore")
      assert gitignore.exists()
      content = gitignore.read_text()
      assert ".agf/" in content
  ```

### 7. Update existing test fixtures to include `install_only` field

- In `tests/agf/triggers/test_process_tasks.py`, find any `EffectiveConfig` constructor calls and add `install_only=False` parameter
- In `tests/agf/workflow/test_task_handler.py`, update all `EffectiveConfig` constructor calls to include `install_only=False`
- In `tests/agf/test_installer.py`, update the `mock_effective_config` fixture to include `install_only=False`
- In `tests/config/test_config_integration.py`, update any `EffectiveConfig` constructor calls to include `install_only=False`

### 8. Validate the implementation

- Run tests to ensure all tests pass including the new tests
- Run the code compilation check to ensure no syntax errors

## Validation Commands

Execute these commands to validate the chore is complete:

- `uv run python -m py_compile agf/config/models.py` - Verify config models compile
- `uv run python -m py_compile agf/config/loader.py` - Verify loader compiles
- `uv run python -m py_compile agf/triggers/process_tasks.py` - Verify CLI compiles
- `uv run pytest tests/agf/triggers/test_process_tasks.py -v` - Run all CLI tests
- `uv run pytest tests/agf/triggers/test_process_tasks.py::TestCLI::test_install_only_mode -v` - Run the specific new tests
- `uv run pytest tests/ -v` - Run all tests to ensure no regressions
- `uv run agf/triggers/process_tasks.py --help` - Verify the new `--install-only` option appears in help

## Notes

- The `--install-only` flag allows setting up AGF commands in a project without running any task processing
- This is particularly useful for initial project setup or when updating AGF commands independently
- The install-only mode does NOT require a valid tasks file with actual tasks - only the file must exist
- The installation uses the `project_dir` as the target directory, not a worktree
- A temporary `Worktree` object is created with `directory_path` set to the project directory to satisfy the `Installer` constructor requirements
- The `--install-only` flag is mutually compatible with other flags like `--dry-run`, but dry-run has no effect since no tasks are processed
- After installation, the script exits with code 0 (success)
