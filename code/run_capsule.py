import warnings

warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", category=DeprecationWarning)

# GENERAL IMPORTS
import os
import sys
import argparse
import numpy as np
from pathlib import Path
import shutil
import json
import time
from pprint import pprint
import logging
from datetime import datetime, timedelta

# SPIKEINTERFACE
import spikeinterface as si
import spikeinterface.preprocessing as spre
import spikeinterface.sorters as ss
import spikeinterface.curation as sc
from spikeinterface.sortingcomponents.motion import InterpolateMotionRecording

from dartsort import dartsort, DARTsortUserConfig, DeveloperConfig
from dartsort import __version__ as dartsort_version
from pydantic import TypeAdapter

# AIND
from aind_data_schema.core.processing import DataProcess, ProcessStage
from aind_data_schema.components.identifiers import Code
from aind_data_schema_models.process_names import ProcessName

try:
    from aind_log_utils import log
    HAVE_AIND_LOG_UTILS = True
except ImportError:
    HAVE_AIND_LOG_UTILS = False

# TODO: update with the actual URL and version of the capsule
URL = "https://github.com/cwindolf/dartsort"
VERSION = "1.0"

# TODO: replace with the actual sorter name
SORTER_NAME = "DARTSort"
MOTION_CORRECTION_SUPPORTED = True  # set to True if the sorter supports motion correction
MOTION_CORRECTION_PARAM_NAME = "do_motion_estimation"  # set to the actual parameter name used by the sorter to enable/disable motion correction

COPY_DARTSORT_OUTPUT_TO_RESULTS = True

data_folder = Path("../data")
results_folder = Path("../results")
scratch_folder = Path("../scratch")

# Define argument parser
parser = argparse.ArgumentParser(description=f"Spike sort ecephys data with {SORTER_NAME}")

raise_if_fails_group = parser.add_mutually_exclusive_group()
raise_if_fails_help = "Whether to raise an error in case of failure or continue. Default True (raise)"
raise_if_fails_group.add_argument("--raise-if-fails", action="store_true", help=raise_if_fails_help)
raise_if_fails_group.add_argument("static_raise_if_fails", nargs="?", default="true", help=raise_if_fails_help)

skip_motion_correction_group = parser.add_mutually_exclusive_group()
skip_motion_correction_help = f"Whether to skip {SORTER_NAME} motion correction. Default: False"
skip_motion_correction_group.add_argument("--skip-motion-correction", action="store_true", help=skip_motion_correction_help)
skip_motion_correction_group.add_argument("static_skip_motion_correction", nargs="?", help=skip_motion_correction_help)

min_drift_channels_group = parser.add_mutually_exclusive_group()
min_drift_channels_help = f"Minimum number of channels to enable {SORTER_NAME} motion correction. Default is 64."
min_drift_channels_group.add_argument("static_min_channels_for_drift", nargs="?", help=min_drift_channels_help)
min_drift_channels_group.add_argument("--min-drift-channels", default="64", help=min_drift_channels_help)

use_preprocessing_motion_group = parser.add_mutually_exclusive_group()
use_preprocessing_motion_help = f"Whether to use motion from preprocessing. Default: True"
use_preprocessing_motion_group.add_argument("--do-not-use-preprocessing-motion", action="store_true", help=use_preprocessing_motion_help)
use_preprocessing_motion_group.add_argument("static_use_preprocessing_motion", nargs="?", help=use_preprocessing_motion_help)

matching_threshold_group = parser.add_mutually_exclusive_group()
matching_threshold_group.add_argument("--matching-threshold", default="8", help="")
matching_threshold_group.add_argument("static_matching_threshold", nargs="?", help="")

initial_threshold_group = parser.add_mutually_exclusive_group()
initial_threshold_group.add_argument("--initial-threshold", default="9", help="")
initial_threshold_group.add_argument("static_initial_threshold", nargs="?", help="")

subsampling_presence_group = parser.add_mutually_exclusive_group()
subsampling_presence_group.add_argument("--subsampling-presence", default="0.1", help="")
subsampling_presence_group.add_argument("static_subsampling_presence", nargs="?", help="")

