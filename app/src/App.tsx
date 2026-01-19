import { useState } from "react";
import { ThemeToggle } from "./components/theme-toggle";
import { WorktreeCard } from "./components/WorktreeCard";
import { AddWorktreeDialog } from "./components/AddWorktreeDialog";
import { mockWorktrees } from "./data/mockData";
import type { Worktree } from "./types/models";

function App() {
  const [worktrees, setWorktrees] = useState<Worktree[]>(mockWorktrees);

  const handleAddWorktree = (newWorktree: Worktree) => {
    setWorktrees([newWorktree, ...worktrees]);
  };

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-7xl mx-auto space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-muted-foreground text-sm"></p>
          <div className="flex items-center gap-2">
            <AddWorktreeDialog onAddWorktree={handleAddWorktree} />
            <ThemeToggle />
          </div>
        </div>
        <div className="space-y-3">
          {worktrees.map((worktree) => (
            <WorktreeCard key={worktree.worktree_id} worktree={worktree} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default App;
