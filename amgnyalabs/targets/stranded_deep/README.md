# Stranded Deep target profile

## Purpose

Stranded Deep is the primary target and acceptance project for this Godot + Unity compatibility engine. Godot remains the main runtime. The Unity compatibility layer exists to recover and map Stranded Deep's Unity project/game data into Godot resources and scenes. This project is not a general Unity clone and does not attempt to execute the Unity runtime.

## Recorded source inventory

The existing inspection notes record:

- 133 OpenScore groups.
- 5 DLL files.
- 3,270 asset entries in the inspected asset set:
  - 1,958 PNG files.
  - 694 Prefab files.
  - 588 Material files.
- Managed `StrandedDeep-OpenScore` and Unity module groups were identified.

These are baseline inventory observations from the prior scan, not proof that all files have been decoded or imported. Re-scan only when the source copy or inventory changes; preserve previous scan outputs and avoid repeating completed checks without a reason.

## Known gameplay and project areas from prior source review

The earlier source review identified scene/tag areas including BOOT, MAIN_MENU, INTRO, LOAD, MAP_EDITOR, WATER, TERRAIN, PLAYER, ANIMAL, SHARK, and RAFT. Unity utility/dependency code (including LeanAudio, MEC, and tweening-related code) must be separated from game-specific behavior during compatibility work. The recorded five DLL files are important evidence for later assembly-backed MonoBehaviour typetree generation; no assembly-backed decode has been validated yet.

These names are discovery clues, not a claim that their full behavior has already been ported.

## Import priorities

1. Build a persistent source inventory and Unity GUID/reference map for Stranded Deep.
2. Decode and retain independently readable Unity serialized objects and resource sidecars; export available MonoBehaviour typetrees as JSON and use the managed DLLs to investigate missing typetrees. Unsupported objects must not discard successful extractions.
3. Import textures and materials first, then meshes and prefab/scene hierarchy.
4. Reconstruct high-value gameplay foundations in Godot: terrain, water, player, then related survival-world objects and systems as evidence permits.
5. Map supported Unity components and script behavior explicitly; preserve unsupported DLLs/scripts as source evidence and report required rewrites.
6. Validate representative imported scenes/resources against the original read-only source.

## Source safety and platform

- Original Stranded Deep source files remain read-only.
- All extraction, conversion, manifests, and generated Godot resources go to a separate output root.
- Android target is Vulkan-only using the Godot Mobile renderer. No DirectX 11 export/rendering/fallback.
- GitHub is the first development environment; Termux is the later local operation/build environment; local Qwen CLI is the constrained operator. Godot APK is for preview and play-testing, not the primary authoring UI.

## Current verified implementation boundary

The repository currently has bounded Unity project discovery, .meta GUID inventory, partial text-YAML object/PPtr inspection, and binary-asset metadata listing. It does not yet decode Unity binary serialized assets, convert Stranded Deep resources, recreate game systems, build the Android APK, or verify runtime compatibility. Do not mark those tasks complete until tests and device validation support the claim.
