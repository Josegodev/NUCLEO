# NUCLEO Refactor Audit

Fecha de auditoria: 2026-05-02

## 1. Estado actual entendido

NUCLEO es un runtime de agentes modular sobre FastAPI. El flujo productivo
verificado es:

```text
HTTP request
-> app.main
-> app.api.routes.agent
-> AgentService
-> AgentRuntime
-> Planner
-> PolicyEngine
-> ToolRegistry
-> Tool o dry_run/proposal
-> AgentResponse
```

El repositorio tambien contiene `runtime_lab/`, que es una zona experimental
para RAG, UI local, document loading, experimentos con modelos y auditorias.
Esa zona no debe convertirse en autoridad de ejecucion del runtime productivo.

Clasificacion: INFORMATIVO.

## 2. Problema detectado

### Mapa de modulos

| Zona | Rol observado | Estado |
| --- | --- | --- |
| `app/main.py` | Punto de entrada FastAPI productivo | Critico |
| `app/api/` | Routers HTTP y dependencias de auth | Critico |
| `app/services/agent_service.py` | Fachada fina sobre runtime | Critico |
| `app/runtime/orchestrator.py` | Orquestador central de ejecucion y approval gate | Critico |
| `app/runtime/planner.py` | Planner determinista y entrada de augmentacion | Critico |
| `app/runtime/augmentation_service.py` | Frontera LLM controlada para propuestas | Critico, reciente |
| `app/runtime/planner_augmentation.py` | Adaptador backward-compatible de augmentacion | Legacy compatible |
| `app/policies/` | Contrato y motor de decision de policy | Critico |
| `app/tools/` | BaseTool, registry productivo y tools locales | Critico |
| `app/schemas/` | Contratos Pydantic publicos e internos | Critico |
| `app/services/approval/` | Persistencia file-backed de propuestas aprobables | Critico |
| `app/services/tool_*`, `app/services/staging/`, `app/services/audit/` | Flujo experimental de propuestas/generacion | Experimental |
| `runtime_lab/llm_lab/` | RAG, modelos y experimentos externos al core | Experimental |
| `runtime_lab/llm_lab_ui/` | UI/API experimental local | Experimental |
| `runtime_lab/document_loader/` | Ingestion local experimental | Experimental |
| `docs/` y `docs_esp/` | Documentacion duplicada por idioma | Util, con riesgo de drift |
| `external/` | Repos externos ignorados por git | No productivo |

### Problemas encontrados

| Clasificacion | Problema | Archivo(s) |
| --- | --- | --- |
| CRITICO | `pytest` sin argumentos recogia `external/` y laboratorios; fallaba antes de validar el core. | repo root, `external/`, `runtime_lab/` |
| CRITICO | CORS estaba definido dos veces en `app/main.py`; una definicion permitia `*`. | `app/main.py` |
| CRITICO | `AgentRuntime` concentra muchas responsabilidades en un archivo grande. | `app/runtime/orchestrator.py` |
| CRITICO | Documentacion de `PolicyEngine` dice que no valida payload en profundidad, pero el codigo si llama `validate_tool_payload`. | `docs/modules/policy_engine.md`, `app/policies/engine.py` |
| CRITICO | La app productiva importa `runtime_lab.llm_lab.model_adapter` a traves de `app/adapters/model_router.py`. Es una dependencia interna confusa entre core y laboratorio. | `app/adapters/model_router.py` |
| CRITICO | `runtime_lab/llm_lab_ui/backend/main.py` declara `app = FastAPI()` dos veces y contiene un endpoint inicial descartado despues por la segunda app. | `runtime_lab/llm_lab_ui/backend/main.py` |
| INFORMATIVO | Hay archivos Python vacios sin imports detectados. | `app/runtime/dispatcher.py`, `app/audit/event_logger.py`, `app/clients/windows_agent_client.py` |
| INFORMATIVO | `docs/` y `docs_esp/` duplican decisiones; cada cambio documental puede divergir. | `docs/`, `docs_esp/` |
| PREMATURO | Mover o borrar laboratorios completos ahora mezclaria limpieza con cambios funcionales no verificados. | `runtime_lab/` |

### Codigo duplicado o responsabilidades mezcladas

