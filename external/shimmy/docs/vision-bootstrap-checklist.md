# Vision Bootstrap Checklist (Single Model)

## Goal
- Rig Shimmy vision to the one validated vision model and its matching binary, with a first-run download/bootstrap that “just works.”

## Single Model Binding
- Model name: **TBD (the validated vision model)**
- GGUF URL: **TBD**
- mmproj URL: **TBD**
- Expected hashes/sizes: **TBD**

## Tasks (check off as done)
- [ ] Rebuild `llama-cpp-minicpm` clean with clip/mmproj support (no stale artifacts).
- [ ] Wire `shimmy vision` to a bootstrapper that checks/downloads the single model GGUF + mmproj into cache.
- [ ] Hard-code the single model choice in the bootstrapper (no alternatives exposed).
- [ ] Add checksum/size verification after download; fail fast with a clear message.
- [ ] Ensure the vision CLI invocation uses the downloaded paths and the rebuilt binary.
- [ ] Add user-facing prompts: first run explains download and paths; subsequent runs are silent unless missing files.
- [ ] Add a small status command/log line that prints which model file paths are used.
- [ ] Smoke-test on a clean workspace: missing files → download → run vision CLI successfully.
- [ ] Document the first-run flow in `README`/`docs/` once validated.

## Notes
- License flow deferred; focus on working prototype first.
- Keep to the validated model only; no other models should be offered in vision mode.
