import base64
import io
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error
from urllib.parse import quote

from persona_studio.server import PersonaStudioApp


def test_api_health_and_characters():
    app = PersonaStudioApp()

    status, health = app.api_response("GET", "/api/health")
    list_status, characters = app.api_response("GET", "/api/characters")
    lora_status, loras = app.api_response("GET", "/api/loras")

    assert status == 200
    assert health["ok"] is True
    assert list_status == 200
    assert lora_status == 200
    assert {lora["id"] for lora in loras["loras"]} >= {"portrait-consistency", "anime-clean-line"}
    assert {character["id"] for character in characters["characters"]} >= {"lina", "kira", "alex"}
    assert characters["characters"][0]["identity"]["reference_count"] == 3
    assert characters["characters"][0]["prompt"]
    assert characters["characters"][0]["style"]["lora"]["id"]


def test_api_settings_save_mask_test_and_persist(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    save_status, save_response = app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "openai-compatible",
                "base_url": "https://example.test/v1/",
                "model": "image-model",
                "api_key": "example-test-key",
            }
        },
    )
    test_status, test_response = app.api_response("POST", "/api/settings/test")
    reloaded = PersonaStudioApp(data_path=data_path)
    get_status, get_response = reloaded.api_response("GET", "/api/settings")

    assert save_status == 200
    assert save_response["settings"]["api"]["api_key_set"] is True
    assert save_response["settings"]["api"]["api_key_masked"] == "sk-p••••7890"
    assert save_response["settings"]["api"]["base_url"] == "https://example.test/v1"
    assert test_status == 200
    assert test_response["test"]["ok"] is True
    assert test_response["test"]["status"] == "ready"
    assert test_response["test"]["scope"] == "local_config"
    assert test_response["test"]["provider"] == "openai-compatible"
    assert test_response["test"]["remote_status"] == "untested"
    assert get_status == 200
    assert get_response["settings"]["api"]["api_key_set"] is True
    assert get_response["settings"]["api"]["api_key_masked"] == "sk-p••••7890"
    assert "example-test-key" not in str(get_response)


def test_api_settings_keep_provider_profiles_for_rotation(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=data_path)

    app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "wanx",
                "base_url": "https://dashscope.aliyuncs.com/api/v1",
                "model": "wan2.6-t2i",
                "api_key": "dashscope-secret",
            }
        },
    )
    app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "kling",
                "base_url": "https://api-singapore.klingai.com",
                "model": "kling-v3",
                "access_key": "kling-ak-test",
                "secret_key": "kling-sk-secret",
            }
        },
    )
    switch_status, switch_response = app.api_response(
        "POST",
        "/api/settings",
        {"api": {"enabled": True, "provider": "wanx"}},
    )
    reloaded = PersonaStudioApp(static_dir=Path("prototype"), data_path=data_path)
    get_status, get_response = reloaded.api_response("GET", "/api/settings")
    captured = {"auth": None, "payload": None}

    def fake_urlopen(request, timeout=120):
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        if "/services/aigc/multimodal-generation/generation" in url:
            captured["auth"] = request.headers.get("Authorization")
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            body = json.dumps({"output": {"choices": [{"message": {"content": [{"image": "https://example.test/wanx.png"}]}}]}}).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        response = MagicMock()
        response.read.return_value = b"\x89PNG\r\n\x1a\n"
        response.headers.get_content_type.return_value = "image/png"
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *args: None
        return response

    with patch("persona_studio.server.urllib.request.urlopen", side_effect=fake_urlopen):
        create_status, create_response = reloaded.api_response(
            "POST",
            "/api/generations",
            {
                "character_id": "lina",
                "mode": "文生图",
                "prompt": "a clean product still life",
                "negative_prompt": "people, face",
                "count": 1,
                "size": "1:1",
            },
        )

    profiles = get_response["settings"]["api"]["profiles"]
    generation = create_response["generations"][0]
    assert switch_status == 200
    assert switch_response["settings"]["api"]["provider"] == "wanx"
    assert switch_response["settings"]["api"]["api_key_set"] is True
    assert get_status == 200
    assert profiles["wanx"]["api_key_set"] is True
    assert profiles["kling"]["access_key_set"] is True
    assert profiles["kling"]["secret_key_set"] is True
    assert "dashscope-secret" not in json.dumps(get_response, ensure_ascii=False)
    assert "kling-sk-secret" not in json.dumps(get_response, ensure_ascii=False)
    assert create_status == 201
    assert captured["auth"] == "Bearer dashscope-secret"
    assert captured["payload"]["model"] == "wan2.6-t2i"
    assert generation["model_route"]["provider"] == "wanx"
    assert generation["model_route"]["real_generation"] is True


def test_kling_settings_accept_ak_sk_without_leaking_secret(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    save_status, save_response = app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "kling",
                "base_url": "https://api-singapore.klingai.com",
                "model": "kling-v3",
                "access_key": "ak-test-public",
                "secret_key": "sk-test-secret",
            }
        },
    )
    test_status, test_response = app.api_response("POST", "/api/settings/test")
    reloaded = PersonaStudioApp(data_path=data_path)
    get_status, get_response = reloaded.api_response("GET", "/api/settings")

    assert save_status == 200
    assert save_response["settings"]["api"]["api_key_set"] is False
    assert save_response["settings"]["api"]["access_key_set"] is True
    assert save_response["settings"]["api"]["secret_key_set"] is True
    assert save_response["settings"]["api"]["auth_configured"] is True
    assert test_status == 200
    assert test_response["test"]["ok"] is True
    assert test_response["test"]["scope"] == "local_config"
    assert test_response["test"]["provider"] == "kling"
    assert test_response["test"]["remote_status"] == "untested"
    assert get_status == 200
    assert get_response["settings"]["api"]["auth_configured"] is True
    assert "ak-test-public" not in str(get_response)
    assert "sk-test-secret" not in str(get_response)
    assert app._image_model_label("kling-v3") == "可灵 AI · Kling v3"
    assert app._image_model_label("kling/kling-v3-omni-image-generation") == "可灵 AI · Kling v3"


def test_api_settings_test_reports_existing_remote_failure_without_calling_provider(tmp_path):
    app = PersonaStudioApp(data_path=tmp_path / "state.json")
    app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "kling",
                "base_url": "https://api-singapore.klingai.com",
                "model": "kling-v3",
                "access_key": "ak-test-public",
                "secret_key": "sk-test-secret",
            }
        },
    )
    app.generation_jobs.append(
        {
            "id": "job-failed",
            "status": "failed",
            "image_model": "kling-v3",
            "size": "1:1",
            "model_route": {"provider": "kling"},
            "completed_at": "2026-06-18T00:00:00Z",
            "error": '可灵创建任务失败：HTTP 401 {"code":1002,"message":"access key not found"}',
        }
    )

    test_status, test_response = app.api_response("POST", "/api/settings/test")
    get_status, get_response = app.api_response("GET", "/api/settings")

    assert test_status == 200
    assert test_response["test"]["ok"] is True
    assert test_response["test"]["status"] == "ready"
    assert test_response["test"]["scope"] == "local_config"
    assert test_response["test"]["remote_status"] == "failed"
    assert test_response["test"]["last_failure"]["id"] == "job-failed"
    assert "最近远端失败" in test_response["test"]["message"]
    assert "access key not found" in test_response["test"]["message"]
    assert get_status == 200
    assert get_response["settings"]["api"]["last_test"]["remote_status"] == "failed"
    assert "sk-test-secret" not in json.dumps(get_response, ensure_ascii=False)


def test_public_settings_refreshes_stale_provider_remote_status(tmp_path):
    app = PersonaStudioApp(data_path=tmp_path / "state.json")
    app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "wanx",
                "base_url": "https://dashscope.aliyuncs.com/api/v1",
                "model": "wan2.6-t2i",
                "api_key": "sk-wanx-stale-status",
            }
        },
    )
    app.settings["api"]["last_test"] = {
        "ok": True,
        "status": "ready",
        "scope": "local_config",
        "provider": "wanx",
        "message": "本地配置完整；最近真实生成通过：gen-old · 9:16",
        "remote_status": "passed",
        "last_success": {"id": "gen-old"},
        "checked_at": "2026-06-18T00:00:00Z",
    }
    app.generation_jobs.append(
        {
            "id": "job-new-wanx-failed",
            "status": "failed",
            "image_model": "wan2.6-t2i",
            "size": "9:16",
            "model_route": {"provider": "wanx"},
            "completed_at": "2099-01-01T00:00:00Z",
            "error": '通义万象生成失败：HTTP 401 {"code":"InvalidApiKey"}',
        }
    )

    status, response = app.api_response("GET", "/api/settings")
    last_test = response["settings"]["api"]["last_test"]

    assert status == 200
    assert last_test["remote_status"] == "failed"
    assert last_test["last_failure"]["id"] == "job-new-wanx-failed"
    assert "最近远端失败" in last_test["message"]
    assert "sk-wanx-stale-status" not in json.dumps(response, ensure_ascii=False)


def test_api_condition_uses_requested_weights():
    app = PersonaStudioApp()

    status, response = app.api_response(
        "POST",
        "/api/characters/lina/condition",
        {
            "prompt": "walking in morning light",
            "state": "calm",
            "identity_weight": 0.82,
            "style_weight": 0.58,
            "lora_id": "soft-daylight-pro",
            "lora_weight": 0.57,
        },
    )

    assert status == 200
    conditioning = response["conditioning"]
    assert conditioning["weights"]["identity"] == 0.82
    assert conditioning["weights"]["style"] == 0.58
    assert conditioning["identity_priority"] is True
    assert conditioning["lora"]["id"] == "soft-daylight-pro"
    assert conditioning["lora"]["weight"] == 0.57
    assert conditioning["diagnostics"]["identity_margin"] == 0.24
    assert conditioning["diagnostics"]["drift_risk"] == "low"
    assert conditioning["diagnostics"]["controlnet_summary"]["face_lock"] == 0.82
    assert conditioning["diagnostics"]["lora_summary"]["id"] == "soft-daylight-pro"
    assert any(check["id"] == "identity_margin" and check["status"] == "pass" for check in conditioning["diagnostics"]["checks"])
    assert conditioning["vector_dim"] == 512


def test_api_condition_rejects_drifty_weights():
    app = PersonaStudioApp()

    status, response = app.api_response(
        "POST",
        "/api/characters/lina/condition",
        {
            "prompt": "walking in morning light",
            "identity_weight": 0.4,
            "style_weight": 0.8,
        },
    )

    assert status == 400
    assert "Identity weight must be higher" in response["error"]


def test_api_style_preview_serializes_style_assets():
    app = PersonaStudioApp()

    library_status, library_response = app.api_response("GET", "/api/styles")
    preview_status, preview_response = app.api_response(
        "POST",
        "/api/styles/preview",
        {
            "preset": "commercial",
            "prompt": "commercial brand campaign studio key light",
            "lora_id": "brand-campaign",
            "lora_weight": 0.61,
        },
    )

    assert library_status == 200
    assert {preset["id"] for preset in library_response["presets"]} >= {"cinematic", "anime", "commercial"}
    assert any(lora["id"] == "brand-campaign" for lora in library_response["loras"])
    assert preview_status == 200
    style = preview_response["style"]
    assert style["preset"] == "commercial"
    assert style["lora"]["id"] == "brand-campaign"
    assert style["lora"]["weight"] == 0.61
    assert style["vector_dim"] == 256
    assert len(style["vector_preview"]) == 8
    assert style["controls"]["lighting"] == "controlled studio key light"
    assert any(row["id"] == "camera_language" for row in style["control_rows"])


def test_api_character_edit_updates_profile_summary_and_persists(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)
    original_version_count = len(app.manager.get_character("lina")["versions"])

    status, response = app.api_response(
        "POST",
        "/api/characters/lina",
        {
            "name": "Lina Pro",
            "prompt": "Lina Pro commercial campaign portrait, identity locked",
            "tags": "商业,广告,商业",
            "style": {
                "preset": "commercial",
                "prompt": "commercial studio key light brand campaign",
                "lora_id": "brand-campaign",
                "lora_weight": 0.61,
            },
        },
    )
    reloaded = PersonaStudioApp(data_path=data_path)
    get_status, get_response = reloaded.api_response("GET", "/api/characters/lina")

    assert status == 200
    character = response["character"]
    assert character["name"] == "Lina Pro"
    assert character["prompt"] == "Lina Pro commercial campaign portrait, identity locked"
    assert character["tags"] == ["商业", "广告"]
    assert character["style"]["preset"] == "commercial"
    assert character["style"]["lora"]["id"] == "brand-campaign"
    assert character["style"]["lora"]["weight"] == 0.61
    assert character["asset_summary"]["version_count"] == original_version_count
    assert character["asset_summary"]["generation_count"] >= 4
    assert character["asset_summary"]["last_used_at"]
    assert get_status == 200
    assert get_response["character"]["name"] == "Lina Pro"
    assert get_response["character"]["tags"] == ["商业", "广告"]
    assert get_response["character"]["style"]["lora"]["id"] == "brand-campaign"


