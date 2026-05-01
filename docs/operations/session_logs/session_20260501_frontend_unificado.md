# Session 20260501 - Frontend Unificado NUCLEO_AUGMENTED_CONTROLLED

### 1. ESTADO INICIAL

- Fragmentacion frontend:
  - existian superficies visuales separadas o parcialmente solapadas para
    observar runtime y laboratorio
  - riesgo de que cada superficie mostrase contratos distintos
- Errores backend:
  - uso de `http.server` para servir el frontend, lo que no expone endpoints
    FastAPI
  - error esperado cuando `/rag/model-answer` no existe en el servidor usado
  - puerto `8765` ocupado durante arranque local
- RAG no funcional:
  - `runtime_lab/llm_lab/rag_nucleo_docs/search.py` tenia un problema de
    indentacion reportado previamente
  - el backend LLM_LAB dependia de que ese modulo pudiera importarse

### 2. PROBLEMAS DETECTADOS

#### CRITICO

- Drift entre superficies visuales:
  - riesgo: un ingeniero podia auditar comportamientos distintos segun la UI
    abierta
  - impacto: perdida de trazabilidad entre frontend, runtime y laboratorio
- Servir el frontend con `http.server`:
  - riesgo: `index.html` carga, pero `/rag/model-answer` responde como endpoint
    inexistente
  - impacto: error operacional falso, porque el problema no estaba en RAG sino
    en el servidor usado
- Contratos frontend/backend no explicitados:
  - riesgo: enviar campos no contractuales como `provider` o `use_rag`
  - impacto: ambiguedad durante HARDENING

#### MEDIO

- Puerto `8765` ocupado:
  - riesgo: arranque inconsistente del backend LLM_LAB
  - impacto: pruebas locales no reproducibles si el proceso anterior sigue vivo
- RAG demasiado estricto:
  - riesgo: devolver `NO_EVIDENCE_FOR_ANSWER` aunque haya evidencia parcial
  - impacto: respuesta correcta desde politica estricta, pero confusa para el
    operador
- Ranking de evidencia mejorable:
  - riesgo: recuperar fragmentos validos pero no los mas utiles
  - impacto: respuestas menos informativas

#### INFORMATIVO

- `provider` aparece como control visual:
  - estado: no es campo contractual de `/rag/model-answer`
  - consecuencia: `openai` se modela como `external/openai` y el backend actual
    lo rechaza con `EXTERNAL_MODEL_NOT_ENABLED`
- `use_rag` aparece como control visual:
  - estado: no es campo contractual
  - consecuencia: el endpoint actual ya es RAG por definicion

### 3. CAMBIOS APLICADOS

- UI unificada:
  - `HARDENING`
  - `LLM_LAB`
  - `COMPARE`
- Funciones frontend registradas:
  - `buildRequestHardening`
  - `buildRequestLLMLab`
  - `callAPI`
  - `renderResponse`
- Separacion de endpoints:
  - `HARDENING` llama a `POST /agent/run`
  - `LLM_LAB` llama a `POST /rag/model-answer`
  - `COMPARE` llama a ambos y mantiene paneles separados
- Correccion RAG:
  - `search.py` compila correctamente en esta revision local
  - el problema de `IndentationError` queda cubierto por validacion de
    compilacion
- Documentacion creada o actualizada:
  - `docs/operations/frontend_unificado.md`
  - `runtime_lab/llm_lab_ui/README.md`
  - `docs/operations/session_logs/session_20260501_frontend_unificado.md`

### 4. IMPACTO TECNICO

- Reduccion de drift:
  - hay una unica UI para observar HARDENING, LLM_LAB y comparacion
  - los payloads esperados quedan documentados
- Mejora de trazabilidad:
  - cada request conserva endpoint, payload enviado, status HTTP y respuesta
    completa
  - los errores de transporte, contrato y parseo se diferencian
- Separacion de responsabilidades:
  - el frontend no ejecuta tools
  - el frontend no decide policy
  - el frontend no interpreta `ALLOW`/`DENY`
  - LLM_LAB sigue siendo experimental y no reemplaza al runtime NUCLEO

### 5. VALIDACION

- Validacion ejecutada en esta sesion:

```bash
python3 -m py_compile runtime_lab/llm_lab/rag_nucleo_docs/search.py
python3 -m py_compile runtime_lab/llm_lab_ui/backend/main.py
```

Resultado:

```text
passed
```

- Endpoints funcionando:
  - `/agent/run`
    - status: unknown
    - reason: not_detected_from_code
    - contrato detectado: `POST /agent/run` existe en FastAPI y usa
      `AgentRequest` -> `AgentResponse`
  - `/rag/model-answer`
    - status: unknown
    - reason: not_detected_from_code
    - contrato detectado: `POST /rag/model-answer` existe en FastAPI y usa
      `RagModelAnswerRequest`

- Tests ejecutados:
  - status: partial
  - ejecutado: compilacion Python de `search.py` y `backend/main.py`
  - suite completa de tests:
    - status: unknown
    - reason: not_detected_from_code

- Outputs esperados:
  - `HARDENING`:

```json
{
  "status": "success",
  "result": {},
  "errors": [],
  "trace_id": "string",
  "version": "execution_result.v1"
}
```

  - `LLM_LAB` con evidencia y modelo local disponible:

```json
{
  "status": "MODEL_ANSWER_READY",
  "query": "string",
  "model": "llama3.1:8b",
  "answer": "string",
  "evidence": [
    {}
  ],
  "warning": "string"
}
```

  - `LLM_LAB` sin evidencia:

```json
{
  "status": "EVIDENCE_NOT_FOUND",
  "query": "string",
  "model": "llama3.1:8b",
  "answer": "",
  "evidence": []
}
```

  - `LLM_LAB` con evidencia insuficiente segun el modelo:

```text
NO_EVIDENCE_FOR_ANSWER
```

### 6. RIESGOS ABIERTOS

- RAG demasiado restrictivo:
  - clasificacion: MEDIO
  - impacto: puede devolver `NO_EVIDENCE_FOR_ANSWER` aunque haya fragmentos
    relacionados
- Provider externo no habilitado:
  - clasificacion: INFORMATIVO
  - impacto: `external/openai` devuelve `EXTERNAL_MODEL_NOT_ENABLED`
- Ranking de evidencia mejorable:
  - clasificacion: MEDIO
  - impacto: la calidad de la respuesta depende de que la evidencia recuperada
    sea la adecuada
- Contratos no descubiertos dinamicamente:
  - clasificacion: INFORMATIVO
  - impacto: si cambia el backend, la documentacion y la UI deben actualizarse
    juntas para evitar drift

### 7. SIGUIENTE PASO RECOMENDADO

- Tests de contrato frontend:
  - validar que `buildRequestHardening` sigue enviando solo `input` y `dry_run`
  - validar que `buildRequestLLMLab` sigue enviando solo `query`, `top_k` y
    `model`
  - validar que `callAPI` conserva errores HTTP, contract errors y parse errors
- Mejora controlada de grounding:
  - revisar ranking de evidencia antes de tocar prompts
  - mantener `NO_EVIDENCE_FOR_ANSWER` como comportamiento estricto mientras no
    exista una politica de grounding mas precisa
