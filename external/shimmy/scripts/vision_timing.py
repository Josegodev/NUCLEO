import argparse
import base64
import json
import os
import re
import time
import urllib.error
import urllib.request


DEFAULT_IMAGES = [
	"assets/vision-samples/extended-02-after-5-messages.png",
	"assets/vision-samples/final-test.png",
	"assets/vision-samples/scene2-models.png",
	"assets/vision-samples/scene4-check-response.png",
]


def post_vision(
	url: str,
	image_path: str,
	mode: str,
	timeout_ms: int,
	socket_timeout_s: int,
	raw: bool,
) -> dict:
	with open(image_path, "rb") as f:
		image_bytes = f.read()

	body = {
		"mode": mode,
		"timeout_ms": timeout_ms,
		"raw": raw,
		"filename": os.path.basename(image_path),
		"image_base64": base64.b64encode(image_bytes).decode("ascii"),
	}

	req = urllib.request.Request(
		url,
		data=json.dumps(body).encode("utf-8"),
		headers={"Content-Type": "application/json"},
		method="POST",
	)

	try:
		with urllib.request.urlopen(req, timeout=socket_timeout_s) as resp:
			return json.loads(resp.read().decode("utf-8"))
	except urllib.error.HTTPError as e:
		body_bytes = b""
		try:
			body_bytes = e.read() or b""
		except Exception:
			body_bytes = b""
		body_text = ""
		try:
			body_text = body_bytes.decode("utf-8", errors="replace")
		except Exception:
			body_text = repr(body_bytes)
		return {
			"_http_error": {
				"code": int(getattr(e, "code", 0) or 0),
				"reason": str(getattr(e, "reason", "")),
				"body": body_text,
			}
		}
	except Exception as e:
		return {"_exception": str(e)}


def main() -> int:
	parser = argparse.ArgumentParser(description="Shimmy vision timing runner")
	parser.add_argument(
		"--url",
		default="http://127.0.0.1:11435/api/vision",
		help="Vision endpoint URL (default: http://127.0.0.1:11435/api/vision)",
	)
	parser.add_argument("--mode", default="full", help="Vision mode (default: full)")
	parser.add_argument(
		"--timeout-ms",
		type=int,
		default=600000,
		help="Server-side timeout_ms to send (default: 600000)",
	)
	parser.add_argument(
		"--socket-timeout-s",
		type=int,
		default=900,
		help="Client socket timeout in seconds (default: 900)",
	)
	parser.add_argument(
		"--raw",
		action="store_true",
		help="Request raw_model_output in the response (sets raw=true)",
	)
	parser.add_argument(
		"--out-dir",
		default=None,
		help="If set, write each JSON response to this directory",
	)
	parser.add_argument(
		"--fail-fast",
		action="store_true",
		help="Stop on first error (HTTP error or exception)",
	)
	parser.add_argument(
		"images",
		nargs="*",
		help="Image paths (default: assets/vision-samples/* from docs/vision-timings.md)",
	)
	args = parser.parse_args()

	images = args.images or DEFAULT_IMAGES

	out_dir = args.out_dir
	if out_dir is not None:
		os.makedirs(out_dir, exist_ok=True)

	rows = []
	for image_path in images:
		print(f"running: {image_path}", flush=True)
		start = time.perf_counter()
		data = post_vision(
			args.url,
			image_path,
			args.mode,
			args.timeout_ms,
			args.socket_timeout_s,
			args.raw,
		)
		elapsed = time.perf_counter() - start

		http_error = data.get("_http_error") if isinstance(data, dict) else None
		exception_text = data.get("_exception") if isinstance(data, dict) else None
		if http_error is not None or exception_text is not None:
			msg = ""
			if http_error is not None:
				msg = f"HTTP {http_error.get('code')}: {http_error.get('reason')}"
			elif exception_text is not None:
				msg = f"EXCEPTION: {exception_text}"
			print(f"error: {image_path}: {msg}", flush=True)
			if args.fail_fast:
				raise SystemExit(2)

		meta = data.get("meta") or {}
		parse_warnings = meta.get("parse_warnings")
		if isinstance(parse_warnings, list):
			parse_warnings = "; ".join(parse_warnings)
		if http_error is not None:
			parse_warnings = (
				f"HTTP {http_error.get('code')}: {http_error.get('reason')}"
			)
		if exception_text is not None:
			parse_warnings = f"EXCEPTION: {exception_text}"
		rows.append(
			{
				"image": image_path,
				"request_seconds": round(elapsed, 3),
				"model_duration_ms": meta.get("duration_ms"),
				"backend": meta.get("backend"),
				"parse_warnings": parse_warnings or "—",
			}
		)

		if out_dir is not None:
			safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", os.path.basename(image_path))
			out_path = os.path.join(out_dir, f"{safe_name}.json")
			with open(out_path, "w", encoding="utf-8") as f:
				json.dump(data, f, ensure_ascii=False, indent=2)

	print("image,request_seconds,model_duration_ms,backend,parse_warnings")
	for row in rows:
		print(
			f"{row['image']},{row['request_seconds']},{row['model_duration_ms']},{row['backend']},{row['parse_warnings']}"
		)

	return 0


if __name__ == "__main__":
	raise SystemExit(main())
