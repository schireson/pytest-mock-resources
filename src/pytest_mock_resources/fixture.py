import uuid


def generate_fixture_id(enabled: bool = True, name=""):
    if enabled:
        uuid_str = str(uuid.uuid4()).replace("-", "_")
        return "_".join(["pmr_template", name, uuid_str])
    return None
