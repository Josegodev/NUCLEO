---
applyTo: "**"
---

# Shimmy Vision Testing Instructions

This document provides comprehensive testing instructions specifically for the Shimmy Vision feature. These tests validate the end-to-end functionality of image analysis and vision capabilities within the Shimmy ecosystem.

## Prerequisites

- **GPU Hardware Required**: Vision processing requires a GPU with at least 4GB VRAM for reasonable performance. CPU-only operation is extremely slow and not suitable for testing or production use.
- Shimmy built with `vision` feature: `cargo build --features llama,vision,llama-cuda` (GPU recommended)
- Vision models available in `models/` directory
- Test images available in `assets/vision-samples/`
- Environment variables configured:
  - `SHIMMY_VISION_MAX_LONG_EDGE=1024` (optional, default 1024)
  - `SHIMMY_VISION_MAX_PIXELS=2500000` (optional, default 2.5M)

## Test Execution Steps

### Step 1: Basic Vision Model Loading
**Purpose**: Verify vision models load correctly and basic inference works.

**Commands to run:**
```bash
# Test vision model loading (GPU recommended)
cd /c/Users/micha/repos/shimmy-workspace && \
cargo run --features llama,vision,llama-cuda -- probe vision-model-name

# Test basic image analysis (GPU recommended)
cd /c/Users/micha/repos/shimmy-workspace && \
cargo run --features llama,vision,llama-cuda -- generate \
  --name vision-model-name \
  --prompt "Describe this image" \
  --image assets/vision-samples/test-image.jpg \
  --max-tokens 100
```

**Expected Results:**
- Model loads without errors
- Image analysis returns descriptive text
- No crashes or memory issues

### Step 2: Vision API Endpoints
**Purpose**: Test HTTP API endpoints for vision functionality.

**Commands to run:**
```bash
# Start vision server (GPU recommended)
cd /c/Users/micha/repos/shimmy-workspace && \
cargo run --features llama,vision,llama-cuda -- serve --bind 127.0.0.1:11435 &

# Wait for server to start
sleep 5

# Test vision API endpoint
curl -X POST http://127.0.0.1:11435/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "vision-model-name",
    "prompt": "What do you see in this image?",
    "image": "data:image/jpeg;base64,'$(base64 -w 0 assets/vision-samples/test-image.jpg)'",
    "stream": false,
    "max_tokens": 200
  }'
```

**Expected Results:**
- Server starts successfully
- API returns 200 status
- Response contains image analysis
- JSON format is correct

### Step 3: Vision WebSocket Streaming
**Purpose**: Test real-time vision analysis via WebSocket.

**Commands to run:**
```bash
# Test WebSocket vision endpoint (requires websocket client)
cd /c/Users/micha/repos/shimmy-workspace && \
python -c "
import websocket
import json
import base64

# Connect to vision WebSocket
ws = websocket.create_connection('ws://127.0.0.1:11435/ws/generate')

# Send vision request
with open('assets/vision-samples/test-image.jpg', 'rb') as f:
    img_data = base64.b64encode(f.read()).decode()

request = {
    'model': 'vision-model-name',
    'prompt': 'Analyze this image in detail',
    'image': f'data:image/jpeg;base64,{img_data}',
    'max_tokens': 300
}

ws.send(json.dumps(request))

# Receive streaming response
while True:
    result = ws.recv()
    data = json.loads(result)
    if 'done' in data and data['done']:
        break
    print(data.get('text', ''), end='')

ws.close()
"
```

**Expected Results:**
- WebSocket connection established
- Streaming tokens received
- Complete analysis generated
- Connection closes cleanly

### Step 4: Vision Performance Testing
**Purpose**: Validate vision processing performance and resource usage.

