import csv
import pathlib
from pathlib import Path
from datetime import datetime
from element_interface.utils import find_full_path, ingest_csv_to_table
from workflow_calcium_imaging.pipeline import (
    subject,
    scan,
    session,
    Equipment,
    trial,
    event,
)
from workflow_calcium_imaging.paths import get_imaging_root_data_dir


def ingest_subjects(
    subject_csv_path:str="./user_data/subjects.csv", skip_duplicates:bool=True, verbose:bool=True
):
    """Inserts ./user_data/subject.csv data into corresponding subject schema tables.

    Args:
        subject_csv_path (str): relative path of subject csv.
        skip_duplicates (bool): Default True. Passed to DataJoint insert.
        verbose (bool): Display number of entries inserted when ingesting.
    """
    csvs = [subject_csv_path]
    tables = [subject.Subject()]

    ingest_csv_to_table(csvs, tables, skip_duplicates=skip_duplicates, verbose=verbose)


def ingest_sessions(
    session_csv_path="./user_data/sessions.csv", skip_duplicates=True, verbose=True
):
    """Ingests all the manual table starting from session schema from
    ./user_data/sessions.csv.

    Args:
        session_csv_path (str): relative path of session csv.
        skip_duplicates (bool): Default True. Passed to DataJoint insert.
        verbose (bool): Default True. Display number of entries inserted when ingesting.
    """

    root_data_dir = get_imaging_root_data_dir()

    # ---------- Insert new "Session" and "Scan" ---------
    with open(session_csv_path, newline="") as f:
        input_sessions = list(csv.DictReader(f, delimiter=","))

    # Folder structure: root / subject / session / .tif (raw)
    session_list, session_dir_list, scan_list, scanner_list = [], [], [], []

    for sess in input_sessions:
        sess_dir = find_full_path(root_data_dir, Path(sess["session_dir"]))

        # search for either ScanImage or Scanbox files (in that order)
        for scan_pattern, scan_type, glob_func in zip(
            ["*.tif", "*.sbx"],
            ["ScanImage", "Scanbox"],
            [sess_dir.glob, sess_dir.rglob],
        ):
            scan_filepaths = [fp.as_posix() for fp in glob_func(scan_pattern)]
            if len(scan_filepaths):
                acq_software = scan_type
                break
        else:
            raise FileNotFoundError(
                "Unable to identify scan files from the supported "
                + "acquisition softwares (ScanImage, Scanbox) at: "
                + f"{sess_dir}"
            )

        if acq_software == "ScanImage":
            import scanreader
            from element_interface import scanimage_utils

            try:  # attempt to read .tif as a scanimage file
                loaded_scan = scanreader.read_scan(scan_filepaths)
                recording_time = scanimage_utils.get_scanimage_acq_time(loaded_scan)
                header = scanimage_utils.parse_scanimage_header(loaded_scan)
                scanner = header["SI_imagingSystem"].strip("'")
            except Exception as e:
                print(f"ScanImage loading error: {scan_filepaths}\n{str(e)}")
                continue
        elif acq_software == "Scanbox":
            import sbxreader

            try:  # attempt to load Scanbox
                sbx_fp = pathlib.Path(scan_filepaths[0])
                sbx_meta = sbxreader.sbx_get_metadata(sbx_fp)
                # read from file when Scanbox support this
                recording_time = datetime.fromtimestamp(sbx_fp.stat().st_ctime)
                scanner = sbx_meta.get("imaging_system", "Scanbox")
            except Exception as e:
                print(f"Scanbox loading error: {scan_filepaths}\n{str(e)}")
                continue
        else:
            raise NotImplementedError(
                "Processing scan from acquisition software of "
                + f"type {acq_software} is not yet implemented"
            )

        session_key = {"subject": sess["subject"], "session_datetime": recording_time}
        if session_key not in session.Session():
            scanner_list.append({"scanner": scanner})
            session_list.append(session_key)
            scan_list.append(
                {
                    **session_key,
                    "scan_id": 0,
                    "scanner": scanner,
                    "acq_software": acq_software,
                }
            )

            session_dir_list.append(
                {
                    **session_key,
                    "session_dir": sess_dir.relative_to(root_data_dir).as_posix(),
                }
            )
    new_equipment = set(val for dic in scanner_list for val in dic.values())
    if verbose:
        print(
            f"\n---- Insert {len(new_equipment)} entry(s) into "
            + "experiment.Equipment ----"
        )
    Equipment.insert(scanner_list, skip_duplicates=skip_duplicates)

    if verbose:
        print(f"\n---- Insert {len(session_list)} entry(s) into session.Session ----")
    session.Session.insert(session_list, skip_duplicates=skip_duplicates)
    session.SessionDirectory.insert(session_dir_list, skip_duplicates=skip_duplicates)

    if verbose:
        print(f"\n---- Insert {len(scan_list)} entry(s) into scan.Scan ----")
    scan.Scan.insert(scan_list, skip_duplicates=skip_duplicates)

    if verbose:
        print("\n---- Successfully completed ingest_sessions ----")


