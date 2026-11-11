from .character_manager import CharacterManager


def create_demo_manager() -> CharacterManager:
    manager = CharacterManager()

    manager.create_character(
        "Lina",
        {
            "character_id": "lina",
            "face_images": [
                "lina-front-soft-daylight",
                "lina-three-quarter-morning",
                "lina-studio-headshot",
            ],
        },
        "cinematic portrait soft daylight 50mm",
    )
    manager.create_character(
        "Kira",
        {
            "character_id": "kira",
            "face_images": [
                "kira-front-anime",
                "kira-rooftop-bloom",
                "kira-city-neon",
            ],
        },
        "anime clean line soft bloom",
    )
    manager.create_character(
        "Alex",
        {
            "character_id": "alex",
            "face_images": [
                "alex-commercial-front",
                "alex-brand-profile",
                "alex-studio-key-light",
            ],
        },
        "commercial studio key light brand campaign",
    )

    manager.characters["lina"]["consistency_score"] = 0.92
    manager.characters["kira"]["consistency_score"] = 0.87
    manager.characters["alex"]["consistency_score"] = 0.89

    manager.record_scene(
        "lina",
        "coffee shop morning",
        "assets/lina-morning.svg",
        "front",
        0.91,
        "soft daylight",
        "calm",
    )
    manager.record_scene(
        "lina",
        "rainy night street",
        "assets/lina-morning.svg",
        "three-quarter",
        0.88,
        "cinematic",
        "confident",
    )
    manager.record_scene(
        "lina",
        "studio headshot",
        "assets/lina-morning.svg",
        "front",
        0.94,
        "commercial",
        "calm",
    )
    manager.record_scene("kira", "school rooftop", "assets/lina-morning.svg", "front", 0.85, "anime", "playful")
    manager.record_scene("kira", "city neon", "assets/lina-morning.svg", "side", 0.79, "anime", "confident")
    manager.record_scene("alex", "studio campaign", "assets/lina-morning.svg", "front", 0.9, "commercial", "calm")
    manager.record_scene("alex", "product launch", "assets/lina-morning.svg", "three-quarter", 0.86, "commercial", "confident")

    return manager
