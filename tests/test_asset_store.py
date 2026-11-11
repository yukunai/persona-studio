from persona_studio.asset_store import CharacterAssetStore
from persona_studio.demo_data import create_demo_manager


def test_asset_store_round_trips_characters_versions_and_memory(tmp_path):
    data_path = tmp_path / "persona_state.json"
    manager = create_demo_manager()
    manager.create_version("lina", {"face_images": ["lina-v2-a", "lina-v2-b", "lina-v2-c"]}, "commercial", "train v2")
    manager.record_scene("lina", "persistent scene", "img.png", "three-quarter", 1.0, "commercial", "confident")

    store = CharacterAssetStore(data_path)
    generations = [{
        "id": "gen-1", 
        "character_id": "lina", 
        "favorite": True,
        "negative_prompt": "low quality",
        "lora_id": "soft-daylight-pro",
        "lora_weight": 0.8
    }]
    projects = [{
        "id": "brand-ip",
        "name": "Brand IP",
        "character_ids": ["lina"],
        "user_segment": "商业用户",
    }]
    settings = {
        "api": {
            "enabled": True,
            "provider": "openai-compatible",
            "base_url": "https://example.test/v1",
            "model": "image-model",
            "api_key": "sk-test-secret",
        }
    }
    account = {
        "plan_id": "upgrade-business",
        "credits_remaining": 7990,
        "credits_used": 10,
    }
    store.save_state(manager, generations, projects, settings, account=account)
    loaded, loaded_generations = store.load_state()
    _workspace_manager, _workspace_generations, loaded_projects = store.load_workspace_state()
    loaded_settings = store.load_settings()
    loaded_account = store.load_account()

    assert loaded.get_character("lina")["version"] == 2
    assert loaded.get_character("lina")["versions"][-1]["note"] == "train v2"
    assert loaded.get_character("lina")["memory"]["best_angles"][0]["pose"] == "three-quarter"
    assert loaded_generations[0]["negative_prompt"] == "low quality"
    assert loaded_generations[0]["lora_id"] == "soft-daylight-pro"
    assert loaded_projects[0]["user_segment"] == "商业用户"
    assert any(entry["prompt"] == "persistent scene" for entry in loaded.memory_store.logs)
    assert loaded_settings["api"]["model"] == "image-model"
    assert loaded_settings["api"]["api_key"] == "sk-test-secret"
    assert loaded_account["plan_id"] == "upgrade-business"
    assert loaded_account["credits_remaining"] == 7990
