from scipy.io import loadmat
import xlrd
import csv, re
import datetime
from dateutil.parser import parse
from django.core.exceptions import ValidationError
from django.http import HttpResponse


def is_datetime(date, workbook):
    try:
        datetime.datetime(*xlrd.xldate_as_tuple(date, workbook.datemode))
        return True

    except ValueError:
        return False


def is_number(s):
    return s.replace("-", "", 1).replace(".", "", 1).isdigit()


def validate_mat_file(file, structure_name):
    if not file:
        return

    try:
        mat_file = loadmat(file)
        key = get_struct_name(list(mat_file.keys()))
        electrodes = mat_file[structure_name].tolist()
    except:
        raise ValidationError(
            "It cannot find an structure called: {}. It got: {}".format(
                structure_name, key
            ),
            code="invalid",
            params={"structure_name": structure_name},
        )
    try:
        mat_file = loadmat(file)
        electrodes = mat_file[structure_name].tolist()
        get_electrodes_clean(electrodes)
    except:
        raise ValidationError(
            "Error loading the file: {}".format(file),
            code="invalid",
            params={"file": file},
        )


def get_struct_name(keys):
    keys_list = list(keys)
    keys_list.remove("__version__")
    keys_list.remove("__globals__")
    keys_list.remove("__header__")
    if len(keys_list) > 0:
        return keys_list[0]
    return None


def get_electrodes_clean(electrodes_mat):
    electrodes_clean = []
    for electrode in electrodes_mat:
        element = {
            "channel": electrode[0][0].tolist()[0][0],
            "start_point": electrode[0][1].tolist()[0],
            "norms": electrode[0][2].tolist()[0],
        }
        electrodes_clean.append(element)
    return electrodes_clean


def get_mat_file_info(file, structure_name):
    mat_file = loadmat(file)
    electrodes = mat_file[structure_name].tolist()
    return get_electrodes_clean(electrodes)


def download_csv_points_mesh(subject_name, date, electrodes, electrode_logs, stl_file):
    response = HttpResponse(content_type="text/csv")
    filename = f"{subject_name}-{date}.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    row = ["electrode", "Datetime", "In HPC", "x", "y", "z"]
    writer.writerow(row)
    logs = {}
    for electrode_log in electrode_logs:
        location = electrode_log.get_current_location()
        is_in = electrode_log.is_in_stl(stl_file)
        row = [
            electrode_log.electrode.channel_number,
            date,
            is_in,
            location["x"],
            location["y"],
            location["z"],
        ]
        logs[electrode_log.electrode.channel_number] = row

    for electrode in electrodes:
        if electrode.channel_number in logs:
            writer.writerow(logs[electrode.channel_number])
        else:
            row = [electrode.channel_number, date, False, "NaN", "NaN", "NaN"]
            writer.writerow(row)

    return response


def validate_electrodelog_file(file):
    if not file:
        return

    regex = "^Trode \(([0-9]|[1-8][0-9]|9[0-9]|1[0-9]{2}|200)\)$"

    try:
        workbook = xlrd.open_workbook(file_contents=file.read())
        # Check sheet names
        sheet_number = 1
        for sheet in workbook.sheets():
            if sheet_number == 1:
                if sheet.name != "Summary":
                    raise ValidationError(
                        "Error loading the file - Summary Sheet - File: {}".format(
                            file
                        ),
                        code="invalid",
                        params={"file": file},
                    )
            else:
                if re.search(regex, sheet.name) == None:
                    raise ValidationError(
                        "Error loading the file - Sheet Name: {} - File: {}".format(
                            sheet.name, file
                        ),
                        code="invalid",
                        params={"file": file},
                    )
            sheet_number += 1

        # Check columns
        sheet_number = 1
        for sheet in workbook.sheets():
            if sheet_number > 1 and re.search(regex, sheet.name) != None:
                for row in range(sheet.nrows):
                    if row >= 3:
                        date = sheet.cell(row, 0)
                        turns = sheet.cell(row, 2)
                        if str(date.value).strip() != "":
                            if is_datetime(date.value, workbook):
                                if is_number(str(turns.value)):
                                    pass
                                else:
                                    print(turns.value)
                                    raise ValidationError(
                                        "Error loading the file - Sheet: {} - Row: {} - Column: 2 - File: {}".format(
                                            sheet.name, row, file
                                        ),
                                        code="invalid",
                                        params={"file": file},
                                    )
                        else:
                            pass
            sheet_number += 1
    except Exception as error:
        raise error


def get_electrodelog_info(file):
    if not file:
        return
    file.seek(0)
    workbook = xlrd.open_workbook(file_contents=file.read())
    electrodes = []
    sheet_number = 1
    for sheet in workbook.sheets():
        if sheet_number > 1:
            # Electrode number in each sheet
            electrode_number = int(sheet.cell(0, 2).value)
            electrode = {"electrode": electrode_number, "logs": []}
            for row in range(sheet.nrows):
                # Logs begin from row 3
                if row >= 3:
                    date = sheet.cell(row, 0)
                    turns = sheet.cell(row, 2)
                    if str(date.value).strip() != "":
                        if is_datetime(date.value, workbook):
                            log_datetime = datetime.datetime(
                                *xlrd.xldate_as_tuple(date.value, workbook.datemode)
                            )
                            electrode["logs"].append(
                                {"turns": float(turns.value), "datetime": log_datetime}
                            )
            if len(electrode["logs"]) > 0:
                electrodes.append(electrode)
        sheet_number += 1
    return electrodes
