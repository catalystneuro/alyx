import csv
import xlrd
import re
from datetime import datetime, date
from datetime import timedelta
from calendar import monthrange
from scipy.io import loadmat
from io import TextIOWrapper
import plotly.graph_objs as go
import numpy as np
from plotly.subplots import make_subplots

from django.contrib.auth import get_user_model
from django.db.models import Q

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from buffalo.constants import (
    SESSIONS_FILE_COLUMNS_V1,
    SESSIONS_FILE_COLUMNS_V2,
    BOOLEAN_VALUES,
    BOOLEAN_CELLS,
    START_TIME_CELLS,
    NUMBER_CELLS,
    VALID_VALUES
)


def is_date_session(value):
    regex_dates = "^[[\\d]{6}[A]*$"
    try:
        return re.search(regex_dates, str(int(value)).strip()) is not None
    except:
        return re.search(regex_dates, str(value).strip()) is not None


def get_date_session(value):
    date = str(value)
    session_date = datetime(
        year=(int(date[0:2]) + 2000), month=int(date[2:4]), day=int(date[4:6])
    )
    return session_date


def get_value(value):
    if isinstance(value, int):
        return str(int(value)).strip()
    elif isinstance(value, float):
        return str(int(value)).strip()
    return str(value).strip()


def is_datetime(date, workbook):
    try:
        datetime(*xlrd.xldate_as_tuple(date, workbook.datemode))
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
        check_type_and_len(electrodes)
        get_electrodes_clean(electrodes)
    except:
        raise ValidationError(
            "Error loading the file: {} - Check the structure".format(file),
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


def check_type_and_len(electrodes_mat):
    for electrode in electrodes_mat:
        channel = electrode[0][0].tolist()[0][0]
        start_point = electrode[0][1].tolist()[0]
        norms = electrode[0][2].tolist()[0]
        assert type(channel) is int
        assert len(start_point) == 3
        assert len(norms) == 3


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
        is_in, _ = electrode_log.is_in_stl(stl_file)
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


def validate_sessions_file(file, subject):
    workbook = xlrd.open_workbook(file_contents=file.read())
    sessions_sheet = workbook.sheet_by_index(0)
    dates = {}
    SESSIONS_FILE_COLUMNS = get_sessions_file_columns(subject)

    for i, column_name in enumerate(SESSIONS_FILE_COLUMNS):
        if SESSIONS_FILE_COLUMNS[i] != sessions_sheet.cell_value(0, i):
            error_message = f"""The column {i} should be {SESSIONS_FILE_COLUMNS[i]} and
            is {sessions_sheet.cell_value(0, i)} instead."""
            raise ValidationError(
                error_message,
                code="invalid",
                params={"file": file},
            )

    for row in range(sessions_sheet.nrows)[1:]:
        date = is_datetime(sessions_sheet.cell(row, 0).value, workbook)
        if not date:
            for i, _ in enumerate(SESSIONS_FILE_COLUMNS):
                if sessions_sheet.cell_value(row, i):
                    raise ValidationError(
                        f"This value in row {row} column {1} must be a valid date",
                        code="invalid",
                        params={"file": file},
                    )
        elif sessions_sheet.cell(row, 0).value in dates.keys():
            repeated_date_row = dates[sessions_sheet.cell(row, 0).value]
            raise ValidationError(
                f"The row {row + 1} and the row {repeated_date_row + 1 } have the same date",
                code="invalid",
                params={"file": file},
            )
        dates[sessions_sheet.cell(row, 0).value] = row
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


def get_sessions_from_file(file, subject):
    file.seek(0)
    workbook = xlrd.open_workbook(file_contents=file.read())
    sessions = []
    session = {}
    sessions_sheet = workbook.sheet_by_index(0)
    SESSIONS_FILE_COLUMNS = get_sessions_file_columns(subject)
    for row in range(sessions_sheet.nrows)[1:]:
        session_date = sessions_sheet.cell(row, 0).value
        if not session_date:
            continue
        session_date = datetime(*xlrd.xldate_as_tuple(session_date, workbook.datemode))
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
                        hours=start_time.hour,
                        minutes=start_time.minute,
                        seconds=start_time.second,
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
                    user = []
                    if str(date.value).strip():
                        if is_datetime(date.value, workbook):
                            log = {}
                            log_datetime = datetime(
                                *xlrd.xldate_as_tuple(date.value, workbook.datemode)
                            )
                            log["turns"] = float(turns.value)
                            log["datetime"] = log_datetime
                            if sheet.cell(row, 1).value.strip():
                                user = get_user_from_initial(
                                    sheet.cell(row, 1).value.strip()
                                )
                            log["user"] = user
                            if str(impedance.value).strip():
                                log["impedance"] = float(impedance.value)
                            else:
                                log["impedance"] = None
                            if str(notes.value).strip():
                                log["notes"] = str(notes.value).strip()
                            else:
                                log["notes"] = None

                            electrode["logs"].append(log)
            if len(electrode["logs"]) > 0:
                electrodes.append(electrode)
        sheet_number += 1
    return electrodes


def validate_channel_recording_file(file):
    if not file:
        return

    regex = "^[\\d]+[a-zA-Z]*$"

    try:
        workbook = xlrd.open_workbook(file_contents=file.read())
        # Check columns
        sheet_number = 1
        msg = "Error loading the file - Sheet: {} - Row: {} - Column: {} - File: {}"
        msg_cr = (
            "Channel number name error - Sheet: {} - Row: {} - Column: {} - File: {}"
        )
        msg_num = "Invalid value error - Sheet: {} - Row: {} - Column: {} - File: {} - Value: {}"
        msg_date = "Invalid date error - Sheet: {} - Row: {} - Column: {} - File: {} - Value: {}"
        for sheet in workbook.sheets():
            if sheet_number == 1:
                for row in range(sheet.nrows):
                    row_valid = True
                    for col in range(sheet.ncols):
                        if row == 1:
                            if col > 0:
                                # Check dates row in sheet 1
                                cell = sheet.cell(row, col)
                                if not is_date_session(cell.value) or not isinstance(
                                    cell.value, float
                                ):
                                    raise ValidationError(
                                        msg.format(sheet.name, row + 1, col + 1, file),
                                        code="invalid",
                                        params={"file": file},
                                    )
                        elif row > 1:
                            if col == 0:
                                # Check channel number
                                cell = sheet.cell(row, col)
                                if not str(cell.value).strip():
                                    row_valid = False
                                else:
                                    if re.search(regex, get_value(cell.value)) is None:
                                        raise ValidationError(
                                            msg_cr.format(
                                                sheet.name, row + 1, col + 1, file
                                            ),
                                            code="invalid",
                                            params={"file": file},
                                        )
                            elif col > 1:
                                if row_valid:
                                    # Check values
                                    cell = sheet.cell(row, col)
                                    if get_value(cell.value) not in VALID_VALUES:
                                        raise ValidationError(
                                            msg_num.format(
                                                sheet.name,
                                                row + 1,
                                                col + 1,
                                                file,
                                                get_value(cell.value),
                                            ),
                                            code="invalid",
                                            params={"file": file},
                                        )
            elif sheet_number == 2:  # Check
                for row in range(sheet.nrows):
                    if row > 0:
                        for col in range(sheet.ncols):
                            # Check session date
                            if col == 0:
                                cell = sheet.cell(row, 0)
                                try:
                                    datetime(
                                        *xlrd.xldate_as_tuple(
                                            cell.value, workbook.datemode
                                        )
                                    )
                                except:
                                    raise ValidationError(
                                        msg_date.format(
                                            sheet.name,
                                            row + 1,
                                            col + 1,
                                            file,
                                            get_value(cell.value),
                                        ),
                                        code="invalid",
                                        params={"file": file},
                                    )
                            elif col == 1 or col == 3 or col == 5 or col == 7:
                                cell = sheet.cell(row, col)
                                if str(cell.value).strip() not in ["Y", "N", ""]:
                                    raise ValidationError(
                                        msg_num.format(
                                            sheet.name,
                                            row + 1,
                                            col + 1,
                                            file,
                                            get_value(cell.value),
                                        ),
                                        code="invalid",
                                        params={"file": file},
                                    )
                            elif col == 2 or col == 4 or col == 6:
                                cell = sheet.cell(row, col)
                                try:
                                    if cell.value.strip():
                                        values = (
                                            cell.value.strip().strip(",").split(",")
                                        )
                                        for value in values:
                                            int(value.strip())
                                except:
                                    raise ValidationError(
                                        msg_num.format(
                                            sheet.name,
                                            row + 1,
                                            col + 1,
                                            file,
                                            get_value(values),
                                        ),
                                        code="invalid",
                                        params={"file": file},
                                    )
            sheet_number += 1
    except Exception as error:
        raise error


def get_channelrecording_info(file, sufix):
    if not file:
        return
    file.seek(0)
    workbook = xlrd.open_workbook(file_contents=file.read())
    sessions = {}
    sheet_number = 1
    for sheet in workbook.sheets():
        if sheet_number == 1:
            for col in range(sheet.ncols):
                if col > 0:
                    date = get_date_session(sheet.cell(1, col).value)
                    session = {"date": date, "records": {}}
                    for row in range(sheet.nrows):
                        if row >= 2:
                            # Check electrode is valid
                            save = True
                            electrode_cell = sheet.cell(row, 0)
                            if str(electrode_cell.value).strip() != "":
                                channel_number = get_value(electrode_cell.value).strip()
                                if sufix is None:
                                    try:
                                        int(channel_number)
                                    except:
                                        save = False
                                else:
                                    exist_sufix = channel_number.find(sufix)
                                    if exist_sufix > 0:
                                        channel_number = channel_number[0:exist_sufix]
                                    else:
                                        save = False
                                value = get_value(sheet.cell(row, col).value).strip()
                                record = {"value": value}
                                if len(value) > 0 and save:
                                    session["records"][channel_number] = record
                    if bool(session["records"]):  # Check empty records
                        sessions[str(date)] = session
        elif sheet_number == 2 and sufix is None:
            for row in range(sheet.nrows):
                if row > 0:
                    for col in range(sheet.ncols):
                        # Ripples
                        if col == 1:
                            cell = sheet.cell(row, col)
                            if (
                                str(cell.value).strip() == "Y" and
                                str(cell.value).strip() != ""
                            ):
                                electrodes_cell = sheet.cell(row, 2)
                                date_cell = sheet.cell(row, 0)
                                electrodes = (
                                    electrodes_cell.value.strip().strip(",").split(",")
                                )
                                date = datetime(
                                    *xlrd.xldate_as_tuple(
                                        date_cell.value, workbook.datemode
                                    )
                                )
                                date_str = str(date)
                                for electrode in electrodes:
                                    channel_number = str(electrode).strip()
                                    if date_str in sessions.keys():
                                        session = sessions[date_str]
                                        if channel_number in session["records"].keys():
                                            session["records"][channel_number][
                                                "ripples"
                                            ] = True
                                        else:
                                            session["records"][channel_number] = {
                                                "ripples": True
                                            }
                                    else:  # Session doesn't exist
                                        sessions[date_str] = {
                                            "date": date,
                                            "records": {
                                                channel_number: {"ripples": True}
                                            },
                                        }
                        # Sharp waves
                        elif col == 3:
                            cell = sheet.cell(row, col)
                            if (
                                str(cell.value).strip() == "Y" and
                                str(cell.value).strip() != ""
                            ):
                                electrodes_cell = sheet.cell(row, 4)
                                date_cell = sheet.cell(row, 0)
                                electrodes = (
                                    electrodes_cell.value.strip().strip(",").split(",")
                                )
                                date = datetime(
                                    *xlrd.xldate_as_tuple(
                                        date_cell.value, workbook.datemode
                                    )
                                )
                                date_str = str(date)
                                for electrode in electrodes:
                                    ch_number = str(electrode).strip()
                                    if date_str in sessions.keys():
                                        session = sessions[date_str]
                                        if ch_number in session["records"].keys():
                                            session["records"][ch_number][
                                                "sharp_waves"
                                            ] = True
                                        else:
                                            session["records"][ch_number] = {
                                                "sharp_waves": True
                                            }
                                    else:  # Session doesn't exist
                                        sessions[date_str] = {
                                            "date": date,
                                            "records": {
                                                ch_number: {"sharp_waves": True}
                                            },
                                        }
                        # Spikes
                        elif col == 5:
                            cell = sheet.cell(row, col)
                            if (
                                str(cell.value).strip() == "Y" and
                                str(cell.value).strip() != ""
                            ):
                                electrodes_cell = sheet.cell(row, 6)
                                date_cell = sheet.cell(row, 0)
                                electrodes = (
                                    electrodes_cell.value.strip().strip(",").split(",")
                                )
                                date = datetime(
                                    *xlrd.xldate_as_tuple(
                                        date_cell.value, workbook.datemode
                                    )
                                )
                                date_str = str(date)
                                for electrode in electrodes:
                                    channel_number = str(electrode).strip()
                                    if date_str in sessions.keys():
                                        session = sessions[date_str]
                                        if channel_number in session["records"].keys():
                                            session["records"][channel_number][
                                                "spikes"
                                            ] = True
                                        else:
                                            session["records"][channel_number] = {
                                                "spikes": True
                                            }
                                    else:  # Session doesn't exist
                                        sessions[date_str] = {
                                            "date": date,
                                            "records": {
                                                channel_number: {"spikes": True}
                                            },
                                        }
                        elif col == 7:
                            cell = sheet.cell(row, col)
                            if (
                                str(cell.value).strip() == "Y" and
                                str(cell.value).strip() != ""
                            ):
                                date_cell = sheet.cell(row, 0)
                                date = datetime(
                                    *xlrd.xldate_as_tuple(
                                        date_cell.value, workbook.datemode
                                    )
                                )
                                date_str = str(date)
                                if date_str in sessions.keys():
                                    if str(cell.value) != "":
                                        session = sessions[date_str]
                                        session["good behavior"] = str(
                                            cell.value
                                        ).strip()
                                else:
                                    sessions[date_str] = {
                                        "date": date,
                                        "good behavior": str(cell.value).strip(),
                                    }
        sheet_number += 1
    return sessions


def get_tasks_info(file, subject):

    file.seek(0)
    f = TextIOWrapper(file, encoding="ascii")
    file_content = csv.reader(f)
    tasks = {}
    for i, file_row in file_content:
        task_data = {}
        if i:
            task_info = file_row.split("_")
            separate_extension = task_info[-1].split(".")[0]
            task_info[-1] = separate_extension
            year_index = None
            log_index = None
            name = ""
            for word in task_info:
                if word.lower().endswith("log") or word.lower() == "log":
                    log_index = task_info.index(word)
                    year_index = log_index + 1
                    for i in range(1, log_index):
                        name += f"{task_info[i]} "
                    name = name.strip()
                    break
            try:
                startdate = datetime(
                    year=(int(task_info[year_index])),
                    month=int(task_info[year_index + 1]),
                    day=int(task_info[year_index + 2]),
                    hour=int(task_info[year_index + 3]),
                    minute=int(task_info[year_index + 4]),
                    second=int(task_info[year_index + 5]),
                )
            except:
                continue
            str_startdate = startdate.strftime("%Y_%m_%d")
            task_data = {
                "name": name,
                "dataset_type": task_info[log_index],
                "start_time": startdate,
            }
            if (
                str_startdate in tasks.keys()
            ):  # and task_data not in tasks[str_startdate]:
                try:
                    if task_data not in tasks[str_startdate]:
                        tasks[str_startdate].append(task_data)
                except:
                    tasks[str_startdate].update([task_data])
            else:
                tasks[str_startdate] = [task_data]
    ordered_tasks = {}
    for session_date in tasks:
        tasks[session_date].sort(key=get_task_startime)
        ordered_tasks.update({session_date: []})
        for task in tasks[session_date]:
            task_name = task["name"]
            if ordered_tasks[session_date]:
                if task_name not in ordered_tasks[session_date][-1]:
                    ordered_tasks[session_date].append({task_name: [task]})
                else:
                    current_key = list(ordered_tasks[session_date][-1].keys())
                    ordered_tasks[session_date][-1][current_key[0]].append(task)
            else:
                ordered_tasks[session_date].append({task_name: [task]})

    return ordered_tasks


def get_task_startime(task):
    return task.get("start_time", None)


def get_sessions_file_columns(subject):
    if subject.sex == "F":
        return SESSIONS_FILE_COLUMNS_V1
    return SESSIONS_FILE_COLUMNS_V2


def display_year(z,
                 year: int = None,
                 month_lines: bool = True,
                 fig=None,
                 row: int = None):
    if year is None:
        year = datetime.now().year
    data = np.ones(365) * np.nan
    data[:len(z)] = z
    d1 = date(year, 1, 1)
    d2 = date(year, 12, 31)
    delta = d2 - d1
    month_names = [
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ]
    month_days = [monthrange(year, month_number)[1] for month_number in range(1, 13)]
    month_positions = (np.cumsum(month_days) - 15) / 7
    # gives me a list with datetimes for each day a year
    dates_in_year = [d1 + timedelta(i) for i in range(delta.days + 1)]
    # gives [0,1,2,3,4,5,6,0,1,2,3,4,5,6,…] (ticktext in xaxis dict translates this to weekdays
    weekdays_in_year = [i.weekday() for i in dates_in_year]
    # gives [1,1,1,1,1,1,1,2,2,2,2,2,2,2,…] name is self-explanatory
    weeknumber_of_dates = [
        int(i.strftime("%V")) if not (int(i.strftime("%V")) == 1 and i.month == 12) else 53
        for i in dates_in_year
    ]
    # gives something like list of strings like '2018-01-25' for each date.
    # Used in data trace to make good hovertext.
    text = [str(i) for i in dates_in_year]
    # 4cc417 green #347c17 dark green
    colorscale = [[False, '#eeeeee'], [True, '#76cf63']]
    if not np.count_nonzero(z):
        colorscale = [[False, '#eeeeee'], [True, '#eeeeee']]
    # handle end of year
    data = [
        go.Heatmap(
            x=weeknumber_of_dates,
            y=weekdays_in_year,
            z=data,
            text=text,
            hoverinfo='text',
            xgap=3,  # this
            ygap=3,  # and this is used to make the grid-like apperance
            showscale=False,
            colorscale=colorscale
        )
    ]
    if month_lines:
        kwargs = dict(
            mode='lines',
            line=dict(
                color='#9e9e9e',
                width=1
            ),
            hoverinfo='skip'
        )
        for datev, dow, wkn in zip(
            dates_in_year,
            weekdays_in_year,
            weeknumber_of_dates
        ):
            if datev.day == 1:
                data += [
                    go.Scatter(
                        x=[wkn - .5, wkn - .5],
                        y=[dow - .5, 6.5],
                        **kwargs
                    )
                ]
                if dow:
                    data += [
                        go.Scatter(
                            x=[wkn - .5, wkn + .5],
                            y=[dow - .5, dow - .5],
                            **kwargs
                        ),
                        go.Scatter(
                            x=[wkn + .5, wkn + .5],
                            y=[dow - .5, - .5],
                            **kwargs
                        )
                    ]
    layout = go.Layout(
        title='activity chart',
        height=250,
        yaxis=dict(
            showline=False, showgrid=False, zeroline=False,
            tickmode='array',
            ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            tickvals=[0, 1, 2, 3, 4, 5, 6],
            autorange="reversed"
        ),
        xaxis=dict(
            showline=False, showgrid=False, zeroline=False,
            tickmode='array',
            ticktext=month_names,
            tickvals=month_positions
        ),
        font={'size': 10, 'color': '#9e9e9e'},
        plot_bgcolor=('#fff'),
        margin=dict(t=40),
        showlegend=False
    )
    if fig is None:
        fig = go.Figure(data=data, layout=layout)
    else:
        fig.add_traces(data, rows=[(row + 1)] * len(data), cols=[1] * len(data))
        fig.update_layout(layout)
        fig.update_xaxes(layout['xaxis'])
        fig.update_yaxes(layout['yaxis'])
    return fig


def display_years(z, years):
    fig = make_subplots(rows=len(years), cols=1, subplot_titles=years)
    for i, year in enumerate(years):
        data = z[i * 365: (i + 1) * 365]
        display_year(data, year=year, fig=fig, row=i)
        fig.update_layout(height=250 * len(years))
    return fig


def discrete_colorscale(bvals, colors):
    """
    bvals - list of values bounding intervals/ranges of interest
    colors - list of rgb or hex colorcodes for values in [bvals[k], bvals[k+1]],0<=k < len(bvals)-1
    returns the plotly  discrete colorscale
    """
    if len(bvals) != len(colors) + 1:
        raise ValueError('len(boundary values) should be equal to  len(colors)+1')
    bvals = sorted(bvals)
    nvals = [(v - bvals[0]) / (bvals[-1] - bvals[0]) for v in bvals]  # normalized values

    dcolorscale = []  # discrete colorscale
    for k in range(len(colors)):
        dcolorscale.extend([[nvals[k], colors[k]], [nvals[k + 1], colors[k]]])

    return dcolorscale


def show_electrode_status(data, days, electrodes, breaks, no_electrodes):

    state_labels = ['no data (0)', 'nothing (1)', 'maybe 1 cell (2)', '1 good cell (3)', '2+ good cells (4)']
    if no_electrodes:
        state_labels.append('no electrodes (5)')

    nlabels = len(state_labels)

    tickvals = np.linspace(0, nlabels - 1, 2 * nlabels + 1)[1::2]

    bvals = np.arange(nlabels + 1) - .5

    colors_hex = ['#eeeeee', '#b81d13', '#efb700', '#008450', '#009ece']
    if no_electrodes:
        colors_hex.append('#000000')

    colors = np.array(colors_hex)[:nlabels]
    dcolorsc = discrete_colorscale(bvals, colors.tolist())
    data = [
        go.Heatmap(
            z=data,
            x=days,
            y=electrodes,
            colorscale=dcolorsc,
            colorbar=dict(
                thickness=10,
                tickvals=tickvals,
                ticktext=state_labels
            ),
            hovertemplate='Date: %{x}<br>Electrode: %{y}<br>Units code: %{z}<extra></extra>',
            xgap=2,
            ygap=2
        ),
    ]

    layout = go.Layout(
        plot_bgcolor=('#fff'),
        margin=dict(t=40),
        yaxis={'title': 'electrode #'},
        height=800,
        xaxis=dict(tickmode='linear', tickangle=90, type='category')
    )

    fig = go.Figure(data=data, layout=layout)
    return fig
