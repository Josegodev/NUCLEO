# Contract: PolicyEngine -> Payload Validation -> ToolRegistry

Fecha: 2026-05-02

## 1. Estado actual entendido

El contrato critico del core es:

```text
PlannedAction
-> PolicyEngine.evaluate(...)
-> ToolRegistry.get(...)
-> BaseTool.validate_input(...)
-> BaseTool.run(...)
-> BaseTool.validate_output(...)
```

En lenguaje sencillo: una tool solo debe ejecutarse si la accion esta
planificada, la policy la permite, la registry la encuentra y el payload cumple
el contrato de esa tool.

Clasificacion: CRITICO.

## 2. Problema detectado

El comportamiento ya existe en codigo, pero estaba repartido entre
`PlannedAction`, `PolicyEngine`, `ToolRegistry`, `BaseTool` y
`AgentRuntime`. Sin un documento unico, es facil confundir quien decide, quien
valida y quien ejecuta.

Ademas habia documentacion desactualizada que decia que `PolicyEngine` no
validaba payload en profundidad. El codigo actual si llama
`validate_tool_payload(...)`.

## 3. Impacto tecnico

Si este contrato se rompe, puede ocurrir alguno de estos fallos:

- Una tool desconocida llega a ejecucion.
- Una tool denegada por policy se ejecuta.
- Un payload incompleto o con campos extra llega a `tool.run(...)`.
- Un error cambia segun el punto donde falle y se vuelve dificil de auditar.

Termino clave: payload significa los argumentos estructurados enviados a una
tool. Para `echo`, el payload valido minimo es:

```json
{"text": "hola"}
```

## 4. Cambio minimo recomendado

Mantener las responsabilidades actuales y fijarlas con tests:

| Componente | Decide | No decide |
| --- | --- | --- |
| `PolicyEngine` | Autenticacion, allowlist, registro, `dry_run` booleano, payload valido, rol basico | No ejecuta tools |
| Payload validation | Forma estricta del payload segun modelo Pydantic de la tool | No autoriza usuarios |
| `ToolRegistry` | Registra/resuelve tools productivas con contrato | No ejecuta tools |
| `Tool` | Valida input/output y ejecuta su accion concreta | No decide policy |
| `AgentRuntime` | Ordena el pipeline y corta en el primer fallo controlado | No inventa payloads |

Clasificacion: CRITICO.

## 5. Explicacion pedagogica

Este contrato usa defensa en profundidad. Eso significa que no confiamos en una
sola barrera:

1. `PlannedAction` valida el payload al crear una accion planificada.
2. `PolicyEngine` vuelve a validar antes de permitir.
3. `AgentRuntime` llama `tool.validate_input(...)` justo antes de ejecutar.

La repeticion es intencionada. Si un test usa una policy falsa que devuelve
`ALLOW`, runtime todavia debe impedir que un payload invalido llegue a
`tool.run(...)`.

## 6. Pasos exactos para hacerlo

Flujo de ejecucion normal:

1. El planner devuelve `PlannedAction(status="planned")`.
2. Runtime llama `PolicyEngine.evaluate(tool_name, payload, dry_run, context)`.
3. Si policy devuelve `DENY`, runtime devuelve `POLICY_DENIED` y no consulta la
   registry.
4. Si policy devuelve algo que no es `PolicyDecision`, runtime devuelve
   `POLICY_INVALID_RESULT`.
5. Si policy permite, runtime llama `ToolRegistry.get(tool_name)`.
6. Si la registry no encuentra tool, runtime devuelve `TOOL_NOT_FOUND`.
7. Si encuentra tool, runtime llama `tool.validate_input(payload)`.
8. Si el input falla, runtime devuelve `TOOL_INPUT_INVALID`.
9. Si `dry_run=True`, runtime no llama `tool.run(...)`.
10. Si `dry_run=False`, runtime llama `tool.run(...)` y despues
    `tool.validate_output(...)`.

## 7. Como comprobar si ha quedado bien

Tests que cubren este contrato:

- `test_policy_denial_stops_before_registry_and_tool_execution`
- `test_unknown_tool_after_policy_allow_returns_controlled_error`
- `test_policy_denies_invalid_echo_payloads`
- `test_runtime_tool_input_validation_blocks_execution_after_policy_allow`
- `test_valid_echo_payload_executes_once`
- `test_invalid_policy_result_stops_before_registry_and_tool`
- `test_tool_registry_rejects_duplicate_names`
- `test_tool_registry_rejects_tool_without_contract`
- `test_tool_registry_rejects_name_outside_closed_tool_set`

Comando:

```bash
.venv/bin/python -m pytest -q
```

Resultado esperado tras esta PR: suite verde.

## 8. Riesgos o dudas pendientes

- CRITICO: `app/adapters/model_router.py` importa
  `runtime_lab.llm_lab.model_adapter`. Esta PR lo documenta como riesgo, pero
  no lo corrige para no mezclar contratos de policy/tools con frontera LLM.
- CRITICO: `AgentRuntime` sigue grande; extraerlo requiere tests de
  caracterizacion antes de mover codigo.
- INFORMATIVO: hay tests existentes bajo `tests/` que ejercitan APIs de
  `runtime_lab`. La validacion por defecto pasa, pero la frontera core/lab
  todavia merece una PR separada.
- PREMATURO: cambiar la semantica del Planner o del approval gate en esta PR.

