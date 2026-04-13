""""
Responsabilidad:

validar API keys
resolver usuario/roles a partir de la key

"""

from typing import Optional

from app.core.config import API_KEYS, ApiKeyRecord


def authenticate_api_key(api_key: str) -> Optional[ApiKeyRecord]:
    return API_KEYS.get(api_key)