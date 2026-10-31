from pathlib import Path

import yaml

DATA_CLASS_ORDER = ["public", "internal", "confidential", "restricted"]
REGISTRY_PATH = Path(__file__).resolve().parent.parent / "config" / "approved_models.yaml"


def load_registry(path: Path = REGISTRY_PATH) -> dict:
    data = yaml.safe_load(path.read_text())
    return {m["id"]: m for m in data["models"]}


def check_model_access(model_id: str, environment: str, data_class: str, registry: dict) -> tuple[bool, str]:
    model = registry.get(model_id)
    if model is None:
        return False, "model_not_registered"
    if model["status"] != "approved":
        return False, "model_not_approved"
    if environment not in model["environments"]:
        return False, "environment_not_allowed"
    if data_class not in DATA_CLASS_ORDER:
        return False, "unknown_data_class"
    if DATA_CLASS_ORDER.index(data_class) > DATA_CLASS_ORDER.index(model["max_data_class"]):
        return False, "data_class_too_high"
    return True, "allowed"