def test_api_scene_updates_character_memory(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    status, response = app.api_response(
        "POST",
        "/api/characters/lina/scene",
        {
            "prompt": "new studio pose",
            "pose": "three-quarter",
            "success_score": 0.99,
            "style": "commercial",
            "state": "confident",
        },
    )

    assert status == 201
    assert response["entry"]["success_score"] == 0.99
    assert response["character"]["memory"]["best_angles"][0]["pose"] == "three-quarter"
    assert response["character"]["memory_insights"]["best_angles"][0]["pose"] == "three-quarter"
    assert response["entries"][0]["prompt"] == "new studio pose"
    assert response["entries"][0]["pose_label"] == "四分之三侧脸"
    assert response["entries"][0]["score_percent"] == 99
    assert response["entries"][0]["source"] == "manual-scene"

    memory_status, memory_response = app.api_response("GET", "/api/characters/lina/memory")
    memory_id = memory_response["entries"][0]["id"]
    delete_status, delete_response = app.api_response("DELETE", f"/api/characters/lina/memory/{memory_id}")
    reloaded = PersonaStudioApp(data_path=data_path)
    reloaded_status, reloaded_response = reloaded.api_response("GET", "/api/characters/lina/memory")

    assert memory_status == 200
    assert memory_response["entries"][0]["id"] == memory_id
    assert memory_response["insights"]["best_angles"][0]["pose"] == "three-quarter"
    assert delete_status == 200
    assert delete_response["deleted"]["id"] == memory_id
    assert all(entry["id"] != memory_id for entry in delete_response["entries"])
    assert reloaded_status == 200
    assert all(entry["id"] != memory_id for entry in reloaded_response["entries"])


def test_api_version_training_accepts_uploaded_reference_paths(tmp_path):
    upload_dir = tmp_path / "assets" / "uploads"
    upload_dir.mkdir(parents=True)
    for index in range(3):
        (upload_dir / f"face-{index}.png").write_bytes(f"face-{index}".encode("utf-8"))
    app = PersonaStudioApp(static_dir=tmp_path)

    status, response = app.api_response(
        "POST",
        "/api/characters/lina/versions",
        {
            "note": "reference upload training",
            "face_images": [
                "assets/uploads/face-0.png",
                "assets/uploads/face-1.png",
                "assets/uploads/face-2.png",
            ],
        },
    )

    assert status == 201
    assert response["version"]["version"] == 2
    assert response["version"]["identity_reference_count"] == 3
    assert response["character"]["identity"]["reference_count"] == 3
    assert response["character"]["version"] == 2


def test_character_reference_assets_sync_train_and_persist(tmp_path):
    data_path = tmp_path / "state.json"
    static_dir = tmp_path / "static"
    upload_dir = static_dir / "assets" / "uploads"
    upload_dir.mkdir(parents=True)
    for index in range(3):
        (upload_dir / f"face-{index}.png").write_bytes(f"face-{index}".encode("utf-8"))
    app = PersonaStudioApp(static_dir=static_dir, data_path=data_path)

    get_status, get_response = app.api_response("GET", "/api/characters/lina")
    original_version = get_response["character"]["version"]
    status, response = app.api_response(
        "POST",
        "/api/characters/lina/references",
        {
            "train": True,
            "note": "reference asset sync test",
            "references": [
                {"id": "main", "label": "主图", "image": "assets/uploads/face-0.png", "active": True},
                {"id": "side", "label": "侧脸", "image": "assets/uploads/face-1.png"},
                {"id": "studio", "label": "棚拍", "image": "assets/uploads/face-2.png"},
            ],
        },
    )
    reloaded = PersonaStudioApp(static_dir=static_dir, data_path=data_path)
    reload_status, reload_response = reloaded.api_response("GET", "/api/characters/lina")

    assert get_status == 200
    assert len(get_response["character"]["reference_assets"]) >= 3
    assert status == 200
    assert response["training_status"] == "trained"
    assert response["version"]["version"] == original_version + 1
    assert response["character"]["reference_assets"][0]["id"] == "main"
    assert response["character"]["asset_summary"]["reference_count"] == 3
    assert reload_status == 200
    assert reload_response["character"]["reference_assets"][1]["image"] == "assets/uploads/face-1.png"
    assert reload_response["character"]["version"] == original_version + 1


def test_character_reference_assets_save_without_training_when_under_minimum(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)
    original_version = app.manager.get_character("lina")["version"]

    status, response = app.api_response(
        "POST",
        "/api/characters/lina/references",
        {
            "train": True,
            "references": [
                {"id": "main", "label": "主图", "image": "assets/persona-ref-1.png", "active": True},
                {"id": "side", "label": "侧脸", "image": "assets/persona-ref-2.png"},
            ],
        },
    )

    assert status == 200
    assert response["training_status"] == "needs_three_references"
    assert response["version"] is None
    assert response["character"]["version"] == original_version
    assert response["character"]["asset_summary"]["reference_count"] == 2
    assert response["character"]["identity_readiness"]["status"] == "incomplete"
    assert response["character"]["identity_readiness"]["can_train"] is False


def test_identity_readiness_flags_duplicate_reference_assets(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    status, response = app.api_response(
        "POST",
        "/api/characters/lina/references",
        {
            "references": [
                {"id": "main", "label": "主图", "image": "assets/persona-ref-1.png", "active": True},
                {"id": "copy", "label": "重复", "image": "assets/persona-ref-1.png"},
                {"id": "side", "label": "侧脸", "image": "assets/persona-ref-2.png"},
            ],
        },
    )

    assert status == 200
    readiness = response["character"]["identity_readiness"]
    assert readiness["status"] == "review"
    assert readiness["can_train"] is True
    assert readiness["duplicate_count"] == 1
    assert next(check for check in readiness["checks"] if check["id"] == "duplicate_references")["status"] == "review"


def test_character_reference_collections_sync_and_persist(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    get_status, get_response = app.api_response("GET", "/api/characters/lina")
    status, response = app.api_response(
        "POST",
        "/api/characters/lina/reference-collections",
        {
            "kind": "outfit",
            "references": [
                {
                    "id": "qa-satin-dress",
                    "label": "缎面裙",
                    "image": "assets/persona-ref-2.png",
                    "prompt": "参考服装：浅色缎面连衣裙",
                    "active": True,
                },
                {
                    "id": "qa-cardigan",
                    "label": "针织外套",
                    "visual": "knit-cardigan",
                    "prompt": "参考服装：浅色针织外套",
                },
            ],
        },
    )
    reloaded = PersonaStudioApp(data_path=data_path)
    reload_status, reload_response = reloaded.api_response("GET", "/api/characters/lina")

    assert get_status == 200
    assert get_response["character"]["reference_collections"]["outfit"][0]["active"] is False
    assert get_response["character"]["asset_summary"]["reference_collection_count"] >= 10
    assert status == 200
    outfit = response["character"]["reference_collections"]["outfit"]
    assert [item["label"] for item in outfit] == ["缎面裙", "针织外套"]
    assert outfit[0]["image"] == "assets/persona-ref-2.png"
    assert outfit[0]["active"] is True
    assert response["collection_count"] >= 9
    assert reload_status == 200
    assert reload_response["character"]["reference_collections"]["outfit"][0]["id"] == "qa-satin-dress"
    assert reload_response["character"]["reference_collections"]["outfit"][1]["visual"] == "knit-cardigan"


def test_character_reference_collection_can_be_cleared(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    status, response = app.api_response(
        "POST",
        "/api/characters/lina/reference-collections",
        {"kind": "accessory", "references": []},
    )
    reloaded = PersonaStudioApp(data_path=data_path)
    _, reload_response = reloaded.api_response("GET", "/api/characters/lina")

    assert status == 200
    assert response["character"]["reference_collections"]["accessory"] == []
    assert reload_response["character"]["reference_collections"]["accessory"] == []


def test_api_generations_create_favorite_export_and_persist(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    create_status, create_response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "mode": "图生图",
            "prompt": "walking in morning light",
            "negative_prompt": "blurry, low quality, face drift",
            "state": "calm",
            "identity_weight": 0.82,
            "style_weight": 0.58,
            "lora_id": "portrait-consistency",
            "lora_weight": 0.72,
            "count": 2,
            "size": "3:4",
            "image_model": "flux-2-max",
            "image_model_label": "FLUX · FLUX.2 Max",
            "pose_control": {"pose": "side", "weight": 0.56},
            "reference_guidance": [
                {
                    "kind": "outfit",
                    "label": "服装",
                    "items": [{"id": "dress", "label": "缎面裙", "prompt": "参考服装：浅色缎面连衣裙"}],
                },
                {
                    "kind": "scene",
                    "label": "环境",
                    "items": [{"id": "park", "label": "公园", "prompt": "参考环境：清晨户外公园"}],
                },
            ],
        },
    )
    generation_id = create_response["generations"][0]["id"]
    favorite_status, favorite_response = app.api_response(
        "POST",
        f"/api/generations/{generation_id}/favorite",
        {"favorite": True},
    )
    export_status, export_response = app.api_response("GET", "/api/export")
    reloaded = PersonaStudioApp(data_path=data_path)
    _, generations_response = reloaded.api_response("GET", "/api/generations")

    assert create_status == 201
    assert len(create_response["generations"]) == 2
    assert create_response["generations"][0]["mode"] == "图生图"
    assert create_response["generations"][0]["drift_risk"] == "low"
    assert create_response["generations"][0]["negative_prompt"] == "blurry, low quality, face drift"
    assert create_response["generations"][0]["lora_id"] == "portrait-consistency"
    assert create_response["generations"][0]["lora_weight"] == 0.72
    assert create_response["generations"][0]["model_route"]["mode"] == "local_demo"
    assert create_response["generations"][0]["model_route"]["model"] == "flux-2-max"
    assert create_response["generations"][0]["model_route"]["label"] == "FLUX · FLUX.2 Max"
    assert create_response["generations"][0]["reference_guidance"][0]["items"][0]["label"] == "缎面裙"
    assert create_response["generations"][0]["pose"] == "side"
    assert create_response["generations"][0]["pose_label"] == "侧脸"
    assert create_response["generations"][0]["pose_control"]["pose"] == "side"
    assert create_response["generations"][0]["quality"]["status"] == "pass"
    assert create_response["generations"][0]["quality"]["match"] is True
    assert create_response["job"]["status"] == "completed"
    assert create_response["job"]["generation_ids"] == [generation["id"] for generation in create_response["generations"]]
    assert create_response["generations"][0]["job_id"] == create_response["job"]["id"]
    manifest = create_response["generations"][0]["conditioning_manifest"]
    assert manifest["uses_identity_lock"] is True
    assert manifest["identity"]["enabled"] is True
    assert manifest["controlnet"]["pose"] == "side"
    assert manifest["controlnet"]["pose_lock"] == 0.56
    assert "ControlNet 姿态约束：侧脸" in manifest["provider_prompt"]
    assert "同一角色身份锁定" in manifest["provider_prompt"]
    assert "缎面裙" in manifest["provider_prompt"]
    assert "different person" in manifest["provider_negative_prompt"]
    assert "no text" in manifest["provider_negative_prompt"]
    assert "no watermark" in manifest["provider_negative_prompt"]
    assert favorite_status == 200
    assert favorite_response["generation"]["favorite"] is True
    assert export_status == 200
    assert export_response["project"]["counts"]["favorites"] >= 1
    assert export_response["project"]["counts"]["loras"] >= 4
    assert export_response["project"]["counts"]["generation_jobs"] >= 1
    assert export_response["project"]["generation_jobs"][-1]["id"] == create_response["job"]["id"]
    assert export_response["project"]["generations"][-1]["negative_prompt"] == "blurry, low quality, face drift"
    assert export_response["project"]["generations"][-1]["mode"] == "图生图"
    assert export_response["project"]["generations"][-1]["lora_id"] == "portrait-consistency"
    assert export_response["project"]["generations"][-1]["model_route"]["model"] == "flux-2-max"
    assert export_response["project"]["generations"][-1]["reference_guidance"][1]["items"][0]["label"] == "公园"
    assert export_response["project"]["generations"][-1]["conditioning_manifest"]["prompt_hash"]
    assert export_response["project"]["generations"][-1]["quality"]["checked_by"] == "deterministic-local-quality-gate"
    assert any(generation["id"] == generation_id for generation in generations_response["generations"])
    assert generations_response["generations"][0]["negative_prompt"] == "blurry, low quality, face drift"
    assert generations_response["generations"][0]["job_id"] == create_response["job"]["id"]
    assert generations_response["generations"][0]["mode"] == "图生图"
    assert generations_response["generations"][0]["lora_id"] == "portrait-consistency"
    assert generations_response["generations"][0]["model_route"]["label"] == "FLUX · FLUX.2 Max"
    assert generations_response["generations"][0]["reference_guidance"][0]["kind"] == "outfit"
    assert generations_response["generations"][0]["conditioning_manifest"]["references"][0]["kind"] == "outfit"
    assert generations_response["generations"][0]["pose"] == "side"
    assert generations_response["generations"][0]["conditioning_manifest"]["controlnet"]["pose_label"] == "侧脸"
    assert generations_response["generations"][0]["quality"]["face_match_score"] >= 0.82


def test_generation_canvas_edit_creates_revision_with_mask(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    create_status, create_response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "mode": "文生图",
            "prompt": "Lina walking in morning light",
            "negative_prompt": "blur, face drift",
            "state": "calm",
            "identity_weight": 0.86,
            "style_weight": 0.52,
            "count": 1,
            "size": "3:4",
        },
    )
    source = create_response["generations"][0]
    edit_status, edit_response = app.api_response(
        "POST",
        f"/api/generations/{source['id']}/edit",
        {
            "instruction": "把左上角杂乱招牌去掉，保留人物脸和服装",
            "mask": {
                "canvas_width": 640,
                "canvas_height": 852,
                "strokes": [
                    {
                        "brush": 0.04,
                        "points": [{"x": 0.12, "y": 0.18}, {"x": 0.24, "y": 0.22}, {"x": 0.31, "y": 0.26}],
                    }
                ],
            },
        },
    )
    edited = edit_response["generation"]
    export_status, export_response = app.api_response("GET", "/api/export")
    reloaded = PersonaStudioApp(data_path=data_path)
    _, generations_response = reloaded.api_response("GET", "/api/generations")
    reloaded_edit = next(item for item in generations_response["generations"] if item["id"] == edited["id"])

    assert create_status == 201
    assert edit_status == 201
    assert edited["mode"] == "局部重绘"
    assert edited["parent_generation_id"] == source["id"]
    assert edited["edit_request"]["source_generation_id"] == source["id"]
    assert edited["edit_request"]["source_image"] == source["image"]
    assert edited["edit_request"]["mask"]["bounds"]["width"] > 0
    assert edited["edit_request"]["mask"]["strokes"][0]["points"][0] == {"x": 0.12, "y": 0.18}
    assert edited["reference_guidance"][0]["kind"] == "edit_source"
    assert edited["reference_guidance"][0]["items"][0]["source_generation_id"] == source["id"]
    assert edited["reference_guidance"][0]["items"][0]["mask"]["bounds"] == edited["edit_request"]["mask"]["bounds"]
    assert edited["model_route"]["mode"] == "local_demo"
    assert edited["model_route"]["model"] == "persona-local-preview"
    assert edited["model_route"]["real_generation"] is False
    assert "局部重绘约束" in edited["conditioning_manifest"]["provider_prompt"]
    assert "只修改画布标记区域" in edited["conditioning_manifest"]["provider_prompt"]
    assert edit_response["job"]["status"] == "completed"
    assert edit_response["job"]["parent_generation_id"] == source["id"]
    assert edit_response["job"]["request"]["edit_request"]["instruction"] == "把左上角杂乱招牌去掉，保留人物脸和服装"
    assert reloaded_edit["edit_request"]["mask"]["bounds"] == edited["edit_request"]["mask"]["bounds"]
    assert export_status == 200
    exported_edit = next(item for item in export_response["project"]["generations"] if item["id"] == edited["id"])
    assert exported_edit["parent_generation_id"] == source["id"]


def test_fal_canvas_edit_routes_masked_removal_to_erase(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    settings_status, _ = app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "fal",
                "base_url": "https://fal.run",
                "model": "fal-ai/flux-pro/v1.1-ultra",
                "api_key": "fal-test-secret",
            }
        },
    )
    source = {
        "id": "gen-source-edit",
        "character_id": "lina",
        "character_name": "Lina",
        "character_version": 1,
        "subject_hint": "portrait",
        "mode": "图生图",
        "prompt": "Lina portrait",
        "negative_prompt": "",
        "state": "calm",
        "size": "3:4",
        "image": "assets/persona-ref-1.png",
        "identity_weight": 0.92,
        "style_weight": 0.5,
        "model_route": {"provider": "fal", "model": "fal-ai/flux-pro/v1.1-ultra", "real_generation": True},
        "reference_guidance": [],
        "pose_control": {},
        "quality": {},
        "created_at": "2026-06-23T00:00:00Z",
    }
    app.generations.append(source)
    captured = {"url": None, "payload": None}

    def fake_urlopen(request, timeout=180):
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        if "fal-ai/flux-pro/v1/erase" in url:
            captured["url"] = url
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            body = json.dumps({"images": [{"url": "https://example.test/erased.jpg"}]}).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        body = b"\xff\xd8\xff\xe0fakejpeg"
        response = MagicMock()
        response.read.return_value = body
        response.headers.get_content_type.return_value = "image/jpeg"
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *args: None
        return response

    with patch("persona_studio.server.urllib.request.urlopen", side_effect=fake_urlopen):
        edit_status, edit_response = app.api_response(
            "POST",
            "/api/generations/gen-source-edit/edit",
            {
                "instruction": "去掉眼镜，人物不变",
                "mask": {
                    "canvas_width": 640,
                    "canvas_height": 852,
                    "strokes": [
                        {
                            "brush": 0.05,
                            "points": [{"x": 0.18, "y": 0.28}, {"x": 0.78, "y": 0.30}],
                        }
                    ],
                },
            },
        )

    edited = edit_response["generation"]
    assert settings_status == 200
    assert edit_status == 201
    assert captured["url"] == "https://fal.run/fal-ai/flux-pro/v1/erase"
    assert captured["payload"]["image_url"].startswith("data:image/")
    assert captured["payload"]["mask_url"].startswith("data:image/png;base64,")
    assert captured["payload"]["dilate_pixels"] >= 10
    assert "prompt" not in captured["payload"]
    assert "image_prompt_strength" not in captured["payload"]
    assert edited["model_route"]["model"] == "fal-ai/flux-pro/v1/erase"
    assert edited["model_route"]["real_generation"] is True
    assert edited["reference_guidance"][0]["items"][0]["mask"]["bounds"]["width"] > 0


def test_delete_source_generation_preserves_image_for_canvas_revision(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=data_path)

    _, create_response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "prompt": "revision source retention qa",
            "count": 1,
        },
    )
    source = create_response["generations"][0]
    source_image = app.static_dir / source["image"]
    _, edit_response = app.api_response(
        "POST",
        f"/api/generations/{source['id']}/edit",
        {
            "instruction": "去掉背景杂物，保留人物脸部",
            "mask": {
                "canvas_width": 640,
                "canvas_height": 852,
                "strokes": [
                    {
                        "brush": 0.04,
                        "points": [{"x": 0.12, "y": 0.18}, {"x": 0.24, "y": 0.22}],
                    }
                ],
            },
        },
    )
    edited = edit_response["generation"]

    assert source_image.exists()
    delete_status, delete_response = app.api_response("DELETE", f"/api/generations/{source['id']}")
    _, generations_response = app.api_response("GET", "/api/generations")
    surviving = next(item for item in generations_response["generations"] if item["id"] == edited["id"])

    assert delete_status == 200
    assert delete_response["deleted"]["image_removed"] is False
    assert source_image.exists()
    assert surviving["edit_request"]["source_image"] == source["image"]
    assert surviving["edit_request"]["source_generation_status"] == "deleted"
    assert surviving["reference_guidance"][0]["items"][0]["source_generation_status"] == "deleted"


def test_account_plan_persists_and_generation_charges_credits(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    account_status, account_response = app.api_response("GET", "/api/account")
    upgrade_status, upgrade_response = app.api_response("POST", "/api/account", {"plan_id": "upgrade-creator"})
    create_status, create_response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "prompt": "creator quota charge qa",
            "count": 2,
        },
    )
    reloaded = PersonaStudioApp(data_path=data_path)
    reload_status, reload_response = reloaded.api_response("GET", "/api/account")

    app.account["credits_remaining"] = 1
    app._save_assets()
    fail_status, fail_response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "prompt": "not enough credits",
            "count": 1,
        },
    )
    jobs_status, jobs_response = app.api_response("GET", "/api/generation-jobs")

    assert account_status == 200
    assert account_response["account"]["plan_id"] == "free"
    assert account_response["account"]["credits_remaining"] == 1200
    assert any(plan["id"] == "upgrade-business" for plan in account_response["plans"])
    assert upgrade_status == 200
    assert upgrade_response["account"]["plan_id"] == "upgrade-creator"
    assert upgrade_response["account"]["credits_remaining"] == 2000
    assert create_status == 201
    assert create_response["account"]["credits_remaining"] == 1996
    assert create_response["account"]["credits_used"] == 4
    assert create_response["job"]["billing"]["cost"] == 4
    assert create_response["job"]["billing"]["credits_before"] == 2000
    assert create_response["job"]["billing"]["credits_after"] == 1996
    assert create_response["job"]["billing"]["status"] == "charged"
    assert create_response["generations"][0]["billing"]["cost"] == 2
    assert reload_status == 200
    assert reload_response["account"]["credits_remaining"] == 1996
    assert reload_response["account"]["credits_used"] == 4
    assert fail_status == 400
    assert "Insufficient credits" in fail_response["error"]
    assert jobs_status == 200
    assert jobs_response["jobs"][0]["status"] == "failed"
    assert jobs_response["jobs"][0]["result_count"] == 0
    assert app.account["credits_remaining"] == 1


