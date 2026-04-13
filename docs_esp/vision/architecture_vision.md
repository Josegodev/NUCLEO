# Visión de arquitectura

## Propósito

Este documento describe la arquitectura objetivo del sistema.

Representa el diseño deseado y puede diferir de la implementación actual.

Para comportamiento verificado, ver:  
`docs/architecture.md`

---

## Visión general del sistema

Este proyecto es un backend de agentes modulares construido con FastAPI.

El objetivo es:
- recibir una petición  
- decidir qué tool utilizar  
- validar la ejecución  
- ejecutar la tool  
- devolver una respuesta estructurada  

---

## Flujo objetivo

Request → API → AgentService → Runtime → Planner → PolicyEngine → ToolRegistry → Tool → Response  

---

## Componentes (diseño objetivo)

### API
- Punto de entrada FastAPI  
- Gestiona el transporte HTTP  
- Delega en AgentService  

### AgentService
- Capa de aplicación estable  
- Punto de entrada de ejecución  
- Desacopla la API del runtime  

### Runtime (Orquestador)
- Coordinador central de ejecución  
- Ejecuta:  
  Planner → Policy → Tool → Response  

### Planner
- Mapea input de usuario a tool + payload  
- Objetivo:
  - lógica de planificación estructurada y extensible  

### Policy Engine
- Controla permisos de ejecución  
- Objetivo:
  - reglas sensibles al payload  
  - decisiones basadas en riesgo  
  - aplicación de `dry_run`  

### Tool Registry
- Mantiene el catálogo de tools  
- Resuelve tools por nombre  

### Tools
- Unidades de ejecución encapsuladas  
- Objetivo:
  - entrada/salida estructurada  
  - comportamiento basado en metadatos  

### Schemas
- Definen contratos de entrada/salida  
- Objetivo:
  - validación estricta  
  - estructuras de ejecución tipadas  

### Core
- Infraestructura compartida  
- Objetivo:
  - logging  
  - configuración  
  - contexto de ejecución  

---

## Principios

- Control explícito sobre la ejecución  
- Sin efectos secundarios implícitos  
- Separación de responsabilidades  
- Contratos fuertes entre componentes  
- Evolución incremental  

---

## Gaps conocidos respecto a la implementación actual

- Los contratos entre componentes siguen siendo implícitos  
- `dry_run` no está aplicado estructuralmente  
- Las salidas de las tools no están estructuradas  
- El runtime no gestiona errores de ejecución  
- La policy se basa en una allowlist simple por nombre de tool  

---

## Capacidades objetivo

- ExecutionContext (trazabilidad y logging)  
- Contratos estructurados de entrada/salida de tools  
- Reglas de policy sensibles al payload  
- Control de ejecución basado en riesgo  
- Planificación multi-step  
- Planificación asistida por LLM (opcional)  
- Gestión de memoria/estado (fase posterior)  