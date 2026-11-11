from persona_studio.character_manager import CharacterManager

def test_character_manager_initialization():
    manager = CharacterManager()
    assert manager.characters == {}

def test_character_manager_get_nonexistent():
    manager = CharacterManager()
    assert manager.get_character("none") is None

def test_character_manager_creates_character_with_identity_and_style():
    manager = CharacterManager()

    character = manager.create_character(
        "Lina",
        {"face_images": ["face-a", "face-b", "face-c"]},
        "cinematic portrait soft daylight",
    )

    assert character["id"] == "lina"
    assert character["version"] == 1
    assert character["identity"]["reference_count"] == 3
    assert character["style"]["preset"] == "cinematic"
    assert character["versions"][0]["note"] == "initial"

def test_character_manager_builds_conditioning_and_records_memory():
    manager = CharacterManager()
    manager.create_character("Lina", {"face_images": ["face-a", "face-b", "face-c"]}, "commercial")

    packet = manager.build_conditioning(
        "lina",
        "walking in morning light",
        "calm",
        identity_weight=0.82,
        style_weight=0.58,
        lora_id="brand-campaign",
        lora_weight=0.61,
    )
    entry = manager.record_scene("lina", "walking in morning light", "img.png", "three-quarter", 0.94, "commercial")
    character = manager.get_character("lina")

    assert packet["character_id"] == "lina"
    assert packet["weights"]["identity"] == 0.82
    assert packet["weights"]["style"] == 0.58
    assert packet["lora"]["id"] == "brand-campaign"
    assert packet["lora"]["weight"] == 0.61
    assert entry["success_score"] == 0.94
    assert character["memory"]["best_angles"][0]["pose"] == "three-quarter"