def test_reselecting_current_plan_does_not_refill_credits(tmp_path):
    # Regression: _update_account always reset credits to the plan's full
    # monthly quota, so a user could refill their balance to full simply by
    # re-posting their own current plan, defeating generation credit accounting.
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    app.api_response(
        "POST", "/api/generations", {"character_id": "lina", "prompt": "spend", "count": 4}
    )
    _, before = app.api_response("GET", "/api/account")
    plan_id = before["account"]["plan_id"]
    spent_remaining = before["account"]["credits_remaining"]
    assert spent_remaining < before["account"]["monthly_credits"]

    # Re-selecting the SAME plan must preserve the spent balance.
    status, same_plan = app.api_response("POST", "/api/account", {"plan_id": plan_id})
    assert status == 200
    assert same_plan["account"]["credits_remaining"] == spent_remaining
    assert same_plan["account"]["credits_used"] == before["account"]["credits_used"]

    # Switching to a DIFFERENT plan still starts a fresh monthly quota.
    _, changed = app.api_response("POST", "/api/account", {"plan_id": "upgrade-business"})
    assert changed["account"]["credits_remaining"] == changed["account"]["monthly_credits"]
    assert changed["account"]["credits_used"] == 0

    # Persisted no-refill survives a reload.
    reloaded = PersonaStudioApp(data_path=data_path)
    reloaded.api_response("POST", "/api/account", {"plan_id": plan_id})
    _, reloaded_same = reloaded.api_response("POST", "/api/account", {"plan_id": plan_id})
    assert reloaded_same["account"]["credits_remaining"] <= reloaded_same["account"]["monthly_credits"]


def test_failed_generation_job_billing_is_marked_not_charged(tmp_path):
    # Regression: a failed job kept its reserved billing record (status
    # "reserved" with a lowered credits_after), advertising a deduction that
    # never hit the account balance. Failures must reflect no charge.
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    _, before = app.api_response("GET", "/api/account")
    balance_before = before["account"]["credits_remaining"]

    # count=3 is rejected inside _create_generation_records, after the credit
    # reservation, so the job transitions running -> failed.
    status, _ = app.api_response(
        "POST", "/api/generations", {"character_id": "lina", "prompt": "x", "count": 3}
    )
    assert status == 400

    failed = [job for job in app.generation_jobs if job.get("status") == "failed"]
    assert failed, "expected a failed generation job"
    billing = failed[-1].get("billing") or {}
    assert billing.get("status") == "not_charged"
    assert billing.get("credits_after") == billing.get("credits_before")

    # The real account balance was never touched.
    _, after = app.api_response("GET", "/api/account")
    assert after["account"]["credits_remaining"] == balance_before


def test_asset_library_indexes_local_character_os_assets(tmp_path):
    app = PersonaStudioApp(data_path=tmp_path / "state.json")
    app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "openai-compatible",
                "base_url": "https://example.test/v1",
                "model": "image-model",
                "api_key": "example-fixture-0-key",
            }
        },
    )
    create_status, create_response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "prompt": "asset library smoke portrait",
            "count": 1,
        },
    )
    generation_id = create_response["generations"][0]["id"]
    app.api_response("POST", f"/api/generations/{generation_id}/favorite", {"favorite": True})
    status, response = app.api_response("GET", "/api/assets/library")
    text = json.dumps(response, ensure_ascii=False)

    items = response["items"]
    type_counts = response["summary"]
    filters = response["filters"]["types"]

    assert create_status == 201
    assert status == 200
    assert type_counts["total"] == len(items)
    assert type_counts["character"] == 3
    assert type_counts["generation"] >= 5
    assert type_counts["reference"] >= 12
    assert type_counts["memory"] >= 1
    assert type_counts["project"] >= 3
    assert type_counts["job"] >= 1
    assert any(item["type"] == "character" and item["id"] == "lina" for item in items)
    assert any(item["type"] == "generation" and item["id"] == generation_id and "favorite" in item["tags"] for item in items)
    assert any(item["type"] == "job" and item["related_id"] == generation_id for item in items)
    assert any(item["type"] == "reference" and item["character_id"] == "lina" for item in items)
    assert any(item["type"] == "memory" and item["related_id"] == generation_id for item in items)
    assert any(item["type"] == "project" and item["metrics"] for item in items)
    assert any(filter_item["id"] == "generation" and filter_item["count"] >= 5 for filter_item in filters)
    assert "asset library smoke portrait" in text
    assert "example-fixture-0-key" not in text
    assert "api_key" not in text.lower()


def test_system_readiness_reports_local_completion_without_secrets(tmp_path):
    app = PersonaStudioApp(data_path=tmp_path / "state.json")
    app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "dashscope",
                "base_url": "https://dashscope.aliyuncs.com/api/v1",
                "model": "wan2.6-image",
                "api_key": "sk-secret-readiness",
            }
        },
    )
    app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "prompt": "readiness smoke portrait",
            "count": 1,
        },
    )

    status, response = app.api_response("GET", "/api/system/readiness")
    text = json.dumps(response, ensure_ascii=False)
    modules = {module["id"]: module for module in response["modules"]}
    dependencies = {dependency["id"]: dependency for dependency in response["external_dependencies"]}

    assert status == 200
    assert response["status"] == "local_ready"
    assert response["completion_percent"] >= 99
    assert response["totals"]["characters"] == 3
    assert response["totals"]["ready_characters"] == 3
    assert response["totals"]["reference_ready_characters"] == 3
    assert response["totals"]["generations"] >= 5
    assert response["totals"]["asset_total"] >= response["totals"]["generations"]
    assert modules["identity_model"]["status"] == "ready"
    assert modules["identity_model"]["score"] == 100
    assert any("3/3 角色身份就绪" in item for item in modules["identity_model"]["evidence"])
    assert any("角色参考可训练" in item for item in modules["identity_model"]["evidence"])
    assert modules["asset_library"]["status"] == "ready"
    assert modules["generation_pipeline"]["score"] == 100
    assert modules["jobs_billing"]["score"] == 100
    assert modules["project_ip_system"]["score"] >= 88
    assert dependencies["real_generation_api"]["status"] == "configured"
    assert dependencies["real_generation_api"]["provider"] == "dashscope"
    assert dependencies["provider_live_health"]["status"] == "configured"
    assert response["provider_health"]["summary"]["configured"] >= 1
    assert "sk-secret-readiness" not in text
    assert "api_key" not in text.lower()


def test_production_identity_training_creates_artifact_without_vector_leak(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    status, response = app.api_response(
        "POST",
        "/api/identity-training/jobs",
        {
            "character_id": "alex",
            "encoder": "insightface-compatible-v1",
            "embedding_dim": 1024,
        },
    )
    character_status, character_response = app.api_response("GET", "/api/characters/alex")
    reloaded = PersonaStudioApp(data_path=data_path)
    reloaded_status, reloaded_response = reloaded.api_response("GET", "/api/identity-training/status")

    job = response["jobs"][0]
    production_identity = character_response["character"]["production_identity"]
    artifact_path = Path(production_identity["artifact_path"])
    public_text = json.dumps(character_response, ensure_ascii=False)
    artifact_text = artifact_path.read_text(encoding="utf-8")

    assert status == 201
    assert response["training"]["trained"] == 1
    assert response["training"]["status"] == "partial"
    assert job["status"] == "completed"
    assert job["encoder"] == "insightface-compatible-v1"
    assert character_status == 200
    assert production_identity["status"] == "trained"
    assert production_identity["embedding_dim"] == 1024
    assert production_identity["vector_hash"]
    assert artifact_path.exists()
    assert '"vector":' not in public_text
    assert '"vector":' not in artifact_text
    assert reloaded_status == 200
    assert reloaded_response["trained"] == 1
    assert any(item["character_id"] == "alex" for item in reloaded_response["characters"])


def test_fal_lora_training_uploads_references_and_stores_weights(tmp_path):
    # Real per-character LoRA: package references -> upload to fal storage ->
    # submit the trainer -> poll -> store the returned weights URL on the
    # character. All fal HTTP calls are mocked; no paid training runs.
    app = PersonaStudioApp(data_path=tmp_path / "state.json")
    app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "fal",
                "base_url": "https://fal.run",
                "model": "fal-ai/flux-pro/v1.1-ultra",
                "api_key": "fal-test-secret",
            }
        },
    )
    seen = {"upload": False, "submit": None, "status": False}

    def fake_urlopen(request, timeout=180):
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        if "storage/auth/token" in url:
            body = json.dumps({"token": "tok-123", "base_url": "https://cdn.fal.test"}).encode("utf-8")
        elif url == "https://cdn.fal.test/files/upload":
            seen["upload"] = True
            assert request.headers.get("Authorization") == "Bearer tok-123"
            body = json.dumps({"access_url": "https://cdn.fal.test/datasets/alex-refs.zip"}).encode("utf-8")
        elif url == "https://queue.fal.run/fal-ai/flux-lora-fast-training":
            seen["submit"] = json.loads(request.data.decode("utf-8"))
            body = json.dumps(
                {
                    "request_id": "req-1",
                    "status_url": "https://queue.fal.run/fal-ai/flux-lora-fast-training/requests/req-1/status",
                    "response_url": "https://queue.fal.run/fal-ai/flux-lora-fast-training/requests/req-1",
                }
            ).encode("utf-8")
        elif url.endswith("/requests/req-1/status"):
            seen["status"] = True
            body = json.dumps(
                {"status": "COMPLETED", "response_url": "https://queue.fal.run/fal-ai/flux-lora-fast-training/requests/req-1"}
            ).encode("utf-8")
        elif url.endswith("/requests/req-1"):
            body = json.dumps({"diffusers_lora_file": {"url": "https://fal.media/files/alex-lora.safetensors"}}).encode("utf-8")
        else:
            body = json.dumps({}).encode("utf-8")
        response = MagicMock()
        response.read.return_value = body
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *args: None
        return response

    with patch("persona_studio.server.urllib.request.urlopen", side_effect=fake_urlopen):
        status, response = app.api_response(
            "POST",
            "/api/identity-training/jobs",
            {"character_id": "alex", "train_lora": True, "lora_steps": 800},
        )

    job = response["jobs"][0]
    _, character_response = app.api_response("GET", "/api/characters/alex")
    _, training_status = app.api_response("GET", "/api/identity-training/status")
    # Source of truth that generation routing reads:
    fal_lora = app.manager.characters["alex"].get("fal_lora") or {}
    alex_status = next(c for c in training_status["characters"] if c["character_id"] == "alex")
    assert status == 201
    assert seen["upload"] is True
    assert seen["status"] is True
    assert seen["submit"]["images_data_url"] == "https://cdn.fal.test/datasets/alex-refs.zip"
    assert seen["submit"]["trigger_word"] == "alexperson"
    assert seen["submit"]["steps"] == 800
    assert job["lora_trained"] is True
    assert fal_lora["url"] == "https://fal.media/files/alex-lora.safetensors"
    assert fal_lora["trigger_word"] == "alexperson"
    assert fal_lora["status"] == "ready"
    # Training status surfaces the LoRA to the UI without leaking the weights URL.
    assert alex_status["lora"]["status"] == "ready"
    assert alex_status["lora"]["trigger_word"] == "alexperson"
    assert alex_status["lora"]["has_weights"] is True
    assert "alex-lora.safetensors" not in json.dumps(training_status, ensure_ascii=False)
    # The API key must never leak into the persisted character record.
    assert "fal-test-secret" not in json.dumps(character_response, ensure_ascii=False)


def test_fal_character_lora_generation_routes_through_flux_lora(tmp_path):
    # Once a character has a trained LoRA, a fresh (non-edit) generation must
    # route through fal-ai/flux-lora with the LoRA weights + trigger word, not
    # the plain ultra/Redux path.
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "fal",
                "base_url": "https://fal.run",
                "model": "fal-ai/flux-pro/v1.1-ultra",
                "api_key": "fal-test-secret",
            }
        },
    )
    app.manager.characters["alex"]["fal_lora"] = {
        "url": "https://fal.media/files/alex-lora.safetensors",
        "trigger_word": "alexperson",
        "scale": 0.9,
        "status": "ready",
    }
    captured = {"url": None, "payload": None}

    def fake_urlopen(request, timeout=180):
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        if "fal-ai/flux-lora" in url and "training" not in url:
            captured["url"] = url
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            body = json.dumps({"images": [{"url": "https://example.test/lora-gen.jpg"}]}).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response
        body = b"\xff\xd8\xff\xe0fakejpeg"
        response = MagicMock()
        response.read.return_value = body
        response.headers.get_content_type.return_value = "image/jpeg"
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *args: None
        return response

    with patch("persona_studio.server.urllib.request.urlopen", side_effect=fake_urlopen):
        status, resp = app.api_response(
            "POST",
            "/api/generations",
            {
                "character_id": "alex",
                "mode": "文生图",
                "prompt": "morning light studio portrait",
                "count": 1,
                "size": "3:4",
            },
        )

    gen = resp["generations"][0]
    assert status == 201
    assert captured["url"] == "https://fal.run/fal-ai/flux-lora"
    assert captured["payload"]["loras"][0]["path"] == "https://fal.media/files/alex-lora.safetensors"
    assert captured["payload"]["loras"][0]["scale"] == 0.9
    assert "alexperson" in captured["payload"]["prompt"]
    assert gen["model_route"]["model"] == "fal-ai/flux-lora"
    assert gen["model_route"]["character_lora_route"] is True
    assert gen["model_route"]["real_generation"] is True
    assert "fal-test-secret" not in json.dumps(gen, ensure_ascii=False)


