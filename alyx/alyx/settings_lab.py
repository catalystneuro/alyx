from textwrap import dedent
from decouple import config, Csv

# ALYX-SPECIFIC
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost", cast=Csv())
LANGUAGE_CODE = "en-us"
TIME_ZONE = "GB"
GLOBUS_CLIENT_ID = "525cc517-8ccb-4d11-8036-af332da5eafd"
SUBJECT_REQUEST_EMAIL_FROM = "alyx-noreply@cortexlab.net"
DEFAULT_SOURCE = "Cruciform BSU"
DEFAULT_PROTOCOL = "1"
SUPERUSERS = ("root",)
STOCK_MANAGERS = ("charu",)
WEIGHT_THRESHOLD = 0.75
DEFAULT_LAB_NAME = config("LAB_NAME", default="cortexlab")
DEFAULT_LAB_PK = "4027da48-7be3-43ec-a222-f75dffe36872"
SESSION_REPO_URL = (
    "http://ibl.flatironinstitute.org/{lab}/Subjects/{subject}/{date}/{number:03d}/"
)
NARRATIVE_TEMPLATES = {
    "Headplate implant": dedent(
        """
    == General ==

    Start time (hh:mm):   ___:___
    End time (hh:mm):    ___:___

    Bregma-Lambda :   _______  (mm)

    == Drugs == (copy paste as many times as needed; select IV, SC or IP)
    __________________( IV / SC / IP ) Admin. time (hh:mm)  ___:___

    == Coordinates ==  (copy paste as many times as needed; select B or L)
    (B / L) - Region: AP:  _______  ML:  ______  (mm)
    Region: _____________________________

    == Notes ==
    <write your notes here>
        """
    ),
}

# Menu Buffalo lab
CUSTOM_MENU = config("CUSTOM_MENU", default=False)
ADMIN_PAGES = (
    ("Start Here", ["Buffalo subjects",],),
    (
        "Inividual Models",
        [
            "Buffalo subjects",
            "Sessions",
            "TaskTypes",
            "Food logs",
            "Food types",
            "Weighing logs",
            "Electrode logs",
            "Starting points",
            "Channel recordings",
            "Stl files",
            "Dataset types",
            "Datasets",
            "Buffalo datasets",
            "Lab members",
        ],
    ),
)
