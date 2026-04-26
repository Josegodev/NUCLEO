# Shimmy Vision Functional Test Plan

## Purpose
This document outlines comprehensive functional testing for Shimmy Vision, an AI-facing tool designed to help AI agents analyze images, screenshots, and web pages. Since humans can use their eyes, this tool is primarily for AI consumption - allowing AI to "see" and extract structured information from visual content.

## How AI Agents Will Use This Tool

### Primary Use Cases
1. **Web Automation**: AI needs to find selectors/elements to click, fill forms, navigate
2. **Visual QA**: AI needs to verify UI state, check for errors, confirm expected content
3. **Data Extraction**: AI needs to read text, prices, status from screenshots
4. **Design Analysis**: AI needs to understand layout, colors, accessibility
5. **Documentation**: AI needs to describe what's on screen for logging/reporting

### Integration Patterns
- **CLI Tool**: `shimmy vision --image <path> --mode <mode>` - subprocess call
- **HTTP API**: `POST /api/vision` with JSON payload - REST client
- **Combined**: Screenshot capture + analysis in one call

## Tool Overview

### CLI Interface
```bash
shimmy vision [OPTIONS]
```

### Input Modes
| Flag | Description |
|------|-------------|
| `--image <PATH>` | Analyze a local image file |
| `--url <URL>` | Analyze a web page (fetch + screenshot) |
| `--screenshot` | Force screenshot capture for URL analysis |

### Analysis Modes (`--mode`)
| Mode | Purpose | Best For |
|------|---------|----------|
| `full` | Complete analysis: OCR, layout, visual, interaction | General purpose, first look |
| `ocr` | Text extraction focus - read all visible text | Reading content, data extraction |
| `layout` | UI structure focus - regions, elements, hierarchy | Understanding page structure |
| `brief` | Quick summary - concise visual description | Fast checks, status verification |
| `web` | Web-specific - includes DOM map for element targeting | Web automation, finding selectors |

### Output Options
| Flag | Description |
|------|-------------|
| `--output json` | Machine-readable JSON (default) |
| `--output pretty` | Human-readable formatted output |
| `--raw` | Include raw model output on parse failures |

### Performance Options
| Flag | Description |
|------|-------------|
| `--timeout <MS>` | Inference timeout (default: 180000ms) |
| `--gpu-backend <TYPE>` | Force GPU: auto, cpu, cuda, vulkan, opencl |
| `--cpu-moe` | Offload MoE experts to CPU (VRAM savings) |
| `--n-cpu-moe <N>` | Partial MoE offload (first N layers) |
| `--viewport-width/height` | Screenshot dimensions (default: 1280x720) |
| `--model-dirs` | Additional model search paths |

---

## Test Categories

### Category 1: Static Image Analysis (Local Files)

These tests use pre-existing screenshots from `theme-tester/screenshots/`.

#### 1.1 OCR Tests (Text Extraction)
| Test ID | Image | Mode | Purpose | Expected Output |
|---------|-------|------|---------|-----------------|
| OCR-01 | `01-model-chooser.png` | ocr | Read model dropdown names | List of model names in text_blocks |
| OCR-02 | `phase1-console.png` | ocr | Read console output text | Console log lines extracted |
| OCR-03 | `chat-test-no-models.png` | ocr | Read error/empty state text | "No models" message extracted |
| OCR-04 | `scene4-check-response.png` | ocr | Read chat response text | Response content extracted |
| OCR-05 | `02-selection-fail-diagnostic.png` | ocr | Read diagnostic text | Failure message extracted |

#### 1.2 Layout Analysis Tests
| Test ID | Image | Mode | Purpose | Expected Output |
|---------|-------|------|---------|-----------------|
| LAY-01 | `shimmy-theme.png` | layout | Large complex UI analysis | regions[], key_ui_elements[] populated |
| LAY-02 | `default-phase0.png` | layout | Minimal UI structure | Basic layout detected |
| LAY-03 | `02-chat-loaded.png` | layout | Chat interface regions | Identify header, chat area, input |
| LAY-04 | `after-click-*.png` | layout | Post-interaction state | Changed UI elements identified |

