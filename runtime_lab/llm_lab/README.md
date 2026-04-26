# llm_lab

Laboratorio local externo para ejecutar chats de Mistral y Qwen con Ollama y
para generar informes de revision HARDENING sobre NUCLEO.

Este directorio no forma parte del runtime principal de NUCLEO. No integra LLM
en `AgentService`, `Runtime`, `Planner`, `PolicyEngine`, `ToolRegistry` ni
`Tools`.

## LLM Lab / Ruta lateral experimental

Propósito:

- cargar contexto de NUCLEO para consultas externas o locales
- ejecutar chats locales de Mistral/Qwen mediante Ollama
- conservar memoria local de laboratorio con SQLite
- generar informes markdown de revisión HARDENING

Estado:

- experimental
- lateral al runtime
- no productivo
- no integrado en el flujo canónico

Flujo canónico de NUCLEO, para comparar:

```text
Request -> API/FastAPI -> AgentService -> AgentRuntime/Orchestrator -> Planner -> PolicyEngine -> ToolRegistry -> Tool -> AgentResponse
```

`llm_lab` no aparece en ese flujo.

Permisos de esta ruta:

- leer documentación y archivos seleccionados del repo para construir contexto
- escribir bases SQLite locales dentro de `runtime_lab/llm_lab/`
- escribir informes bajo `runtime_lab/llm_lab/reports/`
- llamar a Ollama local solo cuando se ejecutan los chats Mistral/Qwen

Prohibido para esta ruta:

- ejecutar tools de producción
- modificar `PolicyEngine`
- registrar tools en `ToolRegistry`
- llamar automáticamente a `/agent/run`
- actuar como `Planner`
- decidir permisos o saltarse policy

Importante: Mistral y Qwen pueden responder preguntas sobre NUCLEO usando
contexto cargado, pero sus respuestas no cambian el runtime y no tienen
autoridad de ejecución.

## Estado documentado

### Antiguo

- Los chats llamaban a Ollama y leian directamente
  `response.json()["message"]["content"]`.
- Si Ollama no estaba disponible, el proceso terminaba con una traza completa
  de Python.
- La documentacion de Qwen estaba duplicada desde Mistral y mencionaba archivos
  y modelo incorrectos.
- La instalacion dependia de usar `.venv`, pero el fallo fuera del entorno no
  estaba explicado.

### Nuevo verificado

- `run_mistral.py` arranca desde la raiz del repo.
- `run_qwen.py` arranca desde la raiz del repo.
- Ambos scripts inicializan su SQLite local.
- Ambos scripts usan rutas absolutas basadas en `__file__`.
- Ambos scripts cargan `contexto.txt` si existe.
- Ambos scripts validan que Ollama devuelva JSON con `message.content`.
- Si Ollama no responde, el chat muestra un error controlado y vuelve al prompt.
- `nucleo_state_review.py` genera un informe markdown en `reports/`.
- `.venv` tiene instalado `requests==2.33.1`.

Comportamiento verificado el 25 de abril de 2026:

```bash
.venv/bin/python -m py_compile runtime_lab/llm_lab/run_mistral.py runtime_lab/llm_lab/run_qwen.py runtime_lab/llm_lab/nucleo_state_review.py runtime_lab/llm_lab/mistral/chat_mistral_sqlite.py runtime_lab/llm_lab/qwen/chat_qwen_sqlite.py
printf 'hola\nsalir\n' | .venv/bin/python runtime_lab/llm_lab/run_mistral.py
printf 'hola\nsalir\n' | .venv/bin/python runtime_lab/llm_lab/run_qwen.py
NUCLEO_REPO_PATH=/home/jose-gonzalez-oliva/NUCLEO .venv/bin/python runtime_lab/llm_lab/nucleo_state_review.py --context-limit-chars 2000
```

En este entorno, la conexion a `localhost:11434` no estuvo disponible. Por eso
se verifico el manejo de error, no una respuesta real del modelo.

### Esperado

Con Ollama levantado y el modelo descargado:

- Mistral debe responder al prompt del usuario.
- Qwen debe responder al prompt del usuario.
- Cada intercambio correcto debe guardar dos filas en SQLite: una `user` y una
  `assistant`.
