import numpy as np
from workflow_imaging import imaging

populate_settings = {'reserve_jobs': True, 'suppress_errors': True, 'display_progress': True}


def populate():
    # populate "dj.Imported" and "dj.Computed" tables
    for tbl in imaging._table_classes:
        if np.any([c.__name__ in ('Imported', 'Computed') for c in tbl.__bases__]):
            print('\n--- Populating {} ---'.format(tbl.__name__))
            tbl.populate(**populate_settings)


if __name__ == '__main__':
    populate()