#### 1.3 Visual/Design Analysis Tests  
| Test ID | Image | Mode | Purpose | Expected Output |
|---------|-------|------|---------|-----------------|
| VIS-01 | Any dark theme | full | Detect dark mode | layout.theme = "dark" |
| VIS-02 | Any light theme | full | Detect light mode | layout.theme = "light" |
| VIS-03 | `shimmy-theme.png` | full | Color palette extraction | accent_colors[] with hex values |
| VIS-04 | High contrast UI | full | Accessibility check | contrast info in output |

#### 1.4 Brief Mode Tests (Quick Summaries)
| Test ID | Image | Mode | Purpose | Expected Output |
|---------|-------|------|---------|-----------------|
| BRF-01 | `default-phase0.png` (4KB) | brief | Tiny image summary | < 100 word description |
| BRF-02 | `shimmy-theme.png` (4.7MB) | brief | Large image summary | Concise despite complexity |
| BRF-03 | Any screenshot | brief | Response time check | Should be faster than full |

#### 1.5 Full Analysis Tests (Complete Output)
| Test ID | Image | Mode | Purpose | Expected Output |
|---------|-------|------|---------|-----------------|
| FUL-01 | `01-model-chooser.png` | full | All output fields populated | text_blocks, layout, visual, interaction |
| FUL-02 | `shimmy-theme.png` | full | Complex UI full analysis | Comprehensive breakdown |

#### 1.6 Image Size/Format Variations
| Test ID | Image | Purpose | Expected |
|---------|-------|---------|----------|
| SIZ-01 | `default-phase0.png` (4KB) | Smallest image | Fast processing |
| SIZ-02 | `shimmy-theme.png` (4.7MB) | Largest image | Handles without OOM |
| SIZ-03 | Various PNG files | Format support | All PNG work |
| SIZ-04 | Portrait orientation | Aspect ratio handling | Correct orientation |

### Category 2: Live Web Analysis (URL Input)

These tests use `--url` to fetch and analyze real websites.

#### 2.1 Simple Static Sites
| Test ID | URL | Mode | Purpose | Expected |
|---------|-----|------|---------|----------|
| WEB-01 | `https://example.com` | web | Simplest possible site | Clean DOM map |
| WEB-02 | `https://example.com` | full | Compare to web mode | Same visual, no DOM |

#### 2.2 Complex Public Sites  
| Test ID | URL | Mode | Purpose | Expected |
|---------|-----|------|---------|----------|
| WEB-03 | `https://news.ycombinator.com` | web | News aggregator | Links, headlines extracted |
| WEB-04 | `https://github.com` | web | Complex app | Navigation, elements found |
| WEB-05 | `https://docs.rs` | web | Documentation site | Code blocks, nav identified |
| WEB-06 | `https://httpbin.org` | web | API test site | Form elements found |

#### 2.3 DOM Map Extraction (Web Automation)
| Test ID | URL | Mode | Purpose | Expected |
|---------|-----|------|---------|----------|
| DOM-01 | `https://httpbin.org/forms/post` | web | Find form inputs | Input selectors in dom_map |
| DOM-02 | `https://example.com` | web | Find links | Anchor elements with hrefs |
| DOM-03 | News site | web | Find article links | Clickable headlines |

#### 2.4 Viewport Variations
| Test ID | URL | Viewport | Purpose | Expected |
|---------|-----|----------|---------|----------|
| VPT-01 | `https://example.com` | 375x667 (mobile) | Mobile layout | Mobile-appropriate regions |
| VPT-02 | `https://example.com` | 768x1024 (tablet) | Tablet layout | Medium layout |
| VPT-03 | `https://example.com` | 1920x1080 (desktop) | Full desktop | Wide layout |
| VPT-04 | `https://example.com` | 1280x720 (default) | Standard | Default behavior |

### Category 3: Mode Comparisons (Same Input, Different Modes)

| Test ID | Input | Modes to Compare | Purpose |
|---------|-------|------------------|---------|
| CMP-01 | `01-model-chooser.png` | ocr vs full | OCR should have more text detail |
| CMP-02 | `01-model-chooser.png` | layout vs full | Layout should have more structure |
| CMP-03 | `01-model-chooser.png` | brief vs full | Brief should be smaller output |
| CMP-04 | `https://example.com` | web vs full | Web should have dom_map |

