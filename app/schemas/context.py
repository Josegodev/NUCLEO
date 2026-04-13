"""
Responsabilidad:

definir el constructor del contexto
funciones auxiliares de contexto

definir ExecutionContext como modelo Pydantic

"""

from pydantic import BaseModel, Field
from typing import List, Optional


class ExecutionContext(BaseModel):
    user_id: str
    username: str
    roles: List[str] = Field(default_factory=list)
    authenticated: bool = True
    auth_method: str = "api_key"
    request_id: str
    api_key_name: Optional[str] = None
    client_ip: Optional[str] = None