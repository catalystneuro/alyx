from scipy.io import loadmat
from django.core.exceptions import ValidationError

def validate_mat_file(file, structure_name):
    try:
        mat_file = loadmat(file)
        key = get_struct_name(list(mat_file.keys()))
        electrodes = mat_file[structure_name].tolist()
    except:
        raise ValidationError(
                            'It cannot find an structure called: {}. It got: {}'.format(structure_name, key), 
                            code='invalid', 
                            params={'structure_name': structure_name}
                            )
    try:
        mat_file = loadmat(file)
        electrodes = mat_file[structure_name].tolist()
        get_electrodes_clean(electrodes)
    except:
        raise ValidationError(
                    'Error loading the file: {}'.format(file), 
                    code='invalid', 
                    params={'file': file}
                )

def get_struct_name(keys):
    keys_list = list(keys)
    keys_list.remove('__version__')
    keys_list.remove('__globals__')
    keys_list.remove('__header__')
    if (len(keys_list) > 0):
        return keys_list[0]
    return None

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

def get_mat_file_info(file, structure_name):
    mat_file = loadmat(file)
    electrodes = mat_file[structure_name].tolist()
    return get_electrodes_clean(electrodes)
