import re
from copy import deepcopy
from typing import Any, Dict, Optional

from .fusion_engine import FusionEngine
from .identity_model import IdentityModel
from .memory_store import MemoryStore
from .style_model import StyleModel


class CharacterManager:
    def __init__(self):
        self.characters = {}  # character_id -> character_data
        self.memory_store = MemoryStore()

    def create_character(
        self,
        name: str,
        identity_config: Optional[Dict[str, Any]] = None,
        style_config: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        角色创建 / 编辑 / 版本.
        """
        identity_config = identity_config or {}
        character_id = identity_config.get("character_id") or self._make_character_id(name)
        identity_profile = None
        style_profile = None

        face_images = identity_config.get("face_images")
        if face_images:
            identity_model = IdentityModel()
            identity_profile = identity_model.encode_faces(face_images)

        if style_config:
            style_profile = StyleModel().encode_style(style_config)

        character = {
            "id": character_id,
            "name": name,
            "version": 1,
            "identity": identity_profile,
            "reference_assets": self._reference_assets_from_faces(face_images or []),
            "style": style_profile,
            "consistency_score": self._initial_consistency_score(identity_profile),
            "versions": [],
            "memory": {
                "best_angles": [],
                "preferred_styles": [],
                "average_success_score": 0.0,
            },
        }
        character["versions"].append(self._version_snapshot(character, note="initial"))
        self.characters[character_id] = character
        return character

    def create_version(
        self,
        character_id: str,
        identity_config: Optional[Dict[str, Any]] = None,
        style_config: Optional[Any] = None,
        note: str = "update",
    ) -> Dict[str, Any]:
        character = self._require_character(character_id)
        if identity_config and identity_config.get("face_images"):
            character["identity"] = IdentityModel().encode_faces(identity_config["face_images"])
        if style_config:
            character["style"] = StyleModel().encode_style(style_config)
        character["version"] += 1
        character["consistency_score"] = self._initial_consistency_score(character.get("identity"))
        snapshot = self._version_snapshot(character, note=note)
        character["versions"].append(snapshot)
        return snapshot

    def update_character(
        self,
        character_id: str,
        name: Optional[str] = None,
        prompt: Optional[str] = None,
        style_config: Optional[Any] = None,
        tags: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        character = self._require_character(character_id)
        if name is not None:
            clean_name = str(name).strip()
            if not clean_name:
                raise ValueError("name cannot be empty")
            character["name"] = clean_name
        if prompt is not None:
            character["prompt"] = str(prompt).strip()
        if style_config is not None:
            character["style"] = StyleModel().encode_style(style_config)
        if tags is not None:
            character["tags"] = list(dict.fromkeys(str(tag).strip() for tag in tags if str(tag).strip()))[:12]
        return deepcopy(character)

    def update_reference_assets(self, character_id: str, reference_assets: list[Dict[str, Any]]) -> Dict[str, Any]:
        character = self._require_character(character_id)
        character["reference_assets"] = deepcopy(reference_assets)
        return deepcopy(character)

    def restore_version(self, character_id: str, version: int, note: Optional[str] = None) -> Dict[str, Any]:
        character = self._require_character(character_id)
        snapshot = self._find_version_snapshot(character, version)
        if not self._snapshot_can_restore(snapshot):
            raise ValueError(f"Version v{version} does not include recoverable identity/style data.")

        character["identity"] = deepcopy(snapshot.get("identity_snapshot"))
        character["style"] = deepcopy(snapshot.get("style_snapshot"))
        if "prompt_snapshot" in snapshot:
            character["prompt"] = snapshot.get("prompt_snapshot")
        character["consistency_score"] = float(
            snapshot.get("consistency_score", self._initial_consistency_score(character.get("identity")))
        )
        character["version"] += 1
        restored = self._version_snapshot(
            character,
            note=note or f"restore v{version}",
            restored_from=version,
        )
        character["versions"].append(restored)
        return restored

    def build_conditioning(
        self,
        character_id: str,
        prompt: str,
        state: str = "calm",
        identity_weight: float = 0.7,
        style_weight: float = 0.6,
        prompt_weight: float = 1.0,
        state_weight: float = 0.4,
        lora_id: Optional[str] = None,
        lora_weight: Optional[float] = None,
        enforce_identity_priority: bool = True,
    ) -> Dict[str, Any]:
        character = self._require_character(character_id)
        identity_vector = character.get("identity") or {}
        style_vector = self._style_with_lora(character.get("style") or {}, lora_id, lora_weight)
        fused = FusionEngine(
            identity_weight=identity_weight,
            style_weight=style_weight,
            prompt_weight=prompt_weight,
            state_weight=state_weight,
            enforce_identity_priority=enforce_identity_priority,
        ).fuse(identity_vector, style_vector, prompt, state)
        fused["character_id"] = character_id
        fused["character_version"] = character["version"]
        fused["style"] = self._conditioning_style_summary(style_vector)
        fused["lora"] = style_vector.get("lora")
        return fused

    def record_scene(
        self,
        character_id: str,
        prompt: str,
        image: Any,
        pose: str,
        success_score: float,
        style: Optional[str] = None,
        state: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self._require_character(character_id)
        entry = self.memory_store.add_entry(
            prompt=prompt,
            image=image,
            pose=pose,
            success_score=success_score,
            character_id=character_id,
            style=style,
            state=state,
            metadata=metadata,
        )
        self.characters[character_id]["memory"] = self.memory_store.character_preferences(character_id)
        return entry

    def get_character(self, character_id):
        character = self.characters.get(character_id)
        return deepcopy(character) if character is not None else None

    def _require_character(self, character_id: str) -> Dict[str, Any]:
        if character_id not in self.characters:
            raise KeyError(f"Unknown character: {character_id}")
        return self.characters[character_id]

    def _make_character_id(self, name: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "character"
        candidate = slug
        index = 2
        while candidate in self.characters:
            candidate = f"{slug}-{index}"
            index += 1
        return candidate

    def _initial_consistency_score(self, identity_profile: Optional[Dict[str, Any]]) -> float:
        if not identity_profile:
            return 0.0
        constraints = identity_profile.get("constraints", {})
        return round(float(constraints.get("reference_stability", 0.0)), 3)

    def _reference_assets_from_faces(self, face_images: list[Any]) -> list[Dict[str, Any]]:
        assets = []
        labels = ["主图", "侧脸", "回眸", "微笑"]
        for index, source in enumerate(face_images[:20]):
            source_text = str(source)
            assets.append({
                "id": f"face-{index + 1}",
                "label": labels[index] if index < len(labels) else f"参考 {index + 1}",
                "image": source_text if source_text.startswith("assets/") else "",
                "source": source_text,
                "prompt": "保持参考人脸五官比例和脸型" if index == 0 else "保持同一角色身份",
                "active": index == 0,
            })
        return assets

    def _version_snapshot(
        self,
        character: Dict[str, Any],
        note: str,
        restored_from: Optional[int] = None,
    ) -> Dict[str, Any]:
        style = character.get("style") or {}
        lora = style.get("lora") or {}
        snapshot = {
            "version": character["version"],
            "note": note,
            "identity_reference_count": (character.get("identity") or {}).get("reference_count", 0),
            "style_preset": style.get("preset"),
            "lora_id": lora.get("id"),
            "consistency_score": character["consistency_score"],
            "can_restore": True,
            "identity_snapshot": deepcopy(character.get("identity")),
            "style_snapshot": deepcopy(character.get("style")),
            "prompt_snapshot": character.get("prompt"),
            "summary": {
                "identity_reference_count": (character.get("identity") or {}).get("reference_count", 0),
                "style_preset": style.get("preset"),
                "lora_id": lora.get("id"),
                "lora_weight": lora.get("weight"),
                "consistency_score": character["consistency_score"],
            },
        }
        if restored_from is not None:
            snapshot["restored_from"] = restored_from
        return snapshot

    def _find_version_snapshot(self, character: Dict[str, Any], version: int) -> Dict[str, Any]:
        for snapshot in character.get("versions", []):
            if int(snapshot.get("version", 0)) == int(version):
                return snapshot
        raise KeyError(f"Unknown version: v{version}")

    def _snapshot_can_restore(self, snapshot: Dict[str, Any]) -> bool:
        return "identity_snapshot" in snapshot and "style_snapshot" in snapshot

    def backfill_current_version_snapshot(self, character_id: str) -> bool:
        character = self._require_character(character_id)
        current_version = int(character.get("version", 1))
        changed = False
        for snapshot in character.get("versions", []):
            if int(snapshot.get("version", 0)) != current_version or self._snapshot_can_restore(snapshot):
                continue
            style = character.get("style") or {}
            lora = style.get("lora") or {}
            snapshot["can_restore"] = True
            snapshot["identity_snapshot"] = deepcopy(character.get("identity"))
            snapshot["style_snapshot"] = deepcopy(character.get("style"))
            snapshot["prompt_snapshot"] = character.get("prompt")
            snapshot["summary"] = {
                "identity_reference_count": (character.get("identity") or {}).get("reference_count", 0),
                "style_preset": style.get("preset"),
                "lora_id": lora.get("id"),
                "lora_weight": lora.get("weight"),
                "consistency_score": character["consistency_score"],
            }
            changed = True
        for snapshot in character.get("versions", []):
            snapshot["can_restore"] = self._snapshot_can_restore(snapshot)
        return changed

    def _style_with_lora(
        self,
        style_profile: Dict[str, Any],
        lora_id: Optional[str],
        lora_weight: Optional[float],
    ) -> Dict[str, Any]:
        if not lora_id and lora_weight is None:
            return style_profile
        lora = style_profile.get("lora") or {}
        style_input = {
            "preset": style_profile.get("preset") or "cinematic",
            "tokens": style_profile.get("tokens", []),
            "photography": style_profile.get("photography"),
            "lighting": style_profile.get("lighting"),
            "color": style_profile.get("color"),
            "camera_language": style_profile.get("camera_language"),
            "lora_id": lora_id or lora.get("id"),
            "lora_weight": lora_weight if lora_weight is not None else lora.get("weight"),
        }
        return StyleModel().encode_style(style_input)

    def _conditioning_style_summary(self, style_profile: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "preset": style_profile.get("preset"),
            "tokens": style_profile.get("tokens", [])[:8],
            "photography": style_profile.get("photography"),
            "lighting": style_profile.get("lighting"),
            "color": style_profile.get("color"),
            "camera_language": style_profile.get("camera_language"),
            "lora": style_profile.get("lora"),
        }
