## MIGRATION CONTEXT – NUCLEO SYSTEM

Estoy retomando el desarrollo del sistema NUCLEO en un nuevo entorno Linux.  
Este proyecto implementa un runtime de agentes con control de políticas para auditoría de sistemas, con una arquitectura preparada para ser distribuida.

### Estado actual del proyecto

- API construida con FastAPI
- Arquitectura modular con separación clara de capas:
  - `api/` → rutas HTTP
  - `runtime/` → orquestación (planner + ejecución)
  - `policies/` → control de permisos
  - `tools/` → herramientas ejecutables
  - `schemas/` → modelos de datos
- Registry desacoplada basada en instancias de tools
- Flujo completo validado:
  request → planner → policy → tool → response

### Refactor reciente (importante)

- Separación de tools en:
  - `tools/local/` → ejecución local
  - `tools/remote/` → reservado para ejecución remota (aún vacío)
- Eliminación de `tools/implementations/`
- Creación de nuevas capas:
  - `clients/` → futura comunicación con agente Windows
  - `audit/` → logging y trazabilidad
  - `runtime/dispatcher.py` → preparado para routing de ejecución

### Tools actuales

- `echo_tool`
- `system_info_tool`

Ambas:
- read_only = true
- funcionando correctamente vía `/agent/run`

### Endpoints operativos

- `GET /tools` → lista tools disponibles
- `POST /agent/run` → ejecuta tools mediante runtime

Ejemplo request válido:
```json
{
  "user_input": "system info",
  "dry_run": true
}