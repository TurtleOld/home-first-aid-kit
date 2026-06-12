from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

INSTRUCTION_FILE_ALLOWED_EXTENSIONS = ["pdf", "jpg", "jpeg", "png", "webp"]
INSTRUCTION_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10 MB

validate_instruction_file_extension = FileExtensionValidator(
    allowed_extensions=INSTRUCTION_FILE_ALLOWED_EXTENSIONS,
)


def validate_instruction_file_size(file):
    if file.size > INSTRUCTION_FILE_MAX_SIZE:
        raise ValidationError("Файл слишком большой: максимум 10 МБ.")


def validate_instruction_file_content(file):
    head = file.read(12)
    file.seek(0)

    if head.startswith(b"%PDF-"):
        return
    if head.startswith(b"\xff\xd8\xff"):  # JPEG
        return
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return

    raise ValidationError("Неподдерживаемый формат файла. Разрешены PDF, JPEG, PNG, WEBP.")
