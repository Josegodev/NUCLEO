# NUCLEO Runtime Audit UI

Static local console for checking the current NUCLEO runtime HTTP contract.

Scope:

- calls `POST /agent/run`
- calls `GET /tools`
- calls `GET /health`
- keeps backend JSON visible
- does not choose tools
- does not evaluate policy
- does not integrate LLMs
- does not call `runtime_lab/llm_lab`

Run the API:

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Serve the UI:

```bash
.venv/bin/python -m http.server 8767 --directory runtime_lab/runtime_audit_ui/frontend
```

Open:

```text
http://127.0.0.1:8767/
```

Set `API base URL` in the UI to:

```text
http://127.0.0.1:8001
```

Use one of the local development keys from `app/core/config.py`, for example:

```text
dev-jose-key
```

Traceability note:

`AgentResponse` currently exposes `status`, `message`, and `result`. It does not
expose a top-level `request_id`. Some tools may include `request_id` inside
`result`, but that is not guaranteed by the public response contract.

CORS note:

`app/main.py` allows only local Runtime Audit UI origins:

- `http://127.0.0.1:8766`
- `http://127.0.0.1:8767`
- `http://localhost:8766`
- `http://localhost:8767`

Allowed methods are `GET`, `POST`, and `OPTIONS`.

Allowed headers are `Authorization` and `Content-Type`.