### Category 4: HTTP API Tests (AI Agent Integration)

These simulate how an AI agent would call the API directly.

#### 4.1 Basic API Calls
| Test ID | Method | Payload | Expected |
|---------|--------|---------|----------|
| API-01 | POST /api/vision | image_base64 + mode:ocr | 200 + JSON response |
| API-02 | POST /api/vision | url + mode:web | 200 + DOM map |
| API-03 | POST /api/vision | missing image_base64 and url | 400 + error |
| API-04 | POST /api/vision | invalid base64 | 400 + decode error |

#### 4.2 License Validation via API
| Test ID | License Key | Expected |
|---------|-------------|----------|
| LIC-01 | Valid key | 200 + response |
| LIC-02 | Invalid key | 403 + license error |
| LIC-03 | Missing key | 402 + missing license |
| LIC-04 | Expired key | 403 + expired |

### Category 5: Error Handling & Edge Cases

| Test ID | Scenario | Expected |
|---------|----------|----------|
| ERR-01 | Non-existent image path | Clear file not found error |
| ERR-02 | Invalid URL | Connection/fetch error |
| ERR-03 | URL returns non-HTML | Graceful handling |
| ERR-04 | Timeout (--timeout 100) | Timeout error, no hang |
| ERR-05 | Very large image | Completes or clear memory error |
| ERR-06 | Empty image data | Validation error |

### Category 6: Real AI Agent Scenarios

Simulate actual AI use cases end-to-end.

| Test ID | Scenario | Steps | Success Criteria |
|---------|----------|-------|------------------|
| AGT-01 | "Find the login button" | 1. Screenshot page 2. web mode 3. Find button in dom_map | Button selector returned |
| AGT-02 | "Read the error message" | 1. Screenshot error 2. ocr mode 3. Extract text | Error text in output |
| AGT-03 | "Is dark mode enabled?" | 1. Screenshot UI 2. brief mode 3. Check theme | Theme correctly identified |
| AGT-04 | "What's the price?" | 1. Screenshot product 2. ocr mode 3. Find price | Price value extracted |
| AGT-05 | "Describe this page" | 1. Screenshot 2. full mode 3. Get description | Coherent description |

---

## Test Execution Approach

### ⚠️ CRITICAL: JSON Construction Rules

**NEVER use heredocs with command substitution for JSON with base64 data.**

```bash
# ❌ WRONG - heredoc with quotes prevents substitution
cat > file.json << 'EOF'
{"image_base64": "$(cat file.b64)"}
EOF
# Result: literal string "$(cat file.b64)" in JSON - HANGS FOR 25+ MINUTES

# ❌ WRONG - heredoc without quotes has escaping issues with base64
cat > file.json << EOF
{"image_base64": "$(cat file.b64)"}
EOF
# Result: base64 may contain characters that break JSON

# ✅ CORRECT - use jq with --rawfile
jq -n --rawfile img file.b64 '{"image_base64": $img, "mode": "ocr"}' > file.json

# ✅ CORRECT - use jq with --arg for small strings
jq -n --arg img "$(cat file.b64)" '{"image_base64": $img}' > file.json
```

### CLI Execution Pattern
```bash
# Set license once
export KEYGEN_PRODUCT_TOKEN="<token>"
export VISION_LICENSE="1CF681-F65AC1-34018A-CA470A-1B107D-V3"

# Run tests (CLI loads model each time - slow but simple)
shimmy vision --image <path> --mode <mode> --license "$VISION_LICENSE" --output json
```

