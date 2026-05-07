# NUCLEO Incremental Refactor Plan

Fecha: 2026-05-02

## 1. Estado actual entendido

El core productivo ya tiene contratos importantes: `AgentRequest`,
`PlannedAction`, `PolicyDecision`, `ToolContractArtifact` y `AgentResponse`.
La refactorizacion debe preservar esos contratos y mejorar legibilidad sin
reescribir el runtime.

Clasificacion: CRITICO.

## 2. Problema detectado

El repositorio tiene dos tipos de complejidad:

- Complejidad productiva: runtime, policy, registry, approval y tools.
- Complejidad accidental: tests sin scope por defecto, CORS duplicado,
  laboratorios mezclados en busquedas, docs duplicadas y archivos vacios.

La primera se debe endurecer. La segunda se debe aislar o documentar.

## 3. Impacto tecnico

Si se refactoriza todo a la vez, sera dificil saber que cambio rompio que
contrato. El plan debe producir pasos pequenos, revisables y con validacion
propia.

## 4. Cambio minimo recomendado

### Etapa 1 - Base verificable

Estado: implementada en esta PR local.

- Crear `pytest.ini` para que `pytest` valide el core por defecto.
- Eliminar CORS duplicado y wildcard en `app/main.py`.
- Centralizar CORS local en `app/core/config.py`.
- Crear `docs/REFACTOR_AUDIT.md`, `docs/ARCHITECTURE.md` y
  `docs/REFACTOR_PLAN.md`.

Clasificacion: CRITICO.

### Etapa 2 - Contrato PolicyEngine/ToolRegistry

Estado: implementada en esta PR local.

- Crear `docs/CONTRACT_POLICY_TOOLREGISTRY.md`.
- Actualizar docs stale de `PolicyEngine`: hoy si valida payload contra
  contrato de tool.
- Anadir tests especificos para:
  - policy deniega una tool y runtime no consulta registry ni ejecuta
  - tool inexistente tras policy `ALLOW` devuelve error controlado
  - policy deniega payload invalido antes de permitir ejecucion
  - runtime revalida input de tool antes de `tool.run(...)`
  - payload valido ejecuta exactamente una vez
  - resultado invalido de policy corta antes de registry/tool
  - `ToolRegistry.register(...)` rechaza duplicados, tools sin contrato y
    nombres fuera del set cerrado
- No cambiar comportamiento funcional.

Clasificacion: CRITICO.

### Etapa 3 - Orchestrator en piezas pequenas

Estado: pendiente.

- Extraer helpers internos de `AgentRuntime` solo donde ya hay bloques claros:
  - ejecucion normal de tool
  - dry_run/proposal result
  - approval execution
- Mantener la clase `AgentRuntime` como fachada publica.
- No introducir bus de eventos, framework, patron nuevo ni multi-step runtime.

Clasificacion: CRITICO.

### Etapa 4 - Frontera app/runtime_lab

Estado: pendiente.

- Documentar y luego aislar la dependencia `app/adapters/model_router.py` ->
  `runtime_lab.llm_lab.model_adapter`.
- Mantener el contrato de `ModelRouter.generate(...)`.
- Evitar mover codigo de modelo hasta tener tests de regresion alrededor.

Clasificacion: CRITICO.

### Etapa 5 - Limpieza de laboratorio

Estado: pendiente.

- Separar claramente README/entrypoints de:
  - `runtime_lab/llm_lab/`
  - `runtime_lab/llm_lab_ui/`
  - `runtime_lab/document_loader/`
- Corregir duplicacion en `runtime_lab/llm_lab_ui/backend/main.py`.
- No conectar laboratorios al core.

Clasificacion: INFORMATIVO para core, CRITICO para mantenibilidad.

### Etapa 6 - Codigo muerto

Estado: pendiente.

- Abrir PR separada para borrar o marcar:
  - `app/runtime/dispatcher.py`
  - `app/audit/event_logger.py`
  - `app/clients/windows_agent_client.py`
- Validar con `rg` y tests antes de borrar.

Clasificacion: INFORMATIVO.

## 5. Explicacion pedagogica

Un buen refactor no empieza moviendo carpetas: empieza haciendo que el sistema
sea verificable. Cuando los tests son estables, cada cambio pequeno se puede
comprobar. Despues se puede dividir codigo grande con menos riesgo.

Termino clave: "drift" significa que dos sitios que deberian decir lo mismo
empiezan a divergir. Ejemplo actual: docs de `PolicyEngine` frente al codigo
real de payload validation.

## 6. Pasos exactos para hacerlo

Checklist para proximas PRs:

1. Ejecutar `.venv/bin/python -m pytest -q`.
2. Elegir un unico limite del sistema.
3. Escribir o actualizar un test de contrato.
4. Hacer el cambio minimo.
5. Ejecutar tests otra vez.
6. Actualizar solo la documentacion afectada.

## 7. Como comprobar si ha quedado bien

Comando base:

```bash
.venv/bin/python -m pytest -q
```

Senales de que el plan va bien:

- El diff de cada etapa es pequeno.
- No aparecen nuevos modulos globales sin necesidad.
- `AgentRuntime.run(...)` sigue devolviendo los mismos estados publicos.
- `PolicyEngine` sigue siendo autoridad antes de ejecutar.
- `ToolRegistry` sigue siendo la fuente de verdad de tools productivas.
- `runtime_lab/` sigue sin ejecutar tools productivas.

## 8. Riesgos o dudas pendientes

- CRITICO: hay cambios previos staged y unstaged en el worktree. Cada etapa
  debe revisarse con `git diff` para no mezclar responsabilidades.
- CRITICO: la suite completa antes de `pytest.ini` fallaba por `external/` y
  laboratorios; eso queda aislado, no corregido internamente.
- PREMATURO: reorganizar carpetas grandes antes de cerrar contratos de runtime.
- PREMATURO: borrar artefactos generados o tocar `external/`.