def test_deployment_initialize_reports_storage_rbac_and_audit_without_secrets(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    status, deployment = app.api_response(
        "POST",
        "/api/deployment/initialize",
        {"workspace_id": "qa-commercial-prod"},
    )
    settings_status, settings_response = app.api_response("GET", "/api/settings")
    reloaded = PersonaStudioApp(data_path=data_path)
    reloaded_status, reloaded_deployment = reloaded.api_response("GET", "/api/deployment/status")

    checks = {check["id"]: check for check in deployment["checks"]}
    audit_path = Path((deployment["manifest"]["audit"] or {})["path"])
    deployment_text = json.dumps(settings_response, ensure_ascii=False)

    assert status == 200
    assert deployment["status"] == "production_local_ready"
    assert deployment["ready"] is True
    assert {"database", "object_store", "identity_artifacts", "release_artifacts", "rbac", "audit_log"} <= set(checks)
    assert all(check["status"] == "passed" for check in checks.values())
    assert deployment["manifest"]["workspace_id"] == "qa-commercial-prod"
    assert {role["id"] for role in deployment["manifest"]["rbac"]["roles"]} >= {"owner", "editor", "viewer"}
    assert audit_path.exists()
    assert "deployment.initialized" in audit_path.read_text(encoding="utf-8")
    assert settings_status == 200
    assert settings_response["settings"]["deployment"]["status"] == "production_local_ready"
    assert "sk-secret" not in deployment_text
    assert "secret_key\":" not in deployment_text
    assert reloaded_status == 200
    assert reloaded_deployment["ready"] is True


def test_project_release_package_marks_commercial_project_ready(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    train_status, train_response = app.api_response(
        "POST",
        "/api/identity-training/jobs",
        {"character_id": "all"},
    )
    create_status, create_response = app.api_response(
        "POST",
        "/api/projects",
        {
            "name": "Lina Commercial Release",
            "user_segment": "商业用户",
            "level": "Level 4 Visual IP System",
            "character_id": "lina",
            "channels": ["广告投放", "电商主图"],
            "deliverables": ["IP 资产包", "商业授权摘要", "发布清单"],
        },
    )
    project_id = create_response["project"]["id"]
    release_status, release_response = app.api_response("POST", f"/api/projects/{project_id}/release")
    readiness_status, readiness_response = app.api_response("GET", "/api/system/readiness")
    reloaded = PersonaStudioApp(data_path=data_path)
    get_status, get_response = reloaded.api_response("GET", f"/api/projects/{project_id}")

    release = release_response["release_package"]
    checklist = {check["id"]: check for check in release["checklist"]}
    artifact_path = Path(release["artifact_path"])
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    dependencies = {dependency["id"]: dependency for dependency in readiness_response["external_dependencies"]}

    assert train_status == 201
    assert train_response["training"]["status"] == "ready"
    assert create_status == 201
    assert release_status == 200
    assert release["status"] == "ready"
    assert release_response["project"]["status"] == "approved"
    assert release_response["project"]["review"]["release_ready"] is True
    assert release_response["project"]["ip_package"]["release_ready"] is True
    assert release_response["project"]["release_package"]["status"] == "ready"
    assert {"production_identity", "storage_rbac", "ip_package_complete", "quality_assets", "commercial_license", "release_artifact"} <= set(checklist)
    assert all(check["status"] == "passed" for check in checklist.values())
    assert artifact_path.exists()
    assert artifact["project"]["user_segment"] == "商业用户"
    assert artifact["ip_package"]["release_ready"] is False
    assert artifact["checklist"][0]["id"] == "production_identity"
    assert readiness_status == 200
    assert readiness_response["totals"]["ready_characters"] == 3
    assert readiness_response["totals"]["production_identity_trained"] == 3
    assert readiness_response["totals"]["release_ready_projects"] >= 1
    assert dependencies["production_identity_training"]["status"] == "ready"
    assert dependencies["deployment_storage"]["status"] == "production_local_ready"
    assert get_status == 200
    assert get_response["project"]["release_package"]["status"] == "ready"


def test_provider_status_reports_live_success_and_remote_failure_without_secrets(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "wanx",
                "base_url": "https://dashscope.aliyuncs.com/api/v1",
                "model": "wan2.6-t2i",
                "api_key": "example-fixture-1-key",
            }
        },
    )

    def fake_urlopen(request, timeout=120):
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        if "multimodal-generation" in url:
            body = json.dumps(
                {
                    "output": {
                        "choices": [
                            {
                                "message": {
                                    "content": [
                                        {
                                            "image": "https://example.test/provider-health.png",
                                            "type": "image",
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            ).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        response = MagicMock()
        response.read.return_value = b"\x89PNG\r\n\x1a\n"
        response.headers.get_content_type.return_value = "image/png"
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *args: None
        return response

    with patch("persona_studio.server.urllib.request.urlopen", side_effect=fake_urlopen):
        create_status, create_response = app.api_response(
            "POST",
            "/api/generations",
            {
                "character_id": "lina",
                "mode": "文生图",
                "prompt": "provider health product shot, no people",
                "count": 1,
                "size": "1:1",
                "image_model": "wan2.6-image",
            },
        )
    assert create_status == 201
    assert create_response["generations"][0]["model_route"]["provider"] == "wanx"
    assert create_response["generations"][0]["model_route"]["real_generation"] is True

    app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "kling",
                "base_url": "https://api-singapore.klingai.com",
                "model": "kling-v3",
                "api_key": "api-kling-provider-health",
            }
        },
    )
    app.generation_jobs.append(
        {
            "id": "job-kling-provider-health",
            "status": "failed",
            "image_model": "kling-v3",
            "image_model_label": "可灵 AI · Kling v3",
            "size": "1:1",
            "requested_at": "2099-01-01T00:00:00Z",
            "completed_at": "2099-01-01T00:00:01Z",
            "model_route": {"provider": "kling", "model": "kling-v3"},
            "request": {"image_model": "kling-v3"},
            "error": '可灵创建任务失败：HTTP 401 {"code":1002,"message":"access key not found"}',
        }
    )

    status, response = app.api_response("GET", "/api/providers/status")
    text = json.dumps(response, ensure_ascii=False)
    providers = {provider["provider"]: provider for provider in response["providers"]}

    assert status == 200
    assert response["summary"]["passed"] >= 1
    assert response["summary"]["failed"] >= 1
    assert providers["wanx"]["remote_status"] == "passed"
    assert providers["wanx"]["last_success"]["id"] == create_response["generations"][0]["id"]
    assert providers["kling"]["remote_status"] == "failed"
    assert providers["kling"]["last_failure"]["id"] == "job-kling-provider-health"
    assert "example-fixture-1-key" not in text
    assert "api-kling-provider-health" not in text
    assert "api_key" not in text.lower()


def test_generation_jobs_record_failures_and_retry_with_overrides(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    failed_status, failed_response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "prompt": "style-heavy portrait",
            "identity_weight": 0.5,
            "style_weight": 0.8,
            "count": 1,
        },
    )
    jobs_status, jobs_response = app.api_response("GET", "/api/generation-jobs")
    failed_job = jobs_response["jobs"][0]
    retry_status, retry_response = app.api_response(
        "POST",
        f"/api/generation-jobs/{failed_job['id']}/retry",
        {
            "identity_weight": 0.86,
            "style_weight": 0.58,
        },
    )
    reloaded = PersonaStudioApp(data_path=data_path)
    _, reloaded_jobs = reloaded.api_response("GET", "/api/generation-jobs")

    assert failed_status == 400
    assert "Identity weight must be higher" in failed_response["error"]
    assert jobs_status == 200
    assert failed_job["status"] == "failed"
    assert failed_job["generation_ids"] == []
    assert failed_job["error"]
    assert retry_status == 201
    assert retry_response["retry_of"] == failed_job["id"]
    assert retry_response["job"]["status"] == "completed"
    assert retry_response["job"]["retry_of"] == failed_job["id"]
    assert retry_response["generations"][0]["job_id"] == retry_response["job"]["id"]
    assert reloaded_jobs["jobs"][0]["status"] == "completed"
    assert reloaded_jobs["jobs"][1]["status"] == "failed"


def test_api_generation_uses_configured_external_model_route(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    settings_status, _settings_response = app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "wanx",
                "base_url": "https://api.example.test/v1",
                "model": "wan2.6-image",
                "api_key": "sk-test-secret",
            }
        },
    )
    create_status, create_response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "prompt": "cinematic portrait",
            "identity_weight": 0.85,
            "style_weight": 0.58,
            "count": 1,
            "image_model": "flux-2-max",
            "image_model_label": "FLUX · FLUX.2 Max",
        },
    )
    export_status, export_response = app.api_response("GET", "/api/export")

    generation = create_response["generations"][0]
    route = generation["model_route"]
    assert settings_status == 200
    assert create_status == 201
    assert route["mode"] == "external_api"
    assert route["provider"] == "wanx"
    assert route["provider_label"] == "通义万象"
    assert route["model"] == "wan2.6-image"
    assert route["request_model"] == "flux-2-max"
    assert route["base_url"] == "https://api.example.test/v1"
    assert route["real_generation"] is False
    assert "sk-test-secret" not in str(generation)
    assert export_status == 200
    assert export_response["project"]["generations"][-1]["model_route"]["mode"] == "external_api"
    assert "sk-test-secret" not in str(export_response)


def test_generation_route_prefers_requested_model_profile_over_active_provider(tmp_path):
    app = PersonaStudioApp(data_path=tmp_path / "state.json")

    app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "wanx",
                "base_url": "https://api.example.test/v1",
                "model": "wan2.6-t2i",
                "api_key": "sk-wanx-secret",
            }
        },
    )
    app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "kling",
                "base_url": "https://api-singapore.klingai.com",
                "model": "kling-v3",
                "api_key": "api-kling-secret",
            }
        },
    )

    create_status, create_response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "prompt": "product photo",
            "identity_weight": 0.85,
            "style_weight": 0.58,
            "count": 1,
            "image_model": "wan2.6-image",
            "image_model_label": "通义万象 · Wan2.6 Image",
            "size": "9:16",
        },
    )

    route = create_response["generations"][0]["model_route"]
    assert create_status == 201
    assert route["mode"] == "external_api"
    assert route["provider"] == "wanx"
    assert route["model"] == "wan2.6-t2i"
    assert route["request_model"] == "wan2.6-image"
    assert route["base_url"] == "https://api.example.test/v1"
    assert route["real_generation"] is False
    assert "api-kling-secret" not in str(create_response)
    assert "sk-wanx-secret" not in str(create_response)


def test_local_generation_preview_respects_non_female_prompt_subject(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")

    car_status, car_response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "prompt": "一辆红色跑车在城市街道上，商业广告摄影",
            "count": 1,
        },
    )
    male_status, male_response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "prompt": "一个成年男性在办公室，写实摄影",
            "count": 1,
        },
    )

    assert car_status == 201
    assert male_status == 201
    car_image = car_response["generations"][0]["image"]
    male_image = male_response["generations"][0]["image"]
    assert car_response["generations"][0]["subject_hint"] == "car"
    assert male_response["generations"][0]["subject_hint"] == "male"
    assert car_response["generations"][0]["conditioning_manifest"]["uses_identity_lock"] is False
    assert car_response["generations"][0]["conditioning_manifest"]["identity"]["reason"] == "prompt_subject_overrides_character_lock"
    assert "同一角色身份锁定" not in car_response["generations"][0]["conditioning_manifest"]["provider_prompt"]
    assert car_image.startswith("assets/generated/gen-")
    assert male_image.startswith("assets/generated/gen-")

    _, car_svg, _ = app.static_response("/" + car_image)
    _, male_svg, _ = app.static_response("/" + male_image)
    assert "汽车主体".encode("utf-8") in car_svg
    assert "男性主体".encode("utf-8") in male_svg
    assert b"persona-ref-" not in car_svg
    assert b"data:image/png" not in car_svg


def test_non_character_prompt_filters_face_reference_and_identity_lora(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")

    status, response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "prompt": "保健品海参单页广告，展示商品卖点和落地页视觉，不要人物",
            "count": 1,
            "size": "9:16",
            "reference_guidance": [
                {
                    "kind": "face",
                    "label": "人脸",
                    "items": [
                        {
                            "id": "face-main",
                            "label": "主图",
                            "image": "assets/persona-ref-1.png",
                            "prompt": "保持参考人脸五官比例和脸型",
                        }
                    ],
                }
            ],
        },
    )

    generation = response["generations"][0]
    manifest = generation["conditioning_manifest"]
    _, svg, _ = app.static_response("/" + generation["image"])

    assert status == 201
    assert generation["subject_hint"] == "product"
    assert generation["size"] == "9:16"
    assert generation["drift_risk"] == "not_applicable"
    assert generation["lora_id"] is None
    assert generation["reference_guidance"] == []
    assert generation["quality"]["checked_by"] == "deterministic-local-subject-gate"
    assert manifest["uses_identity_lock"] is False
    assert manifest["references"] == []
    assert manifest["style"]["lora_id"] is None
    assert manifest["memory"]["best_angle"] is None
    assert "主体约束：生成产品" in manifest["provider_prompt"]
    assert "参考图约束" not in manifest["provider_prompt"]
    assert "人脸" not in manifest["provider_prompt"]
    assert "identity-lock" not in manifest["provider_prompt"]
    assert "portrait medium close-up" not in manifest["provider_prompt"]


def test_non_character_generation_allows_style_above_identity_when_identity_lock_skips(tmp_path):
    app = PersonaStudioApp(static_dir=tmp_path / "static", data_path=tmp_path / "state.json")
    body = {
        "character_id": "lina",
        "prompt": "保健品海参单页广告，展示商品包装、卖点和落地页视觉，不要人物",
        "count": 1,
        "size": "9:16",
        "identity_weight": 0.4,
        "style_weight": 0.8,
        "reference_guidance": [
            {
                "kind": "face",
                "label": "人脸",
                "items": [
                    {
                        "id": "face-main",
                        "label": "主图",
                        "image": "assets/persona-ref-1.png",
                        "prompt": "保持参考人脸五官比例和脸型",
                    }
                ],
            }
        ],
    }

    preflight_status, preflight_response = app.api_response("POST", "/api/generations/preflight", body)
    create_status, create_response = app.api_response("POST", "/api/generations", body)

    preflight = preflight_response["preflight"]
    identity_check = next(check for check in preflight["checks"] if check["id"] == "identity_lock")
    generation = create_response["generations"][0]
    manifest = generation["conditioning_manifest"]
    _, svg, _ = app.static_response("/" + generation["image"])

    assert preflight_status == 200
    assert preflight["status"] == "review"
    assert preflight["subject_hint"] == "product"
    assert preflight["uses_identity_lock"] is False
    assert preflight["identity_margin"] is None
    assert identity_check["status"] == "skip"
    assert "非人像主体不启用" in identity_check["value"]
    assert create_status == 201
    assert generation["subject_hint"] == "product"
    assert generation["drift_risk"] == "not_applicable"
    assert generation["reference_guidance"] == []
    assert manifest["uses_identity_lock"] is False
    assert manifest["identity"]["enabled"] is False
    assert manifest["weights"]["identity"] == 0.4
    assert manifest["weights"]["style"] == 0.8
    assert "LoRA" not in manifest["provider_prompt"]
    assert "human portrait" in manifest["provider_negative_prompt"]
    assert b'width="720" height="1280"' in svg


def test_character_prompt_keeps_face_reference_despite_city_or_poster_words(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")

    status, response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "mode": "图生图",
            "prompt": "沿用参考人脸，同一个亚洲女性角色，城市夜景商业海报，黑色西装，半身构图",
            "count": 1,
            "size": "9:16",
            "reference_guidance": [
                {
                    "kind": "face",
                    "label": "人脸",
                    "items": [
                        {
                            "id": "face-main",
                            "label": "主图",
                            "image": "assets/persona-ref-1.png",
                            "prompt": "保持参考人脸五官比例和脸型",
                        }
                    ],
                }
            ],
        },
    )

    generation = response["generations"][0]
    manifest = generation["conditioning_manifest"]
    assert status == 201
    assert generation["subject_hint"] == "female"
    assert generation["reference_guidance"][0]["kind"] == "face"
    assert manifest["uses_identity_lock"] is True
    assert "同一角色身份锁定" in manifest["provider_prompt"]
    assert "参考图约束" in manifest["provider_prompt"]
    assert "主体约束：生成风景" not in manifest["provider_prompt"]


def test_male_character_prompt_keeps_face_reference(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")

    status, response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "alex",
            "prompt": "同一个男性角色，城市夜景商业海报，黑色西装，半身构图",
            "count": 1,
            "size": "9:16",
            "reference_guidance": [
                {
                    "kind": "face",
                    "label": "人脸",
                    "items": [
                        {
                            "id": "face-main",
                            "label": "主图",
                            "image": "assets/persona-ref-1.png",
                            "prompt": "保持参考人脸五官比例和脸型",
                        }
                    ],
                }
            ],
        },
    )

    generation = response["generations"][0]
    manifest = generation["conditioning_manifest"]
    assert status == 201
    assert generation["subject_hint"] == "male"
    assert generation["reference_guidance"][0]["kind"] == "face"
    assert manifest["uses_identity_lock"] is True
    assert "同一角色身份锁定" in manifest["provider_prompt"]
    assert "参考图约束" in manifest["provider_prompt"]
    assert "主体约束：按提示词生成男性主体" not in manifest["provider_prompt"]