- `app/main.py` mezclaba bootstrap FastAPI con configuracion CORS duplicada.
- `runtime_lab/llm_lab_ui/backend/main.py` mezcla servidor de UI, API de
  experimentos, API RAG y codigo duplicado de modelos de request.
- `app/runtime/orchestrator.py` mezcla run normal, proposal persistence,
  approval execution, tracing tolerante a fallos y conversion de errores.

### Codigo muerto o aparentemente no usado

Evidencia razonable:

- `app/runtime/dispatcher.py` esta vacio.
- `app/audit/event_logger.py` esta vacio.
- `app/clients/windows_agent_client.py` esta vacio.
- No se detectaron imports a esos archivos con `rg`.

No se eliminan en esta etapa porque borrar archivos es mas facil de revisar en
una PR separada.

## 3. Impacto tecnico

El riesgo principal no es que el runtime no funcione, sino que sea dificil saber
cual contrato manda cuando hay contradicciones. En HARDENING, un contrato es una
regla verificable entre modulos: por ejemplo, "PolicyEngine devuelve siempre
PolicyDecision" o "ToolRegistry solo resuelve tools registradas".

Riesgos concretos:

- Si los tests por defecto no son deterministas, un desarrollador nuevo no sabe
  si el core esta roto o si fallo un laboratorio externo.
- Si CORS tiene dos fuentes de verdad, el borde HTTP puede ser mas permisivo de
  lo documentado.
- Si `app/` depende de `runtime_lab/`, la frontera core/lab queda borrosa.
- Si docs y codigo se contradicen, futuras decisiones pueden basarse en un
  contrato que ya no es real.
- Si se refactoriza `orchestrator.py` de golpe, se puede romper approval,
  dry_run o policy sin verlo claramente.

## 4. Cambio minimo recomendado

Primera etapa recomendada e implementada:

1. Hacer determinista la validacion por defecto con `pytest.ini`.
2. Dejar una sola configuracion CORS local explicita.
3. Centralizar los origins/metodos/headers CORS en `app/core/config.py`.
4. Actualizar el test de CORS para comprobar que no hay wildcard y que existe
   una sola capa CORS.
5. Documentar arquitectura, plan y riesgos antes de mover codigo.

Clasificacion: CRITICO.

## 5. Explicacion pedagogica

Un refactor seguro empieza por cerrar el suelo bajo los pies. Antes de mover
funciones, necesitamos que "ejecutar tests" signifique siempre lo mismo. Si el
comando recoge repos externos o pruebas que necesitan servicios locales, el
resultado depende del entorno y no del codigo core.

Tambien necesitamos una sola decision para CORS. CORS es una regla del
navegador que decide que origen web puede llamar a la API. En HARDENING, una
regla duplicada es peligrosa porque no queda claro cual es la real.

## 6. Pasos exactos para hacerlo

He aplicado estos pasos:

1. Crear `pytest.ini` con `testpaths = tests`.
2. Anadir constantes CORS locales en `app/core/config.py`.
3. Actualizar `app/main.py` para registrar una sola `CORSMiddleware`.
4. Actualizar `tests/test_runtime_tracing.py` para validar el nuevo contrato.
5. Crear esta auditoria y los documentos de arquitectura/plan.

## 7. Como comprobar si ha quedado bien

Comando principal:

```bash
.venv/bin/python -m pytest -q
```

Comprobaciones esperadas:

- Pytest ya no intenta recoger `external/`.
- Pytest ya no ejecuta smoke tests de laboratorio por accidente.
- La suite de `tests/` debe pasar.
- El test de CORS debe comprobar que no hay `allow_origins=["*"]`.

## 8. Riesgos o dudas pendientes

- CRITICO: `app/adapters/model_router.py` sigue dependiendo de `runtime_lab`.
  No se corrige todavia porque puede afectar la augmentacion controlada.
- CRITICO: `app/runtime/orchestrator.py` debe dividirse con mucho cuidado,
  probablemente extrayendo primero funciones puras o helpers internos, no
  creando una arquitectura nueva.
- CRITICO: `runtime_lab/llm_lab_ui/backend/main.py` contiene duplicacion real,
  pero es laboratorio y no debe bloquear el core.
- INFORMATIVO: `docs_esp/` no se sincronizo en esta etapa para evitar churn
  documental.
- PREMATURO: borrar archivos vacios o mover `runtime_lab/` completo.

