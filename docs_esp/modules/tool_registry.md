# ToolRegistry

## Propósito
Registro central de tools disponibles en el sistema.

## Comportamiento real
`ToolRegistry` almacena instancias de tools en un diccionario interno indexado por `tool.name`.

Comportamiento:
- `register(tool)`: almacena la tool bajo su nombre  
- `get(tool_name)`: devuelve la tool correspondiente o `None`  
- `list_tools()`: devuelve todas las instancias de tools registradas  

## Fortalezas
- Búsqueda simple y eficiente basada en diccionario  
- Separación clara de responsabilidades  
- Complejidad adecuada para un sistema en fase bootstrap  
- Fácil de entender y testear  

## Problemas detectados
- Nombres de tools duplicados sobrescriben registros anteriores sin aviso  
- No hay validación estricta del tipo de tool ni del nombre  
- El contrato del nombre de la tool es implícito pero crítico  
- `get()` delega el manejo de tools inexistentes a capas posteriores  
- `list_tools()` expone instancias vivas de tools  
- No hay soporte para introspección basada en metadatos  
- No hay distinción entre mutación en bootstrap y en runtime  

## Nivel de riesgo
Medio

## Mejoras recomendadas
- Rechazar registros duplicados  
- Validar el contrato de la tool en el momento del registro  
- Tipar explícitamente el almacenamiento interno  
- Documentar el comportamiento de `get()` cuando no existe la tool  
- Añadir métodos auxiliares como `has()` o `list_tool_names()`  
- Preparar el uso del registry para policy y documentación basadas en metadatos  