def test_character_quality_marks_conditioning_score_as_proxy_not_identity_verification(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    character = app.manager.get_character("lina")
    quality = app._quality_report(
        packet={
            "weights": {"identity": 0.9, "style": 0.55},
            "drift_risk": "low",
        },
        character=character,
        prompt="一个年轻的亚洲女性，正面半身肖像，身份锁定",
        negative_prompt="脸部漂移，脸型改变，低质量",
        mode="图生图",
        image="assets/persona-ref-1.png",
        index=0,
        subject_hint="female",
    )

    similarity = quality["identity_similarity"]
    assert quality["score_kind"] == "conditioning_proxy"
    assert quality["checked_by"] == "deterministic-local-quality-gate"
    assert similarity["match_verified"] is False
    assert similarity["status"] in {"structure_proxy_pass", "heuristic_pass", "review", "not_available"}
    assert "ArcFace" in similarity["review_note"] or "InsightFace" in similarity["review_note"]


def test_real_api_raster_character_quality_requires_verified_identity(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    character = app.manager.get_character("lina")
    unverified_similarity = {
        "status": "structure_proxy_pass",
        "method": "opencv_haar_structure_proxy",
        "match_verified": False,
        "review_note": "结构代理不是同一人认证；需要 ArcFace/InsightFace。",
    }

    with patch.object(app, "_identity_similarity_report", return_value=unverified_similarity):
        quality = app._quality_report(
            packet={
                "weights": {"identity": 0.95, "style": 0.55},
                "drift_risk": "low",
            },
            character=character,
            prompt="把眼镜给去了，人物不变。身份锁定",
            negative_prompt="脸部漂移，脸型改变，低质量",
            mode="图生图",
            image="assets/generated/gen-real.jpg",
            index=0,
            subject_hint="portrait",
        )

    assert quality["score_kind"] == "identity_unverified_proxy"
    assert quality["status"] == "review"
    assert quality["match"] is False
    assert quality["face_match_score"] < quality["threshold"]
    assert quality["identity_similarity"]["match_verified"] is False
    assert "不能标为同一人通过" in quality["review_note"]


def test_backfill_demotes_old_generated_proxy_pass_without_verified_identity(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    app.generations = [
        {
            "id": "gen-old-proxy-pass",
            "character_id": "alex",
            "prompt": "把眼镜给去了，人物不变。",
            "negative_prompt": "脸部漂移，脸型改变，低质量",
            "mode": "图生图",
            "image": "assets/generated/gen-old-proxy-pass.jpg",
            "identity_weight": 0.95,
            "style_weight": 0.6,
            "drift_risk": "low",
            "subject_hint": "portrait",
            "quality": {
                "face_match_score": 0.98,
                "threshold": 0.78,
                "match": True,
                "status": "pass",
                "score_kind": "conditioning_proxy",
                "identity_similarity": {
                    "status": "structure_proxy_pass",
                    "method": "opencv_haar_structure_proxy",
                    "match_verified": False,
                },
            },
        }
    ]
    unverified_similarity = {
        "status": "structure_proxy_pass",
        "method": "opencv_haar_structure_proxy",
        "match_verified": False,
        "review_note": "结构代理不是同一人认证；需要 ArcFace/InsightFace。",
    }

    with patch.object(app, "_identity_similarity_report", return_value=unverified_similarity):
        changed = app._backfill_generation_quality()

    quality = app.generations[0]["quality"]
    assert changed is True
    assert quality["score_kind"] == "identity_unverified_proxy"
    assert quality["status"] == "review"
    assert quality["match"] is False
    assert quality["face_match_score"] < quality["threshold"]


def test_identity_similarity_uses_structure_proxy_without_claiming_identity_match(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    character = app.manager.get_character("lina")
    reference_report = {
        "status": "detected",
        "detected": True,
        "structure": {
            "face_aspect_w_h": 0.82,
            "eye_distance_ratio": 0.43,
            "symmetry": 0.71,
            "contrast": 0.42,
            "brightness": 0.53,
            "sharpness": 0.36,
        },
    }
    generated_report = {
        "status": "detected",
        "detected": True,
        "structure": {
            "face_aspect_w_h": 0.84,
            "eye_distance_ratio": 0.45,
            "symmetry": 0.69,
            "contrast": 0.39,
            "brightness": 0.51,
            "sharpness": 0.33,
        },
    }

    with patch.object(app, "_opencv_frontal_face_report", side_effect=[reference_report, generated_report]):
        similarity = app._identity_similarity_report(character, "assets/generated/gen-structure.png")

    assert similarity["status"] == "structure_proxy_pass"
    assert similarity["method"] == "opencv_haar_structure_proxy"
    assert similarity["score"] >= similarity["threshold"]
    assert similarity["confidence"] >= 0.45
    assert similarity["match_verified"] is False
    assert any(component["id"] == "eye_distance_ratio" for component in similarity["components"])
    assert "不是同一人认证" in similarity["review_note"]
    assert "ArcFace" in similarity["review_note"] or "InsightFace" in similarity["review_note"]


def test_generation_preflight_reports_subject_size_and_filtered_references(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")

    status, response = app.api_response(
        "POST",
        "/api/generations/preflight",
        {
            "character_id": "lina",
            "prompt": "保健品海参单页广告，展示商品卖点和落地页视觉，不要人物",
            "size": "9:16",
            "identity_weight": 0.85,
            "style_weight": 0.6,
            "pose_control": {"pose": "side", "weight": 0.52},
            "reference_guidance": [
                {
                    "kind": "face",
                    "label": "人脸",
                    "items": [
                        {
                            "id": "face-main",
                            "label": "主图",
                            "image": "assets/persona-ref-1.png",
                            "prompt": "保持参考人脸五官比例和脸型",
                        }
                    ],
                }
            ],
        },
    )

    preflight = response["preflight"]
    assert status == 200
    assert preflight["status"] == "review"
    assert preflight["subject_hint"] == "product"
    assert preflight["subject_label"] == "产品主体"
    assert preflight["uses_identity_lock"] is False
    assert preflight["size"]["label"] == "9:16"
    assert preflight["size"]["provider_size"] == "960*1696"
    assert preflight["size"]["preview_canvas"] == {"width": 720, "height": 1280}
    assert preflight["reference_counts"] == {"requested": 1, "effective": 0, "filtered": 1}
    assert preflight["pose_control"]["pose"] == "side"
    assert preflight["pose_control"]["label"] == "侧脸"
    assert preflight["billing"]["cost"] == 8
    assert preflight["billing"]["credits_remaining"] == 1200
    assert preflight["billing"]["credits_after"] == 1192
    assert preflight["billing"]["enough"] is True
    assert any(check["id"] == "references" and check["status"] == "review" for check in preflight["checks"])
    assert any(check["id"] == "pose_control" and check["value"] == "侧脸" for check in preflight["checks"])
    assert any(check["id"] == "credits" and check["status"] == "pass" for check in preflight["checks"])


def test_generation_preflight_blocks_when_account_credits_are_insufficient(tmp_path):
    app = PersonaStudioApp(data_path=tmp_path / "state.json")
    app.account["credits_remaining"] = 1

    status, response = app.api_response(
        "POST",
        "/api/generations/preflight",
        {
            "character_id": "lina",
            "prompt": "walking in morning light",
            "identity_weight": 0.86,
            "style_weight": 0.58,
            "count": 1,
        },
    )

    preflight = response["preflight"]

    assert status == 200
    assert preflight["status"] == "blocked"
    assert preflight["billing"]["cost"] == 2
    assert preflight["billing"]["credits_remaining"] == 1
    assert preflight["billing"]["credits_after"] == 1
    assert preflight["billing"]["enough"] is False
    assert "余额不足" in preflight["summary"]
    assert any(
        check["id"] == "credits" and check["status"] == "fail" and "余额不足" in check["value"]
        for check in preflight["checks"]
    )


def test_generation_preflight_blocks_invalid_count_before_generation_400(tmp_path):
    app = PersonaStudioApp(data_path=tmp_path / "state.json")
    body = {
        "character_id": "lina",
        "prompt": "一个年轻的亚洲女性，清晨自然光，身份锁定",
        "count": 3,
    }

    preflight_status, preflight_response = app.api_response("POST", "/api/generations/preflight", body)
    create_status, create_response = app.api_response("POST", "/api/generations", body)

    preflight = preflight_response["preflight"]
    count_check = next(check for check in preflight["checks"] if check["id"] == "count")

    assert preflight_status == 200
    assert preflight["status"] == "blocked"
    assert "数量不合法" in preflight["summary"]
    assert preflight["billing"]["count"] == 3
    assert preflight["billing"]["count_valid"] is False
    assert count_check["status"] == "fail"
    assert "1、2、4、8" in count_check["value"]
    assert create_status == 400
    assert "count must be one of 1, 2, 4, 8" in create_response["error"]


def test_non_character_legacy_generation_metadata_is_backfilled(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=data_path)
    app.generations[0].update(
        {
            "prompt": "保健品海参单页广告，展示商品卖点和落地页视觉，不要人物",
            "subject_hint": "landscape",
            "size": "9:16",
            "drift_risk": "low",
            "lora_id": "portrait-consistency",
            "lora_name": "人像一致性",
            "lora_weight": 0.72,
            "reference_guidance": [
                {
                    "kind": "face",
                    "label": "人脸",
                    "items": [
                        {
                            "id": "face-main",
                            "label": "主图",
                            "prompt": "保持参考人脸五官比例和脸型",
                        }
                    ],
                }
            ],
            "conditioning_manifest": {
                "schema_version": 1,
                "subject_hint": "landscape",
                "uses_identity_lock": False,
                "identity": {"enabled": False},
                "style": {"lora_id": "portrait-consistency"},
                "memory": {"best_angle": "side"},
                "references": [
                    {
                        "kind": "face",
                        "label": "人脸",
                        "items": [{"id": "face-main", "label": "主图"}],
                    }
                ],
                "provider_prompt": "bad prompt with 人脸 and LoRA",
                "prompt_hash": "old",
            },
            "quality": {"checked_by": "deterministic-local-quality-gate"},
        }
    )
    app._save_assets()

    reloaded = PersonaStudioApp(static_dir=Path("prototype"), data_path=data_path)
    _, response = reloaded.api_response("GET", "/api/generations")
    generation = response["generations"][-1]
    manifest = generation["conditioning_manifest"]

    assert generation["subject_hint"] == "product"
    assert generation["drift_risk"] == "not_applicable"
    assert generation["lora_id"] is None
    assert generation["reference_guidance"] == []
    assert generation["quality"]["checked_by"] == "deterministic-local-subject-gate"
    assert manifest["references"] == []
    assert manifest["style"]["lora_id"] is None
    assert manifest["memory"]["best_angle"] is None
    assert "人脸" not in manifest["provider_prompt"]
    assert "LoRA" not in manifest["provider_prompt"]


def test_local_generation_preview_respects_requested_aspect_ratio(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")

    status, response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "prompt": "一片山海风景，清晨日光",
            "count": 1,
            "size": "9:16",
        },
    )

    image = response["generations"][0]["image"]
    _, svg, _ = app.static_response("/" + image)

    assert status == 201
    assert response["generations"][0]["size"] == "9:16"
    assert b'width="720" height="1280"' in svg


def test_local_generation_preview_covers_canvas_without_letterbox(tmp_path):
    # Regression: the SVG draws in a fixed 960x720 space but declares
    # size-specific width/height (e.g. 720x1280 for 9:16). Without
    # preserveAspectRatio="...slice" the default "meet" letterboxes the 4:3
    # content inside the tall canvas, leaving transparent margins where the
    # card background shows through (the "empty green box" bug). The root SVG
    # must request a cover fit so the preview fills the canvas for every size.
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")

    for size in ("1:1", "9:16", "3:4", "16:9"):
        for prompt in ("a woman in soft morning light", "一辆红色跑车，城市街道"):
            _, response = app.api_response(
                "POST",
                "/api/generations",
                {"character_id": "lina", "prompt": prompt, "count": 1, "size": size},
            )
            image = response["generations"][0]["image"]
            _, svg, _ = app.static_response("/" + image)
            root = svg.split(b">", 1)[0]
            assert b'preserveAspectRatio="xMidYMid slice"' in root, (size, prompt)


def test_api_generation_quality_failure_updates_memory_advice(tmp_path):
    app = PersonaStudioApp(data_path=tmp_path / "state.json")

    status, response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "prompt": "style-heavy portrait",
            "identity_weight": 0.61,
            "style_weight": 0.58,
            "count": 1,
        },
    )
    character_status, character_response = app.api_response("GET", "/api/characters/lina")
    reloaded = PersonaStudioApp(data_path=tmp_path / "state.json")
    _, reloaded_character_response = reloaded.api_response("GET", "/api/characters/lina")

    generation = response["generations"][0]
    failure_advice = character_response["character"]["memory_insights"]["failure_advice"]
    reloaded_failure_advice = reloaded_character_response["character"]["memory_insights"]["failure_advice"]

    assert status == 201
    assert generation["quality"]["status"] == "fail"
    assert generation["quality"]["match"] is False
    assert generation["quality"]["identity_margin"] < 0.08
    assert character_status == 200
    assert "cinematic" in failure_advice["blocked_styles"]
    assert "cinematic" in reloaded_failure_advice["blocked_styles"]


def test_generation_preflight_surfaces_character_scoped_failure_memory(tmp_path):
    app = PersonaStudioApp(data_path=tmp_path / "state.json")
    app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "prompt": "style-heavy portrait",
            "identity_weight": 0.61,
            "style_weight": 0.58,
            "count": 1,
        },
    )

    lina_status, lina_response = app.api_response(
        "POST",
        "/api/generations/preflight",
        {
            "character_id": "lina",
            "prompt": "cinematic portrait recovery",
            "identity_weight": 0.86,
            "style_weight": 0.58,
            "count": 1,
        },
    )
    kira_status, kira_response = app.api_response(
        "POST",
        "/api/generations/preflight",
        {
            "character_id": "kira",
            "prompt": "cinematic portrait recovery",
            "identity_weight": 0.86,
            "style_weight": 0.58,
            "count": 1,
        },
    )

    lina_preflight = lina_response["preflight"]
    kira_preflight = kira_response["preflight"]

    assert lina_status == 200
    assert lina_preflight["status"] == "review"
    assert lina_preflight["memory"]["blocked_styles"] == ["cinematic"]
    assert "失败风格：cinematic" in lina_preflight["summary"]
    assert any(
        check["id"] == "memory" and check["status"] == "review" and "cinematic" in check["value"]
        for check in lina_preflight["checks"]
    )
    assert kira_status == 200
    assert kira_preflight["memory"]["blocked_styles"] == []
    assert any(
        check["id"] == "memory" and check["status"] == "pass" and check["value"] == "暂无失败风格"
        for check in kira_preflight["checks"]
    )


def test_conditioning_manifest_failure_memory_is_scoped_per_character(tmp_path):
    app = PersonaStudioApp(data_path=tmp_path / "state.json")
    app.manager.create_character(
        "Nova",
        {"face_images": ["nova-front", "nova-side", "nova-studio"]},
        "cinematic portrait",
    )
    app.manager.record_scene(
        "nova",
        "failed cinematic test",
        "img.png",
        "front",
        0.1,
        style="cinematic",
    )

    lina_status, lina_response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "prompt": "cinematic portrait",
            "identity_weight": 0.85,
            "style_weight": 0.6,
            "count": 1,
        },
    )
    nova_status, nova_response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "nova",
            "prompt": "cinematic portrait",
            "identity_weight": 0.85,
            "style_weight": 0.6,
            "count": 1,
        },
    )

    lina_manifest = lina_response["generations"][0]["conditioning_manifest"]
    nova_manifest = nova_response["generations"][0]["conditioning_manifest"]

    assert lina_status == 201
    assert nova_status == 201
    assert lina_manifest["memory"]["blocked_styles"] == []
    assert "avoid failed style memory" not in lina_manifest["provider_negative_prompt"]
    assert nova_manifest["memory"]["blocked_styles"] == ["cinematic"]
    assert "avoid failed style memory: cinematic" in nova_manifest["provider_negative_prompt"]


def test_api_generations_rejects_invalid_count():
    app = PersonaStudioApp()
    status, response = app.api_response(
        "POST",
        "/api/generations",
        {"character_id": "lina", "count": 5},
    )
    assert status == 400
    assert "count must be one of" in response["error"]


def test_api_generations_rejects_missing_character_id():
    app = PersonaStudioApp()
    status, response = app.api_response(
        "POST",
        "/api/generations",
        {"prompt": "walking"},
    )
    assert status == 400
    assert "character_id is required" in response["error"]


def test_api_projects_create_update_export_and_persist(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    list_status, list_response = app.api_response("GET", "/api/projects")
    create_status, create_response = app.api_response(
        "POST",
        "/api/projects",
        {
            "name": "Launch Campaign",
            "user_segment": "商业用户",
            "level": "Level 4 Visual IP System",
            "character_id": "alex",
            "channels": ["广告投放", "电商主图"],
            "deliverables": ["IP 资产包", "商业授权摘要"],
        },
    )
    project_id = create_response["project"]["id"]
    submit_status, submit_response = app.api_response(
        "POST",
        f"/api/projects/{project_id}",
        {
            "character_ids": ["alex", "lina"],
            "review_action": "submit_review",
        },
    )
    approve_status, approve_response = app.api_response(
        "POST",
        f"/api/projects/{project_id}",
        {"review_action": "approve"},
    )
    release_status, release_response = app.api_response("POST", f"/api/projects/{project_id}/release")
    app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "openai",
                "api_key": "sk-secret-ip-package",
                "model": "persona-demo-image",
                "base_url": "https://api.example.test/v1",
            }
        },
    )
    export_status, export_response = app.api_response("GET", "/api/export")
    reloaded = PersonaStudioApp(data_path=data_path)
    get_status, get_response = reloaded.api_response("GET", f"/api/projects/{project_id}")
    withdraw_status, withdraw_response = app.api_response(
        "POST",
        f"/api/projects/{project_id}",
        {"review_action": "withdraw_review"},
    )

    assert list_status == 200
    assert {project["user_segment"] for project in list_response["projects"]} >= {"普通用户", "创作者", "商业用户"}
    assert create_status == 201
    assert create_response["project"]["user_segment"] == "商业用户"
    assert create_response["project"]["ip_package"]["license_scope"] == "commercial-campaign"
    assert create_response["project"]["ip_package"]["release_ready"] is False
    assert submit_status == 200
    assert submit_response["project"]["counts"]["characters"] == 2
    assert submit_response["project"]["status"] == "in_review"
    assert submit_response["project"]["review"]["license_status"] == "pending-review"
    assert submit_response["project"]["review"]["submitted_at"]
    assert approve_status == 200
    assert approve_response["project"]["status"] == "approved"
    assert approve_response["project"]["review"]["release_ready"] is False
    assert approve_response["project"]["review"]["approved_at"]
    assert approve_response["project"]["ip_package"]["license_status"] == "commercial-ready"
    assert approve_response["project"]["ip_package"]["release_ready"] is False
    assert approve_response["project"]["ip_package"]["asset_counts"]["characters"] == 2
    assert approve_response["project"]["ip_package"]["asset_counts"]["identity_references"] >= 8
    assert approve_response["project"]["ip_package"]["asset_counts"]["non_face_references"] >= 18
    assert approve_response["project"]["ip_package"]["asset_counts"]["generated_images"] >= 4
    assert approve_response["project"]["ip_package"]["asset_counts"]["quality_passed_images"] >= 4
    checklist_ids = {check["id"] for check in approve_response["project"]["ip_package"]["delivery_checklist"]}
    assert {
        "identity_ready",
        "reference_pack_ready",
        "generation_quality_ready",
        "memory_ready",
        "license_ready",
        "deliverables_ready",
    } <= checklist_ids
    manifest = approve_response["project"]["ip_package"]["asset_manifest"]
    lina_manifest = next(row for row in manifest if row["character_id"] == "lina")
    assert lina_manifest["identity_references"]["can_train"] is True
    assert lina_manifest["reference_collections"]["outfit"]["count"] >= 3
    assert lina_manifest["generation_assets"]["count"] >= 4
    assert lina_manifest["generation_assets"]["quality_pass_count"] >= 4
    assert lina_manifest["generation_assets"]["latest_model_route"]["model"] == "persona-local-preview"
    assert lina_manifest["memory_assets"]["best_angles"]
    assert lina_manifest["version_assets"]["count"] >= 1
    assert release_status == 200
    assert release_response["release_package"]["status"] == "ready"
    assert release_response["project"]["review"]["release_ready"] is True
    assert release_response["project"]["ip_package"]["release_ready"] is True
    assert export_status == 200
    assert export_response["project"]["counts"]["projects"] >= 4
    exported_package = next(package for package in export_response["project"]["ip_packages"] if package["project_id"] == project_id)
    assert exported_package["review"]["status"] == "approved"
    assert exported_package["release_ready"] is True
    assert exported_package["asset_counts"] == release_response["project"]["ip_package"]["asset_counts"]
    exported_text = json.dumps(exported_package)
    assert "sk-secret-ip-package" not in exported_text
    assert "api_key" not in exported_text.lower()
    assert get_status == 200
    assert get_response["project"]["name"] == "Launch Campaign"
    assert get_response["project"]["counts"]["characters"] == 2
    assert get_response["project"]["review"]["status"] == "approved"
    assert get_response["project"]["review"]["release_ready"] is True
    assert get_response["project"]["ip_package"]["asset_manifest"][0]["identity_references"]["count"] >= 4
    assert withdraw_status == 200
    assert withdraw_response["project"]["status"] == "draft"
    assert withdraw_response["project"]["ip_package"]["release_ready"] is False