- Si Ollama devuelve un error HTTP, JSON invalido o una estructura sin
  `message.content`, el chat debe mostrar `[ERROR]` sin cerrar el proceso.

## Entorno virtual

Crear entorno:

```bash
cd /home/jose-gonzalez-oliva/NUCLEO
python3 -m venv .venv
```

Activar entorno:

```bash
source .venv/bin/activate
```

Instalar dependencias:

```bash
python3 -m pip install -r runtime_lab/llm_lab/requirements.txt
```

Nota: en sistemas con PEP 668, instalar con el Python del sistema puede fallar
con `externally-managed-environment`. Usa `.venv`.

## Ejecutar Mistral

Desde la raiz del repo:

```bash
.venv/bin/python runtime_lab/llm_lab/run_mistral.py
```

Script interno equivalente:

```bash
.venv/bin/python runtime_lab/llm_lab/mistral/chat_mistral_sqlite.py
```

## Ejecutar Qwen

Desde la raiz del repo:

```bash
.venv/bin/python runtime_lab/llm_lab/run_qwen.py
```

Script interno equivalente:

```bash
.venv/bin/python runtime_lab/llm_lab/qwen/chat_qwen_sqlite.py
```

## Requisito externo

Los chats esperan Ollama en:

```text
http://localhost:11434/api/chat
```

Modelos configurados:

```text
Mistral: mistral
Qwen: qwen2.5-coder:7b
```

## Ruta lateral de revision NUCLEO

`nucleo_state_review.py` construye un contexto trazable del repo NUCLEO y
genera un informe markdown de auditoria HARDENING.

Uso:

```bash
NUCLEO_REPO_PATH=/home/jose-gonzalez-oliva/NUCLEO .venv/bin/python runtime_lab/llm_lab/nucleo_state_review.py
```

Salida:

```text
runtime_lab/llm_lab/reports/nucleo_state_review_YYYYMMDD_HHMM.md
```

Actualmente `call_local_llm(prompt: str) -> str` es un stub. Esto significa que
el informe prepara el prompt, pero no llama a un modelo local.

Archivos que lee:

- `README.md`
- `docs/`
- `docs_esp/`
- `app/runtime/`
- `app/policies/`
- `app/tools/`
- `tests/`

Archivos que genera:

- `runtime_lab/llm_lab/reports/nucleo_state_review_YYYYMMDD_HHMM.md`

Lo que no hace:

- no importa `app.main`
- no instancia `AgentService`
- no llama a `AgentRuntime`
- no invoca `Planner`, `PolicyEngine`, `ToolRegistry` ni `Tools`
- no llama a `/agent/run`

## Artefactos de experimentos multi-modelo

`experiment_runner.py` genera artefactos JSON versionados bajo:

```text
runtime_lab/llm_lab/artifacts/{experiment_id}.json
```

Contrato:

```text
runtime_lab/docs/llm_lab_experiment_artifact_contract.md
```

Ejecutar mock determinista. Este modo no llama a Ollama y escribe dos
artefactos: uno valido y uno con errores registrados explicitamente.

```bash
.venv/bin/python runtime_lab/llm_lab/experiment_runner.py \
  --mode mock \
  --input "Compara inferencia local y remota en fase HARDENING"
```

Ejecutar solo mock exitoso:

```bash
.venv/bin/python runtime_lab/llm_lab/experiment_runner.py \
  --mode mock-success \
  --input "Resume el objetivo de un artefacto auditable"
```

Ejecutar con Ollama local, si `qwen` y `mistral` estan disponibles:

```bash
.venv/bin/python runtime_lab/llm_lab/experiment_runner.py \
  --mode ollama \
  --stage1-models qwen,mistral \
  --stage2-reviewers qwen,mistral \
  --chairman qwen \
  --input "Explica el contrato de artefactos de llm_lab"
```

Restricciones:

- este runner pertenece solo a `runtime_lab/llm_lab`
- no llama al runtime de NUCLEO
- no ejecuta tools
- no decide politica
- no introduce proveedores externos
