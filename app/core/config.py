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