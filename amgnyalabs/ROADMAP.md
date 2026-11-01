# Roadmap

## Phase 0 — Baseline and boundaries
- [x] Create isolated development branch `amgnyalabs/bootstrap`.
- [x] Record baseline commit and engine version.
- [x] Document the architecture and permission boundaries.
- [x] Record Vulkan-only as a hard Android runtime/export requirement.
- [x] Define best-effort Unity compatibility and partial-extraction behavior.
- [ ] Confirm the user's preferred project name and public/private visibility before adding branding or changing repository settings.

## Phase 1 — Minimal operator foundation
- [x] Define a versioned JSON request/response schema.
- [x] Implement a local read-only gateway with an allowlist of named tools.
- [x] Add tests for path traversal, symlinks, permission denial, and bounded inspection.
- [x] Connect the local Qwen CLI through a constrained adapter.
- [x] Add a small adapter test suite; malformed model output must never become a shell command.
- [ ] Add resumable task records without granting unrestricted access.

## Phase 2 — Unity compatibility integration into the Godot main engine
- [x] Build a Unity project detector for Assets, Packages, ProjectSettings, and ProjectVersion.
- [x] Inventory .meta GUIDs and extract bounded text-YAML object IDs / PPtr references (partial parser; not full YAML conversion).
- [x] Expose an initial per-feature Unity compatibility support matrix.
- [ ] Create a persistent Unity-to-Godot extraction manifest with incremental re-import support.
- [x] Add metadata-only inspection for serialized assets and bundles before conversion.
- [ ] Resolve GUID references across complete project scans and persist source-to-Godot resource mappings.
- [ ] Add texture and audio conversion fixtures.
- [ ] Add mesh, material, shader, animation, and font importers incrementally.
- [ ] Map supported GameObject/Transform/Component hierarchies, Scenes, and Prefabs.
- [ ] Add limited, tested Unity C# API translation; retain unsupported scripts and assemblies unchanged.
- [ ] Preserve partial extraction results and report unsupported fields/references.
- [ ] Keep original Unity data read-only; all converted files go to generated output.

## Phase 3 — Vulkan-only Android build pipeline
- [ ] Select and pin supported Android SDK, NDK, JDK, SCons, and Python versions.
- [ ] Configure the Android project profile for Godot Mobile renderer + Vulkan.
- [ ] Add a validation gate that rejects non-Vulkan renderer/driver settings.
- [ ] Ensure no DirectX 11 renderer, export target, dependency, or fallback is added.
- [ ] Do not silently fall back to OpenGL/Compatibility if Vulkan is unavailable.
- [ ] Add GitHub Actions workflow for reproducible Vulkan-enabled Android builds.
- [ ] Upload build artifacts and build logs.
- [ ] Install and test artifacts on the Android device through Termux; record Vulkan device/driver information.

## Phase 4 — Engine tools and scene automation
- [ ] Add one asset importer at a time, starting with a small representative sample.
- [ ] Add structured scene creation and validation.
- [ ] Add deterministic import/build/test profiles exposed through the gateway.
- [ ] Require explicit approval for project writes, destructive changes, or external actions.

## Phase 5 — Validation and optional ML
- [ ] Validate with a small clean Unity sample project.
- [ ] Validate partial extraction from at least one binary Unity asset fixture.
- [ ] Compare imported hierarchy/resources against source metadata.
- [ ] Measure APK startup, rendering, memory, and runtime behavior on the target Android device.
- [ ] Consider ML-Agents only if a concrete game-behavior training requirement emerges and a compatible environment bridge is available.

## Not in the initial scope
- Rewriting the entire Godot engine.
- Claiming full Unity runtime or binary compatibility.
- Assuming Unity DLLs or MonoBehaviours run unchanged.
- Adding DirectX 11, DX11 export, or non-Vulkan fallback paths to this project.
- Merging ML-Agents into the Qwen operator.
- Modifying original game files in place.
- Requiring full source builds on the Android phone for normal iteration.
