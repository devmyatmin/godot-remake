# Project Status

Last updated: 2026-11-01

## Project direction

- Primary target: Stranded Deep.
- Godot 4.8.0 Beta is the main engine baseline.
- Unity compatibility is an import, inspection, conversion, and reconstruction layer inside the Godot-based engine; Unity is not a replacement main engine.
- Android target is Vulkan-only. No DirectX 11, OpenGL fallback, or silent renderer fallback.
- Original Unity game data remains read-only. Generated files belong in a separate output root.
- Development is GitHub-first, with Termux/Android as the later local operating environment and local Qwen as a constrained AI operator.

## Verified implementation

- Read-only Unity project inspection and metadata/reference inventory.
- Read-only JSONL operator gateway with a named-tool allowlist.
- Local Qwen CLI adapter; model output is validated and is never executed as shell code.
- Standalone UnityPy 1.25.4 first-stage binary extractor for Texture2D/Sprite, Mesh, AudioClip, Font, TextAsset, and MonoBehaviour typetrees when available.
- Per-object partial-failure reporting and exclusive-create output behavior.

## Latest CI verification

- Workflow: AmgNya Operator Tests
- Run: [41310916274](https://github.com/devmyatmin/godot-remake/actions/runs/41310916274)
- Branch: amgnyalabs/bootstrap
- Tested commit: 90bc98197805e44b1eb05a211961a6cd444d99fd
- Result: success on Python 3.10, 3.11, and 3.12.
- Each matrix job completed the Unity binary importer tests, gateway security tests, and Qwen adapter validation tests.

This CI run uses mocked UnityPy objects. It does not prove successful import of original Stranded Deep binary files.

## Not yet verified or implemented

- No representative original Stranded Deep serialized asset and sidecar acceptance test has passed yet.
- The five recorded game DLLs have not yet been validated as inputs for generating missing MonoBehaviour typetrees.
- The standalone binary importer is not exposed through the Qwen gateway.
- Material/shader conversion, scene/prefab reconstruction, gameplay behavior translation, and complete source-to-Godot resource mapping remain incomplete.
- Vulkan-only Android export/runtime enforcement and device testing remain unimplemented.

## Next engineering step

Design and implement a persistent Stranded Deep import manifest with source hashes, per-object outcomes, generated-output references, and safe incremental re-import. Keep the original source read-only and do not overwrite existing generated files. After that, integrate extraction into the gateway only through a configured generated-output root and a dedicated write_generated permission path; never add arbitrary shell or unrestricted write access.
