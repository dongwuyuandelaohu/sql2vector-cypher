from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict
import threading
from fastapi import HTTPException
import uuid

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Future] = {}
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=4)  # 控制并发数

    def add_task(self, task_id: str, future: Future):
        with self.lock:
            self.tasks[task_id] = future

    def cancel_task(self, task_id: str):
        with self.lock:
            if task_id not in self.tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            future = self.tasks[task_id]
            future.cancel()
            del self.tasks[task_id]
            return True

    def shutdown(self):
        self.executor.shutdown(wait=False)

task_manager = TaskManager()