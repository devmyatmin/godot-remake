# Unity compatibility tools

## Read-only project inspection

`project_inspector.py` inventories Unity project markers, package dependencies, `.meta` GUIDs, bounded text-YAML object IDs/PPtr references, and binary asset metadata. It does not decode binary serialized objects.

## Initial binary extraction

`unity_binary_importer.py` uses the pinned UnityPy dependency to process one serialized Unity file or AssetBundle at a time. It independently attempts to export Texture2D/Sprite as PNG, Mesh as OBJ, AudioClip samples as WAV, Font data, and TextAsset payloads. Other object types are retained in the report as metadata-only; per-object errors are recorded while other objects continue.

Install the pinned dependency:

```sh
python -m pip install -r amgnyalabs/unity_compat/requirements.txt
```

Run against one copied Unity data file, directing output outside the original source directory:

```sh
python amgnyals/unity_compat/unity_binary_importer.py \
  --source /absolute/path/to/StrandedDeep_Data/sharedassets0.assets \
  --output /absolute/path/to/generated/strandeddeep/sharedassets0
```

Use a fresh output directory for each run. The importer refuses to place output inside the original source directory and opens exported files with exclusive-create semantics rather than overwriting existing outputs. Keep related `.resS`/`.resource` sidecars beside the source file so UnityPy can resolve external payloads where supported.

This is a first extraction stage, not a complete Unity-to-Godot converter. It does not yet convert Materials/Shaders, rebuild Prefabs/Scenes, translate MonoBehaviours, or prove gameplay equivalence. Real Stranded Deep binary files must be used as acceptance fixtures before claiming game-specific compatibility.
