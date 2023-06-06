from . import pipeline


def test_pipeline(pipeline):
    subject = pipeline["subject"]
    imaging = pipeline["imaging"]
    scan = pipeline["scan"]
    session = pipeline["session"]
    Equipment = pipeline["Equipment"]

    # Test connection from Subject to Session
    assert subject.Subject.full_table_name in session.Session.parents()

    # Test connection from Session and Equipment to Scan
    assert session.Session.full_table_name in scan.Scan.parents()
    assert Equipment.full_table_name in scan.Scan.parents()

    assert "mask_npix" in imaging.Segmentation.Mask.heading.secondary_attributes
    assert "activity_trace" in imaging.Activity.Trace.heading.secondary_attributes

