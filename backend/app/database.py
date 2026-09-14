import json
import threading
from pathlib import Path
from typing import Optional
from app.config import settings
from app.models import Project, Job

DB_FILE = settings.DATA_DIR / "vidsnap_store.json"
_lock = threading.Lock()

class Database:
    def __init__(self, db_path: Path = DB_FILE):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with _lock:
            if not self.db_path.exists():
                initial_data = {"projects": {}, "jobs": {}}
                with open(self.db_path, "w", encoding="utf-8") as f:
                    json.dump(initial_data, f, indent=2)

    def _read_data(self) -> dict:
        with _lock:
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {"projects": {}, "jobs": {}}

    def _write_data(self, data: dict):
        with _lock:
            temp_file = self.db_path.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            temp_file.replace(self.db_path)

    # Project Operations
    def save_project(self, project: Project) -> Project:
        data = self._read_data()
        data["projects"][project.id] = project.model_dump()
        self._write_data(data)
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        data = self._read_data()
        p_dict = data.get("projects", {}).get(project_id)
        if p_dict:
            try:
                return Project(**p_dict)
            except Exception:
                return None
        return None

    def list_projects(self) -> list[Project]:
        data = self._read_data()
        projects_dict = data.get("projects", {})
        # Return sorted by created_at descending, gracefully skipping any legacy corrupt entries
        projects: list[Project] = []
        for p in projects_dict.values():
            try:
                # Self-healing: if scenes is a 2-element tuple/list with [scenes, diagnostics]
                scenes = p.get("scenes")
                if isinstance(scenes, list) and len(scenes) == 2 and isinstance(scenes[0], list) and isinstance(scenes[1], list):
                    p["scenes"] = scenes[0]
                    if not p.get("generation_diagnostics"):
                        p["generation_diagnostics"] = scenes[1]
                projects.append(Project(**p))
            except Exception:
                continue
        projects.sort(key=lambda x: x.created_at, reverse=True)
        return projects

    def delete_project(self, project_id: str) -> bool:
        data = self._read_data()
        if project_id in data.get("projects", {}):
            del data["projects"][project_id]
            self._write_data(data)
            return True
        return False

    # Job Operations
    def save_job(self, job: Job) -> Job:
        data = self._read_data()
        data["jobs"][job.id] = job.model_dump()
        self._write_data(data)
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        data = self._read_data()
        j_dict = data.get("jobs", {}).get(job_id)
        if j_dict:
            return Job(**j_dict)
        return None

    def get_job_by_project(self, project_id: str) -> Optional[Job]:
        data = self._read_data()
        for j in data.get("jobs", {}).values():
            if j.get("project_id") == project_id:
                return Job(**j)
        return None

db = Database()
