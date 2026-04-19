> Archivo origen: `docs/modules/agent_service.md`
> Última sincronización: `2026-04-19`

# AgentService

## Capa

Arquitectura verificada

## Propósito

Proporcionar una fachada estable de capa de servicio entre las rutas de API y la orquestación del runtime.

## Comportamiento actual verificado

`AgentService` actualmente:

- instancia `AgentRuntime`
- expone `run(request, context)`
- delega la ejecución directamente al runtime

Actualmente no asume:

- planificación
- policy
- ejecución de tools
- lógica de generación de proposals del laboratorio

## Fortalezas

- mantiene la API ligera
- preserva un entrypoint estable
- es un lugar limpio para futuros hooks de tracing u orquestación

## Limitaciones actuales

- la dependencia del runtime sigue construyéndose directamente
- todavía no existe una frontera independiente de normalización de errores

## Etiqueta de estado

- Fachada de servicio: implementada
- Frontera de inyección de dependencias: no implementada
