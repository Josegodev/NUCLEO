# PolicyEngine

## Propósito
Validar si la ejecución de una tool planificada está permitida antes de llegar a la fase de ejecución.

## Comportamiento real
El policy engine actual aplica una whitelist estática basada en el nombre de la tool.

Comportamiento:
- Permite `echo`  
- Permite `system_info`  
- Deniega cualquier otra tool  
- Ignora `payload`  
- Ignora `dry_run`  

Devuelve un `PolicyDecision` con:
- `decision`: `allow` o `deny`  
- `reason`: string explicativo  

## Fortalezas
- Comportamiento real de denegación por defecto  
- Simple y auditable  
- Separación clara respecto a la ejecución  
- Salida estructurada mediante `PolicyDecision`  

## Problemas detectados
- `payload` no se evalúa  
- `dry_run` no tiene efecto en las decisiones de policy  
- La seguridad se basa únicamente en el nombre de la tool, no en capacidades o metadatos  
- Los nombres de tools hardcodeados generan duplicidad con planner/registry  
- No existen identificadores estructurados de reglas de policy  
- No está preparado para control contextual o dependiente de parámetros  

## Nivel de riesgo
Medio

## Mejoras recomendadas
- Documentar explícitamente que actualmente es una allowlist por nombre de tool  
- Empezar a usar metadatos de tools como `read_only` y `risk_level`  
- Aplicar restricciones reales basadas en `dry_run`  
- Preparar validaciones sensibles al payload  
- Evolucionar hacia definiciones declarativas de reglas  
- Enriquecer `PolicyDecision` con metadatos de reglas  