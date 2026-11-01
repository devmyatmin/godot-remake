# Deployment Model

Last updated: 2026-11-01

## Core rule

GitHub is used to develop, maintain, build, and test the engine. It is not the final runtime or the user's game-work environment.

The finished engine and required runtime/build artifacts are brought from GitHub to the user's Android phone. The phone is the target environment where the engine is run and where Stranded Deep data is inspected, imported, converted, and tested.

## Intended workflow

1. Develop engine source code and compatibility tooling in the GitHub repository.
2. Use GitHub Actions for automated code tests and reproducible build/test jobs where practical.
3. Produce and publish the required build artifacts.
4. Transfer/download the required engine result and dependencies to the Android phone.
5. Run the engine and local Qwen operator through Termux on Android; do not require a persistent GitHub-hosted runtime for normal use.
6. Process the user's Stranded Deep source data locally on the phone, preserving original game files as read-only and writing generated outputs to a separate location.
7. Run the Android APK on the phone for UI/scene preview and gameplay testing. Android target remains Vulkan-only, with no DirectX 11 or silent OpenGL fallback.

## Important distinction

GitHub Actions may be used as a build machine, but it is not the deployed engine runtime. Do not design project operation around a permanently running GitHub service, remote server, or cloud-only asset pipeline. The target is a locally operated Android workflow after the required engine artifacts have been obtained.

## Acceptance requirement

A feature is not considered complete merely because it passes GitHub CI. Where applicable, it must also be packaged, transferred, and validated in the intended Android/Termux environment. Record separately:
- repository/CI verification;
- artifact build and packaging;
- Android installation/runtime verification;
- local Stranded Deep data import and conversion verification.
