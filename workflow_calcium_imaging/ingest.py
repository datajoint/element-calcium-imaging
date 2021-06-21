import pathlib
import csv
from datetime import datetime

from .pipeline import subject, imaging, scan, session, Equipment
from .paths import get_imaging_root_data_dir


def ingest_subjects(subject_csv_path='./user_data/subjects.csv'):
    # -------------- Insert new "Subject" --------------
    with open(subject_csv_path, newline= '') as f:
        input_subjects = list(csv.DictReader(f, delimiter=','))

    print(f'\n---- Insert {len(input_subjects)} entry(s) into subject.Subject ----')
    subject.Subject.insert(input_subjects, skip_duplicates=True)

    print('\n---- Successfully completed ingest_subjects ----')


def ingest_sessions(session_csv_path='./user_data/sessions.csv'):
    root_data_dir = get_imaging_root_data_dir()

    # ---------- Insert new "Session" and "Scan" ---------
    with open(session_csv_path, newline= '') as f:
        input_sessions = list(csv.DictReader(f, delimiter=','))

    # Folder structure: root / subject / session / .tif (raw)
    session_list, session_dir_list, scan_list, scanner_list = [], [], [], []

    for sess in input_sessions:
        sess_dir = pathlib.Path(sess['session_dir'])

        # search for either ScanImage or Scanbox files (in that order)
        for scan_pattern, scan_type, glob_func in zip(['*.tif', '*.sbx'],
                                                      ['ScanImage', 'Scanbox'],
                                                      [sess_dir.glob, sess_dir.rglob]):
            scan_filepaths = [fp.as_posix() for fp in glob_func(scan_pattern)]
            if len(scan_filepaths):
                acq_software = scan_type
                break
        else:
            raise FileNotFoundError(f'Unable to identify scan files from the supported acquisition softwares (ScanImage, Scanbox) at: {sess_dir}')

        if acq_software == 'ScanImage':
            import scanreader
            from element_data_loader import scanimage_utils
            try:  # attempt to read .tif as a scanimage file
                loaded_scan = scanreader.read_scan(scan_filepaths)
                recording_time = scanimage_utils.get_scanimage_acq_time(loaded_scan)
                header = scanimage_utils.parse_scanimage_header(loaded_scan)
                scanner = header['SI_imagingSystem'].strip('\'')
            except Exception as e:
                print(f'ScanImage loading error: {scan_filepaths}\n{str(e)}')
                continue
        elif acq_software == 'Scanbox':
            import sbxreader
            try:  # attempt to load scanbox
                sbx_fp = pathlib.Path(scan_filepaths[0])
                sbx_meta = sbxreader.sbx_get_metadata(sbx_fp)
                recording_time = datetime.fromtimestamp(sbx_fp.stat().st_ctime)  # read from file when scanbox support this
                scanner = sbx_meta.get('imaging_system', 'Scanbox')
            except Exception as e:
                print(f'Scanbox loading error: {scan_filepaths}\n{str(e)}')
                continue
        else:
            raise NotImplementedError(f'Processing scan from acquisition software of type {acq_software} is not yet implemented')

        session_key = {'subject': sess['subject'], 'session_datetime': recording_time}
        if session_key not in session.Session():
            scanner_list.append({'scanner': scanner})
            session_list.append(session_key)
            scan_list.append({**session_key, 'scan_id': 0, 'scanner': scanner, 'acq_software': acq_software})

            session_dir_list.append({**session_key, 'session_dir': sess_dir.relative_to(root_data_dir).as_posix()})

    print(f'\n---- Insert {len(set(val for dic in scanner_list for val in dic.values()))} entry(s) into experiment.Equipment ----')
    Equipment.insert(scanner_list, skip_duplicates=True)

    print(f'\n---- Insert {len(session_list)} entry(s) into session.Session ----')
    session.Session.insert(session_list)
    session.SessionDirectory.insert(session_dir_list)

    print(f'\n---- Insert {len(scan_list)} entry(s) into scan.Scan ----')
    scan.Scan.insert(scan_list)

    print('\n---- Successfully completed ingest_sessions ----')


if __name__ == '__main__':
    ingest_subjects()
    ingest_sessions()
