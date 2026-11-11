import json
from pathlib import Path
from typing import Callable, Optional

from .character_manager import CharacterManager


class CharacterAssetStore:
    def __init__(self, path):
        self.path = Path(path)

    def exists(self) -> bool:
        return self.path.exists()

    def load_state(self, fallback_factory: Optional[Callable[[], CharacterManager]] = None):
        manager, generations, _projects = self.load_workspace_state(fallback_factory)
        return manager, generations

    def load_workspace_state(self, fallback_factory: Optional[Callable[[], CharacterManager]] = None):
        if not self.path.exists():
            if fallback_factory is None:
                return CharacterManager(), [], []
            manager = fallback_factory()
            self.save_state(manager, [], [])
            return manager, [], []

        payload = json.loads(self.path.read_text(encoding="utf-8"))
        manager = CharacterManager()
        manager.characters = payload.get("characters", {})
        manager.memory_store.logs = payload.get("memory_logs", [])
        self._refresh_character_memory(manager)
        return manager, payload.get("generations", []), payload.get("projects", [])

    def load_settings(self) -> dict:
        if not self.path.exists():
            return {}
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return payload.get("settings", {})

    def load_generation_jobs(self) -> list:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return payload.get("generation_jobs", [])

    def load_account(self) -> dict:
        if not self.path.exists():
            return {}
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return payload.get("account", {})

    def save_state(
        self,
        manager: CharacterManager,
        generations=None,
        projects=None,
        settings=None,
        generation_jobs=None,
        account=None,
    ):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        existing_settings = {}
        existing_generation_jobs = []
        existing_account = {}
        if settings is None and self.path.exists():
            existing_settings = self.load_settings()
        if generation_jobs is None and self.path.exists():
            existing_generation_jobs = self.load_generation_jobs()
        if account is None and self.path.exists():
            existing_account = self.load_account()
        payload = {
            "schema_version": 1,
            "characters": manager.characters,
            "memory_logs": manager.memory_store.logs,
            "generations": generations or [],
            "projects": projects or [],
            "settings": settings if settings is not None else existing_settings,
            "generation_jobs": generation_jobs if generation_jobs is not None else existing_generation_jobs,
            "account": account if account is not None else existing_account,
        }
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _refresh_character_memory(self, manager: CharacterManager):
        for character_id in manager.characters:
            manager.characters[character_id]["memory"] = manager.memory_store.character_preferences(character_id)
