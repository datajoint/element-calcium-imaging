import scanreader

from workflow_imaging.pipeline import subject, imaging, scan, Session, Equipment
from workflow_imaging.paths import get_imaging_root_data_dir

from elements_imaging.readers import get_scanimage_acq_time, parse_scanimage_header


def ingest():
    # ---------- Insert new "Session" and "Scan" ----------
    data_dir = get_imaging_root_data_dir()
    print('---- Search for new sessions ----')

    # Folder structure: root / subject / session / .tif (raw)
    sessions, scans, scanners = [], [], []
    sess_folder_names = []
    for subj_key in subject.Subject.fetch('KEY'):
        subj_dir = data_dir / subj_key['subject']
        if subj_dir.exists():
            for tiff_filepath in subj_dir.glob('*/*.tif'):
                sess_folder = tiff_filepath.parent
                if sess_folder.name not in sess_folder_names:
                    tiff_filepaths = [fp.as_posix() for fp in sess_folder.glob('*.tif')]
                    try:  # attempt to read .tif as a scanimage file
                        loaded_scan = scanreader.read_scan(tiff_filepaths)
                    except Exception as e:
                        print(f'ScanImage loading error: {tiff_filepaths}\n{str(e)}')
                        loaded_scan = None

                    if loaded_scan is not None:
                        sess_folder_names.append(sess_folder.name)
                        recording_time = get_scanimage_acq_time(loaded_scan)
                        header = parse_scanimage_header(loaded_scan)
                        session_key = {**subj_key, 'session_datetime': recording_time}
                        scanner = header['SI_imagingSystem']
                        if session_key not in Session.proj():
                            print(f'Inserting session: {session_key} (from {sess_folder})')
                            scanners.append({'scanner': scanner})
                            sessions.append(session_key)
                            scans.append({**session_key, 'scan_id': 0, 'scanner': scanner})

    Equipment.insert(scanners, skip_duplicates=True)
    Session.insert(sessions)
    scan.Scan.insert(scans)
    print(f'Inserted {len(sessions)} session(s)')

    # populate ScanInfo
    print('---- Populate ScanInfo ----')
    scan.ScanInfo.populate(suppress_errors=True, display_progress=True)

    # ---------- Create ProcessingTask for each scan ----------

    # suite2p
    imaging.ProcessingTask.insert([{**sc, 'paramset_idx': 0, 'task_mode': 'load'}
                                   for sc in scan.Scan.fetch('KEY')], skip_duplicates=True)

    # caiman - 2D
    imaging.ProcessingTask.insert([{**sc, 'paramset_idx': 1, 'task_mode': 'load'}
                                   for sc in (scan.Scan & (scan.ScanInfo & 'ndepths = 1')).fetch('KEY')],
                                  skip_duplicates=True)

    # caiman - 3D
    imaging.ProcessingTask.insert([{**sc, 'paramset_idx': 2, 'task_mode': 'load'}
                                   for sc in (scan.Scan & (scan.ScanInfo & 'ndepths > 1')).fetch('KEY')],
                                  skip_duplicates=True)


if __name__ == '__main__':
    ingest()
