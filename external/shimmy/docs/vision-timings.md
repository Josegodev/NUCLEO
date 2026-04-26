# Vision Timing Benchmarks

## Run 1: CPU-only (no GPU offload)
- Command: `cargo run --features llama,vision --bin shimmy -- serve --bind 127.0.0.1:11435`
- Model: `minicpm-v` (MiniCPM-V via Shimmy cache)
- Mode: `full`
- Requests sent to: `http://127.0.0.1:11435/api/vision`
- Notes: server started once; four images posted sequentially; times include model warm state; `request_seconds` ≈ `meta.duration_ms/1000` from the response.

| image | request_seconds | model_duration_ms | parse_warnings |
| --- | ---: | ---: | --- |
| assets/vision-samples/extended-02-after-5-messages.png | 145.339 | 145283 | — |
| assets/vision-samples/final-test.png | 78.277 | 78274 | Could not parse structured output |
| assets/vision-samples/scene2-models.png | 91.991 | 91988 | — |
| assets/vision-samples/scene4-check-response.png | 99.358 | 99354 | — |

### CPU rerun (spot-check)
- Image: `assets/vision-samples/final-test.png`
- Result: `request_seconds` 223.057, `model_duration_ms` 223019, parse warnings: none.

## Run 2: GPU (CUDA) build
- Build: `CARGO_TARGET_DIR=target-gpu cargo build --features llama,vision,llama-cuda`
- Server: `CARGO_TARGET_DIR=target-gpu cargo run --features llama,vision,llama-cuda --bin shimmy -- serve --bind 127.0.0.1:11436`
- Model/mode/endpoints same as CPU run.

| image | request_seconds | model_duration_ms | parse_warnings |
| --- | ---: | ---: | --- |
| assets/vision-samples/extended-02-after-5-messages.png | 145.323 | 145276 | — |
| assets/vision-samples/final-test.png | 67.683 | 67681 | Could not parse structured output |
| assets/vision-samples/scene2-models.png | 63.072 | 63055 | Could not parse structured output |
| assets/vision-samples/scene4-check-response.png | 85.322 | 85319 | — |

### GPU rerun (after restarting server)
- Server restarted (same build/flags) to check variance.

| image | request_seconds | model_duration_ms | parse_warnings |
| --- | ---: | ---: | --- |
| assets/vision-samples/extended-02-after-5-messages.png | 122.614 | 122587 | — |
| assets/vision-samples/final-test.png | 49.817 | 49815 | Could not parse structured output |
| assets/vision-samples/scene2-models.png | 44.340 | 44337 | Could not parse structured output |
| assets/vision-samples/scene4-check-response.png | 60.084 | 60082 | — |

## Run 3: GPU (CUDA) via VS Code task (server already running)
- Server: started once via VS Code task `serve-vision-gpu` (bind `127.0.0.1:11436`)
- Requests sent sequentially (one per image)
- Model: `minicpm-v`

| image | request_seconds | model_duration_ms | parse_warnings |
| --- | ---: | ---: | --- |
| assets/vision-samples/extended-02-after-5-messages.png | 12.982 | 12980 | — |
| assets/vision-samples/final-test.png | 26.854 | 26851 | — |
| assets/vision-samples/scene2-models.png | 11.077 | 11074 | — |
| assets/vision-samples/scene4-check-response.png | 8.816 | 8814 | — |

## Next steps
- Repeat the same test after rebuilding with GPU features (e.g., `cargo build --features llama,vision,llama-cuda`) and rerun the server, then append results here for comparison.
- Consider lowering vision `max_tokens` for faster responses if quality remains acceptable.

---

## Run 4: Cold Start vs Hot Server Comparison (2024-12-14)

**Purpose:** Measure the overhead of CLI cold start (model loading) vs hot server.

- **Test Image:** `theme-tester/screenshots/02-after-fix.png` (57KB)
- **Mode:** `brief`
- **GPU:** CUDA enabled (RTX 3060 12GB)
- **Model:** `minicpm-v`

### CLI Cold Start (model loads each time)

| Run | Total Time (s) | Inference Time (ms) | Notes |
|-----|----------------|---------------------|-------|
| 1 | 27.5 | 26,669 | Fresh model load |
| 2 | 31.2 | 30,380 | ~15% variance |

### HTTP Hot Server (model in memory)

| Run | Total Time (s) | Inference Time (ms) | Notes |
|-----|----------------|---------------------|-------|
| 1 | 11.2 | 11,042 | Consistent |
| 2 | 11.4 | 11,235 | Consistent |

### Analysis

| Metric | Value |
|--------|-------|
| Cold start overhead | ~16-20 seconds |
| Hot inference time | ~11 seconds |
| Cold/Hot ratio | **2.5-3x slower** |
| Model load time | ~16-20 seconds |

### Implications for Product

1. **One-off CLI calls:** 25-35 seconds per image (acceptable for occasional use)
2. **Batch/repeated use:** Run server mode, get ~11s per image (2.5x faster)
3. **AI agent integration:** Should prefer server mode if doing multiple analyses
