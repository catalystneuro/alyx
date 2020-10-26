import csv
import xlrd
import re
import datetime
from datetime import timedelta
from scipy.io import loadmat

from django.contrib.auth import get_user_model
from django.db.models import Q

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from buffalo.constants import (
    SESSIONS_FILE_COLUMNS,
    BOOLEAN_VALUES,
    BOOLEAN_CELLS,
    START_TIME_CELLS,
    NUMBER_CELLS,
)


def is_datetime(date, workbook):
    try:
        datetime.datetime(*xlrd.xldate_as_tuple(date, workbook.datemode))
        return True

    except:
        return False


def is_number(cell_value):
    return cell_value.replace("-", "", 1).replace(".", "", 1).isdigit()


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


def is_valid_time(time):
    result = re.match(r"\b(([0-9]|1[0-9]|2[0-3]):([0-9]|[1-4][0-9]|5[0-9]))\b", time)
    if result is None:
        return False

    return True


def validate_sessions_file(file):
    workbook = xlrd.open_workbook(file_contents=file.read())
    sessions_sheet = workbook.sheet_by_index(0)
    for i, column_name in enumerate(SESSIONS_FILE_COLUMNS):
        if SESSIONS_FILE_COLUMNS[i] != sessions_sheet.cell_value(0, i):
            error_message = f"""The column {i} should be {SESSIONS_FILE_COLUMNS[i]} and
            is {sessions_sheet.cell_value(0, i)} instead."""
            raise ValidationError(
                error_message, code="invalid", params={"file": file},
            )

    for row in range(sessions_sheet.nrows)[1:]:
        date = is_datetime(sessions_sheet.cell(row, 0).value, workbook)
        if not date:
            for i, _ in enumerate(SESSIONS_FILE_COLUMNS):
                if sessions_sheet.cell_value(row, i):
                    raise ValidationError(
                        f"This value date in row {row} column {i} must be a valid date",
                        code="invalid",
                        params={"file": file},
                    )
        # validate number values
        for number_cell in NUMBER_CELLS:
            value = sessions_sheet.cell_value(row, int(number_cell))
            if value and not isinstance(value, (int, float)):
                raise ValidationError(
                    f"The value {value} is not valid ",
                    code="invalid",
                    params={"file": file},
                )
        # validate Yes No N/A values
        for boolean_cell in BOOLEAN_CELLS:
            value = sessions_sheet.cell_value(row, int(boolean_cell))
            if value and value.strip().lower() not in BOOLEAN_VALUES:
                raise ValidationError(
                    f"The value {value} is not valid",
                    code="invalid",
                    params={"file": file},
                )
        # validate start time values
        for start_time_cell in START_TIME_CELLS:
            start_time = str(
                sessions_sheet.cell(row, int(start_time_cell)).value
            ).strip()
            if start_time:
                try:
                    xlrd.xldate.xldate_as_datetime(
                        sessions_sheet.cell(row, int(start_time_cell)).value,
                        workbook.datemode,
                    )
                except:
                    value = sessions_sheet.cell(row, int(start_time_cell)).value
                    raise ValidationError(
                        f"""The value in the row {row+1} column {start_time_cell} '{value}'
                        is not a valid Start Time (h:m)""",
                        code="invalid",
                        params={"file": file},
                    )


def get_sessions_from_file(file):
    file.seek(0)
    workbook = xlrd.open_workbook(file_contents=file.read())
    sessions = []
    session = {}
    sessions_sheet = workbook.sheet_by_index(0)

    for row in range(sessions_sheet.nrows)[1:]:
        session_date = sessions_sheet.cell(row, 0).value
        if not session_date:
            continue
        session_date = datetime.datetime(
            *xlrd.xldate_as_tuple(session_date, workbook.datemode)
        )
        session["0_Date (mm/dd/yyyy)"] = session_date
        for i, column_name in enumerate(SESSIONS_FILE_COLUMNS[1:]):
            i += 1
            session_index = f"{i}_{column_name}"
            value = sessions_sheet.cell(row, i).value
            if str(i) in START_TIME_CELLS:
                start_time = str(value).strip()
                if start_time:
                    start_time = xlrd.xldate.xldate_as_datetime(
                        value, workbook.datemode
                    )
                    start_time = timedelta(
                        hours=start_time.hour, minutes=start_time.minute
                    )
                    value = session_date + start_time
                else:
                    value = None
            session[session_index] = value
        # At this point if the session doesn't have date is an empty row
        if session:
            sessions.append(session)
            session = {}
    return sessions


def get_user_from_initial(user_initials):
    user_model = get_user_model()
    user = user_model.objects.filter(
        Q(first_name__istartswith=user_initials[0]),
        Q(last_name__istartswith=user_initials[1]),
    )
    return user


def validate_electrodelog_file(file):
    if not file:
        return

    regex = "^Trode \\(([0-9]|[1-8][0-9]|9[0-9]|1[0-9]{2}|200)\\)$"

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
                if re.search(regex, sheet.name) is None:
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
        msg = "Error loading the file - Sheet: {} - Row: {} - Column: {} - File: {}"
        for sheet in workbook.sheets():
            if sheet_number > 1 and re.search(regex, sheet.name) is not None:
                for row in range(sheet.nrows):
                    if row >= 3:
                        date = sheet.cell(row, 0)
                        turns = sheet.cell(row, 2)
                        impedance = sheet.cell(row, 4)
                        if str(date.value).strip() != "":
                            if is_datetime(date.value, workbook):
                                if not is_number(str(turns.value)):
                                    raise ValidationError(
                                        msg.format(sheet.name, row + 1, 3, file),
                                        code="invalid",
                                        params={"file": file},
                                    )
                                if str(impedance.value).strip() != "":
                                    if not is_number(str(impedance.value)):
                                        raise ValidationError(
                                            msg.format(sheet.name, row + 1, 5, file),
                                            code="invalid",
                                            params={"file": file},
                                        )
                            else:
                                raise ValidationError(
                                    msg.format(sheet.name, row + 1, 1, file),
                                    code="invalid",
                                    params={"file": file},
                                )
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
                    impedance = sheet.cell(row, 4)
                    notes = sheet.cell(row, 8)
                    if str(date.value).strip() != "":
                        if is_datetime(date.value, workbook):
                            log = {}
                            log_datetime = datetime.datetime(
                                *xlrd.xldate_as_tuple(date.value, workbook.datemode)
                            )
                            log["turns"] = float(turns.value)
                            log["datetime"] = log_datetime
                            if str(impedance.value).strip() != "":
                                log["impedance"] = float(impedance.value)
                            else:
                                log["impedance"] = None
                            if str(notes.value).strip() != "":
                                log["notes"] = str(notes.value).strip()
                            else:
                                log["notes"] = None

                            electrode["logs"].append(log)
            if len(electrode["logs"]) > 0:
                electrodes.append(electrode)
        sheet_number += 1
    return electrodes
