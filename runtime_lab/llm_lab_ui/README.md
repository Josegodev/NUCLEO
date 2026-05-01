# Productive Agent Console v0

`runtime_lab/llm_lab_ui/frontend/` contiene una consola local para llamar al endpoint productivo real:

```text
POST /agent/run
```

No crea un backend paralelo de chat. La UI solo envia requests al runtime existente de NUCLEO.

## Frontera arquitectonica

Flujo real:

```text
Frontend -> /agent/run -> AgentService -> AgentRuntime -> Planner -> PolicyEngine -> ToolRegistry -> dry_run response
```

Limites explicitos:

- No ejecuta tools desde frontend.
- No permite que el LLM ejecute tools.
- No bypass de `PolicyEngine`.
- No crea endpoints tipo `/api/agent-chat`.
- `agent_mode` queda en `proposal_only`.
- `dry_run` queda en `true`.

## Comandos utiles

Desde la raiz del repositorio:

```bash
python3 -m uvicorn runtime_lab.llm_lab_ui.backend.main:app --host 127.0.0.1 --port 8765
```

Si se usa el entorno virtual local del repositorio:

```bash
.venv/bin/python -m uvicorn runtime_lab.llm_lab_ui.backend.main:app --host 127.0.0.1 --port 8765
```

## Criterio de aceptacion

- La UI llama a `POST /agent/run`.
- La respuesta incluye propuesta estructurada.
- Ninguna tool se ejecuta en v0.
- El fallback local/OpenAI queda dentro de `app/adapters/model_router.py`.

Para el diseno completo, ver:

```text
docs_esp/productive_agent_console_v0.md
```
