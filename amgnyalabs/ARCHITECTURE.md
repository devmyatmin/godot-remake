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
Godot Engine 4.8 baseline + project-specific modules
          |
          v
Android build / runtime / preview APK
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

## 2. Initial tool contract

The first tool interface should be small and deterministic:

| Tool | Purpose | Default permission |
|---|---|---|
| `inspect_project` | Inventory project structure and metadata | Read-only |
| `inspect_asset` | Read supported asset metadata | Read-only |
| `search_assets` | Find assets by type/name/reference | Read-only |
| `convert_asset` | Convert one approved asset to a chosen format | Write generated output |
| `create_scene` | Generate a scene from validated structured input | Write project workspace |
| `validate_project` | Run import/parse checks | Read + generated cache |
| `build_android` | Build an Android target | Write build output |
| `run_test` | Launch a defined test and collect logs | Controlled execution |

Every request and result should be logged with tool name, arguments, status, and output paths. Do not implement arbitrary command execution as a general-purpose tool.

## 3. Unity-oriented compatibility

Implement compatibility incrementally, based on real sample projects and tests:

1. Asset inventory and metadata mapping.
2. Texture, mesh, material, and audio import/conversion adapters.
3. Scene hierarchy mapping (GameObject / Transform / Component concepts).
4. Prefab and serialized-property mapping.
5. Selected Unity API shims where behavior can be tested.

Unity C# assemblies, native plugins, and MonoBehaviours are not assumed to be binary-compatible with Godot. Each supported feature needs an explicit adapter or a documented unsupported status.

## 4. Build and device workflow

- Use GitHub Actions for reproducible Android builds once supported toolchain versions are confirmed.
- Keep SDK, NDK, JDK, SCons, and Python versions pinned in CI.
- Publish build artifacts from CI; install/test them on the Android device through Termux.
- Use the Godot Android app/APK for preview and play-testing.
- Avoid requiring a full Godot source build on the phone for every iteration.

## 5. ML-Agents boundary

The separate ML-Agents repository is not part of the engine core or Qwen gateway. Consider it only if a later requirement needs reinforcement/imitation learning and a suitable Unity-compatible training environment or custom bridge exists.
