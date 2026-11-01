# Architecture

## 1. Layers

```text
Local Qwen (planner / operator brain)
          |
          v
Operator Gateway (structured requests + policy checks)
          |
          v
Engine Tools (inspect, import, convert, scene, build, test)
          |
          v
Godot 4.8 baseline + AmgNya project modules
          |
          v
Android APK (Vulkan-only runtime / preview / play-test)
```

### Godot core
Godot supplies scene/runtime, rendering, resources, platform support, and the Android export/build foundation. Keep upstream changes small and isolated.

### AmgNya project layer
Project-specific adapters, importers, automation tools, and compatibility code live under `amgnyalabs/` first. Promote code into Godot core only when there is a concrete technical reason and a reviewable patch.

### Operator gateway
Qwen must not receive unrestricted shell or filesystem access. It emits structured tool requests. The gateway validates:
- allowed operation name;
- canonical workspace root and path containment;
- read/write permission for the operation;
- file type and size limits;
- explicit approval for destructive or external-source writes;
- operation result and logs.

Inspection is read-only by default. Conversion/build output goes to a separate generated-output directory; original game data stays untouched.

## 2. Rendering and Android target: Vulkan only

This is a hard project requirement, not a preference or optional fallback.

- Android APK runtime must use the Godot Mobile renderer with the Vulkan rendering driver.
- Vulkan is the only supported graphics backend for project builds and exported APKs.
- Do not add a DirectX 11 renderer, DirectX 11 export target, DX11 dependency, or DX11 fallback path.
- Do not silently fall back to OpenGL/Compatibility rendering when Vulkan is unavailable. Report a clear unsupported-device error instead.
- Android build/export profiles must validate the selected renderer and reject a non-Vulkan configuration.
- Device validation must check Vulkan availability and report the Vulkan/GPU/driver details before runtime testing.

Godot's upstream source may contain renderers and platform code outside this project's target. Do not modify or remove unrelated upstream capabilities merely to enforce this product rule; enforce Vulkan-only in AmgNya project configuration, build profiles, validation, and APK acceptance tests.

## 3. Initial tool contract

The first tool interface should be small and deterministic:

| Tool | Purpose | Default permission |
|---|---|---|
| `inspect_project` | Inventory project structure and metadata | Read-only |
| `inspect_asset` | Read supported asset metadata | Read-only |
| `search_assets` | Find assets by type/name/reference | Read-only |
| `convert_asset` | Convert one approved asset to a chosen format | Write generated output |
| `create_scene` | Generate a scene from validated structured input | Write project workspace |
| `validate_project` | Run import/parse checks | Read + generated cache |
| `build_android` | Build a Vulkan-only Android target | Write build output |
| `run_test` | Launch a defined test and collect logs | Controlled execution |

Every request and result should be logged with tool name, arguments, status, and output paths. Do not implement arbitrary command execution as a general-purpose tool.

## 4. Best-effort Unity compatibility

Goal: accept, inspect, preserve, and convert as much useful Unity project information as can be handled safely. Full Unity runtime or binary compatibility is not promised. Partial extraction is still useful: retain every successfully decoded field/resource, record its source and confidence, and report unsupported portions instead of discarding the whole asset.

### Compatibility stages

1. **Project discovery:** recognize Unity project folders, `Assets/`, `Packages/manifest.json`, `Packages/packages-lock.json`, `ProjectSettings/`, `ProjectVersion.txt`, and build/platform metadata.
2. **Identity and serialization:** parse `.meta` GUIDs, references, text-serialized Unity YAML, object IDs, GameObject/Transform/Component relationships, and supported serialized properties.
3. **Common resources:** inspect and convert textures, sprites, meshes, materials, shaders, audio clips, fonts, animations, and supported video/image resources.
4. **Scene and prefab mapping:** map supported GameObject hierarchies, Transform data, Prefabs, Scenes, components, and references into Godot scenes/resources.
5. **Scripting compatibility:** inventory C# scripts and assemblies; translate only explicitly supported Unity API patterns into documented Godot equivalents. Preserve original scripts as source; do not claim that Unity DLLs, MonoBehaviours, native plugins, or assemblies execute unchanged.
6. **Binary asset recovery:** attempt supported parsers for Unity serialized files, AssetBundles, and resource sidecars. Extract independently decodable objects even if other objects fail. Record parser/version limits and unresolved references.
7. **Validation:** compare source and converted metadata, resource counts, references, dimensions, mesh/material properties, and scene hierarchy on representative fixtures.

### Importer behavior and support reporting

- Use a per-format/per-feature support matrix: `supported`, `partial`, `metadata-only`, or `unsupported`.
- Prefer loss-minimizing extraction. Keep unknown fields and raw payloads where practical for future converters.
- Never overwrite source Unity files. Write conversions beneath a separate generated-output root.
- Report each successful extraction and each skipped/failed field with a reason.
- Preserve Unity GUID/reference mapping in a manifest so partially imported projects can be repaired incrementally.
- Add fixtures from real Unity versions and test each parser before widening support.

Unity C# assemblies, native plugins, and MonoBehaviours are not assumed to be binary-compatible with Godot. Each supported feature needs an explicit adapter or a documented unsupported status.

## 5. Build and device workflow

- Use GitHub Actions for reproducible Android builds once supported toolchain versions are confirmed.
- Keep SDK, NDK, JDK, SCons, and Python versions pinned in CI.
- Build only the Vulkan-enabled Android target for this project; fail validation if a non-Vulkan renderer or fallback is selected.
- Publish build artifacts from CI; install/test them on the Android device through Termux.
- Use the Godot Android app/APK for preview and play-testing.
- Avoid requiring a full Godot source build on the phone for every iteration.

## 6. ML-Agents boundary

The separate ML-Agents repository is not part of the engine core or Qwen gateway. Consider it only if a later requirement needs reinforcement/imitation learning and a suitable Unity-compatible training environment or custom bridge exists.
