import scanreader
import numpy as np
import pandas as pd
import pathlib

from workflow_imaging.pipeline import subject, imaging, scan, Session, Equipment

from elements_imaging.readers import get_scanimage_acq_time, parse_scanimage_header


def ingest():
    # -------------- Insert new "Subject" --------------
    subjects_pd = pd.read_csv('./user_data/subjects.csv')
    subjects_dict = subjects_pd.to_dict('records')

    print(f'\n---- Insert {len(subjects_dict)} entry(s) into subject.Subject ----')
    subject.Subject.insert(subjects_dict, skip_duplicates=True)

    # ---------- Insert new "Session" and "Scan" ---------
    sessions_pd = pd.read_csv('./user_data/sessions.csv', delimiter=',')
    sessions_dict = sessions_pd.to_dict('records')

    # Folder structure: root / subject / session / .tif (raw)
    sessions, scans, scanners = [], [], []
    session_directories, processing_tasks = [], []

    for session in sessions_dict:
        sess_dir = pathlib.Path(session['session_dir'])
        tiff_filepaths = [fp.as_posix() for fp in sess_dir.glob('*.tif')]

        try:  # attempt to read .tif as a scanimage file
            loaded_scan = scanreader.read_scan(tiff_filepaths)
        except Exception as e:
            print(f'ScanImage loading error: {tiff_filepaths}\n{str(e)}')
            loaded_scan = None

        if loaded_scan is not None:
            recording_time = get_scanimage_acq_time(loaded_scan)
            header = parse_scanimage_header(loaded_scan)
            session_key = {'subject': session['subject'], 'session_datetime': recording_time}
            scanner = header['SI_imagingSystem'].strip('\'')
            if session_key not in Session.proj():
                scanners.append({'scanner': scanner})
                sessions.append(session_key)
                scans.append({**session_key, 'scan_id': 0, 'scanner': scanner})
                session_directories.append({**session_key, 'session_dir': session['session_dir']})
                
                parameter_set = [int(s) for s in session['paramset'].split(' ')]
                for param in parameter_set:
                    processing_tasks.append({**session_key, 'scan_id': 0, 'paramset_idx': param, 'task_mode': 'load'})

    print(f'\n---- Insert {len(set(val for dic in scanners for val in dic.values()))} entry(s) into experiment.Equipment ----')
    Equipment.insert(scanners, skip_duplicates=True)

    print(f'\n---- Insert {len(sessions)} entry(s) into experiment.Session ----')
    Session.insert(sessions, skip_duplicates=True)
    
    print(f'\n---- Insert {len(session_directories)} entry(s) into experiment.Session.Directory ----')
    Session.Directory.insert(session_directories, skip_duplicates=True)

    print(f'\n---- Insert {len(scans)} entry(s) into scan.Scan ----')
    scan.Scan.insert(scans, skip_duplicates=True)

    print(f'\n---- Insert {len(processing_tasks)} entry(s) into imaging.ProcessingTask ----')
    imaging.ProcessingTask.insert(processing_tasks, skip_duplicates=True)

    print('\n---- Successfully completed workflow_imaging/ingest.py ----')


if __name__ == '__main__':
    ingest()
