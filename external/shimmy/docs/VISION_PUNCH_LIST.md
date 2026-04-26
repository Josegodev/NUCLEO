# Shimmy Vision — Punch List

## Must-do before release
- Confirm URL/web mode is safe for untrusted input (SSRF protections, timeouts, size limits) and add a short security note to docs.
- Add an end-to-end functional test script that starts `serve-vision-gpu` and runs 1 image + 1 URL request (fails fast, prints clear diagnostics).
- Verify license failure happens *before* any model download.
- Document first-run model download paths, disk usage (~5.7GB), and how to pre-seed model files for offline installs.

## High-value next steps
- Make model downloads resumable (range requests) and add progress output for CLI.
- Add a cross-process download lock (so two shimmy processes can’t download the same files concurrently).
- Add HTTP rate limiting for `/api/vision` (especially for `--url`/web mode).
- Add stricter image input limits/config (max pixels/bytes) with clear errors.

## Docs / onboarding
- Update `README.md` + `docs/SHIMMY_VISION_SPEC.md` to link a single “Vision Quickstart” page (install, license, first run, troubleshooting).
- Add a troubleshooting section for: missing CUDA, missing Chromium, model checksum mismatch, and license validation failures.

## Observability
- Ensure logs never include license keys, raw base64, or fetched URLs in production level logs.
- Add structured fields for: mode, image dimensions, duration, and error category.
