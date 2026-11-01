# AmgNya Engine Layer

This directory contains the project-specific layer built on top of the Godot Engine source tree. The upstream Godot engine remains the runtime and rendering foundation; this project adds a Unity-oriented workflow and automation interface in separate, reviewable steps.

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

## Design boundaries

- Godot remains the engine/runtime; this is not a from-scratch Unity replacement.
- Unity assets and APIs require explicit import/conversion or compatibility work. Unity assemblies and MonoBehaviours are not assumed to run unchanged.
- Qwen proposes and coordinates actions; deterministic tools perform file operations, conversions, builds, and tests.
- Tool permissions must distinguish read-only inspection from writes/builds. No source-game files are modified without explicit authorization.
- The ML-Agents fork is kept separate. It is an optional future game-behavior training component, not the Qwen operator or engine core.

## Initial milestones

- [x] Establish a project branch without changing the upstream `master` branch.
- [ ] Define the engine/operator architecture and permission model.
- [ ] Add a minimal headless project-tool interface.
- [ ] Add reproducible Android build automation after validating SDK/NDK/JDK versions.
- [ ] Add Termux installation and Qwen operator integration.
- [ ] Validate with a small sample project before importing a full game.

See [ARCHITECTURE.md](ARCHITECTURE.md) and [ROADMAP.md](ROADMAP.md).
