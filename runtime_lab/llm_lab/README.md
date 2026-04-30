# llm_lab

Laboratorio externo para ejecutar chats de Mistral y Qwen con Ollama, lanzar
experimentos multi-modelo locales o remotos, y generar informes de revision
HARDENING sobre NUCLEO.

Este directorio no forma parte del runtime principal de NUCLEO. No integra LLM
en `AgentService`, `Runtime`, `Planner`, `PolicyEngine`, `ToolRegistry` ni
`Tools`.

## 1. Arquitectura del RAG

El sistema RAG implementa un pipeline con separación estricta de responsabilidades:

```
query
→ rag_nucleo_docs/search.py (retrieval determinista)
→ rag_nucleo_docs/evidence.py (paquete de evidencias)
→ rag_nucleo_docs/rag_answer.py (respuesta extractiva determinista, sin LLM)
→ llm_rag_answer.py (capa experimental de generación LLM)
```

## 2. Separación de responsabilidades

- **Retrieval (Determinista)**: `rag_nucleo_docs/` maneja la búsqueda y empaquetado de evidencia sin usar LLM. El resultado es determinista y reproducible.
- **Evidence (Contrato Cerrado)**: `evidence.py` define un contrato fijo para el paquete de evidencias, independiente de modelos.
- **LLM Generation (Experimental)**: `llm_rag_answer.py` consume evidencia determinista y genera respuestas usando modelos LLM vía `model_adapter.py`.
- **Model Execution**: `model_adapter.py` abstrae la ejecución de modelos (Ollama/local), sin lógica de negocio.

Reglas estrictas:
- Retrieval NO usa LLM.
- LLM no decide fuentes ni altera evidencia.
- LLM no ejecuta tools ni modifica runtime.
- Evidence siempre se devuelve intacta.

## 3. Contratos

### search()
- **Entrada**: `query` (str)
- **Salida**: Lista ordenada determinista de resultados con `doc_id`, `file`, `score`, `snippet`.

### evidence_package
```json
{
  "query": "string",
  "status": "EVIDENCE_FOUND" | "NO_EVIDENCE",
  "evidence": [
    {
      "doc_id": "string",
      "source": "string",
      "score": float,
      "snippet": "string"
    }
  ]
}
```

### llm_rag_answer
```json
{
  "query": "string",
  "model": "string",
  "status": "EVIDENCE_FOUND" | "NO_EVIDENCE",
  "answer": "string",
  "evidence": [...]
}
```

## 4. Reglas de seguridad del RAG

- Si `status == NO_EVIDENCE` → NO llamar al LLM, devolver `"NO_CONSTA_EN_DOCUMENTACION"`.
- Respuesta LLM debe derivarse únicamente de snippets proporcionados.
- No se permite conocimiento externo del modelo.
- Evidence se devuelve intacta, sin modificaciones.

## 5. Validación

### eval_cases.json
Contiene casos de prueba con términos esperados, prohibidos y fuentes requeridas.

### smoke_test.py
Valida:
- Términos esperados en respuestas.
- Ausencia de términos prohibidos.
- Presencia de fuentes requeridas.
- Determinismo en retrieval.

Ejecución: `python3 -m runtime_lab.llm_lab.rag_nucleo_docs.smoke_test`

## 6. Ejecución

Ejemplos reales de uso:

```bash
python3 -m runtime_lab.llm_lab.llm_rag_answer "Qué hace dry_run=True?" --model mistral
python3 -m runtime_lab.llm_lab.llm_rag_answer "Qué hace dry_run=True?" --model qwen
python3 -m runtime_lab.llm_lab.llm_rag_answer "Qué hace dry_run=True?" --model llama3.1:8b
```

Modelos soportados: `mistral`, `qwen`, `llama3.1:8b` (vía Ollama).

## 7. Limitaciones actuales

- LLM puede variar redacción en respuestas.
- Posibles errores de formato en output del modelo.
- Dependencia de calidad y completitud de snippets.
- No hay council ni agregación multi-modelo implementados.

## 8. Estado del sistema

**HARDENING COMPLETADO (RETRIEVAL + EVIDENCE)**  
**LLM INTEGRATION: EXPERIMENTAL**

## 9. Próximos pasos (no implementados)

- Council (comparación multi-modelo).
- Scoring de respuestas.
- Integración opcional en runtime NUCLEO.

Estos features NO están implementados actualmente.
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

Ejecutar con Ollama local, si `qwen`, `mistral` y `llama3.1:8b` estan disponibles:

Comprueba primero los nombres reales instalados:

```bash
ollama list
```

El runner acepta nombres con tag, por ejemplo `mistral:latest`.

```bash
.venv/bin/python runtime_lab/llm_lab/experiment_runner.py \
  --mode ollama \
  --stage1-models qwen,mistral,llama3.1:8b \
  --stage2-reviewers qwen,mistral,llama3.1:8b \
  --chairman qwen \
  --input "Explica el contrato de artefactos de llm_lab"
```

### Proveedores remotos en experimentos

El runner mantiene `--mode ollama` por compatibilidad. En esta ruta, `ollama`
significa "ejecucion real de modelo"; el proveedor concreto se infiere desde el
prefijo de cada `model_id`.

Convencion de IDs:

```text
qwen                         -> Ollama local
mistral                      -> Ollama local
llama3.1:8b                  -> Ollama local
openai:gpt-4o                -> proveedor OpenAI-compatible
anthropic:claude-...         -> Anthropic
google:gemini-...            -> Google
```

Variables de entorno usadas por los proveedores remotos:

```text
OPENAI_API_KEY
OPENAI_BASE_URL   # opcional para proveedores OpenAI-compatible
ANTHROPIC_API_KEY
GOOGLE_API_KEY
```

Las API keys no se guardan en artefactos. Los artefactos conservan el mismo
schema `llm_lab.experiment.v1` y registran solo `model_id`, estado, latencia,
respuesta o error normalizado.

Ejemplo mixto local/remoto:

```bash
OPENAI_API_KEY=... 
  --mode ollama \
  --stage1-models qwen,openai:gpt-4o \
  --stage2-reviewers mistral,openai:gpt-4o \
  --chairman openai:gpt-4o \
  --input "Compara una respuesta local y una remota"
```

Restricciones:

- este runner pertenece solo a `runtime_lab/llm_lab`
- no llama al runtime de NUCLEO
- no ejecuta tools
- no decide politica
- no persiste API keys
- no permite que un LLM ejecute tools ni controle el runtime de NUCLEO
