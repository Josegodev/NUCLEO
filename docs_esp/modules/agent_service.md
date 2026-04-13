# AgentService

## Propósito
Capa de servicio de alto nivel que expone un punto de entrada estable para la ejecución del sistema de agentes.

## Comportamiento real
`AgentService` instancia `AgentRuntime` y delega la ejecución mediante `run(request)`.  
No implementa lógica de planificación, policy, selección de tools ni transporte.

## Dependencias
- `AgentRuntime`  
- `AgentRequest`  
- `AgentResponse`  

## Fortalezas actuales
- Separación clara respecto a las rutas de API  
- Lógica mínima  
- Buen punto de extensión para crecimiento futuro  

## Problemas detectados
- La instanciación directa del runtime genera acoplamiento fuerte  
- No hay normalización explícita de errores  
- El contrato de tipos depende completamente de la corrección del runtime  
- La documentación es más ambiciosa que la implementación actual  

## Nivel de riesgo
Medio

## Mejoras recomendadas
- Permitir inyección de dependencias del runtime  
- Añadir una capa controlada de manejo de errores  
- Mantener la documentación alineada con el comportamiento real  
- Usar esta capa como punto de entrada futuro para trazabilidad y contexto de ejecución  