import re
import threading
from pathlib import Path

from .models import Task, Worktree, TaskStatus


class MarkdownTaskSource:
    """
    TaskSource implementation that reads and updates tasks in Markdown files.

    Expects Markdown format:
    ## Git Worktree <worktree-name> {<worktree_id>}

    - [<status>, <task_id>, <git_sha>] <description> {<tag1>, <tag2>}
    """

    # Status emoji mapping
    STATUS_EMOJI = {
        TaskStatus.NOT_STARTED: "[]",
        TaskStatus.BLOCKED: "[⏰]",
        TaskStatus.IN_PROGRESS: "[🟡]",
        TaskStatus.COMPLETED: "[✅]",
        TaskStatus.FAILED: "[❌]",
    }

    EMOJI_STATUS = {v: k for k, v in STATUS_EMOJI.items()}

    def __init__(self, file_path: str):
        """
        Initialize with path to Markdown file.

        Args:
            file_path: Path to the Markdown task file
        """
        self.file_path = Path(file_path)
        self._file_lock = threading.Lock()

    def list_worktrees(self) -> list[Worktree]:
        """
        Parse the Markdown file and return all worktrees with tasks.

        Returns:
            List of Worktree objects with populated tasks
        """
        with self._file_lock:
            if not self.file_path.exists():
                return []

            content = self.file_path.read_text()
            lines = content.split('\n')

            worktrees = []
            current_worktree = None
            sequence_number = 0
            current_task_lines = []

            for i, line in enumerate(lines):
                # Check for worktree header
                if line.startswith('## '):
                    # Parse any pending task
                    if current_task_lines and current_worktree:
                        task = self._parse_task_lines(current_task_lines, sequence_number)
                        if task:
                            current_worktree.tasks.append(task)
                            sequence_number += 1
                        current_task_lines = []

                    # Save previous worktree if any
                    if current_worktree:
                        worktrees.append(current_worktree)

                    # Parse new worktree
                    worktree_name, worktree_id = self._parse_worktree_header(line)
                    current_worktree = Worktree(
                        worktree_name=worktree_name,
                        worktree_id=worktree_id,
                        tasks=[]
                    )
                    sequence_number = 0

                # Check for task line (unordered list item)
                elif line.strip().startswith('- [') and current_worktree:
                    # Parse any previous task
                    if current_task_lines:
                        task = self._parse_task_lines(current_task_lines, sequence_number)
                        if task:
                            current_worktree.tasks.append(task)
                            sequence_number += 1

                    # Start new task
                    current_task_lines = [line]

                # Check for continuation line (indented, following a task)
                elif current_task_lines and line and line[0] in ' \t' and current_worktree:
                    current_task_lines.append(line)

                # Empty line or other content - finish current task if any
                elif current_task_lines and current_worktree:
                    task = self._parse_task_lines(current_task_lines, sequence_number)
                    if task:
                        current_worktree.tasks.append(task)
                        sequence_number += 1
                    current_task_lines = []

            # Parse any final pending task
            if current_task_lines and current_worktree:
                task = self._parse_task_lines(current_task_lines, sequence_number)
                if task:
                    current_worktree.tasks.append(task)

            # Don't forget the last worktree
            if current_worktree:
                worktrees.append(current_worktree)

            return worktrees

    def update_task_status(
        self,
        worktree_name: str,
        task_id: str,
        status: TaskStatus,
        commit_sha: str | None = None
    ) -> None:
        """
        Update task status in the Markdown file.

        Args:
            worktree_name: Name of the worktree
            task_id: ID of the task to update
            status: New status
            commit_sha: Optional commit SHA to add
        """
        with self._file_lock:
            content = self.file_path.read_text()
            lines = content.split('\n')

            current_worktree = None
            updated_lines = []

            for line in lines:
                if line.startswith('## '):
                    wt_name, _ = self._parse_worktree_header(line)
                    current_worktree = wt_name
                    updated_lines.append(line)
                elif line.strip().startswith('- [') and current_worktree == worktree_name:
                    # Check if this is the task we're looking for
                    if f', {task_id},' in line or f', {task_id}]' in line:
                        # Update this task
                        updated_line = self._update_task_line(line, status, commit_sha)
                        updated_lines.append(updated_line)
                    else:
                        updated_lines.append(line)
                else:
                    updated_lines.append(line)

            self.file_path.write_text('\n'.join(updated_lines))

    def update_task_id(
        self,
        worktree_name: str,
        sequence_number: int,
        task_id: str
    ) -> None:
        """
        Write a generated task_id back to the Markdown file.

        Args:
            worktree_name: Name of the worktree
            sequence_number: Position of the task in the worktree
            task_id: The task ID to insert
        """
        with self._file_lock:
            content = self.file_path.read_text()
            lines = content.split('\n')

            current_worktree = None
            current_sequence = 0
            updated_lines = []

            for line in lines:
                if line.startswith('## '):
                    wt_name, _ = self._parse_worktree_header(line)
                    current_worktree = wt_name
                    current_sequence = 0
                    updated_lines.append(line)
                elif line.strip().startswith('- [') and current_worktree == worktree_name:
                    if current_sequence == sequence_number:
                        # Insert task_id into this line
                        updated_line = self._insert_task_id(line, task_id)
                        updated_lines.append(updated_line)
                    else:
                        updated_lines.append(line)
                    current_sequence += 1
                else:
                    updated_lines.append(line)

            self.file_path.write_text('\n'.join(updated_lines))

    def mark_task_error(
        self,
        worktree_name: str,
        task_id: str,
        error_msg: str
    ) -> None:
        """
        Mark a task as failed.

        Args:
            worktree_name: Name of the worktree
            task_id: ID of the task
            error_msg: Error message (currently not written to file)
        """
        # Simply update status to FAILED
        self.update_task_status(worktree_name, task_id, TaskStatus.FAILED)

    def _parse_worktree_header(self, line: str) -> tuple[str, str | None]:
        """
        Parse worktree header line.

        Args:
            line: Header line like "## Git Worktree feature-auth {SCHIP-7899}"

        Returns:
            Tuple of (worktree_name, worktree_id)
        """
        # Remove "##" and strip
        header = line[2:].strip()

        # Extract worktree_id if present (in curly braces)
        worktree_id = None
        match = re.search(r'\{([^}]+)\}', header)
        if match:
            worktree_id = match.group(1)
            # Remove the worktree_id part from header
            header = header[:match.start()].strip()

        # Extract worktree name (after "Git Worktree")
        if header.startswith('Git Worktree '):
            worktree_name = header[13:].strip()
        else:
            worktree_name = header

        return worktree_name, worktree_id

    def _parse_task_lines(self, lines: list[str], sequence: int) -> Task | None:
        """
        Parse a task from one or more lines (supporting multi-line descriptions).

        Args:
            lines: List of lines making up the task (first line is the task line, rest are continuations)
            sequence: Sequence number for this task

        Returns:
            Task object or None if parsing fails
        """
        if not lines:
            return None

        # Parse the first line for status, task_id, git_sha
        first_line = lines[0].strip()
        match = re.match(r'^-\s*\[(.*?)\]\s*(.*)$', first_line)
        if not match:
            return None

        status_part = match.group(1).strip()
        first_line_rest = match.group(2).strip()

        # Parse status, task_id, git_sha from status_part
        parts = [p.strip() for p in status_part.split(',')]

        # First part is status emoji
        status_str = parts[0] if parts else ''
        status = self._emoji_to_status(f'[{status_str}]' if status_str else '[]')

        # Second part is task_id (if present)
        task_id = parts[1] if len(parts) > 1 and parts[1] else None

        # Third part is git_sha (if present)
        git_sha = parts[2] if len(parts) > 2 and parts[2] else None

        # Combine all lines for the full description, preserving internal newlines
        description_parts = [first_line_rest]
        for line in lines[1:]:
            # Strip leading/trailing whitespace from each line
            description_parts.append(line.strip())

        # Join with newlines to preserve structure
        full_text = '\n'.join(description_parts)

        # Parse description and tags from the combined text
        description, tags = self._parse_tags(full_text)

        # Strip leading/trailing whitespace from final description
        description = description.strip()

        # Generate task_id if not present
        if not task_id:
            from .utils import generate_short_id
            task_id = generate_short_id(6)

        return Task(
            task_id=task_id,
            description=description,
            status=status,
            sequence_number=sequence,
            tags=tags,
            commit_sha=git_sha
        )

    def _parse_task_line(self, line: str, sequence: int) -> Task | None:
        """
        Parse a single task line.

        Args:
            line: Task line like "- [✅, ntjnwftq, 17d16d17] Implement login endpoint"
            sequence: Sequence number for this task

        Returns:
            Task object or None if parsing fails
        """
        # Pattern: - [status(, task_id)(, git_sha)] description {tags}
        # Status can be emoji or empty brackets
        match = re.match(r'^-\s*\[(.*?)\]\s*(.*)$', line.strip())
        if not match:
            return None

        status_part = match.group(1).strip()
        rest = match.group(2).strip()

        # Parse status, task_id, git_sha from status_part
        parts = [p.strip() for p in status_part.split(',')]

        # First part is status emoji
        status_str = parts[0] if parts else ''
        status = self._emoji_to_status(f'[{status_str}]' if status_str else '[]')

        # Second part is task_id (if present)
        task_id = parts[1] if len(parts) > 1 and parts[1] else None

        # Third part is git_sha (if present)
        git_sha = parts[2] if len(parts) > 2 and parts[2] else None

        # Parse description and tags
        description, tags = self._parse_tags(rest)

        # Generate task_id if not present
        if not task_id:
            from .utils import generate_short_id
            task_id = generate_short_id(6)

        return Task(
            task_id=task_id,
            description=description,
            status=status,
            sequence_number=sequence,
            tags=tags,
            commit_sha=git_sha
        )

    def _parse_tags(self, text: str) -> tuple[str, list[str]]:
        """
        Extract tags from description.

        Args:
            text: Text like "Description {tag1, tag2}"

        Returns:
            Tuple of (description, list of tags)
        """
        # Look for tags in curly braces at the end
        match = re.search(r'\{([^}]+)\}\s*$', text)
        if match:
            tags_str = match.group(1)
            tags = [t.strip() for t in tags_str.split(',')]
            description = text[:match.start()].strip()
            return description, tags

        return text.strip(), []

    def _emoji_to_status(self, emoji: str) -> TaskStatus:
        """
        Convert emoji to TaskStatus.

        Args:
            emoji: Status emoji like "[✅]"

        Returns:
            TaskStatus enum value
        """
        return self.EMOJI_STATUS.get(emoji, TaskStatus.NOT_STARTED)

    def _status_to_emoji(self, status: TaskStatus) -> str:
        """
        Convert TaskStatus to emoji.

        Args:
            status: TaskStatus enum value

        Returns:
            Status emoji string
        """
        return self.STATUS_EMOJI.get(status, "[]")

    def _update_task_line(
        self,
        line: str,
        status: TaskStatus,
        commit_sha: str | None
    ) -> str:
        """
        Update the status (and optionally commit_sha) in a task line.

        Args:
            line: Original task line
            status: New status
            commit_sha: Optional new commit SHA

        Returns:
            Updated line
        """
        # Parse the existing line
        match = re.match(r'^(-\s*\[)(.*?)(\]\s*.*)$', line.strip())
        if not match:
            return line

        prefix = match.group(1)
        status_part = match.group(2).strip()
        suffix = match.group(3)

        # Parse existing parts
        parts = [p.strip() for p in status_part.split(',')]

        # Update status (first part)
        new_emoji = self._status_to_emoji(status)
        # Remove brackets from emoji for insertion
        new_emoji = new_emoji[1:-1] if new_emoji.startswith('[') else new_emoji

        # Keep task_id (second part) if present
        task_id = parts[1] if len(parts) > 1 and parts[1] else None

        # Update or keep git_sha (third part)
        if commit_sha:
            git_sha = commit_sha
        else:
            git_sha = parts[2] if len(parts) > 2 and parts[2] else None

        # Reconstruct status_part
        new_parts = [new_emoji]
        if task_id:
            new_parts.append(task_id)
        if git_sha:
            new_parts.append(git_sha)

        new_status_part = ', '.join(new_parts)

        return f"{prefix}{new_status_part}{suffix}"

    def _insert_task_id(self, line: str, task_id: str) -> str:
        """
        Insert task_id into a task line that doesn't have one.

        Args:
            line: Original task line
            task_id: Task ID to insert

        Returns:
            Updated line with task_id
        """
        match = re.match(r'^(-\s*\[)(.*?)(\]\s*.*)$', line.strip())
        if not match:
            return line

        prefix = match.group(1)
        status_part = match.group(2).strip()
        suffix = match.group(3)

        # Parse existing parts
        parts = [p.strip() for p in status_part.split(',')]

        # If task_id already exists, don't add it again
        if len(parts) > 1 and parts[1]:
            return line

        # Insert task_id as second part
        if len(parts) == 1:
            # Just status, add task_id
            new_status_part = f"{parts[0]}, {task_id}"
        elif len(parts) == 2:
            # Status and empty task_id, fill it
            new_status_part = f"{parts[0]}, {task_id}"
        else:
            # Status, empty task_id, and git_sha - insert task_id in middle
            new_status_part = f"{parts[0]}, {task_id}, {parts[2]}"

        return f"{prefix}{new_status_part}{suffix}"
