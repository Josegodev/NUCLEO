#!/bin/bash
# Cross-Platform Vision Testing Script
# Tests vision functionality across all supported platforms using Docker

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "🧪 Shimmy Vision Cross-Platform Testing"
echo "======================================"
echo "Testing vision functionality across all supported platforms"
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required for cross-platform testing"
    exit 1
fi

# Test results tracking
declare -A test_results
declare -A test_durations

run_test() {
    local platform=$1
    local dockerfile=$2
    local tag="vision-test-$platform"
    local start_time=$(date +%s)

    echo "🏗️ Building and testing: $platform"
    echo "Dockerfile: $dockerfile"

    # Build the container
    if ! docker build -f "$dockerfile" -t "$tag" .; then
        echo "❌ Build failed for $platform"
        test_results[$platform]="BUILD_FAILED"
        return 1
    fi

    # Run the test
    echo "🚀 Running tests for $platform..."
    if docker run -v "$(pwd)":/workspace "$tag"; then
        echo "✅ Tests passed for $platform"
        test_results[$platform]="PASSED"
    else
        echo "❌ Tests failed for $platform"
        test_results[$platform]="FAILED"
        return 1
    fi

    local end_time=$(date +%s)
    test_durations[$platform]=$((end_time - start_time))
}

# Test platforms
echo "📋 Testing platforms:"
echo "  - Linux x86_64 (CUDA)"
echo "  - Linux ARM64"
echo "  - Windows x86_64 (Wine)"
echo "  - macOS Cross-Compilation"
echo ""

# Run tests
run_test "linux-cuda" "packaging/docker/Dockerfile.vision-test-linux-cuda"
run_test "linux-arm64" "packaging/docker/Dockerfile.vision-test-linux-arm64"
run_test "windows" "packaging/docker/Dockerfile.vision-test-windows"
run_test "macos-cross" "packaging/docker/Dockerfile.vision-test-macos-cross"

# Summary
echo ""
echo "📊 Test Results Summary"
echo "======================"

all_passed=true
for platform in "${!test_results[@]}"; do
    status="${test_results[$platform]}"
    duration="${test_durations[$platform]:-0}"

    case $status in
        "PASSED")
            echo "✅ $platform: PASSED (${duration}s)"
            ;;
        "BUILD_FAILED")
            echo "❌ $platform: BUILD FAILED"
            all_passed=false
            ;;
        "FAILED")
            echo "❌ $platform: TESTS FAILED"
            all_passed=false
            ;;
    esac
done

echo ""
if [ "$all_passed" = true ]; then
    echo "🎉 ALL CROSS-PLATFORM VISION TESTS PASSED!"
    echo "✅ Ready for Product Hunt launch"
    echo ""
    echo "📋 Next steps:"
    echo "1. Run manual testing on actual macOS hardware (Intel + ARM64)"
    echo "2. Validate performance meets expectations"
    echo "3. Update release notes with platform support"
    echo "4. Prepare Product Hunt launch materials"
    exit 0
else
    echo "💥 CROSS-PLATFORM VISION TESTS FAILED!"
    echo "❌ DO NOT LAUNCH until all platforms pass"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "1. Check Docker logs for specific errors"
    echo "2. Ensure GPU drivers are available for CUDA tests"
    echo "3. Verify vision model downloads are working"
    echo "4. Check license key configuration"
    exit 1
fi