export const TaskStatus = {
  NOT_STARTED: "not_started",
  BLOCKED: "blocked",
  IN_PROGRESS: "in_progress",
  COMPLETED: "completed",
  FAILED: "failed",
} as const;

export type TaskStatus = (typeof TaskStatus)[keyof typeof TaskStatus];

export interface Task {
  task_id: string;
  description: string;
  status: TaskStatus;
  sequence_number: number;
  tags: string[];
  commit_sha: string | null;
}

export interface Worktree {
  worktree_name: string;
  worktree_id: string | null;
  agent: string | null;
  tasks: Task[];
  directory_path: string | null;
  head_sha: string | null;
}
