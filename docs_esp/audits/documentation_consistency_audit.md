> Archivo origen: `docs/audits/documentation_consistency_audit.md`
> Última sincronización: `2026-04-19`

# Auditoría de consistencia documental

## Alcance

Auditoría completa de Markdown de la documentación de NUCLEO, excluyendo Markdown de terceros o vendorizado bajo `.venv/`.

## Convención documental aplicada

La documentación se normaliza en estas capas:

- arquitectura verificada
- arquitectura objetivo / visión
- operación
- auditoría
- session log

Fuente primaria de verdad:

- `docs/`

Traducción mantenida:

- `docs_esp/`

Cuando existe conflicto entre documentación y código, el código se trata como la fuente de mayor confianza.

## Inventario de archivos Markdown

### Raíz

- `README.md` -> visión general del repositorio, arranque rápido y resumen del runtime verificado -> operación + visión general de entrada

### Documentación primaria

- `docs/architecture.md` -> arquitectura verificada
- `docs/EVOLUTION_MAP.md` -> roadmap de evolución desde el estado actual
- `docs/vision/architecture_vision.md` -> arquitectura objetivo
- `docs/planning/development_plan.md` -> prioridades técnicas planificadas
- `docs/operations/operational_state.md` -> estado operativo actual
- `docs/operations/dev_state_snapshot.md` -> snapshot puntual de implementación
- `docs/operations/session_log.md` -> log histórico de ingeniería
- `docs/operations/session_log_llm_tool_expansion.md` -> session log del subsistema de laboratorio
- `docs/modules/agent_service.md` -> documentación de módulo
- `docs/modules/orchestrator.md` -> documentación de módulo
- `docs/modules/planner.md` -> documentación de módulo
- `docs/modules/policy_engine.md` -> documentación de módulo
- `docs/modules/tool_registry.md` -> documentación de módulo
- `docs/modules/base_tool.md` -> documentación de módulo
- `docs/modules/tool_proposal_service.md` -> documentación de módulo experimental
- `docs/modules/tool_generation_service.md` -> documentación de módulo experimental
- `docs/modules/staging_registry.md` -> documentación de módulo experimental
- `docs/modules/audit_store.md` -> documentación de módulo experimental
- `docs/architecture/llm_tool_expansion.md` -> nota de arquitectura experimental
- `docs/audits/repo_audit.md` -> auditoría de estructura del repositorio
- `docs/audits/files_audit.md` -> auditoría de cobertura
- `docs/audits/documentation_consistency_audit.md` -> auditoría de consistencia documental

### Traducción mantenida

- `docs_esp/architecture.md`
- `docs_esp/EVOLUTION_MAP.md`
- `docs_esp/vision/architecture_vision.md`
- `docs_esp/architecture/llm_tool_expansion.md`
- `docs_esp/planning/development_plan.md`
- `docs_esp/operations/operational_state.md`
- `docs_esp/operations/dev_state_snapshot.md`
- `docs_esp/operations/session_log.md`
- `docs_esp/operations/session_log_docs_normalization.md`
- `docs_esp/operations/session_log_llm_tool_expansion.md`
- `docs_esp/operations/session_log_docs_esp_sync.md`
- `docs_esp/modules/agent_service.md`
- `docs_esp/modules/orchestrator.md`
- `docs_esp/modules/planner.md`
- `docs_esp/modules/policy_engine.md`
- `docs_esp/modules/tool_registry.md`
- `docs_esp/modules/base_tool.md`
- `docs_esp/modules/tool_proposal_service.md`
- `docs_esp/modules/tool_generation_service.md`
- `docs_esp/modules/staging_registry.md`
- `docs_esp/modules/audit_store.md`
- `docs_esp/audits/repo_audit.md`
- `docs_esp/audits/files_audit.md`
- `docs_esp/audits/documentation_consistency_audit.md`
- `docs_esp/audits/docs_esp_sync_audit.md`

## Contradicciones detectadas

### 1. Estado actual de arquitectura frente a notas históricas de auth

Conflicto:
- `docs/architecture.md` mezclaba notas de runtime verificado con una sección histórica de diseño de auth.

Decisión:
- Normalizar `docs/architecture.md` como arquitectura verificada únicamente.
- Mantener auth como parte del estado actual verificado, no como nota futura.

