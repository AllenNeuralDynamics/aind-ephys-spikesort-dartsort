# aind-ephys-spikesort-template

Template repository to build a custom spike sorting capsule for the AIND ephys pipeline.

---

## Overview

This template provides the boilerplate needed to integrate any
[SpikeInterface](https://spikeinterface.readthedocs.io)-compatible spike sorter into the
AIND CodeOcean ephys pipeline.  All places that need customisation are marked with a
`# TODO` comment so they are easy to find with a text search.

The capsule:
1. Reads preprocessed recordings produced by
   [aind-ephys-preprocessing](https://github.com/AllenNeuralDynamics/aind-ephys-preprocessing).
2. Runs spike sorting with the sorter of your choice.
3. Applies minimal curation (removes empty units and excess spikes).
4. Saves results in SpikeInterface's folder format and writes an
   `aind-data-schema` `DataProcess` JSON for provenance tracking.

For reference implementations see:
- [aind-ephys-spikesort-kilosort4](https://github.com/AllenNeuralDynamics/aind-ephys-spikesort-kilosort4)
- [aind-ephys-spikesort-kilosort25](https://github.com/AllenNeuralDynamics/aind-ephys-spikesort-kilosort25)
- [aind-ephys-spikesort-spykingcircus2](https://github.com/AllenNeuralDynamics/aind-ephys-spikesort-spykingcircus2)

---

## Repository structure

```
aind-ephys-spikesort-template/
├── code/
│   ├── run                  # Bash entry-point called by CodeOcean
│   ├── run_capsule.py       # Main Python script (edit this)
│   └── params.json          # Default sorter parameters (edit this)
├── environment/
│   └── Dockerfile           # Container definition (optional)
└── README.md
```

---

## Steps to use the template

### 1 — Create a new repository from this template

On GitHub, click **"Use this template"** → **"Create a new repository"** and give it a
name following the convention `aind-ephys-spikesort-<sorter_name>`.

### 2 — Update `code/run_capsule.py`

All required edits are tagged `# TODO`:

| Location | What to change |
|---|---|
| `URL` constant | GitHub URL of the new repository |
| `VERSION` constant | Release tag or git commit SHA |
| `SORTER_NAME` constant | Sorter name as used in SpikeInterface (e.g. `"kilosort4"`) |
| `MOTION_CORRECTION_SUPPORTED` constant | Set to `True` if sorter internally supports motion correction
| `MOTION_CORRECTION_PARAM_NAME` constant | If `MOTION_CORRECTION_SUPPORTED`, specify which boolean parameter needs to be set to True to enable motion correction.

### 3 — Provide spike sorter implementation (if not integrated into SpikeInterface)

If the sorter is not integrated into SpikeInterface, you can provide a custom implementation [here](https://github.com/AllenNeuralDynamics/aind-ephys-spikesort-template/blob/main/code/run_capsule.py#L232)
The only requirements are:
1. the input is a [`spikeinterface.BaseRecording`](https://spikeinterface.readthedocs.io/en/stable/api.html#spikeinterface.core.BaseRecording)
2. the output is a [`spikeinterface.BaseSorting`](https://spikeinterface.readthedocs.io/en/stable/api.html#spikeinterface.core.BaseSorting)

### 4 — Populate `code/params.json`

Fill in the `"sorter"` section with all default parameters your sorter accepts.
The `"job_kwargs"` section controls SpikeInterface parallelism and should usually be
left as-is.

Example:

```json
{
    "job_kwargs": {
        "chunk_duration": "1s",
        "progress_bar": false
    },
    "sorter": {
        "detect_threshold": 5,
        "apply_motion_correction": true
    }
}
```


### 5 — Update `environment/Dockerfile` (optional)

Choose a base image (the `# TODO` comment gives examples) and add the pip packages
required by your sorter.  For GPU-based sorters (e.g. Kilosort4) use a CUDA-enabled
CodeOcean base image.  For CPU-only sorters, the plain
`codeocean/mambaforge3` image is a good starting point.


---

## Inputs

The `data/` folder must contain the output of
[aind-ephys-preprocessing](https://github.com/AllenNeuralDynamics/aind-ephys-preprocessing),
i.e. one or more `preprocessed_{recording_name}` sub-folders (and optionally
`binary_{recording_name}.json` / `.pkl` files).

---

## Parameters

The `code/run` script accepts the following arguments:

```
  --raise-if-fails          Raise an error on failure instead of continuing. Default: True
  --skip-motion-correction  Disable sorter motion correction. Default: False
  --min-drift-channels N    Min channels needed to enable motion correction. Default: 64
  --n-jobs N                Parallel jobs (-1 = all cores, 0.x = fraction). Default: -1
  --params PATH_OR_JSON     JSON file path or inline JSON string with full parameter override
```

Sorter-specific parameters are defined in `code/params.json` and can be overridden at
runtime with `--params`.

---

## Outputs

- `results/spikesorted_{recording_name}/` — SpikeInterface sorting folder and sorter log
- `results/data_process_spikesorting_{recording_name}.json` — `DataProcess` provenance
  record ([aind-data-schema](https://aind-data-schema.readthedocs.io/))