### HTTP API Execution Pattern (Preferred - model stays loaded)
```bash
# Step 1: Create base64 file
base64 -w0 image.png > /tmp/image.b64

# Step 2: Build JSON with jq (SAFE - handles all escaping)
jq -n --rawfile img /tmp/image.b64 \
  --arg mode "ocr" \
  --arg license "$VISION_LICENSE" \
  '{image_base64: $img, mode: $mode, license: $license}' > /tmp/req.json

# Step 3: Send request
curl -s -X POST http://127.0.0.1:11436/api/vision \
  -H "Content-Type: application/json" \
  -d @/tmp/req.json | jq .

# URL analysis (no base64, simpler)
curl -s -X POST http://127.0.0.1:11436/api/vision \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "mode": "web",
    "license": "'"$VISION_LICENSE"'"
  }'
```

---

## Test Execution Log

### Environment
- **Date**: 2024-12-14
- **Shimmy Version**: 1.8.1
- **Model**: Qwen2-VL 7B (Q4_0, 4.12 GiB)
- **GPU**: NVIDIA RTX 3060 12GB (CUDA)
- **Server**: http://127.0.0.1:11436
- **License**: Keygen test key `1CF681-F65AC1-34018A-CA470A-1B107D-V3`
- **Screenshots Path**: `/c/Users/micha/repos/shimmy/theme-tester/screenshots/`

### Available Test Images
```
# Sorted by size
default-phase0.png                    4.2 KB   (smallest)
02-selection-fail-diagnostic.png      4.2 KB
03-chat-fail-diagnostic.png           4.2 KB
scene4-check-response.png            12 KB
chat-test-no-models.png              12 KB
01-model-chooser.png                115 KB
02-chat-loaded.png                   48 KB
phase1-console.png                  197 KB
shimmy-theme.png                     4.7 MB   (largest)
after-click-*.png                   ~194 KB  (interaction results)
```

---

## Test Results

### Category 1: Static Image Analysis

#### OCR-01: Model Chooser Text Extraction
**Command:**
```bash
shimmy vision --image screenshots/01-model-chooser.png --mode ocr --license $VISION_LICENSE
```
**Status:** ⏳ Pending
**Result:**
```
(output will be logged here)
```
**Assessment:** 

---

#### OCR-02: Console Output Text
**Command:**
```bash
shimmy vision --image screenshots/phase1-console.png --mode ocr --license $VISION_LICENSE
```
**Status:** ⏳ Pending
**Result:**
```
```
**Assessment:**

---

#### LAY-01: Complex UI Layout (Large Image)
**Command:**
```bash
shimmy vision --image screenshots/shimmy-theme.png --mode layout --license $VISION_LICENSE
```
**Status:** ⏳ Pending
**Result:**
```
```
**Assessment:**

---

#### BRF-01: Brief Summary (Small Image)
**Command:**
```bash
shimmy vision --image screenshots/default-phase0.png --mode brief --license $VISION_LICENSE
```
**Status:** ⏳ Pending
**Result:**
```
```
**Assessment:**

---

#### FUL-01: Full Analysis
**Command:**
```bash
shimmy vision --image screenshots/01-model-chooser.png --mode full --license $VISION_LICENSE
```
**Status:** ⏳ Pending
**Result:**
```
```
**Assessment:**

---

### Category 2: Live Web Analysis

#### WEB-01: Simple Static Site
**Command:**
```bash
shimmy vision --url "https://example.com" --mode web --license $VISION_LICENSE
```
**Status:** ⏳ Pending
**Result:**
```
```
**Assessment:**

---

#### WEB-03: Hacker News (Complex Links)
**Command:**
```bash
shimmy vision --url "https://news.ycombinator.com" --mode web --license $VISION_LICENSE
```
**Status:** ⏳ Pending
**Result:**
```
```
**Assessment:**

---

#### DOM-01: Form Input Detection
**Command:**
```bash
shimmy vision --url "https://httpbin.org/forms/post" --mode web --license $VISION_LICENSE
```
**Status:** ⏳ Pending
**Result:**
```
```
**Assessment:**

---

#### VPT-01: Mobile Viewport
**Command:**
```bash
shimmy vision --url "https://example.com" --mode web --viewport-width 375 --viewport-height 667 --license $VISION_LICENSE
```
**Status:** ⏳ Pending
**Result:**
```
```
**Assessment:**

---

### Category 3: Mode Comparisons

#### CMP-01: OCR vs Full
**Test:** Same image, compare ocr mode output vs full mode output
**Status:** ⏳ Pending
**Observations:**

