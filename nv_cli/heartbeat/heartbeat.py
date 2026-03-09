"""Heartbeat system for periodic checks."""

import json
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class HeartbeatTask:
    """A periodic task to check."""
    name: str
    description: str
    interval_minutes: int = 60
    last_run: Optional[float] = None
    enabled: bool = True


@dataclass
class HeartbeatState:
    """State of heartbeat checks."""
    tasks: Dict[str, float] = field(default_factory=dict)
    last_heartbeat: Optional[float] = None


class HeartbeatManager:
    """Manages heartbeat tasks."""

    def __init__(self, workspace_dir: Path):
        self.workspace = Path(workspace_dir)
        self.memory_dir = self.workspace / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.memory_dir / "heartbeat-state.json"
        self.tasks: List[HeartbeatTask] = []
        self.state = self._load_state()
        self._load_tasks()

    def _load_state(self) -> HeartbeatState:
        """Load heartbeat state from file."""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                return HeartbeatState(
                    tasks=data.get("tasks", {}),
                    last_heartbeat=data.get("last_heartbeat")
                )
            except Exception:
                pass
        return HeartbeatState()

    def _save_state(self):
        """Save heartbeat state to file."""
        self.state_file.write_text(json.dumps(asdict(self.state), indent=2))

    def _load_tasks(self):
        """Load tasks from HEARTBEAT.md."""
        heartbeat_file = self.workspace / "HEARTBEAT.md"
        if not heartbeat_file.exists():
            return

        content = heartbeat_file.read_text()
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("-"):
                parts = line.lstrip("- ").split(":", 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    desc = parts[1].strip()
                    interval = 60
                    if "(" in desc and "min" in desc.lower():
                        match = re.search(r'(\d+)\s*min', desc)
                        if match:
                            interval = int(match.group(1))
                            desc = desc.split("(")[0].strip()

                    self.tasks.append(HeartbeatTask(
                        name=name,
                        description=desc,
                        interval_minutes=interval
                    ))

    def get_due_tasks(self) -> List[HeartbeatTask]:
        """Get tasks that are due to run."""
        now = time.time()
        due = []
        for task in self.tasks:
            if not task.enabled:
                continue
            last_run = self.state.tasks.get(task.name)
            if last_run is None or (now - last_run) > (task.interval_minutes * 60):
                due.append(task)
        return due

    def mark_complete(self, task_name: str):
        """Mark a task as completed."""
        self.state.tasks[task_name] = time.time()
        self.state.last_heartbeat = time.time()
        self._save_state()

    def is_quiet_hours(self, quiet_start: Optional[int], quiet_end: Optional[int]) -> bool:
        """Check if current time is in quiet hours."""
        if quiet_start is None or quiet_end is None:
            return False
        now = datetime.now().hour
        if quiet_start <= quiet_end:
            return quiet_start <= now < quiet_end
        else:
            return now >= quiet_start or now < quiet_end

    def get_status(self) -> Dict:
        """Get heartbeat status."""
        return {
            "tasks": len(self.tasks),
            "due": len(self.get_due_tasks()),
            "last_heartbeat": self.state.last_heartbeat,
            "tasks_status": [
                {"name": t.name, "last_run": self.state.tasks.get(t.name), "due": t in self.get_due_tasks()}
                for t in self.tasks
            ]
        }

    def add_task(self, name: str, description: str, interval_minutes: int = 60):
        """Add a new task."""
        self.tasks.append(HeartbeatTask(name=name, description=description, interval_minutes=interval_minutes))
        heartbeat_file = self.workspace / "HEARTBEAT.md"
        content = heartbeat_file.read_text() if heartbeat_file.exists() else "# Heartbeat\n\n"
        content += f"\n- {name}: {description} ({interval_minutes} min)\n"
        heartbeat_file.write_text(content)