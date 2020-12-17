from workflow_imaging.pipeline import subject, imaging
import numpy as np


# -------------- Insert new "Subject" --------------

subjects = [{'subject': 'subjectname', 'sex': 'F', 'subject_birth_date': '2020-05-06 15:20:01'}]

subject.Subject.insert(subjects, skip_duplicates=True)

# -------------- Insert new "ProcessingParamSet" for Suite2p --------------
params = np.load('./params/suite2p_0.npy', allow_pickle=True).item()

imaging.ProcessingParamSet.insert_new_params(
    'suite2p', 0, 'Calcium imaging analysis with Suite2p using default Suite2p parameters', params)

# -------------- Insert new "ProcessingParamSet" for CaImAn --------------
params = np.load('./params/caiman_1.npy', allow_pickle=True).item()

imaging.ProcessingParamSet.insert_new_params(
    'caiman', 1, 'Calcium imaging analysis with CaImAn using default CaImAn parameters', params)
