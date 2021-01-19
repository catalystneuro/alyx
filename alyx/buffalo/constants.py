SESSIONS_FILE_COLUMNS_V1 = [
    "Date (mm/dd/yyyy)",
    "Handler Initials",
    "Weight (kg)",
    "Food (mL)",
    "Pump Setting",
    "Menstration",
    "General Comments",
    "Daily Task List",
    "Task 1",
    "Start Time (hh:mm)",
    "Comments",
    "File Name",
    "Task 2",
    "Start Time (hh:mm)",
    "Comments",
    "File Name",
    "Task 3",
    "Start Time (hh:mm)",
    "Comments",
    "File Name",
    "Task 4",
    "Start Time (hh:mm)",
    "Comments",
    "File Name",
    "Task 5",
    "Start Time (hh:mm)",
    "Comments",
    "File Name",
    "Task 6",
    "Start Time (hh:mm)",
    "Comments",
    "File Name",
    "Task 7",
    "Start Time (hh:mm)",
    "Comments",
    "File Name",
    "Task 8",
    "Start Time (hh:mm)",
    "Comments",
    "File Name",
    "Task 9",
    "Start Time (hh:mm)",
    "Comments",
    "File Name",
    "",
    "",
    "",
    "",
    "",
    "Handler List",
    "Task List",
    "Chamber Cleaning",
]

SESSIONS_FILE_COLUMNS_V2 = [
    "Date (mm/dd/yyyy)",
    "Handler Initials",
    "Weight (kg)",
    "Food (mL)",
    "Pump Setting",
    "Chamber Cleaning",
    "General Comments",
    "Daily Task List",
    "Task 1",
    "Start Time (hh:mm)",
    "Comments",
    "File Name",
    "Task 2",
    "Start Time (hh:mm)",
    "Comments",
    "File Name",
    "Task 3",
    "Start Time (hh:mm)",
    "Comments",
    "File Name",
    "Task 4",
    "Start Time (hh:mm)",
    "Comments",
    "File Name",
    "Task 5",
    "Start Time (hh:mm)",
    "Comments",
    "File Name",
    "Task 6",
    "Start Time (hh:mm)",
    "Comments",
    "File Name",
    "Task 7",
    "Start Time (hh:mm)",
    "Comments",
    "File Name",
    "Task 8",
    "Start Time (hh:mm)",
    "Comments",
    "File Name",
    "Task 9",
    "Start Time (hh:mm)",
    "Comments",
    "File Name",
    "",
    "",
    "",
    "",
    "",
    "Handler List",
    "Task List",
    "Chamber Cleaning",
]

BOOLEAN_VALUES = ["yes", "no", "n/a"]

NUMBER_CELLS = ["2", "3", "4"]

BOOLEAN_CELLS = ["5", "51"]

START_TIME_CELLS = ["9", "13", "17", "21", "25", "29", "33", "37", "41"]

TASK_CELLS = ["8", "12", "16", "20", "24", "28", "32", "36", "40"]

CATEGORIES_KEY_WORDS = ["ymaze", "foraging", "arnov", "colorgame", "calibration"]

DEAD_VALUES = ["dead", "dead?", "DEAD"]
NUMBER_OF_CELLS_VALUES = ["1", "2", "3", "4"]
ALIVE_VALUES = ["sparse"]
MAYBE_VALUES = ["0", "", "?", "NOISE", "noise"]
NOT_SAVE_VALUES = ["not in"]
OTHER_VALUES = ["5", "X", "11", "10"]

VALID_VALUES = (
    NUMBER_OF_CELLS_VALUES +
    DEAD_VALUES +
    ALIVE_VALUES +
    MAYBE_VALUES +
    NOT_SAVE_VALUES +
    OTHER_VALUES
)

NOT_SAVE_TASKS = ["mid-day break", "done, home"]
