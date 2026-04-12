"""
NUCLEO - AGENT SERVICE

Capa de servicio de alto nivel sobre el runtime.

Responsable de:
- Exponer una interfaz estable para la ejecución del agente
- Desacoplar la capa API (routes) del runtime interno
- Centralizar futuras extensiones del comportamiento del agente

Flujo:
Route → AgentService → AgentRuntime → Tools → Response

Notas:
- No implementa lógica de ejecución (delegada al runtime)
- No contiene lógica de transporte (HTTP)
- Actúa como fachada del sistema de ejecución

Evolución prevista:
- Inyección de ExecutionContext
- Trazabilidad y logging estructurado
- Orquestación multi-step
- Integración con LLM
- Gestión de memoria y estado
"""

from app.schemas.requests import AgentRequest
from app.schemas.responses import AgentResponse
from app.runtime.orchestrator import AgentRuntime


class AgentService:
    def __init__(self) -> None:
        self.runtime = AgentRuntime()

    def run(self, request: AgentRequest) -> AgentResponse:
        return self.runtime.run(request)