def test_api_project_paths_decode_unicode_ids(tmp_path):
    app = PersonaStudioApp(data_path=tmp_path / "state.json")

    create_status, create_response = app.api_response(
        "POST",
        "/api/projects",
        {
            "name": "Lina 系列项目",
            "character_id": "lina",
        },
    )
    project_id = create_response["project"]["id"]
    encoded_id = quote(project_id)
    get_status, get_response = app.api_response("GET", f"/api/projects/{encoded_id}")

    assert create_status == 201
    assert project_id == "lina-系列项目"
    assert get_status == 200
    assert get_response["project"]["name"] == "Lina 系列项目"


def test_api_delete_project_persists(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)
    create_status, create_response = app.api_response(
        "POST",
        "/api/projects",
        {
            "name": "Duplicate Project",
            "character_id": "lina",
        },
    )
    project_id = create_response["project"]["id"]

    delete_status, delete_response = app.api_response("DELETE", f"/api/projects/{project_id}")
    reloaded = PersonaStudioApp(data_path=data_path)
    list_status, list_response = reloaded.api_response("GET", "/api/projects")

    assert create_status == 201
    assert delete_status == 200
    assert delete_response["deleted"]["id"] == project_id
    assert list_status == 200
    assert project_id not in {project["id"] for project in list_response["projects"]}


def test_api_reference_asset_upload_is_served_from_static_dir(tmp_path):
    app = PersonaStudioApp(static_dir=tmp_path)
    data_url = "data:image/png;base64,iVBORw0KGgo="

    status, response = app.api_response(
        "POST",
        "/api/assets/reference",
        {"name": "face.png", "data_url": data_url},
    )
    asset = response["asset"]
    static_status, content, content_type = app.static_response(f"/{asset['path']}")

    assert status == 201
    assert asset["path"].startswith("assets/uploads/reference-")
    assert asset["content_type"] == "image/png"
    assert static_status == 200
    assert content == b"\x89PNG\r\n\x1a\n"
    assert content_type == "image/png"


def test_api_reference_asset_upload_avoids_same_second_filename_collision(tmp_path):
    app = PersonaStudioApp(static_dir=tmp_path)
    app._timestamp = lambda: "2026-06-17T12:34:56Z"

    _, first_response = app.api_response(
        "POST",
        "/api/assets/reference",
        {"name": "first.png", "data_url": "data:image/png;base64,Zmlyc3Q="},
    )
    _, second_response = app.api_response(
        "POST",
        "/api/assets/reference",
        {"name": "second.png", "data_url": "data:image/png;base64,c2Vjb25k"},
    )

    first_asset = first_response["asset"]
    second_asset = second_response["asset"]
    first_status, first_content, _ = app.static_response(f"/{first_asset['path']}")
    second_status, second_content, _ = app.static_response(f"/{second_asset['path']}")

    assert first_asset["path"] != second_asset["path"]
    assert second_asset["id"].endswith("-2")
    assert first_status == 200
    assert second_status == 200
    assert first_content == b"first"
    assert second_content == b"second"


def test_api_create_character_and_reload_from_disk(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    status, response = app.api_response(
        "POST",
        "/api/characters",
        {
            "name": "Nova",
            "style": "cinematic portrait soft daylight",
            "prompt": "consistent character portrait",
        },
    )
    reloaded = PersonaStudioApp(data_path=data_path)
    _, characters = reloaded.api_response("GET", "/api/characters")

    assert status == 201
    assert response["character"]["id"] == "nova"
    assert data_path.exists()
    assert "nova" in {character["id"] for character in characters["characters"]}


def test_api_delete_character_cleans_assets_and_persists(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)
    app.api_response(
        "POST",
        "/api/characters",
        {
            "name": "Nova",
            "style": "cinematic portrait soft daylight",
            "prompt": "consistent character portrait",
        },
    )
    app.api_response("POST", "/api/generations", {"character_id": "nova", "count": 1})
    app.api_response(
        "POST",
        "/api/projects",
        {
            "name": "Nova Series",
            "character_id": "nova",
        },
    )

    delete_status, delete_response = app.api_response("DELETE", "/api/characters/nova")
    generations_status, generations_response = app.api_response("GET", "/api/generations")
    projects_status, projects_response = app.api_response("GET", "/api/projects")
    reloaded = PersonaStudioApp(data_path=data_path)
    _, characters_response = reloaded.api_response("GET", "/api/characters")

    assert delete_status == 200
    assert delete_response["deleted"]["id"] == "nova"
    assert "nova" not in {character["id"] for character in delete_response["characters"]}
    assert generations_status == 200
    assert all(generation["character_id"] != "nova" for generation in generations_response["generations"])
    assert projects_status == 200
    assert all("nova" not in project["character_ids"] for project in projects_response["projects"])
    assert "nova" not in {character["id"] for character in characters_response["characters"]}


def test_delete_character_unlinks_its_generations_from_jobs(tmp_path):
    # Regression: single-generation deletion unlinks ids from jobs, but deleting
    # a whole character only dropped its generation records, leaving jobs with
    # dangling generation_ids and a stale result_count. Keep both paths
    # consistent so the jobs panel never points at deleted generations.
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    app.api_response(
        "POST",
        "/api/characters",
        {"name": "Tmp Hero", "style": "cinematic portrait", "prompt": "portrait"},
    )
    _, created = app.api_response(
        "POST", "/api/generations", {"character_id": "tmp-hero", "count": 2, "prompt": "portrait"}
    )
    job_id = created["job"]["id"]
    generated_ids = set(created["job"]["generation_ids"])
    assert generated_ids

    delete_status, _ = app.api_response("DELETE", "/api/characters/tmp-hero")
    assert delete_status == 200

    _, job_response = app.api_response("GET", f"/api/generation-jobs/{job_id}")
    job = job_response["job"]

    # No surviving generation ids may point at the deleted character's records.
    live_ids = {generation["id"] for generation in app.generations}
    assert all(gid in live_ids for gid in job.get("generation_ids", []))
    assert not (generated_ids & set(job.get("generation_ids", [])))
    assert job["result_count"] == len(job.get("generation_ids", []))
    # The unlinked ids are preserved for audit, mirroring single deletion.
    assert generated_ids.issubset(set(job.get("deleted_generation_ids", [])))

    # Survives a reload from disk.
    reloaded = PersonaStudioApp(data_path=data_path)
    _, reloaded_jobs = reloaded.api_response("GET", f"/api/generation-jobs/{job_id}")
    assert not (generated_ids & set(reloaded_jobs["job"].get("generation_ids", [])))


def test_generation_ids_stay_unique_after_deletion(tmp_path):
    # Regression: ids were derived from len(generations); deleting a character
    # removed its records, so new ids collided with surviving higher-numbered
    # ones. Force the non-contiguous deletion pattern and assert uniqueness.
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    # demo seeds lina-owned generations; interleave kira then lina batches.
    app.api_response("POST", "/api/generations", {"character_id": "kira", "count": 4})
    app.api_response("POST", "/api/generations", {"character_id": "lina", "count": 4})

    # Deleting lina removes both its demo (low) and its latest (high) records,
    # leaving kira's mid-range ids surrounded by gaps.
    app.api_response("DELETE", "/api/characters/lina")
    app.api_response("POST", "/api/generations", {"character_id": "kira", "count": 4})

    ids = [generation["id"] for generation in app.generations]

    assert len(ids) == len(set(ids)), f"duplicate generation ids: {ids}"


def test_favorite_targets_correct_record_after_deletion(tmp_path):
    # With colliding ids, favoriting hit the first matching record instead of
    # the intended one. Unique ids keep favorite/lookup unambiguous.
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    app.api_response("POST", "/api/generations", {"character_id": "kira", "count": 4})
    app.api_response("POST", "/api/generations", {"character_id": "lina", "count": 4})
    app.api_response("DELETE", "/api/characters/lina")
    _, created = app.api_response("POST", "/api/generations", {"character_id": "kira", "count": 4})

    target_id = created["generations"][-1]["id"]
    status, response = app.api_response(
        "POST", f"/api/generations/{target_id}/favorite", {"favorite": True}
    )

    assert status == 200
    assert response["generation"]["id"] == target_id
    favorited = [g for g in app.generations if g.get("favorite")]
    assert [g["id"] for g in favorited] == [target_id]


def test_generation_delete_removes_record_memory_job_and_generated_file(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=data_path)

    create_status, create_response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "prompt": "qa removable generation",
            "count": 1,
            "pose_control": {"pose": "side"},
        },
    )
    generation = create_response["generations"][0]
    image_file = app.static_dir / generation["image"]
    before_memory = len([entry for entry in app.manager.memory_store.logs if (entry.get("metadata") or {}).get("generation_id") == generation["id"]])

    assert create_status == 201
    assert image_file.exists()
    assert before_memory == 1

    delete_status, delete_response = app.api_response("DELETE", f"/api/generations/{generation['id']}")
    reloaded = PersonaStudioApp(static_dir=Path("prototype"), data_path=data_path)
    _, generations_response = reloaded.api_response("GET", "/api/generations")

    assert delete_status == 200
    assert delete_response["deleted"]["id"] == generation["id"]
    assert delete_response["deleted"]["memory_entries_removed"] == 1
    assert delete_response["deleted"]["job_ids"] == [create_response["job"]["id"]]
    assert delete_response["deleted"]["image_removed"] is True
    assert delete_response["jobs"][0]["deleted_generation_ids"] == [generation["id"]]
    assert any(character["id"] == "lina" for character in delete_response["characters"])
    assert not image_file.exists()
    assert generation["id"] not in {item["id"] for item in app.generations}
    assert generation["id"] in app.generation_jobs[-1]["deleted_generation_ids"]
    assert generation["id"] not in {item["id"] for item in generations_response["generations"]}


def test_api_delete_rejects_last_character():
    app = PersonaStudioApp()
    app.manager.characters = {"solo": app.manager.characters["lina"]}

    status, response = app.api_response("DELETE", "/api/characters/solo")

    assert status == 400
    assert "cannot delete the last character" in response["error"]