**Commands to run:**
```bash
# Test vision performance with different image sizes
cd /c/Users/micha/repos/shimmy-workspace && \
for img in assets/vision-samples/*.jpg; do
  echo "Testing $img..."
  time cargo run --features llama,vision,llama-cuda -- generate \
    --name vision-model-name \
    --prompt "Brief description" \
    --image "$img" \
    --max-tokens 50
  echo "---"
done

# Monitor GPU usage during vision processing
nvidia-smi --query-gpu=timestamp,utilization.gpu,memory.used,memory.total \
  --format=csv -l 1 &
NVIDIA_PID=$!

# Run vision test
cargo run --features llama,vision,llama-cuda -- generate \
  --name vision-model-name \
  --prompt "Detailed analysis" \
  --image assets/vision-samples/large-image.jpg \
  --max-tokens 200

# Stop monitoring
kill $NVIDIA_PID
```

**Expected Results:**
- Processing completes within reasonable time (< 30s for typical images)
- GPU utilization appropriate for vision tasks
- Memory usage stays within bounds
- No GPU memory leaks

### Step 5: Vision Error Handling
**Purpose**: Test error conditions and edge cases.

**Commands to run:**
```bash
# Test invalid image format
cd /c/Users/micha/repos/shimmy-workspace && \
cargo run --features llama,vision,llama-cuda -- generate \
  --name vision-model-name \
  --prompt "Analyze" \
  --image assets/invalid-image.txt \
  --max-tokens 50

# Test oversized image
curl -X POST http://127.0.0.1:11435/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "vision-model-name",
    "prompt": "What is this?",
    "image": "data:image/jpeg;base64,'$(base64 -w 0 assets/vision-samples/very-large-image.jpg)'",
    "max_tokens": 100
  }'

# Test missing image
curl -X POST http://127.0.0.1:11435/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "vision-model-name",
    "prompt": "Describe the image",
    "max_tokens": 50
  }'
```

**Expected Results:**
- Invalid formats return appropriate error messages
- Oversized images handled gracefully (resized/downsampled)
- Missing image data returns clear error
- No crashes on error conditions

### Step 6: Vision Integration Testing
**Purpose**: Test vision combined with other Shimmy features.

**Commands to run:**
```bash
# Test vision + regular text generation in sequence
cd /c/Users/micha/repos/shimmy-workspace && \
VISION_DESC=$(cargo run --features llama,vision -- generate \
  --name vision-model-name \
  --prompt "Describe this chart" \
  --image assets/vision-samples/chart.jpg \
  --max-tokens 100)

# Use vision output as context for text generation
cargo run --features llama -- generate \
  --name text-model-name \
  --prompt "Based on this image description: $VISION_DESC. What insights can you draw?" \
  --max-tokens 200
```

**Expected Results:**
- Vision analysis provides useful context
- Text model can process vision-derived insights
- Combined workflow functions end-to-end

## Success Criteria

✅ **All tests pass when:**
- Vision models load without errors
- Image analysis returns coherent descriptions
- API endpoints respond correctly
- WebSocket streaming works
- Performance is acceptable (< 30s for typical images)
- Error conditions handled gracefully
- Integration with other features works

## Common Issues & Troubleshooting

### Issue: Vision model fails to load
**Solution:** Check model file exists and is compatible with vision feature

### Issue: Image processing fails
**Solution:** Verify image format (JPEG/PNG) and file integrity

### Issue: GPU memory errors
**Solution:** Reduce `SHIMMY_VISION_MAX_PIXELS` or image size

### Issue: WebSocket streaming stalls
**Solution:** Check server logs for vision processing errors

### Issue: Poor analysis quality
**Solution:** Ensure model is vision-capable and properly trained

## Vision Model Compatibility

- **Supported formats:** JPEG, PNG, WebP
- **Recommended resolution:** Max 1024px on longest edge
- **Memory requirements:** 4-8GB GPU RAM minimum
- **Performance:** 10-30 seconds per image analysis

## Test Environment Reset

To reset vision test environment:

```bash
# Kill any running vision servers
pkill -f "shimmy.*serve"

# Clear GPU memory
nvidia-smi --gpu-reset

# Reset environment variables
unset SHIMMY_VISION_MAX_LONG_EDGE
unset SHIMMY_VISION_MAX_PIXELS
```

## Notes

- Vision testing requires GPU with sufficient VRAM
- Test images should be varied (charts, photos, documents, etc.)
- Performance benchmarks should be run on consistent hardware
- Vision models are larger and slower than text-only models
- Integration testing validates vision as part of broader workflows