# AmgNya Hybrid Engine Layer

This project combines **Godot as the main engine** with a **Unity compatibility/import layer**. Godot remains the runtime and rendering foundation; Unity project structures, data, assets, scenes, prefabs, references, and supported behaviors are inspected and progressively mapped or converted into Godot-usable resources. This is not a Unity runtime reimplementation. Partial extraction is valuable and must be retained/reported when full conversion is not possible.

## Primary target: Stranded Deep

Stranded Deep is the target game for this engine project. Godot is the main runtime; the Unity compatibility layer exists to inspect, extract, convert, and map Stranded Deep's Unity data into Godot resources/scenes. The current recorded inventory is 133 OpenScore groups, 5 DLL files, and 3,270 asset entries (1,958 PNG, 694 Prefab, 588 Material). These are scan observations, not decoded/imported completion counts. See [the Stranded Deep target profile](targets/stranded_deep/README.md) for known areas, priorities, and verified boundaries.

## Baseline

- Upstream repository: https://github.com/godotengine/godot
- Fork: https://github.com/devmyatmin/godot-remake
- Starting branch: `master`
- Starting commit: `95c0fa5fe8a019adc29d074c16b64469b04571f7`
- Reported engine version at this baseline: Godot 4.8.0 Beta
- Project work branch: `amgnyalabs/bootstrap`

The upstream engine source is not being wholesale rewritten. Project-specific code and documentation belong under `amgnyalabs/` unless a reviewed integration specifically requires a change elsewhere.

## Target workflow

1. Develop and review the engine layer in GitHub.
2. Build Android artifacts in cloud CI (GitHub Actions) so a desktop toolchain is not required on the phone.
3. Download/install the resulting tools and artifacts in Termux.
4. Connect the local Qwen model as an operator through a constrained tool interface.
5. Use the Godot Android app/APK for visual preview and play-testing, not as the primary project authoring interface.

## Hard graphics requirement: Vulkan only

- The Android APK must use the Godot Mobile renderer with Vulkan.
- Vulkan is the only supported graphics backend for this project.
- Do not add DirectX 11 rendering, DirectX 11 export, DX11 dependencies, or DX11 fallback.
- Do not silently fall back to OpenGL/Compatibility rendering when Vulkan is unavailable; report the device as unsupported instead.
- Build/export validation must reject non-Vulkan configurations.

## Unity compatibility integration: best effort, preserve partial results

Accept and inspect as much Unity project information as practical, even when complete conversion is impossible. Start with project structure, Packages, ProjectSettings, .meta GUIDs, text YAML, common resources, scenes/prefabs, and then supported binary serialized assets/bundles. Convert only features with tested mappings. Keep extracted metadata and successfully decoded resources when another part fails, and report unsupported fields clearly.

Original Unity files remain read-only. Converted output belongs in a separate generated-output directory. Unity assemblies, MonoBehaviours, and native plugins are not assumed to run unchanged.

See [ARCHITECTURE.md](ARCHITECTURE.md) and [ROADMAP.md](ROADMAP.md).