def test_api_versions_train_more_and_persist(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    status, response = app.api_response(
        "POST",
        "/api/characters/lina/versions",
        {
            "note": "train more references",
            "style": "commercial studio key light",
        },
    )
    versions_status, versions_response = app.api_response("GET", "/api/characters/lina/versions")
    reloaded = PersonaStudioApp(data_path=data_path)
    _, character_response = reloaded.api_response("GET", "/api/characters/lina")

    assert status == 201
    assert response["version"]["version"] == 2
    assert response["character"]["version"] == 2
    assert versions_status == 200
    assert versions_response["versions"][-1]["note"] == "train more references"
    assert character_response["character"]["version"] == 2


def test_api_version_restore_creates_restored_version_and_persists(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)

    app.api_response(
        "POST",
        "/api/characters/lina/versions",
        {
            "note": "switch to anime",
            "style": "anime clean line",
        },
    )
    restore_status, restore_response = app.api_response(
        "POST",
        "/api/characters/lina/versions/1/restore",
        {"note": "restore original face"},
    )
    reloaded = PersonaStudioApp(data_path=data_path)
    _, character_response = reloaded.api_response("GET", "/api/characters/lina")
    _, versions_response = reloaded.api_response("GET", "/api/characters/lina/versions")

    assert restore_status == 200
    assert restore_response["restored"]["version"] == 3
    assert restore_response["restored"]["restored_from"] == 1
    assert restore_response["character"]["style"]["preset"] == "cinematic"
    assert character_response["character"]["version"] == 3
    assert character_response["character"]["style"]["preset"] == "cinematic"
    assert versions_response["versions"][-1]["can_restore"] is True
    assert versions_response["versions"][-1]["restored_from"] == 1


def test_static_index_response():
    app = PersonaStudioApp()

    status, content, content_type = app.static_response("/")

    assert status == 200
    assert content_type == "text/html"
    assert b"Persona Studio" in content
    assert "\u89d2\u8272\u7cfb\u7edf".encode("utf-8") in content # "角色系统"


def test_reference_guidance_preserves_image_paths(tmp_path):
    app = PersonaStudioApp(data_path=tmp_path / "state.json")

    status, response = app.api_response(
        "POST",
        "/api/generations",
        {
            "character_id": "lina",
            "mode": "图生图",
            "prompt": "沿用参考图构图",
            "count": 1,
            "reference_guidance": [
                {
                    "kind": "face",
                    "label": "人脸",
                    "items": [
                        {
                            "id": "face-main",
                            "label": "主图",
                            "image": "assets/persona-ref-1.png",
                            "prompt": "保持参考人脸五官比例和脸型",
                        }
                    ],
                }
            ],
        },
    )

    guidance = response["generations"][0]["reference_guidance"][0]["items"][0]
    assert status == 201
    assert guidance["image"] == "assets/persona-ref-1.png"


def test_legacy_conditioning_manifest_is_upgraded_on_load(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(data_path=data_path)
    app.generations[0]["conditioning_manifest"] = {"provider_prompt": "old"}
    app._save_assets()

    reloaded = PersonaStudioApp(data_path=data_path)
    _, response = reloaded.api_response("GET", "/api/generations")

    manifest = response["generations"][-1]["conditioning_manifest"]
    assert manifest["schema_version"] == 1
    assert manifest["prompt_hash"]
    assert isinstance(manifest["identity"], dict)
    assert manifest["provider_prompt"] != "old"


def test_conditioning_manifest_backfill_adds_identity_edit_mode(tmp_path):
    data_path = tmp_path / "state.json"
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=data_path)
    app.generations = [
        {
            "id": "gen-old-edit-manifest",
            "character_id": "alex",
            "character_name": "Alex",
            "subject_hint": "portrait",
            "mode": "图生图",
            "prompt": "把眼镜去掉，人物不变。",
            "negative_prompt": "模糊，低质量",
            "state": "calm",
            "identity_weight": 0.95,
            "style_weight": 0.6,
            "lora_id": "brand-campaign",
            "lora_weight": 0.62,
            "reference_guidance": [
                {
                    "kind": "face",
                    "label": "人脸",
                    "items": [
                        {
                            "id": "face-main",
                            "label": "主图",
                            "image": "assets/persona-ref-1.png",
                            "prompt": "保持参考人脸五官比例和脸型",
                        }
                    ],
                }
            ],
            "conditioning_manifest": {
                "schema_version": 1,
                "subject_hint": "portrait",
                "references": [
                    {
                        "kind": "face",
                        "label": "人脸",
                        "items": [
                            {
                                "id": "face-main",
                                "label": "主图",
                                "image": "assets/persona-ref-1.png",
                                "prompt": "保持参考人脸五官比例和脸型",
                            }
                        ],
                    }
                ],
                "identity": {},
                "provider_prompt": "旧提示词；风格约束：commercial",
                "prompt_hash": "oldhash",
            },
        }
    ]
    app._save_assets()

    reloaded = PersonaStudioApp(static_dir=Path("prototype"), data_path=data_path)
    manifest = reloaded.generations[0]["conditioning_manifest"]
    assert manifest["identity_edit_mode"] is True
    assert "身份编辑模式" in manifest["provider_prompt"]
    assert "风格约束" not in manifest["provider_prompt"]


def test_wanx_t2i_non_character_prompt_excludes_face_reference_and_keeps_size(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    settings_status, _ = app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "wanx",
                "base_url": "https://dashscope.aliyuncs.com/api/v1",
                "model": "wan2.6-image",
                "api_key": "sk-test-secret",
            }
        },
    )
    captured = {"payload": None}

    def fake_urlopen(request, timeout=120):
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        if "multimodal-generation" in url:
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            body = json.dumps(
                {
                    "output": {
                        "choices": [
                            {
                                "message": {
                                    "content": [
                                        {
                                            "image": "https://example.test/generated.png",
                                            "type": "image",
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            ).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        body = b"\x89PNG\r\n\x1a\n"
        response = MagicMock()
        response.read.return_value = body
        response.headers.get_content_type.return_value = "image/png"
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *args: None
        return response

    with patch("persona_studio.server.urllib.request.urlopen", side_effect=fake_urlopen):
        create_status, create_response = app.api_response(
            "POST",
            "/api/generations",
            {
                "character_id": "lina",
                "mode": "文生图",
                "prompt": "保健品海参单页广告，展示商品卖点和落地页视觉，不要人物",
                "count": 1,
                "size": "9:16",
                "reference_guidance": [
                    {
                        "kind": "face",
                        "label": "人脸",
                        "items": [
                            {
                                "id": "face-main",
                                "label": "主图",
                                "image": "assets/persona-ref-1.png",
                                "prompt": "保持参考人脸五官比例和脸型",
                            }
                        ],
                    }
                ],
            },
        )

    generation = create_response["generations"][0]
    content = captured["payload"]["input"]["messages"][0]["content"]
    provider_prompt = content[0]["text"]
    assert settings_status == 200
    assert create_status == 201
    assert generation["subject_hint"] == "product"
    assert generation["reference_guidance"] == []
    assert generation["model_route"]["generation_kind"] == "t2i"
    assert captured["payload"]["parameters"]["size"] == "960*1696"
    assert captured["payload"]["model"] == "wan2.6-t2i"
    assert len(content) == 1
    assert "主体约束：生成产品" in provider_prompt
    assert "参考图约束" not in provider_prompt
    assert "人脸" not in provider_prompt
    assert "identity-lock" not in provider_prompt
    assert "portrait medium close-up" not in provider_prompt
    assert "LoRA" not in provider_prompt
    assert "human portrait" in captured["payload"]["parameters"]["negative_prompt"]


def test_wanx_text_mode_character_face_reference_auto_uses_image_conditioning(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    settings_status, _ = app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "wanx",
                "base_url": "https://dashscope.aliyuncs.com/api/v1",
                "model": "wan2.6-t2i",
                "api_key": "sk-test-secret",
            }
        },
    )
    captured = {"payload": None}

    def fake_urlopen(request, timeout=120):
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        if "multimodal-generation" in url:
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            body = json.dumps(
                {
                    "output": {
                        "choices": [
                            {
                                "message": {
                                    "content": [
                                        {
                                            "image": "https://example.test/reference-locked.png",
                                            "type": "image",
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            ).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        body = b"\x89PNG\r\n\x1a\n"
        response = MagicMock()
        response.read.return_value = body
        response.headers.get_content_type.return_value = "image/png"
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *args: None
        return response

    with patch("persona_studio.server.urllib.request.urlopen", side_effect=fake_urlopen):
        create_status, create_response = app.api_response(
            "POST",
            "/api/generations",
            {
                "character_id": "lina",
                "mode": "文生图",
                "prompt": "一个年轻的亚洲女性，户外公园自然光，保持同一张脸和脸型，写实摄影",
                "negative_prompt": "脸部漂移，五官错位",
                "identity_weight": 0.86,
                "style_weight": 0.58,
                "count": 1,
                "size": "9:16",
                "reference_guidance": [
                    {
                        "kind": "face",
                        "label": "人脸",
                        "items": [
                            {
                                "id": "face-main",
                                "label": "主图",
                                "image": "assets/persona-ref-1.png",
                                "prompt": "保持参考人脸五官比例和脸型",
                            }
                        ],
                    }
                ],
            },
        )

    generation = create_response["generations"][0]
    route = generation["model_route"]
    manifest = generation["conditioning_manifest"]
    content = captured["payload"]["input"]["messages"][0]["content"]
    provider_prompt = content[0]["text"]

    assert settings_status == 200
    assert create_status == 201
    assert generation["mode"] == "文生图"
    assert generation["subject_hint"] == "female"
    assert generation["reference_guidance"][0]["kind"] == "face"
    assert route["provider"] == "wanx"
    assert route["real_generation"] is True
    assert route["generation_kind"] == "img2img"
    assert manifest["reference_conditioning_mode"] == "图生图"
    assert manifest["uses_identity_lock"] is True
    assert captured["payload"]["model"] == "wan2.6-image"
    assert captured["payload"]["parameters"]["size"] == "960*1696"
    assert captured["payload"]["parameters"]["enable_interleave"] is False
    assert len(content) == 2
    assert any("image" in item for item in content[1:])
    assert "同一角色身份锁定" in provider_prompt
    assert "参考图约束" in provider_prompt
    assert "人脸参考硬约束" in provider_prompt
    assert "参考图输入约束" in provider_prompt
    assert "脸部漂移" in captured["payload"]["parameters"]["negative_prompt"]
    assert "different jawline" in captured["payload"]["parameters"]["negative_prompt"]
    assert "sk-test-secret" not in json.dumps(generation, ensure_ascii=False)


def test_wanx_generation_uses_requested_profile_credentials_when_active_provider_differs(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "wanx",
                "base_url": "https://dashscope.aliyuncs.com/api/v1",
                "model": "wan2.6-t2i",
                "api_key": "sk-wanx-secret",
            }
        },
    )
    app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "kling",
                "base_url": "https://api-singapore.klingai.com",
                "model": "kling-v3",
                "api_key": "api-kling-secret",
            }
        },
    )
    captured = {"auth": None, "payload": None}

    def fake_urlopen(request, timeout=120):
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        if "multimodal-generation" in url:
            captured["auth"] = request.headers.get("Authorization")
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            body = json.dumps(
                {
                    "output": {
                        "choices": [
                            {
                                "message": {
                                    "content": [
                                        {
                                            "image": "https://example.test/generated.png",
                                            "type": "image",
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            ).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        body = b"\x89PNG\r\n\x1a\n"
        response = MagicMock()
        response.read.return_value = body
        response.headers.get_content_type.return_value = "image/png"
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *args: None
        return response

    with patch("persona_studio.server.urllib.request.urlopen", side_effect=fake_urlopen):
        create_status, create_response = app.api_response(
            "POST",
            "/api/generations",
            {
                "character_id": "lina",
                "mode": "文生图",
                "prompt": "商业产品摄影，不要人物",
                "count": 1,
                "size": "9:16",
                "image_model": "wan2.6-image",
                "image_model_label": "通义万象 · Wan2.6 Image",
            },
        )

    generation = create_response["generations"][0]
    assert create_status == 201
    assert generation["model_route"]["provider"] == "wanx"
    assert generation["model_route"]["real_generation"] is True
    assert generation["model_route"]["generation_kind"] == "t2i"
    assert captured["auth"] == "Bearer sk-wanx-secret"
    assert captured["payload"]["parameters"]["size"] == "960*1696"
    assert "api-kling-secret" not in str(create_response)
    assert "sk-wanx-secret" not in str(create_response)


def test_volcengine_ark_real_generation_calls_images_endpoint(tmp_path):
    # 火山引擎 (Volcano Ark / Doubao Seedream) text-to-image: a single Bearer
    # key + the OpenAI-compatible /images/generations endpoint should produce a
    # real generation (not a local-preview fallback).
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    settings_status, _ = app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "volcengine",
                "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                "model": "doubao-seedream-5-0-260128",
                "api_key": "ark-test-secret",
            }
        },
    )
    captured = {"url": None, "payload": None, "auth": None}

    def fake_urlopen(request, timeout=120):
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        if url.endswith("/images/generations"):
            captured["url"] = url
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            captured["auth"] = request.headers.get("Authorization")
            body = json.dumps({"data": [{"url": "https://example.test/ark-generated.png"}]}).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        body = b"\x89PNG\r\n\x1a\n"
        response = MagicMock()
        response.read.return_value = body
        response.headers.get_content_type.return_value = "image/png"
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *args: None
        return response

    with patch("persona_studio.server.urllib.request.urlopen", side_effect=fake_urlopen):
        create_status, create_response = app.api_response(
            "POST",
            "/api/generations",
            {
                "character_id": "lina",
                "mode": "文生图",
                "prompt": "a woman in soft morning light",
                "negative_prompt": "blurry, low quality",
                "count": 1,
                "size": "9:16",
            },
        )

    generation = create_response["generations"][0]
    assert settings_status == 200
    assert create_status == 201
    assert captured["url"] == "https://ark.cn-beijing.volces.com/api/v3/images/generations"
    assert captured["auth"] == "Bearer ark-test-secret"
    assert captured["payload"]["model"] == "doubao-seedream-5-0-260128"
    assert captured["payload"]["size"] == "1440x2560"
    assert captured["payload"]["prompt"]
    assert "避免：" in captured["payload"]["prompt"]  # negative prompt folded into prompt
    assert generation["model_route"]["mode"] == "external_api"
    assert generation["model_route"]["provider"] == "volcengine"
    assert generation["model_route"]["real_generation"] is True
    assert generation["image"].startswith("assets/generated/gen-")
    # API key must never leak into persisted/exported records.
    assert "ark-test-secret" not in json.dumps(generation, ensure_ascii=False)


def test_volcengine_ark_img2img_sends_reference_images_for_identity(tmp_path):
    # 火山引擎 (Seedream) image-to-image: face/scene references must reach the
    # /images/generations endpoint via the `image` field so the reference
    # actually conditions the result instead of silently degrading to t2i.
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    settings_status, _ = app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "volcengine",
                "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                "model": "doubao-seedream-5-0-260128",
                "api_key": "ark-test-secret",
            }
        },
    )
    captured = {"payload": None}

    def fake_urlopen(request, timeout=120):
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        if url.endswith("/images/generations"):
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            body = json.dumps({"data": [{"url": "https://example.test/ark-generated.png"}]}).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        body = b"\x89PNG\r\n\x1a\n"
        response = MagicMock()
        response.read.return_value = body
        response.headers.get_content_type.return_value = "image/png"
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *args: None
        return response

    with patch("persona_studio.server.urllib.request.urlopen", side_effect=fake_urlopen):
        create_status, create_response = app.api_response(
            "POST",
            "/api/generations",
            {
                "character_id": "lina",
                "mode": "图生图",
                "prompt": "沿用参考图构图，保持人物姿态和光线方向，身份锁定",
                "count": 1,
                "size": "3:4",
                "reference_guidance": [
                    {
                        "kind": "face",
                        "label": "人脸",
                        "items": [
                            {
                                "id": "face-main",
                                "label": "主图",
                                "image": "assets/persona-ref-1.png",
                                "prompt": "保持参考人脸五官比例和脸型",
                            }
                        ],
                    }
                ],
            },
        )

    generation = create_response["generations"][0]
    route = generation["model_route"]
    assert settings_status == 200
    assert create_status == 201
    assert route["real_generation"] is True
    assert route["generation_kind"] == "img2img"
    # The face reference must be carried into the Ark payload as a base64 image.
    image_field = captured["payload"]["image"]
    images = image_field if isinstance(image_field, list) else [image_field]
    assert images and all(str(img).startswith("data:image/") for img in images)
    assert "ark-test-secret" not in json.dumps(generation, ensure_ascii=False)


def test_fal_flux_ultra_real_generation_uses_identity_reference_image(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    settings_status, settings_response = app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "fal",
                "base_url": "https://fal.run",
                "model": "fal-ai/flux/ultra",
                "api_key": "fal-test-secret",
            }
        },
    )
    captured = {"url": None, "payload": None, "auth": None}

    def fake_urlopen(request, timeout=180):
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        if "kontext" in url:
            captured["url"] = url
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            captured["auth"] = request.headers.get("Authorization")
            body = json.dumps({"images": [{"url": "https://example.test/fal-generated.jpg"}]}).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        body = b"\xff\xd8\xff\xe0fakejpeg"
        response = MagicMock()
        response.read.return_value = body
        response.headers.get_content_type.return_value = "image/jpeg"
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *args: None
        return response

    with patch("persona_studio.server.urllib.request.urlopen", side_effect=fake_urlopen):
        create_status, create_response = app.api_response(
            "POST",
            "/api/generations",
            {
                "character_id": "lina",
                "mode": "图生图",
                "prompt": "沿用参考人脸，去掉眼镜，商业海报写真",
                "negative_prompt": "low quality",
                "count": 1,
                "size": "3:4",
                "reference_guidance": [
                    {
                        "kind": "face",
                        "label": "人脸",
                        "items": [
                            {
                                "id": "face-main",
                                "label": "主图",
                                "image": "assets/persona-ref-1.png",
                                "prompt": "保持参考人脸五官比例和脸型",
                            }
                        ],
                    }
                ],
            },
        )

    generation = create_response["generations"][0]
    assert settings_status == 200
    assert settings_response["settings"]["api"]["auth_configured"] is True
    assert create_status == 201
    assert captured["url"] == "https://fal.run/fal-ai/flux-pro/kontext/max"
    assert captured["auth"] == "Key fal-test-secret"
    # Kontext is instruction-based editing: it sends the source image + a removal
    # instruction with no mask (so no mask-shaped artifacts) and no Redux strength.
    assert captured["payload"]["guidance_scale"] == 2.5
    assert "raw" not in captured["payload"]
    assert captured["payload"]["num_images"] == 1
    assert captured["payload"]["output_format"] == "jpeg"
    assert captured["payload"]["image_url"].startswith("data:image/")
    assert "mask_url" not in captured["payload"]
    assert "image_prompt_strength" not in captured["payload"]
    assert "glasses" in captured["payload"]["prompt"].lower()
    assert generation["conditioning_manifest"]["identity_edit_mode"] is True
    assert "身份编辑模式" in generation["conditioning_manifest"]["provider_prompt"]
    assert "眼镜编辑约束" in generation["conditioning_manifest"]["provider_prompt"]
    assert "风格约束" not in generation["conditioning_manifest"]["provider_prompt"]
    assert generation["model_route"]["provider"] == "fal"
    assert generation["model_route"]["model"] == "fal-ai/flux-pro/kontext/max"
    assert generation["model_route"]["identity_edit_route"] is True
    assert generation["model_route"]["identity_edit_routed_from"] == "fal-ai/flux-pro/v1.1-ultra"
    assert generation["model_route"]["real_generation"] is True
    assert generation["model_route"]["generation_kind"] == "img2img"
    assert generation["image"].startswith("assets/generated/gen-")
    assert "fal-test-secret" not in json.dumps(generation, ensure_ascii=False)
    assert app._fal_generation_endpoint(
        "https://fal.run/fal-ai/flux/ultra",
        "fal-ai/flux/ultra",
    ) == "https://fal.run/fal-ai/flux-pro/v1.1-ultra"


def test_identity_edit_mode_corrects_chinese_eye_glasses_typo(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    assert app._prompt_requests_remove_eyewear("把眼镜去掉") is True
    assert app._is_identity_preserving_edit("把眼镜去掉，人物要求一致性，严格遵守人物的脸型。不得有差异。") is True
    character = app.manager.get_character("alex")
    packet = app.manager.build_conditioning(
        "alex",
        prompt="把眼睛去掉，严格遵守人物一致性。",
        state="calm",
        identity_weight=0.92,
        style_weight=0.6,
        lora_id="brand-campaign",
        lora_weight=0.62,
        enforce_identity_priority=True,
    )
    manifest = app._conditioning_manifest(
        character=character,
        packet=packet,
        prompt="把眼睛去掉，严格遵守人物一致性。",
        negative_prompt="模糊，低质量",
        state="calm",
        mode="图生图",
        reference_guidance=[
            {
                "kind": "face",
                "label": "人脸",
                "items": [
                    {
                        "id": "face-main",
                        "label": "主图",
                        "image": "assets/persona-ref-1.png",
                        "prompt": "保持参考人脸五官比例和脸型",
                    }
                ],
            }
        ],
        subject_hint="portrait",
    )

    assert manifest["identity_edit_mode"] is True
    assert "如果用户写成“眼睛去掉”，按“眼镜去掉”理解" in manifest["provider_prompt"]
    assert "保留双眼自然完整" in manifest["provider_prompt"]
    assert "missing eyes" in manifest["provider_negative_prompt"]
    assert "eyeglasses" in manifest["provider_negative_prompt"]
    assert "风格约束" not in manifest["provider_prompt"]


def test_eyewear_inpaint_mask_matches_reference_dimensions(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    mask_url = app._eyewear_inpaint_mask_data_url("assets/persona-ref-1.png")

    assert mask_url
    assert mask_url.startswith("data:image/png;base64,")
    mask_bytes = base64.b64decode(mask_url.split(",", 1)[1])
    assert mask_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    mask_width = int.from_bytes(mask_bytes[16:20], "big")
    mask_height = int.from_bytes(mask_bytes[20:24], "big")
    source_width, source_height = app._image_dimensions(Path("prototype/assets/persona-ref-1.png"))
    assert (mask_width, mask_height) == (source_width, source_height)


def test_canvas_edit_mask_matches_source_dimensions(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    mask_url = app._canvas_edit_mask_data_url(
        "assets/persona-ref-1.png",
        {
            "version": 1,
            "canvas_width": 640,
            "canvas_height": 852,
            "bounds": {"x": 0.12, "y": 0.18, "width": 0.18, "height": 0.08},
            "strokes": [
                {
                    "brush": 0.05,
                    "points": [{"x": 0.12, "y": 0.18}, {"x": 0.24, "y": 0.22}, {"x": 0.31, "y": 0.26}],
                }
            ],
        },
    )
    assert mask_url
    mask_bytes = base64.b64decode(mask_url.split(",", 1)[1])
    assert mask_bytes.startswith(b"\x89PNG\r\n\x1a\n")
    mask_width = int.from_bytes(mask_bytes[16:20], "big")
    mask_height = int.from_bytes(mask_bytes[20:24], "big")
    source_width, source_height = app._image_dimensions(Path("prototype/assets/persona-ref-1.png"))
    assert (mask_width, mask_height) == (source_width, source_height)


def test_fal_identity_edit_route_upgrades_eyewear_and_other_edits_to_kontext(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    normal_route = {
        "mode": "external_api",
        "provider": "fal",
        "model": "fal-ai/flux-pro/v1.1-ultra",
        "label": "fal.ai · FLUX 1.1 Pro Ultra",
        "configured": True,
    }

    unchanged = app._maybe_upgrade_identity_edit_route(normal_route, {"identity_edit_mode": False})
    eyewear_upgraded = app._maybe_upgrade_identity_edit_route(
        normal_route,
        {"identity_edit_mode": True, "source_prompt": "把眼镜去掉，人物不变。"},
    )
    edit_upgraded = app._maybe_upgrade_identity_edit_route(
        normal_route,
        {"identity_edit_mode": True, "source_prompt": "只把背景换成灰色，人物不变。"},
    )

    assert unchanged["model"] == "fal-ai/flux-pro/v1.1-ultra"
    # Auto eyewear removal → Kontext instruction edit (no mask, keeps the person).
    assert eyewear_upgraded["model"] == "fal-ai/flux-pro/kontext/max"
    assert eyewear_upgraded["identity_edit_route"] is True
    assert eyewear_upgraded["identity_edit_routed_from"] == "fal-ai/flux-pro/v1.1-ultra"
    assert edit_upgraded["model"] == "fal-ai/flux-pro/kontext/max"


def test_remove_eyewear_detection_covers_quchu_and_subject_phrasing(tmp_path):
    # User-reported miss: "只把眼镜取掉，人物主体不变。" used 取掉 (not 去掉) and
    # 人物主体不变 (not 人物不变), so the old phrase list failed to detect the
    # identity edit and the request fell through to plain v1.1-ultra Redux,
    # which kept the glasses and drifted the face. Detection must now catch it
    # and route the edit to the identity-preserving erase model.
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    prompt = "只把眼镜取掉，人物主体不变。"
    assert app._prompt_requests_remove_eyewear(prompt) is True
    assert app._is_identity_preserving_edit(prompt) is True
    # Other natural removal verbs/nouns also resolve via the combinatorial path.
    assert app._prompt_requests_remove_eyewear("把墨镜摘下来") is True
    assert app._prompt_requests_remove_eyewear("拿掉太阳镜") is True
    # Must not over-trigger when the user wants to KEEP the eyewear.
    assert app._prompt_requests_remove_eyewear("保持眼镜不变，换个发型") is False
    assert app._prompt_requests_remove_eyewear("帮我把背景换成蓝色") is False
    # Subject-preservation phrasing alone still marks an identity edit.
    assert app._is_identity_preserving_edit("把背景换成灰色，主体不变") is True

    route = {
        "mode": "external_api",
        "provider": "fal",
        "model": "fal-ai/flux-pro/v1.1-ultra",
        "label": "fal.ai · FLUX 1.1 Pro Ultra",
        "configured": True,
    }
    upgraded = app._maybe_upgrade_identity_edit_route(
        route, {"identity_edit_mode": True, "source_prompt": prompt}
    )
    # Auto eyewear removal (no user-drawn mask) routes to Kontext, the
    # instruction-based editor that removes the glasses without a mask while
    # keeping the same person.
    assert upgraded["model"] == "fal-ai/flux-pro/kontext/max"
    assert upgraded["identity_edit_route"] is True


def test_bfl_flux_2_max_real_generation_polls_and_downloads_image(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    settings_status, settings_response = app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "flux",
                "base_url": "https://api.bfl.ai/v1",
                "model": "flux-2-max",
                "api_key": "bfl-test-secret",
            }
        },
    )
    captured = {"create_url": None, "poll_url": None, "payload": None, "key": None}

    def fake_urlopen(request, timeout=180):
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        if url.endswith("/flux-2-max"):
            captured["create_url"] = url
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            captured["key"] = request.headers.get("X-key") or request.headers.get("x-key")
            body = json.dumps(
                {
                    "id": "bfl-task-123",
                    "polling_url": "https://api.bfl.ai/v1/get_result?id=bfl-task-123",
                }
            ).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        if "get_result" in url:
            captured["poll_url"] = url
            body = json.dumps(
                {
                    "status": "Ready",
                    "result": {"sample": "https://example.test/bfl-generated.png"},
                }
            ).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        response = MagicMock()
        response.read.return_value = b"\x89PNG\r\n\x1a\n"
        response.headers.get_content_type.return_value = "image/png"
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *args: None
        return response

    with patch("persona_studio.server.urllib.request.urlopen", side_effect=fake_urlopen):
        create_status, create_response = app.api_response(
            "POST",
            "/api/generations",
            {
                "character_id": "lina",
                "mode": "文生图",
                "prompt": "high-end skincare bottle on stone table, clean commercial photography",
                "negative_prompt": "people, face, low quality",
                "count": 1,
                "size": "16:9",
                "image_model": "flux-2-max",
                "image_model_label": "FLUX · FLUX.2 Max",
            },
        )

    generation = create_response["generations"][0]
    assert settings_status == 200
    assert settings_response["settings"]["api"]["auth_configured"] is True
    assert create_status == 201
    assert captured["create_url"] == "https://api.bfl.ai/v1/flux-2-max"
    assert captured["poll_url"] == "https://api.bfl.ai/v1/get_result?id=bfl-task-123"
    assert captured["key"] == "bfl-test-secret"
    assert captured["payload"]["width"] == 1920
    assert captured["payload"]["height"] == 1088
    assert captured["payload"]["output_format"] == "jpeg"
    assert "Avoid:" in captured["payload"]["prompt"]
    assert generation["model_route"]["provider"] == "flux"
    assert generation["model_route"]["real_generation"] is True
    assert generation["model_route"]["generation_kind"] == "t2i"
    assert generation["image"].startswith("assets/generated/gen-")
    assert "bfl-test-secret" not in json.dumps(generation, ensure_ascii=False)
    assert app._bfl_generation_endpoint("https://api.bfl.ai/v1", "black-forest-labs/flux.2-max") == "https://api.bfl.ai/v1/flux-2-max"


def test_bfl_flux_img2img_sends_reference_images_for_identity(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "flux",
                "base_url": "https://api.bfl.ai/v1",
                "model": "flux-2-max",
                "api_key": "bfl-test-secret",
            }
        },
    )
    captured = {"payload": None, "key": None}

    def fake_urlopen(request, timeout=180):
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        if url.endswith("/flux-2-max"):
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            captured["key"] = request.headers.get("X-key") or request.headers.get("x-key")
            body = json.dumps(
                {
                    "id": "bfl-edit-123",
                    "polling_url": "https://api.bfl.ai/v1/get_result?id=bfl-edit-123",
                }
            ).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        if "get_result" in url:
            body = json.dumps(
                {
                    "status": "Ready",
                    "result": {"sample": "https://example.test/bfl-edited.jpg"},
                }
            ).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        response = MagicMock()
        response.read.return_value = b"\xff\xd8\xff\xd9"
        response.headers.get_content_type.return_value = "image/jpeg"
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *args: None
        return response

    with patch("persona_studio.server.urllib.request.urlopen", side_effect=fake_urlopen):
        create_status, create_response = app.api_response(
            "POST",
            "/api/generations",
            {
                "character_id": "lina",
                "mode": "图生图",
                "prompt": "保持参考人脸，生成商业写真",
                "negative_prompt": "low quality",
                "count": 1,
                "size": "3:4",
                "image_model": "flux-2-max",
                "image_model_label": "FLUX · FLUX.2 Max",
                "reference_guidance": [
                    {
                        "kind": "face",
                        "items": [
                            {"id": "face-main", "label": "主图", "image": "assets/persona-ref-1.png"}
                        ],
                    },
                    {
                        "kind": "scene",
                        "items": [
                            {"id": "scene-ref", "label": "环境", "image": "assets/persona-ref-2.png"}
                        ],
                    },
                ],
            },
        )

    generation = create_response["generations"][0]
    assert create_status == 201
    assert captured["key"] == "bfl-test-secret"
    assert captured["payload"]["input_image"]
    assert captured["payload"]["input_image_2"]
    assert not captured["payload"]["input_image"].startswith("data:image/")
    assert "provided input image references" in captured["payload"]["prompt"]
    assert "Avoid:" in captured["payload"]["prompt"]
    assert generation["model_route"]["provider"] == "flux"
    assert generation["model_route"]["real_generation"] is True
    assert generation["model_route"]["generation_kind"] == "img2img"
    assert generation["image"].startswith("assets/generated/gen-")
    assert "bfl-test-secret" not in json.dumps(generation, ensure_ascii=False)


def test_kling_real_generation_polls_task_and_downloads_image_with_ak_sk(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    settings_status, settings_response = app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "kling",
                "base_url": "https://api-singapore.klingai.com",
                "model": "kling/kling-v3-omni-image-generation",
                "api_key": "stale-kling-api-key",
                "access_key": "kling-ak-test",
                "secret_key": "kling-sk-secret",
            }
        },
    )
    captured = {"create_url": None, "query_url": None, "payload": None, "auth": None}

    def fake_urlopen(request, timeout=120):
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        if url.endswith("/v1/images/generations"):
            captured["create_url"] = url
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            captured["auth"] = request.headers.get("Authorization")
            body = json.dumps({"code": 0, "data": {"task_id": "task-123", "task_status": "submitted"}}).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        if url.endswith("/v1/images/generations/task-123"):
            captured["query_url"] = url
            body = json.dumps(
                {
                    "code": 0,
                    "data": {
                        "task_id": "task-123",
                        "task_status": "succeed",
                        "task_result": {
                            "images": [
                                {"url": "https://example.test/kling-generated.png"}
                            ]
                        },
                    },
                }
            ).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        body = b"\x89PNG\r\n\x1a\n"
        response = MagicMock()
        response.read.return_value = body
        response.headers.get_content_type.return_value = "image/png"
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *args: None
        return response

    with (
        patch("persona_studio.server.time.time", return_value=1000),
        patch("persona_studio.server.urllib.request.urlopen", side_effect=fake_urlopen),
    ):
        create_status, create_response = app.api_response(
            "POST",
            "/api/generations",
            {
                "character_id": "lina",
                "mode": "文生图",
                "prompt": "a cinematic portrait in morning light",
                "negative_prompt": "blurry, low quality",
                "count": 1,
                "size": "9:16",
            },
        )

    generation = create_response["generations"][0]
    auth_token = captured["auth"].removeprefix("Bearer ")
    jwt_payload = auth_token.split(".")[1] + "=="
    decoded_payload = json.loads(base64.urlsafe_b64decode(jwt_payload.encode("ascii")).decode("utf-8"))

    assert settings_status == 200
    assert settings_response["settings"]["api"]["auth_configured"] is True
    assert create_status == 201
    assert captured["create_url"] == "https://api-singapore.klingai.com/v1/images/generations"
    assert captured["query_url"] == "https://api-singapore.klingai.com/v1/images/generations/task-123"
    assert captured["payload"]["model_name"] == "kling-v3"
    assert captured["payload"]["aspect_ratio"] == "9:16"
    assert "blurry, low quality" in captured["payload"]["negative_prompt"]
    assert "face drift" in captured["payload"]["negative_prompt"]
    assert "image" not in captured["payload"]
    assert decoded_payload == {"iss": "kling-ak-test", "exp": 2800, "nbf": 995}
    assert auth_token != "stale-kling-api-key"
    assert "kling-sk-secret" not in auth_token
    assert generation["model_route"]["mode"] == "external_api"
    assert generation["model_route"]["provider"] == "kling"
    assert generation["model_route"]["real_generation"] is True
    assert generation["model_route"]["generation_kind"] == "t2i"
    assert generation["image"].startswith("assets/generated/gen-")
    assert "kling-sk-secret" not in json.dumps(generation, ensure_ascii=False)


def test_kling_img2img_sends_face_reference_without_negative_prompt(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    settings_status, _ = app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "kling",
                "base_url": "https://api-singapore.klingai.com/v1",
                "model": "kling-v3",
                "api_key": "kling-api-key",
            }
        },
    )
    captured = {"payload": None, "auth": None}

    def fake_urlopen(request, timeout=120):
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        if url.endswith("/images/generations"):
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            captured["auth"] = request.headers.get("Authorization")
            body = json.dumps({"code": 0, "data": {"task_id": "task-ref", "task_status": "submitted"}}).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        if url.endswith("/images/generations/task-ref"):
            body = json.dumps(
                {
                    "code": 0,
                    "data": {
                        "task_status": "succeed",
                        "task_result": {"images": [{"url": "https://example.test/kling-ref.png"}]},
                    },
                }
            ).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        body = b"\x89PNG\r\n\x1a\n"
        response = MagicMock()
        response.read.return_value = body
        response.headers.get_content_type.return_value = "image/png"
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *args: None
        return response

    with patch("persona_studio.server.urllib.request.urlopen", side_effect=fake_urlopen):
        create_status, create_response = app.api_response(
            "POST",
            "/api/generations",
            {
                "character_id": "lina",
                "mode": "图生图",
                "prompt": "沿用参考图人脸结构，换成雨夜街道风格",
                "negative_prompt": "low quality",
                "count": 1,
                "size": "3:4",
                "reference_guidance": [
                    {
                        "kind": "face",
                        "label": "人脸",
                        "items": [
                            {
                                "id": "face-main",
                                "label": "主图",
                                "image": "assets/persona-ref-1.png",
                                "prompt": "保持参考人脸五官比例和脸型",
                            }
                        ],
                    }
                ],
            },
        )

    route = create_response["generations"][0]["model_route"]
    assert settings_status == 200
    assert create_status == 201
    assert captured["auth"] == "Bearer kling-api-key"
    assert captured["payload"]["image"]
    assert captured["payload"]["image_reference"] == "face"
    assert captured["payload"]["aspect_ratio"] == "3:4"
    assert "negative_prompt" not in captured["payload"]
    assert route["provider"] == "kling"
    assert route["real_generation"] is True
    assert route["generation_kind"] == "img2img"


def test_kling_generation_retries_auth_and_region_before_failing_to_local(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "kling",
                "base_url": "https://api-singapore.klingai.com",
                "model": "kling-v3",
                "api_key": "direct-kling-fallback",
                "access_key": "legacy-ak-not-found",
                "secret_key": "legacy-sk-secret",
            }
        },
    )
    attempts: list[tuple[str, str]] = []

    def unauthorized(url):
        return urllib.error.HTTPError(
            url,
            401,
            "Unauthorized",
            {},
            io.BytesIO(b'{"code":1002,"message":"access key not found"}'),
        )

    def fake_urlopen(request, timeout=120):
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        auth = request.headers.get("Authorization") or ""
        if url.endswith("/v1/images/generations"):
            attempts.append((url, auth))
            if url == "https://api.klingai.com/v1/images/generations" and auth == "Bearer direct-kling-fallback":
                body = json.dumps({"code": 0, "data": {"task_id": "task-fallback"}}).encode("utf-8")
                response = MagicMock()
                response.read.return_value = body
                response.__enter__ = lambda self: self
                response.__exit__ = lambda self, *args: None
                return response
            raise unauthorized(url)

        if url == "https://api.klingai.com/v1/images/generations/task-fallback":
            body = json.dumps(
                {
                    "code": 0,
                    "data": {
                        "task_status": "succeed",
                        "task_result": {"images": [{"url": "https://example.test/kling-fallback.png"}]},
                    },
                }
            ).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        body = b"\x89PNG\r\n\x1a\n"
        response = MagicMock()
        response.read.return_value = body
        response.headers.get_content_type.return_value = "image/png"
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *args: None
        return response

    with patch("persona_studio.server.urllib.request.urlopen", side_effect=fake_urlopen):
        create_status, create_response = app.api_response(
            "POST",
            "/api/generations",
            {
                "character_id": "lina",
                "mode": "文生图",
                "prompt": "consistent character portrait",
                "count": 1,
                "size": "1:1",
            },
        )

    assert create_status == 201
    assert attempts[0][0] == "https://api-singapore.klingai.com/v1/images/generations"
    assert attempts[-1] == ("https://api.klingai.com/v1/images/generations", "Bearer direct-kling-fallback")
    assert len(attempts) == 4
    assert create_response["generations"][0]["model_route"]["provider"] == "kling"
    assert create_response["generations"][0]["model_route"]["real_generation"] is True
    assert "legacy-sk-secret" not in json.dumps(create_response, ensure_ascii=False)


