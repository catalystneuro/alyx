from scipy.io import loadmat
import xlrd
import csv
import re
import datetime
from django.core.exceptions import ValidationError
from django.http import HttpResponse


def is_date_session(value):
    regex_dates = "^[[\\d]{6}|[\\d]{5}[A]*$"
    try:
        return re.search(regex_dates, str(int(value)).strip()) is not None
    except:
        return re.search(regex_dates, str(value).strip()) is not None


def get_date_session(value):
    regex_dates = "^[[\\d]{6}|[\\d]{5}[A]*$"
    try:
        if re.search(regex_dates, str(int(value)).strip()):
            date_str = str(int(value)).strip()
    except:
        date_str = value[0:6]
    year = date_str[0:2]
    month = date_str[2:4]
    day = date_str[4:6]
    date = datetime(
        year=int(year),
        month=int(month),
        day=int(day)
    )
    return date


def get_value(value):
    if isinstance(value, int):
        return str(int(value)).strip()
    elif isinstance(value, float):
        return str(int(value)).strip()
    return str(value).strip()


def is_datetime(date, workbook):
    try:
        datetime.datetime(*xlrd.xldate_as_tuple(date, workbook.datemode))
        return True

    except:
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


def validate_channel_recording_file(file):
    if not file:
        return

    regex = "^[\\d]+[a]*$"

    valid_values = ["0", "1", "2", "3", "4", "dead", "dead?", "", "?", "DEAD", "sparse", "NOISE", "noise", "not in", "5", "X", "11", "10"]

    try:
        workbook = xlrd.open_workbook(file_contents=file.read())

        # Check columns
        sheet_number = 1
        msg = "Error loading the file - Sheet: {} - Row: {} - Column: {} - File: {}"
        msg_cr = "Channel number name error - Sheet: {} - Row: {} - Column: {} - File: {}"
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
                                if not is_date_session(cell.value):
                                    raise ValidationError(
                                        msg.format(sheet.name, row + 1, col + 1, file),
                                        code="invalid",
                                        params={"file": file},
                                    )
                        elif row > 1:
                            if col == 0:
                                # Check channel number
                                cell = sheet.cell(row, col)
                                if str(cell.value).strip() == "":
                                    row_valid = False
                                else:
                                    if re.search(regex, get_value(cell.value)) is None:
                                        raise ValidationError(
                                            msg_cr.format(sheet.name, row + 1, col + 1, file),
                                            code="invalid",
                                            params={"file": file},
                                        )
                            elif col > 1:
                                if row_valid:
                                    # Check values
                                    cell = sheet.cell(row, col)

                                    if get_value(cell.value) not in valid_values:
                                        raise ValidationError(
                                            msg_num.format(
                                                sheet.name,
                                                row + 1,
                                                col + 1,
                                                file, get_value(cell.value)
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
                                    datetime.datetime(
                                        *xlrd.xldate_as_tuple(
                                            cell.value,
                                            workbook.datemode
                                        )
                                    )
                                except:
                                    raise ValidationError(
                                        msg_date.format(
                                            sheet.name,
                                            row + 1,
                                            col + 1,
                                            file, get_value(cell.value)
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
                                            file, get_value(cell.value)
                                        ),
                                        code="invalid",
                                        params={"file": file},
                                    )
                            elif col == 2 or col == 4 or col == 6:
                                cell = sheet.cell(row, col)
                                try:
                                    if cell.value.strip() != "":
                                        values = cell.value.strip().strip(",").split(",")
                                        for value in values:
                                            int(value.strip())
                                except:
                                    raise ValidationError(
                                        msg_num.format(
                                            sheet.name,
                                            row + 1,
                                            col + 1,
                                            file, get_value(values)
                                        ),
                                        code="invalid",
                                        params={"file": file},
                                    )
            sheet_number += 1
    except Exception as error:
        raise error


def get_channelrecording_info(file):
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
                    date = get_date_session(sheet.cell(row, 0).value)
                    session = {"date": date, "records": []}
                    for row in range(sheet.nrows):
                        if row >= 3:
                            # Check electrode is valid
                            electrode_cell = sheet.cell(row, 0)
                            if str(electrode_cell.value).strip() != "":
                                electrode_number = get_value(electrode_cell.value)
                                value = get_value(sheet.cell(row, col))
                                record = {"electrode": electrode_number, "value": value}
                                if len(record["value"]) > 0:
                                    session["records"] = {
                                        "electrode": record
                                    }
                    sessions[str(date)] = session
        elif sheet_number == 2:
            for row in range(sheet.nrows):
                if row > 0:
                    for col in range(sheet.ncols):
                        # Ripples
                        if col == 1:
                            cell = sheet(row, col)
                            if str(cell.value).strip() == "Y" and str(cell.value).strip() != "":
                                electrodes_cell = sheet(row, 2)
                                electrodes = electrodes_cell.value.strip().strip(",").split(",")
                                date = datetime.datetime(
                                    *xlrd.xldate_as_tuple(
                                        cell.value,
                                        workbook.datemode
                                    )
                                )
                                for electrode in electrodes:
                                    channel_number = str(electrode)
                                    if str(date) in sessions:
                                        session = sessions[date]
                                        if str(electrode) in session["records"]:
                                            session["records"][channel_number]["ripples"] = True
                                        else:
                                            session["records"][channel_number] = {
                                                "ripples": True
                                            }
                                    else:  # Session doesn't exist
                                        sessions[date] = {
                                            "records": {
                                                channel_number: {
                                                    "ripples": True
                                                }
                                            }
                                        }
                        # Sharp waves
                        elif col == 3:
                            cell = sheet(row, col)
                            if str(cell.value).strip() == "Y" and str(cell.value).strip() != "":
                                electrodes_cell = sheet(row, 4)
                                electrodes = electrodes_cell.cell.value.strip().strip(",").split(",")
                                date = datetime.datetime(
                                    *xlrd.xldate_as_tuple(
                                        cell.value,
                                        workbook.datemode
                                    )
                                )
                                for electrode in electrodes:
                                    channel_number = str(electrode)
                                    if str(date) in sessions:
                                        session = sessions[date]
                                        if str(electrode) in session["records"]:
                                            session["records"][channel_number]["sharp_waves"] = True
                                        else:
                                            session["records"][channel_number] = {
                                                "sharp_waves" : True
                                            }
                                    else:  # Session doesn't exist
                                        sessions[date] = {
                                            "records": {
                                                channel_number: {
                                                    "sharp_waves": True
                                                }
                                            }
                                        }
                        # Spikes
                        elif col == 5:
                            cell = sheet(row, col)
                            if str(cell.value).strip() == "Y" and str(cell.value).strip() != "":
                                electrodes_cell = sheet(row, 6)
                                electrodes = electrodes_cell.cell.value.strip().strip(",").split(",")
                                date = datetime.datetime(
                                    *xlrd.xldate_as_tuple(
                                        cell.value,
                                        workbook.datemode
                                    )
                                )
                                for electrode in electrodes:
                                    channel_number = str(electrode)
                                    if str(date) in sessions:
                                        session = sessions[date]
                                        if str(electrode) in session["records"]:
                                            session["records"][channel_number]["spikes"] = True
                                        else:
                                            session["records"][channel_number] = {
                                                "spikes": True
                                            }
                                    else:  # Session doesn't exist
                                        sessions[date] = {
                                            "records": {
                                                channel_number: {
                                                    "spikes": True
                                                }
                                            }
                                        }
                        elif col == 7:
                            cell = sheet(row, col)
                            if str(cell.value).strip() == "Y" and str(cell.value).strip() != "":
                                date = datetime.datetime(
                                    *xlrd.xldate_as_tuple(
                                        cell.value,
                                        workbook.datemode
                                    )
                                )
                                if str(date) in sessions:
                                    if str(cell.value) != "":
                                        session = sessions[date]
                                        session["good behavior"] = str(cell.value).strip()
                                else:
                                    sessions[date] = {
                                        "good behavior": str(cell.value).strip()
                                    }
        sheet_number += 1
    return sessions
