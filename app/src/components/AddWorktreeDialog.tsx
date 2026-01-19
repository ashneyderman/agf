import { useState } from 'react';
import type { Worktree, Task } from '../types/models';
import { TaskStatus } from '../types/models';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Plus, X } from 'lucide-react';

interface AddWorktreeDialogProps {
  onAddWorktree: (worktree: Worktree) => void;
}

interface TaskInput {
  id: string;
  description: string;
  tags: string;
}

export function AddWorktreeDialog({ onAddWorktree }: AddWorktreeDialogProps) {
  const [open, setOpen] = useState(false);
  const [worktreeName, setWorktreeName] = useState('');
  const [agent, setAgent] = useState('');
  const [tasks, setTasks] = useState<TaskInput[]>([
    { id: '1', description: '', tags: '' },
  ]);

  const addTask = () => {
    setTasks([...tasks, { id: Date.now().toString(), description: '', tags: '' }]);
  };

  const removeTask = (id: string) => {
    if (tasks.length > 1) {
      setTasks(tasks.filter((t) => t.id !== id));
    }
  };

  const updateTask = (id: string, field: 'description' | 'tags', value: string) => {
    setTasks(
      tasks.map((t) => (t.id === id ? { ...t, [field]: value } : t))
    );
  };

  const generateTaskId = () => {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < 6; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const newTasks: Task[] = tasks
      .filter((t) => t.description.trim())
      .map((t, index) => ({
        task_id: generateTaskId(),
        description: t.description.trim(),
        status: TaskStatus.NOT_STARTED,
        sequence_number: index + 1,
        tags: t.tags
          .split(',')
          .map((tag) => tag.trim())
          .filter((tag) => tag),
        commit_sha: null,
      }));

    const newWorktree: Worktree = {
      worktree_name: worktreeName,
      worktree_id: `wt${String(Date.now()).slice(-3)}`,
      agent: agent || null,
      tasks: newTasks,
      directory_path: null,
      head_sha: null,
    };

    onAddWorktree(newWorktree);

    // Reset form
    setWorktreeName('');
    setAgent('');
    setTasks([{ id: '1', description: '', tags: '' }]);
    setOpen(false);
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="icon">
          <Plus className="h-4 w-4" />
          <span className="sr-only">Add Worktree</span>
        </Button>
      </DialogTrigger>
      <DialogContent
        className="max-w-2xl max-h-[90vh] overflow-y-auto"
        onEscapeKeyDown={(e) => e.preventDefault()}
        onPointerDownOutside={(e) => e.preventDefault()}
        onInteractOutside={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>Add New Worktree</DialogTitle>
          <DialogDescription>
            Create a new worktree with tasks. Fill in the details below.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="worktree-name">Worktree Name *</Label>
              <Input
                id="worktree-name"
                value={worktreeName}
                onChange={(e) => setWorktreeName(e.target.value)}
                placeholder="e.g., feature-user-profile"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="agent">Agent</Label>
              <Input
                id="agent"
                value={agent}
                onChange={(e) => setAgent(e.target.value)}
                placeholder="e.g., claude, human"
              />
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Tasks</Label>
                <Button type="button" variant="outline" size="sm" onClick={addTask}>
                  <Plus className="h-3 w-3 mr-1" />
                  Add Task
                </Button>
              </div>

              {tasks.map((task, index) => (
                <div key={task.id} className="space-y-2 p-3 border rounded-md">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Task {index + 1}</span>
                    {tasks.length > 1 && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => removeTask(task.id)}
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor={`task-desc-${task.id}`}>Description</Label>
                    <Textarea
                      id={`task-desc-${task.id}`}
                      value={task.description}
                      onChange={(e) => updateTask(task.id, 'description', e.target.value)}
                      placeholder="Describe the task..."
                      rows={2}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor={`task-tags-${task.id}`}>Tags (comma-separated)</Label>
                    <Input
                      id={`task-tags-${task.id}`}
                      value={task.tags}
                      onChange={(e) => updateTask(task.id, 'tags', e.target.value)}
                      placeholder="e.g., frontend, ui, react"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={!worktreeName.trim()}>
              Create Worktree
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