def ingest_events(
    recording_csv_path="./user_data/behavior_recordings.csv",
    block_csv_path="./user_data/blocks.csv",
    trial_csv_path="./user_data/trials.csv",
    event_csv_path="./user_data/events.csv",
    skip_duplicates=True,
    verbose=True,
):
    """
    Ingest session, block, trial, and event data.

    Ingest each level of experiment hierarchy for element-trial: recording, block (i.e.,
    phases of trials), trials (repeated units), events (optionally 0-duration occurances
    within trial).

    This ingestion function is duplicated across wf-array-ephys and wf-calcium-imaging.

    Args:
        recording_csv_path (str, optional): relative path of behavior_recordings.csv.
        block_csv_path (str, optional): relative path of blocks.csv.
        trial_csv_path (str, optional): relative path of trials.csv.
        event_csv_path (str, optional): relative path of events.csv.
        skip_duplicates (bool, optional): Default True. Passed to DataJoint insert.
        verbose (bool, optional): Display number of entries inserted when ingesting.
            Default True.
    """
    csvs = [
        recording_csv_path,
        recording_csv_path,
        block_csv_path,
        block_csv_path,
        trial_csv_path,
        trial_csv_path,
        trial_csv_path,
        trial_csv_path,
        event_csv_path,
        event_csv_path,
        event_csv_path,
    ]
    tables = [
        event.BehaviorRecording(),
        event.BehaviorRecording.File(),
        trial.Block(),
        trial.Block.Attribute(),
        trial.TrialType(),
        trial.Trial(),
        trial.Trial.Attribute(),
        trial.BlockTrial(),
        event.EventType(),
        event.Event(),
        trial.TrialEvent(),
    ]

    # Allow direct insert required bc element-trial has Imported that should be Manual
    ingest_csv_to_table(
        csvs,
        tables,
        skip_duplicates=skip_duplicates,
        verbose=verbose,
        allow_direct_insert=True,
    )


def ingest_alignment(
    alignment_csv_path="./user_data/alignments.csv", skip_duplicates=True, verbose=True
):
    """This is duplicated across wf-array-ephys and wf-calcium-imaging.

    Args:
        alignment_csv_path (str): relative path of alignments.csv
        skip_duplicates (bool, optional): Default True. Passed to DataJoint insert.
        verbose (bool, optional): Display number of entries inserted when ingesting.
            Default True.
    """

    csvs = [alignment_csv_path]
    tables = [event.AlignmentEvent()]

    ingest_csv_to_table(csvs, tables, skip_duplicates=skip_duplicates, verbose=verbose)


if __name__ == "__main__":
    ingest_subjects()
    ingest_sessions()
    ingest_events()
    ingest_alignment()
