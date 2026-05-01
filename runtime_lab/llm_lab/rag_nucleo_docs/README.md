# rag_nucleo_docs

Módulo de retrieval determinista para documentación Markdown de NUCLEO en `llm_lab`.

## Propósito

Indexa documentación viva de NUCLEO y recupera evidencia determinista para preguntas de arquitectura y HARDENING. Ayuda a inspeccionar coherencia interna de documentación.

## Alcance

Permitido:
- Leer archivos `.md` del repositorio NUCLEO.
- Fragmentar Markdown por encabezados.
- Construir índice léxico local.
- Consultar documentación.
- Devolver evidencia con rangos de archivo y línea.

Prohibido:
- Importar `app/`.
- Llamar a `AgentService`, `AgentRuntime`, `Planner`, `PolicyEngine`, `ToolRegistry`, `Tools`.
- Acceder a `CONTROL_OPERATIVO`.
- Copiar documentación fuente como fuente de verdad nueva.
- Modificar comportamiento de runtime NUCLEO.
- Integrar lógica LLM (generación, prompts, llamadas a modelos).

## Separación de responsabilidades

- **Retrieval/Evidence (Determinista)**: Este módulo maneja retrieval y empaquetado de evidencia. NO contiene lógica LLM.
- **Generación LLM (Experimental)**: La generación con LLM se maneja en `llm_rag_answer.py` del directorio padre `llm_lab`, que consume `evidence.build_evidence_package` y llama a modelos vía `model_adapter.call_model`.

## Arquitectura

```text
Archivos Markdown vivos de NUCLEO
        ↓
ingest_md.py
        ↓
chunk_md.py
        ↓
build_index.py
        ↓
.index/md_chunks_index.json
        ↓
query_index.py
        ↓
evidence.py (empaquetado determinista)
        ↓
Consumido por llm_rag_answer.py (generación LLM)
```

## Estado

Este módulo es determinista y no depende de LLM. Sirve como base sólida para integración futura opcional en runtime NUCLEO.

Ejemplo de ejecución determinista:
```bash
python3 -m runtime_lab.llm_lab.rag_nucleo_docs.rag_answer "Qué hace dry_run=True?"
```