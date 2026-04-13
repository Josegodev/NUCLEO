# AgentRuntime

## Propósito
Orquestador central de ejecución del runtime modular de agentes.

## Comportamiento real
El runtime recibe un `AgentRequest`, solicita un plan al planner, evalúa la policy, resuelve la tool desde el registry, la ejecuta y devuelve un `AgentResponse`.

Flujo de ejecución actual:
1. `planner.create_plan(request)`  
2. Extrae `plan["tool"]` y `plan["payload"]`  
3. `policy_engine.evaluate(tool_name, payload, dry_run)`  
4. Si se deniega, devuelve `blocked`  
5. Resuelve la tool desde el registry  
6. Si no existe, devuelve `error`  
7. Ejecuta `tool.run(payload)`  
8. Devuelve `success` o `dry_run_success`  

## Fortalezas
- Pipeline claro  
- La policy se aplica antes de la ejecución  
- Las tools desconocidas se gestionan explícitamente  
- Lógica de orquestación legible  

## Problemas detectados
- El contrato de salida del planner es implícito y no está validado  
- No hay manejo de excepciones en planner, policy ni ejecución de tools  
- `dry_run` no está garantizado estructuralmente por el runtime  
- Inicialización global tipo singleton en tiempo de importación del módulo  
- El runtime está acoplado a tools concretas y lógica de bootstrap  
- Los resultados de las tools se convierten a `str`, perdiendo estructura  
- No hay validación de payload por tool  
- Las respuestas de error son demasiado genéricas  

## Nivel de riesgo
Alto

## Mejoras recomendadas
- Introducir un esquema explícito de plan de ejecución  
- Añadir manejo controlado de errores por etapa del pipeline  
- Aplicar `dry_run` de forma estructural  
- Inyectar planner, policy engine y registry  
- Mover el registro de tools a la capa de bootstrap  
- Devolver salidas de tools estructuradas  
- Añadir contratos de validación de payload  
- Mejorar trazabilidad y modelado de errores de dominio  