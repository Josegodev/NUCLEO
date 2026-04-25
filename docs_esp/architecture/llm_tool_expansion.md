> Archivo origen: `docs/architecture/llm_tool_expansion.md`
> Última sincronización: `2026-04-19`

# Arquitectura de expansión de tools con LLM

## Propósito

Este documento describe un subsistema experimental y aislado para generación
controlada de tools asistida por LLM en NUCLEO. Es un diseño de laboratorio y
un conjunto de servicios aislados, no una rama activa del runtime estable
actual.

## Ruta estable

La ruta de producción permanece así:

Request -> API/FastAPI -> AgentService -> AgentRuntime/Orchestrator -> Planner -> PolicyEngine -> ToolRegistry -> Tool -> AgentResponse

Las tools existentes conservan su comportamiento actual.

## Ruta experimental

El repositorio contiene servicios que pueden crear proposals estructuradas,
almacenarlas en `runtime_lab/proposals/`, registrarlas en un staging registry
aislado, generar skeletons de tool bajo `runtime_lab/generated_tools/` y
registrar artefactos de audit bajo `runtime_lab/audit/`.

Restricción importante del estado actual: el Planner estable no emite
`capability_gap_detected`. Su contrato actual solo es `planned` o `no_plan`.
El campo `experimental_tool_generation` existe en la request, pero el flujo
estable de `/agent/run` no lo usa para activar esta ruta.

Esta ruta nunca registra la tool generada en el `ToolRegistry` de producción.

## Relación con llm_lab

`runtime_lab/llm_lab/` es una ruta lateral separada para chats locales de
Mistral/Qwen e informes HARDENING. No ejecuta esta ruta de expansión, no actúa
como Planner y no registra tools.

## Propiedades de seguridad

- No se introduce ejecución de shell.
- No se introduce instalación de paquetes.
- Las tools generadas no se auto-cargan en el runtime de producción.
- El enforcement de policy no cambia para las tools de producción.
- Se escribe un audit trail para creación de proposals, actualizaciones de staging, generación y orquestación.
