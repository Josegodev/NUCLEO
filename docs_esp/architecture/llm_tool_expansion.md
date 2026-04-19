> Archivo origen: `docs/architecture/llm_tool_expansion.md`
> Última sincronización: `2026-04-19`

# Arquitectura de expansión de tools con LLM

## Propósito

Este documento describe un subsistema experimental y aislado para generación controlada de tools asistida por LLM en NUCLEO. El diseño amplía el runtime existente sin sustituir el pipeline estable de producción.

## Ruta estable

La ruta de producción permanece así:

API -> AgentService -> AgentRuntime -> Planner -> PolicyEngine -> ToolRegistry -> Tool

Las tools existentes conservan su comportamiento actual.

## Ruta experimental

Cuando el planner detecta un capability gap y la request habilita explícitamente el flujo de laboratorio, NUCLEO crea una proposal estructurada, la almacena en `runtime_lab/proposals/`, la registra en un staging registry aislado, genera un skeleton de tool bajo `runtime_lab/generated_tools/` y registra artefactos de audit bajo `runtime_lab/audit/`.

Esta ruta nunca registra la tool generada en el `ToolRegistry` de producción.

## Propiedades de seguridad

- No se introduce ejecución de shell.
- No se introduce instalación de paquetes.
- Las tools generadas no se auto-cargan en el runtime de producción.
- El enforcement de policy no cambia para las tools de producción.
- Se escribe un audit trail para creación de proposals, actualizaciones de staging, generación y orquestación.
