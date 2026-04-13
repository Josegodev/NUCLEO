# Estado operativo – NUCLEO

## Propósito

Describir el estado operativo actual del sistema,
incluyendo comportamiento verificado, limitaciones y reglas de trabajo.

---

## Objetivo actual

Construir un runtime de agentes mínimo y controlado en FastAPI capaz de:

- recibir una petición  
- mapearla a una tool mediante un planner  
- validar la ejecución mediante una capa de policy  
- ejecutar la tool  
- devolver una respuesta  

Objetivo:  
Control y claridad por encima de complejidad.

---

## Arquitectura actual (verificada)

Flujo de ejecución:

AgentRequest  
→ AgentService  
→ AgentRuntime  
→ Planner  
→ PolicyEngine  
→ ToolRegistry  
→ Tool  
→ AgentResponse  

---

## Componentes

### API
- Aplicación FastAPI  
- Endpoint: `/agent/run`  
- Endpoint de salud disponible  

### AgentService
- Fachada ligera sobre el runtime  
- Delega la ejecución  

### Runtime (orquestador)
- Coordina el flujo de ejecución:  
  Planner → Policy → Registry → Tool  

### Planner
- Matching por substrings basado en reglas  
- Devuelve un dict implícito: `{tool, payload}`  

### Tool Registry
- Registro basado en diccionario  
- Resuelve tools por nombre  

### Tools implementadas
- echo  
- system_info  

### Policy Engine
- Whitelist estática:  
  - permite: echo, system_info  
  - deniega el resto  
- Ignora payload y dry_run  

### Schemas
- AgentRequest (user_input, dry_run)  
- AgentResponse (status, message)  

---

## Características técnicas verificadas

- La salida del planner no está validada (contrato implícito)  
- La policy no aplica modos de ejecución (`dry_run`)  
- El runtime ejecuta tools incluso en dry_run  
- Los resultados de tools se convierten a string (`str(result)`)  
- El runtime no captura excepciones (planner, policy, tool)  
- Los contratos de entrada/salida de tools son implícitos  

---

## Último punto estable

Commit:  
3622055 (HEAD -> main, origin/main)  

Estado:
- `/agent/run` funciona  
- tool echo funcional  
- tool system_info funcional  
- pipeline planner → policy → ejecución operativo  
- respuesta simple (status + message)  

---

## Trabajo completado

- Base FastAPI inicializada  
- AgentService implementado  
- AgentRuntime implementado  
- Planner integrado  
- ToolRegistry implementado  
- tool echo operativa  
- tool system_info operativa  
- Capa de policy introducida  
- Ejecución end-to-end funcional  

---

## Problemas abiertos (validados)

- No hay plan de ejecución estructurado  
- No hay validación de payload  
- No hay salida estructurada de tools  
- No hay trazabilidad de ejecución  
- No hay manejo de errores en runtime  
- `dry_run` no aplicado  
- La policy no usa metadatos de tools  

---

## Siguiente paso (ESTRICTO)

Reconstrucción incremental, NO refactor completo.

### Acción inmediata

Añadir logging mínimo dentro del orquestador:

- log de request_id  
- log de tool seleccionada  
- log de decisión de policy  
- log de resultado de ejecución  

### NO hacer

- introducir ExecutionContext todavía  
- refactorizar estructura de respuesta  
- modificar tools en profundidad  

---

## Restricciones

- Ejecución en una sola máquina (local)  
- Debe mantenerse comprensible  
- Cambios incrementales  
- Cada cambio debe ser testeable vía `/agent/run`  

---

## Reglas de trabajo

- Un cambio = un commit  
- Sin refactors grandes  
- Testear siempre vía `/agent/run`  
- Actualizar SESSION_LOG.md tras cada sesión  
- Actualizar development_plan.md antes de terminar  