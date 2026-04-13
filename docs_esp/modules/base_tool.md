# BaseTool

## Propósito
Definir la interfaz común y los metadatos requeridos para todas las tools del sistema.

## Comportamiento real
`BaseTool` define atributos y un método `run(payload)` que debe ser implementado por las tools concretas.

Sin embargo:
- No es una clase abstracta  
- Los metadatos no se validan  
- No existe un contrato definido para entradas ni salidas  

## Fortalezas
- Proporciona una estructura conceptual común  
- Separa las tools del runtime  
- Simple y fácil de extender  

## Problemas detectados
- No es una interfaz real (puede instanciarse directamente)  
- Los campos de metadatos no están validados ni forzados  
- `risk_level` es un string sin tipado  
- `read_only` no se aplica en ningún punto del sistema  
- El contrato de salida de `run()` no está definido  
- No hay esquema ni validación del payload  
- No hay soporte para `dry_run`  
- La identidad de la tool depende únicamente de un nombre string  

## Nivel de riesgo
Medio-Alto

## Mejoras recomendadas
- Convertirla en una clase base abstracta  
- Validar metadatos en la inicialización  
- Introducir un `RiskLevel` tipado  
- Estandarizar el formato de salida de las tools  
- Definir esquemas de payload por tool  
- Añadir soporte para `dry_run` o contexto de ejecución  
- Preparar la separación entre metadatos y lógica de ejecución  