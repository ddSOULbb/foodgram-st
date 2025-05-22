import re

from foodgram.constants import REGEX_NAME, RESERVED_USERNAMES
from rest_framework.serializers import ValidationError


def validate_username(value):
    """Проверка никнейма."""
    if not re.match(REGEX_NAME, value):
        raise ValidationError("Некорректный никнейм.")
    elif value in RESERVED_USERNAMES:
        raise ValidationError("Это имя зарезервировано.")
    return value
