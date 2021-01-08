import numpy as np
from workflow_imaging.pipeline import imaging, scan

populate_settings = {'display_progress': True, 'reserve_jobs': False, 'suppress_errors': False}


def populate():
    # populate "dj.Imported" and "dj.Computed" tables
    imaging.Processing.populate(**populate_settings)
    imaging.MotionCorrection.populate(**populate_settings)
    imaging.Segmentation.populate(**populate_settings)
    imaging.MaskClassification.populate(**populate_settings)
    imaging.Fluorescence.populate(**populate_settings)
    imaging.Activity.populate(**populate_settings)


if __name__ == '__main__':
    populate()
