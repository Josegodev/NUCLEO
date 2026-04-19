> Archivo origen: `docs/audits/repo_audit.md`
> Última sincronización: `2026-04-19`

# Auditoría del repositorio

## Capa

Auditoría

## Propósito

Evaluar la estructura del repositorio, los límites entre módulos, la consistencia de nombres y el ajuste entre el layout físico y la intención arquitectónica.

## Forma actual del repositorio

Estructura de alto nivel verificada en el repositorio:

- `app/`
- `docs/`
- `docs_esp/`
- `runtime_lab/`

### Estructura de aplicación

- `api/` -> rutas HTTP y frontera de auth
- `services/` -> capa de servicio y servicios del laboratorio
- `runtime/` -> orquestación y planificación
- `policies/` -> control de ejecución
- `tools/` -> tools de producción
- `schemas/` -> schemas de request, response y experimentales
- `domain/` -> entidades de dominio del laboratorio

### Estructura de documentación

- `docs/architecture.md` -> arquitectura verificada
- `docs/vision/` -> visión objetivo
- `docs/operations/` -> estado operativo y session logs
- `docs/audits/` -> auditorías
- `docs/modules/` -> documentación por módulo
- `docs/planning/` -> roadmap de desarrollo

### Estructura experimental de runtime-lab

- `runtime_lab/proposals/`
- `runtime_lab/generated_tools/`
- `runtime_lab/staging_registry/`
- `runtime_lab/audit/`

## Fortalezas estructurales

- separación clara entre runtime de producción y artefactos del laboratorio
- límites razonables de paquetes para la escala actual
- la estructura documental puede soportar múltiples capas documentales

## Riesgos estructurales

- la composición del runtime de producción sigue embebida en el módulo de runtime
- existen mirrors documentales (`docs_esp/`) que pueden derivar
- la persistencia de `runtime_lab/` está operativamente separada, pero sigue colocalizada en el workspace del repo

## Evaluación de nombres

Los nombres primarios actuales son coherentes y deberían permanecer estables:

- runtime
- orchestrator
- planner
- policy engine
- tool registry
- tool
- staging
- audit
- proposal
- lab / runtime_lab

## Evaluación general

El repositorio sigue siendo estructuralmente coherente, pero la deriva documental y la composición en tiempo de importación siguen siendo los principales riesgos a nivel de arquitectura, más que el desorden de directorios en sí.
