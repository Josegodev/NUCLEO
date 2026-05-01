 NUCLEO – Document Loader Lab (HARDENING SUMMARY)

## 1. Estado actual

NUCLEO se mantiene en fase **HARDENING**.

El laboratorio `runtime_lab/document_loader`:

- No modifica `app/`
- No interactúa con:
  - AgentRuntime
  - Planner
  - PolicyEngine
  - ToolRegistry
- No integra LLMs
- No ejecuta parsing real de PDFs
- No depende de librerías externas (OpenDataLoader desactivado)

Arquitectura actual:


PDF (input local)
→ loader
→ ParserAdapter (NoOp)
→ JSONL (normalizado)
→ manifest (trazabilidad)
→ context.md (lectura futura por LLM)


---

## 2. Objetivo alcanzado

Se ha construido un **pipeline determinista y validable** previo a cualquier parser real.

Capacidades actuales:

- Validación de entrada (ruta, extensión, tamaño, raíces permitidas)
- Generación de:
  - JSONL
  - manifest.json
  - context.md
- Contrato de salida cerrado
- Validación automática del contrato
- Modelo de errores normalizado
- Límites operativos definidos
- Adaptador de parser desacoplado
- Batch processing (smoke test)
- Tests unitarios reproducibles

---

## 3. Componentes clave

### 3.1 Loader

`load_pdf_to_jsonl.py`

Responsabilidades:

- Validar input
- Ejecutar parser (actualmente NoOp)
- Validar resultado contra contrato
- Generar outputs deterministas
- Emitir errores normalizados

---

### 3.2 Parser Adapter

`parser_adapter.py`

Define:

- `BasePdfParser`
- `ParserResult`
- `ParserError`

Implementaciones:

- `NoOpPdfParser` (activo)
- `OpenDataLoaderPdfParser` (stub desactivado)

---

### 3.3 Contrato

`PARSER_CONTRACT.md`

Define:

- Esquema JSONL
- Tipos válidos (`block_type`)
- Reglas de hash
- Límites
- Semántica de errores
- Prohibición de truncado silencioso

---

### 3.4 Validador

`validate_jsonl_contract.py`

Garantiza:

- JSON válido
- Campos obligatorios
- Hash correcto
- Límites respetados
- Coherencia del contenido

Acepta:

- JSONL vacío si:

---

### 3.5 Modelo de errores

`ERROR_MODEL.md`

Errores definidos:

- `invalid_path`
- `non_pdf_input`
- `file_too_large`
- `path_not_allowed`
- `parser_unavailable`
- `parser_disabled`
- `parser_not_integrated`
- `parser_timeout`
- `too_many_records`
- `content_record_too_large`
- `content_total_too_large`

---

### 3.6 Configuración

`loader_config.py`

Límites actuales:

```python
MAX_PDF_BYTES = 5242880
MAX_PAGES = 100
PARSER_TIMEOUT_SECONDS = 10
MAX_RECORDS_PER_DOCUMENT = 1000
MAX_CONTENT_CHARS_PER_RECORD = 256
MAX_TOTAL_CONTENT_CHARS = 100000
ALLOWED_INPUT_ROOTS = ["/tmp", "runtime_lab/"]