whiten_temporal_length_group = parser.add_mutually_exclusive_group()
whiten_temporal_length_group.add_argument("--whiten-temporal-length", default="3", help="")
whiten_temporal_length_group.add_argument("static_whiten_temporal_length", nargs="?", help="")

si_merge_preset_group = parser.add_mutually_exclusive_group()
si_merge_preset_group.add_argument("--si-merge-preset", default="dartsort_slay_xc_ccg", help="")
si_merge_preset_group.add_argument("static_si_merge_preset", nargs="?", help="")

n_jobs_group = parser.add_mutually_exclusive_group()
n_jobs_help = (
    "Number of jobs to use for parallel processing. Default is -1 (all available cores). "
    "It can also be a float between 0 and 1 to use a fraction of available cores"
)
n_jobs_group.add_argument("static_n_jobs", nargs="?", default="-1", help=n_jobs_help)
n_jobs_group.add_argument("--n-jobs", default="-1", help=n_jobs_help)

parser.add_argument("--params", default=None, help="Path to the parameters file or JSON string. If given, it will override all other arguments.")


if __name__ == "__main__":
    args = parser.parse_args()

    PARAMS = args.params

    if PARAMS is not None:
        try:
            # try to parse the JSON string first to avoid file name too long error
            spikesorting_params = json.loads(PARAMS)
        except json.JSONDecodeError:
            if Path(PARAMS).is_file():
                with open(PARAMS, "r") as f:
                    spikesorting_params = json.load(f)
            else:
                raise ValueError(f"Invalid parameters: {PARAMS} is not a valid JSON string or file path")
        SKIP_MOTION_CORRECTION = spikesorting_params.pop("skip_motion_correction", False)
        MIN_DRIFT_CHANNELS = spikesorting_params.pop("min_drift_channels", 64)
        RAISE_IF_FAILS = spikesorting_params.pop("raise_if_fails", True)
        USE_PREPROCESSING_MOTION = spikesorting_params.pop("use_preprocessing_motion", True)
        MATCHING_THRESHOLD = spikesorting_params.pop("matching_threshold", 8.)
        INITIAL_THRESHOLD = spikesorting_params.pop("initial_threshold", 9.)
        SUBSAMPLING_PRESENCE = spikesorting_params.pop("subsampling_presence", 0.1)
        WHITEN_TEMPORAL_LENGTH = spikesorting_params.pop("whiten_temporal_length", 3)
        SI_MERGE_PRESET = spikesorting_params.pop("si_merge_preset", "dartsort_slay_xc_ccg")
    else:
        SKIP_MOTION_CORRECTION = True if args.static_skip_motion_correction and args.static_skip_motion_correction.lower() == "true" else args.skip_motion_correction
        MIN_DRIFT_CHANNELS = args.static_min_channels_for_drift or args.min_drift_channels
        MIN_DRIFT_CHANNELS = int(MIN_DRIFT_CHANNELS)
        RAISE_IF_FAILS = True if args.static_raise_if_fails and args.static_raise_if_fails.lower() == "true" else args.raise_if_fails
        USE_PREPROCESSING_MOTION = True if args.static_use_preprocessing_motion and args.static_use_preprocessing_motion.lower() == "true" else not args.do_not_use_preprocessing_motion
        MATCHING_THRESHOLD = args.static_matching_threshold or args.matching_threshold
        MATCHING_THRESHOLD = float(MATCHING_THRESHOLD)
        INITIAL_THRESHOLD = args.static_initial_threshold or args.initial_threshold
        INITIAL_THRESHOLD = float(INITIAL_THRESHOLD)
        SUBSAMPLING_PRESENCE = args.static_subsampling_presence or args.subsampling_presence
        SUBSAMPLING_PRESENCE = float(SUBSAMPLING_PRESENCE)
        WHITEN_TEMPORAL_LENGTH = args.static_whiten_temporal_length or args.whiten_temporal_length
        WHITEN_TEMPORAL_LENGTH = int(WHITEN_TEMPORAL_LENGTH)
        SI_MERGE_PRESET = args.static_si_merge_preset or args.si_merge_preset

        # read default parameters from JSON file
        default_params_file = Path(__file__).parent / "params.json"
        if default_params_file.is_file():
            with open(default_params_file, "r") as f:
                spikesorting_params = json.load(f)

    N_JOBS = args.static_n_jobs or args.n_jobs
    N_JOBS = int(N_JOBS) if not N_JOBS.startswith("0.") else float(N_JOBS)

    # Use CO_CPUS/N_JOBS_EXT env variable if available
    N_JOBS_EXT = os.getenv("CO_CPUS") or os.getenv("N_JOBS_EXT")
    N_JOBS = int(N_JOBS_EXT) if N_JOBS_EXT is not None else N_JOBS

    # look for subject and data_description JSON files
    subject_id = "undefined"
    session_name = "undefined"
    for f in data_folder.iterdir():
        # the file name is {recording_name}_subject.json
        if "subject.json" in f.name:
            with open(f, "r") as file:
                subject_id = json.load(file)["subject_id"]
        # the file name is {recording_name}_data_description.json
        if "data_description.json" in f.name:
            with open(f, "r") as file:
                session_name = json.load(file)["name"]

    if HAVE_AIND_LOG_UTILS:
        log.setup_logging(
            f"Spikesort {SORTER_NAME} Ecephys",
            subject_id=subject_id,
            asset_name=session_name,
        )
    else:
        logging.basicConfig(level=15, stream=sys.stdout, format="%(message)s")

    data_process_prefix = "data_process_spikesorting"

    job_kwargs = spikesorting_params.pop("job_kwargs")
    job_kwargs["n_jobs"] = N_JOBS
    si.set_global_job_kwargs(**job_kwargs)

    sorter_params = spikesorting_params["sorter"]

    ####### SPIKESORTING ########
    logging.info(f"\n\nSPIKE SORTING WITH {SORTER_NAME.upper()}\n")

    logging.info(f"\tRAISE_IF_FAILS: {RAISE_IF_FAILS}")
    logging.info(f"\tSKIP_MOTION_CORRECTION: {SKIP_MOTION_CORRECTION}")
    logging.info(f"\tMIN_DRIFT_CHANNELS: {MIN_DRIFT_CHANNELS}")
    logging.info(f"\tUSE_PREPROCESSING_MOTION: {USE_PREPROCESSING_MOTION}")
    logging.info(f"\tMATCHING_THRESHOLD: {MATCHING_THRESHOLD}")
    logging.info(f"\tINITIAL_THRESHOLD: {INITIAL_THRESHOLD}")
    logging.info(f"\tSUBSAMPLING_PRESENCE: {SUBSAMPLING_PRESENCE}")
    logging.info(f"\tWHITEN_TEMPORAL_LENGTH: {WHITEN_TEMPORAL_LENGTH}")
    logging.info(f"\tSI_MERGE_PRESET: {SI_MERGE_PRESET}")
    logging.info(f"\tN_JOBS: {N_JOBS}")

    assert 0 < SUBSAMPLING_PRESENCE < 1, f"Subsampling presence must be between 0 and 1 (excluded): {SUBSAMPLING_PRESENCE} is invalid"

    sorting_params = None

    si.set_global_job_kwargs(**job_kwargs)
    t_sorting_start_all = time.perf_counter()

    # check if test
    if (data_folder / "preprocessing_pipeline_output_test").is_dir():
        logging.info("\n*******************\n**** TEST MODE ****\n*******************\n")
        preprocessed_folder = data_folder / "preprocessing_pipeline_output_test"
    else:
        preprocessed_folder = data_folder

    spikesorting_data_processes = []
    preprocessed_folders = [p for p in preprocessed_folder.iterdir() if p.is_dir() and "preprocessed_" in p.name]
    for recording_folder in preprocessed_folders:
        datetime_start_sorting = datetime.now()
        t_sorting_start = time.perf_counter()
        spikesorting_notes = ""

        recording_name = ("_").join(recording_folder.name.split("_")[1:])
        binary_json_file = preprocessed_folder / f"binary_{recording_name}.json"
        binary_pickle_file = preprocessed_folder / f"binary_{recording_name}.pkl"
        sorting_output_folder = results_folder / f"spikesorted_{recording_name}"
        sorting_output_process_json = results_folder / f"{data_process_prefix}_{recording_name}.json"

            # try results here
        if COPY_DARTSORT_OUTPUT_TO_RESULTS:
            spikesorted_raw_output_folder = results_folder / f"dartsort_{recording_name}"
        else:
            spikesorted_raw_output_folder = scratch_folder / "spikesorted_raw"

        logging.info(f"Sorting recording: {recording_name}")
        try:
            if binary_json_file.is_file():
                logging.info(f"Loading recording from binary JSON")
                recording = si.load(binary_json_file, base_folder=preprocessed_folder)
            elif binary_pickle_file.is_file():
                logging.info(f"Loading recording from binary PKL")
                recording = si.load(binary_pickle_file, base_folder=preprocessed_folder)
            else:
                recording = si.load(recording_folder)
            logging.info(recording)
        except Exception as e:
            logging.info(f"Skipping spike sorting for {recording_name}.")
            # create an empty result file (needed for pipeline)
            sorting_output_folder.mkdir(parents=True, exist_ok=True)
            error_file = sorting_output_folder / "error.txt"
            error_file.write_text("Too many bad channels")
            continue

        # concatenate segments if needed (required by some sorters)
        split_segments = False
        if recording.get_num_segments() > 1:
            logging.info("Concatenating multi-segment recording")
            recording = si.concatenate_recordings([recording])
            split_segments = True

        si_motion = None
        if MOTION_CORRECTION_SUPPORTED:
            if recording.get_num_channels() < MIN_DRIFT_CHANNELS:
                logging.info("Drift correction not enabled due to low number of channels")
                sorter_params[MOTION_CORRECTION_PARAM_NAME] = False

            if SKIP_MOTION_CORRECTION:
                logging.info("Drift correction disabled")
                sorter_params[MOTION_CORRECTION_PARAM_NAME] = False

            if not SKIP_MOTION_CORRECTION and USE_PREPROCESSING_MOTION:
                motion_folder = preprocessed_folder / f"motion_{recording_name}"
                if motion_folder.is_dir():
                    motion_info = spre.load_motion_info(motion_folder)
                    si_motion = motion_info["motion"]
                    logging.info(f"Using SI motion: {si_motion}")

                    # If motion correction was applied, retrieve pre-interpolation recording.
                    # This is done since DartSort makes use of motion without interpolating the traces
                    if isinstance(recording, InterpolateMotionRecording):
                        logging.info("Undoing motion interpolation!")
                        recording = recording.get_parent()

        sorter_params["n_jobs_small"] = N_JOBS - 2

        sorter_params["matching_threshold"] = MATCHING_THRESHOLD
        sorter_params["initial_threshold"] = INITIAL_THRESHOLD
        sorter_params["subsampling_presence"] = SUBSAMPLING_PRESENCE
        sorter_params["whiten_temporal_length"] = WHITEN_TEMPORAL_LENGTH
        sorter_params["spikeinterface_merge_preset"] = SI_MERGE_PRESET

        # run sorter
        try:
            # cfg = DARTsortUserConfig(**sorter_params)
            # dartsort_params = TypeAdapter(DARTsortUserConfig).dump_python(cfg)
            # Use Dev config to play around with params for now
            cfg = DeveloperConfig(**sorter_params)
            dartsort_params = TypeAdapter(DeveloperConfig).dump_python(cfg)
            logging.info(f"DartSort CFG:\n{dartsort_params}")
            spikesorted_raw_output_folder.mkdir(exist_ok=True)
            t_start_dartsort = time.perf_counter()
            results_dartsort = dartsort(recording, output_dir=spikesorted_raw_output_folder / recording_name, cfg=cfg, si_motion=si_motion)
            sorting = results_dartsort["sorting"].to_numpy_sorting()
            t_stop_dartsort = time.perf_counter()

            # Save spikeinterface log
            log = dict(
                sorter_name="dartsort",
                sorter_version=dartsort_version,
                run_time=t_stop_dartsort - t_start_dartsort
            )
            with open(spikesorted_raw_output_folder / recording_name / "spikeinterface_log.json", "w") as f:
                json.dump(log, f)
            
            logging.info(f"\tRaw sorting output: {sorting}")
            n_original_units = int(len(sorting.unit_ids))
            spikesorting_notes += f"\n- {SORTER_NAME} found {n_original_units} units, "
            if sorting_params is None:
                sorting_params = dartsort_params

            # remove empty units
            sorting = sorting.remove_empty_units()
            # remove spikes beyond num_samples (if any)
            sorting = sc.remove_excess_spikes(sorting=sorting, recording=recording)
            n_non_empty_units = int(len(sorting.unit_ids))
            n_empty_units = n_original_units - n_non_empty_units
            # save params in output
            sorting_outputs = dict(empty_units=n_empty_units)
            logging.info(f"\tSorting output without empty units: {sorting}")
            spikesorting_notes += f"{len(sorting.unit_ids)} after removing empty templates.\n"

            # split back to get original segments
            if split_segments:
                logging.info("Splitting sorting into multiple segments")
                sorting = si.split_sorting(sorting, recording)

            # save results
            logging.info(f"\tSaving results to {sorting_output_folder}")
            sorting = sorting.save(folder=sorting_output_folder)
            if (spikesorted_raw_output_folder / recording_name / "spikeinterface_log.json").is_file():
                shutil.copy(
                    spikesorted_raw_output_folder / recording_name / "spikeinterface_log.json", sorting_output_folder
                )

            # safe delete the output folder
            try:
                shutil.rmtree(spikesorted_raw_output_folder / recording_name)
            except Exception as e:
                logging.info(f"\tError deleting sorter output folder: {e}")
        except Exception as e:
            logging.info("\n\tSPIKE SORTING FAILED!")
            log_file = spikesorted_raw_output_folder / recording_name / "spikeinterface_log.json"
            if log_file.is_file():
                with open(log_file, "r") as f:
                    spike_sorter_log = json.load(f)
                logging.info("Error log:\n")
                pprint(spike_sorter_log)
            else:
                logging.info(f"Error log:\n{e}")
            if RAISE_IF_FAILS:
                raise Exception(e)
            else:
                # save log to results
                (sorting_output_folder).mkdir(parents=True, exist_ok=True)
                if log_file.is_file():
                    shutil.copy(log_file, sorting_output_folder)
                sorting_outputs = dict()
                sorting_params = dict()

        t_sorting_end = time.perf_counter()
        elapsed_time_sorting = np.round(t_sorting_end - t_sorting_start, 2)

        spikesorting_process = DataProcess(
            process_type=ProcessName.SPIKE_SORTING,
            stage=ProcessStage.PROCESSING,
            name="Spike sorting",
            experimenters=["Unknown"],
            code=Code(
                url=URL,
                version=VERSION,  # either release or git commit
                parameters=sorting_params
            ),
            start_date_time=datetime_start_sorting,
            end_date_time=datetime_start_sorting + timedelta(seconds=np.floor(elapsed_time_sorting)),
            output_path=str(results_folder),
            output_parameters=sorting_outputs,
            notes=spikesorting_notes,
        )
        with open(sorting_output_process_json, "w") as f:
            f.write(spikesorting_process.model_dump_json(indent=3))

    t_sorting_end_all = time.perf_counter()
    elapsed_time_sorting_all = np.round(t_sorting_end_all - t_sorting_start_all, 2)
    logging.info(f"SPIKE SORTING time: {elapsed_time_sorting_all}s")
