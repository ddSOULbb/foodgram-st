import re
from rest_framework.serializers import ValidationError


def validate_username(name):
    """Проверка никнейма"""
    if name == 'me' or not re.match(r'^[\w.@+-]+$', name):
        raise ValidationError('Некорректный никнейм')
    return name
