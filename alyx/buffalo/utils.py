from scipy.io import loadmat
from django.core.exceptions import ValidationError

def validate_mat_file(file, unique_id):
    try:
        mat_file = loadmat(file)
        electrodes = mat_file[unique_id].tolist()
    except:
        raise ValidationError(
                            'It cannot find an structure called: {}'.format(unique_id), 
                            code='invalid', 
                            params={'unique_id': unique_id}
                            )
    try:
        mat_file = loadmat(file)
        electrodes = mat_file[unique_id].tolist()
        get_electrodes_clean(electrodes)
    except:
        raise ValidationError(
                    'Error loading the file: {}'.format(file), 
                    code='invalid', 
                    params={'file': file}
                    )

def get_electrodes_clean(electrodes_mat):
    electrodes_clean = []
    for electrode in electrodes_mat:
        element = {
            "channel": electrode[0][0].tolist()[0][0],
            "start_point": electrode[0][1].tolist()[0],
            "norms": electrode[0][2].tolist()[0]
        }
        electrodes_clean.append(element)
    return electrodes_clean

def get_mat_file_info(file, unique_id):
    mat_file = loadmat(file)
    electrodes = mat_file[unique_id].tolist()
    return get_electrodes_clean(electrodes)

    
