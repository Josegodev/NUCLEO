## Comportamiento actual verificado

### Flujo de ejecución (real)

AgentRequest  
→ Planner (`create_plan`)  
→ PolicyEngine (`evaluate`)  
→ ToolRegistry (`get`)  
→ Tool (`run`)  
→ AgentResponse  

### Características de la implementación actual

- El Planner devuelve un `dict` plano con las claves:
  - `tool`: str  
  - `payload`: dict  
  Este contrato es implícito y no está validado por el runtime.

- El PolicyEngine aplica una whitelist estática basada únicamente en `tool_name`:
  - permite: `echo`, `system_info`  
  - deniega todos los demás  
  No evalúa `payload` ni `dry_run`.

- `dry_run` se propaga a través del sistema pero:
  - no afecta a las decisiones de policy  
  - no evita la ejecución de la tool  
  Las tools se siguen ejecutando normalmente por el runtime.

- La resolución de tools se realiza mediante `ToolRegistry.get(tool_name)`:
  - devuelve una instancia de la tool o `None`  
  - las tools inexistentes son gestionadas explícitamente por el runtime  

- Los resultados de las tools se devuelven mediante:
  ```python
  message = str(result)