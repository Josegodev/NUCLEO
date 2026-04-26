# Vision Cross-Platform Testing Guide

## Overview

Before launching Shimmy Vision on Product Hunt, we need to ensure the vision features work correctly across all supported platforms. This guide provides a systematic approach to testing vision functionality on:

- Linux x86_64 (CUDA GPU acceleration)
- Linux ARM64 (CPU-only)
- Windows x86_64 (Vulkan GPU acceleration)
- macOS Intel (MLX GPU acceleration)
- macOS ARM64 (MLX GPU acceleration)

## Quick Test (Automated)

The fastest way to test all platforms:

```bash
# Run automated cross-platform tests
./scripts/test_vision_cross_platform.sh
```

This will:
- Build Docker containers for each platform
- Run vision tests using the test suite
- Generate a comprehensive test report
- Validate that all platforms pass

## Manual Testing

For more detailed testing or when you need to debug issues:

### Linux x86_64 (CUDA)

```bash
# Build with CUDA support
cargo build --release --features llama,vision,llama-cuda

# Test vision functionality
python3 scripts/test_cross_compiled_vision.py \
    --binary ./target/release/shimmy \
    --test-image assets/vision-samples/final-test.png \
    --license "your-test-license" \
    --output-report linux-cuda-results.json
```

### Linux ARM64

```bash
# Cross-compile for ARM64
cargo build --release --target aarch64-unknown-linux-gnu --features llama,vision

# Test (requires ARM64 environment or emulation)
python3 scripts/test_cross_compiled_vision.py \
    --binary ./target/aarch64-unknown-linux-gnu/release/shimmy \
    --cpu-only \
    --output-report linux-arm64-results.json
```

### Windows x86_64

```bash
# Cross-compile for Windows
cargo build --release --target x86_64-pc-windows-msvc --features llama,vision,llama-vulkan

# Test using Wine (on Linux)
# Note: Requires Wine setup for Windows testing
```

### macOS Testing

Since we can't run macOS in Docker, macOS testing requires:

1. **Cross-compilation validation** (automated):
   ```bash
   ./scripts/test_vision_cross_platform.sh  # Includes macOS cross-compilation check
   ```

2. **Manual testing on actual macOS hardware** (required):
   - Intel Mac: Test with MLX features
   - Apple Silicon Mac: Test with MLX features
   - Validate GPU acceleration works
   - Check performance meets expectations

## Test Images

The test suite uses these standard images:
- `assets/vision-samples/final-test.png` - Primary test image
- `assets/vision-samples/ocr-test.png` - OCR accuracy validation
- `assets/vision-samples/layout-test.png` - Layout analysis validation

## Performance Expectations

| Platform | Expected Time | GPU Support |
|----------|---------------|-------------|
| Linux x86_64 (CUDA) | 4-15 seconds | ✅ NVIDIA GPU |
| Linux ARM64 | 60-120 seconds | ❌ CPU-only |
| Windows x86_64 | 4-15 seconds | ✅ Vulkan |
| macOS Intel | 10-30 seconds | ✅ MLX |
| macOS ARM64 | 4-15 seconds | ✅ MLX |

## License Testing

Vision features require valid licenses. The test suite validates:
- License validation is enforced (402 errors for invalid licenses)
- Valid licenses allow vision processing
- License usage is tracked correctly

## Pre-Launch Checklist

- [ ] Linux x86_64 CUDA: Tests pass
- [ ] Linux ARM64: Tests pass
- [ ] Windows x86_64: Tests pass
- [ ] macOS Intel: Manual testing completed
- [ ] macOS ARM64: Manual testing completed
- [ ] Performance meets expectations on all platforms
- [ ] License validation working correctly
- [ ] Documentation updated with platform requirements
- [ ] Test reports archived for reference

## Troubleshooting

### Common Issues

1. **CUDA not available**: Ensure NVIDIA drivers are installed in Docker
2. **Wine setup issues**: Windows testing requires proper Wine configuration
3. **ARM64 emulation**: May require QEMU setup for cross-platform testing
4. **License errors**: Ensure test license keys are properly configured

### Debug Mode

Run tests with verbose output:
```bash
SHIMMY_VISION_TRACE=1 ./scripts/test_cross_compiled_vision.py --binary ./target/release/shimmy
```

## CI/CD Integration

The testing framework integrates with GitHub Actions:

```yaml
- name: Run Cross-Platform Vision Tests
  run: ./scripts/test_vision_cross_platform.sh
```

This ensures vision functionality is validated on all platforms before any release.

## External Testing Requirements

Since you don't have access to Apple Silicon hardware, you'll need to coordinate with external testers for macOS ARM64 validation. Consider:

1. **GitHub Sponsors**: Reach out to Apple Silicon users
2. **Beta testers**: Recruit from your user community
3. **Cloud options**: Use MacStadium or similar for testing
4. **Cross-compilation validation**: At minimum, ensure builds work correctly

## Go/No-Go Decision

**GO criteria (all must pass):**
- ✅ All automated platform tests pass
- ✅ Manual macOS testing completed
- ✅ Performance within acceptable ranges
- ✅ License validation working
- ✅ No critical bugs found

**NO-GO criteria (any failure):**
- ❌ Any platform fails automated tests
- ❌ Performance issues on GPU platforms
- ❌ License validation broken
- ❌ Critical vision functionality bugs

Only proceed with Product Hunt launch when all GO criteria are met.