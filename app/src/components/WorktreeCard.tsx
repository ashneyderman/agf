import type { Worktree } from '../types/models';
import { TaskStatus } from '../types/models';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Table, TableBody, TableHead, TableHeader, TableRow } from './ui/table';
import { TaskRow } from './TaskRow';

interface WorktreeCardProps {
  worktree: Worktree;
}

const calculateOverallStatus = (worktree: Worktree): TaskStatus => {
  if (worktree.tasks.length === 0) {
    return TaskStatus.NOT_STARTED;
  }

  const hasFailedTasks = worktree.tasks.some(task => task.status === TaskStatus.FAILED);
  if (hasFailedTasks) {
    return TaskStatus.FAILED;
  }

  const hasBlockedTasks = worktree.tasks.some(task => task.status === TaskStatus.BLOCKED);
  if (hasBlockedTasks) {
    return TaskStatus.BLOCKED;
  }

  const hasInProgressTasks = worktree.tasks.some(task => task.status === TaskStatus.IN_PROGRESS);
  if (hasInProgressTasks) {
    return TaskStatus.IN_PROGRESS;
  }

  const allCompleted = worktree.tasks.every(task => task.status === TaskStatus.COMPLETED);
  if (allCompleted) {
    return TaskStatus.COMPLETED;
  }

  return TaskStatus.NOT_STARTED;
};

const getStatusColor = (status: TaskStatus): string => {
  switch (status) {
    case TaskStatus.COMPLETED:
      return 'bg-green-500/10 text-green-500 hover:bg-green-500/20';
    case TaskStatus.IN_PROGRESS:
      return 'bg-blue-500/10 text-blue-500 hover:bg-blue-500/20';
    case TaskStatus.BLOCKED:
      return 'bg-yellow-500/10 text-yellow-500 hover:bg-yellow-500/20';
    case TaskStatus.FAILED:
      return 'bg-red-500/10 text-red-500 hover:bg-red-500/20';
    case TaskStatus.NOT_STARTED:
      return 'bg-gray-500/10 text-gray-500 hover:bg-gray-500/20';
    default:
      return 'bg-gray-500/10 text-gray-500 hover:bg-gray-500/20';
  }
};

const getStatusLabel = (status: TaskStatus): string => {
  switch (status) {
    case TaskStatus.NOT_STARTED:
      return 'Not Started';
    case TaskStatus.IN_PROGRESS:
      return 'In Progress';
    case TaskStatus.BLOCKED:
      return 'Blocked';
    case TaskStatus.COMPLETED:
      return 'Completed';
    case TaskStatus.FAILED:
      return 'Failed';
    default:
      return status;
  }
};

export function WorktreeCard({ worktree }: WorktreeCardProps) {
  const overallStatus = calculateOverallStatus(worktree);
  const taskCount = worktree.tasks.length;
  const completedCount = worktree.tasks.filter(t => t.status === TaskStatus.COMPLETED).length;

  return (
    <Card className="w-full">
      <CardHeader className="py-3 px-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle>
              {worktree.worktree_name}
            </CardTitle>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {worktree.agent && (
                <span className="flex items-center gap-1">
                  Agent: <span className="font-medium">{worktree.agent}</span>
                </span>
              )}
              {worktree.worktree_id && (
                <span className="flex items-center gap-1">
                  ID: <span className="font-mono">{worktree.worktree_id}</span>
                </span>
              )}
            </div>
          </div>
          <div className="flex flex-col items-end gap-1">
            <Badge className={getStatusColor(overallStatus)}>
              {getStatusLabel(overallStatus)}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {completedCount} / {taskCount} tasks completed
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="py-2 px-4">
        {worktree.tasks.length > 0 ? (
          <Table className="table-fixed">
            <TableHeader>
              <TableRow className="border-b">
                <TableHead className="w-[120px] hidden md:table-cell h-8 py-2 text-xs">Task ID</TableHead>
                <TableHead className="h-8 py-2 text-xs">Description</TableHead>
                <TableHead className="w-[140px] h-8 py-2 text-xs">Status</TableHead>
                <TableHead className="w-[200px] hidden lg:table-cell h-8 py-2 text-xs">Tags</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {worktree.tasks.map((task) => (
                <TaskRow key={task.task_id} task={task} />
              ))}
            </TableBody>
          </Table>
        ) : (
          <div className="text-center py-8 text-muted-foreground">
            No tasks in this worktree
          </div>
        )}
      </CardContent>
    </Card>
  );
}
