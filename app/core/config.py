"""
Responsabilidad:

definir el constructor del contexto
funciones auxiliares de contexto

"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ApiKeyRecord:
    key: str
    user_id: str
    username: str
    roles: list[str]
    key_name: str


API_KEYS = {
    "dev-jose-key": ApiKeyRecord(
        key="dev-jose-key",
        user_id="jose",
        username="jose",
        roles=["admin"],
        key_name="local_jose_dev",
    ),
    "dev-readonly-key": ApiKeyRecord(
        key="dev-readonly-key",
        user_id="readonly",
        username="readonly",
        roles=["reader"],
        key_name="local_readonly_dev",
    ),
}


LOCAL_UI_CORS_ORIGINS = [
    "http://127.0.0.1:8765",
    "http://localhost:8765",
    "http://127.0.0.1:8766",
    "http://localhost:8766",
    "http://127.0.0.1:8767",
    "http://localhost:8767",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
]
LOCAL_UI_CORS_METHODS = ["GET", "POST", "OPTIONS"]
LOCAL_UI_CORS_HEADERS = ["Authorization", "Content-Type", "X-Idempotency-Key"]
