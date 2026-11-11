from persona_studio.character_manager import CharacterManager

def test_character_versioning_flow():
    manager = CharacterManager()
    
    # Create v1
    character = manager.create_character(
        "Lina",
        {"face_images": ["face-1", "face-2", "face-3"]},
        "cinematic"
    )
    assert character["version"] == 1
    assert len(character["versions"]) == 1
    assert character["versions"][0]["note"] == "initial"
    
    # Create v2 with more faces
    v2_snapshot = manager.create_version(
        "lina",
        {"face_images": ["face-1", "face-2", "face-3", "face-4", "face-5"]},
        note="train v2"
    )
    
    updated_character = manager.get_character("lina")
    assert updated_character["version"] == 2
    assert len(updated_character["versions"]) == 2
    assert updated_character["versions"][1]["note"] == "train v2"
    assert updated_character["identity"]["reference_count"] == 5

def test_character_versioning_style_update():
    manager = CharacterManager()
    manager.create_character("Lina", {"face_images": ["face-1", "face-2", "face-3"]}, "cinematic")
    
    # Update style in v2
    manager.create_version("lina", style_config="anime", note="switch to anime")
    
    updated = manager.get_character("lina")
    assert updated["version"] == 2
    assert updated["style"]["preset"] == "anime"
    assert updated["versions"][1]["style_preset"] == "anime"


def test_character_version_restore_creates_audited_version():
    manager = CharacterManager()
    manager.create_character("Lina", {"face_images": ["face-1", "face-2", "face-3"]}, "cinematic")
    manager.create_version("lina", style_config="anime", note="switch to anime")

    restored = manager.restore_version("lina", 1)
    updated = manager.get_character("lina")

    assert restored["version"] == 3
    assert restored["restored_from"] == 1
    assert updated["version"] == 3
    assert updated["style"]["preset"] == "cinematic"
    assert updated["versions"][-1]["can_restore"] is True
    assert updated["versions"][-1]["style_snapshot"]["preset"] == "cinematic"
