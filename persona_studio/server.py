import argparse
import base64
import hashlib
import hmac
import json
import mimetypes
import posixpath
import re
import struct
import time
import urllib.error
import urllib.request
import zlib
from datetime import datetime
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import unquote, urlparse

from .asset_store import CharacterAssetStore
from .demo_data import create_demo_manager
from .identity_model import IdentityModel
from .style_model import StyleModel


JsonResponse = Tuple[int, Dict[str, Any]]
ALLOWED_GENERATION_COUNTS = {1, 2, 4, 8}


class PersonaStudioApp:
    def __init__(self, manager=None, static_dir: Optional[Path] = None, data_path: Optional[Path] = None):
        self.asset_store = CharacterAssetStore(data_path) if data_path else None
        self.static_dir = Path(static_dir or Path(__file__).resolve().parent.parent / "prototype").resolve()
        if manager is not None:
            self.manager = manager
            self.generations = []
            self.projects = self._demo_projects()
            self.generation_jobs = []
        elif self.asset_store is not None:
            if self.asset_store.exists():
                self.manager, self.generations, self.projects = self.asset_store.load_workspace_state(create_demo_manager)
                self.generation_jobs = self.asset_store.load_generation_jobs()
                if not self.projects:
                    self.projects = self._demo_projects()
                    self.asset_store.save_state(
                        self.manager, self.generations, self.projects, generation_jobs=self.generation_jobs
                    )
            else:
                self.manager = create_demo_manager()
                self.generations = self._demo_generations()
                self.projects = self._demo_projects()
                self.generation_jobs = []
                self.asset_store.save_state(
                    self.manager, self.generations, self.projects, generation_jobs=self.generation_jobs
                )
        else:
            self.manager = create_demo_manager()
            self.generations = self._demo_generations()
            self.projects = self._demo_projects()
            self.generation_jobs = []
        self.settings = self._normalize_settings(self.asset_store.load_settings() if self.asset_store else {})
        self.account = self._normalize_account(self.asset_store.load_account() if self.asset_store else {})
        changed = self._backfill_generation_quality()
        changed = self._backfill_generation_model_route() or changed
        changed = self._backfill_non_character_generation_metadata() or changed
        changed = self._backfill_generation_conditioning_manifest() or changed
        changed = self._backfill_current_version_snapshots() or changed
        changed = self._backfill_character_reference_assets() or changed
        if changed:
            self._save_assets()

    def api_response(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> JsonResponse:
        try:
            return self._api_response(method.upper(), path, body or {})
        except (KeyError, ValueError, TypeError) as error:
            return 400, {"error": str(error)}

    def _api_response(self, method: str, path: str, body: Dict[str, Any]) -> JsonResponse:
        parts = [unquote(part) for part in path.strip("/").split("/") if part]
        if parts == ["api", "health"] and method == "GET":
            return 200, {
                "ok": True,
                "characters": len(self.manager.characters),
                "generations": len(self.generations),
                "persistent": self.asset_store is not None,
                "data_path": str(self.asset_store.path) if self.asset_store else None,
                "api_configured": self._configured_external_api_auth_is_set(),
                "generation_jobs": len(self.generation_jobs),
                "account_plan": self.account.get("plan_id"),
                "credits_remaining": self.account.get("credits_remaining"),
            }

        if parts == ["api", "system", "readiness"] and method == "GET":
            return 200, self._system_readiness_response()

        if parts == ["api", "providers", "status"] and method == "GET":
            return 200, self._provider_status_response()

        if parts == ["api", "identity-training", "status"] and method == "GET":
            return 200, self._identity_training_status()

        if parts == ["api", "identity-training", "jobs"] and method == "POST":
            response = self._create_identity_training_jobs(body)
            self._save_assets()
            return 201, response

        if len(parts) == 4 and parts[:3] == ["api", "identity-training", "jobs"] and method == "GET":
            return 200, {"job": self._get_identity_training_job(parts[3])}

        if parts == ["api", "deployment", "status"] and method == "GET":
            return 200, self._deployment_status()

        if parts == ["api", "deployment", "initialize"] and method == "POST":
            deployment = self._initialize_deployment(body)
            self._save_assets()
            return 200, deployment

        if parts == ["api", "account"] and method == "GET":
            return 200, self._account_response()

        if parts == ["api", "account"] and method == "POST":
            self.account = self._update_account(body)
            self._save_assets()
            return 200, self._account_response()

        if parts == ["api", "settings"] and method == "GET":
            return 200, {"settings": self._public_settings()}

        if parts == ["api", "settings"] and method == "POST":
            self.settings = self._update_api_settings(body)
            self._save_assets()
            return 200, {"settings": self._public_settings()}

        if parts == ["api", "settings", "test"] and method == "POST":
            result = self._test_api_settings()
            self._set_active_api_last_test(result)
            self._save_assets()
            return 200, {"test": result, "settings": self._public_settings()}

        if parts == ["api", "export"] and method == "GET":
            return 200, {"project": self._export_project()}

        if parts == ["api", "loras"] and method == "GET":
            return 200, {"loras": StyleModel.available_loras()}

        if parts == ["api", "projects"] and method == "GET":
            return 200, {"projects": [self._serialize_project(project) for project in self.projects]}

        if parts == ["api", "projects"] and method == "POST":
            project = self._create_project(body)
            self._save_assets()
            return 201, {"project": self._serialize_project(project, include_package=True)}

        if len(parts) == 3 and parts[:2] == ["api", "projects"] and method == "GET":
            project = self._get_project(parts[2])
            return 200, {"project": self._serialize_project(project, include_package=True)}

        if len(parts) == 3 and parts[:2] == ["api", "projects"] and method == "POST":
            project = self._update_project(parts[2], body)
            self._save_assets()
            return 200, {"project": self._serialize_project(project, include_package=True)}

        if len(parts) == 4 and parts[:2] == ["api", "projects"] and parts[3] == "release" and method == "POST":
            release = self._build_project_release(parts[2], body)
            self._save_assets()
            return 200, release

        if len(parts) == 3 and parts[:2] == ["api", "projects"] and method == "DELETE":
            deleted = self._delete_project(parts[2])
            self._save_assets()
            return 200, {"deleted": deleted, "projects": [self._serialize_project(project) for project in self.projects]}

        if parts == ["api", "assets", "reference"] and method == "POST":
            return 201, {"asset": self._save_reference_asset(body)}

        if parts == ["api", "assets", "library"] and method == "GET":
            return 200, self._asset_library_response()

        if parts == ["api", "styles"] and method == "GET":
            return 200, self._style_library_response()

        if parts == ["api", "styles", "preview"] and method == "POST":
            return 200, {"style": self._style_preview_response(body)}

        if parts == ["api", "generations"] and method == "GET":
            return 200, {"generations": list(reversed(self.generations))}

        if parts == ["api", "generations", "preflight"] and method == "POST":
            return 200, {"preflight": self._generation_preflight_response(body)}

        if parts == ["api", "generations"] and method == "POST":
            records, job = self._create_generations_with_job(body)
            self._save_assets()
            return 201, {"generations": records, "job": job, "account": self._normalize_account(self.account)}

        if len(parts) == 4 and parts[:2] == ["api", "generations"] and parts[3] == "edit" and method == "POST":
            response = self._edit_generation(parts[2], body)
            self._save_assets()
            return 201, response

        if len(parts) == 3 and parts[:2] == ["api", "generations"] and method == "DELETE":
            deleted = self._delete_generation(parts[2])
            self._save_assets()
            return 200, {
                "deleted": deleted,
                "generations": list(reversed(self.generations)),
                "jobs": list(reversed(self.generation_jobs)),
                "characters": [self._serialize_character(character_id) for character_id in self.manager.characters],
            }

        if parts == ["api", "generation-jobs"] and method == "GET":
            return 200, {"jobs": list(reversed(self.generation_jobs))}

        if len(parts) == 3 and parts[:2] == ["api", "generation-jobs"] and method == "GET":
            return 200, {"job": self._get_generation_job(parts[2])}

        if (
            len(parts) == 4
            and parts[:2] == ["api", "generation-jobs"]
            and parts[3] == "retry"
            and method == "POST"
        ):
            original_job = self._get_generation_job(parts[2])
            if not original_job.get("request"):
                raise ValueError(f"Generation job {parts[2]} does not include a retryable request.")
            retry_request = {**original_job["request"], **body}
            records, job = self._create_generations_with_job(retry_request, retry_of=parts[2])
            original_job["retry_job_id"] = job["id"]
            self._save_assets()
            return 201, {
                "generations": records,
                "job": job,
                "retry_of": parts[2],
                "account": self._normalize_account(self.account),
            }

        if len(parts) == 4 and parts[:2] == ["api", "generations"] and parts[3] == "favorite" and method == "POST":
            generation = self._set_generation_favorite(parts[2], body.get("favorite"))
            self._save_assets()
            return 200, {"generation": generation}

        if parts == ["api", "characters"] and method == "GET":
            characters = [self._serialize_character(character_id) for character_id in self.manager.characters]
            return 200, {"characters": characters}

        if parts == ["api", "characters"] and method == "POST":
            name = str(body.get("name") or "").strip()
            face_images = body.get("face_images") or []
            style = body.get("style") or "cinematic portrait"
            if not name:
                raise ValueError("name is required")
            character = self.manager.create_character(
                name,
                {
                    "character_id": body.get("character_id"),
                    "face_images": self._resolve_face_images(face_images) if face_images else self._synthetic_faces(name),
                },
                style,
            )
            now = self._timestamp()
            live_character = self.manager.characters[character["id"]]
            live_character["prompt"] = body.get("prompt") or self._default_prompt(character["id"])
            live_character["tags"] = self._normalize_character_tags(body.get("tags"))
            live_character["created_at"] = now
            live_character["updated_at"] = now
            self._save_assets()
            return 201, {"character": self._serialize_character(character["id"], include_detail=True)}

        if len(parts) == 3 and parts[:2] == ["api", "characters"] and method == "DELETE":
            deleted = self._delete_character(parts[2])
            self._save_assets()
            characters = [self._serialize_character(character_id) for character_id in self.manager.characters]
            return 200, {"deleted": deleted, "characters": characters}

        if len(parts) == 3 and parts[:2] == ["api", "characters"] and method == "POST":
            character = self._update_character(parts[2], body)
            self._save_assets()
            return 200, {"character": character}

        if len(parts) == 3 and parts[:2] == ["api", "characters"] and method == "GET":
            return 200, {"character": self._serialize_character(parts[2], include_detail=True)}

        if len(parts) == 4 and parts[:2] == ["api", "characters"] and parts[3] == "references" and method == "POST":
            response = self._update_character_references(parts[2], body)
            self._save_assets()
            return 200, response

        if (
            len(parts) == 4
            and parts[:2] == ["api", "characters"]
            and parts[3] == "reference-collections"
            and method == "POST"
        ):
            response = self._update_character_reference_collections(parts[2], body)
            self._save_assets()
            return 200, response

        if len(parts) == 4 and parts[:2] == ["api", "characters"] and parts[3] == "versions" and method == "GET":
            character = self.manager.get_character(parts[2])
            if character is None:
                raise KeyError(f"Unknown character: {parts[2]}")
            return 200, {"versions": character.get("versions", [])}

        if len(parts) == 4 and parts[:2] == ["api", "characters"] and parts[3] == "versions" and method == "POST":
            note = str(body.get("note") or "train more")
            style = body.get("style")
            face_images = self._resolve_face_images(body.get("face_images") or []) or self._synthetic_faces(
                parts[2],
                suffix=f"v{self._next_version(parts[2])}",
            )
            version = self.manager.create_version(
                parts[2],
                identity_config={"face_images": face_images},
                style_config=style,
                note=note,
            )
            self._save_assets()
            return 201, {
                "version": version,
                "character": self._serialize_character(parts[2], include_detail=True),
            }

        if (
            len(parts) == 6
            and parts[:2] == ["api", "characters"]
            and parts[3] == "versions"
            and parts[5] == "restore"
            and method == "POST"
        ):
            restored = self.manager.restore_version(
                parts[2],
                int(parts[4]),
                note=str(body.get("note") or f"restore v{parts[4]}"),
            )
            self._save_assets()
            character = self.manager.get_character(parts[2])
            return 200, {
                "restored": restored,
                "versions": character.get("versions", []) if character else [],
                "character": self._serialize_character(parts[2], include_detail=True),
            }

        if len(parts) == 4 and parts[:2] == ["api", "characters"] and parts[3] == "condition" and method == "POST":
            packet = self.manager.build_conditioning(
                parts[2],
                prompt=str(body.get("prompt") or ""),
                state=str(body.get("state") or "calm"),
                identity_weight=float(body.get("identity_weight", 0.7)),
                style_weight=float(body.get("style_weight", 0.6)),
                prompt_weight=float(body.get("prompt_weight", 1.0)),
                state_weight=float(body.get("state_weight", 0.4)),
                lora_id=str(body.get("lora_id") or "").strip() or None,
                lora_weight=float(body.get("lora_weight", 0.0)) if body.get("lora_weight") is not None else None,
            )
            return 200, {"conditioning": self._serialize_conditioning(packet)}

        if len(parts) == 4 and parts[:2] == ["api", "characters"] and parts[3] == "memory" and method == "GET":
            return 200, self._memory_response(parts[2])

        if len(parts) == 5 and parts[:2] == ["api", "characters"] and parts[3] == "memory" and method == "DELETE":
            deleted = self._delete_memory_entry(parts[2], parts[4])
            self._save_assets()
            response = self._memory_response(parts[2])
            response["deleted"] = deleted
            response["character"] = self._serialize_character(parts[2], include_detail=True)
            return 200, response

        if len(parts) == 4 and parts[:2] == ["api", "characters"] and parts[3] == "scene" and method == "POST":
            created_at = self._timestamp()
            entry = self.manager.record_scene(
                parts[2],
                prompt=str(body.get("prompt") or ""),
                image=body.get("image") or "assets/lina-morning.svg",
                pose=str(body.get("pose") or "front"),
                success_score=float(body.get("success_score", 0.8)),
                style=body.get("style"),
                state=body.get("state"),
                metadata={
                    "source": "manual-scene",
                    "created_at": created_at,
                    "memory_id": f"memory-{created_at.replace(':', '').replace('-', '').replace('T', '-').removesuffix('Z')}",
                },
            )
            self._save_assets()
            return 201, {
                "entry": entry,
                **self._memory_response(parts[2]),
                "character": self._serialize_character(parts[2], include_detail=True),
            }

        return 404, {"error": "not found"}

    def static_response(self, request_path: str) -> Tuple[int, bytes, str]:
        parsed = urlparse(request_path)
        safe_path = posixpath.normpath(unquote(parsed.path)).lstrip("/")
        if not safe_path:
            safe_path = "index.html"
        file_path = (self.static_dir / safe_path).resolve()
        if self.static_dir not in file_path.parents and file_path != self.static_dir:
            return 403, b"Forbidden", "text/plain"
        if file_path.is_dir():
            file_path = file_path / "index.html"
        if not file_path.exists() or not file_path.is_file():
            return 404, b"Not found", "text/plain"
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        return 200, file_path.read_bytes(), content_type

    def _serialize_character(self, character_id: str, include_detail: bool = False) -> Dict[str, Any]:
        character = self.manager.get_character(character_id)
        if character is None:
            raise KeyError(f"Unknown character: {character_id}")

        style = character.get("style") or {}
        identity = character.get("identity") or {}
        scene_logs = [
            entry
            for entry in self.manager.memory_store.logs
            if entry.get("character_id") == character_id
        ]
        asset_summary = self._character_asset_summary(character_id, character, scene_logs)
        reference_assets = self._character_reference_assets(character_id, character)
        reference_collections = self._character_reference_collections(character_id, character)
        identity_readiness = self._identity_readiness(reference_assets)
        production_identity = self._production_identity_summary(character)
        summary = {
            "id": character["id"],
            "name": character["name"],
            "version": character["version"],
            "consistency_score": character.get("consistency_score", 0.0),
            "consistency_percent": round(character.get("consistency_score", 0.0) * 100),
            "identity_strength": self._identity_strength(character),
            "identity": {
                "reference_count": identity.get("reference_count", 0),
                "embedding_dim": identity.get("embedding_dim", 0),
                "constraints": identity.get("constraints", {}),
            },
            "style": {
                "preset": style.get("preset"),
                "tokens": style.get("tokens", [])[:6],
                "photography": style.get("photography"),
                "lighting": style.get("lighting"),
                "color": style.get("color"),
                "camera_language": style.get("camera_language"),
                "lora": style.get("lora"),
            },
            "style_labels": self._style_labels(style),
            "tags": asset_summary["tags"],
            "asset_summary": asset_summary,
            "reference_assets": reference_assets,
            "reference_collections": reference_collections,
            "identity_readiness": identity_readiness,
            "production_identity": production_identity,
            "last_used_at": asset_summary["last_used_at"],
            "memory": character.get("memory", {}),
            "memory_insights": self._memory_insights(character_id, style),
            "memory_entries": self._character_memory_entries(character_id, limit=4),
            "memory_labels": [entry["prompt"] for entry in scene_logs[-3:]],
            "image": "assets/lina-morning.svg",
            "prompt": character.get("prompt") or self._default_prompt(character_id),
        }
        if include_detail:
            summary["versions"] = self._public_character_versions(character.get("versions", []))
            summary["scene_logs"] = scene_logs
            summary["identity_training_jobs"] = character.get("identity_training_jobs", [])
        return summary

    def _public_character_versions(self, versions: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        public_versions = []
        for version in versions or []:
            identity_snapshot = version.get("identity_snapshot") if isinstance(version.get("identity_snapshot"), dict) else {}
            style_snapshot = version.get("style_snapshot") if isinstance(version.get("style_snapshot"), dict) else {}
            public_version = {
                key: value
                for key, value in version.items()
                if key not in {"identity_snapshot", "style_snapshot"}
            }
            public_version["identity_snapshot"] = {
                "reference_count": identity_snapshot.get("reference_count", 0),
                "embedding_dim": identity_snapshot.get("embedding_dim", 0),
                "constraints": identity_snapshot.get("constraints") or {},
                "encoder": identity_snapshot.get("encoder") or "",
                "provider": identity_snapshot.get("provider") or "",
                "vector_hash": identity_snapshot.get("vector_hash") or "",
                "production_artifact": identity_snapshot.get("production_artifact") or "",
            }
            public_version["style_snapshot"] = {
                "preset": style_snapshot.get("preset"),
                "tokens": (style_snapshot.get("tokens") or [])[:8],
                "lora": style_snapshot.get("lora"),
                "photography": style_snapshot.get("photography"),
                "lighting": style_snapshot.get("lighting"),
                "color": style_snapshot.get("color"),
                "camera_language": style_snapshot.get("camera_language"),
            }
            public_versions.append(public_version)
        return public_versions

    def _serialize_conditioning(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        vector = packet.get("conditioning_vector", [])
        weights = packet.get("weights") or {}
        return {
            "character_id": packet.get("character_id"),
            "character_version": packet.get("character_version"),
            "weights": weights,
            "identity_priority": packet.get("identity_priority"),
            "drift_risk": packet.get("drift_risk"),
            "controlnet": packet.get("controlnet"),
            "style": packet.get("style"),
            "lora": packet.get("lora"),
            "prompt": packet.get("prompt"),
            "state": packet.get("state"),
            "diagnostics": self._conditioning_diagnostics(packet, weights),
            "vector_dim": len(vector),
            "vector_preview": [round(value, 6) for value in vector[:8]],
        }

    def _style_library_response(self) -> Dict[str, Any]:
        preset_inputs = [
            {"id": "cinematic", "label": "电影人像", "prompt": "cinematic portrait soft daylight 50mm"},
            {"id": "anime", "label": "动漫线稿", "prompt": "anime clean line soft glow"},
            {"id": "commercial", "label": "商业广告", "prompt": "commercial brand campaign studio key light"},
        ]
        return {
            "presets": [
                {
                    **self._serialize_style_profile(
                        StyleModel().encode_style({"preset": item["id"], "prompt": item["prompt"]})
                    ),
                    "id": item["id"],
                    "label": item["label"],
                }
                for item in preset_inputs
            ],
            "loras": StyleModel.available_loras(),
        }

    def _style_preview_response(self, body: Dict[str, Any]) -> Dict[str, Any]:
        style_input: Any
        if "style" in body:
            style_input = body.get("style")
        else:
            style_input = {
                "preset": body.get("preset") or "cinematic",
                "prompt": body.get("prompt") or body.get("preset") or "cinematic portrait",
                "lora_id": body.get("lora_id"),
                "lora_weight": body.get("lora_weight"),
            }
        return self._serialize_style_profile(StyleModel().encode_style(style_input))

    def _serialize_style_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        vector = profile.get("vector") or []
        controls = {
            "photography": profile.get("photography"),
            "lighting": profile.get("lighting"),
            "color": profile.get("color"),
            "camera_language": profile.get("camera_language"),
        }
        return {
            "preset": profile.get("preset"),
            "tokens": profile.get("tokens", [])[:12],
            "token_count": len(profile.get("tokens", [])),
            "controls": controls,
            "control_rows": [
                {"id": "photography", "label": "摄影", "value": controls["photography"]},
                {"id": "lighting", "label": "光影", "value": controls["lighting"]},
                {"id": "color", "label": "色彩", "value": controls["color"]},
                {"id": "camera_language", "label": "镜头语言", "value": controls["camera_language"]},
            ],
            "lora": profile.get("lora"),
            "vector_dim": len(vector),
            "vector_preview": [round(value, 6) for value in vector[:8]],
        }

    def _conditioning_diagnostics(self, packet: Dict[str, Any], weights: Dict[str, Any]) -> Dict[str, Any]:
        identity_weight = float(weights.get("identity") or 0.0)
        style_weight = float(weights.get("style") or 0.0)
        prompt_weight = float(weights.get("prompt") or 0.0)
        state_weight = float(weights.get("state") or 0.0)
        margin = round(identity_weight - style_weight, 3)
        drift_risk = str(packet.get("drift_risk") or "unknown")
        lora = packet.get("lora") or {}
        controlnet = packet.get("controlnet") or {}
        checks = [
            {
                "id": "identity_priority",
                "label": "身份权重高于风格",
                "status": "pass" if margin > 0 else "fail",
                "value": margin,
            },
            {
                "id": "identity_margin",
                "label": "身份安全边距",
                "status": "pass" if margin >= 0.2 else "review" if margin >= 0.08 else "fail",
                "value": margin,
            },
            {
                "id": "style_pressure",
                "label": "风格压力",
                "status": "pass" if style_weight <= 0.7 else "review",
                "value": round(style_weight, 3),
            },
            {
                "id": "prompt_weight",
                "label": "提示词主导",
                "status": "pass" if prompt_weight >= 0.8 else "review",
                "value": round(prompt_weight, 3),
            },
        ]
        return {
            "identity_margin": margin,
            "drift_risk": drift_risk,
            "summary": self._conditioning_diagnostic_summary(drift_risk, margin),
            "checks": checks,
            "weight_total": round(identity_weight + style_weight + prompt_weight + state_weight, 3),
            "controlnet_summary": {
                "face_lock": round(float(controlnet.get("face_lock") or 0.0), 3),
                "pose_lock": round(float(controlnet.get("pose_lock") or 0.0), 3),
                "style_guidance": round(float(controlnet.get("style_guidance") or 0.0), 3),
            },
            "lora_summary": {
                "id": lora.get("id"),
                "label": lora.get("label") or lora.get("name"),
                "weight": round(float(lora.get("weight") or 0.0), 3),
            } if lora else None,
        }

    def _conditioning_diagnostic_summary(self, drift_risk: str, margin: float) -> str:
        if drift_risk == "low":
            return f"身份优先稳定，身份/风格边距 {margin:.2f}。"
        if drift_risk == "medium":
            return f"身份边距 {margin:.2f} 偏紧，建议适当提高身份或降低风格。"
        return f"身份边距 {margin:.2f} 过低，存在漂脸风险。"

    def _create_generations_with_job(self, body: Dict[str, Any], retry_of: Optional[str] = None):
        character_id = str(body.get("character_id") or "").strip()
        if not character_id:
            raise ValueError("character_id is required")
        count = int(body.get("count") or 4)
        request = self._generation_request_snapshot(body)
        job = self._begin_generation_job(request, retry_of=retry_of)
        try:
            charge = self._reserve_generation_credits(count)
            job["billing"] = charge
            records = self._create_generation_records(
                character_id=character_id,
                mode=str(body.get("mode") or "文生图"),
                prompt=str(body.get("prompt") or ""),
                negative_prompt=str(body.get("negative_prompt") or ""),
                state=str(body.get("state") or "calm"),
                identity_weight=float(body.get("identity_weight", 0.7)),
                style_weight=float(body.get("style_weight", 0.6)),
                lora_id=str(body.get("lora_id") or "").strip() or None,
                lora_weight=float(body.get("lora_weight", 0.0)) if body.get("lora_weight") is not None else None,
                size=str(body.get("size") or "3:4"),
                image_model=str(body.get("image_model") or "").strip(),
                image_model_label=str(body.get("image_model_label") or "").strip(),
                reference_guidance=body.get("reference_guidance"),
                pose_control=body.get("pose_control"),
                count=count,
            )
        except Exception as error:
            self._fail_generation_job(job, error)
            self._save_assets()
            raise
        self._complete_generation_job(job, records)
        self._commit_generation_charge(charge, job, records)
        return records, job

    def _generation_request_snapshot(self, body: Dict[str, Any]) -> Dict[str, Any]:
        allowed_fields = [
            "character_id",
            "mode",
            "prompt",
            "negative_prompt",
            "state",
            "identity_weight",
            "style_weight",
            "lora_id",
            "lora_weight",
            "size",
            "image_model",
            "image_model_label",
            "reference_guidance",
            "pose_control",
            "parent_generation_id",
            "edit_request",
            "count",
        ]
        return {field: body.get(field) for field in allowed_fields if field in body}

    def _begin_generation_job(self, request: Dict[str, Any], retry_of: Optional[str] = None) -> Dict[str, Any]:
        now = self._timestamp()
        job = {
            "id": self._next_generation_job_id(),
            "status": "running",
            "character_id": str(request.get("character_id") or ""),
            "mode": str(request.get("mode") or "文生图"),
            "prompt": str(request.get("prompt") or ""),
            "count": int(request.get("count") or 4),
            "size": str(request.get("size") or "3:4"),
            "image_model": str(request.get("image_model") or ""),
            "image_model_label": str(request.get("image_model_label") or ""),
            "request": request,
            "retry_of": retry_of,
            "requested_at": now,
            "started_at": now,
            "completed_at": None,
            "duration_ms": None,
            "generation_ids": [],
            "error": None,
        }
        self.generation_jobs.append(job)
        return job

    def _complete_generation_job(self, job: Dict[str, Any], records: list[Dict[str, Any]]) -> None:
        completed_at = self._timestamp()
        for record in records:
            record["job_id"] = job["id"]
        job.update(
            {
                "status": "completed",
                "completed_at": completed_at,
                "duration_ms": self._duration_ms(job.get("started_at"), completed_at),
                "generation_ids": [record.get("id") for record in records if record.get("id")],
                "model_route": records[0].get("model_route") if records else None,
                "quality_summary": self._job_quality_summary(records),
                "result_count": len(records),
            }
        )

    def _fail_generation_job(self, job: Dict[str, Any], error: Exception) -> None:
        completed_at = self._timestamp()
        job.update(
            {
                "status": "failed",
                "completed_at": completed_at,
                "duration_ms": self._duration_ms(job.get("started_at"), completed_at),
                "error": self._compact_error(str(error)),
                "result_count": 0,
            }
        )
        # Credits are only committed on success (_commit_generation_charge runs
        # after _create_generation_records). A failed job must not keep its
        # reserved billing record advertising a deduction that never hit the
        # account balance, otherwise audit/UI shows phantom spend.
        billing = job.get("billing")
        if isinstance(billing, dict) and billing.get("status") == "reserved":
            billing["status"] = "not_charged"
            billing["credits_after"] = billing.get("credits_before")

    def _job_quality_summary(self, records: list[Dict[str, Any]]) -> Dict[str, Any]:
        if not records:
            return {"passed": 0, "total": 0, "lowest_score": 0.0}
        scores = [float((record.get("quality") or {}).get("face_match_score") or 0.0) for record in records]
        passed = sum(1 for record in records if (record.get("quality") or {}).get("status") == "pass")
        return {
            "passed": passed,
            "total": len(records),
            "lowest_score": round(min(scores), 3),
        }

    def _duration_ms(self, started_at: Optional[str], completed_at: Optional[str]) -> int:
        try:
            started = datetime.fromisoformat(str(started_at).removesuffix("Z"))
            completed = datetime.fromisoformat(str(completed_at).removesuffix("Z"))
        except ValueError:
            return 0
        return max(0, int((completed - started).total_seconds() * 1000))

    def _get_generation_job(self, job_id: str) -> Dict[str, Any]:
        for job in self.generation_jobs:
            if job.get("id") == job_id:
                return job
        raise KeyError(f"Unknown generation job: {job_id}")

    def _max_generation_job_index(self) -> int:
        max_index = 0
        for job in self.generation_jobs:
            job_id = str(job.get("id") or "")
            if not job_id.startswith("job-"):
                continue
            try:
                max_index = max(max_index, int(job_id[4:]))
            except ValueError:
                continue
        return max_index

    def _next_generation_job_id(self) -> str:
        return f"job-{self._max_generation_job_index() + 1:06d}"

    def _account_plans(self) -> list[Dict[str, Any]]:
        return [
            {
                "id": "free",
                "label": "免费版",
                "badge": "Free",
                "user_segment": "普通用户",
                "monthly_credits": 1200,
                "cost_per_image": 2,
                "features": ["轻量写真", "基础角色资产", "本地项目导出"],
            },
            {
                "id": "upgrade-creator",
                "label": "创作者 Pro",
                "badge": "Pro",
                "user_segment": "创作者",
                "monthly_credits": 2000,
                "cost_per_image": 2,
                "features": ["角色版本历史", "批量生成", "记忆资产管理"],
            },
            {
                "id": "upgrade-business",
                "label": "商业团队",
                "badge": "Team",
                "user_segment": "商业用户",
                "monthly_credits": 8000,
                "cost_per_image": 2,
                "features": ["共享角色资产", "品牌 LoRA", "IP 资产包导出"],
            },
        ]

    def _account_plan(self, plan_id: str) -> Dict[str, Any]:
        for plan in self._account_plans():
            if plan["id"] == plan_id:
                return plan
        return self._account_plans()[0]

    def _normalize_account(self, account: Dict[str, Any]) -> Dict[str, Any]:
        plan = self._account_plan(str((account or {}).get("plan_id") or "free"))
        monthly_credits = int(plan["monthly_credits"])
        raw_remaining = (account or {}).get("credits_remaining")
        raw_used = (account or {}).get("credits_used")
        credits_remaining = monthly_credits if raw_remaining is None else int(raw_remaining)
        credits_used = 0 if raw_used is None else int(raw_used)
        credits_remaining = max(0, min(monthly_credits, credits_remaining))
        credits_used = max(0, credits_used)
        return {
            "plan_id": plan["id"],
            "label": plan["label"],
            "badge": plan["badge"],
            "user_segment": plan["user_segment"],
            "monthly_credits": monthly_credits,
            "credits_remaining": credits_remaining,
            "credits_used": credits_used,
            "cost_per_image": int(plan["cost_per_image"]),
            "features": list(plan["features"]),
            "billing_cycle": str((account or {}).get("billing_cycle") or "monthly"),
            "updated_at": str((account or {}).get("updated_at") or self._timestamp()),
        }

    def _account_response(self) -> Dict[str, Any]:
        return {
            "account": self._normalize_account(self.account),
            "plans": self._account_plans(),
        }

    def _update_account(self, body: Dict[str, Any]) -> Dict[str, Any]:
        plan_id = str(body.get("plan_id") or "").strip()
        if not plan_id:
            raise ValueError("plan_id is required")
        plan = self._account_plan(plan_id)
        if plan["id"] != plan_id:
            raise ValueError(f"Unknown account plan: {plan_id}")
        current = self._normalize_account(self.account)
        if current.get("plan_id") != plan["id"]:
            # Switching to a different plan starts a fresh monthly quota.
            credits_remaining = int(plan["monthly_credits"])
            credits_used = 0
        else:
            # Re-selecting the current plan must NOT refill credits — otherwise
            # a user can reset their balance to full by re-posting their own
            # plan, defeating the generation credit accounting.
            credits_remaining = current.get("credits_remaining")
            credits_used = current.get("credits_used")
        return self._normalize_account(
            {
                "plan_id": plan["id"],
                "credits_remaining": credits_remaining,
                "credits_used": credits_used,
                "billing_cycle": "monthly",
                "updated_at": self._timestamp(),
            }
        )

    def _generation_credit_cost(self, count: int) -> int:
        cost_per_image = int((self.account or {}).get("cost_per_image") or self._account_plan("free")["cost_per_image"])
        return max(1, int(count)) * cost_per_image

    def _reserve_generation_credits(self, count: int) -> Dict[str, Any]:
        self.account = self._normalize_account(self.account)
        cost = self._generation_credit_cost(count)
        remaining = int(self.account.get("credits_remaining") or 0)
        if remaining < cost:
            raise ValueError(f"Insufficient credits: need {cost}, remaining {remaining}.")
        return {
            "plan_id": self.account.get("plan_id"),
            "plan_label": self.account.get("label"),
            "user_segment": self.account.get("user_segment"),
            "cost": cost,
            "count": max(1, int(count)),
            "cost_per_image": int(self.account.get("cost_per_image") or 2),
            "credits_before": remaining,
            "credits_after": remaining - cost,
            "status": "reserved",
        }

    def _commit_generation_charge(
        self,
        charge: Dict[str, Any],
        job: Dict[str, Any],
        records: list[Dict[str, Any]],
    ) -> None:
        self.account = self._normalize_account(self.account)
        cost = int(charge.get("cost") or 0)
        before = int(charge.get("credits_before") or self.account.get("credits_remaining") or 0)
        after = max(0, before - cost)
        self.account["credits_remaining"] = after
        self.account["credits_used"] = int(self.account.get("credits_used") or 0) + cost
        self.account["updated_at"] = self._timestamp()
        charge.update(
            {
                "credits_after": after,
                "status": "charged",
                "charged_at": self.account["updated_at"],
            }
        )
        job["billing"] = dict(charge)
        for record in records:
            record["billing"] = {
                "job_id": job.get("id"),
                "plan_id": self.account.get("plan_id"),
                "cost": int(self.account.get("cost_per_image") or 2),
            }

    def _generation_preflight_response(self, body: Dict[str, Any]) -> Dict[str, Any]:
        character_id = str(body.get("character_id") or "").strip()
        if not character_id:
            raise ValueError("character_id is required")
        character = self.manager.get_character(character_id)
        if character is None:
            raise KeyError(f"Unknown character: {character_id}")

        prompt = str(body.get("prompt") or "")
        size = str(body.get("size") or "3:4")
        mode = str(body.get("mode") or "文生图")
        count = int(body.get("count") or 4)
        count_valid = count in ALLOWED_GENERATION_COUNTS
        identity_weight = float(body.get("identity_weight", 0.7))
        style_weight = float(body.get("style_weight", 0.6))
        pose_control = self._normalize_pose_control(body.get("pose_control"), mode=mode)
        normalized_reference_guidance = self._normalize_reference_guidance(body.get("reference_guidance"))
        subject_hint = self._prompt_subject(prompt)
        effective_reference_guidance = self._effective_reference_guidance(
            normalized_reference_guidance,
            subject_hint=subject_hint,
            mode=mode,
        )
        reference_count_before = self._reference_item_count(normalized_reference_guidance)
        reference_count_after = self._reference_item_count(effective_reference_guidance)
        filtered_references = max(0, reference_count_before - reference_count_after)
        uses_character_identity = self._subject_uses_character_identity(subject_hint)
        identity_margin = round(identity_weight - style_weight, 3)
        blocked = uses_character_identity and identity_margin <= 0
        style = character.get("style") or {}
        failure_advice = self.manager.memory_store.avoid_failure_styles(
            style.get("preset"), character_id=character_id
        )
        blocked_styles = failure_advice.get("blocked_styles") or []
        memory_warning = bool(blocked_styles)
        self.account = self._normalize_account(self.account)
        credit_cost = self._generation_credit_cost(count)
        credits_remaining = int(self.account.get("credits_remaining") or 0)
        credits_after = credits_remaining - credit_cost
        credits_ok = credits_remaining >= credit_cost
        canvas_width, canvas_height = self._preview_canvas(size)
        checks = [
            {
                "id": "subject",
                "label": "主体",
                "status": "pass",
                "value": self._subject_label(subject_hint),
            },
            {
                "id": "size",
                "label": "尺寸",
                "status": "pass",
                "value": f"{size} · {self._dashscope_size(size)} · 预览 {canvas_width}x{canvas_height}",
            },
            {
                "id": "identity_lock",
                "label": "身份锁",
                "status": "pass" if uses_character_identity and not blocked else "skip" if not uses_character_identity else "fail",
                "value": "启用" if uses_character_identity and not blocked else "非人像主体不启用" if not uses_character_identity else "身份权重必须高于风格",
            },
            {
                "id": "references",
                "label": "参考图",
                "status": "review" if filtered_references else "pass",
                "value": f"{reference_count_after}/{reference_count_before} 生效" if reference_count_before else "未使用额外参考",
            },
            {
                "id": "count",
                "label": "数量",
                "status": "pass" if count_valid else "fail",
                "value": f"{count} 张" if count_valid else "数量必须是 1、2、4、8",
            },
            {
                "id": "pose_control",
                "label": "姿态锁",
                "status": "pass" if pose_control["enabled"] else "skip",
                "value": pose_control["label"] if pose_control["enabled"] else "自动",
            },
            {
                "id": "memory",
                "label": "记忆避坑",
                "status": "review" if memory_warning else "pass",
                "value": "避开：" + "、".join(blocked_styles[:4]) if memory_warning else "暂无失败风格",
            },
            {
                "id": "credits",
                "label": "额度",
                "status": "pass" if credits_ok else "fail",
                "value": f"{credit_cost} 点 · {credits_remaining} → {max(credits_after, 0)}" if credits_ok else f"余额不足：需要 {credit_cost} 点，剩余 {credits_remaining} 点",
            },
        ]
        status = "blocked" if blocked or not count_valid or not credits_ok else "review" if filtered_references or memory_warning else "ready"
        return {
            "status": status,
            "summary": self._generation_preflight_summary(
                status,
                subject_hint,
                filtered_references,
                blocked_styles,
                credits_ok=credits_ok,
                credit_cost=credit_cost,
                credits_remaining=credits_remaining,
                count_valid=count_valid,
                count=count,
            ),
            "character_id": character_id,
            "character_name": character.get("name"),
            "subject_hint": subject_hint,
            "subject_label": self._subject_label(subject_hint),
            "uses_identity_lock": uses_character_identity and not blocked,
            "identity_margin": identity_margin if uses_character_identity else None,
            "size": {
                "label": size,
                "provider_size": self._dashscope_size(size),
                "preview_canvas": {"width": canvas_width, "height": canvas_height},
                "aspect_ratio": f"{canvas_width}:{canvas_height}",
            },
            "reference_counts": {
                "requested": reference_count_before,
                "effective": reference_count_after,
                "filtered": filtered_references,
            },
            "pose_control": pose_control,
            "memory": {
                "blocked_styles": blocked_styles,
                "reason": failure_advice.get("reason"),
            },
            "billing": {
                "plan_id": self.account.get("plan_id"),
                "cost": credit_cost,
                "cost_per_image": int(self.account.get("cost_per_image") or 2),
                "count": count,
                "count_valid": count_valid,
                "credits_remaining": credits_remaining,
                "credits_after": credits_after if credits_ok else credits_remaining,
                "enough": credits_ok,
            },
            "checks": checks,
        }

    def _generation_preflight_summary(
        self,
        status: str,
        subject_hint: str,
        filtered_references: int,
        blocked_styles: Optional[list[str]] = None,
        credits_ok: bool = True,
        credit_cost: int = 0,
        credits_remaining: int = 0,
        count_valid: bool = True,
        count: int = 4,
    ) -> str:
        if status == "blocked":
            if not credits_ok:
                return f"余额不足，本次需要 {credit_cost} 点，当前剩余 {credits_remaining} 点。"
            if not count_valid:
                return f"数量不合法：{count}，只能选择 1、2、4、8。"
            return "身份权重低于风格权重，生成会被阻断以避免漂脸。"
        if blocked_styles:
            return f"{self._subject_label(subject_hint)}预检需复核，记忆建议避开失败风格：" + "、".join(blocked_styles[:4]) + "。"
        if filtered_references:
            return f"{self._subject_label(subject_hint)}预检可继续，已自动过滤 {filtered_references} 个不适用参考。"
        return f"{self._subject_label(subject_hint)}预检通过，可以生成。"

    def _reference_item_count(self, guidance: list[Dict[str, Any]]) -> int:
        return sum(len(group.get("items") or []) for group in guidance)

    def _create_generation_records(
        self,
        character_id: str,
        mode: str,
        prompt: str,
        negative_prompt: str,
        state: str,
        identity_weight: float,
        style_weight: float,
        lora_id: Optional[str],
        lora_weight: Optional[float],
        size: str,
        image_model: str,
        image_model_label: str,
        reference_guidance: Any,
        pose_control: Any,
        count: int,
    ):
        if count not in ALLOWED_GENERATION_COUNTS:
            raise ValueError("count must be one of 1, 2, 4, 8")
        character = self.manager.get_character(character_id)
        if character is None:
            raise KeyError(f"Unknown character: {character_id}")
        model_route = self._generation_model_route(image_model=image_model, image_model_label=image_model_label)
        normalized_reference_guidance = self._normalize_reference_guidance(reference_guidance)
        subject_hint = self._prompt_subject(prompt)
        uses_character_identity = self._subject_uses_character_identity(subject_hint)
        packet = self.manager.build_conditioning(
            character_id,
            prompt=prompt,
            state=state,
            identity_weight=identity_weight,
            style_weight=style_weight,
            lora_id=lora_id,
            lora_weight=lora_weight,
            enforce_identity_priority=uses_character_identity,
        )
        lora = packet.get("lora") or {}
        effective_reference_guidance = self._effective_reference_guidance(
            normalized_reference_guidance,
            subject_hint=subject_hint,
            mode=mode,
        )
        normalized_pose_control = self._normalize_pose_control(pose_control, mode=mode)
        conditioning_manifest = self._conditioning_manifest(
            character=character,
            packet=packet,
            prompt=prompt,
            negative_prompt=negative_prompt,
            state=state,
            mode=mode,
            reference_guidance=effective_reference_guidance,
            subject_hint=subject_hint,
            pose_control=normalized_pose_control,
        )
        model_route = self._maybe_upgrade_identity_edit_route(model_route, conditioning_manifest)
        model_route = self._maybe_route_to_character_lora(
            model_route, character, conditioning_manifest, uses_character_identity
        )

        records = []
        generation_ids = [self._next_generation_id(offset=index) for index in range(count)]
        external_image_paths = []
        if self._should_call_external_generation(
            model_route,
            mode=mode,
            reference_guidance=effective_reference_guidance,
        ):
            external_image_paths = self._create_external_generation_previews(
                generation_ids=generation_ids,
                prompt=conditioning_manifest["provider_prompt"],
                negative_prompt=conditioning_manifest["provider_negative_prompt"],
                count=count,
                size=size,
                mode=mode,
                model_route=model_route,
                reference_guidance=effective_reference_guidance,
            )
            generation_kind = (
                "t2i"
                if model_route.get("character_lora")
                else self._external_generation_kind(
                    str(model_route.get("provider") or "").strip(),
                    mode,
                    effective_reference_guidance,
                )
            )
            model_route = {
                **model_route,
                "status": "completed",
                "real_generation": True,
                "generation_kind": generation_kind,
            }
        else:
            model_route = {**model_route, "real_generation": False}

        for index in range(count):
            generation_id = generation_ids[index]
            image_path = (
                external_image_paths[index]
                if index < len(external_image_paths)
                else self._create_local_generation_preview(
                    generation_id=generation_id,
                    source_index=index,
                    prompt=prompt,
                    mode=mode,
                    state=state,
                    size=size,
                    reference_guidance=effective_reference_guidance,
                )
            )
            effective_lora = lora if uses_character_identity else {}
            quality = self._quality_report(
                packet=packet,
                character=character,
                prompt=prompt,
                negative_prompt=negative_prompt,
                mode=mode,
                image=image_path,
                index=index,
                subject_hint=subject_hint,
            )
            generation_pose = self._pose_for_generation(mode, index, normalized_pose_control)
            generation = {
                "id": generation_id,
                "character_id": character_id,
                "character_name": character["name"],
                "character_version": character["version"],
                "subject_hint": subject_hint,
                "mode": mode,
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "state": state,
                "size": size,
                "pose": generation_pose,
                "pose_label": self._pose_label(generation_pose),
                "image": image_path,
                "favorite": False,
                "variant": index + 1,
                "drift_risk": packet["drift_risk"] if uses_character_identity else "not_applicable",
                "identity_weight": identity_weight,
                "style_weight": style_weight,
                "lora_id": effective_lora.get("id"),
                "lora_name": effective_lora.get("label") or effective_lora.get("name"),
                "lora_weight": effective_lora.get("weight"),
                "model_route": dict(model_route),
                "reference_guidance": effective_reference_guidance,
                "pose_control": normalized_pose_control,
                "conditioning_manifest": conditioning_manifest,
                "conditioning_preview": [round(value, 6) for value in packet["conditioning_vector"][:8]],
                "quality": quality,
                "created_at": self._timestamp(),
            }
            self.generations.append(generation)
            records.append(generation)

            self.manager.record_scene(
                character_id,
                prompt=prompt,
                image=image_path,
                pose=generation_pose,
                success_score=self._quality_memory_score(quality),
                style=(character.get("style") or {}).get("preset"),
                state=state,
                metadata={
                    "memory_id": f"memory-{generation['id']}",
                    "created_at": generation["created_at"],
                    "source": "generation",
                    "generation_id": generation["id"],
                    "quality": quality,
                    "reference_guidance": effective_reference_guidance,
                },
            )
        return records

    def _maybe_upgrade_identity_edit_route(
        self,
        model_route: Dict[str, Any],
        conditioning_manifest: Dict[str, Any],
    ) -> Dict[str, Any]:
        if str(model_route.get("provider") or "").strip() != "fal":
            return model_route
        model = str(model_route.get("model") or "").strip()
        prompt = str(conditioning_manifest.get("source_prompt") or conditioning_manifest.get("provider_prompt") or "")
        localized_edit = self._is_localized_inpaint_edit(conditioning_manifest)
        remove_eyewear = self._prompt_requests_remove_eyewear(prompt)
        if localized_edit and (self._prompt_requests_object_removal(prompt) or remove_eyewear):
            # User drew an explicit removal mask on the canvas: clean object erase.
            upgraded_model = "fal-ai/flux-pro/v1/erase"
            label = "fal.ai · FLUX.1 Pro Erase"
        elif localized_edit:
            upgraded_model = "fal-ai/flux-pro/v1/fill"
            label = "fal.ai · FLUX.1 Pro Fill"
        elif remove_eyewear:
            # Auto eyewear removal (no user-drawn mask): use Kontext, the
            # instruction-based editor. Mask-based models failed here — `erase`
            # regenerated the whole face (lost identity) and `fill` either kept
            # the glasses or painted cartoon-eye artifacts into the masked band.
            # Kontext does the semantic "remove the glasses, keep the same person"
            # edit with no mask, so it can't produce mask-shaped artifacts.
            upgraded_model = "fal-ai/flux-pro/kontext/max"
            label = "fal.ai · FLUX.1 Kontext Max"
        elif not conditioning_manifest.get("identity_edit_mode"):
            return model_route
        elif self._is_fal_kontext_model(model) or self._is_fal_fill_model(model) or self._is_fal_erase_model(model):
            return model_route
        else:
            upgraded_model = "fal-ai/flux-pro/kontext/max"
            label = "fal.ai · FLUX.1 Kontext Max"
        routed_from = self._fal_model_name(model) if model else model_route.get("request_model")
        return {
            **model_route,
            "model": upgraded_model,
            "label": label,
            "identity_edit_route": True,
            "identity_edit_routed_from": routed_from,
        }

    def _is_localized_inpaint_edit(self, conditioning_manifest: Dict[str, Any]) -> bool:
        return (
            str(conditioning_manifest.get("mode") or "") == "局部重绘"
            and self._reference_guidance_has_kind(conditioning_manifest.get("references"), "edit_source")
        )

    def _conditioning_manifest(
        self,
        character: Dict[str, Any],
        packet: Dict[str, Any],
        prompt: str,
        negative_prompt: str,
        state: str,
        mode: str,
        reference_guidance: list[Dict[str, Any]],
        subject_hint: str,
        pose_control: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        weights = packet.get("weights") or {}
        style = character.get("style") or {}
        identity = character.get("identity") or {}
        constraints = identity.get("constraints") or {}
        lora = packet.get("lora") or style.get("lora") or {}
        uses_character_identity = self._subject_uses_character_identity(subject_hint)
        uses_identity_lock = uses_character_identity and packet.get("identity_priority") is True
        has_face_reference = self._reference_guidance_has_kind(reference_guidance, "face")
        identity_edit_mode = uses_identity_lock and has_face_reference and self._is_identity_preserving_edit(prompt)
        removes_eyewear = self._prompt_requests_remove_eyewear(prompt)

        prompt_clauses = [str(prompt or "").strip() or "写实摄影主体"]
        negative_clauses = [str(negative_prompt or "").strip(), self._visual_artifact_negative_clause()]
        if uses_identity_lock:
            prompt_clauses.append(self._identity_prompt_clause(character, constraints, weights))
            negative_clauses.append("different person, face drift, changed facial structure, inconsistent identity")
        elif not uses_character_identity:
            subject_clause = self._non_character_subject_clause(subject_hint)
            if subject_clause:
                prompt_clauses.append(subject_clause)
            negative_clause = self._non_character_negative_clause(subject_hint)
            if negative_clause:
                negative_clauses.append(negative_clause)

        if identity_edit_mode:
            prompt_clauses.append(self._identity_edit_prompt_clause())
            negative_clauses.append(self._identity_edit_negative_clause())
        else:
            style_clause = self._style_prompt_clause(style, lora if uses_character_identity else {}, subject_hint)
            if style_clause:
                prompt_clauses.append(style_clause)

        if removes_eyewear:
            prompt_clauses.append(self._eyewear_edit_prompt_clause(prompt))
            negative_clauses.append(
                "eyeglasses, sunglasses, glasses frame, eyewear, reflective lenses, "
                "missing eyes, removed eyes, empty eye sockets, deformed eyes, changed eye shape"
            )
        elif identity_edit_mode:
            # In identity edit mode, keep the original photographic look unless
            # the requested edit explicitly needs stronger styling.
            prompt_clauses.append("保持原始照片的自然光线、皮肤质感、发型、脸部角度和服装关系。")

        memory_clause = self._memory_prompt_clause(character["id"], style) if uses_character_identity else ""
        if memory_clause:
            prompt_clauses.append(memory_clause)

        reference_clauses = [
            self._reference_prompt_clause(group, item)
            for group in reference_guidance
            for item in group.get("items", [])
            if item.get("prompt") or item.get("label")
        ]
        if reference_clauses:
            prompt_clauses.append("参考图约束：" + "；".join(reference_clauses[:8]))
        if uses_identity_lock and has_face_reference:
            prompt_clauses.append(self._face_reference_lock_clause())
            negative_clauses.append(
                "different face shape, different jawline, different cheekbones, different eye spacing, "
                "changed nose bridge, older face, changed age impression, new identity"
            )

        pose_control = pose_control or self._normalize_pose_control(None, mode=mode)
        if pose_control.get("enabled"):
            prompt_clauses.append(f"ControlNet 姿态约束：{pose_control['label']}，姿态锁权重 {float(pose_control.get('weight') or 0.4):.2f}。")

        reference_conditioning_mode = self._reference_conditioning_mode(mode, reference_guidance)
        if mode == "图生图":
            prompt_clauses.append("图生图约束：保持参考图构图、姿态和主体关系。")
        elif reference_conditioning_mode == "图生图":
            prompt_clauses.append("参考图输入约束：使用参考图锁定人脸结构、主体比例和关键视觉关系。")
        elif mode == "局部重绘":
            prompt_clauses.append("局部重绘约束：只修复目标区域，保留背景和主体身份。")

        failure_advice = (
            self.manager.memory_store.avoid_failure_styles(style.get("preset"), character_id=character.get("id"))
            if uses_character_identity
            else {"blocked_styles": []}
        )
        blocked_styles = failure_advice.get("blocked_styles") or []
        if blocked_styles:
            negative_clauses.append("avoid failed style memory: " + ", ".join(blocked_styles[:4]))
        # Append last (lower priority than identity clauses, which must not be
        # truncated) but keep the cap large enough that it survives.
        negative_clauses.append(self._skin_realism_negative_clause())

        provider_prompt = self._compact_prompt("；".join(clause for clause in prompt_clauses if clause), 2100)
        provider_negative_prompt = self._compact_prompt(
            ", ".join(clause for clause in negative_clauses if clause),
            820,
        )
        return {
            "schema_version": 1,
            "source_prompt": prompt,
            "subject_hint": subject_hint,
            "uses_identity_lock": uses_identity_lock,
            "state": state,
            "mode": mode,
            "reference_conditioning_mode": reference_conditioning_mode,
            "identity_edit_mode": identity_edit_mode,
            "weights": {
                "identity": weights.get("identity"),
                "style": weights.get("style"),
                "prompt": weights.get("prompt"),
                "state": weights.get("state"),
            },
            "identity": {
                "enabled": uses_identity_lock,
                "reference_count": identity.get("reference_count", 0),
                "embedding_dim": identity.get("embedding_dim", 0),
                "constraints": constraints if uses_identity_lock else {},
                "reason": "identity_priority_above_style" if uses_identity_lock else "prompt_subject_overrides_character_lock",
            },
            "style": {
                "preset": style.get("preset"),
                "lighting": style.get("lighting"),
                "camera_language": style.get("camera_language"),
                "lora_id": lora.get("id") if uses_character_identity else None,
                "lora_weight": lora.get("weight") if uses_character_identity else None,
            },
            "memory": self._conditioning_memory_summary(character["id"], style) if uses_character_identity else {
                "best_angle": None,
                "preferred_style": None,
                "average_success_score": 0.0,
                "blocked_styles": [],
            },
            "controlnet": {
                "pose": pose_control.get("pose"),
                "pose_label": pose_control.get("label"),
                "pose_source": pose_control.get("source"),
                "pose_lock": pose_control.get("weight"),
                "enabled": bool(pose_control.get("enabled")),
            },
            "references": reference_guidance,
            "provider_prompt": provider_prompt,
            "provider_negative_prompt": provider_negative_prompt,
            "prompt_hash": hashlib.sha256(provider_prompt.encode("utf-8")).hexdigest()[:16],
        }

    def _identity_prompt_clause(
        self,
        character: Dict[str, Any],
        constraints: Dict[str, Any],
        weights: Dict[str, Any],
    ) -> str:
        age_distribution = constraints.get("age_distribution") or {}
        age_label = max(age_distribution, key=age_distribution.get) if age_distribution else "adult"
        return (
            f"同一角色身份锁定：角色 {character.get('name')} 必须保持同一张脸；"
            f"身份权重 {float(weights.get('identity', 0.0)):.2f} 高于风格权重 {float(weights.get('style', 0.0)):.2f}；"
            f"保持眼距 {constraints.get('eye_distance', 'stable')}、"
            f"{constraints.get('jaw_shape', 'stable')} 脸型、鼻梁 {constraints.get('nose_bridge', 'stable')}、"
            f"{age_label} 年龄观感。"
        )

    def _subject_uses_character_identity(self, subject_hint: str) -> bool:
        return subject_hint in {"portrait", "female", "male", "child"}

    def _non_character_subject_clause(self, subject_hint: str) -> str:
        clauses = {
            "product": "主体约束：生成产品、商品或单页广告视觉，不生成人像，不使用人物参考。",
            "car": "主体约束：生成汽车商业广告画面，车辆是主角，不生成人像或角色参考。",
            "landscape": "主体约束：生成风景、城市或建筑画面，不生成人像或角色参考。",
            "animal": "主体约束：生成动物或宠物画面，不生成人像或角色参考。",
            "male": "主体约束：按提示词生成男性主体，不套用当前女性角色或人物参考。",
            "child": "主体约束：按提示词生成儿童主体，不套用当前角色或人物参考。",
        }
        return clauses.get(subject_hint, "")

    def _non_character_negative_clause(self, subject_hint: str) -> str:
        if subject_hint in {"product", "car", "landscape", "animal"}:
            return "human portrait, face close-up, reference face, identity lock, character headshot"
        if subject_hint in {"male", "child"}:
            return "female character face, reference face, identity lock, copied persona face"
        return ""

    def _style_prompt_clause(self, style: Dict[str, Any], lora: Dict[str, Any], subject_hint: str = "portrait") -> str:
        uses_character_identity = self._subject_uses_character_identity(subject_hint)
        camera_language = str(style.get("camera_language") or "").strip()
        if not uses_character_identity and any(token in camera_language.lower() for token in ["portrait", "face", "headshot"]):
            camera_language = ""
        parts = [
            style.get("preset"),
            style.get("lighting"),
            style.get("color"),
            camera_language,
        ]
        if uses_character_identity and (lora.get("label") or lora.get("name")):
            parts.append(f"LoRA {lora.get('label') or lora.get('name')} {float(lora.get('weight') or 0.0):.2f}")
            parts.extend((lora.get("trigger_tokens") or [])[:3])
        clean = [str(part).strip() for part in parts if str(part or "").strip()]
        return "风格约束：" + "，".join(clean) if clean else ""

    def _memory_prompt_clause(self, character_id: str, style: Dict[str, Any]) -> str:
        summary = self._conditioning_memory_summary(character_id, style)
        clauses = []
        if summary.get("best_angle"):
            clauses.append(f"优先 {summary['best_angle']} 构图")
        if summary.get("preferred_style"):
            clauses.append(f"延续高分风格 {summary['preferred_style']}")
        return "记忆推荐：" + "，".join(clauses) if clauses else ""

    def _reference_prompt_clause(self, group: Dict[str, Any], item: Dict[str, Any]) -> str:
        group_label = str(group.get("label") or "参考").strip()
        item_label = str(item.get("label") or "").strip()
        item_prompt = str(item.get("prompt") or "").strip()
        if item_label and item_prompt:
            return f"{group_label}:{item_label}，{item_prompt}"
        if item_prompt:
            return item_prompt
        return f"{group_label}参考：{item_label}"

    def _face_reference_lock_clause(self) -> str:
        return (
            "人脸参考硬约束：主参考脸优先级高于风格与场景；保持参考脸的脸型轮廓、下颌线、"
            "颧骨宽度、眼距、鼻梁高度、嘴唇比例、年龄观感和肤质，不要重塑成另一张脸。"
        )

    def _is_identity_preserving_edit(self, prompt: str) -> bool:
        text = str(prompt or "").lower()
        return self._prompt_requests_remove_eyewear(prompt) or any(
            token in text
            for token in [
                "人物不变",
                "人不变",
                "身份不变",
                "主体不变",
                "人物主体不变",
                "主体保持不变",
                "保持主体",
                "保持人物主体",
                "主体一致",
                "保持人物",
                "保持原人",
                "保持本人",
                "人物一致",
                "人物一致性",
                "人物要求一致性",
                "同一人",
                "不得有差异",
                "严格遵守人物",
                "严格遵守人物的脸型",
                "只修改",
                "只去",
                "仅修改",
                "仅去",
                "strictly preserve identity",
                "same person",
                "identity consistency",
                "preserve the person",
            ]
        )

    def _identity_edit_prompt_clause(self) -> str:
        return (
            "身份编辑模式：只执行用户指定的小范围编辑；不得重新生成、商业化美化、年轻化、换脸或重塑成新模特。"
            "保留原人的脸型轮廓、下颌线、颧骨、眼距、鼻梁、嘴型、年龄观感、肤色、皮肤纹理、发型、头部角度和服装关系。"
        )

    def _identity_edit_negative_clause(self) -> str:
        return (
            "new face, different person, different model, beautified face, fashion makeover, commercial ad makeover, "
            "younger face, older face, changed hairstyle, changed jawline, changed cheekbones, changed nose, "
            "changed mouth, changed eye spacing, over-retouched skin, plastic skin"
        )

    def _eyewear_edit_prompt_clause(self, prompt: str) -> str:
        text = str(prompt or "")
        typo_guard = "眼睛" in text and "眼镜" not in text
        typo_note = "如果用户写成“眼睛去掉”，按“眼镜去掉”理解；保留双眼自然完整。" if typo_guard else ""
        return (
            "眼镜编辑约束：只移除眼镜/墨镜/镜片/镜框及其反光，保留真实双眼、眉眼形态、眼距、眼神方向、"
            "鼻梁、脸型和原人物身份；不要改变脸、不要换人、不要生成空洞眼眶。"
            + typo_note
        )

    def _skin_realism_negative_clause(self) -> str:
        # Push back on FLUX/Seedream's default airbrushed look so faces keep real
        # texture. Used by the negative-prompt-capable providers (通义万象/火山/
        # 可灵/fal ultra/kontext); flux-lora has no negative input and instead gets
        # a positive realism clause in _append_skin_realism_clause.
        return (
            "smooth plastic skin, airbrushed, over-retouched, heavy beauty filter, "
            "waxy skin, doll-like face, porcelain skin, over-smoothed, glossy CGI skin, "
            "oily skin, shiny skin, greasy skin, sweaty skin, specular highlights, skin glare, "
            "磨皮, 过度美颜, 塑料感皮肤, 假面, 油光, 油腻皮肤, 反光"
        )

    def _visual_artifact_negative_clause(self) -> str:
        return (
            "no text, no words, no letters, no captions, no subtitles, no labels, no UI panels, "
            "no watermark, no logo, no signature, no typography, no garbled text, no pseudo text, "
            "不要文字，不要字幕，不要标签，不要水印，不要 logo，不要界面文字，不要乱码字"
        )

    def _prompt_requests_remove_eyewear(self, prompt: str) -> bool:
        text = str(prompt or "").lower()
        explicit = any(
            token in text
            for token in [
                # Common Chinese typo where 眼睛 (eyes) is written for 眼镜 (glasses);
                # kept explicit so it is recognized even without a glasses noun.
                "眼睛去掉",
                "去掉眼睛",
                "眼睛给去",
                "眼睛取掉",
                "取掉眼睛",
                "去眼镜",
                "去墨镜",
                "去太阳镜",
                "remove glasses",
                "without glasses",
                "no glasses",
                "remove sunglasses",
                "without sunglasses",
                "no sunglasses",
                "take off glasses",
                "take off sunglasses",
            ]
        )
        if explicit:
            return True
        # Combinatorial fallback: an eyewear noun plus any removal intent. This is
        # far more robust than enumerating every verb/noun phrasing — e.g. it now
        # catches 取掉/拿掉/摘下/去除 ("只把眼镜取掉") which the old phrase list missed.
        eyewear_nouns = ["眼镜", "墨镜", "太阳镜", "镜片", "镜框", "glasses", "sunglasses", "eyewear", "spectacles"]
        removal_verbs = [
            "去掉", "取掉", "拿掉", "摘掉", "摘下", "摘了", "去除", "脱掉", "卸掉",
            "拿下", "取下", "去了", "给去", "不要", "没有", "remove", "without", "take off", "get rid",
        ]
        has_eyewear = any(noun in text for noun in eyewear_nouns)
        has_removal = any(verb in text for verb in removal_verbs)
        return has_eyewear and has_removal

    def _prompt_requests_object_removal(self, prompt: str) -> bool:
        text = str(prompt or "").lower()
        return any(
            token in text
            for token in [
                "去掉",
                "去除",
                "删除",
                "移除",
                "擦除",
                "清除",
                "清理",
                "不要",
                "remove",
                "erase",
                "delete",
                "clean up",
            ]
        )

    def _conditioning_memory_summary(self, character_id: str, style: Dict[str, Any]) -> Dict[str, Any]:
        preferences = self.manager.memory_store.character_preferences(character_id)
        failure_advice = self.manager.memory_store.avoid_failure_styles(
            style.get("preset"), character_id=character_id
        )
        best_angle = (preferences.get("best_angles") or [{}])[0].get("pose")
        preferred_style = (preferences.get("preferred_styles") or [{}])[0].get("style")
        return {
            "best_angle": best_angle,
            "preferred_style": preferred_style,
            "average_success_score": preferences.get("average_success_score", 0.0),
            "blocked_styles": failure_advice.get("blocked_styles", []),
        }

    def _compact_prompt(self, value: str, limit: int) -> str:
        text = re.sub(r"\s+", " ", str(value or "")).strip()
        return text[:limit]

    def _normalize_reference_guidance(self, guidance: Any) -> list[Dict[str, Any]]:
        if not isinstance(guidance, list):
            return []
        normalized = []
        for group in guidance[:8]:
            if not isinstance(group, dict):
                continue
            items = []
            raw_items = group.get("items") if isinstance(group.get("items"), list) else []
            for item in raw_items[:12]:
                if not isinstance(item, dict):
                    continue
                normalized_item = {
                    "id": str(item.get("id") or "").strip(),
                    "label": str(item.get("label") or "").strip(),
                    "prompt": str(item.get("prompt") or "").strip(),
                }
                image_path = str(item.get("image") or "").strip()
                if image_path:
                    normalized_item["image"] = image_path
                source_generation_id = str(item.get("source_generation_id") or "").strip()
                if source_generation_id:
                    normalized_item["source_generation_id"] = source_generation_id
                if isinstance(item.get("mask"), dict):
                    try:
                        normalized_item["mask"] = self._normalize_canvas_edit_mask(item["mask"])
                    except ValueError:
                        pass
                items.append(normalized_item)
            if items:
                normalized.append(
                    {
                        "kind": str(group.get("kind") or "").strip(),
                        "label": str(group.get("label") or "").strip(),
                        "items": items,
                    }
                )
        return normalized

    def _effective_reference_guidance(
        self,
        reference_guidance: list[Dict[str, Any]],
        subject_hint: str,
        mode: str,
    ) -> list[Dict[str, Any]]:
        uses_character_identity = self._subject_uses_character_identity(subject_hint)
        effective = []
        for group in reference_guidance:
            kind = str(group.get("kind") or "").strip()
            if kind == "face" and not uses_character_identity:
                continue
            items = group.get("items") if isinstance(group.get("items"), list) else []
            if items:
                effective.append({**group, "items": items})
        return effective

    def _create_local_generation_preview(
        self,
        generation_id: str,
        source_index: int,
        prompt: str,
        mode: str,
        state: str,
        size: str,
        reference_guidance: list[Dict[str, Any]],
    ) -> str:
        generated_dir = self.static_dir / "assets" / "generated"
        generated_dir.mkdir(parents=True, exist_ok=True)
        file_name = f"{generation_id}.svg"
        file_path = generated_dir / file_name
        canvas_width, canvas_height = self._preview_canvas(size)

        seed_source = "|".join(
            [
                generation_id,
                str(source_index),
                prompt,
                mode,
                state,
                ",".join(item.get("label", "") for group in reference_guidance for item in group.get("items", [])),
            ]
        )
        digest = hashlib.sha256(seed_source.encode("utf-8")).digest()
        subject = self._prompt_subject(prompt)
        accent = ["#735cff", "#4fd69f", "#efcb64", "#f07167"][digest[11] % 4]
        label = escape(f"{generation_id.replace('gen-', '#')} · V{source_index + 1}")
        mode_label = escape(mode or "文生图")
        if subject not in {"female", "portrait"}:
            svg = self._subject_preview_svg(
                subject=subject,
                digest=digest,
                accent=accent,
                label=label,
                mode_label=mode_label,
                canvas_width=canvas_width,
                canvas_height=canvas_height,
            )
            file_path.write_text(svg, encoding="utf-8")
            return f"assets/generated/{file_name}"

        base_index = source_index % 4 + 1
        source_file = self.static_dir / "assets" / f"persona-ref-{base_index}.png"
        if source_file.exists():
            source_href = "data:image/png;base64," + base64.b64encode(source_file.read_bytes()).decode("ascii")
        else:
            source_href = f"../persona-ref-{base_index}.png"
        hue = int(digest[1] % 58) - 29
        saturation = 0.88 + (digest[2] % 32) / 100
        brightness = 0.9 + (digest[3] % 24) / 100
        contrast = 0.94 + (digest[4] % 18) / 100
        scale = 1.02 + (digest[5] % 9) / 100
        shift_x = int(digest[6] % 70) - 35
        shift_y = int(digest[7] % 46) - 23
        rotation = (int(digest[8] % 7) - 3) * 0.8
        warm_opacity = 0.16 + (digest[9] % 14) / 100
        cool_opacity = 0.1 + (digest[10] % 12) / 100
        image_width = int(960 * scale)
        image_height = int(720 * scale)
        image_x = int((960 - image_width) / 2 + shift_x)
        image_y = int((720 - image_height) / 2 + shift_y)
        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_width}" height="{canvas_height}" viewBox="0 0 960 720" preserveAspectRatio="xMidYMid slice">
  <defs>
    <filter id="tone">
      <feColorMatrix type="hueRotate" values="{hue}"/>
      <feColorMatrix type="saturate" values="{saturation:.2f}"/>
      <feComponentTransfer>
        <feFuncR type="linear" slope="{brightness:.2f}" intercept="0"/>
        <feFuncG type="linear" slope="{brightness:.2f}" intercept="0"/>
        <feFuncB type="linear" slope="{brightness:.2f}" intercept="0"/>
      </feComponentTransfer>
      <feComponentTransfer>
        <feFuncR type="linear" slope="{contrast:.2f}" intercept="-0.02"/>
        <feFuncG type="linear" slope="{contrast:.2f}" intercept="-0.02"/>
        <feFuncB type="linear" slope="{contrast:.2f}" intercept="-0.02"/>
      </feComponentTransfer>
    </filter>
    <linearGradient id="warm" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0" stop-color="#fff0c4" stop-opacity="{warm_opacity:.2f}"/>
      <stop offset="0.48" stop-color="{accent}" stop-opacity="0.06"/>
      <stop offset="1" stop-color="#111827" stop-opacity="0.2"/>
    </linearGradient>
    <linearGradient id="cool" x1="1" x2="0" y1="0" y2="1">
      <stop offset="0" stop-color="#d9f7ff" stop-opacity="{cool_opacity:.2f}"/>
      <stop offset="1" stop-color="#0b0f17" stop-opacity="0.0"/>
    </linearGradient>
  </defs>
  <rect width="960" height="720" fill="#10131a"/>
  <image href="{source_href}" x="{image_x}" y="{image_y}" width="{image_width}" height="{image_height}" preserveAspectRatio="xMidYMid slice" filter="url(#tone)" transform="rotate({rotation:.2f} 480 360)"/>
  <rect width="960" height="720" fill="url(#warm)"/>
  <rect width="960" height="720" fill="url(#cool)"/>
  <path d="M0 626 C220 584 365 640 540 602 C700 568 828 590 960 548 L960 720 L0 720 Z" fill="#090d13" opacity="0.22"/>
  <rect x="24" y="24" width="912" height="672" rx="18" fill="none" stroke="{accent}" stroke-opacity="0.34" stroke-width="2"/>
  <g font-family="Inter, Arial, sans-serif" font-weight="700">
    <rect x="34" y="36" width="142" height="34" rx="10" fill="#080b10" opacity="0.58"/>
    <text x="48" y="58" font-size="16" fill="#f7f9fc">{label}</text>
    <rect x="784" y="36" width="132" height="34" rx="10" fill="{accent}" opacity="0.82"/>
    <text x="805" y="58" font-size="15" fill="#ffffff">{mode_label}</text>
  </g>
</svg>
"""
        file_path.write_text(svg, encoding="utf-8")
        return f"assets/generated/{file_name}"

    def _prompt_subject(self, prompt: str) -> str:
        text = str(prompt or "").lower()
        excludes_people = any(token in text for token in [
            "不要人物",
            "不要人像",
            "无人物",
            "无人像",
            "不生成人",
            "no people",
            "no person",
            "without people",
        ])
        if any(token in text for token in ["男人", "男性", "男孩", "男士", "父亲", "man", "male", "boy", "gentleman"]):
            return "male"
        if any(token in text for token in ["儿童", "小孩", "孩子", "child", "kid"]):
            return "child"
        if not excludes_people:
            if any(token in text for token in ["女人", "女性", "女孩", "女模特", "亚洲女性", "女性角色", "女角色", "woman", "female", "girl"]):
                return "female"
            if any(token in text for token in ["参考人脸", "人脸", "脸部", "人像", "肖像", "半身", "模特", "角色", "portrait", "face", "model"]):
                return "portrait"
        if any(token in text for token in ["汽车", "跑车", "轿车", "车辆", "车 ", "car", "vehicle", "sports car"]):
            return "car"
        if any(token in text for token in [
            "产品",
            "商品",
            "包装",
            "香水",
            "瓶子",
            "单页",
            "落地页",
            "详情页",
            "广告页",
            "保健品",
            "海参",
            "电商",
            "product",
            "bottle",
            "package",
            "landing page",
            "single page",
            "advertorial",
        ]):
            return "product"
        if any(token in text for token in ["风景", "山", "大海", "海边", "海岸", "海面", "森林", "城市", "建筑", "landscape", "mountain", "city", "building"]):
            return "landscape"
        if any(token in text for token in ["狗", "猫", "动物", "宠物", "dog", "cat", "animal", "pet"]):
            return "animal"
        return "portrait"

    def _subject_label(self, subject: str) -> str:
        return {
            "male": "男性主体",
            "child": "儿童主体",
            "car": "汽车主体",
            "product": "产品主体",
            "landscape": "风景主体",
            "animal": "动物主体",
            "female": "角色主体",
            "portrait": "角色主体",
        }.get(subject, "提示词主体")

    def _subject_preview_svg(
        self,
        subject: str,
        digest: bytes,
        accent: str,
        label: str,
        mode_label: str,
        canvas_width: int,
        canvas_height: int,
    ) -> str:
        bg_a = ["#17202b", "#1e2736", "#151c24", "#201b2c"][digest[0] % 4]
        bg_b = ["#516b63", "#65776f", "#7a5f58", "#526175"][digest[1] % 4]
        sun_x = 120 + digest[2] % 620
        sun_y = 70 + digest[3] % 160
        subject_label = self._subject_label(subject)
        drawings = {
            "male": f"""
  <circle cx="480" cy="224" r="74" fill="#d8aa86"/>
  <path d="M406 218 C424 126 550 126 566 220 C528 190 461 183 406 218 Z" fill="#1f252b"/>
  <path d="M332 616 C358 420 602 420 628 616 Z" fill="{accent}" opacity="0.88"/>
  <rect x="386" y="290" width="188" height="250" rx="86" fill="#2c3442"/>
  <path d="M386 360 C430 402 528 402 574 360" fill="none" stroke="#ffffff" stroke-opacity="0.28" stroke-width="18"/>
""",
            "child": f"""
  <circle cx="482" cy="244" r="66" fill="#efbf9e"/>
  <path d="M420 232 C440 166 526 160 548 232 C512 211 456 211 420 232 Z" fill="#442c24"/>
  <path d="M350 622 C380 440 584 440 614 622 Z" fill="{accent}" opacity="0.78"/>
  <circle cx="452" cy="250" r="8" fill="#1f2937"/>
  <circle cx="512" cy="250" r="8" fill="#1f2937"/>
  <path d="M450 292 Q482 316 514 292" fill="none" stroke="#8b4b3e" stroke-width="8" stroke-linecap="round"/>
""",
            "car": f"""
  <path d="M160 458 L270 330 H628 L782 458 Z" fill="{accent}" opacity="0.92"/>
  <rect x="118" y="438" width="724" height="112" rx="40" fill="#1d2531"/>
  <path d="M300 344 H594 L680 438 H226 Z" fill="#d7eef4" opacity="0.72"/>
  <circle cx="282" cy="554" r="58" fill="#070a0e"/>
  <circle cx="676" cy="554" r="58" fill="#070a0e"/>
  <circle cx="282" cy="554" r="24" fill="#9aa5b2"/>
  <circle cx="676" cy="554" r="24" fill="#9aa5b2"/>
""",
            "product": f"""
  <ellipse cx="480" cy="614" rx="238" ry="34" fill="#06090f" opacity="0.36"/>
  <rect x="384" y="190" width="192" height="330" rx="44" fill="#f2f5f8"/>
  <rect x="412" y="226" width="136" height="168" rx="30" fill="{accent}" opacity="0.82"/>
  <rect x="432" y="130" width="96" height="74" rx="22" fill="#cfd6df"/>
  <path d="M384 492 H576 V536 C536 558 424 558 384 536 Z" fill="#d8dee6"/>
""",
            "landscape": f"""
  <circle cx="{sun_x}" cy="{sun_y}" r="68" fill="#ffe0a1" opacity="0.86"/>
  <path d="M0 500 L190 302 L360 500 Z" fill="#263b34"/>
  <path d="M220 520 L500 230 L820 520 Z" fill="#334b42"/>
  <path d="M560 530 L760 330 L960 530 Z" fill="#425c50"/>
  <path d="M0 590 C210 540 392 636 580 572 C750 514 860 560 960 530 V720 H0 Z" fill="{accent}" opacity="0.38"/>
""",
            "animal": f"""
  <ellipse cx="484" cy="450" rx="188" ry="132" fill="#b88964"/>
  <circle cx="404" cy="310" r="70" fill="#c99973"/>
  <circle cx="558" cy="310" r="70" fill="#c99973"/>
  <path d="M365 274 L326 176 L424 236 Z" fill="#8b5e45"/>
  <path d="M595 274 L640 176 L538 236 Z" fill="#8b5e45"/>
  <circle cx="452" cy="322" r="10" fill="#10131a"/>
  <circle cx="512" cy="322" r="10" fill="#10131a"/>
  <path d="M464 366 Q482 384 500 366" fill="none" stroke="#38251d" stroke-width="8" stroke-linecap="round"/>
""",
        }
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_width}" height="{canvas_height}" viewBox="0 0 960 720" preserveAspectRatio="xMidYMid slice">
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0" stop-color="{bg_a}"/>
      <stop offset="1" stop-color="{bg_b}"/>
    </linearGradient>
  </defs>
  <rect width="960" height="720" fill="url(#bg)"/>
  <circle cx="{sun_x}" cy="{sun_y}" r="150" fill="#ffffff" opacity="0.08"/>
  {drawings.get(subject, drawings["product"])}
  <rect x="24" y="24" width="912" height="672" rx="18" fill="none" stroke="{accent}" stroke-opacity="0.38" stroke-width="2"/>
  <g font-family="Inter, Arial, sans-serif" font-weight="700">
    <rect x="34" y="36" width="142" height="34" rx="10" fill="#080b10" opacity="0.58"/>
    <text x="48" y="58" font-size="16" fill="#f7f9fc">{label}</text>
    <rect x="724" y="36" width="192" height="34" rx="10" fill="{accent}" opacity="0.84"/>
    <text x="744" y="58" font-size="15" fill="#ffffff">{escape(subject_label)} · {mode_label}</text>
  </g>
</svg>
"""

    def _quality_report(
        self,
        packet: Dict[str, Any],
        character: Dict[str, Any],
        prompt: str,
        negative_prompt: str,
        mode: str,
        image: str,
        index: int,
        subject_hint: str = "portrait",
    ) -> Dict[str, Any]:
        if not self._subject_uses_character_identity(subject_hint):
            return {
                "face_match_score": 0.98,
                "subject_match_score": 0.98,
                "threshold": 0.82,
                "match": True,
                "status": "pass",
                "identity_margin": None,
                "review_note": "非人像主体按提示词生成，已跳过角色人脸一致性质检。",
                "checked_by": "deterministic-local-subject-gate",
                "score_kind": "subject_gate",
                "identity_similarity": {
                    "status": "skipped",
                    "method": "not_applicable",
                    "match_verified": False,
                    "review_note": "非人像主体不执行角色人脸相似度检查。",
                },
                "image": image,
            }
        weights = packet.get("weights") or {}
        identity_weight = float(weights.get("identity", 0.0))
        style_weight = float(weights.get("style", 0.0))
        margin = identity_weight - style_weight
        consistency = float(character.get("consistency_score", 0.0))
        reference_count = int((character.get("identity") or {}).get("reference_count") or 0)
        threshold = 0.82 if reference_count < 5 else 0.78

        score = 0.58
        score += identity_weight * 0.26
        score += max(0.0, min(margin, 0.35)) * 0.5
        score += min(consistency, 1.0) * 0.08
        score -= max(style_weight - 0.7, 0.0) * 0.14
        score -= index * 0.012
        if mode == "图生图":
            score += 0.025
        if any(token in negative_prompt for token in ["脸部漂移", "变形", "低质量"]):
            score += 0.018
        if "身份锁定" in prompt:
            score += 0.015
        score = round(max(0.0, min(0.98, score)), 3)

        identity_similarity = self._identity_similarity_report(character, image)
        identity_review_required = (
            self._requires_verified_identity_quality(image)
            and identity_similarity.get("match_verified") is not True
        )
        drift_risk = packet.get("drift_risk")
        if drift_risk == "high":
            status = "fail"
        elif drift_risk == "medium" or score < threshold:
            status = "review"
        else:
            status = "pass"
        score_kind = "conditioning_proxy"
        if identity_review_required:
            score = round(min(score, max(0.0, threshold - 0.02)), 3)
            score_kind = "identity_unverified_proxy"
            if status == "pass":
                status = "review"
        match = status == "pass"
        if identity_review_required:
            match = False
            reason = "真实 API 结果只有条件/结构代理分，未接入 ArcFace/InsightFace 同人认证；当前结果必须人工复核，不能标为同一人通过。"
        else:
            reason = {
                "pass": "身份权重高于风格，生成结果通过本地一致性质检。",
                "review": "身份与风格权重差距偏小，建议加强锁脸后再复用。",
                "fail": "身份权重与风格权重差距不足，已写入失败记忆用于避坑。",
            }[status]
        return {
            "face_match_score": score,
            "threshold": threshold,
            "match": match,
            "status": status,
            "identity_margin": round(margin, 3),
            "review_note": reason,
            "checked_by": "deterministic-local-quality-gate",
            "score_kind": score_kind,
            "identity_similarity": identity_similarity,
            "image": image,
        }

    def _requires_verified_identity_quality(self, image: str) -> bool:
        normalized = str(image or "").strip().lower().removeprefix("./")
        return normalized.startswith("assets/generated/") and normalized.endswith((".jpg", ".jpeg", ".png", ".webp"))

    def _quality_needs_identity_review_backfill(self, generation: Dict[str, Any], quality: Dict[str, Any]) -> bool:
        if quality.get("score_kind") != "conditioning_proxy" or quality.get("status") != "pass":
            return False
        prompt = str(generation.get("prompt") or "")
        subject_hint = str(generation.get("subject_hint") or self._prompt_subject(prompt))
        if not self._subject_uses_character_identity(subject_hint):
            return False
        if not self._requires_verified_identity_quality(str(generation.get("image") or "")):
            return False
        similarity = quality.get("identity_similarity") if isinstance(quality.get("identity_similarity"), dict) else {}
        return similarity.get("match_verified") is not True

    def _quality_memory_score(self, quality: Dict[str, Any]) -> float:
        if quality.get("status") == "fail":
            return min(0.38, float(quality.get("face_match_score") or 0.0))
        return float(quality.get("face_match_score") or 0.0)

    def _identity_similarity_report(self, character: Dict[str, Any], image: str) -> Dict[str, Any]:
        reference_image = self._primary_face_reference_image(character)
        if not reference_image:
            return {
                "status": "not_available",
                "method": "none",
                "match_verified": False,
                "review_note": "角色没有可用于质检的主参考脸。",
            }

        reference_face = self._opencv_frontal_face_report(reference_image)
        generated_face = self._opencv_frontal_face_report(image)
        method = "opencv_haar_structure_proxy"
        if reference_face.get("status") == "unavailable" or generated_face.get("status") == "unavailable":
            return {
                "status": "not_available",
                "method": "none",
                "match_verified": False,
                "reference_image": reference_image,
                "generated_image": image,
                "review_note": "本机未安装可用的人脸相似度模型；需要 ArcFace/InsightFace 才能验证同一人。",
            }
        if reference_face.get("status") == "unsupported" or generated_face.get("status") == "unsupported":
            return {
                "status": "not_available",
                "method": method,
                "match_verified": False,
                "reference_image": reference_image,
                "generated_image": image,
                "reference_face": reference_face,
                "generated_face": generated_face,
                "review_note": "当前图片格式无法做 OpenCV 脸检；需要栅格图片和 ArcFace/InsightFace 做同人验证。",
            }
        if not reference_face.get("detected") or not generated_face.get("detected"):
            return {
                "status": "review",
                "method": method,
                "score": 0.0,
                "match_verified": False,
                "reference_image": reference_image,
                "generated_image": image,
                "reference_face": reference_face,
                "generated_face": generated_face,
                "review_note": "OpenCV 未稳定检测到参考脸或生成脸，无法确认脸型一致。",
            }

        structure = self._face_structure_similarity(reference_face, generated_face)
        reliable = bool(structure.get("reliable"))
        return {
            "status": "structure_proxy_pass" if reliable else "review",
            "method": method,
            "score": structure.get("score"),
            "threshold": structure.get("threshold"),
            "confidence": structure.get("confidence"),
            "components": structure.get("components"),
            "structure_proxy": reliable,
            "match_verified": False,
            "reference_image": reference_image,
            "generated_image": image,
            "reference_face": reference_face,
            "generated_face": generated_face,
            "review_note": (
                "OpenCV 结构代理通过：脸框比例、眼距/对称度等局部结构接近；"
                "这不是同一人认证，生产环境仍需 ArcFace 或 InsightFace 复核。"
                if reliable
                else "OpenCV 结构代理未达阈值或置信度不足，生成结果需要人工复核脸型；"
                "生产同人认证仍需 ArcFace 或 InsightFace。"
            ),
        }

    def _face_structure_similarity(
        self,
        reference_face: Dict[str, Any],
        generated_face: Dict[str, Any],
    ) -> Dict[str, Any]:
        reference_structure = reference_face.get("structure") if isinstance(reference_face.get("structure"), dict) else {}
        generated_structure = generated_face.get("structure") if isinstance(generated_face.get("structure"), dict) else {}
        metric_specs = [
            ("face_aspect_w_h", 0.22, 0.28, "脸框宽高"),
            ("eye_distance_ratio", 0.16, 0.34, "眼距比例"),
            ("symmetry", 0.22, 0.14, "左右对称"),
            ("contrast", 0.35, 0.08, "面部对比"),
            ("brightness", 0.4, 0.06, "亮度"),
            ("sharpness", 0.55, 0.1, "清晰度"),
        ]
        components = []
        weighted_total = 0.0
        observed_weight = 0.0
        possible_weight = sum(weight for _, _, weight, _ in metric_specs)
        for key, tolerance, weight, label in metric_specs:
            left = reference_structure.get(key)
            right = generated_structure.get(key)
            if left is None or right is None:
                continue
            try:
                delta = abs(float(left) - float(right))
            except (TypeError, ValueError):
                continue
            score = max(0.0, 1.0 - min(1.0, delta / tolerance))
            weighted_total += score * weight
            observed_weight += weight
            components.append(
                {
                    "id": key,
                    "label": label,
                    "reference": round(float(left), 3),
                    "generated": round(float(right), 3),
                    "delta": round(delta, 3),
                    "score": round(score, 3),
                }
            )
        if observed_weight == 0:
            return {
                "score": 0.0,
                "threshold": 0.74,
                "confidence": 0.0,
                "reliable": False,
                "components": components,
            }
        score = weighted_total / observed_weight
        confidence = observed_weight / possible_weight if possible_weight else 0.0
        return {
            "score": round(score, 3),
            "threshold": 0.74,
            "confidence": round(confidence, 3),
            "reliable": score >= 0.74 and confidence >= 0.45,
            "components": components,
        }

    def _primary_face_reference_image(self, character: Dict[str, Any]) -> str:
        assets = character.get("reference_assets") if isinstance(character.get("reference_assets"), list) else []
        active_assets = [asset for asset in assets if isinstance(asset, dict) and asset.get("active", True)]
        ordered_assets = active_assets or [asset for asset in assets if isinstance(asset, dict)]
        for asset in ordered_assets:
            image = str(asset.get("image") or "").strip()
            if image:
                return image
        identity = character.get("identity") if isinstance(character.get("identity"), dict) else {}
        face_images = identity.get("face_images") if isinstance(identity.get("face_images"), list) else []
        for image in face_images:
            text = str(image or "").strip()
            if text:
                return text
        return ""

    def _opencv_frontal_face_report(self, image: str) -> Dict[str, Any]:
        image_path = str(image or "").strip()
        static_file = self._resolve_static_image_path(image_path)
        if static_file is None:
            return {"status": "unsupported", "detected": False, "image": image_path}
        if static_file.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            return {"status": "unsupported", "detected": False, "image": image_path}
        try:
            import cv2  # type: ignore[import-not-found]
        except Exception:
            return {"status": "unavailable", "detected": False, "image": image_path}

        image_data = cv2.imread(str(static_file))
        if image_data is None:
            return {"status": "unsupported", "detected": False, "image": image_path}
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        face_cascade = cv2.CascadeClassifier(cascade_path)
        if face_cascade.empty():
            return {"status": "unavailable", "detected": False, "image": image_path}

        gray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=4, minSize=(30, 30))
        if len(faces) == 0:
            return {
                "status": "detected_none",
                "detected": False,
                "image": image_path,
                "image_size": {"width": int(image_data.shape[1]), "height": int(image_data.shape[0])},
            }
        x, y, width, height = max(faces, key=lambda face: int(face[2]) * int(face[3]))
        image_area = int(image_data.shape[0]) * int(image_data.shape[1])
        box_area = int(width) * int(height)
        face_gray = gray[int(y) : int(y + height), int(x) : int(x + width)]
        structure = self._opencv_face_structure(face_gray, cv2)
        return {
            "status": "detected",
            "detected": True,
            "image": image_path,
            "image_size": {"width": int(image_data.shape[1]), "height": int(image_data.shape[0])},
            "box": {"x": int(x), "y": int(y), "w": int(width), "h": int(height)},
            "box_aspect_w_h": round(float(width) / float(height or 1), 3),
            "box_area_ratio": round(float(box_area) / float(image_area or 1), 4),
            "structure": structure,
        }

    def _opencv_face_structure(self, face_gray: Any, cv2: Any) -> Dict[str, Any]:
        shape = getattr(face_gray, "shape", [0, 0])
        height = int(shape[0] or 0)
        width = int(shape[1] or 0)
        if height <= 0 or width <= 0:
            return {}

        mean, stddev = cv2.meanStdDev(face_gray)
        brightness = float(mean[0][0]) / 255.0
        contrast = min(1.0, float(stddev[0][0]) / 96.0)
        try:
            sharpness = min(1.0, float(cv2.Laplacian(face_gray, cv2.CV_64F).var()) / 900.0)
        except Exception:
            sharpness = 0.0

        half_width = max(1, width // 2)
        left = face_gray[:, :half_width]
        right = face_gray[:, width - half_width :]
        try:
            right_flipped = cv2.flip(right, 1)
            right_resized = cv2.resize(right_flipped, (left.shape[1], left.shape[0]))
            symmetry_delta = float(cv2.mean(cv2.absdiff(left, right_resized))[0]) / 255.0
            symmetry = max(0.0, 1.0 - min(1.0, symmetry_delta / 0.34))
        except Exception:
            symmetry = None

        structure: Dict[str, Any] = {
            "face_aspect_w_h": round(float(width) / float(height or 1), 3),
            "brightness": round(brightness, 3),
            "contrast": round(contrast, 3),
            "sharpness": round(sharpness, 3),
        }
        if symmetry is not None:
            structure["symmetry"] = round(symmetry, 3)

        eye_distance = self._opencv_eye_distance_ratio(face_gray, cv2)
        if eye_distance is not None:
            structure["eye_distance_ratio"] = eye_distance
        return structure

    def _opencv_eye_distance_ratio(self, face_gray: Any, cv2: Any) -> Optional[float]:
        shape = getattr(face_gray, "shape", [0, 0])
        height = int(shape[0] or 0)
        width = int(shape[1] or 0)
        if height <= 0 or width <= 0:
            return None
        cascade_path = cv2.data.haarcascades + "haarcascade_eye_tree_eyeglasses.xml"
        eye_cascade = cv2.CascadeClassifier(cascade_path)
        if eye_cascade.empty():
            return None
        upper_face = face_gray[: max(1, int(height * 0.64)), :]
        min_eye = max(8, min(width, height) // 12)
        eyes = eye_cascade.detectMultiScale(
            upper_face,
            scaleFactor=1.08,
            minNeighbors=4,
            minSize=(min_eye, min_eye),
        )
        if len(eyes) < 2:
            return None
        eye_candidates = sorted(eyes, key=lambda eye: int(eye[2]) * int(eye[3]), reverse=True)[:6]
        centers = sorted((float(ex + ew / 2), float(ey + eh / 2)) for ex, ey, ew, eh in eye_candidates)
        best_distance = 0.0
        for left_index, left in enumerate(centers):
            for right in centers[left_index + 1 :]:
                distance = abs(right[0] - left[0])
                vertical_delta = abs(right[1] - left[1])
                if vertical_delta > height * 0.22:
                    continue
                if distance > best_distance:
                    best_distance = distance
        if best_distance <= width * 0.16:
            return None
        return round(min(1.0, best_distance / float(width)), 3)

    def _generation_model_route(self, image_model: str, image_model_label: str) -> Dict[str, Any]:
        if str(image_model or "").strip() == "persona-local-preview":
            return self._local_model_route(image_model, image_model_label)
        api_settings = self.settings.get("api") or {}
        active_provider = str(api_settings.get("provider") or "").strip()
        requested_provider = self._provider_for_image_model(image_model)
        provider_locked = requested_provider in {"fal", "wanx", "volcengine", "kling"}
        candidates: list[Dict[str, Any]] = []
        if requested_provider:
            candidates.append(self._api_profile_for_provider(requested_provider))
        if not provider_locked and active_provider and active_provider != requested_provider:
            candidates.append(api_settings)
        for candidate in candidates:
            route = self._external_model_route_from_profile(candidate, image_model, image_model_label)
            if route:
                return route
        return self._local_model_route(image_model, image_model_label)

    def _external_model_route_from_profile(
        self,
        api_settings: Dict[str, Any],
        image_model: str,
        image_model_label: str,
    ) -> Optional[Dict[str, Any]]:
        provider = str(api_settings.get("provider") or "").strip()
        configured_model = str(api_settings.get("model") or "").strip()
        base_url = str(api_settings.get("base_url") or "").strip()
        external_ready = bool(
            api_settings.get("enabled")
            and configured_model
            and self._external_api_auth_is_set(provider, api_settings)
        )
        if not external_ready:
            return None
        provider_label = self._provider_label(provider)
        return {
            "mode": "external_api",
            "provider": provider or "custom",
            "provider_label": provider_label,
            "model": configured_model,
            "label": f"{provider_label} · {configured_model}",
            "base_url": base_url,
            "configured": True,
            "request_model": image_model,
            "request_label": image_model_label,
            "status": "ready",
            "real_generation": False,
        }

    def _fal_profile_ready(self) -> bool:
        profile = self._api_profile_for_provider("fal")
        return bool(
            profile.get("enabled")
            and self._external_api_auth_is_set("fal", profile)
        )

    def _default_canvas_edit_model(self, instruction: str) -> tuple[str, str]:
        if self._fal_profile_ready():
            if self._prompt_requests_object_removal(instruction):
                return "fal-ai/flux-pro/v1/erase", "fal.ai · FLUX.1 Pro Erase"
            return "fal-ai/flux-pro/v1/fill", "fal.ai · FLUX.1 Pro Fill"
        return "persona-local-preview", "画布局部重绘 · 本地预览"

    def _api_profile_for_provider(self, provider: str) -> Dict[str, Any]:
        api_settings = self.settings.get("api") or {}
        normalized_provider = str(provider or "").strip()
        profiles = api_settings.get("profiles") if isinstance(api_settings.get("profiles"), dict) else {}
        profile = profiles.get(normalized_provider) if isinstance(profiles, dict) else None
        if isinstance(profile, dict):
            return self._normalize_api_profile(normalized_provider, profile)
        if str(api_settings.get("provider") or "").strip() == normalized_provider:
            return self._normalize_api_profile(normalized_provider, api_settings)
        return self._default_api_profile(normalized_provider)

    def _provider_for_image_model(self, image_model: str) -> str:
        model = str(image_model or "").strip()
        exact = {
            "fal-ai/flux-pro/v1.1-ultra": "fal",
            "fal-ai/flux/ultra": "fal",
            "flux-2-max": "flux",
            "flux-2-pro-preview": "flux",
            "flux-2-pro": "flux",
            "flux-2-flex": "flux",
            "stable-image-ultra": "stable-diffusion",
            "midjourney-v8.1": "midjourney",
            "gpt-image-1.5": "openai",
            "gemini-3.1-flash-image": "google-imagen",
            "wan2.6": "wanx",
            "wan2.6-image": "wanx",
            "wan2.6-t2i": "wanx",
            "wan2.6-t2i-preview": "wanx",
            "glm-image": "zhipu",
            "doubao-seedream-5-0-260128": "volcengine",
            "kling-v3": "kling",
            "kling/kling-v3-omni-image-generation": "kling",
            "wenxin-yige-sft": "wenxin",
        }
        if model in exact:
            return exact[model]
        if model.startswith("fal-ai/"):
            return "fal"
        if model.startswith("doubao-seedream"):
            return "volcengine"
        if model.startswith("wan"):
            return "wanx"
        if model.startswith("kling"):
            return "kling"
        return ""

    def _local_model_route(self, image_model: str = "", image_model_label: str = "") -> Dict[str, Any]:
        model = image_model or "persona-local-preview"
        label = image_model_label or self._image_model_label(model)
        return {
            "mode": "local_demo",
            "provider": "local",
            "provider_label": "本地演示",
            "model": model,
            "label": label,
            "base_url": "",
            "configured": False,
            "request_model": model,
            "request_label": label,
            "status": "simulated",
            "real_generation": False,
        }

    def _should_call_external_generation(
        self,
        model_route: Dict[str, Any],
        mode: str = "文生图",
        reference_guidance: Optional[list[Dict[str, Any]]] = None,
    ) -> bool:
        if (
            model_route.get("mode") != "external_api"
            or model_route.get("configured") is not True
        ):
            return False
        provider = str(model_route.get("provider") or "").strip()
        if not self._external_api_auth_is_set(provider, self._api_profile_for_provider(provider)):
            return False
        base_url = str(model_route.get("base_url") or "").strip()
        reference_mode = self._reference_conditioning_mode(mode, reference_guidance)
        if provider == "wanx" and "dashscope.aliyuncs.com" in base_url:
            if reference_mode == "图生图":
                return len(self._collect_reference_images_for_wanx(reference_guidance, reference_mode)) >= 1
            return True
        if provider == "volcengine":
            # Volcano Ark (Doubao Seedream) text-to-image via a single Bearer key.
            return True
        if provider == "kling":
            if reference_mode == "图生图":
                return self._collect_reference_image_for_kling(reference_guidance, reference_mode) is not None
            return True
        if provider == "fal":
            return True
        if provider == "flux":
            if reference_mode == "图生图":
                return len(self._collect_reference_images_for_bfl(reference_guidance, reference_mode)) >= 1
            return True
        return False

    def _external_generation_kind(
        self,
        provider: str,
        mode: str,
        reference_guidance: list[Dict[str, Any]],
    ) -> str:
        if provider == "wanx":
            return self._wanx_generation_kind(mode, reference_guidance)
        reference_mode = self._reference_conditioning_mode(mode, reference_guidance)
        if provider == "volcengine" and self._collect_reference_images_for_wanx(reference_guidance, reference_mode):
            return "img2img"
        if provider == "kling" and self._collect_reference_image_for_kling(reference_guidance, reference_mode):
            return "img2img"
        if provider == "fal" and self._collect_reference_image_for_fal(reference_guidance):
            return "img2img"
        if provider == "flux" and self._collect_reference_images_for_bfl(reference_guidance, reference_mode):
            return "img2img"
        return "t2i"

    def _wanx_generation_kind(self, mode: str, reference_guidance: list[Dict[str, Any]]) -> str:
        reference_mode = self._reference_conditioning_mode(mode, reference_guidance)
        if reference_mode == "图生图" and self._collect_reference_images_for_wanx(reference_guidance, reference_mode):
            return "img2img"
        return "t2i"

    def _reference_conditioning_mode(
        self,
        mode: str,
        reference_guidance: Optional[list[Dict[str, Any]]],
    ) -> str:
        if mode == "图生图":
            return "图生图"
        if mode == "文生图" and self._reference_guidance_has_image(reference_guidance):
            return "图生图"
        return mode

    def _reference_guidance_has_image(self, reference_guidance: Optional[list[Dict[str, Any]]]) -> bool:
        for group in reference_guidance or []:
            items = group.get("items") if isinstance(group.get("items"), list) else []
            for item in items:
                if str(item.get("image") or "").strip():
                    return True
        return False

    def _reference_guidance_has_kind(
        self,
        reference_guidance: Optional[list[Dict[str, Any]]],
        kind: str,
    ) -> bool:
        expected = str(kind or "").strip()
        for group in reference_guidance or []:
            if str(group.get("kind") or "").strip() == expected and group.get("items"):
                return True
        return False

    def _create_external_generation_previews(
        self,
        generation_ids: list[str],
        prompt: str,
        negative_prompt: str,
        count: int,
        size: str,
        mode: str,
        model_route: Dict[str, Any],
        reference_guidance: list[Dict[str, Any]],
    ) -> list[str]:
        provider = str(model_route.get("provider") or "").strip()
        reference_mode = self._reference_conditioning_mode(mode, reference_guidance)
        reference_images = self._collect_reference_images_for_wanx(reference_guidance, reference_mode)
        paths = []
        for generation_id in generation_ids[:count]:
            if provider == "volcengine":
                image_url = self._call_ark_generation(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    size=size,
                    model_route=model_route,
                    reference_images=reference_images,
                )
            elif provider == "kling":
                image_url = self._call_kling_generation(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    size=size,
                    mode=reference_mode,
                    model_route=model_route,
                    reference_guidance=reference_guidance,
                )
            elif provider == "fal":
                if model_route.get("character_lora"):
                    image_url = self._call_fal_lora_generation(
                        prompt=prompt,
                        negative_prompt=negative_prompt,
                        size=size,
                        model_route=model_route,
                    )
                else:
                    image_url = self._call_fal_generation(
                        prompt=prompt,
                        negative_prompt=negative_prompt,
                        size=size,
                        model_route=model_route,
                        reference_guidance=reference_guidance,
                    )
            elif provider == "flux":
                image_url = self._call_bfl_flux_generation(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    size=size,
                    model_route=model_route,
                    mode=reference_mode,
                    reference_guidance=reference_guidance,
                )
            else:
                image_url = self._call_wanx_sync_generation(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    size=size,
                    mode=reference_mode,
                    model_route=model_route,
                    reference_images=reference_images,
                )
            paths.append(self._download_external_image(image_url, generation_id))
        return paths

    def _collect_reference_images_for_wanx(
        self,
        reference_guidance: Optional[list[Dict[str, Any]]],
        mode: str,
    ) -> list[str]:
        if mode != "图生图":
            return []

        images = []
        for group in reference_guidance or []:
            if group.get("kind") != "face":
                continue
            for item in group.get("items", []):
                encoded = self._encode_image_for_wanx(item.get("image"))
                if encoded and encoded not in images:
                    images.append(encoded)

        for group in reference_guidance or []:
            if group.get("kind") == "face":
                continue
            for item in group.get("items", []):
                encoded = self._encode_image_for_wanx(item.get("image"))
                if encoded and encoded not in images:
                    images.append(encoded)

        if not images:
            for index in range(1, 5):
                encoded = self._encode_image_for_wanx(f"assets/persona-ref-{index}.png")
                if encoded:
                    images.append(encoded)
                    break
        return images[:4]

    def _resolve_static_image_path(self, image_path: str) -> Optional[Path]:
        if not image_path or str(image_path).startswith("data:"):
            return None
        clean_path = str(image_path).split("?", 1)[0].strip().removeprefix("./")
        if clean_path.startswith("/"):
            clean_path = clean_path.lstrip("/")
        static_file = (self.static_dir / clean_path).resolve()
        if (
            (self.static_dir in static_file.parents or static_file == self.static_dir)
            and static_file.exists()
            and static_file.is_file()
        ):
            return static_file
        return None

    def _encode_image_for_wanx(self, image_path: Any) -> Optional[str]:
        if not image_path:
            return None
        text = str(image_path).strip()
        if text.startswith("data:image/"):
            return text
        static_file = self._resolve_static_image_path(text)
        if static_file is None:
            return None
        mime_type = mimetypes.guess_type(static_file.name)[0] or "image/png"
        if mime_type == "image/jpg":
            mime_type = "image/jpeg"
        encoded = base64.b64encode(static_file.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _collect_reference_image_for_kling(
        self,
        reference_guidance: Optional[list[Dict[str, Any]]],
        mode: str,
    ) -> Optional[Dict[str, str]]:
        if mode != "图生图":
            return None

        ordered_groups = list(reference_guidance or [])
        ordered_groups.sort(key=lambda group: 0 if group.get("kind") == "face" else 1)
        for group in ordered_groups:
            for item in group.get("items", []):
                encoded = self._encode_image_for_wanx(item.get("image"))
                if not encoded:
                    continue
                image = encoded.split(",", 1)[1] if encoded.startswith("data:image/") and "," in encoded else encoded
                return {
                    "image": image,
                    "image_reference": "face" if group.get("kind") == "face" else "subject",
                }
        return None

    def _collect_reference_image_for_fal(
        self,
        reference_guidance: Optional[list[Dict[str, Any]]],
    ) -> Optional[Dict[str, Any]]:
        ordered_groups = list(reference_guidance or [])
        ordered_groups.sort(key=lambda group: 0 if group.get("kind") == "face" else 1)
        for group in ordered_groups:
            kind = str(group.get("kind") or "").strip()
            for item in group.get("items", []):
                encoded = self._encode_image_for_wanx(item.get("image"))
                if not encoded:
                    continue
                return {
                    "image_url": encoded,
                    "source_path": str(item.get("image") or ""),
                    "mask": item.get("mask") if isinstance(item.get("mask"), dict) else None,
                    "kind": kind,
                    "image_prompt_strength": 0.82 if kind == "face" else 0.3,
                }
        return None

    def _fal_mask_data_url_for_reference(self, reference_image: Dict[str, Any]) -> Optional[str]:
        source_path = str(reference_image.get("source_path") or "")
        mask = reference_image.get("mask")
        if isinstance(mask, dict):
            return self._canvas_edit_mask_data_url(source_path, mask)
        return self._eyewear_inpaint_mask_data_url(source_path)

    def _eyewear_inpaint_mask_data_url(self, image_path: str) -> Optional[str]:
        static_file = self._resolve_static_image_path(str(image_path or ""))
        if static_file is None:
            return None
        try:
            import cv2  # type: ignore[import-not-found]
        except Exception:
            return self._fallback_eyewear_mask_data_url(static_file)

        image_data = cv2.imread(str(static_file))
        if image_data is None:
            return self._fallback_eyewear_mask_data_url(static_file)
        height, width = image_data.shape[:2]
        if height <= 0 or width <= 0:
            return None
        mask = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
        mask[:, :] = 0
        report = self._opencv_frontal_face_report(str(image_path or ""))
        box = report.get("box") if isinstance(report.get("box"), dict) else {}
        if box:
            face_x = int(box.get("x") or 0)
            face_y = int(box.get("y") or 0)
            face_w = int(box.get("w") or width * 0.48)
            face_h = int(box.get("h") or height * 0.48)
            # Cover the full eyewear extent: wide enough to reach the temples/arms
            # near the ears, and tall enough to span eyebrows down to mid-cheek.
            # If the mask leaves any frame/temple unmasked, FLUX fill repaints the
            # glasses back from that context, so erring large here is what makes
            # the removal actually stick.
            x1 = max(0, int(face_x - face_w * 0.24))
            x2 = min(width, int(face_x + face_w * 1.24))
            y1 = max(0, int(face_y + face_h * 0.10))
            y2 = min(height, int(face_y + face_h * 0.60))
        else:
            x1 = int(width * 0.08)
            x2 = int(width * 0.92)
            y1 = int(height * 0.14)
            y2 = int(height * 0.54)
        cv2.rectangle(mask, (x1, y1), (x2, y2), 255, thickness=-1)
        # Dilate the solid core so the whole frame is inside the removal region,
        # then feather the edge so the inpaint blends into the surrounding skin.
        dilate = max(7, int(min(width, height) * 0.03))
        mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (dilate, dilate)), iterations=1)
        kernel = max(5, int(min(width, height) * 0.018))
        if kernel % 2 == 0:
            kernel += 1
        mask = cv2.GaussianBlur(mask, (kernel, kernel), 0)
        ok, encoded = cv2.imencode(".png", mask)
        if not ok:
            return self._fallback_eyewear_mask_data_url(static_file)
        return "data:image/png;base64," + base64.b64encode(encoded.tobytes()).decode("ascii")

    def _canvas_edit_mask_data_url(self, image_path: str, mask: Dict[str, Any]) -> Optional[str]:
        static_file = self._resolve_static_image_path(str(image_path or ""))
        if static_file is None:
            return None
        dimensions = self._image_dimensions(static_file)
        if dimensions is None:
            return None
        width, height = dimensions
        rows = [bytearray(width) for _ in range(height)]
        for stroke in mask.get("strokes") or []:
            if not isinstance(stroke, dict):
                continue
            points = [point for point in stroke.get("points") or [] if isinstance(point, dict)]
            if not points:
                continue
            radius = max(1, int(round(min(width, height) * self._clamp_unit(stroke.get("brush"), default=0.035) * 0.62)))
            pixel_points = [
                (
                    int(round(self._clamp_unit(point.get("x")) * (width - 1))),
                    int(round(self._clamp_unit(point.get("y")) * (height - 1))),
                )
                for point in points
            ]
            for index, point in enumerate(pixel_points):
                self._paint_mask_disk(rows, width, height, point[0], point[1], radius)
                if index:
                    previous = pixel_points[index - 1]
                    self._paint_mask_line(rows, width, height, previous[0], previous[1], point[0], point[1], radius)
        return "data:image/png;base64," + base64.b64encode(
            self._grayscale_png(width, height, [bytes(row) for row in rows])
        ).decode("ascii")

    def _paint_mask_line(
        self,
        rows: list[bytearray],
        width: int,
        height: int,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        radius: int,
    ) -> None:
        steps = max(abs(x2 - x1), abs(y2 - y1), 1)
        for step in range(steps + 1):
            t = step / float(steps)
            x = int(round(x1 + (x2 - x1) * t))
            y = int(round(y1 + (y2 - y1) * t))
            self._paint_mask_disk(rows, width, height, x, y, radius)

    def _paint_mask_disk(
        self,
        rows: list[bytearray],
        width: int,
        height: int,
        center_x: int,
        center_y: int,
        radius: int,
    ) -> None:
        radius_sq = radius * radius
        x_min = max(0, center_x - radius)
        x_max = min(width - 1, center_x + radius)
        y_min = max(0, center_y - radius)
        y_max = min(height - 1, center_y + radius)
        for y in range(y_min, y_max + 1):
            row = rows[y]
            dy_sq = (y - center_y) * (y - center_y)
            for x in range(x_min, x_max + 1):
                if (x - center_x) * (x - center_x) + dy_sq <= radius_sq:
                    row[x] = 255

    def _fallback_eyewear_mask_data_url(self, static_file: Path) -> Optional[str]:
        dimensions = self._image_dimensions(static_file)
        if dimensions is None:
            return None
        width, height = dimensions
        x1 = int(width * 0.14)
        x2 = int(width * 0.86)
        y1 = int(height * 0.20)
        y2 = int(height * 0.48)
        rows = []
        for y in range(height):
            row = bytearray(width)
            if y1 <= y <= y2:
                row[x1:x2] = b"\xff" * max(0, x2 - x1)
            rows.append(bytes(row))
        return "data:image/png;base64," + base64.b64encode(self._grayscale_png(width, height, rows)).decode("ascii")

    def _image_dimensions(self, file_path: Path) -> Optional[tuple[int, int]]:
        data = file_path.read_bytes()[:65536]
        if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
            return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
        if data.startswith(b"\xff\xd8"):
            index = 2
            while index + 9 < len(data):
                if data[index] != 0xFF:
                    index += 1
                    continue
                marker = data[index + 1]
                index += 2
                if marker in {0xD8, 0xD9}:
                    continue
                if index + 2 > len(data):
                    break
                segment_length = int.from_bytes(data[index : index + 2], "big")
                if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                    if index + 7 <= len(data):
                        height = int.from_bytes(data[index + 3 : index + 5], "big")
                        width = int.from_bytes(data[index + 5 : index + 7], "big")
                        return width, height
                    break
                index += max(2, segment_length)
        return None

    def _grayscale_png(self, width: int, height: int, rows: list[bytes]) -> bytes:
        def chunk(kind: bytes, payload: bytes) -> bytes:
            checksum = zlib.crc32(kind + payload) & 0xFFFFFFFF
            return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)

        raw = b"".join(b"\x00" + row for row in rows)
        header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
        return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")

    def _collect_reference_images_for_bfl(
        self,
        reference_guidance: Optional[list[Dict[str, Any]]],
        mode: str,
    ) -> list[str]:
        if mode != "图生图":
            return []

        images = []
        ordered_groups = list(reference_guidance or [])
        ordered_groups.sort(key=lambda group: 0 if group.get("kind") == "face" else 1)
        for group in ordered_groups:
            for item in group.get("items", []):
                encoded = self._encode_image_for_bfl(item.get("image"))
                if encoded and encoded not in images:
                    images.append(encoded)
                if len(images) >= 8:
                    return images
        return images

    def _encode_image_for_bfl(self, image_path: Any) -> Optional[str]:
        if not image_path:
            return None
        text = str(image_path).strip()
        if text.startswith(("http://", "https://")):
            return text
        if text.startswith("data:image/"):
            return text.split(",", 1)[1] if "," in text else text
        static_file = self._resolve_static_image_path(text)
        if static_file is None:
            return None
        return base64.b64encode(static_file.read_bytes()).decode("ascii")

    def _call_wanx_sync_generation(
        self,
        prompt: str,
        negative_prompt: str,
        size: str,
        mode: str,
        model_route: Dict[str, Any],
        reference_images: Optional[list[str]] = None,
    ) -> str:
        api_settings = self._api_profile_for_provider(str(model_route.get("provider") or "wanx"))
        api_key = str(api_settings.get("api_key") or "").strip()
        if not api_key:
            raise ValueError("通义万象 API Key 未配置")

        endpoint = self._wanx_generation_endpoint(str(model_route.get("base_url") or ""))
        generation_kind = "img2img" if reference_images else "t2i"
        content = [{"text": (prompt or "写实摄影主体").strip()[:2100]}]
        if generation_kind == "img2img":
            for image in (reference_images or [])[:4]:
                content.append({"image": image})

        payload = {
            "model": self._wanx_model_name(str(model_route.get("model") or ""), generation_kind=generation_kind),
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": content,
                    }
                ]
            },
            "parameters": {
                "prompt_extend": True,
                "watermark": False,
                "n": 1,
                "size": self._dashscope_size(size),
            },
        }
        if generation_kind == "img2img":
            payload["parameters"]["enable_interleave"] = False
        if negative_prompt.strip():
            payload["parameters"]["negative_prompt"] = negative_prompt.strip()[:500]

        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                response_body = response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise ValueError(f"通义万象生成失败：HTTP {error.code} {self._compact_error(detail)}") from error
        except urllib.error.URLError as error:
            raise ValueError(f"通义万象生成失败：{error.reason}") from error
        except TimeoutError as error:
            raise ValueError("通义万象生成超时，请稍后重试") from error

        try:
            response_payload = json.loads(response_body.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("通义万象返回了无法解析的响应") from error

        image_url = self._extract_first_image_url(response_payload)
        if image_url:
            return image_url
        message = response_payload.get("message") or response_payload.get("code") or response_payload
        raise ValueError(f"通义万象生成失败：{self._compact_error(str(message))}")

    def _wanx_generation_endpoint(self, base_url: str) -> str:
        normalized = (base_url or "https://dashscope.aliyuncs.com/api/v1").strip().rstrip("/")
        if "/services/aigc/multimodal-generation/generation" in normalized:
            return normalized
        if normalized.endswith("/api/v1"):
            return f"{normalized}/services/aigc/multimodal-generation/generation"
        return f"{normalized}/api/v1/services/aigc/multimodal-generation/generation"

    def _wanx_model_name(self, model: str, generation_kind: str = "t2i") -> str:
        if generation_kind == "img2img":
            return "wan2.6-image"
        normalized = (model or "").strip()
        aliases = {
            "wan2.6": "wan2.6-t2i",
            "wan2.6-image": "wan2.6-t2i",
            "wan2.6-t2i-preview": "wan2.6-t2i",
        }
        return aliases.get(normalized, normalized or "wan2.6-t2i")

    def _dashscope_size(self, size: str) -> str:
        return {
            "1:1": "1280*1280",
            "3:4": "1104*1472",
            "4:3": "1472*1104",
            "16:9": "1696*960",
            "9:16": "960*1696",
        }.get(size, "1104*1472")

    def _call_ark_generation(
        self,
        prompt: str,
        negative_prompt: str,
        size: str,
        model_route: Dict[str, Any],
        reference_images: Optional[list[str]] = None,
    ) -> str:
        """Volcano Ark (Doubao Seedream) text-to-image, or image-to-image when
        reference images are supplied, via the OpenAI-compatible
        ``/images/generations`` endpoint with a single Bearer API key. Seedream
        4.0/5.0 accept an ``image`` field (a single base64/URL string, or an
        array for multi-reference) to condition generation on the character's
        face/scene references."""
        api_settings = self._api_profile_for_provider(str(model_route.get("provider") or "volcengine"))
        api_key = str(api_settings.get("api_key") or "").strip()
        if not api_key:
            raise ValueError("火山引擎 API Key 未配置")

        endpoint = self._ark_generation_endpoint(str(model_route.get("base_url") or ""))
        prompt_text = (prompt or "写实摄影主体").strip()[:2000]
        if negative_prompt.strip():
            prompt_text = f"{prompt_text}。避免：{negative_prompt.strip()[:400]}"
        payload = {
            "model": str(model_route.get("model") or "").strip() or "doubao-seedream-4-0-250828",
            "prompt": prompt_text,
            "size": self._ark_size(size),
            "response_format": "url",
            "n": 1,
            "watermark": False,
        }
        ark_references = [image for image in (reference_images or []) if image][:10]
        if ark_references:
            # Single reference stays a string; multiple references become an
            # array so Seedream uses them all as identity/scene conditioning.
            payload["image"] = ark_references[0] if len(ark_references) == 1 else ark_references
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                response_body = response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise ValueError(f"火山引擎生成失败：HTTP {error.code} {self._compact_error(detail)}") from error
        except urllib.error.URLError as error:
            raise ValueError(f"火山引擎生成失败：{error.reason}") from error
        except TimeoutError as error:
            raise ValueError("火山引擎生成超时，请稍后重试") from error

        try:
            response_payload = json.loads(response_body.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("火山引擎返回了无法解析的响应") from error

        image_url = self._extract_first_image_url(response_payload)
        if image_url:
            return image_url
        message = (
            response_payload.get("message")
            or response_payload.get("error")
            or response_payload.get("code")
            or response_payload
        )
        raise ValueError(f"火山引擎生成失败：{self._compact_error(str(message))}")

    def _ark_generation_endpoint(self, base_url: str) -> str:
        normalized = (base_url or "").strip().rstrip("/") or "https://ark.cn-beijing.volces.com/api/v3"
        if normalized.endswith("/images/generations"):
            return normalized
        return f"{normalized}/images/generations"

    def _ark_size(self, size: str) -> str:
        # Seedream on Volcano Ark rejects low-res 1K images; its image endpoint
        # currently requires at least 2560*1440 total pixels.
        return {
            "1:1": "2048x2048",
            "3:4": "1728x2304",
            "4:3": "2304x1728",
            "16:9": "2560x1440",
            "9:16": "1440x2560",
        }.get(size, "1728x2304")

    def _call_bfl_flux_generation(
        self,
        prompt: str,
        negative_prompt: str,
        size: str,
        model_route: Dict[str, Any],
        mode: str = "文生图",
        reference_guidance: Optional[list[Dict[str, Any]]] = None,
    ) -> str:
        api_settings = self._api_profile_for_provider(str(model_route.get("provider") or "flux"))
        api_key = str(api_settings.get("api_key") or "").strip()
        if not api_key:
            raise ValueError("FLUX / BFL API Key 未配置")

        width, height = self._bfl_size(size)
        reference_images = self._collect_reference_images_for_bfl(reference_guidance, mode)
        prompt_text = (prompt or "写实摄影主体").strip()[:4000]
        if reference_images:
            prompt_text = (
                f"{prompt_text}\n"
                "Use the provided input image references for identity, subject, pose, outfit, or scene consistency. "
                "When a face reference is present, preserve the same facial structure and proportions."
            )
        if negative_prompt.strip():
            prompt_text = f"{prompt_text}\nAvoid: {negative_prompt.strip()[:600]}"
        payload = {
            "prompt": prompt_text,
            "width": width,
            "height": height,
            "output_format": "jpeg",
        }
        for index, image in enumerate(reference_images[:8]):
            key = "input_image" if index == 0 else f"input_image_{index + 1}"
            payload[key] = image
        endpoint = self._bfl_generation_endpoint(
            str(model_route.get("base_url") or ""),
            str(model_route.get("model") or ""),
        )
        create_payload = self._bfl_json_request(
            urllib.request.Request(
                endpoint,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={
                    "accept": "application/json",
                    "x-key": api_key,
                    "Content-Type": "application/json",
                },
                method="POST",
            ),
            "创建任务",
        )
        polling_url = str(create_payload.get("polling_url") or "").strip()
        request_id = str(create_payload.get("id") or "").strip()
        immediate_url = self._extract_bfl_image_url(create_payload)
        if immediate_url:
            return immediate_url
        if not polling_url:
            message = create_payload.get("message") or create_payload.get("error") or create_payload
            raise ValueError(f"FLUX / BFL 生成失败：{self._compact_error(str(message))}")

        last_status = ""
        for attempt in range(60):
            result_payload = self._bfl_json_request(
                urllib.request.Request(
                    polling_url,
                    headers={
                        "accept": "application/json",
                        "x-key": api_key,
                    },
                    method="GET",
                ),
                "查询任务",
            )
            last_status = str(result_payload.get("status") or "").strip()
            if last_status == "Ready":
                image_url = self._extract_bfl_image_url(result_payload)
                if image_url:
                    return image_url
                raise ValueError("FLUX / BFL 生成成功但没有返回图片 URL")
            if last_status in {"Error", "Failed"}:
                message = result_payload.get("message") or result_payload.get("error") or result_payload
                raise ValueError(f"FLUX / BFL 生成失败：{self._compact_error(str(message))}")
            if attempt < 59:
                time.sleep(1)
        raise ValueError(f"FLUX / BFL 生成超时：任务 {request_id or 'unknown'} 状态 {last_status or 'unknown'}")

    def _bfl_json_request(self, request: urllib.request.Request, action: str) -> Dict[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                response_body = response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise ValueError(f"FLUX / BFL {action}失败：HTTP {error.code} {self._compact_error(detail)}") from error
        except urllib.error.URLError as error:
            raise ValueError(f"FLUX / BFL {action}失败：{error.reason}") from error
        except TimeoutError as error:
            raise ValueError(f"FLUX / BFL {action}超时，请稍后重试") from error

        try:
            payload = json.loads(response_body.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"FLUX / BFL {action}返回了无法解析的响应") from error
        if not isinstance(payload, dict):
            raise ValueError(f"FLUX / BFL {action}返回了无法识别的响应")
        return payload

    def _bfl_generation_endpoint(self, base_url: str, model: str) -> str:
        normalized_base = (base_url or "https://api.bfl.ai/v1").strip().rstrip("/")
        model_name = self._bfl_model_name(model)
        if normalized_base.endswith(f"/{model_name}"):
            return normalized_base
        return f"{normalized_base}/{model_name}"

    def _bfl_model_name(self, model: str) -> str:
        normalized = (model or "").strip().strip("/")
        aliases = {
            "flux-2-max": "flux-2-max",
            "flux.2-max": "flux-2-max",
            "black-forest-labs/flux.2-max": "flux-2-max",
            "black-forest-labs/flux-2-max": "flux-2-max",
        }
        return aliases.get(normalized, normalized or "flux-2-max")

    def _bfl_size(self, size: str) -> tuple[int, int]:
        return {
            "1:1": (1440, 1440),
            "3:4": (1440, 1920),
            "4:3": (1920, 1440),
            "16:9": (1920, 1088),
            "9:16": (1088, 1920),
        }.get(size, (1440, 1920))

    def _extract_bfl_image_url(self, payload: Dict[str, Any]) -> Optional[str]:
        result = payload.get("result") if isinstance(payload, dict) else {}
        if isinstance(result, dict):
            sample = result.get("sample")
            if isinstance(sample, str) and sample.startswith(("http://", "https://", "data:image/")):
                return sample
        return self._extract_first_image_url(payload)

    def _call_fal_generation(
        self,
        prompt: str,
        negative_prompt: str,
        size: str,
        model_route: Dict[str, Any],
        reference_guidance: list[Dict[str, Any]],
    ) -> str:
        api_settings = self._api_profile_for_provider(str(model_route.get("provider") or "fal"))
        api_key = str(api_settings.get("api_key") or "").strip()
        if not api_key:
            raise ValueError("fal.ai API Key 未配置")

        reference_image = self._collect_reference_image_for_fal(reference_guidance)
        model_name = self._fal_model_name(str(model_route.get("model") or ""))
        uses_kontext_edit = self._is_fal_kontext_model(model_name)
        uses_fill_inpaint = self._is_fal_fill_model(model_name)
        uses_erase_inpaint = self._is_fal_erase_model(model_name)
        prompt_text = (prompt or "写实摄影主体").strip()[:2500]
        if reference_image and reference_image.get("kind") == "face":
            prompt_text = (
                f"{prompt_text}. Use the reference image only as identity source. "
                "Preserve the exact same person, face shape, jawline, eye spacing, nose bridge, "
                "mouth proportions, age impression, skin texture, hairstyle, head angle, and clothing relationship. "
                "Perform only the requested small edit. Do not beautify into a new model, do not change age, "
                "do not change facial structure, and do not turn the subject into a different advertising portrait. "
                "If the request says to remove eyes in Chinese, interpret it as removing eyeglasses/sunglasses; "
                "keep both eyes natural and intact. Do not add any text, labels, captions, UI panels, watermark, "
                "logo, signature, or pseudo text inside the image."
            )
        if negative_prompt.strip():
            prompt_text = f"{prompt_text}。Avoid: {negative_prompt.strip()[:500]}"
        if uses_erase_inpaint:
            payload: Dict[str, Any] = {
                "sync_mode": False,
                "output_format": "jpeg",
                "dilate_pixels": 18,
            }
        else:
            payload = {
                "prompt": prompt_text,
                "sync_mode": False,
                "num_images": 1,
                "output_format": "jpeg",
                "safety_tolerance": "2",
                "enhance_prompt": False,
                "aspect_ratio": self._fal_aspect_ratio(size),
                "raw": False,
            }
        if uses_fill_inpaint:
            payload.pop("raw", None)
            payload.pop("aspect_ratio", None)
            if reference_image and isinstance(reference_image.get("mask"), dict):
                payload["prompt"] = (
                    "Edit only the masked area according to this instruction: "
                    f"{prompt_text[:1600]}. Preserve every unmasked pixel and keep the same person, face, "
                    "pose, clothing, lighting, background, camera angle, and image geometry unchanged."
                )
            else:
                payload["prompt"] = (
                    "Remove all eyeglasses, sunglasses, lenses, frames, reflections, and eyewear only inside the masked area. "
                    "Reconstruct natural eyes and nearby skin while preserving the original person's exact face, "
                    "jawline, cheeks, nose, mouth, hair, head shape, clothing, background, lighting, and all unmasked pixels. "
                    "No glasses, no sunglasses, no eyewear, no frames, no lenses. "
                    "Do not beautify, do not change identity, do not alter any unmasked area."
                )
        elif uses_kontext_edit:
            payload.pop("raw", None)
            payload["guidance_scale"] = 2.5
        if reference_image:
            payload["image_url"] = reference_image["image_url"]
            if uses_fill_inpaint or uses_erase_inpaint:
                mask_url = self._fal_mask_data_url_for_reference(reference_image)
                if not mask_url:
                    raise ValueError("fal.ai 局部一致性编辑需要可读取的原图和 mask")
                payload["mask_url"] = mask_url
            elif not uses_kontext_edit:
                payload["image_prompt_strength"] = reference_image["image_prompt_strength"]

        endpoint = self._fal_generation_endpoint(
            str(model_route.get("base_url") or ""),
            model_name,
        )
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Key {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                response_body = response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise ValueError(f"fal.ai 生成失败：HTTP {error.code} {self._compact_error(detail)}") from error
        except urllib.error.URLError as error:
            raise ValueError(f"fal.ai 生成失败：{error.reason}") from error
        except TimeoutError as error:
            raise ValueError("fal.ai 生成超时，请稍后重试") from error

        try:
            response_payload = json.loads(response_body.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("fal.ai 返回了无法解析的响应") from error

        image_url = self._extract_first_image_url(response_payload)
        if image_url:
            return image_url
        message = (
            response_payload.get("message")
            or response_payload.get("error")
            or response_payload.get("detail")
            or response_payload
        )
        raise ValueError(f"fal.ai 生成失败：{self._compact_error(str(message))}")

    def _fal_generation_endpoint(self, base_url: str, model: str) -> str:
        normalized_base = (base_url or "https://fal.run").strip().rstrip("/")
        model_name = self._fal_model_name(model)
        parsed = urlparse(normalized_base)
        if parsed.scheme in {"http", "https"} and parsed.netloc == "fal.run":
            raw_path_model = parsed.path.strip("/")
            path_model = self._fal_model_name(raw_path_model) if raw_path_model else model_name
            return f"{parsed.scheme}://{parsed.netloc}/{path_model or model_name}"
        if normalized_base.endswith(model_name):
            return normalized_base
        return f"{normalized_base}/{model_name}"

    def _fal_model_name(self, model: str) -> str:
        normalized = (model or "").strip().strip("/")
        aliases = {
            "fal-ai/flux/ultra": "fal-ai/flux-pro/v1.1-ultra",
            "flux/ultra": "fal-ai/flux-pro/v1.1-ultra",
            "flux-ultra": "fal-ai/flux-pro/v1.1-ultra",
            "flux-pro-ultra": "fal-ai/flux-pro/v1.1-ultra",
            "fal-ai/flux-pro/kontext": "fal-ai/flux-pro/kontext",
            "fal-ai/flux-pro/kontext/max": "fal-ai/flux-pro/kontext/max",
            "fal-ai/flux-pro/v1/fill": "fal-ai/flux-pro/v1/fill",
            "fal-ai/flux-pro/v1/erase": "fal-ai/flux-pro/v1/erase",
            "flux-pro-fill": "fal-ai/flux-pro/v1/fill",
            "flux-pro-erase": "fal-ai/flux-pro/v1/erase",
            "flux-kontext": "fal-ai/flux-pro/kontext",
            "flux-kontext-max": "fal-ai/flux-pro/kontext/max",
            "kontext": "fal-ai/flux-pro/kontext",
            "kontext-max": "fal-ai/flux-pro/kontext/max",
            "fill": "fal-ai/flux-pro/v1/fill",
            "erase": "fal-ai/flux-pro/v1/erase",
        }
        return aliases.get(normalized, normalized or "fal-ai/flux-pro/v1.1-ultra")

    def _is_fal_kontext_model(self, model: str) -> bool:
        return "kontext" in self._fal_model_name(model)

    def _is_fal_fill_model(self, model: str) -> bool:
        return self._fal_model_name(model) == "fal-ai/flux-pro/v1/fill"

    def _is_fal_erase_model(self, model: str) -> bool:
        return self._fal_model_name(model) == "fal-ai/flux-pro/v1/erase"

    def _fal_aspect_ratio(self, size: str) -> str:
        allowed = {"21:9", "16:9", "4:3", "3:2", "1:1", "2:3", "3:4", "9:16", "9:21"}
        return size if size in allowed else "3:4"

    # ------------------------------------------------------------------
    # Per-character LoRA: train a real identity LoRA on fal and route the
    # character's fresh (non-edit) generations through fal-ai/flux-lora so the
    # face is locked far tighter than prompt/reference conditioning alone.
    # ------------------------------------------------------------------

    def _append_skin_realism_clause(self, prompt: str) -> str:
        text = str(prompt or "").strip()
        if "skin" in text.lower() and "pore" in text.lower():
            return text  # caller already asked for skin texture; don't double up
        clause = (
            "extremely detailed realistic skin with deep visible pores, rough uneven skin texture, "
            "slight blemishes and imperfections, fine wrinkles, weathered natural skin, "
            "completely matte dry skin with no oily sheen, no shine, no specular highlights, "
            "no skin glare, no sweat, flat shadowless overcast lighting, no direct light, "
            "no highlights, no rim light, shot on 35mm film Kodak Portra 400 with visible grain, "
            "macro skin detail, light stubble, candid unretouched photograph, no makeup, "
            "no skin smoothing, no beauty filter, sharp realistic photo"
        )
        return f"{text}, {clause}" if text else clause

    def _fal_lora_image_size(self, size: str) -> Any:
        return {
            "1:1": "square_hd",
            "3:4": "portrait_4_3",
            "9:16": "portrait_16_9",
            "4:3": "landscape_4_3",
            "16:9": "landscape_16_9",
        }.get(size, "portrait_4_3")

    def _character_lora_trigger(self, character_id: str, character: Dict[str, Any]) -> str:
        existing = ""
        if isinstance(character.get("fal_lora"), dict):
            existing = str(character["fal_lora"].get("trigger_word") or "").strip()
        if existing:
            return existing
        base = re.sub(r"[^a-z0-9]+", "", str(character_id or "").lower()) or "persona"
        return f"{base}person"

    def _character_lora_summary(self, character: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        lora = character.get("fal_lora") if isinstance(character.get("fal_lora"), dict) else None
        if not lora:
            return None
        # Surface trained-LoRA state to the UI without leaking the weights URL
        # into broad listings (it is still on the character record for routing).
        return {
            "status": str(lora.get("status") or "ready"),
            "trigger_word": str(lora.get("trigger_word") or ""),
            "scale": float(lora.get("scale") or 0.85),
            "steps": lora.get("steps"),
            "reference_count": lora.get("reference_count"),
            "trained_at": lora.get("trained_at"),
            "has_weights": bool(str(lora.get("url") or "").strip()),
        }

    def _character_fal_lora(self, character: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        lora = character.get("fal_lora") if isinstance(character.get("fal_lora"), dict) else None
        if not lora:
            return None
        url = str(lora.get("url") or "").strip()
        status = str(lora.get("status") or "").strip()
        if not url or status not in {"ready", "completed", "trained"}:
            return None
        return lora

    def _maybe_route_to_character_lora(
        self,
        model_route: Dict[str, Any],
        character: Dict[str, Any],
        conditioning_manifest: Dict[str, Any],
        uses_character_identity: bool,
    ) -> Dict[str, Any]:
        # LoRA inference is text-to-image: only for fresh character generations,
        # not identity edits (those stay on Kontext/fill, which keep the source
        # photo). Requires fal as the active provider and a trained LoRA.
        if not uses_character_identity or conditioning_manifest.get("identity_edit_mode"):
            return model_route
        if str(model_route.get("provider") or "").strip() != "fal":
            return model_route
        lora = self._character_fal_lora(character)
        if not lora:
            return model_route
        return {
            **model_route,
            "model": "fal-ai/flux-lora",
            "label": "fal.ai · FLUX LoRA · 角色身份",
            "character_lora": {
                "url": str(lora.get("url") or ""),
                "scale": float(lora.get("scale") or 0.85),
                "trigger_word": str(lora.get("trigger_word") or ""),
            },
            "character_lora_route": True,
            "character_lora_routed_from": self._fal_model_name(str(model_route.get("model") or "")),
        }

    def _call_fal_lora_generation(
        self,
        prompt: str,
        negative_prompt: str,
        size: str,
        model_route: Dict[str, Any],
    ) -> str:
        api_settings = self._api_profile_for_provider(str(model_route.get("provider") or "fal"))
        api_key = str(api_settings.get("api_key") or "").strip()
        if not api_key:
            raise ValueError("fal.ai API Key 未配置")
        lora = model_route.get("character_lora") if isinstance(model_route.get("character_lora"), dict) else {}
        lora_url = str((lora or {}).get("url") or "").strip()
        if not lora_url:
            raise ValueError("角色 LoRA 权重缺失")
        trigger = str((lora or {}).get("trigger_word") or "").strip()
        prompt_text = (prompt or "写实摄影主体").strip()[:2300]
        if trigger and trigger.lower() not in prompt_text.lower():
            prompt_text = f"{trigger}, {prompt_text}"
        # Skin realism: FLUX tends to airbrush faces. flux-lora (FLUX.1 dev) has no
        # negative-prompt input, so anchor realism in the positive prompt instead —
        # this keeps natural pores/texture and avoids the plastic, over-smoothed
        # look. A lower guidance also reads less "idealized".
        prompt_text = self._append_skin_realism_clause(prompt_text)
        # Identity-lock tuning: a stronger LoRA scale and a slightly lower
        # guidance let the trained face dominate the prompt; more steps stabilize
        # fine facial detail. Scale is clamped so a mis-stored value can't fry the
        # image.
        lora_scale = float((lora or {}).get("scale") or 1.0)
        lora_scale = max(0.6, min(1.4, lora_scale))
        payload = {
            "prompt": prompt_text,
            "image_size": self._fal_lora_image_size(size),
            "num_images": 1,
            "num_inference_steps": 44,
            "guidance_scale": 2.0,
            "output_format": "jpeg",
            "enable_safety_checker": True,
            "loras": [{"path": lora_url, "scale": lora_scale}],
        }
        endpoint = self._fal_generation_endpoint(str(model_route.get("base_url") or ""), "fal-ai/flux-lora")
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": f"Key {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                response_body = response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise ValueError(f"fal.ai LoRA 生成失败：HTTP {error.code} {self._compact_error(detail)}") from error
        except urllib.error.URLError as error:
            raise ValueError(f"fal.ai LoRA 生成失败：{error.reason}") from error
        except TimeoutError as error:
            raise ValueError("fal.ai LoRA 生成超时，请稍后重试") from error
        try:
            response_payload = json.loads(response_body.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("fal.ai LoRA 返回了无法解析的响应") from error
        image_url = self._extract_first_image_url(response_payload)
        if image_url:
            return image_url
        raise ValueError(f"fal.ai LoRA 生成失败：{self._compact_error(str(response_payload))}")

    def _image_bytes_for_training(self, image_path: Any) -> Optional[bytes]:
        text = str(image_path or "").strip()
        if text.startswith("data:image/") and "," in text:
            try:
                return base64.b64decode(text.split(",", 1)[1])
            except Exception:
                return None
        static_file = self._resolve_static_image_path(text)
        if static_file is None:
            return None
        try:
            return static_file.read_bytes()
        except OSError:
            return None

    def _build_character_reference_zip(self, reference_payloads: list[str], trigger_word: str) -> bytes:
        import io
        import zipfile

        buffer = io.BytesIO()
        count = 0
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for payload in reference_payloads:
                raw = self._image_bytes_for_training(payload)
                if not raw:
                    continue
                count += 1
                name = f"img_{count:02d}"
                archive.writestr(f"{name}.png", raw)
                if trigger_word:
                    archive.writestr(f"{name}.txt", f"a photo of {trigger_word}, the same person")
        if count == 0:
            raise ValueError("没有可用于训练的参考人脸图片")
        return buffer.getvalue()

    def _fal_storage_upload(self, data: bytes, content_type: str, file_name: str, api_key: str) -> str:
        """Upload bytes to fal's CDN-v3 storage and return a fal-hosted URL the
        trainer can fetch. Two-step: mint a short-lived token, then PUT the file."""
        token_request = urllib.request.Request(
            "https://rest.alpha.fal.ai/storage/auth/token?storage_type=fal-cdn-v3",
            data=b"{}",
            headers={"Authorization": f"Key {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(token_request, timeout=60) as response:
                token_payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise ValueError(f"fal.ai 存储令牌获取失败：HTTP {error.code} {self._compact_error(detail)}") from error
        except urllib.error.URLError as error:
            raise ValueError(f"fal.ai 存储令牌获取失败：{error.reason}") from error
        token = str(token_payload.get("token") or "").strip()
        base_url = str(token_payload.get("base_url") or "").strip().rstrip("/")
        if not token or not base_url:
            raise ValueError("fal.ai 存储令牌无效")
        upload_request = urllib.request.Request(
            f"{base_url}/files/upload",
            data=data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": content_type,
                "X-Fal-File-Name": file_name,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(upload_request, timeout=180) as response:
                upload_payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise ValueError(f"fal.ai 文件上传失败：HTTP {error.code} {self._compact_error(detail)}") from error
        except urllib.error.URLError as error:
            raise ValueError(f"fal.ai 文件上传失败：{error.reason}") from error
        access_url = str(upload_payload.get("access_url") or upload_payload.get("url") or "").strip()
        if not access_url:
            raise ValueError("fal.ai 文件上传未返回可访问地址")
        return access_url

    def _poll_fal_queue_result(self, status_url: str, response_url: str, api_key: str, attempts: int = 90, delay: float = 10.0) -> Dict[str, Any]:
        headers = {"Authorization": f"Key {api_key}"}
        for _ in range(max(1, attempts)):
            status_request = urllib.request.Request(status_url, headers=headers, method="GET")
            try:
                with urllib.request.urlopen(status_request, timeout=60) as response:
                    status_payload = json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as error:
                detail = error.read().decode("utf-8", errors="replace")
                raise ValueError(f"fal.ai 任务状态查询失败：HTTP {error.code} {self._compact_error(detail)}") from error
            except urllib.error.URLError as error:
                raise ValueError(f"fal.ai 任务状态查询失败：{error.reason}") from error
            status = str(status_payload.get("status") or "").upper()
            if status == "COMPLETED":
                result_url = str(status_payload.get("response_url") or response_url or "").strip()
                result_request = urllib.request.Request(result_url, headers=headers, method="GET")
                try:
                    with urllib.request.urlopen(result_request, timeout=120) as response:
                        return json.loads(response.read().decode("utf-8"))
                except urllib.error.HTTPError as error:
                    detail = error.read().decode("utf-8", errors="replace")
                    raise ValueError(f"fal.ai 任务结果获取失败：HTTP {error.code} {self._compact_error(detail)}") from error
                except urllib.error.URLError as error:
                    raise ValueError(f"fal.ai 任务结果获取失败：{error.reason}") from error
            if status in {"FAILED", "ERROR", "CANCELLED"}:
                raise ValueError(f"fal.ai 训练任务失败：{self._compact_error(str(status_payload))}")
            time.sleep(delay)
        raise ValueError("fal.ai 训练任务超时，请稍后在任务列表中重试")

    def _train_fal_lora_for_character(
        self,
        character_id: str,
        character: Dict[str, Any],
        reference_payloads: list[str],
        steps: int = 1000,
    ) -> Dict[str, Any]:
        api_settings = self._api_profile_for_provider("fal")
        api_key = str(api_settings.get("api_key") or "").strip()
        if not api_key:
            raise ValueError("fal.ai API Key 未配置，无法训练角色 LoRA")
        trigger_word = self._character_lora_trigger(character_id, character)
        zip_bytes = self._build_character_reference_zip(reference_payloads, trigger_word)
        images_url = self._fal_storage_upload(zip_bytes, "application/zip", f"{character_id}-refs.zip", api_key)
        submit_payload = {
            "images_data_url": images_url,
            "trigger_word": trigger_word,
            "steps": int(steps),
            "create_masks": True,
        }
        submit_request = urllib.request.Request(
            "https://queue.fal.run/fal-ai/flux-lora-fast-training",
            data=json.dumps(submit_payload).encode("utf-8"),
            headers={"Authorization": f"Key {api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(submit_request, timeout=120) as response:
                submit_response = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise ValueError(f"fal.ai LoRA 训练提交失败：HTTP {error.code} {self._compact_error(detail)}") from error
        except urllib.error.URLError as error:
            raise ValueError(f"fal.ai LoRA 训练提交失败：{error.reason}") from error
        request_id = str(submit_response.get("request_id") or "").strip()
        status_url = str(submit_response.get("status_url") or "").strip() or (
            f"https://queue.fal.run/fal-ai/flux-lora-fast-training/requests/{request_id}/status"
        )
        response_url = str(submit_response.get("response_url") or "").strip() or (
            f"https://queue.fal.run/fal-ai/flux-lora-fast-training/requests/{request_id}"
        )
        result = self._poll_fal_queue_result(status_url, response_url, api_key)
        lora_file = result.get("diffusers_lora_file") if isinstance(result.get("diffusers_lora_file"), dict) else {}
        lora_url = str((lora_file or {}).get("url") or "").strip()
        if not lora_url:
            raise ValueError(f"fal.ai 训练未返回 LoRA 权重：{self._compact_error(str(result))}")
        return {
            "url": lora_url,
            "trigger_word": trigger_word,
            "scale": 0.85,
            "status": "ready",
            "provider": "fal",
            "base_model": "fal-ai/flux-lora",
            "steps": int(steps),
            "request_id": request_id,
            "reference_count": len(reference_payloads),
            "trained_at": self._timestamp(),
        }

    def _call_kling_generation(
        self,
        prompt: str,
        negative_prompt: str,
        size: str,
        mode: str,
        model_route: Dict[str, Any],
        reference_guidance: list[Dict[str, Any]],
    ) -> str:
        api_profile = self._api_profile_for_provider(str(model_route.get("provider") or "kling"))
        auth_candidates = self._kling_auth_candidates(api_profile)
        if not auth_candidates:
            raise ValueError("可灵 API Key 或 Access Key + Secret Key 未配置")

        endpoints = self._kling_generation_endpoints(str(model_route.get("base_url") or ""))
        reference_image = self._collect_reference_image_for_kling(reference_guidance, mode)
        payload: Dict[str, Any] = {
            "model_name": self._kling_model_name(str(model_route.get("model") or "")),
            "prompt": (prompt or "写实摄影主体").strip()[:2500],
            "n": 1,
            "aspect_ratio": self._kling_aspect_ratio(size),
            "resolution": "1k",
            "watermark_info": {"enabled": False},
        }
        if reference_image:
            payload["image"] = reference_image["image"]
            payload["image_reference"] = reference_image["image_reference"]
        elif negative_prompt.strip():
            payload["negative_prompt"] = negative_prompt.strip()[:2500]

        create_payload: Dict[str, Any] | None = None
        selected_endpoint = ""
        selected_token = ""
        last_retryable_error: Exception | None = None
        for endpoint in endpoints:
            for auth_candidate in auth_candidates:
                token = str(auth_candidate.get("token") or "").strip()
                if not token:
                    continue
                try:
                    create_payload = self._kling_json_request(
                        urllib.request.Request(
                            endpoint,
                            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                            headers={
                                "Authorization": f"Bearer {token}",
                                "Content-Type": "application/json",
                            },
                            method="POST",
                        ),
                        "创建任务",
                    )
                    selected_endpoint = endpoint
                    selected_token = token
                    break
                except ValueError as error:
                    if self._kling_can_retry_auth_or_region(error):
                        last_retryable_error = error
                        continue
                    raise
            if create_payload is not None:
                break
        if create_payload is None:
            detail = self._compact_error(str(last_retryable_error or "未知错误"))
            raise ValueError(
                f"可灵创建任务失败：已尝试 {len(endpoints)} 个 API 域名和 "
                f"{len(auth_candidates)} 种鉴权，最后错误：{detail}"
            )

        create_data = create_payload.get("data") if isinstance(create_payload, dict) else {}
        task_id = str((create_data or {}).get("task_id") or (create_data or {}).get("id") or "").strip()
        immediate_url = self._extract_first_image_url(create_data)
        if immediate_url:
            return immediate_url
        if not task_id:
            message = create_payload.get("message") or create_payload.get("msg") or create_payload
            raise ValueError(f"可灵生成失败：{self._compact_error(str(message))}")

        query_endpoint = f"{selected_endpoint}/{task_id}"
        last_status = ""
        for attempt in range(30):
            query_payload = self._kling_json_request(
                urllib.request.Request(
                    query_endpoint,
                    headers={"Authorization": f"Bearer {selected_token}"},
                    method="GET",
                ),
                "查询任务",
            )
            query_data = query_payload.get("data") if isinstance(query_payload, dict) else {}
            last_status = str((query_data or {}).get("task_status") or (query_data or {}).get("status") or "").strip()
            if last_status == "succeed":
                image_url = self._extract_first_image_url((query_data or {}).get("task_result") or query_data)
                if image_url:
                    return image_url
                raise ValueError("可灵生成成功但没有返回图片 URL")
            if last_status in {"failed", "fail", "failure"}:
                message = (
                    (query_data or {}).get("task_status_msg")
                    or query_payload.get("message")
                    or query_payload.get("msg")
                    or last_status
                )
                raise ValueError(f"可灵生成失败：{self._compact_error(str(message))}")
            if attempt < 29:
                time.sleep(2)
        raise ValueError(f"可灵生成超时：任务 {task_id} 状态 {last_status or 'unknown'}")

    def _kling_json_request(self, request: urllib.request.Request, action: str) -> Dict[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                response_body = response.read()
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise ValueError(f"可灵{action}失败：HTTP {error.code} {self._compact_error(detail)}") from error
        except urllib.error.URLError as error:
            raise ValueError(f"可灵{action}失败：{error.reason}") from error
        except TimeoutError as error:
            raise ValueError(f"可灵{action}超时，请稍后重试") from error

        try:
            payload = json.loads(response_body.decode("utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"可灵{action}返回了无法解析的响应") from error

        code = payload.get("code") if isinstance(payload, dict) else None
        if code not in (None, 0, "0"):
            message = payload.get("message") or payload.get("msg") or payload.get("code")
            raise ValueError(f"可灵{action}失败：{self._compact_error(str(message))}")
        return payload

    def _kling_generation_endpoint(self, base_url: str, task_id: str = "") -> str:
        normalized = (base_url or "").strip().rstrip("/") or "https://api-singapore.klingai.com"
        if normalized.endswith("/v1/images/generations"):
            endpoint = normalized
        elif normalized.endswith("/images/generations"):
            endpoint = normalized
        elif normalized.endswith("/v1"):
            endpoint = f"{normalized}/images/generations"
        else:
            endpoint = f"{normalized}/v1/images/generations"
        return f"{endpoint}/{task_id}" if task_id else endpoint

    def _kling_generation_endpoints(self, base_url: str) -> list[str]:
        candidates = [
            base_url,
            "https://api.klingai.com",
            "https://api-singapore.klingai.com",
        ]
        endpoints: list[str] = []
        seen: set[str] = set()
        for candidate in candidates:
            endpoint = self._kling_generation_endpoint(candidate)
            if endpoint in seen:
                continue
            seen.add(endpoint)
            endpoints.append(endpoint)
        return endpoints

    def _kling_can_retry_auth_or_region(self, error: Exception) -> bool:
        detail = str(error).lower()
        retry_markers = (
            "http 401",
            "http 403",
            "unauthorized",
            "forbidden",
            "access key not found",
            "api key not found",
            "api-key",
            "invalid token",
            "invalid jwt",
            "signature",
            "鉴权",
        )
        return any(marker in detail for marker in retry_markers)

    def _kling_model_name(self, model: str) -> str:
        normalized = (model or "").strip()
        official = {"kling-v1", "kling-v1-5", "kling-v2", "kling-v2-new", "kling-v2-1", "kling-v3"}
        if normalized in official:
            return normalized
        lowered = normalized.lower()
        if "v3" in lowered:
            return "kling-v3"
        if "v2-1" in lowered or "v2.1" in lowered:
            return "kling-v2-1"
        if "v2-new" in lowered:
            return "kling-v2-new"
        if "v2" in lowered:
            return "kling-v2"
        if "v1-5" in lowered or "v1.5" in lowered:
            return "kling-v1-5"
        if "v1" in lowered:
            return "kling-v1"
        return "kling-v3"

    def _kling_aspect_ratio(self, size: str) -> str:
        allowed = {"16:9", "9:16", "1:1", "4:3", "3:4", "3:2", "2:3", "21:9"}
        return size if size in allowed else "3:4"

    def _preview_canvas(self, size: str) -> tuple[int, int]:
        return {
            "1:1": (960, 960),
            "3:4": (900, 1200),
            "4:3": (1200, 900),
            "16:9": (1280, 720),
            "9:16": (720, 1280),
        }.get(size, (900, 1200))

    def _extract_first_image_url(self, payload: Any) -> Optional[str]:
        if isinstance(payload, dict):
            for key in ("image", "url"):
                value = payload.get(key)
                if isinstance(value, str) and value.startswith(("http://", "https://", "data:image/")):
                    return value
            for value in payload.values():
                found = self._extract_first_image_url(value)
                if found:
                    return found
        if isinstance(payload, list):
            for item in payload:
                found = self._extract_first_image_url(item)
                if found:
                    return found
        return None

    def _download_external_image(self, image_url: str, generation_id: str) -> str:
        generated_dir = self.static_dir / "assets" / "generated"
        generated_dir.mkdir(parents=True, exist_ok=True)
        content_type = "image/png"
        if image_url.startswith("data:image/"):
            header, encoded = image_url.split(",", 1)
            content_type = header.split(";", 1)[0].removeprefix("data:")
            content = base64.b64decode(encoded)
        else:
            request = urllib.request.Request(image_url, headers={"User-Agent": "PersonaStudio/1.0"})
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    content = response.read()
                    content_type = response.headers.get_content_type() or content_type
            except urllib.error.URLError as error:
                raise ValueError(f"生成成功但图片下载失败：{error.reason}") from error
        if not content:
            raise ValueError("生成成功但图片内容为空")
        extension = {
            "image/jpeg": "jpg",
            "image/jpg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
        }.get(content_type.lower())
        if extension is None:
            extension = self._extension_from_url(image_url) or "png"
        file_path = generated_dir / f"{generation_id}.{extension}"
        file_path.write_bytes(content)
        return f"assets/generated/{file_path.name}"

    def _extension_from_url(self, image_url: str) -> Optional[str]:
        suffix = Path(urlparse(image_url).path).suffix.lower().lstrip(".")
        if suffix in {"png", "jpg", "jpeg", "webp"}:
            return "jpg" if suffix == "jpeg" else suffix
        return None

    def _compact_error(self, value: str) -> str:
        text = re.sub(r"\s+", " ", str(value or "")).strip()
        return text[:260] or "未知错误"

    def _provider_label(self, provider: str) -> str:
        return {
            "flux": "FLUX",
            "stable-diffusion": "Stable Diffusion",
            "stability": "Stable Diffusion",
            "midjourney": "Midjourney",
            "openai": "OpenAI",
            "openai-compatible": "OpenAI",
            "google-imagen": "Google Imagen",
            "fal": "fal.ai",
            "wanx": "通义万象",
            "zhipu": "智谱 AI",
            "volcengine": "火山引擎",
            "kling": "可灵 AI",
            "wenxin": "文心一格",
            "custom": "自定义 API",
        }.get(provider, provider or "自定义 API")

    def _image_model_label(self, image_model: str) -> str:
        return {
            "flux-2-max": "FLUX · FLUX.2 Max",
            "stable-image-ultra": "Stable Diffusion · Stable Image Ultra",
            "midjourney-v8.1": "Midjourney · V8.1",
            "gpt-image-1.5": "OpenAI · GPT-Image-1.5",
            "gemini-3.1-flash-image": "Google Imagen · Nano Banana 2",
            "fal-ai/flux-pro/v1.1-ultra": "fal.ai · FLUX 1.1 Pro Ultra",
            "fal-ai/flux/ultra": "fal.ai · FLUX 1.1 Pro Ultra",
            "fal-ai/flux-pro/kontext": "fal.ai · FLUX.1 Kontext Pro",
            "fal-ai/flux-pro/kontext/max": "fal.ai · FLUX.1 Kontext Max",
            "fal-ai/flux-pro/v1/fill": "fal.ai · FLUX.1 Pro Fill",
            "fal-ai/flux-pro/v1/erase": "fal.ai · FLUX.1 Pro Erase",
            "wan2.6-image": "通义万象 · Wan2.6 Image",
            "glm-image": "智谱 AI · GLM-Image",
            "doubao-seedream-5-0-260128": "火山引擎 · Seedream 5.0",
            "kling-v3": "可灵 AI · Kling v3",
            "kling/kling-v3-omni-image-generation": "可灵 AI · Kling v3",
            "wenxin-yige-sft": "文心一格 · 精调模型",
            "persona-local-preview": "本地演示模型",
        }.get(image_model, image_model or "本地演示模型")

    def _normalize_pose_control(self, value: Any, mode: str = "文生图") -> Dict[str, Any]:
        raw_pose = value.get("pose") if isinstance(value, dict) else value
        pose = str(raw_pose or "auto").strip() or "auto"
        allowed = {"auto", "front", "three-quarter", "side", "reference_pose"}
        if pose not in allowed:
            pose = "auto"
        if pose == "auto" and mode == "图生图":
            pose = "reference_pose"
            source = "mode"
        else:
            source = "auto" if pose == "auto" else "user"
        weight = value.get("weight") if isinstance(value, dict) else None
        try:
            weight_value = round(max(0.0, min(1.0, float(0.4 if weight is None else weight))), 2)
        except (TypeError, ValueError):
            weight_value = 0.4
        return {
            "pose": pose,
            "label": self._pose_label(pose),
            "source": source,
            "enabled": pose != "auto",
            "weight": weight_value,
        }

    def _pose_for_generation(self, mode: str, index: int, pose_control: Optional[Dict[str, Any]] = None) -> str:
        if pose_control and pose_control.get("enabled"):
            return str(pose_control.get("pose") or "front")
        if mode == "图生图":
            return "reference_pose"
        if mode == "局部重绘":
            return "front"
        return ["three-quarter", "front", "side", "three-quarter"][index % 4]

    def _backfill_generation_quality(self) -> bool:
        changed = False
        for index, generation in enumerate(self.generations):
            quality = generation.get("quality") if isinstance(generation.get("quality"), dict) else {}
            similarity = quality.get("identity_similarity") if isinstance(quality.get("identity_similarity"), dict) else {}
            if (
                quality
                and quality.get("score_kind")
                and similarity
                and similarity.get("method") != "opencv_haar_frontal_face"
                and not self._quality_needs_identity_review_backfill(generation, quality)
            ):
                continue
            character = self.manager.get_character(generation.get("character_id"))
            if character is None:
                continue
            packet = {
                "weights": {
                    "identity": float(generation.get("identity_weight", 0.8)),
                    "style": float(generation.get("style_weight", 0.6)),
                },
                "drift_risk": generation.get("drift_risk") or "low",
            }
            generation["quality"] = self._quality_report(
                packet=packet,
                character=character,
                prompt=str(generation.get("prompt") or ""),
                negative_prompt=str(generation.get("negative_prompt") or ""),
                mode=str(generation.get("mode") or "文生图"),
                image=str(generation.get("image") or "assets/persona-ref-1.png"),
                index=index % 4,
                subject_hint=str(generation.get("subject_hint") or self._prompt_subject(str(generation.get("prompt") or ""))),
            )
            changed = True
        return changed

    def _backfill_generation_model_route(self) -> bool:
        changed = False
        for generation in self.generations:
            if generation.get("model_route"):
                continue
            generation["model_route"] = self._local_model_route()
            changed = True
        return changed

    def _backfill_non_character_generation_metadata(self) -> bool:
        changed = False
        for index, generation in enumerate(self.generations):
            prompt = str(generation.get("prompt") or "")
            subject_hint = self._prompt_subject(prompt)
            if generation.get("subject_hint") != subject_hint:
                generation["subject_hint"] = subject_hint
                changed = True
            if self._subject_uses_character_identity(subject_hint):
                continue
            mode = str(generation.get("mode") or "文生图")
            reference_guidance = self._normalize_reference_guidance(generation.get("reference_guidance"))
            effective_reference_guidance = self._effective_reference_guidance(
                reference_guidance,
                subject_hint=subject_hint,
                mode=mode,
            )
            if generation.get("reference_guidance") != effective_reference_guidance:
                generation["reference_guidance"] = effective_reference_guidance
                changed = True
            for key in ("lora_id", "lora_name", "lora_weight"):
                if generation.get(key) is not None:
                    generation[key] = None
                    changed = True
            if generation.get("drift_risk") != "not_applicable":
                generation["drift_risk"] = "not_applicable"
                changed = True
            quality = generation.get("quality") if isinstance(generation.get("quality"), dict) else {}
            if (
                quality.get("checked_by") != "deterministic-local-subject-gate"
                or not quality.get("score_kind")
                or not quality.get("identity_similarity")
            ):
                character = self.manager.get_character(generation.get("character_id"))
                if character is None:
                    continue
                packet = {
                    "weights": {
                        "identity": float(generation.get("identity_weight", 0.8)),
                        "style": float(generation.get("style_weight", 0.6)),
                    },
                    "drift_risk": generation.get("drift_risk") or "not_applicable",
                }
                generation["quality"] = self._quality_report(
                    packet=packet,
                    character=character,
                    prompt=prompt,
                    negative_prompt=str(generation.get("negative_prompt") or ""),
                    mode=mode,
                    image=str(generation.get("image") or "assets/persona-ref-1.png"),
                    index=index % 4,
                    subject_hint=subject_hint,
                )
                changed = True
        return changed

    def _backfill_generation_conditioning_manifest(self) -> bool:
        changed = False
        for generation in self.generations:
            manifest = generation.get("conditioning_manifest")
            subject_hint = str(generation.get("subject_hint") or self._prompt_subject(str(generation.get("prompt") or "")))
            mode = str(generation.get("mode") or "文生图")
            reference_guidance = self._effective_reference_guidance(
                self._normalize_reference_guidance(generation.get("reference_guidance")),
                subject_hint=subject_hint,
                mode=mode,
            )
            expected_identity_edit_mode = (
                self._subject_uses_character_identity(subject_hint)
                and self._reference_guidance_has_kind(reference_guidance, "face")
                and self._is_identity_preserving_edit(str(generation.get("prompt") or ""))
            )
            if (
                isinstance(manifest, dict)
                and manifest.get("schema_version") == 1
                and manifest.get("prompt_hash")
                and isinstance(manifest.get("identity"), dict)
                and manifest.get("subject_hint") == subject_hint
                and manifest.get("references") == reference_guidance
                and manifest.get("identity_edit_mode") == expected_identity_edit_mode
                and (
                    self._subject_uses_character_identity(subject_hint)
                    or (
                        manifest.get("uses_identity_lock") is False
                        and not (manifest.get("style") or {}).get("lora_id")
                        and not (manifest.get("memory") or {}).get("best_angle")
                    )
                )
            ):
                continue
            character_id = str(generation.get("character_id") or "")
            character = self.manager.get_character(character_id)
            if character is None:
                continue
            try:
                packet = self.manager.build_conditioning(
                    character_id,
                    prompt=str(generation.get("prompt") or ""),
                    state=str(generation.get("state") or "calm"),
                    identity_weight=float(generation.get("identity_weight", 0.8)),
                    style_weight=float(generation.get("style_weight", 0.6)),
                    lora_id=str(generation.get("lora_id") or "").strip() or None,
                    lora_weight=(
                        float(generation.get("lora_weight"))
                        if generation.get("lora_weight") is not None
                        else None
                    ),
                    enforce_identity_priority=self._subject_uses_character_identity(subject_hint),
                )
            except (KeyError, ValueError, TypeError):
                continue
            generation["conditioning_manifest"] = self._conditioning_manifest(
                character=character,
                packet=packet,
                prompt=str(generation.get("prompt") or ""),
                negative_prompt=str(generation.get("negative_prompt") or ""),
                state=str(generation.get("state") or "calm"),
                mode=mode,
                reference_guidance=reference_guidance,
                subject_hint=subject_hint,
            )
            changed = True
        return changed

    def _backfill_current_version_snapshots(self) -> bool:
        changed = False
        for character_id in list(self.manager.characters):
            changed = self.manager.backfill_current_version_snapshot(character_id) or changed
        return changed

    def _backfill_character_reference_assets(self) -> bool:
        changed = False
        for character_id, character in self.manager.characters.items():
            references = self._character_reference_assets(character_id, character)
            if character.get("reference_assets") != references:
                character["reference_assets"] = references
                changed = True
            reference_collections = self._character_reference_collections(character_id, character)
            if character.get("reference_collections") != reference_collections:
                character["reference_collections"] = reference_collections
                changed = True
        return changed

    def _set_generation_favorite(self, generation_id: str, favorite):
        for generation in self.generations:
            if generation["id"] == generation_id:
                generation["favorite"] = bool(favorite) if favorite is not None else not generation.get("favorite", False)
                return generation
        raise KeyError(f"Unknown generation: {generation_id}")

    def _get_generation(self, generation_id: str) -> Dict[str, Any]:
        for generation in self.generations:
            if generation.get("id") == generation_id:
                return generation
        raise KeyError(f"Unknown generation: {generation_id}")

    def _edit_generation(self, generation_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        source = self._get_generation(generation_id)
        instruction = str(body.get("instruction") or "").strip()
        if not instruction:
            raise ValueError("instruction is required")
        mask = self._normalize_canvas_edit_mask(body.get("mask"))
        created_at = self._timestamp()
        edit_request = {
            "source_generation_id": source["id"],
            "source_image": source.get("image"),
            "instruction": instruction,
            "mask": mask,
            "created_at": created_at,
            "status": "completed",
        }
        default_model, default_model_label = self._default_canvas_edit_model(instruction)
        prompt = str(body.get("prompt") or source.get("prompt") or "").strip()
        edit_prompt = f"{prompt}。局部修改：{instruction}。只修改画布标记区域，未标记区域保持原图人物身份、构图、光线和背景连续。"
        reference_guidance = [
            {
                "kind": "edit_source",
                "label": "画布原图",
                "items": [
                    {
                        "id": source["id"],
                        "label": "原图",
                        "image": source.get("image"),
                        "mask": mask,
                        "source_generation_id": source["id"],
                        "prompt": "参考原图，保留未标记区域，只重绘画布 mask 覆盖位置。",
                    }
                ],
            }
        ]
        records, job = self._create_generations_with_job(
            {
                "character_id": source.get("character_id"),
                "mode": "局部重绘",
                "prompt": edit_prompt,
                "negative_prompt": str(body.get("negative_prompt") or source.get("negative_prompt") or ""),
                "state": str(body.get("state") or source.get("state") or "calm"),
                "identity_weight": float(body.get("identity_weight", source.get("identity_weight", 0.85))),
                "style_weight": float(body.get("style_weight", source.get("style_weight", 0.55))),
                "lora_id": str(body.get("lora_id") or source.get("lora_id") or "").strip(),
                "lora_weight": body.get("lora_weight", source.get("lora_weight")),
                "size": str(body.get("size") or source.get("size") or "3:4"),
                "image_model": str(body.get("image_model") or default_model).strip(),
                "image_model_label": str(body.get("image_model_label") or default_model_label).strip(),
                "reference_guidance": reference_guidance,
                "pose_control": source.get("pose_control"),
                "parent_generation_id": source["id"],
                "edit_request": edit_request,
                "count": 1,
            }
        )
        for record in records:
            record["parent_generation_id"] = source["id"]
            record["edit_request"] = dict(edit_request)
        job["parent_generation_id"] = source["id"]
        job["edit_request"] = dict(edit_request)
        if isinstance(job.get("request"), dict):
            job["request"]["parent_generation_id"] = source["id"]
            job["request"]["edit_request"] = dict(edit_request)
        return {
            "source": source,
            "generation": records[0],
            "generations": records,
            "job": job,
            "edit_request": edit_request,
            "account": self._normalize_account(self.account),
        }

    def _normalize_canvas_edit_mask(self, mask: Any) -> Dict[str, Any]:
        if not isinstance(mask, dict):
            raise ValueError("mask is required")
        raw_strokes = mask.get("strokes")
        if not isinstance(raw_strokes, list) or not raw_strokes:
            raise ValueError("mask must include at least one stroke")
        strokes = []
        all_points = []
        for raw_stroke in raw_strokes[:100]:
            if not isinstance(raw_stroke, dict):
                continue
            raw_points = raw_stroke.get("points")
            if not isinstance(raw_points, list):
                continue
            points = []
            for raw_point in raw_points[:80]:
                if not isinstance(raw_point, dict):
                    continue
                x = self._clamp_unit(raw_point.get("x"))
                y = self._clamp_unit(raw_point.get("y"))
                point = {"x": x, "y": y}
                points.append(point)
                all_points.append(point)
            if points:
                strokes.append({"brush": self._clamp_unit(raw_stroke.get("brush"), default=0.035), "points": points})
        if not strokes or not all_points:
            raise ValueError("mask must include drawable points")
        bounds = {
            "x": min(point["x"] for point in all_points),
            "y": min(point["y"] for point in all_points),
            "width": max(point["x"] for point in all_points) - min(point["x"] for point in all_points),
            "height": max(point["y"] for point in all_points) - min(point["y"] for point in all_points),
        }
        return {
            "version": 1,
            "canvas_width": int(mask.get("canvas_width") or 0),
            "canvas_height": int(mask.get("canvas_height") or 0),
            "bounds": {key: round(value, 4) for key, value in bounds.items()},
            "strokes": strokes,
        }

    def _clamp_unit(self, value: Any, default: float = 0.0) -> float:
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = default
        return round(max(0.0, min(1.0, number)), 4)

    def _delete_generation(self, generation_id: str) -> Dict[str, Any]:
        for index, generation in enumerate(self.generations):
            if generation.get("id") != generation_id:
                continue
            deleted = dict(generation)
            del self.generations[index]
            removed_memory = self._delete_generation_memory(generation_id)
            touched_job_ids = self._unlink_generation_from_jobs(generation_id)
            self._mark_generation_revisions_source_deleted(generation_id)
            image_removed = self._delete_generated_image_if_unreferenced(deleted.get("image"))
            return {
                "id": generation_id,
                "character_id": deleted.get("character_id"),
                "image": deleted.get("image"),
                "memory_entries_removed": removed_memory,
                "job_ids": touched_job_ids,
                "image_removed": image_removed,
            }
        raise KeyError(f"Unknown generation: {generation_id}")

    def _delete_generation_memory(self, generation_id: str) -> int:
        removed = 0
        retained_logs = []
        touched_characters = set()
        for entry in self.manager.memory_store.logs:
            metadata = entry.get("metadata") if isinstance(entry.get("metadata"), dict) else {}
            if metadata.get("generation_id") == generation_id or entry.get("id") == f"memory-{generation_id}":
                removed += 1
                if entry.get("character_id"):
                    touched_characters.add(entry.get("character_id"))
                continue
            retained_logs.append(entry)
        if removed:
            self.manager.memory_store.logs = retained_logs
            for character_id in touched_characters:
                if character_id in self.manager.characters:
                    self.manager.characters[character_id]["memory"] = self.manager.memory_store.character_preferences(character_id)
        return removed

    def _unlink_generation_from_jobs(self, generation_id: str) -> list[str]:
        touched = []
        for job in self.generation_jobs:
            ids = list(job.get("generation_ids") or [])
            if generation_id not in ids:
                continue
            remaining = [item for item in ids if item != generation_id]
            job["generation_ids"] = remaining
            job["result_count"] = len(remaining)
            job["deleted_generation_ids"] = sorted(set([*(job.get("deleted_generation_ids") or []), generation_id]))
            touched.append(str(job.get("id") or ""))
        return [job_id for job_id in touched if job_id]

    def _generation_referenced_images(self, generation: Dict[str, Any]) -> set[str]:
        images: set[str] = set()
        primary = str(generation.get("image") or "").strip().removeprefix("./")
        if primary:
            images.add(primary)
        edit_request = generation.get("edit_request")
        if isinstance(edit_request, dict):
            source_image = str(edit_request.get("source_image") or "").strip().removeprefix("./")
            if source_image:
                images.add(source_image)
        for group in generation.get("reference_guidance") or []:
            if not isinstance(group, dict):
                continue
            for item in group.get("items") or []:
                if not isinstance(item, dict):
                    continue
                ref_image = str(item.get("image") or "").strip().removeprefix("./")
                if ref_image:
                    images.add(ref_image)
        quality = generation.get("quality")
        if isinstance(quality, dict):
            quality_image = str(quality.get("image") or "").strip().removeprefix("./")
            if quality_image:
                images.add(quality_image)
        return images

    def _mark_generation_revisions_source_deleted(self, generation_id: str) -> None:
        for generation in self.generations:
            if generation.get("parent_generation_id") != generation_id:
                continue
            edit_request = generation.get("edit_request")
            if not isinstance(edit_request, dict):
                edit_request = {}
                generation["edit_request"] = edit_request
            edit_request["source_generation_status"] = "deleted"
            for group in generation.get("reference_guidance") or []:
                if not isinstance(group, dict):
                    continue
                for item in group.get("items") or []:
                    if not isinstance(item, dict):
                        continue
                    if item.get("source_generation_id") == generation_id:
                        item["source_generation_status"] = "deleted"

    def _delete_generated_image_if_unreferenced(self, image_path: Any) -> bool:
        image = str(image_path or "").strip().removeprefix("./")
        if not image.startswith("assets/generated/"):
            return False
        if any(image in self._generation_referenced_images(generation) for generation in self.generations):
            return False
        file_path = (self.static_dir / image).resolve()
        generated_dir = (self.static_dir / "assets" / "generated").resolve()
        if not (generated_dir == file_path.parent or generated_dir in file_path.parents):
            return False
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
            return True
        return False

    def _update_character(self, character_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        if character_id not in self.manager.characters:
            raise KeyError(f"Unknown character: {character_id}")

        style_config = None
        if "style" in body:
            style_config = body.get("style") or {}
            if isinstance(style_config, dict):
                style_config = {
                    "preset": style_config.get("preset") or "cinematic",
                    "prompt": style_config.get("prompt") or style_config.get("preset") or "cinematic portrait",
                    "lora_id": style_config.get("lora_id"),
                    "lora_weight": style_config.get("lora_weight"),
                }

        self.manager.update_character(
            character_id,
            name=body.get("name") if "name" in body else None,
            prompt=body.get("prompt") if "prompt" in body else None,
            style_config=style_config,
            tags=self._normalize_character_tags(body.get("tags")) if "tags" in body else None,
        )
        live_character = self.manager.characters[character_id]
        now = self._timestamp()
        live_character.setdefault("created_at", now)
        live_character["updated_at"] = now
        return self._serialize_character(character_id, include_detail=True)

    def _update_character_references(self, character_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        if character_id not in self.manager.characters:
            raise KeyError(f"Unknown character: {character_id}")
        references = self._normalize_character_references(body.get("references"))
        if not references:
            raise ValueError("references are required")
        self.manager.update_reference_assets(character_id, references)

        version = None
        training_status = "stored"
        train_requested = bool(body.get("train"))
        face_images = self._resolve_face_images([
            reference.get("image") or reference.get("source")
            for reference in references
            if reference.get("image") or reference.get("source")
        ])
        if train_requested and len(face_images) >= 3:
            character = self.manager.get_character(character_id)
            style = character.get("style") if character else None
            lora = (style or {}).get("lora") or {}
            version = self.manager.create_version(
                character_id,
                identity_config={"face_images": face_images[:20]},
                style_config={
                    "preset": (style or {}).get("preset") or "cinematic",
                    "prompt": " ".join((style or {}).get("tokens") or []) or (style or {}).get("preset") or "cinematic portrait",
                    "lora_id": lora.get("id"),
                    "lora_weight": lora.get("weight"),
                },
                note=str(body.get("note") or "reference asset sync"),
            )
            self.manager.update_reference_assets(character_id, references)
            training_status = "trained"
        elif train_requested:
            training_status = "needs_three_references"

        live_character = self.manager.characters[character_id]
        now = self._timestamp()
        live_character.setdefault("created_at", now)
        live_character["updated_at"] = now
        return {
            "character": self._serialize_character(character_id, include_detail=True),
            "version": version,
            "training_status": training_status,
            "reference_count": len(references),
        }

    def _update_character_reference_collections(self, character_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        if character_id not in self.manager.characters:
            raise KeyError(f"Unknown character: {character_id}")

        live_character = self.manager.characters[character_id]
        current = self._character_reference_collections(character_id, live_character)
        now = self._timestamp()

        if isinstance(body.get("collections"), dict):
            for kind, references in body["collections"].items():
                normalized_kind = self._normalize_reference_collection_kind(kind)
                current[normalized_kind] = self._normalize_reference_collection(
                    normalized_kind,
                    references,
                    created_at_default=now,
                )
        else:
            kind = self._normalize_reference_collection_kind(body.get("kind"))
            if "references" not in body:
                raise ValueError("references are required")
            current[kind] = self._normalize_reference_collection(
                kind,
                body.get("references"),
                created_at_default=now,
            )

        live_character["reference_collections"] = current
        live_character.setdefault("created_at", now)
        live_character["updated_at"] = now
        return {
            "character": self._serialize_character(character_id, include_detail=True),
            "collection_count": sum(len(items) for items in current.values()),
        }

    def _delete_character(self, character_id: str) -> Dict[str, Any]:
        if character_id not in self.manager.characters:
            raise KeyError(f"Unknown character: {character_id}")
        if len(self.manager.characters) <= 1:
            raise ValueError("cannot delete the last character")

        character = self.manager.characters.pop(character_id)
        self.manager.memory_store.logs = [
            entry for entry in self.manager.memory_store.logs if entry.get("character_id") != character_id
        ]
        removed_generations = [
            generation for generation in self.generations if generation.get("character_id") == character_id
        ]
        self.generations = [
            generation for generation in self.generations if generation.get("character_id") != character_id
        ]
        # Keep generation jobs consistent with single-generation deletion
        # (_delete_generation): unlink removed ids so jobs no longer report
        # dangling generation_ids / stale result_count, then drop generated
        # image files that are no longer referenced by any surviving record.
        for generation in removed_generations:
            generation_id = str(generation.get("id") or "")
            if generation_id:
                self._unlink_generation_from_jobs(generation_id)
            self._delete_generated_image_if_unreferenced(generation.get("image"))
        for project in self.projects:
            project["character_ids"] = [
                item for item in project.get("character_ids", []) if item != character_id
            ]
            project["updated_at"] = self._timestamp()
        return {"id": character_id, "name": character.get("name")}

    def _normalize_character_tags(self, tags: Any) -> list[str]:
        if tags is None:
            return []
        if isinstance(tags, str):
            raw_tags = re.split(r"[,，、\s]+", tags)
        else:
            raw_tags = tags
        normalized = []
        for tag in raw_tags or []:
            clean = str(tag).strip()
            if clean and clean not in normalized:
                normalized.append(clean[:24])
        return normalized[:12]

    def _normalize_character_references(self, references: Any) -> list[Dict[str, Any]]:
        normalized = []
        labels = ["主图", "侧脸", "回眸", "微笑"]
        for index, reference in enumerate(references or []):
            if not isinstance(reference, dict):
                continue
            image = str(reference.get("image") or reference.get("path") or reference.get("source") or "").strip()
            if image.startswith("./"):
                image = image[2:]
            if image and not image.startswith(("assets/", "data:image/")):
                continue
            reference_id = str(reference.get("id") or f"face-{index + 1}").strip()
            reference_id = re.sub(r"[^a-zA-Z0-9_.:-]+", "-", reference_id).strip("-") or f"face-{index + 1}"
            item = {
                "id": reference_id[:64],
                "label": str(reference.get("label") or (labels[index] if index < len(labels) else f"参考 {index + 1}")).strip()[:24],
                "image": image,
                "source": str(reference.get("source") or image).strip(),
                "prompt": str(reference.get("prompt") or "保持同一角色身份").strip()[:160],
                "active": bool(reference.get("active", index == 0)),
                "created_at": str(reference.get("created_at") or self._timestamp()),
            }
            if reference.get("updated_at"):
                item["updated_at"] = str(reference.get("updated_at"))
            normalized.append(item)
            if len(normalized) >= 20:
                break
        if normalized and not any(reference.get("active") for reference in normalized):
            normalized[0]["active"] = True
        return normalized

    def _normalize_reference_collection_kind(self, kind: Any) -> str:
        normalized = str(kind or "").strip()
        if normalized not in self._reference_collection_kinds():
            raise ValueError(f"Unsupported reference collection kind: {normalized or 'empty'}")
        return normalized

    def _normalize_reference_collection(
        self,
        kind: str,
        references: Any,
        created_at_default: Optional[str] = None,
    ) -> list[Dict[str, Any]]:
        normalized = []
        created_at_default = created_at_default or "2026-06-17T00:00:00Z"
        for index, reference in enumerate(references or []):
            if not isinstance(reference, dict):
                continue
            image = str(reference.get("image") or reference.get("path") or reference.get("source") or "").strip()
            if image.startswith("./"):
                image = image[2:]
            if image and not image.startswith(("assets/", "data:image/")):
                continue
            visual = str(reference.get("visual") or "").strip()
            visual = re.sub(r"[^a-zA-Z0-9_.:-]+", "-", visual).strip("-")[:48]
            if not image and not visual:
                continue
            reference_id = str(reference.get("id") or f"{kind}-{index + 1}").strip()
            reference_id = re.sub(r"[^a-zA-Z0-9_.:-]+", "-", reference_id).strip("-") or f"{kind}-{index + 1}"
            item = {
                "id": reference_id[:64],
                "label": str(reference.get("label") or f"参考 {index + 1}").strip()[:24],
                "prompt": str(reference.get("prompt") or "").strip()[:180],
                "active": bool(reference.get("active", False)),
                "created_at": str(reference.get("created_at") or created_at_default),
            }
            if image:
                item["image"] = image
                item["source"] = str(reference.get("source") or image).strip()
            if visual:
                item["visual"] = visual
            alt = str(reference.get("alt") or "").strip()
            if alt:
                item["alt"] = alt[:80]
            if reference.get("updated_at"):
                item["updated_at"] = str(reference.get("updated_at"))
            normalized.append(item)
            if len(normalized) >= 20:
                break
        return normalized

    def _save_reference_asset(self, body: Dict[str, Any]) -> Dict[str, Any]:
        data_url = str(body.get("data_url") or "")
        if not data_url.startswith("data:image/") or "," not in data_url:
            raise ValueError("data_url must be an image data URL")

        header, encoded = data_url.split(",", 1)
        media_type = header.split(";", 1)[0].removeprefix("data:")
        extension = {
            "image/jpeg": "jpg",
            "image/jpg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
            "image/gif": "gif",
        }.get(media_type)
        if extension is None:
            raise ValueError("unsupported image type")

        try:
            content = base64.b64decode(encoded, validate=True)
        except ValueError as error:
            raise ValueError("invalid image data") from error
        if not content:
            raise ValueError("image data is empty")
        if len(content) > 5 * 1024 * 1024:
            raise ValueError("image is larger than 5MB")

        upload_dir = self.static_dir / "assets" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        base_asset_id = f"reference-{self._timestamp().replace(':', '').replace('-', '').replace('T', '-').removesuffix('Z')}"
        asset_id = base_asset_id
        file_path = upload_dir / f"{asset_id}.{extension}"
        suffix = 2
        while file_path.exists():
            asset_id = f"{base_asset_id}-{suffix}"
            file_path = upload_dir / f"{asset_id}.{extension}"
            suffix += 1
        file_path.write_bytes(content)
        return {
            "id": asset_id,
            "name": str(body.get("name") or file_path.name),
            "path": f"assets/uploads/{file_path.name}",
            "content_type": media_type,
            "size": len(content),
            "created_at": self._timestamp(),
        }

    def _max_generation_index(self) -> int:
        max_index = 0
        for generation in self.generations:
            generation_id = str(generation.get("id") or "")
            if not generation_id.startswith("gen-"):
                continue
            try:
                max_index = max(max_index, int(generation_id[4:]))
            except ValueError:
                continue
        return max_index

    def _next_generation_id(self, offset: int = 0) -> str:
        # Derive from the highest existing suffix, not len(): deleting a
        # character removes its generations, so a count-based id would collide
        # with surviving higher-numbered records.
        return f"gen-{self._max_generation_index() + offset + 1:06d}"

    def _timestamp(self) -> str:
        return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    def _demo_generations(self):
        return [
            {
                "id": f"gen-{index:06d}",
                "character_id": "lina",
                "character_name": "Lina",
                "character_version": 1,
                "prompt": "coffee shop morning",
                "mode": "文生图",
                "state": "calm",
                "size": "3:4",
                "image": "assets/lina-morning.svg",
                "favorite": index == 1,
                "variant": index,
                "drift_risk": "low",
                "identity_weight": 0.8,
                "style_weight": 0.6,
                "lora_id": "portrait-consistency",
                "lora_name": "人像一致性",
                "lora_weight": 0.72,
                "model_route": self._local_model_route("persona-local-preview", "本地演示模型"),
                "conditioning_preview": [],
                "quality": {
                    "face_match_score": 0.92,
                    "threshold": 0.82,
                    "match": True,
                    "status": "pass",
                    "identity_margin": 0.2,
                    "review_note": "身份权重高于风格，生成结果通过本地一致性质检。",
                    "checked_by": "deterministic-local-quality-gate",
                    "image": "assets/lina-morning.svg",
                },
                "created_at": f"2026-06-17T00:00:0{index}Z",
            }
            for index in range(1, 5)
        ]

    def _demo_projects(self):
        return [
            self._project_record(
                project_id="light-portrait-playground",
                name="轻写真试玩",
                user_segment="普通用户",
                level="Level 1 Image Tool",
                character_ids=["lina"],
                goal="上传参考脸并快速生成一组写真",
                channels=["头像", "朋友圈"],
                deliverables=["1:1 头像", "3:4 写真", "收藏精选"],
                status="draft",
            ),
            self._project_record(
                project_id="creator-character-series",
                name="创作者角色系列",
                user_segment="创作者",
                level="Level 3 Character OS",
                character_ids=["lina", "kira"],
                goal="围绕同一角色持续产出小红书 / 抖音系列图",
                channels=["小红书", "抖音", "短剧分镜"],
                deliverables=["角色版本", "系列封面", "场景记忆", "风格预设"],
                status="active",
            ),
            self._project_record(
                project_id="brand-virtual-ip",
                name="品牌虚拟模特 IP",
                user_segment="商业用户",
                level="Level 4 Visual IP System",
                character_ids=["alex"],
                goal="沉淀长期可复用的品牌广告模特资产",
                channels=["广告投放", "电商主图", "品牌海报"],
                deliverables=["IP 资产包", "商业授权摘要", "品牌 LoRA", "版本审阅记录"],
                status="in_review",
            ),
        ]

    def _export_project(self):
        characters = [self._serialize_character(character_id, include_detail=True) for character_id in self.manager.characters]
        favorites = [generation for generation in self.generations if generation.get("favorite")]
        projects = [self._serialize_project(project, include_package=True) for project in self.projects]
        return {
            "schema_version": 1,
            "name": "Persona Studio Character OS",
            "loras": StyleModel.available_loras(),
            "projects": projects,
            "ip_packages": [self._project_ip_package(project) for project in self.projects],
            "characters": characters,
            "generations": self.generations,
            "generation_jobs": self.generation_jobs,
            "account": self._normalize_account(self.account),
            "favorites": favorites,
            "counts": {
                "projects": len(projects),
                "characters": len(characters),
                "generations": len(self.generations),
                "generation_jobs": len(self.generation_jobs),
                "favorites": len(favorites),
                "memory_logs": len(self.manager.memory_store.logs),
                "loras": len(StyleModel.available_loras()),
            },
        }

    def _provider_status_response(self) -> Dict[str, Any]:
        api_settings = self.settings.get("api") or {}
        profiles = api_settings.get("profiles") if isinstance(api_settings.get("profiles"), dict) else {}
        provider_ids = ["fal", "flux", "volcengine", "wanx", "kling"]
        active_provider = str(api_settings.get("provider") or "").strip()
        if active_provider and active_provider not in provider_ids:
            provider_ids.append(active_provider)
        for provider_id in profiles:
            if provider_id not in provider_ids:
                provider_ids.append(provider_id)

        providers = [self._provider_status(provider_id) for provider_id in provider_ids]
        return {
            "generated_at": self._timestamp(),
            "active_provider": active_provider,
            "summary": {
                "total": len(providers),
                "configured": sum(1 for provider in providers if provider["local_status"] == "ready"),
                "passed": sum(1 for provider in providers if provider["remote_status"] == "passed"),
                "failed": sum(1 for provider in providers if provider["remote_status"] == "failed"),
                "untested": sum(1 for provider in providers if provider["remote_status"] == "untested"),
            },
            "providers": providers,
        }

    def _provider_status(self, provider_id: str) -> Dict[str, Any]:
        profile = self._api_profile_for_provider(provider_id)
        provider = str(profile.get("provider") or provider_id).strip() or provider_id
        missing = self._profile_missing_requirements(provider, profile)
        local_status = "ready" if not missing else "incomplete"
        last_success = self._last_provider_success(provider)
        last_failure = self._last_provider_failure(provider)
        success_time = str((last_success or {}).get("created_at") or "")
        failure_time = str((last_failure or {}).get("completed_at") or (last_failure or {}).get("requested_at") or "")
        if last_failure and (not last_success or failure_time >= success_time):
            remote_status = "failed"
            remote_label = "远端失败"
            note = str(last_failure.get("error") or "真实生成失败")
        elif last_success:
            remote_status = "passed"
            remote_label = "真实生成通过"
            note = f"最近成功：{last_success.get('id')} · {last_success.get('size')}"
        elif local_status == "ready":
            remote_status = "untested"
            remote_label = "未实测"
            note = "本地配置完整，但还没有真实生成成功记录。"
        else:
            remote_status = "not_configured"
            remote_label = "未配置"
            note = f"缺少：{'、'.join(missing)}" if missing else "未启用"
        return {
            "provider": provider,
            "label": self._provider_label(provider),
            "model": profile.get("model") or "",
            "base_url": profile.get("base_url") or "",
            "enabled": bool(profile.get("enabled")),
            "auth_configured": self._external_api_auth_is_set(provider, profile),
            "credential_masked": self._provider_credential_mask(provider, profile),
            "missing": missing,
            "local_status": local_status,
            "remote_status": remote_status,
            "remote_label": remote_label,
            "note": self._compact_error(note),
            "last_success": self._provider_success_summary(last_success),
            "last_failure": self._provider_failure_summary(last_failure),
        }

    def _profile_missing_requirements(self, provider: str, profile: Dict[str, Any]) -> list[str]:
        missing = []
        if not profile.get("enabled"):
            missing.append("启用")
        if not str(profile.get("model") or "").strip():
            missing.append("模型")
        if not self._external_api_auth_is_set(provider, profile):
            missing.append("API Key 或 AK/SK" if provider == "kling" else "API Key")
        return missing

    def _provider_credential_mask(self, provider: str, profile: Dict[str, Any]) -> str:
        if provider == "kling" and self._access_key_is_set(profile) and self._secret_key_is_set(profile):
            return self._mask_api_key(profile.get("access_key") or "")
        return self._mask_api_key(profile.get("api_key") or profile.get("access_key") or "")

    def _last_provider_success(self, provider: str) -> Optional[Dict[str, Any]]:
        for generation in reversed(self.generations):
            route = generation.get("model_route") or {}
            if route.get("provider") == provider and route.get("real_generation") is True:
                return generation
        return None

    def _last_provider_failure(self, provider: str) -> Optional[Dict[str, Any]]:
        for job in reversed(self.generation_jobs):
            if job.get("status") != "failed":
                continue
            if self._provider_for_generation_job(job) == provider:
                return job
        return None

    def _provider_for_generation_job(self, job: Dict[str, Any]) -> str:
        route = job.get("model_route") if isinstance(job.get("model_route"), dict) else {}
        if route.get("provider"):
            return str(route.get("provider") or "")
        error = str(job.get("error") or "")
        if "可灵" in error or "kling" in error.lower():
            return "kling"
        if "通义" in error or "dashscope" in error.lower() or "wanx" in error.lower():
            return "wanx"
        if "火山" in error or "volc" in error.lower() or "ark" in error.lower():
            return "volcengine"
        if "fal" in error.lower():
            return "fal"
        request = job.get("request") if isinstance(job.get("request"), dict) else {}
        return self._provider_for_image_model(str(request.get("image_model") or job.get("image_model") or ""))

    def _provider_success_summary(self, generation: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not generation:
            return None
        route = generation.get("model_route") or {}
        return {
            "id": generation.get("id"),
            "created_at": generation.get("created_at"),
            "image": generation.get("image"),
            "size": generation.get("size"),
            "model": route.get("model"),
            "generation_kind": route.get("generation_kind"),
        }

    def _provider_failure_summary(self, job: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not job:
            return None
        return {
            "id": job.get("id"),
            "completed_at": job.get("completed_at"),
            "image_model": job.get("image_model"),
            "size": job.get("size"),
            "error": self._compact_error(str(job.get("error") or "")),
        }

    def _system_readiness_response(self) -> Dict[str, Any]:
        library = self._asset_library_response()
        summary = library.get("summary") or {}
        characters = [self._serialize_character(character_id, include_detail=True) for character_id in self.manager.characters]
        reference_ready_characters = len([
            character
            for character in characters
            if (character.get("identity_readiness") or {}).get("status") == "ready"
        ])
        total_characters = len(characters)
        memory_logs = len(self.manager.memory_store.logs)
        projects = [self._serialize_project(project, include_package=True) for project in self.projects]
        release_ready_projects = int(summary.get("release_ready_projects") or 0)
        quality_passed = int(summary.get("quality_passed_generations") or 0)
        api_settings = (self._public_settings().get("api") or {})
        api_enabled = bool(api_settings.get("enabled"))
        api_configured = api_enabled and self._configured_external_api_auth_is_set()
        provider_health = self._provider_status_response()
        provider_health_summary = provider_health.get("summary") or {}
        provider_configured = int(provider_health_summary.get("configured") or 0)
        provider_passed = int(provider_health_summary.get("passed") or 0)
        provider_failed = int(provider_health_summary.get("failed") or 0)
        provider_untested = int(provider_health_summary.get("untested") or 0)
        identity_training = self._identity_training_status()
        trained_identity_ids = {
            str(character.get("character_id"))
            for character in identity_training.get("characters", [])
            if character.get("status") == "trained"
        }
        trained_identity_count = int(identity_training.get("trained") or 0)
        identity_ready_characters = len([
            character
            for character in characters
            if (character.get("identity_readiness") or {}).get("status") == "ready"
            or str(character.get("id")) in trained_identity_ids
        ])
        deployment = self._deployment_status()
        identity_training_ready = identity_training.get("status") == "ready"
        deployment_ready = bool(deployment.get("ready"))
        identity_model_score = (
            100
            if identity_ready_characters == total_characters and total_characters
            else 78
            if identity_ready_characters
            else 45
        )
        identity_next_step = (
            ""
            if identity_model_score >= 90
            else "补足每个角色 3 张以上高质量人脸参考，或先完成生产身份包训练"
        )
        generation_pipeline_score = 100 if self.generations else 78
        jobs_billing_score = 100 if self.asset_store and self.account else 82
        project_ip_score = 100 if release_ready_projects else 88 if projects else 70
        modules = [
            self._readiness_module(
                "identity_model",
                "Identity Model",
                identity_model_score,
                [
                    f"{identity_ready_characters}/{total_characters} 角色身份就绪",
                    f"{reference_ready_characters}/{total_characters} 角色参考可训练",
                    f"{trained_identity_count}/{total_characters} 生产身份包已训练",
                    f"{int(summary.get('reference') or 0)} 个参考资产",
                ],
                identity_next_step,
            ),
            self._readiness_module(
                "style_model",
                "Style Model",
                100 if StyleModel.available_loras() else 60,
                [
                    f"{len(StyleModel.available_loras())} 个 LoRA/风格适配器",
                    "风格向量预览和摄影/光影/色彩/镜头语言已本地化",
                ],
            ),
            self._readiness_module(
                "memory_store",
                "Memory Store",
                100 if memory_logs else 65,
                [
                    f"{memory_logs} 条场景记忆",
                    "成功角度、偏好风格、失败风格避坑已接入预检和条件包",
                ],
                "继续沉淀真实生成结果的成功/失败记忆",
            ),
            self._readiness_module(
                "fusion_engine",
                "Conditioning Fusion",
                100,
                [
                    "身份权重高于风格权重的漂移保护已启用",
                    "条件包、ControlNet 姿态、LoRA、记忆摘要已编译",
                ],
            ),
            self._readiness_module(
                "generation_pipeline",
                "Generation Pipeline",
                generation_pipeline_score,
                [
                    f"{len(self.generations)} 张生成图",
                    f"{quality_passed}/{len(self.generations)} 张通过质检" if self.generations else "暂无生成图",
                    "预检、尺寸映射、主体路由、外部 Provider 分发、删除、收藏、下载已本地闭环",
                ],
            ),
            self._readiness_module(
                "jobs_billing",
                "Jobs + Credit Ledger",
                jobs_billing_score,
                [
                    f"{len(self.generation_jobs)} 个生成任务",
                    f"{self.account.get('label')} · 剩余 {self.account.get('credits_remaining')} 点",
                    "失败记录、重试、扣费审计已持久化",
                ],
            ),
            self._readiness_module(
                "asset_library",
                "Unified Asset Library",
                100 if int(summary.get("total") or 0) else 70,
                [
                    f"{int(summary.get('total') or 0)} 个统一资产",
                    f"{int(summary.get('character') or 0)} 角色 · {int(summary.get('generation') or 0)} 图 · {int(summary.get('memory') or 0)} 记忆",
                    "搜索、类型筛选、打开角色/项目/生成图/记忆/任务已接通",
                ],
            ),
            self._readiness_module(
                "project_ip_system",
                "Project + Visual IP System",
                project_ip_score,
                [
                    f"{len(projects)} 个项目",
                    f"{release_ready_projects} 个发布就绪项目",
                    "IP 包、资产清单、审阅状态和商业交付摘要已可导出",
                ],
                "生成至少 1 个商业发布包并归档 release artifact",
            ),
            self._readiness_module(
                "workspace_ui",
                "Workspace UI",
                100,
                [
                    "首页/我的作品/资产库/项目/任务/记忆/预检/风格/版本历史已分面切换",
                    "深层工具页已隔离生成网格和参考轨，避免混排",
                ],
            ),
        ]
        completion_percent = round(sum(module["score"] for module in modules) / max(1, len(modules)))
        external_dependencies = [
            {
                "id": "real_generation_api",
                "label": "真实图像生成 API",
                "status": "configured" if api_configured else "optional",
                "provider": api_settings.get("provider") or "未配置",
                "model": api_settings.get("model") or "",
                "base_url": api_settings.get("base_url") or "",
                "note": "已配置外部生成；本地仍保留可验证预览路径。" if api_configured else "本地功能可运行；真实生产出图需要配置外部服务商。",
            },
            {
                "id": "provider_live_health",
                "label": "Provider 真实生成健康",
                "status": "review" if provider_failed else "ready" if provider_passed else "configured" if provider_configured else "optional",
                "provider": f"{provider_passed}/{provider_configured} 已通过",
                "model": f"{provider_failed} 失败 · {provider_untested} 未实测",
                "base_url": "",
                "note": "有服务商远端生成失败，请查看个人中心 API 健康。" if provider_failed else "已按真实生成记录区分远端健康和本地配置。",
            },
            {
                "id": "production_identity_training",
                "label": "生产级身份训练",
                "status": "ready" if identity_training_ready else "external_required",
                "provider": identity_training.get("provider") or "local-production-encoder",
                "model": f"{identity_training.get('trained', 0)}/{identity_training.get('total', 0)} 已训练",
                "base_url": self._workspace_data_dir().as_posix(),
                "note": "生产身份包、训练任务和 artifact 已本地闭环，可替换为 ArcFace / InsightFace / custom ViT 服务。" if identity_training_ready else "需要为全部角色生成生产身份包。",
            },
            {
                "id": "deployment_storage",
                "label": "部署与共享存储",
                "status": "production_local_ready" if deployment_ready else "local_persistent" if self.asset_store else "memory_only",
                "provider": (deployment.get("manifest") or {}).get("mode") or "local-json",
                "model": f"{len([check for check in deployment.get('checks', []) if check.get('status') == 'passed'])}/{len(deployment.get('checks', []))} 检查通过" if deployment.get("checks") else "",
                "base_url": ((deployment.get("manifest") or {}).get("database") or {}).get("path") or str(self.asset_store.path) if self.asset_store else "",
                "note": "本地生产存储、对象仓库、RBAC 和审计日志已闭环；云数据库/对象存储可按同一 manifest 替换。" if deployment_ready else "本地持久化可验证；团队/商业上线仍需初始化存储、对象仓库和权限层。",
            },
        ]
        return {
            "generated_at": self._timestamp(),
            "status": "local_complete" if completion_percent >= 100 else "local_ready" if completion_percent >= 90 else "needs_review",
            "completion_percent": completion_percent,
            "summary": f"本地 Character OS 完成度 {completion_percent}% · {len(self.generations)} 图 · {int(summary.get('total') or 0)} 资产",
            "totals": {
                "characters": total_characters,
                "ready_characters": identity_ready_characters,
                "reference_ready_characters": reference_ready_characters,
                "generations": len(self.generations),
                "quality_passed_generations": quality_passed,
                "references": int(summary.get("reference") or 0),
                "memory_logs": memory_logs,
                "projects": len(projects),
                "generation_jobs": len(self.generation_jobs),
                "asset_total": int(summary.get("total") or 0),
                "credits_remaining": int(self.account.get("credits_remaining") or 0),
                "release_ready_projects": release_ready_projects,
                "production_identity_trained": trained_identity_count,
            },
            "modules": modules,
            "external_dependencies": external_dependencies,
            "provider_health": provider_health,
            "identity_training": identity_training,
            "deployment": deployment,
            "next_steps": [
                module["next_step"]
                for module in modules
                if module.get("next_step") and module.get("status") != "ready"
            ],
        }

    def _readiness_module(
        self,
        module_id: str,
        label: str,
        score: int,
        evidence: list[str],
        next_step: str = "",
    ) -> Dict[str, Any]:
        normalized_score = max(0, min(100, int(score)))
        status = "ready" if normalized_score >= 90 else "review" if normalized_score >= 70 else "incomplete"
        return {
            "id": module_id,
            "label": label,
            "status": status,
            "score": normalized_score,
            "evidence": [str(item) for item in evidence if item],
            "next_step": next_step if status != "ready" else "",
        }

    def _asset_library_response(self) -> Dict[str, Any]:
        items = []
        type_counts = {
            "character": 0,
            "generation": 0,
            "reference": 0,
            "memory": 0,
            "project": 0,
            "job": 0,
        }

        for character_id in self.manager.characters:
            character = self._serialize_character(character_id, include_detail=True)
            summary = character.get("asset_summary") or {}
            items.append(
                self._asset_library_item(
                    item_type="character",
                    item_id=character_id,
                    title=character.get("name") or character_id,
                    subtitle=f"v{character.get('version', 1)} · 一致性 {character.get('consistency_percent', 0)}% · {summary.get('generation_count', 0)} 图",
                    character_id=character_id,
                    character_name=character.get("name"),
                    status=(character.get("identity_readiness") or {}).get("status") or "ready",
                    image=(character.get("reference_assets") or [{}])[0].get("image") if character.get("reference_assets") else "",
                    tags=[
                        *(character.get("tags") or []),
                        str((character.get("style") or {}).get("preset") or ""),
                    ],
                    metrics={
                        "versions": summary.get("version_count", 0),
                        "references": summary.get("reference_count", 0),
                        "generations": summary.get("generation_count", 0),
                        "memory": summary.get("memory_count", 0),
                    },
                    updated_at=summary.get("updated_at") or character.get("last_used_at"),
                )
            )
            type_counts["character"] += 1

            for reference in character.get("reference_assets") or []:
                items.append(
                    self._asset_library_item(
                        item_type="reference",
                        item_id=f"{character_id}:face:{reference.get('id')}",
                        title=reference.get("label") or "人脸参考",
                        subtitle=f"{character.get('name')} · 人脸参考" + (" · 主参考" if reference.get("active") else ""),
                        character_id=character_id,
                        character_name=character.get("name"),
                        status="active" if reference.get("active") else "stored",
                        image=reference.get("image"),
                        tags=["face", "identity", "active" if reference.get("active") else "reference"],
                        related_id=reference.get("id"),
                        updated_at=reference.get("updated_at") or reference.get("created_at"),
                    )
                )
                type_counts["reference"] += 1

            for kind, references in (character.get("reference_collections") or {}).items():
                for reference in references or []:
                    items.append(
                        self._asset_library_item(
                            item_type="reference",
                            item_id=f"{character_id}:{kind}:{reference.get('id')}",
                            title=reference.get("label") or f"{kind} 参考",
                            subtitle=f"{character.get('name')} · {self._reference_kind_label(kind)}" + (" · 已启用" if reference.get("active") else ""),
                            character_id=character_id,
                            character_name=character.get("name"),
                            status="active" if reference.get("active") else "stored",
                            image=reference.get("image"),
                            tags=[kind, self._reference_kind_label(kind), "active" if reference.get("active") else "reference"],
                            related_id=reference.get("id"),
                            updated_at=reference.get("updated_at") or reference.get("created_at"),
                        )
                    )
                    type_counts["reference"] += 1

            for memory in self._character_memory_entries(character_id):
                items.append(
                    self._asset_library_item(
                        item_type="memory",
                        item_id=memory.get("id"),
                        title=memory.get("prompt") or "记忆资产",
                        subtitle=f"{character.get('name')} · {memory.get('pose_label') or '未标注'} · {memory.get('score_percent', 0)}%",
                        character_id=character_id,
                        character_name=character.get("name"),
                        status=memory.get("quality_status") or "memory",
                        image=memory.get("image"),
                        tags=[memory.get("style") or "", memory.get("pose") or "", memory.get("source") or ""],
                        related_id=memory.get("generation_id"),
                        metrics={"score": memory.get("score_percent", 0)},
                        updated_at=memory.get("created_at"),
                    )
                )
                type_counts["memory"] += 1

        for generation in self.generations:
            quality = generation.get("quality") or {}
            items.append(
                self._asset_library_item(
                    item_type="generation",
                    item_id=generation.get("id"),
                    title=generation.get("prompt") or generation.get("id"),
                    subtitle=f"{generation.get('character_name') or generation.get('character_id')} · {generation.get('size')} · {self._subject_label(str(generation.get('subject_hint') or 'portrait'))}",
                    character_id=generation.get("character_id"),
                    character_name=generation.get("character_name"),
                    status=quality.get("status") or generation.get("drift_risk") or "generated",
                    image=generation.get("image"),
                    tags=[
                        generation.get("subject_hint") or "",
                        "favorite" if generation.get("favorite") else "",
                        generation.get("mode") or "",
                        (generation.get("model_route") or {}).get("provider_label") or "",
                    ],
                    related_id=generation.get("job_id"),
                    metrics={
                        "quality": quality.get("face_match_score") or quality.get("subject_match_score"),
                        "favorite": bool(generation.get("favorite")),
                    },
                    updated_at=generation.get("created_at") or generation.get("id"),
                )
            )
            type_counts["generation"] += 1

        for project in self.projects:
            serialized = self._serialize_project(project, include_package=True)
            review = serialized.get("review") or {}
            package = serialized.get("ip_package") or {}
            items.append(
                self._asset_library_item(
                    item_type="project",
                    item_id=serialized.get("id"),
                    title=serialized.get("name") or serialized.get("id"),
                    subtitle=f"{serialized.get('user_segment')} · {serialized.get('counts', {}).get('characters', 0)} 角色 · {serialized.get('counts', {}).get('generations', 0)} 图",
                    status=serialized.get("status") or review.get("status") or "active",
                    image="",
                    tags=[
                        serialized.get("user_segment") or "",
                        package.get("license_status") or "",
                        "release-ready" if package.get("release_ready") else "",
                    ],
                    related_id=package.get("project_id"),
                    metrics=package.get("asset_counts") or serialized.get("counts") or {},
                    updated_at=serialized.get("updated_at") or serialized.get("created_at"),
                )
            )
            type_counts["project"] += 1

        for job in self.generation_jobs:
            billing = job.get("billing") if isinstance(job.get("billing"), dict) else {}
            items.append(
                self._asset_library_item(
                    item_type="job",
                    item_id=job.get("id"),
                    title=job.get("prompt") or job.get("id"),
                    subtitle=f"{self._project_status_label(job.get('status'))} · {job.get('count', 0)} 张 · {job.get('size') or '未记录'}",
                    character_id=job.get("character_id"),
                    character_name=(self.manager.get_character(str(job.get("character_id") or "")) or {}).get("name"),
                    status=job.get("status") or "unknown",
                    image="",
                    tags=[job.get("mode") or "", job.get("image_model_label") or "", "retry" if job.get("retry_of") else ""],
                    related_id=(job.get("generation_ids") or [None])[0],
                    metrics={
                        "result_count": job.get("result_count", 0),
                        "cost": billing.get("cost", 0),
                    },
                    updated_at=job.get("completed_at") or job.get("requested_at"),
                )
            )
            type_counts["job"] += 1

        items = sorted(
            items,
            key=lambda item: (str(item.get("updated_at") or ""), str(item.get("id") or "")),
            reverse=True,
        )
        return {
            "summary": {
                **type_counts,
                "total": len(items),
                "favorites": len([generation for generation in self.generations if generation.get("favorite")]),
                "quality_passed_generations": len([
                    generation
                    for generation in self.generations
                    if (generation.get("quality") or {}).get("status") == "pass"
                ]),
                "release_ready_projects": len([
                    project
                    for project in self.projects
                    if self._project_ip_package(project).get("release_ready")
                ]),
            },
            "filters": {
                "types": [
                    {"id": "all", "label": "全部", "count": len(items)},
                    {"id": "character", "label": "角色", "count": type_counts["character"]},
                    {"id": "generation", "label": "生成图", "count": type_counts["generation"]},
                    {"id": "reference", "label": "参考图", "count": type_counts["reference"]},
                    {"id": "memory", "label": "记忆", "count": type_counts["memory"]},
                    {"id": "project", "label": "项目", "count": type_counts["project"]},
                    {"id": "job", "label": "任务", "count": type_counts["job"]},
                ],
                "statuses": sorted({item.get("status") for item in items if item.get("status")}),
            },
            "items": items,
        }

    def _asset_library_item(
        self,
        item_type: str,
        item_id: Any,
        title: Any,
        subtitle: Any,
        status: Any,
        image: Any = "",
        character_id: Any = "",
        character_name: Any = "",
        tags: Optional[list[Any]] = None,
        related_id: Any = "",
        metrics: Optional[Dict[str, Any]] = None,
        updated_at: Any = "",
    ) -> Dict[str, Any]:
        clean_tags = [str(tag) for tag in (tags or []) if str(tag or "").strip()]
        return {
            "type": item_type,
            "id": str(item_id or f"{item_type}-asset"),
            "title": str(title or item_id or item_type),
            "subtitle": str(subtitle or ""),
            "status": str(status or ""),
            "image": str(image or ""),
            "character_id": str(character_id or ""),
            "character_name": str(character_name or ""),
            "tags": clean_tags[:8],
            "related_id": str(related_id or ""),
            "metrics": metrics or {},
            "updated_at": str(updated_at or ""),
            "search_text": " ".join([
                item_type,
                str(item_id or ""),
                str(title or ""),
                str(subtitle or ""),
                str(status or ""),
                str(character_id or ""),
                str(character_name or ""),
                " ".join(clean_tags),
            ]).lower(),
        }

    def _reference_kind_label(self, kind: str) -> str:
        return {
            "face": "人脸",
            "outfit": "服装",
            "accessory": "配饰",
            "scene": "环境",
        }.get(str(kind or ""), str(kind or "参考"))

    def _project_record(
        self,
        project_id: str,
        name: str,
        user_segment: str,
        level: str,
        character_ids,
        goal: str,
        channels,
        deliverables,
        status: str = "active",
    ) -> Dict[str, Any]:
        return {
            "id": project_id,
            "name": name,
            "user_segment": user_segment,
            "level": level,
            "character_ids": self._valid_character_ids(character_ids),
            "goal": goal,
            "channels": list(channels or []),
            "deliverables": list(deliverables or []),
            "status": status,
            "submitted_at": self._timestamp() if status in {"in_review", "approved"} else None,
            "approved_at": self._timestamp() if status == "approved" else None,
            "reviewed_by": "local-reviewer" if status == "approved" else None,
            "created_at": self._timestamp(),
            "updated_at": self._timestamp(),
        }

    def _serialize_project(self, project: Dict[str, Any], include_package: bool = False) -> Dict[str, Any]:
        character_ids = self._valid_character_ids(project.get("character_ids") or [])
        project_generations = [
            generation
            for generation in self.generations
            if generation.get("character_id") in character_ids
        ]
        serialized = {
            **project,
            "character_ids": character_ids,
            "characters": [
                {
                    "id": character["id"],
                    "name": character["name"],
                    "version": character.get("version", 1),
                    "consistency_percent": round(character.get("consistency_score", 0.0) * 100),
                }
                for character_id in character_ids
                if (character := self.manager.get_character(character_id)) is not None
            ],
            "counts": {
                "characters": len(character_ids),
                "generations": len(project_generations),
                "favorites": len([generation for generation in project_generations if generation.get("favorite")]),
                "deliverables": len(project.get("deliverables") or []),
            },
            "review": self._project_review_packet(project),
            "recommendations": self._project_recommendations(project),
        }
        if include_package:
            serialized["ip_package"] = self._project_ip_package(project)
        return serialized

    def _project_ip_package(self, project: Dict[str, Any]) -> Dict[str, Any]:
        character_ids = self._valid_character_ids(project.get("character_ids") or [])
        characters = [
            self.manager.get_character(character_id)
            for character_id in character_ids
            if self.manager.get_character(character_id) is not None
        ]
        project_generations = [
            generation
            for generation in self.generations
            if generation.get("character_id") in character_ids
        ]
        generation_ids = [generation["id"] for generation in project_generations]
        generation_id_set = set(generation_ids)
        project_jobs = [
            job
            for job in self.generation_jobs
            if generation_id_set.intersection(set(job.get("generation_ids") or []))
        ]
        minimum_consistency = min(
            [round(character.get("consistency_score", 0.0), 2) for character in characters],
            default=0.0,
        )
        asset_manifest = self._project_asset_manifest(
            project,
            character_ids,
            characters,
            project_generations,
            project_jobs,
        )
        asset_counts = self._project_asset_counts(asset_manifest, project_generations, project_jobs, project)
        delivery_checklist = self._project_delivery_checklist(project, asset_manifest, asset_counts)
        release_package = self._project_release_summary(project)
        release_ready = release_package.get("status") == "ready" and project.get("status") == "approved"
        return {
            "project_id": project.get("id"),
            "name": project.get("name"),
            "user_segment": project.get("user_segment"),
            "license_scope": self._project_license_scope(project),
            "license_status": self._project_license_status(project),
            "release_ready": release_ready,
            "release_package": release_package,
            "review": self._project_review_packet(project),
            "identity_bundle": {
                "characters": character_ids,
                "versions": sum(len(character.get("versions", [])) for character in characters),
                "minimum_consistency": minimum_consistency,
            },
            "style_bundle": {
                "loras": sorted({
                    ((character.get("style") or {}).get("lora") or {}).get("id")
                    for character in characters
                    if ((character.get("style") or {}).get("lora") or {}).get("id")
                }),
                "channels": project.get("channels") or [],
            },
            "memory_bundle": {
                "scene_logs": len([
                    entry
                    for entry in self.manager.memory_store.logs
                    if entry.get("character_id") in character_ids
                ]),
                "best_angles_required": True,
                "failure_styles_blocked": True,
            },
            "generation_ids": generation_ids,
            "asset_manifest": asset_manifest,
            "asset_counts": asset_counts,
            "delivery_checklist": delivery_checklist,
            "package_complete": all(check.get("status") == "passed" for check in delivery_checklist),
            "deliverables": project.get("deliverables") or [],
            "review_steps": ["身份一致性检查", "风格一致性检查", "商业授权确认"],
        }

    def _project_asset_manifest(
        self,
        project: Dict[str, Any],
        character_ids: list[str],
        characters: list[Dict[str, Any]],
        project_generations: list[Dict[str, Any]],
        project_jobs: list[Dict[str, Any]],
    ) -> list[Dict[str, Any]]:
        manifest = []
        job_count_by_character = {
            character_id: len([
                job
                for job in project_jobs
                if str(job.get("character_id") or "") == character_id
            ])
            for character_id in character_ids
        }
        for character in characters:
            character_id = character["id"]
            scene_logs = [
                entry
                for entry in self.manager.memory_store.logs
                if entry.get("character_id") == character_id
            ]
            generations = [
                generation
                for generation in project_generations
                if generation.get("character_id") == character_id
            ]
            reference_assets = self._character_reference_assets(character_id, character)
            reference_collections = self._character_reference_collections(character_id, character)
            readiness = self._identity_readiness(reference_assets)
            production_identity = self._production_identity_summary(character)
            preferences = self.manager.memory_store.character_preferences(character_id)
            versions = character.get("versions") or []
            latest_generation = generations[-1] if generations else None
            generation_quality_passed = len([
                generation
                for generation in generations
                if (generation.get("quality") or {}).get("status") == "pass"
            ])
            manifest.append(
                {
                    "character_id": character_id,
                    "name": character.get("name"),
                    "version": character.get("version", 1),
                    "consistency_percent": round(character.get("consistency_score", 0.0) * 100),
                    "identity_references": {
                        "count": len(reference_assets),
                        "active_labels": [item.get("label") for item in reference_assets if item.get("active")],
                        "labels": [item.get("label") for item in reference_assets],
                        "readiness_status": readiness.get("status"),
                        "readiness_score": readiness.get("score"),
                        "can_train": readiness.get("can_train"),
                    },
                    "production_identity": production_identity,
                    "reference_collections": {
                        kind: {
                            "count": len(items),
                            "active_labels": [item.get("label") for item in items if item.get("active")],
                            "labels": [item.get("label") for item in items],
                        }
                        for kind, items in reference_collections.items()
                    },
                    "generation_assets": {
                        "count": len(generations),
                        "favorite_count": len([generation for generation in generations if generation.get("favorite")]),
                        "quality_pass_count": generation_quality_passed,
                        "latest_generation_id": latest_generation.get("id") if latest_generation else None,
                        "latest_model_route": self._project_model_route_summary(
                            latest_generation.get("model_route") if latest_generation else None
                        ),
                        "job_count": job_count_by_character.get(character_id, 0),
                    },
                    "memory_assets": {
                        "scene_logs": len(scene_logs),
                        "best_angles": [
                            angle.get("pose")
                            for angle in preferences.get("best_angles", [])
                            if angle.get("pose")
                        ],
                        "preferred_styles": [
                            style.get("style")
                            for style in preferences.get("preferred_styles", [])
                            if style.get("style")
                        ],
                        "average_success_score": preferences.get("average_success_score", 0.0),
                    },
                    "version_assets": {
                        "count": len(versions),
                        "current_version": character.get("version", 1),
                        "restorable_count": len([version for version in versions if version.get("can_restore")]),
                    },
                }
            )
        return manifest

    def _project_asset_counts(
        self,
        asset_manifest: list[Dict[str, Any]],
        project_generations: list[Dict[str, Any]],
        project_jobs: list[Dict[str, Any]],
        project: Dict[str, Any],
    ) -> Dict[str, Any]:
        non_face_references = 0
        active_non_face_references = 0
        for row in asset_manifest:
            for collection in (row.get("reference_collections") or {}).values():
                non_face_references += int(collection.get("count") or 0)
                active_non_face_references += len(collection.get("active_labels") or [])
        return {
            "characters": len(asset_manifest),
            "identity_references": sum(
                int((row.get("identity_references") or {}).get("count") or 0)
                for row in asset_manifest
            ),
            "non_face_references": non_face_references,
            "active_non_face_references": active_non_face_references,
            "generated_images": len(project_generations),
            "favorite_images": len([generation for generation in project_generations if generation.get("favorite")]),
            "quality_passed_images": len([
                generation
                for generation in project_generations
                if (generation.get("quality") or {}).get("status") == "pass"
            ]),
            "memory_logs": sum(
                int((row.get("memory_assets") or {}).get("scene_logs") or 0)
                for row in asset_manifest
            ),
            "versions": sum(
                int((row.get("version_assets") or {}).get("count") or 0)
                for row in asset_manifest
            ),
            "restorable_versions": sum(
                int((row.get("version_assets") or {}).get("restorable_count") or 0)
                for row in asset_manifest
            ),
            "generation_jobs": len(project_jobs),
            "deliverables": len(project.get("deliverables") or []),
        }

    def _project_delivery_checklist(
        self,
        project: Dict[str, Any],
        asset_manifest: list[Dict[str, Any]],
        asset_counts: Dict[str, Any],
    ) -> list[Dict[str, Any]]:
        identity_ready_count = len([
            row
            for row in asset_manifest
            if (row.get("identity_references") or {}).get("readiness_status") == "ready"
        ])
        release_ready = project.get("status") == "approved"
        return [
            {
                "id": "identity_ready",
                "label": "身份资产可训练",
                "status": "passed" if asset_manifest and identity_ready_count == len(asset_manifest) else "needs_review",
                "value": f"{identity_ready_count}/{len(asset_manifest)}",
            },
            {
                "id": "reference_pack_ready",
                "label": "参考资产已归档",
                "status": "passed" if asset_counts.get("non_face_references", 0) > 0 else "needs_review",
                "value": asset_counts.get("non_face_references", 0),
            },
            {
                "id": "generation_quality_ready",
                "label": "生成图通过质检",
                "status": "passed" if asset_counts.get("quality_passed_images", 0) > 0 else "needs_review",
                "value": f"{asset_counts.get('quality_passed_images', 0)}/{asset_counts.get('generated_images', 0)}",
            },
            {
                "id": "memory_ready",
                "label": "场景记忆可复用",
                "status": "passed" if asset_counts.get("memory_logs", 0) > 0 else "needs_review",
                "value": asset_counts.get("memory_logs", 0),
            },
            {
                "id": "license_ready",
                "label": "商业授权状态",
                "status": "passed" if release_ready else "pending",
                "value": self._project_license_status(project),
            },
            {
                "id": "deliverables_ready",
                "label": "交付物范围",
                "status": "passed" if asset_counts.get("deliverables", 0) > 0 else "needs_review",
                "value": asset_counts.get("deliverables", 0),
            },
        ]

    def _project_model_route_summary(self, model_route: Any) -> Optional[Dict[str, Any]]:
        if not isinstance(model_route, dict):
            return None
        return {
            "mode": model_route.get("mode"),
            "provider": model_route.get("provider"),
            "model": model_route.get("model"),
            "label": model_route.get("label"),
            "generation_kind": model_route.get("generation_kind"),
            "real_generation": bool(model_route.get("real_generation")),
        }

    def _project_recommendations(self, project: Dict[str, Any]):
        if project.get("status") == "approved":
            return ["可导出投放包", "锁定当前角色版本", "保留审阅记录"]
        if project.get("status") == "in_review":
            return ["等待商业授权确认", "避免修改绑定角色", "检查失败风格"]
        segment = project.get("user_segment")
        if segment == "普通用户":
            return ["上传 3 张以上清晰人脸", "使用轻写真模板", "收藏最稳定的一组图"]
        if segment == "商业用户":
            return ["身份权重保持 0.90+", "绑定品牌 LoRA", "导出 IP 资产包并进入审阅"]
        return ["按系列场景生成", "复用高分角度", "沉淀版本历史和失败风格"]

    def _create_project(self, body: Dict[str, Any]) -> Dict[str, Any]:
        name = str(body.get("name") or "").strip()
        if not name:
            raise ValueError("name is required")
        project_id = str(body.get("project_id") or self._slug(name)).strip()
        existing_ids = {project["id"] for project in self.projects}
        base_id = project_id
        suffix = 2
        while project_id in existing_ids:
            project_id = f"{base_id}-{suffix}"
            suffix += 1
        character_ids = body.get("character_ids") or [body.get("character_id") or next(iter(self.manager.characters))]
        project = self._project_record(
            project_id=project_id,
            name=name,
            user_segment=str(body.get("user_segment") or "创作者"),
            level=str(body.get("level") or "Level 3 Character OS"),
            character_ids=character_ids,
            goal=str(body.get("goal") or "沉淀一个可持续复用的角色项目"),
            channels=body.get("channels") or ["小红书", "抖音"],
            deliverables=body.get("deliverables") or ["角色资产", "生成图", "项目导出"],
            status=str(body.get("status") or "active"),
        )
        self.projects.append(project)
        return project

    def _update_project(self, project_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        project = self._get_project(project_id)
        for field in ["name", "user_segment", "level", "goal", "status"]:
            if field in body:
                project[field] = str(body.get(field) or "").strip()
                if field == "status":
                    self._normalize_project_review_dates(project)
        if "character_ids" in body or "character_id" in body:
            project["character_ids"] = self._valid_character_ids(body.get("character_ids") or [body.get("character_id")])
        for field in ["channels", "deliverables"]:
            if field in body:
                project[field] = [str(item) for item in body.get(field) or [] if str(item).strip()]
        if body.get("review_action"):
            self._transition_project_review(project, str(body.get("review_action")))
        project["updated_at"] = self._timestamp()
        return project

    def _transition_project_review(self, project: Dict[str, Any], action: str) -> None:
        normalized = action.strip().lower().replace("-", "_")
        now = self._timestamp()
        if normalized in {"submit", "submit_review", "submit_project_review"}:
            project["status"] = "in_review"
            project["submitted_at"] = now
            project["approved_at"] = None
            project["reviewed_by"] = None
            return
        if normalized in {"approve", "approve_project", "approve_review"}:
            project["status"] = "approved"
            project["submitted_at"] = project.get("submitted_at") or now
            project["approved_at"] = now
            project["reviewed_by"] = "local-reviewer"
            return
        if normalized in {"withdraw", "withdraw_review", "reopen", "draft", "return_draft"}:
            project["status"] = "draft"
            project["approved_at"] = None
            project["reviewed_by"] = None
            return
        raise ValueError(f"Unknown project review action: {action}")

    def _normalize_project_review_dates(self, project: Dict[str, Any]) -> None:
        status = project.get("status")
        now = self._timestamp()
        if status in {"in_review", "approved"} and not project.get("submitted_at"):
            project["submitted_at"] = now
        if status == "approved" and not project.get("approved_at"):
            project["approved_at"] = now
            project["reviewed_by"] = project.get("reviewed_by") or "local-reviewer"
        if status != "approved":
            project["approved_at"] = None
            project["reviewed_by"] = None

    def _project_review_packet(self, project: Dict[str, Any]) -> Dict[str, Any]:
        status = str(project.get("status") or "active")
        character_ids = self._valid_character_ids(project.get("character_ids") or [])
        characters = [
            self.manager.get_character(character_id)
            for character_id in character_ids
            if self.manager.get_character(character_id) is not None
        ]
        minimum_consistency = min(
            [round(character.get("consistency_score", 0.0), 2) for character in characters],
            default=0.0,
        )
        has_deliverables = bool(project.get("deliverables"))
        release_package = self._project_release_summary(project)
        checks = [
            {
                "id": "identity_consistency",
                "label": "身份一致性",
                "status": "passed" if minimum_consistency >= 0.72 else "needs_review",
                "value": minimum_consistency,
            },
            {
                "id": "asset_scope",
                "label": "资产范围",
                "status": "passed" if character_ids and has_deliverables else "needs_review",
                "value": len(character_ids),
            },
            {
                "id": "license_confirm",
                "label": "商业授权",
                "status": "passed" if status == "approved" else "pending",
                "value": self._project_license_status(project),
            },
        ]
        return {
            "status": status,
            "label": self._project_status_label(status),
            "license_scope": self._project_license_scope(project),
            "license_status": self._project_license_status(project),
            "release_ready": release_package.get("status") == "ready" and status == "approved",
            "release_package": release_package,
            "submitted_at": project.get("submitted_at"),
            "approved_at": project.get("approved_at"),
            "reviewed_by": project.get("reviewed_by"),
            "checks": checks,
        }

    def _project_license_scope(self, project: Dict[str, Any]) -> str:
        return "commercial-campaign" if project.get("user_segment") == "商业用户" else "creator-demo"

    def _project_license_status(self, project: Dict[str, Any]) -> str:
        status = project.get("status")
        if status == "approved":
            return "commercial-ready" if project.get("user_segment") == "商业用户" else "creator-ready"
        if status == "in_review":
            return "pending-review"
        if status == "draft":
            return "draft"
        return "internal-active"

    def _project_status_label(self, status: str) -> str:
        return {
            "draft": "草稿",
            "active": "进行中",
            "in_review": "审阅中",
            "approved": "已批准",
            "archived": "已归档",
        }.get(status, "进行中")

    def _get_project(self, project_id: str) -> Dict[str, Any]:
        for project in self.projects:
            if project.get("id") == project_id:
                return project
        raise KeyError(f"Unknown project: {project_id}")

    def _delete_project(self, project_id: str) -> Dict[str, Any]:
        project = self._get_project(project_id)
        self.projects = [item for item in self.projects if item.get("id") != project_id]
        return {"id": project_id, "name": project.get("name")}

    def _project_release_summary(self, project: Dict[str, Any]) -> Dict[str, Any]:
        release_package = project.get("release_package")
        if not isinstance(release_package, dict):
            return {"status": "not_built", "label": "未生成发布包"}
        return {
            "id": release_package.get("id"),
            "status": release_package.get("status") or "not_built",
            "label": release_package.get("label") or "商业发布包",
            "artifact_path": release_package.get("artifact_path") or "",
            "built_at": release_package.get("built_at"),
            "approved_at": release_package.get("approved_at"),
            "checklist": release_package.get("checklist") or [],
        }

    def _build_project_release(self, project_id: str, body: Dict[str, Any]) -> Dict[str, Any]:
        project = self._get_project(project_id)
        if body.get("ensure_deployment", True) and not self._deployment_status().get("ready"):
            self._initialize_deployment({"workspace_id": body.get("workspace_id") or "persona-studio-local-prod"})
        if body.get("auto_train_identity", True):
            for character_id in self._valid_character_ids(project.get("character_ids") or []):
                character = self.manager.get_character(character_id)
                if character and self._production_identity_summary(character).get("status") != "trained":
                    self._train_identity_for_character(
                        character_id,
                        encoder=str(body.get("encoder") or "arcface-compatible-v1"),
                        provider=str(body.get("provider") or "local-production-encoder"),
                        embedding_dim=int(body.get("embedding_dim") or 512),
                    )

        self._transition_project_review(project, "approve")
        project["channels"] = project.get("channels") or ["广告投放", "电商主图", "品牌海报"]
        project["deliverables"] = project.get("deliverables") or ["IP 资产包", "商业授权摘要", "发布清单"]
        ip_package = self._project_ip_package(project)
        checklist = self._project_release_checklist(project, ip_package)
        ready = all(check.get("status") == "passed" for check in checklist)
        release_id = f"release-{project_id}-{self._safe_timestamp_id()}"
        built_at = self._timestamp()
        release_payload = {
            "id": release_id,
            "status": "ready" if ready else "needs_review",
            "project": {
                "id": project.get("id"),
                "name": project.get("name"),
                "user_segment": project.get("user_segment"),
                "level": project.get("level"),
                "channels": project.get("channels") or [],
                "deliverables": project.get("deliverables") or [],
            },
            "identity_training": self._identity_training_status(),
            "deployment": self._deployment_status(),
            "ip_package": ip_package,
            "checklist": checklist,
            "built_at": built_at,
            "approved_at": project.get("approved_at"),
        }
        artifact_path = self._write_json_artifact(
            f"releases/{project_id}",
            f"{release_id}.json",
            release_payload,
        )
        release_summary = {
            "id": release_id,
            "status": "ready" if ready else "needs_review",
            "label": "商业发布包已就绪" if ready else "发布包需复核",
            "artifact_path": artifact_path,
            "built_at": built_at,
            "approved_at": project.get("approved_at"),
            "checklist": [
                *checklist,
                {
                    "id": "release_artifact",
                    "label": "发布包归档",
                    "status": "passed",
                    "value": artifact_path,
                },
            ],
        }
        project["release_package"] = release_summary
        if ready:
            project["status"] = "approved"
        else:
            project["status"] = "in_review"
            project["approved_at"] = None
            project["reviewed_by"] = None
        project["updated_at"] = built_at
        self._append_audit_event(
            "project.release_built",
            {"project_id": project_id, "release_id": release_id, "status": release_summary["status"]},
        )
        return {
            "release_package": release_summary,
            "project": self._serialize_project(project, include_package=True),
        }

    def _project_release_checklist(self, project: Dict[str, Any], ip_package: Dict[str, Any]) -> list[Dict[str, Any]]:
        character_ids = self._valid_character_ids(project.get("character_ids") or [])
        production_ready = [
            character_id
            for character_id in character_ids
            if self._production_identity_summary(self.manager.characters.get(character_id) or {}).get("status") == "trained"
        ]
        deployment = self._deployment_status()
        asset_counts = ip_package.get("asset_counts") or {}
        checklist = [
            {
                "id": "production_identity",
                "label": "生产身份包",
                "status": "passed" if character_ids and len(production_ready) == len(character_ids) else "needs_review",
                "value": f"{len(production_ready)}/{len(character_ids)}",
            },
            {
                "id": "storage_rbac",
                "label": "存储与权限",
                "status": "passed" if deployment.get("ready") else "needs_review",
                "value": deployment.get("status"),
            },
            {
                "id": "ip_package_complete",
                "label": "IP 资产包",
                "status": "passed" if ip_package.get("package_complete") else "needs_review",
                "value": f"{len([check for check in ip_package.get('delivery_checklist') or [] if check.get('status') == 'passed'])}/{len(ip_package.get('delivery_checklist') or [])}",
            },
            {
                "id": "quality_assets",
                "label": "可投放图像资产",
                "status": "passed" if int(asset_counts.get("quality_passed_images") or 0) > 0 else "needs_review",
                "value": f"{asset_counts.get('quality_passed_images', 0)}/{asset_counts.get('generated_images', 0)}",
            },
            {
                "id": "commercial_license",
                "label": "商业授权",
                "status": "passed" if project.get("status") == "approved" else "needs_review",
                "value": self._project_license_status(project),
            },
        ]
        return checklist

    def _valid_character_ids(self, character_ids):
        valid_ids = []
        for character_id in character_ids or []:
            character_id = str(character_id or "").strip()
            if character_id and character_id in self.manager.characters and character_id not in valid_ids:
                valid_ids.append(character_id)
        return valid_ids

    def _slug(self, value: str) -> str:
        slug = "".join(character.lower() if character.isalnum() else "-" for character in value).strip("-")
        while "--" in slug:
            slug = slug.replace("--", "-")
        return slug or "project"

    def _style_labels(self, style: Dict[str, Any]):
        labels = [
            style.get("preset"),
            style.get("lighting"),
            style.get("camera_language"),
            (style.get("lora") or {}).get("label"),
        ]
        return [label for label in labels if label]

    def _character_asset_summary(
        self,
        character_id: str,
        character: Dict[str, Any],
        scene_logs: list[Dict[str, Any]],
    ) -> Dict[str, Any]:
        character_generations = [
            generation for generation in self.generations if generation.get("character_id") == character_id
        ]
        timestamps = [
            str(value)
            for value in [
                character.get("updated_at"),
                character.get("created_at"),
                *(generation.get("created_at") for generation in character_generations),
                *(entry.get("created_at") for entry in scene_logs),
            ]
            if value
        ]
        identity = character.get("identity") or {}
        reference_assets = self._character_reference_assets(character_id, character)
        reference_collections = self._character_reference_collections(character_id, character)
        return {
            "generation_count": len(character_generations),
            "favorite_count": len([generation for generation in character_generations if generation.get("favorite")]),
            "version_count": len(character.get("versions") or []),
            "reference_count": len(reference_assets) or int(identity.get("reference_count") or 0),
            "reference_collection_count": sum(len(items) for items in reference_collections.values()),
            "memory_count": len(scene_logs),
            "last_used_at": max(timestamps) if timestamps else None,
            "updated_at": character.get("updated_at"),
            "tags": self._normalize_character_tags(character.get("tags")),
        }

    def _character_reference_assets(self, character_id: str, character: Dict[str, Any]) -> list[Dict[str, Any]]:
        references = self._normalize_character_references(character.get("reference_assets"))
        if references:
            return references
        image_paths = self._default_character_reference_images(character_id)
        labels = ["主图", "侧脸", "回眸", "微笑"]
        return [
            {
                "id": f"{character_id}-face-{index + 1}",
                "label": labels[index] if index < len(labels) else f"参考 {index + 1}",
                "image": image,
                "source": image,
                "prompt": "保持参考人脸五官比例和脸型" if index == 0 else "保持同一角色身份",
                "active": index == 0,
                "created_at": character.get("created_at") or "2026-06-17T00:00:00Z",
            }
            for index, image in enumerate(image_paths)
        ]

    def _default_character_reference_images(self, character_id: str) -> list[str]:
        offset = {"lina": 0, "kira": 1, "alex": 2}.get(character_id, 0)
        images = [f"assets/persona-ref-{((offset + index) % 4) + 1}.png" for index in range(4)]
        return images

    def _reference_collection_kinds(self) -> tuple[str, ...]:
        return ("outfit", "accessory", "scene")

    def _character_reference_collections(
        self,
        character_id: str,
        character: Dict[str, Any],
    ) -> Dict[str, list[Dict[str, Any]]]:
        existing = character.get("reference_collections") if isinstance(character.get("reference_collections"), dict) else {}
        collections = {}
        for kind in self._reference_collection_kinds():
            if kind in existing:
                collections[kind] = self._normalize_reference_collection(
                    kind,
                    existing.get(kind),
                    created_at_default=character.get("created_at") or "2026-06-17T00:00:00Z",
                )
            else:
                collections[kind] = self._default_reference_collection(kind, character_id)
        return collections

    def _default_reference_collection(self, kind: str, character_id: str = "") -> list[Dict[str, Any]]:
        created_at = "2026-06-17T00:00:00Z"
        defaults = {
            "outfit": [
                {
                    "id": "outfit-white-blouse",
                    "label": "白色上衣",
                    "visual": "white-blouse",
                    "prompt": "参考服装：白色轻薄上衣，干净自然，布料有柔和褶皱",
                },
                {
                    "id": "outfit-satin-dress",
                    "label": "缎面裙",
                    "visual": "satin-dress",
                    "prompt": "参考服装：浅色缎面连衣裙，垂坠感明显，适合写真",
                },
                {
                    "id": "outfit-knit-cardigan",
                    "label": "针织外套",
                    "visual": "knit-cardigan",
                    "prompt": "参考服装：浅色针织外套，柔软纹理，温和生活感",
                },
            ],
            "accessory": [
                {
                    "id": "accessory-leather-bag",
                    "label": "手提包",
                    "visual": "leather-bag",
                    "prompt": "参考配饰：小号皮质手提包，低调商业感",
                },
                {
                    "id": "accessory-pearl-earring",
                    "label": "耳饰",
                    "visual": "pearl-earring",
                    "prompt": "参考配饰：小珍珠耳饰，精致但不抢脸",
                },
                {
                    "id": "accessory-silk-scarf",
                    "label": "丝巾",
                    "visual": "silk-scarf",
                    "prompt": "参考配饰：暖色丝巾，轻微飘动，增加层次",
                },
            ],
            "scene": [
                {
                    "id": "scene-park",
                    "label": "公园",
                    "image": "assets/persona-ref-1.png",
                    "alt": "Park environment reference",
                    "prompt": "参考环境：清晨户外公园，自然逆光，背景绿植虚化",
                },
                {
                    "id": "scene-riverside",
                    "label": "河边",
                    "image": "assets/persona-ref-3.png",
                    "alt": "Riverside environment reference",
                    "prompt": "参考环境：河边步道，冷色水面反光，浅景深",
                },
                {
                    "id": "scene-garden",
                    "label": "花园",
                    "image": "assets/persona-ref-4.png",
                    "alt": "Garden environment reference",
                    "prompt": "参考环境：花园小路，暖色阳光，花丛背景",
                },
                {
                    "id": "scene-studio",
                    "label": "棚拍",
                    "visual": "studio",
                    "prompt": "参考环境：干净摄影棚，受控主光，商业头像质感",
                },
            ],
        }
        return [
            {
                **item,
                "active": False,
                "created_at": created_at,
            }
            for item in defaults.get(kind, [])
        ]

    def _identity_readiness(self, reference_assets: list[Dict[str, Any]]) -> Dict[str, Any]:
        usable = [
            reference
            for reference in reference_assets
            if reference.get("image") or reference.get("source")
        ]
        image_keys = [
            str(reference.get("image") or reference.get("source") or "").split("?", 1)[0]
            for reference in usable
        ]
        unique_images = set(image_keys)
        duplicate_count = max(0, len(image_keys) - len(unique_images))
        checks = [
            {
                "id": "minimum_references",
                "label": "至少 3 张参考脸",
                "status": "passed" if len(usable) >= 3 else "failed",
                "value": len(usable),
            },
            {
                "id": "duplicate_references",
                "label": "重复参考",
                "status": "review" if duplicate_count else "passed",
                "value": duplicate_count,
            },
            {
                "id": "active_anchor",
                "label": "主参考",
                "status": "passed" if any(reference.get("active") for reference in usable) else "review",
                "value": len([reference for reference in usable if reference.get("active")]),
            },
        ]
        if len(usable) < 3:
            status = "incomplete"
            label = "参考脸不足"
        elif duplicate_count:
            status = "review"
            label = "需要复核"
        else:
            status = "ready"
            label = "可训练"
        score = 0.0
        score += min(1.0, len(usable) / 3) * 0.7
        score += (0.2 if any(reference.get("active") for reference in usable) else 0.0)
        score += (0.1 if duplicate_count == 0 else 0.0)
        return {
            "status": status,
            "label": label,
            "score": round(min(score, 1.0), 2),
            "reference_count": len(usable),
            "duplicate_count": duplicate_count,
            "can_train": len(usable) >= 3,
            "checks": checks,
        }

    def _identity_strength(self, character: Dict[str, Any]) -> float:
        score = float(character.get("consistency_score", 0.0))
        return round(max(0.55, min(0.95, score)), 2)

    def _memory_response(self, character_id: str) -> Dict[str, Any]:
        if character_id not in self.manager.characters:
            raise KeyError(f"Unknown character: {character_id}")
        character = self.manager.characters[character_id]
        style = character.get("style") or {}
        return {
            "character_id": character_id,
            "entries": self._character_memory_entries(character_id),
            "insights": self._memory_insights(character_id, style),
        }

    def _character_memory_entries(self, character_id: str, limit: Optional[int] = None) -> list[Dict[str, Any]]:
        entries = []
        for index, entry in enumerate(self.manager.memory_store.logs):
            if entry.get("character_id") != character_id:
                continue
            entries.append(self._serialize_memory_entry(entry, index))
        entries = list(reversed(entries))
        return entries[:limit] if limit is not None else entries

    def _serialize_memory_entry(self, entry: Dict[str, Any], index: int) -> Dict[str, Any]:
        metadata = entry.get("metadata") if isinstance(entry.get("metadata"), dict) else {}
        quality = metadata.get("quality") if isinstance(metadata.get("quality"), dict) else {}
        reference_guidance = metadata.get("reference_guidance") if isinstance(metadata.get("reference_guidance"), list) else []
        reference_labels = [
            f"{group.get('label') or group.get('kind')}:{item.get('label')}"
            for group in reference_guidance
            for item in (group.get("items") or [])
            if item.get("label")
        ]
        score = float(entry.get("success_score") or 0.0)
        return {
            "id": self._memory_entry_id(entry, index),
            "prompt": entry.get("prompt") or "",
            "image": entry.get("image"),
            "pose": entry.get("pose"),
            "pose_label": self._pose_label(entry.get("pose")),
            "style": entry.get("style"),
            "state": entry.get("state"),
            "success_score": round(score, 3),
            "score_percent": round(score * 100),
            "generation_id": metadata.get("generation_id"),
            "quality_status": quality.get("status"),
            "quality_score": quality.get("face_match_score"),
            "reference_labels": reference_labels[:6],
            "source": metadata.get("source") or ("generation" if metadata.get("generation_id") else "manual"),
            "created_at": entry.get("created_at") or metadata.get("created_at"),
        }

    def _memory_entry_id(self, entry: Dict[str, Any], index: int) -> str:
        if entry.get("id"):
            return str(entry["id"])
        metadata = entry.get("metadata") if isinstance(entry.get("metadata"), dict) else {}
        if metadata.get("memory_id"):
            return str(metadata["memory_id"])
        if metadata.get("generation_id"):
            return f"memory-{metadata['generation_id']}"
        payload = json.dumps(
            {
                "character_id": entry.get("character_id"),
                "prompt": entry.get("prompt"),
                "image": entry.get("image"),
                "pose": entry.get("pose"),
                "style": entry.get("style"),
                "state": entry.get("state"),
                "success_score": entry.get("success_score"),
                "index": index,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        return f"memory-{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:12]}"

    def _delete_memory_entry(self, character_id: str, memory_id: str) -> Dict[str, Any]:
        for index, entry in enumerate(self.manager.memory_store.logs):
            if entry.get("character_id") != character_id:
                continue
            if self._memory_entry_id(entry, index) != memory_id:
                continue
            deleted = self._serialize_memory_entry(entry, index)
            del self.manager.memory_store.logs[index]
            if character_id in self.manager.characters:
                self.manager.characters[character_id]["memory"] = self.manager.memory_store.character_preferences(character_id)
            return deleted
        raise KeyError(f"Unknown memory entry: {memory_id}")

    def _pose_label(self, pose: Any) -> str:
        return {
            "front": "正面",
            "three-quarter": "四分之三侧脸",
            "side": "侧脸",
            "reference_pose": "参考姿态",
        }.get(str(pose or ""), str(pose or "未标注"))

    def _memory_insights(self, character_id: str, style: Dict[str, Any]) -> Dict[str, Any]:
        preferences = self.manager.memory_store.character_preferences(character_id)
        failure_advice = self.manager.memory_store.avoid_failure_styles(
            style.get("preset"), character_id=character_id
        )
        return {
            "best_angles": preferences.get("best_angles", []),
            "preferred_styles": preferences.get("preferred_styles", []),
            "average_success_score": preferences.get("average_success_score", 0.0),
            "failure_advice": failure_advice,
        }

    def _resolve_face_images(self, face_images):
        resolved = []
        for image in face_images:
            if isinstance(image, str):
                clean_path = image.split("?", 1)[0].lstrip("/")
                static_file = (self.static_dir / clean_path).resolve()
                if (
                    (self.static_dir in static_file.parents or static_file == self.static_dir)
                    and static_file.exists()
                    and static_file.is_file()
                ):
                    resolved.append(str(static_file))
                    continue
            resolved.append(image)
        return resolved

    def _synthetic_faces(self, name: str, suffix: str = "seed"):
        safe_name = str(name).strip().lower().replace(" ", "-") or "character"
        return [
            f"{safe_name}-{suffix}-front",
            f"{safe_name}-{suffix}-three-quarter",
            f"{safe_name}-{suffix}-studio",
        ]

    def _next_version(self, character_id: str) -> int:
        character = self.manager.get_character(character_id)
        if character is None:
            raise KeyError(f"Unknown character: {character_id}")
        return int(character.get("version", 1)) + 1

    def _save_assets(self):
        if self.asset_store is not None:
            self.asset_store.save_state(
                self.manager,
                self.generations,
                self.projects,
                self.settings,
                generation_jobs=self.generation_jobs,
                account=self.account,
            )

    def _workspace_data_dir(self) -> Path:
        if self.asset_store is not None:
            return self.asset_store.path.parent
        return (Path.cwd() / "output" / "runtime").resolve()

    def _safe_timestamp_id(self) -> str:
        return self._timestamp().replace(":", "").replace("-", "").replace("T", "-").removesuffix("Z")

    def _write_json_artifact(self, folder: str, filename: str, payload: Dict[str, Any]) -> str:
        artifact_dir = self._workspace_data_dir() / folder
        artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = artifact_dir / filename
        artifact_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return str(artifact_path)

    def _production_identity_summary(self, character: Dict[str, Any]) -> Dict[str, Any]:
        production_identity = character.get("production_identity")
        if not isinstance(production_identity, dict):
            return {
                "status": "not_trained",
                "label": "未训练生产身份包",
                "encoder": "",
                "embedding_dim": 0,
                "artifact_path": "",
            }
        return {
            "status": production_identity.get("status") or "not_trained",
            "label": production_identity.get("label") or "生产身份包",
            "job_id": production_identity.get("job_id"),
            "encoder": production_identity.get("encoder") or "",
            "provider": production_identity.get("provider") or "",
            "embedding_dim": int(production_identity.get("embedding_dim") or 0),
            "reference_count": int(production_identity.get("reference_count") or 0),
            "quality_score": production_identity.get("quality_score"),
            "trained_at": production_identity.get("trained_at"),
            "artifact_path": production_identity.get("artifact_path") or "",
            "vector_hash": production_identity.get("vector_hash") or "",
        }

    def _identity_training_status(self) -> Dict[str, Any]:
        characters = []
        jobs = []
        for character_id, character in self.manager.characters.items():
            summary = self._production_identity_summary(character)
            readiness = self._identity_readiness(self._character_reference_assets(character_id, character))
            characters.append(
                {
                    "character_id": character_id,
                    "name": character.get("name") or character_id,
                    "status": summary.get("status"),
                    "encoder": summary.get("encoder"),
                    "embedding_dim": summary.get("embedding_dim"),
                    "artifact_path": summary.get("artifact_path"),
                    "quality_score": summary.get("quality_score"),
                    "reference_count": summary.get("reference_count") or readiness.get("reference_count"),
                    "can_train": readiness.get("can_train"),
                    "lora": self._character_lora_summary(character),
                }
            )
            jobs.extend(character.get("identity_training_jobs") or [])
        total = len(characters)
        trained = len([character for character in characters if character.get("status") == "trained"])
        return {
            "generated_at": self._timestamp(),
            "status": "ready" if total and trained == total else "partial" if trained else "not_started",
            "total": total,
            "trained": trained,
            "provider": "local-production-encoder",
            "supported_encoders": ["arcface-compatible-v1", "insightface-compatible-v1", "custom-vit-compatible-v1"],
            "characters": characters,
            "jobs": sorted(jobs, key=lambda job: str(job.get("created_at") or ""), reverse=True),
        }

    def _create_identity_training_jobs(self, body: Dict[str, Any]) -> Dict[str, Any]:
        requested_character_id = str(body.get("character_id") or "").strip()
        if requested_character_id and requested_character_id != "all":
            character_ids = [requested_character_id]
        else:
            character_ids = list(self.manager.characters)
        train_lora = bool(body.get("train_lora"))
        lora_steps = int(body.get("lora_steps") or 1000)
        jobs = [
            self._train_identity_for_character(
                character_id,
                encoder=str(body.get("encoder") or "arcface-compatible-v1"),
                provider=str(body.get("provider") or "local-production-encoder"),
                embedding_dim=int(body.get("embedding_dim") or 512),
                train_lora=train_lora,
                lora_steps=lora_steps,
            )
            for character_id in character_ids
        ]
        return {"jobs": jobs, "training": self._identity_training_status()}

    def _train_identity_for_character(
        self,
        character_id: str,
        encoder: str,
        provider: str,
        embedding_dim: int,
        train_lora: bool = False,
        lora_steps: int = 1000,
    ) -> Dict[str, Any]:
        if character_id not in self.manager.characters:
            raise KeyError(f"Unknown character: {character_id}")
        character = self.manager.characters[character_id]
        embedding_dim = 1024 if embedding_dim >= 1024 else 512
        reference_assets = self._character_reference_assets(character_id, character)
        readiness = self._identity_readiness(reference_assets)
        if not readiness.get("can_train"):
            raise ValueError(f"{character.get('name') or character_id} 缺少生产身份训练所需的 3 张参考脸")
        reference_payloads = [
            str(reference.get("image") or reference.get("source") or "")
            for reference in reference_assets
            if reference.get("image") or reference.get("source")
        ][:20]
        resolved_faces = self._resolve_face_images(reference_payloads)
        bundle = IdentityModel(embedding_dim=embedding_dim).encode_faces(resolved_faces)
        vector_hash = hashlib.sha256(
            json.dumps(bundle.get("vector") or [], separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        created_at = self._timestamp()
        job_id = f"idtrain-{character_id}-{self._safe_timestamp_id()}"
        artifact_payload = {
            "id": job_id,
            "character_id": character_id,
            "character_name": character.get("name"),
            "provider": provider,
            "encoder": encoder,
            "embedding_dim": embedding_dim,
            "reference_ids": [reference.get("id") for reference in reference_assets],
            "reference_count": len(reference_payloads),
            "constraints": bundle.get("constraints") or {},
            "vector_hash": vector_hash,
            "quality": {
                "status": "passed",
                "readiness_score": readiness.get("score"),
                "reference_stability": (bundle.get("constraints") or {}).get("reference_stability"),
            },
            "created_at": created_at,
        }
        artifact_path = self._write_json_artifact(
            f"identity_models/{character_id}",
            f"{job_id}.json",
            artifact_payload,
        )
        quality_score = round(
            min(
                0.99,
                max(float(character.get("consistency_score") or 0.0), 0.72)
                + float(readiness.get("score") or 0.0) * 0.08
                + float((bundle.get("constraints") or {}).get("reference_stability") or 0.0) * 0.03,
            ),
            3,
        )
        character["identity"] = {
            **bundle,
            "encoder": encoder,
            "provider": provider,
            "production_artifact": artifact_path,
            "vector_hash": vector_hash,
        }
        character["production_identity"] = {
            "status": "trained",
            "label": "生产身份包已训练",
            "job_id": job_id,
            "provider": provider,
            "encoder": encoder,
            "embedding_dim": embedding_dim,
            "reference_count": len(reference_payloads),
            "quality_score": quality_score,
            "trained_at": created_at,
            "artifact_path": artifact_path,
            "vector_hash": vector_hash,
        }
        character["consistency_score"] = max(float(character.get("consistency_score") or 0.0), quality_score)
        character["updated_at"] = created_at
        job = {
            "id": job_id,
            "character_id": character_id,
            "character_name": character.get("name"),
            "status": "completed",
            "provider": provider,
            "encoder": encoder,
            "embedding_dim": embedding_dim,
            "reference_count": len(reference_payloads),
            "quality_score": quality_score,
            "artifact_path": artifact_path,
            "created_at": created_at,
            "completed_at": created_at,
        }
        if train_lora:
            # Real per-character LoRA on fal: package the references, upload, run
            # the trainer, and store the weights URL so future fresh generations
            # route through fal-ai/flux-lora for a tight identity lock.
            lora_record = self._train_fal_lora_for_character(
                character_id, character, reference_payloads, steps=lora_steps
            )
            character["fal_lora"] = lora_record
            job["lora_trained"] = True
            job["fal_lora"] = {
                "trigger_word": lora_record.get("trigger_word"),
                "scale": lora_record.get("scale"),
                "status": lora_record.get("status"),
                "steps": lora_record.get("steps"),
                "reference_count": lora_record.get("reference_count"),
                "trained_at": lora_record.get("trained_at"),
            }
        character.setdefault("identity_training_jobs", []).append(job)
        return job

    def _get_identity_training_job(self, job_id: str) -> Dict[str, Any]:
        for character in self.manager.characters.values():
            for job in character.get("identity_training_jobs") or []:
                if job.get("id") == job_id:
                    return job
        raise KeyError(f"Unknown identity training job: {job_id}")

    def _deployment_manifest(self) -> Dict[str, Any]:
        deployment = self.settings.get("deployment") if isinstance(self.settings.get("deployment"), dict) else {}
        return dict(deployment or {})

    def _initialize_deployment(self, body: Dict[str, Any]) -> Dict[str, Any]:
        data_dir = self._workspace_data_dir()
        workspace_id = str(body.get("workspace_id") or "persona-studio-local-prod").strip()
        object_store_path = self.static_dir / "assets"
        generated_path = object_store_path / "generated"
        identity_path = data_dir / "identity_models"
        release_path = data_dir / "releases"
        audit_path = data_dir / "audit" / "events.jsonl"
        for path in [generated_path, identity_path, release_path, audit_path.parent]:
            path.mkdir(parents=True, exist_ok=True)
        manifest = {
            "status": "production_local_ready",
            "workspace_id": workspace_id,
            "mode": "local-single-node",
            "database": {
                "kind": "json-state",
                "path": str(self.asset_store.path if self.asset_store else data_dir / "persona_studio_state.json"),
            },
            "object_store": {
                "kind": "local-file-store",
                "path": str(object_store_path),
                "generated_path": str(generated_path),
            },
            "identity_model_store": {
                "kind": "local-artifact-store",
                "path": str(identity_path),
            },
            "release_store": {
                "kind": "local-artifact-store",
                "path": str(release_path),
            },
            "rbac": {
                "default_user": "owner",
                "roles": [
                    {"id": "owner", "permissions": ["read", "write", "export", "approve", "admin"]},
                    {"id": "editor", "permissions": ["read", "write", "export"]},
                    {"id": "viewer", "permissions": ["read"]},
                ],
            },
            "audit": {
                "kind": "jsonl",
                "path": str(audit_path),
            },
            "initialized_at": self._timestamp(),
        }
        self.settings["deployment"] = manifest
        self._append_audit_event("deployment.initialized", {"workspace_id": workspace_id})
        return self._deployment_status()

    def _append_audit_event(self, action: str, payload: Dict[str, Any]) -> None:
        deployment = self._deployment_manifest()
        audit_path = Path(((deployment.get("audit") or {}).get("path") or self._workspace_data_dir() / "audit" / "events.jsonl"))
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "id": f"audit-{self._safe_timestamp_id()}",
            "action": action,
            "payload": payload,
            "created_at": self._timestamp(),
            "actor": "local-owner",
        }
        with audit_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    def _deployment_status(self) -> Dict[str, Any]:
        manifest = self._deployment_manifest()
        if not manifest:
            return {
                "generated_at": self._timestamp(),
                "status": "not_configured",
                "ready": False,
                "manifest": {},
                "checks": [
                    {"id": "deployment_manifest", "label": "部署清单", "status": "missing", "value": "未初始化"},
                ],
            }
        database_path = Path((manifest.get("database") or {}).get("path") or "")
        object_store_path = Path((manifest.get("object_store") or {}).get("path") or "")
        generated_path = Path((manifest.get("object_store") or {}).get("generated_path") or "")
        identity_path = Path((manifest.get("identity_model_store") or {}).get("path") or "")
        release_path = Path((manifest.get("release_store") or {}).get("path") or "")
        audit_path = Path((manifest.get("audit") or {}).get("path") or "")
        roles = ((manifest.get("rbac") or {}).get("roles") or [])
        checks = [
            {
                "id": "database",
                "label": "状态数据库",
                "status": "passed" if database_path.exists() else "missing",
                "value": str(database_path),
            },
            {
                "id": "object_store",
                "label": "对象存储",
                "status": "passed" if object_store_path.exists() and generated_path.exists() else "missing",
                "value": str(object_store_path),
            },
            {
                "id": "identity_artifacts",
                "label": "身份模型仓库",
                "status": "passed" if identity_path.exists() else "missing",
                "value": str(identity_path),
            },
            {
                "id": "release_artifacts",
                "label": "发布包仓库",
                "status": "passed" if release_path.exists() else "missing",
                "value": str(release_path),
            },
            {
                "id": "rbac",
                "label": "权限角色",
                "status": "passed" if {"owner", "editor", "viewer"}.issubset({role.get("id") for role in roles}) else "missing",
                "value": len(roles),
            },
            {
                "id": "audit_log",
                "label": "审计日志",
                "status": "passed" if audit_path.exists() else "missing",
                "value": str(audit_path),
            },
        ]
        ready = all(check["status"] == "passed" for check in checks)
        return {
            "generated_at": self._timestamp(),
            "status": "production_local_ready" if ready else "needs_review",
            "ready": ready,
            "manifest": manifest,
            "checks": checks,
        }

    def _default_api_profile(self, provider: str = "") -> Dict[str, Any]:
        provider = str(provider or "openai-compatible").strip() or "openai-compatible"
        return {
            "enabled": False,
            "provider": provider,
            "base_url": "",
            "model": "",
            "api_key": "",
            "access_key": "",
            "secret_key": "",
            "last_test": None,
        }

    def _normalize_api_profile(self, provider: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        profile = dict(profile or {})
        normalized_provider = str(profile.get("provider") or provider or "openai-compatible").strip() or "openai-compatible"
        return {
            "enabled": bool(profile.get("enabled", False)),
            "provider": normalized_provider,
            "base_url": str(profile.get("base_url") or "").strip().rstrip("/"),
            "model": str(profile.get("model") or "").strip(),
            "api_key": str(profile.get("api_key") or "").strip(),
            "access_key": str(profile.get("access_key") or "").strip(),
            "secret_key": str(profile.get("secret_key") or "").strip(),
            "last_test": profile.get("last_test"),
        }

    def _api_profile_has_config(self, profile: Dict[str, Any]) -> bool:
        return bool(
            profile.get("enabled")
            or profile.get("base_url")
            or profile.get("model")
            or profile.get("api_key")
            or profile.get("access_key")
            or profile.get("secret_key")
            or profile.get("last_test")
        )

    def _settings_from_active_profile(self, provider: str, profiles: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        provider = str(provider or "openai-compatible").strip() or "openai-compatible"
        normalized_profiles = {}
        for profile_id, profile in (profiles or {}).items():
            normalized = self._normalize_api_profile(str(profile_id), profile)
            normalized_profiles[normalized["provider"]] = normalized
        active_profile = normalized_profiles.get(provider) or self._default_api_profile(provider)
        normalized_profiles[provider] = active_profile
        return {
            "api": {
                **active_profile,
                "profiles": normalized_profiles,
            }
        }

    def _normalize_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        api_settings = dict((settings or {}).get("api") or {})
        active_provider = str(api_settings.get("provider") or "openai-compatible").strip() or "openai-compatible"
        profiles: Dict[str, Dict[str, Any]] = {}
        raw_profiles = api_settings.get("profiles")
        if isinstance(raw_profiles, dict):
            for profile_id, profile in raw_profiles.items():
                if not isinstance(profile, dict):
                    continue
                normalized = self._normalize_api_profile(str(profile_id), profile)
                profiles[normalized["provider"]] = normalized

        legacy_profile = self._normalize_api_profile(active_provider, api_settings)
        if self._api_profile_has_config(legacy_profile) or active_provider not in profiles:
            merged = {
                **profiles.get(active_provider, self._default_api_profile(active_provider)),
                **legacy_profile,
            }
            profiles[active_provider] = self._normalize_api_profile(active_provider, merged)
        normalized = self._settings_from_active_profile(active_provider, profiles)
        if isinstance((settings or {}).get("deployment"), dict):
            normalized["deployment"] = dict((settings or {}).get("deployment") or {})
        return normalized

    def _public_settings(self) -> Dict[str, Any]:
        api_settings = self.settings.get("api") or {}
        provider = str(api_settings.get("provider") or "openai-compatible").strip()
        raw_profiles = api_settings.get("profiles") if isinstance(api_settings.get("profiles"), dict) else {}
        public_profiles = {
            profile_id: self._public_api_profile(profile)
            for profile_id, profile in raw_profiles.items()
        }
        active_public = self._public_api_profile(api_settings)
        active_public["profiles"] = public_profiles
        return {
            "api": active_public,
            "deployment": self._deployment_status(),
        }

    def _public_api_profile(self, api_settings: Dict[str, Any]) -> Dict[str, Any]:
        provider = str(api_settings.get("provider") or "openai-compatible").strip()
        return {
            "enabled": bool(api_settings.get("enabled", False)),
            "provider": provider,
            "base_url": api_settings.get("base_url") or "",
            "model": api_settings.get("model") or "",
            "api_key_set": self._api_key_is_set(api_settings),
            "api_key_masked": self._mask_api_key(api_settings.get("api_key") or ""),
            "access_key_set": self._access_key_is_set(api_settings),
            "access_key_masked": self._mask_api_key(api_settings.get("access_key") or ""),
            "secret_key_set": self._secret_key_is_set(api_settings),
            "secret_key_masked": self._mask_api_key(api_settings.get("secret_key") or ""),
            "auth_configured": self._external_api_auth_is_set(provider, api_settings),
            "last_test": self._public_api_last_test(provider, api_settings),
        }

    def _public_api_last_test(self, provider: str, api_settings: Dict[str, Any]) -> Dict[str, Any]:
        stored = dict(api_settings.get("last_test") or {}) if isinstance(api_settings.get("last_test"), dict) else {}
        missing = []
        if not api_settings.get("enabled"):
            missing.append("启用")
        if not str(provider or "").strip():
            missing.append("服务商")
        if not str(api_settings.get("base_url") or "").strip():
            missing.append("Base URL")
        if not str(api_settings.get("model") or "").strip():
            missing.append("模型")
        if not self._external_api_auth_is_set(provider, api_settings):
            missing.append("API Key 或 Access Key + Secret Key" if provider == "kling" else "API Key")

        base_url = str(api_settings.get("base_url") or "").strip()
        invalid_url = bool(base_url) and not base_url.startswith(("http://", "https://"))
        ok = not missing and not invalid_url
        if invalid_url:
            message = "Base URL 必须以 http:// 或 https:// 开头"
            local_status = "invalid"
        elif missing:
            message = f"缺少：{'、'.join(missing)}"
            local_status = "incomplete"
        else:
            message = "本地配置完整；未发起真实生成请求"
            local_status = "ready"

        provider_status = self._provider_status(provider) if provider else {}
        remote_status = str(provider_status.get("remote_status") or "not_configured")
        if ok and remote_status == "passed":
            success = provider_status.get("last_success") or {}
            message = f"本地配置完整；最近真实生成通过：{success.get('id') or 'unknown'} · {success.get('size') or '未知尺寸'}"
        elif ok and remote_status == "failed":
            message = f"本地配置完整；但最近远端失败：{provider_status.get('note') or '请查看 Provider 健康'}"
        elif ok and remote_status == "untested":
            message = "本地配置完整；尚未产生真实生成通过记录"

        return {
            **stored,
            "ok": ok,
            "status": local_status,
            "scope": "local_config",
            "provider": provider,
            "message": message,
            "remote_status": remote_status,
            "remote_label": provider_status.get("remote_label") or "",
            "remote_note": provider_status.get("note") or "",
            "last_success": provider_status.get("last_success"),
            "last_failure": provider_status.get("last_failure"),
            "checked_at": stored.get("checked_at") or datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }

    def _update_api_settings(self, body: Dict[str, Any]) -> Dict[str, Any]:
        current_root = self._normalize_settings(self.settings).get("api", {})
        profiles = dict(current_root.get("profiles") or {})
        incoming = body.get("api") if isinstance(body.get("api"), dict) else body
        incoming = incoming or {}
        provider = str(incoming.get("provider") or current_root.get("provider") or "openai-compatible").strip()
        current = profiles.get(provider) or self._default_api_profile(provider)
        api_key = current.get("api_key") or ""
        if incoming.get("clear_api_key") is True:
            api_key = ""
        elif "api_key" in incoming and str(incoming.get("api_key") or "").strip():
            api_key = str(incoming.get("api_key") or "").strip()
        access_key = current.get("access_key") or ""
        if incoming.get("clear_access_key") is True:
            access_key = ""
        elif "access_key" in incoming and str(incoming.get("access_key") or "").strip():
            access_key = str(incoming.get("access_key") or "").strip()
        secret_key = current.get("secret_key") or ""
        if incoming.get("clear_secret_key") is True:
            secret_key = ""
        elif "secret_key" in incoming and str(incoming.get("secret_key") or "").strip():
            secret_key = str(incoming.get("secret_key") or "").strip()
        api_settings = {
            "enabled": bool(incoming.get("enabled")) if "enabled" in incoming else bool(current.get("enabled", False)),
            "provider": provider,
            "base_url": str(
                (incoming.get("base_url") if "base_url" in incoming else current.get("base_url")) or ""
            ).strip().rstrip("/"),
            "model": str((incoming.get("model") if "model" in incoming else current.get("model")) or "").strip(),
            "api_key": api_key,
            "access_key": access_key,
            "secret_key": secret_key,
            "last_test": current.get("last_test"),
        }
        profiles[provider] = self._normalize_api_profile(provider, api_settings)
        updated = self._settings_from_active_profile(provider, profiles)
        if isinstance(self.settings.get("deployment"), dict):
            updated["deployment"] = dict(self.settings.get("deployment") or {})
        return updated

    def _test_api_settings(self) -> Dict[str, Any]:
        api_settings = self.settings.get("api") or {}
        missing = []
        if not api_settings.get("enabled"):
            missing.append("启用")
        if not str(api_settings.get("provider") or "").strip():
            missing.append("服务商")
        if not str(api_settings.get("base_url") or "").strip():
            missing.append("Base URL")
        if not str(api_settings.get("model") or "").strip():
            missing.append("模型")
        provider = str(api_settings.get("provider") or "").strip()
        if not self._external_api_auth_is_set(provider):
            if provider == "kling":
                missing.append("API Key 或 Access Key + Secret Key")
            else:
                missing.append("API Key")

        base_url = str(api_settings.get("base_url") or "").strip()
        invalid_url = bool(base_url) and not base_url.startswith(("http://", "https://"))
        ok = not missing and not invalid_url
        if invalid_url:
            message = "Base URL 必须以 http:// 或 https:// 开头"
            status = "invalid"
        elif missing:
            message = f"缺少：{'、'.join(missing)}"
            status = "incomplete"
        else:
            message = "本地配置完整；未发起真实生成请求"
            status = "ready"
        provider_status = self._provider_status(provider) if provider else {}
        remote_status = str(provider_status.get("remote_status") or "not_configured")
        if ok and remote_status == "passed":
            success = provider_status.get("last_success") or {}
            message = f"本地配置完整；最近真实生成通过：{success.get('id') or 'unknown'} · {success.get('size') or '未知尺寸'}"
        elif ok and remote_status == "failed":
            message = f"本地配置完整；但最近远端失败：{provider_status.get('note') or '请查看 Provider 健康'}"
        elif ok and remote_status == "untested":
            message = "本地配置完整；尚未产生真实生成通过记录"
        return {
            "ok": ok,
            "status": status,
            "scope": "local_config",
            "provider": provider,
            "message": message,
            "remote_status": remote_status,
            "remote_label": provider_status.get("remote_label") or "",
            "remote_note": provider_status.get("note") or "",
            "last_success": provider_status.get("last_success"),
            "last_failure": provider_status.get("last_failure"),
            "checked_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        }

    def _set_active_api_last_test(self, result: Dict[str, Any]) -> None:
        api_settings = self.settings.setdefault("api", {})
        provider = str(api_settings.get("provider") or "openai-compatible").strip()
        api_settings["last_test"] = result
        profiles = api_settings.setdefault("profiles", {})
        if isinstance(profiles, dict):
            profile = profiles.setdefault(provider, self._default_api_profile(provider))
            profile["last_test"] = result

    def _api_key_is_set(self, api_settings: Optional[Dict[str, Any]] = None) -> bool:
        api_settings = api_settings or (self.settings.get("api") or {})
        return bool(str(api_settings.get("api_key") or "").strip())

    def _access_key_is_set(self, api_settings: Optional[Dict[str, Any]] = None) -> bool:
        api_settings = api_settings or (self.settings.get("api") or {})
        return bool(str(api_settings.get("access_key") or "").strip())

    def _secret_key_is_set(self, api_settings: Optional[Dict[str, Any]] = None) -> bool:
        api_settings = api_settings or (self.settings.get("api") or {})
        return bool(str(api_settings.get("secret_key") or "").strip())

    def _kling_auth_is_set(self, api_settings: Optional[Dict[str, Any]] = None) -> bool:
        return self._api_key_is_set(api_settings) or (
            self._access_key_is_set(api_settings) and self._secret_key_is_set(api_settings)
        )

    def _external_api_auth_is_set(self, provider: str, api_settings: Optional[Dict[str, Any]] = None) -> bool:
        return self._kling_auth_is_set(api_settings) if provider == "kling" else self._api_key_is_set(api_settings)

    def _configured_external_api_auth_is_set(self) -> bool:
        provider = str((self.settings.get("api") or {}).get("provider") or "").strip()
        return self._external_api_auth_is_set(provider)

    def _kling_auth_candidates(self, api_settings: Optional[Dict[str, Any]] = None) -> list[Dict[str, str]]:
        api_settings = api_settings or (self.settings.get("api") or {})
        access_key = str(api_settings.get("access_key") or "").strip()
        secret_key = str(api_settings.get("secret_key") or "").strip()
        api_key = str(api_settings.get("api_key") or "").strip()
        candidates: list[Dict[str, str]] = []
        if access_key and secret_key:
            candidates.append({"mode": "ak_sk_jwt", "token": self._kling_jwt_token(access_key, secret_key)})
        if api_key:
            candidates.append({"mode": "api_key", "token": api_key})
        return candidates

    def _kling_jwt_token(self, access_key: str, secret_key: str) -> str:
        now = int(time.time())
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {"iss": access_key, "exp": now + 1800, "nbf": now - 5}
        signing_input = ".".join([
            self._base64url_json(header),
            self._base64url_json(payload),
        ])
        signature = hmac.new(secret_key.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
        return f"{signing_input}.{self._base64url_bytes(signature)}"

    def _base64url_json(self, value: Dict[str, Any]) -> str:
        return self._base64url_bytes(json.dumps(value, separators=(",", ":")).encode("utf-8"))

    def _base64url_bytes(self, value: bytes) -> str:
        return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")

    def _mask_api_key(self, api_key: str) -> str:
        if not api_key:
            return ""
        if len(api_key) <= 8:
            return "••••"
        return f"{api_key[:4]}••••{api_key[-4:]}"

    def _default_prompt(self, character_id: str) -> str:
        prompts = {
            "lina": "一个年轻的亚洲女性，柔和的自然光，户外公园，微风吹动头发，清新自然的氛围，写实摄影风格，50mm 镜头，浅景深",
            "kira": "动漫风格角色，清晨街角，柔和轮廓光，轻微微笑，干净饱和色彩，半身构图",
            "alex": "商业广告模特，极简摄影棚，品牌大片质感，受控主光，中景构图，清晰面部结构",
        }
        return prompts.get(character_id, "consistent character portrait, identity locked, production ready lighting")


def create_handler(app: PersonaStudioApp):
    class PersonaStudioHandler(BaseHTTPRequestHandler):
        server_version = "PersonaStudio/0.1"

        def do_GET(self):
            if self.path.startswith("/api/"):
                self._send_json(*app.api_response("GET", urlparse(self.path).path))
                return
            status, content, content_type = app.static_response(self.path)
            self._send_bytes(status, content, content_type)

        def do_HEAD(self):
            self.do_GET()

        def do_POST(self):
            payload = self._read_json()
            self._send_json(*app.api_response("POST", urlparse(self.path).path, payload))

        def do_DELETE(self):
            self._send_json(*app.api_response("DELETE", urlparse(self.path).path))

        def log_message(self, format, *args):
            return

        def _read_json(self):
            length = int(self.headers.get("Content-Length") or 0)
            if length == 0:
                return {}
            raw = self.rfile.read(length)
            if not raw:
                return {}
            return json.loads(raw.decode("utf-8"))

        def _send_json(self, status: int, payload: Dict[str, Any]):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self._send_bytes(status, body, "application/json; charset=utf-8")

        def _send_bytes(self, status: int, content: bytes, content_type: str):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(content)

    return PersonaStudioHandler


def run(host: str = "127.0.0.1", port: int = 8787, data_path: Optional[Path] = None):
    app = PersonaStudioApp(data_path=data_path or Path("data/persona_studio_state.json"))
    server = ThreadingHTTPServer((host, port), create_handler(app))
    print(f"Persona Studio running at http://{host}:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nPersona Studio stopped.")
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description="Run the Persona Studio demo server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8787, type=int)
    parser.add_argument("--data-path", default="data/persona_studio_state.json")
    args = parser.parse_args()
    run(args.host, args.port, Path(args.data_path))


if __name__ == "__main__":
    main()
