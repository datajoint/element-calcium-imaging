from workflow_calcium_imaging.pipeline import imaging, scan
import warnings

warnings.filterwarnings("ignore")


def run(display_progress=True):

    populate_settings = {
        "display_progress": display_progress,
        "reserve_jobs": False,
        "suppress_errors": False,
    }

    print("\n---- Populate imported and computed tables ----")

    scan.ScanInfo.populate(**populate_settings)

    imaging.Processing.populate(**populate_settings)

    imaging.MotionCorrection.populate(**populate_settings)

    imaging.Segmentation.populate(**populate_settings)

    imaging.MaskClassification.populate(**populate_settings)

    imaging.Fluorescence.populate(**populate_settings)

    imaging.Activity.populate(**populate_settings)

    print("\n---- Successfully completed workflow_calcium_imaging/process.py ----")


if __name__ == "__main__":
    run()