---

### Category 4: HTTP API Tests

#### API-01: Basic Image via API
**Command:**
```bash
curl -s -X POST http://127.0.0.1:11436/api/vision \
  -H "Content-Type: application/json" \
  -d '{"image_base64": "...", "mode": "ocr", "license": "..."}'
```
**Status:** ⏳ Pending
**HTTP Status:** 
**Response:**
```
```

---

#### API-03: Missing Input Error
**Command:**
```bash
curl -s -X POST http://127.0.0.1:11436/api/vision \
  -H "Content-Type: application/json" \
  -d '{"mode": "ocr", "license": "..."}'
```
**Status:** ⏳ Pending
**Expected:** 400 Bad Request
**HTTP Status:**
**Response:**
```
```

---

#### LIC-03: Missing License
**Command:**
```bash
curl -s -X POST http://127.0.0.1:11436/api/vision \
  -H "Content-Type: application/json" \
  -d '{"image_base64": "...", "mode": "ocr"}'
```
**Status:** ⏳ Pending
**Expected:** 402 Payment Required
**HTTP Status:**
**Response:**
```
```

---

### Category 5: Error Handling

#### ERR-01: Non-existent File
**Command:**
```bash
shimmy vision --image /nonexistent/path.png --mode ocr --license $VISION_LICENSE
```
**Status:** ⏳ Pending
**Expected:** Clear error message
**Result:**
```
```

---

#### ERR-04: Timeout Test
**Command:**
```bash
shimmy vision --image screenshots/shimmy-theme.png --mode full --timeout 100 --license $VISION_LICENSE
```
**Status:** ⏳ Pending
**Expected:** Timeout error (not hang)
**Result:**
```
```

---

### Category 6: AI Agent Scenarios

#### AGT-02: Read Error Message
**Scenario:** An AI agent needs to read an error message from a screenshot
**Image:** `03-chat-fail-diagnostic.png`
**Command:**
```bash
shimmy vision --image screenshots/03-chat-fail-diagnostic.png --mode ocr --license $VISION_LICENSE
```
**Status:** ⏳ Pending
**Success Criteria:** Error text clearly extracted
**Result:**
```
```

---

#### AGT-03: Theme Detection
**Scenario:** AI needs to verify if dark mode is enabled
**Command:**
```bash
shimmy vision --image screenshots/shimmy-theme.png --mode brief --license $VISION_LICENSE
```
**Status:** ⏳ Pending
**Success Criteria:** Theme mentioned in output
**Result:**
```
```

---

## Summary

| Category | Total Tests | Passed | Failed | Pending |
|----------|-------------|--------|--------|---------|
| Static Image (OCR) | 5 | 0 | 0 | 5 |
| Static Image (Layout) | 4 | 0 | 0 | 4 |
| Static Image (Visual) | 4 | 0 | 0 | 4 |
| Static Image (Brief) | 3 | 0 | 0 | 3 |
| Static Image (Full) | 2 | 0 | 0 | 2 |
| Static Image (Size) | 4 | 0 | 0 | 4 |
| Web Analysis | 6 | 0 | 0 | 6 |
| DOM Extraction | 3 | 0 | 0 | 3 |
| Viewport | 4 | 0 | 0 | 4 |
| Mode Comparisons | 4 | 0 | 0 | 4 |
| HTTP API | 4 | 0 | 0 | 4 |
| License Validation | 4 | 0 | 0 | 4 |
| Error Handling | 6 | 0 | 0 | 6 |
| AI Agent Scenarios | 5 | 0 | 0 | 5 |
| **TOTAL** | **58** | **0** | **0** | **58** |

---

## Success Criteria

1. **Accuracy**: OCR correctly extracts visible text (> 90% accuracy)
2. **Structure**: JSON output matches documented schema
3. **Performance**: Completes within timeout (default 180s)
4. **Robustness**: Graceful error handling (no crashes)
5. **Consistency**: Same input produces consistent output structure
6. **DOM Quality**: Web mode provides usable selectors
7. **Mode Differentiation**: Different modes produce appropriately different output
