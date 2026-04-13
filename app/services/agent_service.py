"""
NUCLEO - AGENT SERVICE

Capa de servicio de alto nivel sobre el runtime.

Responsable de:
- Exponer una interfaz estable para la ejecución del agente
- Desacoplar la capa API (routes) del runtime interno
- Propagar el ExecutionContext hacia el runtime
- Centralizar futuras extensiones del comportamiento del agente

Flujo:
Route → AgentService → AgentRuntime → Tools → Response

Notas:
- No implementa lógica de ejecución (delegada al runtime)
- No contiene lógica de transporte (HTTP)
- No valida credenciales directamente
- Actúa como fachada del sistema de ejecución

Evolución prevista:
- Trazabilidad y logging estructurado
- Orquestación multi-step
- Integración con LLM
- Gestión de memoria y estado
"""

from app.schemas.context import ExecutionContext
from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResponse
from app.runtime.orchestrator import AgentRuntime


class AgentService:
    def __init__(self) -> None:
        self.runtime = AgentRuntime()

    def run(self, request: AgentRequest, context: ExecutionContext) -> AgentResponse:
        return self.runtime.run(request, context)