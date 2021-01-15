from workflow_imaging.pipeline import subject, imaging
import numpy as np


# -------------- Insert new "Subject" --------------
print('Inserting Subject')

subjects = [{'subject': 'subject1', 'sex': 'F', 'subject_birth_date': '2020-05-06 15:20:01'},
            {'subject': 'subject2', 'sex': 'F', 'subject_birth_date': '2020-11-26 05:12:21'}]

subject.Subject.insert(subjects, skip_duplicates=True)

# -------------- Insert new "ProcessingParamSet" for Suite2p --------------
print('Inserting ProcessingParamSet for Suite2p')

params = np.load('./user_data/params/suite2p_default.npy', allow_pickle=True).item()

imaging.ProcessingParamSet.insert_new_params(
    'suite2p', 0, 'Calcium imaging analysis with Suite2p using default Suite2p parameters', params)

# -------------- Insert new "ProcessingParamSet" for CaImAn --------------
print('Inserting ProcessingParamSet for CaIman')

params = np.load('./user_data/params/caiman_2d_default.npy', allow_pickle=True).item()

imaging.ProcessingParamSet.insert_new_params(
    'caiman', 1, 'Calcium imaging analysis with CaImAn using default CaImAn parameters for 2d planar images', params)

params = np.load('./user_data/params/caiman_3d_default.npy', allow_pickle=True).item()

imaging.ProcessingParamSet.insert_new_params(
    'caiman', 2, 'Calcium imaging analysis with CaImAn using default CaImAn parameters for 3d volumetric images', params)