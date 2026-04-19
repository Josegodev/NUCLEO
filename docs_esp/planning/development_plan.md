> Archivo origen: `docs/planning/development_plan.md`
> Última sincronización: `2026-04-19`

# Plan de desarrollo - NUCLEO

## Propósito

Definir los siguientes pasos técnicos desde el estado verificado actual del repositorio sin presentar objetivos futuros como comportamiento implementado.

## Base actual

Verificado hoy:

- ruta estable del runtime de producción
- autenticación por API key con alcance de request y `ExecutionContext`
- `result` estructurado preservado en la respuesta
- laboratorio experimental aislado para proposal de tools y generación de skeletons

## Prioridades actuales

### Prioridad 1 - Refuerzo de contratos

Objetivo:
Reducir contratos implícitos en el runtime de producción.

Acciones:

- introducir un execution plan tipado
- definir contratos más sólidos de payload para tools
- definir un contrato más sólido para resultados de tools
- reforzar `BaseTool`

### Prioridad 2 - Control de ejecución

Objetivo:
Hacer que la semántica de ejecución sea más segura y explícita.

Acciones:

- imponer un `dry_run` con significado real
- usar `read_only` y `risk_level` en decisiones de policy
- preparar restricciones sensibles al payload

### Prioridad 3 - Robustez del runtime

Objetivo:
Hacer que el runtime de producción sea resistente ante fallos.

Acciones:

- añadir manejo controlado de excepciones por etapa del pipeline
- estandarizar respuestas de error
- mejorar la trazabilidad a nivel de dominio

### Prioridad 4 - Limpieza de composición

Objetivo:
Separar bootstrap de orquestación.

Acciones:

- inyectar planner, policy engine y registry en el runtime
- mover la lógica de composición fuera del módulo `orchestrator`
- preparar una capa de bootstrap dedicada

### Prioridad 5 - Maduración del Experimental Lab

Objetivo:
Hacer que la ruta de laboratorio sea revisable y operativamente más clara sin promocionarla a producción.

Acciones:

- mejorar la calidad del schema de proposals
- mejorar el workflow de review en staging
- mejorar los metadatos de los artefactos generados
- añadir un diseño explícito de aprobación/promoción sin activación automática

## Explícitamente futuro, no actual

Lo siguiente no son capacidades actuales de producción:

- planificación real soportada por LLM
- activación autónoma de tools
- autoextensión de producción
- instalación dinámica de paquetes
- ejecución arbitraria de shell
- orquestación de memoria/estado en producción

## Principio rector

Estabilizar antes de expandir.

El runtime de producción debe volverse más explícito y controlado antes de que las capacidades experimentales se hagan más ambiciosas.
