# Spike sorting with DARTSort for AIND ephys pipeline
## aind-ephys-spikesort-dartsort


### Description

This capsule is designed to spike sort ephys data using [DARTsort](https://github.com/cwindolf/dartsort/) for the AIND pipeline.

This capsule spike sorts preprocessed ephys stream and applies a minimal curation to:

- remove empty units


### Inputs

The `data/` folder must include the output of the [aind-ephys-preprocessing](https://github.com/AllenNeuralDynamics/aind-ephys-preprocessing), containing 
the `data/preprocessed_{recording_name}` folder.

### Parameters

Parameters are read from a `params.json` file that must be in the root folder of the capsule (next to `code/`, i.e. `../params.json` from `code/`), using the `spikesorting.kilosort4` section (`skip_motion_correction`, `min_drift_channels`, `raise_if_fails`, `n_jobs`, `job_kwargs`, `sorter`, ...) and the optional top-level `logging` section.

A list of spike sorting parameters can be found in the `code/params.json`:

```json
{
    "job_kwargs": {
        "chunk_duration": "1s",
        "progress_bar": false
    },
    "sorter": {
        "do_motion_estimation": true,
        "already_preprocessed": "assume_yes_if_float",
        "preprocessing": "standardize",
        "preprocessing_dtype": "float32",
        "subsampling_spikes_per_channel": 5000,
        "subsampling_presence": 0.025,
        "matching_iterations": 1,
        "dredge_only": false,
        "n_jobs_cpu": 0,
        "n_jobs_gpu": 0,
        "motion_n_jobs_gpu": 2,
        "n_jobs_small": -2,
        "n_jobs_small_gpu": 4,
        "device": null,
        "executor": "threading_unless_multigpu",
        "chunk_length_samples": 30000,
        "work_in_tmpdir": true,
        "copy_recording_to_tmpdir": "no",
        "workdir_copier": "shutil",
        "workdir_follow_symlinks": false,
        "tmpdir_parent": "../scratch",
        "save_intermediates": false,
        "save_final_features": true,
        "ms_before": 1.4,
        "ms_after": 2.6333333333333333,
        "alignment_ms": 1.5,
        "deduplication_ms": 0.25,
        "peak_sign": "both",
        "voltage_threshold": 3.0,
        "matching_threshold": 6.0,
        "initial_threshold": 9.0,
        "motion_voltage_threshold": 4.0,
        "temporal_pca_rank": 8,
        "feature_ms_before": 0.75,
        "feature_ms_after": 1.25,
        "subtraction_radius_um": 200.0,
        "deduplication_radius_um": 50.0,
        "featurization_radius_um": 150.0,
        "fit_radius_um": 75.0,
        "localization_radius_um": 100.0,
        "nn_denoiser_class_name": "Decollider",
        "nn_denoiser_pretrained_path": null,
        "amplitude_scaling_stddev": 0.01,
        "amplitude_scaling_boundary": 0.3333333333333333,
        "temporal_upsamples": 4,
        "postprocessing": "agglomerate_and_clean",
        "rigid": false,
        "probe_boundary_padding_um": 100.0,
        "spatial_bin_length_um": 1.0,
        "temporal_bin_length_s": 1.0,
        "smoothing_um": 3.0,
        "smoothing_s": null,
        "window_step_um": 400.0,
        "window_scale_um": 600.0,
        "window_margin_um": null,
        "max_dt_s": 500.0,
        "max_disp_um": null,
        "correlation_threshold": 0.1,
        "min_amplitude": null,
        "speed_limit_um_per_s": 500.0,
        "max_dist_from_median_um": 250.0,
        "median_neighborhood_bins": 51,
        "motion_batching_mode": "full",
        "motion_chunk_len_s": 3000.0,
        "fit_matching_models_only": false,
        "save_full_final_residual": false
    }
}
```

### Output

The output of this capsule is the following:

- `results/spikesorted_{recording_name}` folder, containing the spike sorted data saved by SpikeInterface and the spike sorting log
- `results/data_process_spikesorting_{recording_name}.json` file, a JSON file containing a `DataProcess` object from the [aind-data-schema](https://aind-data-schema.readthedocs.io/en/stable/) package.

