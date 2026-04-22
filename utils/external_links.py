from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator


KNOWN_EXTERNAL_STORAGE_HOSTS = (
    'docs.google.com',
    'drive.google.com',
    'dropbox.com',
    'www.dropbox.com',
    'onedrive.live.com',
    '1drv.ms',
)

EXTERNAL_LINK_HELP_TEXT = (
    'Cole um link do Google Docs, Google Drive, Dropbox ou outra nuvem. '
    'Verifique se o documento está compartilhado com permissão de visualização.'
)


def validate_external_resource_url(value):
    """Valida links externos usados no lugar de upload local."""
    if not value:
        return

    validator = URLValidator(schemes=['http', 'https'])
    try:
        validator(value)
    except ValidationError as exc:
        raise ValidationError(
            'Informe um link válido começando com http:// ou https://.'
        ) from exc

    parsed = urlparse(value)
    if not parsed.netloc:
        raise ValidationError('Informe um link externo completo.')


def is_known_storage_host(value):
    if not value:
        return False
    host = urlparse(value).netloc.lower()
    return any(host == known or host.endswith(f'.{known}') for known in KNOWN_EXTERNAL_STORAGE_HOSTS)
