import numpy as np
import csv
from workflow_imaging.pipeline import subject, imaging

# -------------- Insert new "Subject" --------------
print('Inserting Subject')

subjects = []
with open("./user_data/subjects.csv") as fp:
    reader = csv.reader(fp, delimiter=",")
    next(reader, None)  # skip the header
    [subjects.append(dict(subject                = row[0],
                          sex                    = row[1],
                          subject_birth_date     = row[2],
                          subject_description    = row[3]
                         )) for row in reader]

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