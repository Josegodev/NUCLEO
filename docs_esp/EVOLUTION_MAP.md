# Mapa de evolución

## Propósito

Este documento describe la transición desde el estado actual auditado del sistema
hacia un runtime de agentes modulares más robusto y escalable.

Está basado en el comportamiento real del código verificado, no solo en la arquitectura teórica.

---

## Estado actual (auditado)

El sistema actualmente proporciona:

- Punto de entrada FastAPI para ejecución del agente  
- AgentService como fachada ligera sobre el runtime  
- AgentRuntime como orquestador central de ejecución  
- Planner basado en reglas  
- PolicyEngine basado en whitelist estática  
- ToolRegistry para resolución de tools  
- BaseTool como interfaz común débil  
- Tools iniciales: `echo`, `system_info`  

### Características actuales

- el flujo de ejecución es claro y modular  
- los contratos entre componentes son mayoritariamente implícitos  
- el planner devuelve un dict plano (`tool`, `payload`)  
- la policy evalúa únicamente el nombre de la tool  
- `dry_run` existe pero no está estructuralmente aplicado  
- las salidas de las tools se convierten a string en `AgentResponse.message`  
- el runtime no captura excepciones de planner / policy / tool  
- el registro de tools ocurre en tiempo de importación de módulos  

---

## Principales debilidades

### 1. Contratos internos débiles
- la salida del planner no está tipada ni validada  
- los contratos de payload de las tools son implícitos  
- el formato de salida de las tools no está estandarizado  

### 2. Seguridad de ejecución incompleta
- `dry_run` no está garantizado por diseño  
- la policy no evalúa payload ni metadatos de la tool  
- `read_only` y `risk_level` están definidos pero no aplicados  

### 3. Robustez limitada ante errores
- no hay manejo estructurado de excepciones en el runtime  
- los fallos pueden propagarse fuera del modelo de respuesta del dominio  

### 4. Acoplamiento en fase bootstrap
- planner, registry y policy engine se crean de forma global  
- el runtime está acoplado a decisiones concretas de inicialización  

### 5. Escalabilidad limitada en la lógica de decisión
- el planner se basa en matching simple por substrings  
- la policy se basa en una allowlist hardcodeada por nombre de tool  

---

## Prioridades de evolución

## Prioridad 1 — Reforzar contratos

Objetivo:  
Hacer las interfaces explícitas y verificables por máquina.

Acciones:
- introducir un `ExecutionPlan` tipado  
- definir esquemas estructurados de entrada de tools  
- definir un modelo estructurado de salida/resultados de tools  
- reforzar `BaseTool` como contrato abstracto real  

Impacto esperado:
- menos supuestos implícitos  
- refactors más seguros  
- mayor facilidad de testing y extensión  

---

## Prioridad 2 — Aplicar control de ejecución

Objetivo:  
Convertir las garantías de seguridad en algo real, especialmente en los modos de ejecución.

Acciones:
- aplicar correctamente `dry_run`  
- usar `read_only` y `risk_level` en decisiones de policy  
- preparar validaciones de policy sensibles al payload  

Impacto esperado:
- mayores garantías de ejecución  
- base segura para tools no read-only en el futuro  

---

## Prioridad 3 — Mejorar robustez del runtime

Objetivo:  
Hacer que la capa de orquestación sea resiliente a fallos.

Acciones:
- añadir manejo controlado de excepciones por etapa del pipeline  
- estandarizar respuestas de error  
- mejorar la trazabilidad de fallos y decisiones  

Impacto esperado:
- comportamiento predecible ante errores  
- depuración y auditoría más sencillas  

---

## Prioridad 4 — Desacoplar composición de orquestación

Objetivo:  
Separar la configuración del sistema de su ejecución.

Acciones:
- inyectar planner, registry y policy engine en el runtime  
- mover el registro de tools fuera del módulo del orquestador  
- preparar una capa de bootstrap/composición  

Impacto esperado:
- mejor testabilidad  
- arquitectura más limpia  
- configuración más sencilla por entorno  

---

## Prioridad 5 — Evolucionar capas de decisión y policy

Objetivo:  
Preparar el sistema para crecer sin perder control.

Acciones:
- evolucionar el planner de checks ad hoc a reglas declarativas  
- evolucionar la policy de allowlist por nombre a reglas basadas en metadatos/capacidades  
- añadir metadatos mínimos de trazabilidad de ejecución  

Impacto esperado:
- mayor escalabilidad  
- mejor observabilidad  
- transición más fluida hacia planificación multi-step o asistida por LLM  

---

## Orden sugerido de evolución

1. Contratos  
2. Aplicación de dry-run y policy  
3. Manejo de errores en runtime  
4. Inyección de dependencias / limpieza de bootstrap  
5. Evolución de planner y policy  
6. Capacidades avanzadas:
   - contexto de ejecución  
   - trazabilidad  
   - planificación multi-step  
   - integración con LLM  
   - memoria/estado  

---

## No recomendado aún

Lo siguiente no debería priorizarse antes de reforzar contratos y control:

- orquestación multi-step  
- gestión de memoria/estado  
- reemplazo del planner por LLM  
- composición autónoma de tools  

Motivo:  
El sistema actual es modular y comprensible, pero aún depende de supuestos implícitos frágiles.

---

## Dirección objetivo

Un runtime modular robusto con:

- contratos explícitos  
- ejecución controlada  
- estructuras tipadas de planificación y salida  
- ejecución de tools consciente de policy  
- límites de dependencias limpios  
- orquestación trazable y testeable  