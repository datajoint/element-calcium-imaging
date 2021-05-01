from workflow_calcium_imaging.pipeline import imaging, scan
import warnings

warnings.filterwarnings('ignore')


def run(display_progress=True):

    populate_settings = {'display_progress': display_progress,
                         'reserve_jobs': False,
                         'suppress_errors': False}

    print('\n---- Populate scan.ScanInfo ----')
    scan.ScanInfo.populate(**populate_settings)

    print('\n---- Populate imaging.Processing ----')
    imaging.Processing.populate(**populate_settings)

    print('\n---- Populate imaging.MotionCorrection ----')
    imaging.MotionCorrection.populate(**populate_settings)

    print('\n---- Populate imaging.Segmentation ----')
    imaging.Segmentation.populate(**populate_settings)

    print('\n---- Populate imaging.MaskClassification ----')
    imaging.MaskClassification.populate(**populate_settings)

    print('\n---- Populate imaging.Fluorescence ----')
    imaging.Fluorescence.populate(**populate_settings)

    print('\n---- Populate imaging.Activity ----')
    imaging.Activity.populate(**populate_settings)

    print('\n---- Successfully completed workflow_calcium_imaging/populate.py ----')


if __name__ == '__main__':
    run()
