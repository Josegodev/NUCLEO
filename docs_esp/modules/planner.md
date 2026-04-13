# Planner

## Propósito
Transformar un `AgentRequest` en un plan ejecutable para el runtime.

## Comportamiento real
El planner actual realiza una normalización mínima sobre `request.user_input` y aplica reglas simples basadas en palabras clave.

Comportamiento:
1. Normaliza el input con `strip().lower()`  
2. Si el texto contiene `system` o `info`, devuelve:  
   - tool: `system_info`  
   - payload: `{}`  
3. En caso contrario, devuelve:  
   - tool: `echo`  
   - payload: `{"text": request.user_input}`  

## Fortalezas
- Determinista  
- Fácil de entender  
- Separación clara respecto a runtime y tools  
- Sin efectos secundarios  

## Problemas detectados
- El contrato de salida del plan es implícito (`dict`)  
- La lógica de matching es débil y basada en substrings  
- Supone palabras clave solo en inglés  
- Acoplamiento fuerte a nombres literales de tools  
- No hay manejo explícito de input vacío  
- No hay trazabilidad de decisiones  
- La compatibilidad payload/tool es implícita  
- El fallback universal a `echo` se asume seguro pero no está formalizado  

## Nivel de riesgo
Medio

## Mejoras recomendadas
- Introducir un esquema tipado de plan de ejecución  
- Añadir metadatos de razonamiento o trazabilidad de reglas aplicadas  
- Formalizar comandos o reglas de intención  
- Aclarar o ampliar soporte de idiomas  
- Manejar explícitamente inputs vacíos  
- Reducir el acoplamiento basado en strings con nombres de tools  
- Preparar evolución hacia tablas de reglas o routing declarativo  