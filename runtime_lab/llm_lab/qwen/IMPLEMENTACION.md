# Implementacion Qwen SQLite

Fecha de revision: 25 de abril de 2026
Fase: HARDENING
Estado: verificado parcialmente

## Límite con NUCLEO

Este chat de Qwen es una ruta lateral experimental. Puede leer su
`contexto.txt`, llamar a Ollama y guardar memoria local en SQLite, pero no forma
parte del flujo canónico de NUCLEO.

No llama a `AgentService`, no actúa como `Planner`, no modifica
`PolicyEngine`, no consulta `ToolRegistry` y no ejecuta `Tools`.

## Estado antiguo

- Este documento estaba duplicado desde Mistral y mencionaba `chat_mistral_sqlite.py`.
- El chat usaba SQLite para guardar mensajes en `memoria_qwen.db`.
- El contexto base se leia desde `contexto.txt`.
- Las rutas ya eran estables porque usaban `Path(__file__).resolve().parent`.
- La respuesta de Ollama se leia directamente con
  `response.json()["message"]["content"]`.
- Si Ollama no respondia, el proceso terminaba con una traza completa.

## Estado nuevo verificado

- El entrypoint externo es `runtime_lab/llm_lab/run_qwen.py`.
- El script interno es `runtime_lab/llm_lab/qwen/chat_qwen_sqlite.py`.
- El modelo configurado es `qwen2.5-coder:7b`.
- La base de datos activa es `runtime_lab/llm_lab/qwen/memoria_qwen.db`.
- El contexto base es `runtime_lab/llm_lab/qwen/contexto.txt`.
- El chat valida que la respuesta de Ollama sea JSON valido.
- El chat valida que exista `message.content`.
- El chat valida que `message.content` sea texto.
- Los errores de red o de contrato con Ollama se muestran como `[ERROR]` y no
  cierran el bucle interactivo.
- `Ctrl-D` y `Ctrl-C` salen del bucle sin mostrar una traza.

## Comportamiento esperado

Con Ollama levantado en `http://localhost:11434/api/chat` y el modelo
`qwen2.5-coder:7b` disponible:

- El usuario escribe un mensaje.
- El script carga contexto y ultimos mensajes.
- El script llama a Ollama.
- Si Ollama responde correctamente, se guardan el mensaje del usuario y la
  respuesta del asistente.
- Si Ollama falla, no se guarda ese intercambio incompleto.

## Flujo tecnico actual

1. `main()` llama a `init_db()`.
2. `ask(text)` carga contexto con `load_user_context()`.
3. `ask(text)` carga historial con `get_messages()`.
4. `build_prompt(...)` compone `system`, historial y mensaje actual.
5. `requests.post(...)` llama a Ollama.
6. `response.raise_for_status()` valida HTTP.
7. `extract_answer(response)` valida el contrato JSON.
8. `save_message(...)` persiste solo si hay respuesta valida.

Un contrato es una regla entre dos partes. Aqui el contrato es: Ollama debe
devolver JSON con esta forma minima:

```json
{
  "message": {
    "content": "texto de respuesta"
  }
}
```

## Validacion realizada

Compilacion:

```bash
.venv/bin/python -m py_compile runtime_lab/llm_lab/qwen/chat_qwen_sqlite.py
```

Arranque y salida sin llamar al modelo:

```bash
printf 'salir\n' | .venv/bin/python runtime_lab/llm_lab/run_qwen.py
```

Manejo de error cuando Ollama no esta accesible:

```bash
printf 'hola\nsalir\n' | .venv/bin/python runtime_lab/llm_lab/run_qwen.py
```

Resultado verificado en este entorno:

```text
[ERROR] No se pudo obtener respuesta de Ollama: ...
```

## Pendiente

- Verificar una respuesta real con Ollama levantado fuera del sandbox.
- Confirmar que el modelo `qwen2.5-coder:7b` esta descargado en Ollama.
- Revisar manualmente que la tabla `mensajes` aumenta en dos filas tras una
  respuesta correcta.
