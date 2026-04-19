> Archivo origen: `docs/modules/tool_generation_service.md`
> Última sincronización: `2026-04-19`

# ToolGenerationService

## Responsabilidad

`ToolGenerationService` convierte una proposal experimental en artefactos solo de laboratorio:

- skeleton Python de la tool
- archivo de test placeholder
- metadatos mínimos

## Salida

Los artefactos se escriben bajo `runtime_lab/generated_tools/<tool_name>/`.

## Notas

- Los ficheros generados no se auto-registran en producción.
- La salida está pensada para review, no para despliegue directo de ejecución.
- La generación queda auditada.
