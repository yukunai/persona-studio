import pytest

from persona_studio.identity_model import IdentityModel


def test_identity_model_encodes_feature_bundle():
    model = IdentityModel()

    bundle = model.encode_faces(["face-a", "face-b", "face-c"])

    assert len(bundle["vector"]) == 512
    assert bundle["reference_count"] == 3
    assert bundle["constraints"]["eye_distance"] is not None
    assert bundle["constraints"]["jaw_shape"] in {"oval", "soft_square", "heart", "angular"}
    assert bundle["constraints"]["reference_stability"] >= 0


def test_identity_model_enforces_reference_count():
    model = IdentityModel()

    with pytest.raises(ValueError, match="3-20 face images"):
        model.encode_faces(["only-one"])


def test_identity_model_consistency_report_requires_encoded_identity():
    model = IdentityModel()

    assert model.verify_consistency("generated") is False
    with pytest.raises(ValueError, match="encode_faces"):
        model.consistency_report("generated")
