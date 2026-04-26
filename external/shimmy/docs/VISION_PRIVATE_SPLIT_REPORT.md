# Vision Paid Feature: Private Repo / Crate Split Report (2025-12-15)

## Executive summary
You’re correct: if the Vision implementation ships as public source, a developer can trivially remove the license checks and build their own “free” Vision binary. You cannot prevent that with code tricks.

The best-practice fix is **open-core / paid plugin**:
- Keep `shimmy` core public.
- Move **all Vision implementation + license enforcement** into a **separate private repo**.
- Distribute Vision as either:
  1) a **separate closed-source binary** (recommended), or
  2) a **private crate** linked into your official release binary.

This doesn’t make piracy impossible (a determined attacker can still patch a binary), but it **eliminates the “one-line patch”** problem and dramatically reduces casual bypass.

## Threat model (practical)
- **If source is public**: bypass is trivial (fork, delete checks, recompile).
- **If source is private but runs locally**: bypass is still possible via binary patching, but requires reverse-engineering effort.
- **If inference runs on your servers**: server-side enforcement is the only approach that meaningfully prevents bypass.

Given your product is for developers and runs locally, the goal is realistic deterrence:
- remove source-level bypass
- make unauthorized use costly/annoying
- keep “official” builds, support, and updates behind payment

## Current code boundaries in this repo
Vision touches these public integration points:
- CLI: `src/cli.rs` has `Command::Vision` behind `cfg(feature = "vision")`
- HTTP: `src/api.rs` exposes `POST /api/vision` behind `cfg(feature = "vision")`
- App state: `AppState` contains `vision_license_manager` behind `cfg(feature = "vision")`
- Vision implementation + model bootstrap: `src/vision.rs`
- License enforcement: `src/vision_license.rs`

These are good seams: Vision is already behind a single cargo feature.

## Options

### Option A (recommended): Private “Vision Engine” binary + public shim adapter
**Idea:** Vision is a separate executable (e.g. `shimmy-vision-engine`) that:
- validates Keygen license
- manages model bootstrap/cache
- runs inference

Public `shimmy`:
- keeps `/api/vision` and `shimmy vision` UX
- delegates work to the private engine via a local IPC boundary:
  - simplest: spawn process, pass JSON on stdin, receive JSON on stdout
  - better: start engine as a local HTTP socket and proxy requests

Pros:
- Vision code doesn’t ship in public source
- clear separation; you can version/distribute engine independently
- easiest to keep licensing logic entirely private

Cons:
- slightly more engineering (IPC + packaging)
- still patchable, but much harder than “delete 3 lines and rebuild”

### Option B: Private crate linked into `shimmy` (open-core via optional dependency)
**Idea:** Move `vision.rs` + `vision_license.rs` into private repo crate `shimmy-vision`.

Public `shimmy`:
- keeps CLI + HTTP wiring
- `vision` feature becomes `vision = ["dep:shimmy-vision"]`
- only official builds (your CI) have access to the private repo

Pros:
- minimal runtime change (no IPC)
- very clean from a Rust architecture perspective

Cons:
- anyone with the private crate can still build; you must control distribution
- still patchable at binary level
- public contributors cannot build `--features vision` (acceptable for open-core)

### Option C: Hosted Vision
Pros:
- strongest enforcement
Cons:
- you now operate infrastructure and inference costs

## Best-practice recommendation
Given your constraints (local-first, developer buyers, you already have Stripe→Keygen):

1) Do **Option A** if you want the cleanest “paid plugin” story and future-proofing.
2) Do **Option B** if you want minimal refactor now and you’re comfortable distributing only official binaries.

My suggestion: **start with Option B (fastest)**, then evolve to Option A when you want a smoother installer/onboarding and tighter IP separation.

## How to implement Option B (private crate) with minimal churn

### Step 1: Create private repo
Create a new private repo, e.g. `shimmy-vision-private`.

### Step 2: Move Vision code
Move these modules into the private crate:
- `src/vision.rs`
- `src/vision_license.rs`

The private crate should expose a small API surface, e.g.:
- `pub struct VisionRequest`
- `pub struct VisionResponse`
- `pub struct VisionLicenseManager`
- `pub async fn process_vision_request(...) -> Result<VisionResponse, ...>`

### Step 3: Public shimmy becomes an adapter
In public `shimmy`:
- Replace modules with re-exports when the dep exists:
  - `pub use shimmy_vision::{vision, vision_license};` (or direct items)
- Keep the CLI and `/api/vision` handler calling into the private crate.

### Step 4: Cargo feature wiring
In public `Cargo.toml`:
- `vision = ["dep:shimmy-vision-private"]`
- `shimmy-vision-private = { git = "ssh://git@github.com/<you>/shimmy-vision-private.git", optional = true }`

### Step 5: CI/build pipeline
- Your release CI uses a deploy key to fetch the private repo.
- Public CI runs without `--features vision`.

## What this does (and does not) protect
Protects against:
- trivial “remove license check and rebuild from source” piracy

Does NOT fully protect against:
- binary patching / cracking by motivated attackers

Mitigations (non-obscurity):
- keep license checks inside private module + redundant checks at multiple layers
- watermarking/logging (careful with privacy)
- frequent updates + support value
- trademark enforcement for people distributing “Shimmy Vision” forks

## Next action if you want me to proceed
I can implement Option B in this workspace by:
- creating a new crate boundary in-tree first (as a dry-run)
- replacing `src/vision*.rs` with a thin adapter layer
- updating `Cargo.toml` feature wiring
- verifying `cargo clippy --features llama,vision -- -D warnings` for the private-enabled build and a plain `cargo clippy` for public build

(Then you’d copy the extracted crate into the new private repo and swap the path dep to a git dep.)