### 2. Estructura de la respuesta

Conflicto:
- documentos anteriores afirmaban que la respuesta solo tenía `status + message`
- el código actual incluye `result` opcional

Decisión:
- todos los documentos primarios se actualizaron para describir `result` como comportamiento actual verificado
- los logs históricos se conservan como logs, no como verdad actual

### 3. Estado de ExecutionContext

Conflicto:
- algunos documentos operativos decían "do not introduce ExecutionContext yet"
- el código ya incluye execution context por request

Decisión:
- los documentos operativos primarios se actualizaron al estado actual verificado
- las afirmaciones históricas se conservan solo dentro del session log como contexto histórico

### 4. Ruta experimental de laboratorio frente a ruta de producción

Conflicto:
- documentos anteriores no mencionaban el laboratorio experimental
- documentos nuevos lo describían, pero no siempre lo separaban claramente de producción

Decisión:
- los documentos primarios ahora separan:
  - runtime estable de producción
  - laboratorio experimental aislado

### 5. Comportamiento de Policy

Conflicto:
- varios documentos describían una policy solo basada en whitelist
- el código ahora también comprueba autenticación y rol admin para `system_info`

Decisión:
- los documentos primarios se actualizaron para reflejar el comportamiento actual verificado de policy

### 6. Comportamiento del Planner

Conflicto:
- documentos anteriores describían solo la rama `system_info` / `echo`
- el código ahora también tiene señalización opt-in de capability gap

Decisión:
- los documentos primarios se actualizaron para describir ambas:
  - comportamiento estable de producción
  - rama experimental opt-in

### 7. `docs/` frente a `docs_esp/`

Conflicto:
- `docs_esp/` era parcial y podía contradecir a `docs/`

Decisión:
- sincronizar `docs_esp/` como traducción mantenida de `docs/`
- mantener `docs/` como fuente primaria verificada

## Contradicciones no completamente resueltas

### Operatividad de la persistencia en runtime_lab

Motivo:
- el código implementa persistencia respaldada por ficheros para el laboratorio
- la sesión del repositorio no pudo verificar completamente el comportamiento de escritura de artefactos en el entorno de sandbox actual

Decisión:
- documentarlo como ruta de código implementada
- evitar afirmar verificación operativa completa

### Rol de dispatcher

Motivo:
- `runtime/dispatcher.py` existe, pero no está integrado en el flujo principal del runtime

Decisión:
- describirlo como presente, pero no integrado

## Documentos redundantes o solapados

- `docs/operations/operational_state.md` y `docs/operations/dev_state_snapshot.md` se solapan, pero ahora sirven a ámbitos distintos:
  - operational state = modelo operativo actual
  - dev snapshot = snapshot puntual de implementación
- `docs/architecture.md` y `docs/vision/architecture_vision.md` se solapan en tema, pero ahora difieren claramente por horizonte temporal
- `docs_esp/` se superpone con `docs/`, pero ahora se trata como traducción mantenida, no como fuente primaria verificada

## Jerarquía documental recomendada

1. `README.md` -> entrada al repositorio
2. `docs/architecture.md` -> arquitectura verificada
3. `docs/vision/architecture_vision.md` -> diseño futuro
4. `docs/operations/*` -> estado y logs
5. `docs/modules/*` -> detalle por componente
6. `docs/audits/*` -> evaluación crítica
7. `docs_esp/*` -> traducción mantenida

## Archivos modificados durante la normalización

- `README.md`
- `docs/architecture.md`
- `docs/vision/architecture_vision.md`
- `docs/EVOLUTION_MAP.md`
- `docs/operations/operational_state.md`
- `docs/operations/dev_state_snapshot.md`
- `docs/operations/session_log.md`
- `docs/planning/development_plan.md`
- `docs/modules/agent_service.md`
- `docs/modules/orchestrator.md`
- `docs/modules/planner.md`
- `docs/modules/policy_engine.md`
- `docs/modules/tool_registry.md`
- `docs/modules/base_tool.md`
- `docs/audits/repo_audit.md`
- `docs/audits/files_audit.md`
- `docs/audits/documentation_consistency_audit.md`
- `docs/operations/session_log_docs_normalization.md`
- los archivos `docs_esp/*.md` se marcaron primero como mirror de traducción y después se sincronizaron
