import pathlib
import csv

from .pipeline import subject, imaging, scan, Session, Equipment
from .paths import get_imaging_root_data_dir


def ingest_subjects():
    # -------------- Insert new "Subject" --------------
    with open('./user_data/subjects.csv', newline='') as f:
        input_subjects = list(csv.DictReader(f, delimiter=','))

    print(f'\n---- Insert {len(input_subjects)} entry(s) into subject.Subject ----')
    subject.Subject.insert(input_subjects, skip_duplicates=True)


def ingest_sessions():
    root_data_dir = get_imaging_root_data_dir()

    # ---------- Insert new "Session" and "Scan" ---------
    with open('./user_data/sessions.csv', newline='') as f:
        input_sessions = list(csv.DictReader(f, delimiter=','))

    # Folder structure: root / subject / session / .tif (raw)
    sessions, scans, scanners = [], [], []
    session_directories, processing_tasks = [], []

    for session in input_sessions:
        sess_dir = pathlib.Path(session['session_dir'])
        # search for either ScanImage or ScanBox files (in that order)
        for scan_pattern, scan_type in zip(['*.tif', '*.sbx'], ['ScanImage', 'ScanBox']):
            scan_filepaths = [fp.as_posix() for fp in sess_dir.glob(scan_pattern)]
            if len(scan_filepaths):
                acq_software = scan_type
                break

        if acq_software == 'ScanImage':
            import scanreader
            from elements_imaging.readers import get_scanimage_acq_time, parse_scanimage_header
            try:  # attempt to read .tif as a scanimage file
                loaded_scan = scanreader.read_scan(scan_filepaths)
                recording_time = get_scanimage_acq_time(loaded_scan)
                header = parse_scanimage_header(loaded_scan)
                scanner = header['SI_imagingSystem'].strip('\'')
            except Exception as e:
                print(f'ScanImage loading error: {scan_filepaths}\n{str(e)}')
                continue
        elif acq_software == 'ScanBox':
            import sbxreader
            try:  # attempt to load scanbox
                sbx_meta = sbxreader.sbx_get_metadata(scan_filepaths[0])
                sbx_matinfo = sbxreader.sbx_get_info(scan_filepaths[0])
                recording_time = sbx_meta.get('recording_time', None)  #TODO - NOT FOUND
                scanner = sbx_meta.get('imaging_system', None)  #TODO - NOT FOUND
            except Exception as e:
                print(f'ScanBox loading error: {scan_filepaths}\n{str(e)}')
                continue

        session_key = {'subject': session['subject'], 'session_datetime': recording_time}
        if session_key not in Session.proj():
            scanners.append({'scanner': scanner})
            sessions.append(session_key)
            scans.append({**session_key, 'scan_id': 0, 'scanner': scanner, 'acq_software': acq_software})

            session_directories.append({**session_key, 'session_dir': sess_dir.relative_to(root_data_dir).as_posix()})

            parameter_set = [int(s) for s in session['paramset'].split(' ')]
            for param in parameter_set:
                processing_tasks.append({**session_key, 'scan_id': 0, 'paramset_idx': param, 'task_mode': 'load'})

    print(f'\n---- Insert {len(set(val for dic in scanners for val in dic.values()))} entry(s) into experiment.Equipment ----')
    Equipment.insert(scanners, skip_duplicates=True)

    print(f'\n---- Insert {len(sessions)} entry(s) into experiment.Session ----')
    Session.insert(sessions)
    
    print(f'\n---- Insert {len(session_directories)} entry(s) into experiment.Session.Directory ----')
    Session.Directory.insert(session_directories)

    print(f'\n---- Insert {len(scans)} entry(s) into scan.Scan ----')
    scan.Scan.insert(scans)

    print(f'\n---- Insert {len(processing_tasks)} entry(s) into imaging.ProcessingTask ----')
    imaging.ProcessingTask.insert(processing_tasks)

    print('\n---- Successfully completed workflow_imaging/ingest.py ----')


if __name__ == '__main__':
    ingest_subjects()
    ingest_sessions()