def test_wanx_img2img_real_generation_uses_reference_images(tmp_path):
    app = PersonaStudioApp(static_dir=Path("prototype"), data_path=tmp_path / "state.json")
    settings_status, _ = app.api_response(
        "POST",
        "/api/settings",
        {
            "api": {
                "enabled": True,
                "provider": "wanx",
                "base_url": "https://dashscope.aliyuncs.com/api/v1",
                "model": "wan2.6-image",
                "api_key": "sk-test-secret",
            }
        },
    )
    captured = {"payload": None}

    def fake_urlopen(request, timeout=120):
        url = request.full_url if hasattr(request, "full_url") else request.get_full_url()
        if "multimodal-generation" in url:
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            body = json.dumps(
                {
                    "output": {
                        "choices": [
                            {
                                "message": {
                                    "content": [
                                        {
                                            "image": "https://example.test/generated.png",
                                            "type": "image",
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            ).encode("utf-8")
            response = MagicMock()
            response.read.return_value = body
            response.__enter__ = lambda self: self
            response.__exit__ = lambda self, *args: None
            return response

        body = b"\x89PNG\r\n\x1a\n"
        response = MagicMock()
        response.read.return_value = body
        response.headers.get_content_type.return_value = "image/png"
        response.__enter__ = lambda self: self
        response.__exit__ = lambda self, *args: None
        return response

    with patch("persona_studio.server.urllib.request.urlopen", side_effect=fake_urlopen):
        create_status, create_response = app.api_response(
            "POST",
            "/api/generations",
            {
                "character_id": "lina",
                "mode": "图生图",
                "prompt": "沿用参考图构图，保持人物姿态和光线方向，身份锁定",
                "count": 1,
                "size": "3:4",
                "reference_guidance": [
                    {
                        "kind": "face",
                        "label": "人脸",
                        "items": [
                            {
                                "id": "face-main",
                                "label": "主图",
                                "image": "assets/persona-ref-1.png",
                                "prompt": "保持参考人脸五官比例和脸型",
                            }
                        ],
                    }
                ],
            },
        )

    route = create_response["generations"][0]["model_route"]
    content = captured["payload"]["input"]["messages"][0]["content"]
    generation = create_response["generations"][0]
    assert settings_status == 200
    assert create_status == 201
    assert route["real_generation"] is True
    assert route["generation_kind"] == "img2img"
    assert generation["image"].startswith("assets/generated/gen-")
    assert generation["conditioning_manifest"]["uses_identity_lock"] is True
    assert generation["conditioning_manifest"]["prompt_hash"]
    assert captured["payload"]["model"] == "wan2.6-image"
    assert captured["payload"]["parameters"]["enable_interleave"] is False
    assert "同一角色身份锁定" in content[0]["text"]
    assert "参考图约束" in content[0]["text"]
    assert "图生图约束" in content[0]["text"]
    assert any("image" in item for item in content[1:])
