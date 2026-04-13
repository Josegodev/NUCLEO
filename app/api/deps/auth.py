"""dependencia FastAPI que:

lee Authorization
valida bearer token/API key
crea ExecutionContext
lo entrega al router

"""

from uuid import uuid4

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.auth import authenticate_api_key
from app.schemas.context import ExecutionContext

from fastapi.security import HTTPBearer

security = HTTPBearer()

def get_execution_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> ExecutionContext:
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization scheme",
        )

    token = credentials.credentials
    principal = authenticate_api_key(token)

    if not principal:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    return ExecutionContext(
        user_id=principal.user_id,
        username=principal.username,
        roles=principal.roles,
        authenticated=True,
        auth_method="api_key",
        request_id=str(uuid4()),
        api_key_name=principal.key_name,
        client_ip=request.client.host if request.client else None,
    )