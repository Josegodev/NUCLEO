> Archivo origen: `docs/vision/architecture_vision.md`
> Última sincronización: `2026-04-19`

# Visión de arquitectura

## Propósito

Este documento describe la arquitectura objetivo de NUCLEO. Está orientado de forma intencional al futuro y no debe leerse como una afirmación de comportamiento actual verificado.

Para el comportamiento implementado, ver:

- `docs/architecture.md`

## Dirección objetivo

NUCLEO debería evolucionar hacia un runtime agentic modular con:

- contratos internos explícitos
- semántica de ejecución controlada
- planificación de ejecución tipada
- enforcement de policy más rico
- orquestación auditable
- superficies experimentales aisladas para crecimiento de capacidades asistido por LLM

## Flujo objetivo

Request  
-> API  
-> AgentService  
-> Runtime  
-> Planner  
-> PolicyEngine  
-> ToolRegistry  
-> Tool  
-> AgentResponse

La forma objetivo preserva el pipeline estable, pero refuerza la calidad de los contratos y el control operativo en cada etapa.

## Diseño objetivo de componentes

### API

- Solo frontera de transporte
- Autenticación y validación de requests en el borde
- Sin lógica de ejecución de negocio

### AgentService

- Entrypoint estable de aplicación
- Fachada del runtime
- Futuros hooks de tracing y orquestación

### Runtime

- Capa central de orquestación
- Manejo explícito de planes
- Semántica de fallo controlada
- Ramificación aislada entre runtime de producción y flujos experimentales de laboratorio

### Planner

- Evolucionar desde reglas ad hoc hacia estructuras de planificación más explícitas
- Soportar primero reglas declarativas
- Soportar más adelante lógica opcional de proposals asistida por LLM
- Nunca convertirse en la autoridad final de ejecución

### PolicyEngine

- Pasar de comprobaciones name-based a control sensible a metadatos y payload
- Imponer un `dry_run` con significado real
- Preservar el comportamiento deny-by-default

### ToolRegistry

- Mantener el registry de producción distinto de registries de staging o de laboratorio
- Reforzar contratos de registro y validación de metadatos

### Tools

- Contratos tipados de entrada/salida
- Semántica clara de metadatos
- Límites de ejecución más seguros

### Experimental Lab

- Permanecer aislado del runtime de producción
- Soportar generación de proposals, generación de skeletons, review en staging y auditabilidad
- Nunca auto-promocionar a producción sin review explícita

## Principios de diseño

- control explícito sobre la ejecución
- sin desplazamientos ocultos de autoridad hacia modelos o artefactos generados
- separación de responsabilidades
- ruta de producción estable
- ruta experimental aislada
- trazabilidad antes que autonomía

## Gap conocido entre estado actual y visión

El código actual ya contiene una primera ruta experimental de laboratorio, pero la arquitectura objetivo aún no está completa. En particular, lo siguiente sigue siendo futuro o parcial:

- execution plan tipado
- validación estricta de planes en runtime
- enforcement completo de dry-run
- policy sensible al payload
- trazabilidad completa de la ejecución de producción
- planificación real soportada por LLM en condiciones controladas
- workflow formal de promoción desde staging a producción
