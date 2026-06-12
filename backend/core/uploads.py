import uuid
from pathlib import PurePosixPath


def _family_scoped_path(prefix, instance, filename):
    extension = PurePosixPath(filename).suffix.lower()
    return f"{prefix}/{instance.family_id}/{uuid.uuid4().hex}{extension}"


def medicine_photo_upload_to(instance, filename):
    return _family_scoped_path("medicine_photos", instance, filename)


def medicine_instruction_upload_to(instance, filename):
    return _family_scoped_path("medicine_instructions", instance, filename)
