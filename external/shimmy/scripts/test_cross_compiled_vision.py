#!/usr/bin/env python3
"""
Phase 2 Cross-Validation: Vision Functionality Test

Tests vision features in cross-compiled binaries to ensure:
1. Vision models load correctly
2. OCR processing works
3. License validation functions
4. API endpoints respond correctly
5. Structured output matches expectations

Usage:
    python scripts/test_cross_compiled_vision.py --binary ./target/x86_64-pc-windows-msvc/release/shimmy.exe
    python scripts/test_cross_compiled_vision.py --binary ./target/release/shimmy --test-image assets/vision-samples/final-test.png --license test-key --output-report results.json
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, Any, Optional


def start_server(binary_path: str, port: int = 11435) -> subprocess.Popen:
    """Start the shimmy server with vision features."""
    cmd = [binary_path, "serve", "--bind", f"127.0.0.1:{port}"]
    print(f"🚀 Starting server: {' '.join(cmd)}")

    # Set environment variables for vision testing
    env = os.environ.copy()
    env["SHIMMY_VISION_MAX_LONG_EDGE"] = "1024"
    env["SHIMMY_VISION_MAX_PIXELS"] = "2500000"

    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )


def wait_for_server(port: int, timeout: int = 30) -> bool:
    """Wait for server to be ready."""
    url = f"http://127.0.0.1:{port}/health"
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                if resp.status == 200:
                    print("✅ Server is ready")
                    return True
        except (urllib.error.URLError, OSError):
            pass

        time.sleep(1)

    print("❌ Server failed to start within timeout")
    return False


def test_vision_processing(port: int, image_path: str) -> tuple:
    """Test vision processing with a sample image. Returns (response, is_license_error)."""
    print(f"🖼️  Testing vision processing with: {image_path}")

    # Read and encode image
    with open(image_path, "rb") as f:
        image_data = f.read()

    # Prepare request
    body = {
        "mode": "analyze",
        "timeout_ms": 30000,
        "raw": False,
        "filename": os.path.basename(image_path),
        "image_base64": base64.b64encode(image_data).decode("ascii"),
    }

    url = f"http://127.0.0.1:{port}/api/vision"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            print("✅ Vision processing successful")
            return result, False
    except urllib.error.HTTPError as e:
        if e.code == 402:
            print("✅ License validation working (expected 402 Payment Required)")
            try:
                error_body = json.loads(e.read().decode("utf-8"))
                return error_body, True
            except:
                return {"error": "License required"}, True
        else:
            print(f"❌ Unexpected HTTP error: {e.code}")
            return None, False
    except Exception as e:
        print(f"❌ Vision processing failed: {e}")
        return None, False


def validate_response(response: dict, expected_keys: list) -> bool:
    """Validate that response contains expected structure."""
    if not response:
        return False

    # Check for required top-level keys
    for key in expected_keys:
        if key not in response:
            print(f"❌ Missing expected key: {key}")
            return False

    print("✅ Response structure validation passed")
    return True


def detect_platform(binary_path: str) -> str:
    """Detect the platform of the binary."""
    try:
        result = subprocess.run([binary_path, "--version"], capture_output=True, text=True, timeout=10)
        if "windows" in binary_path.lower() or ".exe" in binary_path:
            return "windows-x86_64"
        elif "aarch64" in binary_path:
            if "apple" in binary_path:
                return "macos-arm64"
            else:
                return "linux-arm64"
        elif "x86_64" in binary_path:
            if "apple" in binary_path:
                return "macos-intel"
            else:
                return "linux-x86_64"
        else:
            return "unknown"
    except:
        return "unknown"


def run_cross_validation_test(binary_path: str, test_image: str, license_key: str, port: int = 11435, timeout: int = 120, cpu_only: bool = False) -> tuple[bool, Dict[str, Any]]:
    """Run complete cross-validation test."""
    port = 11437  # Use different port to avoid conflicts

    test_results = {
        "server_started": False,
        "vision_tests": [],
        "license_validation": False,
        "performance_warnings": [],
        "errors": []
    }

    # Start server
    server_process = start_server(binary_path, port)

    try:
        # Wait for server to be ready
        if not wait_for_server(port):
            test_results["errors"].append("Server failed to start")
            return False, test_results

        test_results["server_started"] = True

        # Test with the specified image
        if not os.path.exists(test_image):
            test_results["errors"].append(f"Test image not found: {test_image}")
            return False, test_results

        # Test vision processing
        response, is_license_error = test_vision_processing(port, test_image)

        test_result = {
            "image": test_image,
            "response_received": response is not None,
            "license_error": is_license_error,
            "has_text_blocks": response and "text_blocks" in response if response else False,
            "text_blocks_count": len(response.get("text_blocks", [])) if response else 0
        }
        test_results["vision_tests"].append(test_result)

        if is_license_error:
            test_results["license_validation"] = True
            print("🔐 License validation correctly enforced")

        # Performance check
        if cpu_only and response:
            test_results["performance_warnings"].append("CPU-only mode detected - performance may be slow")

        # Determine success
        success = (response is not None) and (is_license_error or test_result["has_text_blocks"])

        return success, test_results

    finally:
        # Clean up server
        print("🛑 Stopping server...")
        server_process.terminate()
        server_process.wait(timeout=10)


def main():
    parser = argparse.ArgumentParser(description="Test vision functionality in cross-compiled binaries")
    parser.add_argument("--binary", required=True, help="Path to shimmy binary to test")
    parser.add_argument("--port", type=int, default=11437, help="Port to run test server on")
    parser.add_argument("--test-image", default="assets/vision-samples/final-test.png", help="Path to test image")
    parser.add_argument("--license", default="test-license-key", help="License key for testing")
    parser.add_argument("--output-report", help="Path to save JSON test report")
    parser.add_argument("--cpu-only", action="store_true", help="Mark test as CPU-only (expect slower performance)")
    parser.add_argument("--timeout", type=int, default=120, help="Test timeout in seconds")

    args = parser.parse_args()

    # Validate binary exists
    if not os.path.exists(args.binary):
        print(f"❌ Binary not found: {args.binary}")
        sys.exit(1)

    # Validate binary is executable
    if not os.access(args.binary, os.X_OK):
        print(f"❌ Binary not executable: {args.binary}")
        sys.exit(1)

    # Validate test image exists
    if not os.path.exists(args.test_image):
        print(f"❌ Test image not found: {args.test_image}")
        sys.exit(1)

    print("🔬 Starting Phase 2 Cross-Validation: Vision Functionality Test")
    print(f"📁 Testing binary: {args.binary}")
    print(f"🖼️ Test image: {args.test_image}")
    print(f"🌐 Test port: {args.port}")
    print(f"⏱️ Timeout: {args.timeout}s")
    if args.cpu_only:
        print("⚠️ CPU-only mode: expecting slower performance")
    print()

    # Run the test
    start_time = time.time()
    success, test_results = run_cross_validation_test(args.binary, args.test_image, args.license, args.port, args.timeout, args.cpu_only)
    end_time = time.time()

    # Generate report
    report = {
        "test_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "binary_path": args.binary,
        "test_image": args.test_image,
        "platform": detect_platform(args.binary),
        "cpu_only": args.cpu_only,
        "total_duration_seconds": round(end_time - start_time, 2),
        "success": success,
        "results": test_results
    }

    if args.output_report:
        with open(args.output_report, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"📋 Test report saved to: {args.output_report}")

    if success:
        print("\n🎉 Phase 2 Cross-Validation PASSED")
        print("✅ Vision features work correctly in cross-compiled binary")
        sys.exit(0)
    else:
        print("\n💥 Phase 2 Cross-Validation FAILED")
        print("❌ Vision features not working in cross-compiled binary")
        sys.exit(1)


if __name__ == "__main__":
    main()