import scanreader

from workflow_imaging.pipeline import subject, imaging, scan, Session, Equipment
from workflow_imaging.paths import get_imaging_data_dir

from elements_imaging.readers import get_scanimage_acq_time, parse_scanimage_header


def ingest():
    # ========== Insert new "Session" and "Scan" ===========
    data_dir = get_imaging_data_dir()

    # Folder structure: root / subject / session / .tif (raw)
    sessions, scans, scanners = [], [], []
    sess_folder_names = []
    for subj_key in subject.Subject.fetch('KEY'):
        subj_dir = data_dir / subj_key['subject']
        if subj_dir.exists():
            for tiff_filepath in subj_dir.glob('*/*.tif'):
                sess_folder = tiff_filepath.parent.name
                if sess_folder not in sess_folder_names:
                    tiff_filepaths = [fp.as_posix() for fp in (subj_dir / sess_folder).glob('*.tif')]
                    try:  # attempt to read .tif as a scanimage file
                        scanimage = scanreader.read_scan(tiff_filepaths)
                    except Exception as e:
                        print(f'ScanImage loading error: {tiff_filepaths}\n{str(e)}')
                        scanimage = None

                    if scanimage is not None:
                        recording_time = get_scanimage_acq_time(scanimage)
                        header = parse_scanimage_header(scanimage)
                        scanner = header['SI_imagingSystem']

                        scanners.append({'scanner': scanner})
                        sessions.append({**subj_key, 'session_datetime': recording_time})
                        scans.append({**subj_key, 'session_datetime': recording_time,
                                      'scan_id': 0, 'scanner': scanner})
                        sess_folder_names.append(sess_folder)

    print(f'Inserting {len(sessions)} session(s)')
    Equipment.insert(scanners, skip_duplicates=True)
    Session.insert(sessions, skip_duplicates=True)
    scan.Scan.insert(scans, skip_duplicates=True)

    # ---------- Create ProcessingTask for each scan ----------

    # suite2p
    imaging.ProcessingTask.insert([{**sc, 'paramset_idx': 0, 'task_mode': 'load'}
                                   for sc in scan.Scan.fetch('KEY')], skip_duplicates=True)

    # caiman
    imaging.ProcessingTask.insert([{**sc, 'paramset_idx': 1, 'task_mode': 'load'}
                                   for sc in scan.Scan.fetch('KEY')], skip_duplicates=True)


if __name__ == '__main__':
    ingest()
