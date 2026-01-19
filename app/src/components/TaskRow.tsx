import type { Task } from '../types/models';
import { TaskStatus } from '../types/models';
import { Badge } from './ui/badge';
import { TableCell, TableRow } from './ui/table';

interface TaskRowProps {
  task: Task;
}

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

export function TaskRow({ task }: TaskRowProps) {
  return (
    <TableRow className="h-8">
      <TableCell className="font-mono text-xs hidden md:table-cell py-1">{task.task_id}</TableCell>
      <TableCell className="truncate text-sm py-1">{task.description}</TableCell>
      <TableCell className="py-1">
        <Badge className={`${getStatusColor(task.status)} text-xs py-0 px-2`}>
          {getStatusLabel(task.status)}
        </Badge>
      </TableCell>
      <TableCell className="hidden lg:table-cell py-1">
        <div className="flex gap-1 flex-wrap">
          {task.tags.map((tag) => (
            <Badge key={tag} variant="outline" className="text-xs py-0 px-1.5">
              {tag}
            </Badge>
          ))}
        </div>
      </TableCell>
    </TableRow>
  );
}
